"""
Narrative Pipeline — generates game script narratives for picks missing them.

Called from orchestrator.py as Phase 4 after picks are generated.
Can also be run standalone for backfilling:
    PYTHONPATH=/root/sporttrader/backend python3 /root/sporttrader/backend/pipeline/narrative_pipeline.py
"""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


def _rows(sql: str, params: tuple = ()) -> list[dict]:
    from pipeline.db.connection import execute_query
    return execute_query(sql, params)


def _enrich_pick(pk: dict) -> dict:
    """Fetch supporting data for a single pick and return enriched dict."""
    home  = pk["home_team"]
    away  = pk["away_team"]
    spt   = pk["sport"]
    gid   = pk.get("game_id")

    # Team ratings
    ratings = {}
    for r in _rows(
        "SELECT * FROM team_ratings WHERE team = ANY(%s) AND sport = %s",
        ([home, away], spt),
    ):
        ratings[r["team"]] = r

    # Line snapshots (oldest → newest)
    snaps = []
    if gid:
        snaps = sorted(
            _rows(
                """SELECT DISTINCT ON (snapshot_label) * FROM line_snapshots
                   WHERE game_id = %s ORDER BY snapshot_label, snapshot_at DESC""",
                (gid,),
            ),
            key=lambda x: x.get("snapshot_at") or "",
        )

    # Injuries
    inj_rows = _rows(
        "SELECT * FROM injury_log WHERE team = ANY(%s) ORDER BY fetched_at DESC",
        ([home, away],),
    )
    home_inj, away_inj = [], []
    for inj in inj_rows:
        if inj["team"] == home and len(home_inj) < 12:
            home_inj.append(inj)
        elif inj["team"] == away and len(away_inj) < 12:
            away_inj.append(inj)

    # H2H + ATS (NFL only)
    h2h, home_ats, away_ats = [], None, None
    if spt == "nfl":
        h2h = _rows(
            """SELECT season, week, game_date, home_team, away_team,
                      home_score, away_score, spread_close, home_covered,
                      total_close, total_went_over
               FROM nfl_historical_odds
               WHERE sport = 'nfl'
                 AND ((home_team = %s AND away_team = %s)
                      OR (home_team = %s AND away_team = %s))
               ORDER BY game_date DESC LIMIT 8""",
            (home, away, away, home),
        )

        def _ats(team: str, role: str) -> dict | None:
            col = "home_team" if role == "home" else "away_team"
            cov = "home_covered" if role == "home" else "NOT home_covered"
            rs = _rows(
                f"""SELECT COUNT(*) AS g,
                           SUM(CASE WHEN {cov} THEN 1 ELSE 0 END) AS c,
                           MIN(season) AS fs, MAX(season) AS ts
                    FROM nfl_historical_odds
                    WHERE sport='nfl' AND {col}=%s AND season>=2022""",
                (team,),
            )
            if not rs or not rs[0]["g"]:
                return None
            r = rs[0]; g = r["g"]; c = r["c"] or 0
            return {"team": team, "role": role, "games": g, "covers": c,
                    "cover_pct": round(c / g * 100, 1),
                    "from_season": r["fs"], "to_season": r["ts"]}

        home_ats = _ats(home, "home")
        away_ats = _ats(away, "away")

    return {
        **pk,
        "home_rating":    ratings.get(home),
        "away_rating":    ratings.get(away),
        "line_snapshots": snaps,
        "h2h":            h2h,
        "home_ats":       home_ats,
        "away_ats":       away_ats,
        "home_injuries":  home_inj,
        "away_injuries":  away_inj,
    }


def run_narrative_generation(pick_ids: list[int] | None = None) -> int:
    """
    Generate game script narratives for picks that are missing them.

    Args:
        pick_ids: If provided, generate only for these IDs.
                  If None, generates for all pending picks with null narrative.

    Returns:
        Number of narratives successfully generated and saved.
    """
    from pipeline.agents.sonnet_reasoner import generate_game_script

    if pick_ids:
        picks = _rows(
            "SELECT * FROM predictions WHERE id = ANY(%s) AND status = 'pending'",
            (pick_ids,),
        )
    else:
        picks = _rows(
            """SELECT * FROM predictions
               WHERE status = 'pending'
                 AND (sonnet_narrative IS NULL OR sonnet_narrative = '')
                 AND (game_time_cst IS NULL OR game_time_cst >= NOW() - INTERVAL '2 days')
               ORDER BY edge_pct DESC
               LIMIT 20""",
            (),
        )

    if not picks:
        logger.info("Narrative pipeline: no picks need narratives")
        return 0

    logger.info("Narrative pipeline: generating for %d picks", len(picks))
    generated = 0

    for pk in picks:
        try:
            enriched = _enrich_pick(pk)
            narrative = generate_game_script(enriched)

            from pipeline.db.connection import execute_write as _write
            _write(
                "UPDATE predictions SET sonnet_narrative = %s WHERE id = %s",
                (narrative, pk["id"]),
            )
            logger.info(
                "Narrative generated for pick %d (%s @ %s)",
                pk["id"], pk["away_team"], pk["home_team"],
            )
            generated += 1

        except Exception as exc:
            logger.error("Narrative generation failed for pick %d: %s", pk["id"], exc)

    logger.info("Narrative pipeline: %d/%d generated", generated, len(picks))
    return generated


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    ids = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else None
    n = run_narrative_generation(pick_ids=ids)
    print(f"Generated {n} narratives")
