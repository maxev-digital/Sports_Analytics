"""
Game script tool — on-demand handicapper analysis with injury cascade integration.

Called by the agent's tool-use loop when a user asks to break down a game.
Fetches enriched game context from DB, runs injury cascade analysis on any
active injuries, then calls Sonnet to generate a full game script.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Players classified as superstars get higher cascade thresholds.
# These PPG estimates are used when no stats table row is found.
_POSITION_PPG_ESTIMATES = {
    # NBA
    "PG": 20.0, "SG": 18.0, "SF": 17.0, "PF": 14.0, "C": 13.0,
    "G": 18.0, "F": 15.0,
    # NFL
    "QB": None, "RB": None, "WR": None, "TE": None,
    "K": None, "DE": None, "LB": None, "CB": None, "S": None,
    # NHL
    "LW": None, "RW": None, "D": None, "G": None,
}

_IMPACT_BY_PPG = [
    (25.0, "superstar"),
    (18.0, "star"),
    (10.0, "starter"),
    (0.0,  "role"),
]


def _rows(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    from pipeline.db.connection import execute_query
    return execute_query(sql, params)


def _guess_impact(ppg: float) -> str:
    for threshold, label in _IMPACT_BY_PPG:
        if ppg >= threshold:
            return label
    return "role"


def _run_cascade_analysis(enriched: dict) -> list[dict[str, Any]]:
    """
    Check all Out/Doubtful players for injury cascade opportunities.

    Returns a list of cascade opportunity dicts (may be empty).
    Each dict contains the fields from CascadeAnalysis plus player_team/player_name.
    """
    from strategies.injury_cascade_strategy import InjuryCascadeStrategy

    cascade = InjuryCascadeStrategy()
    opportunities: list[dict[str, Any]] = []

    snaps = enriched.get("line_snapshots") or []
    open_snap = snaps[0] if snaps else {}
    cur_snap  = snaps[-1] if snaps else {}

    pregame_total  = open_snap.get("total_line")
    current_total  = cur_snap.get("total_line")

    # Need both totals to measure book movement
    if not pregame_total or not current_total:
        return []

    sport = (enriched.get("sport") or "").upper()

    for role_key, inj_list, opp_team in [
        ("home_injuries", enriched.get("home_injuries") or [], enriched.get("away_team")),
        ("away_injuries", enriched.get("away_injuries") or [], enriched.get("home_team")),
    ]:
        inj_team = enriched.get("home_team") if role_key == "home_injuries" else enriched.get("away_team")
        rating   = enriched.get("home_rating") if role_key == "home_injuries" else enriched.get("away_rating")
        team_ppg = float((rating or {}).get("points_per_game") or 0) if rating else 0.0

        for inj in inj_list:
            status = (inj.get("status") or "").lower()
            if not any(k in status for k in ("out", "doubtful")):
                continue

            player_name = inj.get("player_name") or "Unknown"
            position    = (inj.get("position") or "").upper()

            # Estimate PPG from DB player stats if available, else position heuristic
            player_ppg: float = 0.0
            stat_rows = _rows(
                "SELECT ppg FROM player_stats WHERE player_name = %s AND sport = %s LIMIT 1",
                (player_name, sport.lower()),
            )
            if stat_rows and stat_rows[0].get("ppg"):
                player_ppg = float(stat_rows[0]["ppg"])
            else:
                player_ppg = _POSITION_PPG_ESTIMATES.get(position) or 15.0

            # Skip non-scoring sports / positions where PPG is N/A
            if player_ppg == 0.0:
                continue

            player_impact = _guess_impact(player_ppg)

            analysis = cascade.analyze_injury_impact(
                game_id      = enriched.get("game_id") or "",
                injury_player= player_name,
                injury_team  = inj_team or "",
                injured_team_ppg = team_ppg,
                opponent     = opp_team or "",
                pregame_total= float(pregame_total),
                current_total= float(current_total),
                player_ppg   = player_ppg,
                player_impact= player_impact,
                position     = position,
            )

            if analysis is not None:
                opportunities.append({
                    "player_name":   analysis.injury_player,
                    "player_team":   analysis.injury_team,
                    "opponent":      analysis.opponent,
                    "pregame_total": analysis.pregame_total,
                    "current_total": analysis.current_total,
                    "expected_drop": round(analysis.expected_drop, 1),
                    "actual_drop":   round(analysis.actual_drop, 1),
                    "overreaction":  round(analysis.overreaction, 1),
                    "recommendation": analysis.recommendation,
                    "edge":          round(analysis.edge, 1),
                    "confidence":    analysis.confidence,
                    "reasoning":     analysis.reasoning,
                })

    return opportunities


def _enrich_pick_for_agent(pk: dict) -> dict:
    """
    Enrich a pick dict with ratings, injuries, line snapshots, H2H, and cascade analysis.
    Mirrors narrative_pipeline._enrich_pick but runs synchronously from the agent tool.
    """
    home = pk["home_team"]
    away = pk["away_team"]
    spt  = pk["sport"]
    gid  = pk.get("game_id")

    # Team ratings
    ratings: dict[str, Any] = {}
    for r in _rows(
        "SELECT * FROM team_ratings WHERE team = ANY(%s) AND sport = %s",
        ([home, away], spt),
    ):
        ratings[r["team"]] = r

    # Line snapshots
    snaps: list[dict] = []
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
    home_inj: list[dict] = []
    away_inj: list[dict] = []
    for inj in inj_rows:
        if inj["team"] == home and len(home_inj) < 12:
            home_inj.append(inj)
        elif inj["team"] == away and len(away_inj) < 12:
            away_inj.append(inj)

    # H2H + ATS (NFL)
    h2h: list[dict] = []
    home_ats = None
    away_ats = None
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
                           SUM(CASE WHEN {cov} THEN 1 ELSE 0 END) AS c
                    FROM nfl_historical_odds
                    WHERE sport='nfl' AND {col}=%s AND season>=2022""",
                (team,),
            )
            if not rs or not rs[0]["g"]:
                return None
            r = rs[0]
            g = int(r["g"]); c = int(r["c"] or 0)
            return {"team": team, "role": role, "games": g, "covers": c,
                    "cover_pct": round(c / g * 100, 1)}

        home_ats = _ats(home, "home")
        away_ats = _ats(away, "away")

    enriched = {
        **pk,
        "home_rating":   ratings.get(home),
        "away_rating":   ratings.get(away),
        "line_snapshots": snaps,
        "h2h":           h2h,
        "home_ats":      home_ats,
        "away_ats":      away_ats,
        "home_injuries": home_inj,
        "away_injuries": away_inj,
    }

    # Run cascade analysis and inject results
    try:
        cascades = _run_cascade_analysis(enriched)
        enriched["cascade_opportunities"] = cascades
    except Exception as exc:
        logger.warning("Cascade analysis failed (non-fatal): %s", exc)
        enriched["cascade_opportunities"] = []

    return enriched


def build_game_script(
    sport: str,
    home_team: str,
    away_team: str,
    game_id: str | None = None,
) -> dict[str, Any]:
    """
    Main entry point for the agent tool.

    Looks up the pending pick for this game, enriches it, runs cascade analysis,
    and generates a full game script via Sonnet.

    Returns a dict with keys: script, cascade_opportunities, game_found (bool).
    """
    from pipeline.agents.sonnet_reasoner import generate_game_script

    # Look up the pick
    params: list[Any] = [sport.lower(), home_team, away_team]
    id_clause = "AND game_id = %s" if game_id else ""
    if game_id:
        params.append(game_id)
    params.append(1)

    rows = _rows(
        f"""
        SELECT id, sport, home_team, away_team, pick_side, pick_type,
               edge_pct, confidence_tier, market_odds, our_probability,
               market_implied_prob, detector, total_line, game_time_cst,
               game_id, sonnet_narrative
        FROM predictions
        WHERE LOWER(sport) = %s
          AND (LOWER(home_team) LIKE LOWER(%s) OR LOWER(home_team) LIKE LOWER(%%s))
          AND (LOWER(away_team) LIKE LOWER(%s) OR LOWER(away_team) LIKE LOWER(%%s))
          {id_clause}
        ORDER BY edge_pct DESC
        LIMIT %s
        """.replace("%%s", "%s"),
        tuple(params + [f"%{home_team}%", away_team, f"%{away_team}%"]),
    )

    # Fallback: fuzzy team match
    if not rows:
        rows = _rows(
            """
            SELECT id, sport, home_team, away_team, pick_side, pick_type,
                   edge_pct, confidence_tier, market_odds, our_probability,
                   market_implied_prob, detector, total_line, game_time_cst,
                   game_id, sonnet_narrative
            FROM predictions
            WHERE LOWER(sport) = %s
              AND (LOWER(home_team) LIKE %s OR LOWER(away_team) LIKE %s
                   OR LOWER(home_team) LIKE %s OR LOWER(away_team) LIKE %s)
            ORDER BY edge_pct DESC
            LIMIT 1
            """,
            (sport.lower(), f"%{home_team.split()[-1].lower()}%",
             f"%{home_team.split()[-1].lower()}%",
             f"%{away_team.split()[-1].lower()}%",
             f"%{away_team.split()[-1].lower()}%"),
        )

    if not rows:
        return {
            "game_found": False,
            "script": f"No pick found for {away_team} @ {home_team} ({sport.upper()}). The game may not be in today's model output.",
            "cascade_opportunities": [],
        }

    pk = dict(rows[0])
    enriched = _enrich_pick_for_agent(pk)
    script = generate_game_script(enriched)

    return {
        "game_found": True,
        "matchup": f"{pk['away_team']} @ {pk['home_team']}",
        "sport": pk["sport"].upper(),
        "script": script,
        "cascade_opportunities": enriched.get("cascade_opportunities") or [],
        "pick_side": pk.get("pick_side"),
        "pick_type": pk.get("pick_type"),
        "edge_pct": pk.get("edge_pct"),
        "confidence_tier": pk.get("confidence_tier"),
    }
