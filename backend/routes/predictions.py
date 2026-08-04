"""
Predictions API Routes — reads from PostgreSQL maxev_sports.predictions table.

Schema (key columns):
  id, created_at_cst, sport, home_team, away_team, game_time_cst,
  pick_side, pick_type, our_probability, market_odds, market_implied_prob,
  edge_pct, detector, confidence_tier, status, result, pl_units,
  sonnet_narrative, game_id, total_line
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime, date, timedelta
import logging
import pytz

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

CST = pytz.timezone("America/Chicago")

def _today_cst() -> str:
    return datetime.now(CST).strftime("%Y-%m-%d")


def _get_db():
    from pipeline.db.connection import execute_query
    return execute_query


def _rows(sql: str, params: tuple = ()) -> list[dict]:
    execute_query = _get_db()
    return execute_query(sql, params)


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/today")
def get_today_predictions(
    sport: Optional[str] = Query(None),
    pick_type: Optional[str] = Query(None),
):
    """Today's picks based on game_time_cst date in CST."""
    try:
        today = _today_cst()
        where = ["game_time_cst::date = %s OR created_at_cst::date = %s"]
        params: list = [today, today]

        if sport:
            where.append("LOWER(sport) = LOWER(%s)")
            params.append(sport)
        if pick_type:
            where.append("LOWER(pick_type) = LOWER(%s)")
            params.append(pick_type)

        sql = f"""
            SELECT * FROM predictions
            WHERE {' AND '.join(where)}
            ORDER BY game_time_cst, sport, home_team
        """
        rows = _rows(sql, tuple(params))
        return {"total": len(rows), "date": today, "predictions": rows}
    except Exception as e:
        logger.error("get_today_predictions: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
def get_recent_predictions(
    sport: Optional[str] = Query(None),
    pick_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    days: int = Query(7, ge=1, le=90),
):
    try:
        where = ["created_at_cst >= now() - INTERVAL %s"]
        params: list = [f"{days} days"]

        if sport:
            where.append("LOWER(sport) = LOWER(%s)")
            params.append(sport)
        if pick_type:
            where.append("LOWER(pick_type) = LOWER(%s)")
            params.append(pick_type)

        sql = f"""
            SELECT * FROM predictions
            WHERE {' AND '.join(where)}
            ORDER BY created_at_cst DESC
            LIMIT %s
        """
        params.append(limit)
        rows = _rows(sql, tuple(params))
        return {"total": len(rows), "days": days, "predictions": rows}
    except Exception as e:
        logger.error("get_recent_predictions: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-sport/{sport}")
def get_predictions_by_sport(
    sport: str,
    days: int = Query(7, ge=1, le=90),
    pick_type: Optional[str] = Query(None),
):
    try:
        where = ["LOWER(sport) = LOWER(%s)", "created_at_cst >= now() - INTERVAL %s"]
        params: list = [sport, f"{days} days"]

        if pick_type:
            where.append("LOWER(pick_type) = LOWER(%s)")
            params.append(pick_type)

        sql = f"""
            SELECT * FROM predictions
            WHERE {' AND '.join(where)}
            ORDER BY game_time_cst DESC, home_team
        """
        rows = _rows(sql, tuple(params))
        return {"sport": sport, "total": len(rows), "days": days, "predictions": rows}
    except Exception as e:
        logger.error("get_predictions_by_sport: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def get_prediction_stats():
    """Aggregate stats from the PostgreSQL predictions table."""
    try:
        # Total all-time
        total_row = _rows("SELECT COUNT(*) AS n FROM predictions")
        total = total_row[0]["n"] if total_row else 0

        # Today
        today = _today_cst()
        today_row = _rows(
            "SELECT COUNT(*) AS n FROM predictions WHERE created_at_cst::date = %s",
            (today,),
        )
        today_count = today_row[0]["n"] if today_row else 0

        # Last 7 days
        last7_row = _rows(
            "SELECT COUNT(*) AS n FROM predictions WHERE created_at_cst >= now() - INTERVAL '7 days'"
        )
        last_7 = last7_row[0]["n"] if last7_row else 0

        # By sport (last 30 days)
        by_sport_rows = _rows("""
            SELECT sport, COUNT(*) AS n
            FROM predictions
            WHERE created_at_cst >= now() - INTERVAL '30 days'
            GROUP BY sport ORDER BY n DESC
        """)
        by_sport = {r["sport"]: r["n"] for r in by_sport_rows}

        # By pick_type (last 30 days)
        by_type_rows = _rows("""
            SELECT pick_type, COUNT(*) AS n
            FROM predictions
            WHERE created_at_cst >= now() - INTERVAL '30 days'
            GROUP BY pick_type ORDER BY n DESC
        """)
        by_type = {r["pick_type"]: r["n"] for r in by_type_rows}

        # Status breakdown (last 30 days)
        status_rows = _rows("""
            SELECT status, COUNT(*) AS n
            FROM predictions
            WHERE created_at_cst >= now() - INTERVAL '30 days'
            GROUP BY status ORDER BY n DESC
        """)
        by_status = {r["status"]: r["n"] for r in status_rows}

        # Graded picks record (last 30 days)
        # Grader writes status = result directly ('win'/'loss'/'push')
        graded_rows = _rows("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'win' THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN status = 'loss' THEN 1 ELSE 0 END) AS losses,
                SUM(CASE WHEN status = 'push' THEN 1 ELSE 0 END) AS pushes,
                ROUND(AVG(pl_units)::numeric, 3) AS avg_pl,
                ROUND(SUM(pl_units)::numeric, 3) AS total_pl
            FROM predictions
            WHERE status IN ('win', 'loss', 'push')
              AND created_at_cst >= now() - INTERVAL '30 days'
        """)
        graded = graded_rows[0] if graded_rows else {}
        total_graded = graded.get("total", 0) or 0
        win_rate = None
        if total_graded and total_graded > 0:
            wins = graded.get("wins", 0) or 0
            losses = graded.get("losses", 0) or 0
            denom = wins + losses
            win_rate = round(wins / denom * 100, 1) if denom else None

        # Average edge on pending picks
        edge_row = _rows("""
            SELECT ROUND(AVG(edge_pct)::numeric, 2) AS avg_edge
            FROM predictions
            WHERE status = 'pending'
              AND created_at_cst >= now() - INTERVAL '7 days'
        """)
        avg_edge = edge_row[0]["avg_edge"] if edge_row else None

        return {
            "total_all_time": total,
            "today": today_count,
            "last_7_days": last_7,
            "by_sport_30d": by_sport,
            "by_pick_type_30d": by_type,
            "by_status_30d": by_status,
            "graded_30d": {
                "total": total_graded,
                "wins": graded.get("wins", 0),
                "losses": graded.get("losses", 0),
                "pushes": graded.get("pushes", 0),
                "win_rate_pct": win_rate,
                "total_pl_units": graded.get("total_pl"),
                "avg_pl_per_pick": graded.get("avg_pl"),
            },
            "avg_edge_pending_7d": avg_edge,
            "generated_at": datetime.now(CST).isoformat(),
        }
    except Exception as e:
        logger.error("get_prediction_stats: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending")
def get_pending_predictions(
    sport: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """Picks awaiting grading."""
    try:
        where = ["status IN ('pending', 'needs_review')", "(game_time_cst IS NULL OR game_time_cst >= NOW() - INTERVAL '4 hours')"]
        params: list = []

        if sport:
            where.append("LOWER(sport) = LOWER(%s)")
            params.append(sport)

        sql = f"""
            SELECT * FROM predictions
            WHERE {' AND '.join(where)}
            ORDER BY game_time_cst ASC
            LIMIT %s
        """
        params.append(limit)
        rows = _rows(sql, tuple(params))
        return {"total": len(rows), "predictions": rows}
    except Exception as e:
        logger.error("get_pending_predictions: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graded")
def get_graded_predictions(
    sport: Optional[str] = Query(None),
    result: Optional[str] = Query(None, description="WIN, LOSS, or PUSH"),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=500),
):
    """Graded picks — filter by sport, result, date range."""
    try:
        where = ["status IN ('win', 'loss', 'push')", "created_at_cst >= now() - INTERVAL %s"]
        params: list = [f"{days} days"]

        if sport:
            where.append("LOWER(sport) = LOWER(%s)")
            params.append(sport)
        if result:
            where.append("UPPER(result) = UPPER(%s)")
            params.append(result)

        sql = f"""
            SELECT * FROM predictions
            WHERE {' AND '.join(where)}
            ORDER BY created_at_cst DESC
            LIMIT %s
        """
        params.append(limit)
        rows = _rows(sql, tuple(params))
        return {"total": len(rows), "days": days, "predictions": rows}
    except Exception as e:
        logger.error("get_graded_predictions: %s", e)
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/enriched")
def get_enriched_predictions(
    status: Optional[str] = Query("pending"),
    sport: Optional[str] = Query(None),
):
    """Picks enriched with team ratings, line movement, H2H, ATS splits, injuries."""
    try:
        sql = """
            SELECT * FROM predictions
            WHERE status = %s
              AND (game_time_cst IS NULL OR game_time_cst >= NOW() - INTERVAL '2 days')
        """
        p: list = [status]
        if sport:
            sql += " AND LOWER(sport) = LOWER(%s)"
            p.append(sport)
        sql += " ORDER BY edge_pct DESC LIMIT 50"
        picks = _rows(sql, tuple(p))

        if not picks:
            return {"picks": [], "total": 0}

        game_ids  = [pk["game_id"] for pk in picks if pk.get("game_id")]
        all_teams = list({t for pk in picks for t in [pk["home_team"], pk["away_team"]]})
        sports    = list({pk["sport"] for pk in picks})

        # ── Team ratings (batch) ────────────────────────────────────────────
        ratings: dict = {}
        if all_teams:
            for r in _rows(
                "SELECT * FROM team_ratings WHERE team = ANY(%s) AND sport = ANY(%s)",
                (all_teams, sports),
            ):
                ratings[f"{r['team']}|{r['sport']}"] = r

        # ── Line snapshots (batch, grouped by game_id) ──────────────────────
        snapshots: dict = {}
        if game_ids:
            for s in _rows(
                """
                SELECT DISTINCT ON (game_id, snapshot_label) *
                FROM line_snapshots WHERE game_id = ANY(%s)
                ORDER BY game_id, snapshot_label, snapshot_at DESC
                """,
                (game_ids,),
            ):
                gid = s["game_id"]
                snapshots.setdefault(gid, []).append(s)
            # sort oldest-first per game so frontend can show movement direction
            for gid in snapshots:
                snapshots[gid].sort(key=lambda x: x.get("snapshot_at") or "")

        # ── Injuries (batch) ────────────────────────────────────────────────
        injuries: dict = {}
        if all_teams:
            for inj in _rows(
                "SELECT * FROM injury_log WHERE team = ANY(%s) ORDER BY fetched_at DESC",
                (all_teams,),
            ):
                injuries.setdefault(inj["team"], [])
                if len(injuries[inj["team"]]) < 12:
                    injuries[inj["team"]].append(inj)

        # ── Enrich each pick ────────────────────────────────────────────────
        enriched = []
        for pk in picks:
            home    = pk["home_team"]
            away    = pk["away_team"]
            spt     = pk["sport"]
            gid     = pk.get("game_id")

            h2h      = []
            home_ats = None
            away_ats = None

            if spt == "nfl" and home and away:
                h2h = _rows(
                    """
                    SELECT season, week, game_date, home_team, away_team,
                           home_score, away_score, spread_close, home_covered,
                           total_close, total_went_over
                    FROM nfl_historical_odds
                    WHERE sport = 'nfl'
                      AND ((home_team = %s AND away_team = %s)
                           OR (home_team = %s AND away_team = %s))
                    ORDER BY game_date DESC LIMIT 8
                    """,
                    (home, away, away, home),
                )

                def _ats(team: str, role: str) -> dict | None:
                    if role == "home":
                        rows = _rows(
                            """SELECT COUNT(*) AS g,
                                      SUM(CASE WHEN home_covered THEN 1 ELSE 0 END) AS c,
                                      MIN(season) AS fs, MAX(season) AS ts
                               FROM nfl_historical_odds
                               WHERE sport='nfl' AND home_team=%s AND season>=2022""",
                            (team,),
                        )
                        cov_key = "c"
                    else:
                        rows = _rows(
                            """SELECT COUNT(*) AS g,
                                      SUM(CASE WHEN NOT home_covered THEN 1 ELSE 0 END) AS c,
                                      MIN(season) AS fs, MAX(season) AS ts
                               FROM nfl_historical_odds
                               WHERE sport='nfl' AND away_team=%s AND season>=2022""",
                            (team,),
                        )
                        cov_key = "c"
                    if not rows or not rows[0]["g"]:
                        return None
                    r = rows[0]
                    g = r["g"]; c = r["c"] or 0
                    return {
                        "team": team, "role": role, "games": g, "covers": c,
                        "cover_pct": round(c / g * 100, 1),
                        "from_season": r["fs"], "to_season": r["ts"],
                    }

                home_ats = _ats(home, "home")
                away_ats = _ats(away, "away")

            enriched.append({
                **pk,
                "home_rating":   ratings.get(f"{home}|{spt}"),
                "away_rating":   ratings.get(f"{away}|{spt}"),
                "line_snapshots": snapshots.get(gid, []) if gid else [],
                "h2h":           h2h,
                "home_ats":      home_ats,
                "away_ats":      away_ats,
                "home_injuries": injuries.get(home, []),
                "away_injuries": injuries.get(away, []),
            })

        return {"picks": enriched, "total": len(enriched)}

    except Exception as e:
        logger.error("get_enriched_predictions: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-narrative/{pick_id}")
def generate_narrative_for_pick(pick_id: int):
    """On-demand game script generation for a single pick. Saves to DB and returns."""
    try:
        from pipeline.narrative_pipeline import _enrich_pick, run_narrative_generation
        from pipeline.agents.sonnet_reasoner import generate_game_script

        picks = _rows("SELECT * FROM predictions WHERE id = %s", (pick_id,))
        if not picks:
            raise HTTPException(status_code=404, detail=f"Pick {pick_id} not found")

        pk = picks[0]
        enriched = _enrich_pick(pk)
        narrative = generate_game_script(enriched)

        from pipeline.db.connection import execute_write as _write
        _write(
            "UPDATE predictions SET sonnet_narrative = %s WHERE id = %s",
            (narrative, pick_id),
        )
        logger.info("On-demand narrative generated for pick %d", pick_id)
        return {
            "pick_id": pick_id,
            "narrative": narrative,
            "chars": len(narrative),
            "saved": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("generate_narrative_for_pick %d: %s", pick_id, e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/edges")
def get_predictions_with_edges(
    min_edge: float = Query(3.0, ge=0),
    sport: Optional[str] = Query(None),
    pick_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """Pending picks with edge >= min_edge, sorted by edge descending."""
    try:
        where = ["status IN ('pending', 'needs_review')", "edge_pct >= %s",
                 "game_time_cst >= now()"]
        params: list = [min_edge]

        if sport:
            where.append("LOWER(sport) = LOWER(%s)")
            params.append(sport)
        if pick_type:
            where.append("LOWER(pick_type) = LOWER(%s)")
            params.append(pick_type)

        sql = f"""
            SELECT * FROM predictions
            WHERE {' AND '.join(where)}
            ORDER BY edge_pct DESC
            LIMIT %s
        """
        params.append(limit)
        rows = _rows(sql, tuple(params))
        return {"total": len(rows), "min_edge": min_edge, "predictions": rows}
    except Exception as e:
        logger.error("get_predictions_with_edges: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recap")
def get_predictions_recap(
    date: Optional[str] = Query(None, description="YYYY-MM-DD, defaults to yesterday"),
):
    """
    All pipeline predictions for a given date with results, pitcher context,
    and daily summary. Used by the Daily Recap page alongside F5 signals.
    """
    from datetime import date as dt_date, timedelta
    try:
        recap_date = date or str(dt_date.today() - timedelta(days=1))

        rows = _rows(
            """
            SELECT id, sport, home_team, away_team, game_time_cst,
                   pick_side, pick_type, edge_pct, confidence_tier,
                   market_odds, our_probability, detector,
                   status, pl_units, sonnet_narrative,
                   home_pitcher, away_pitcher,
                   home_pitcher_era, away_pitcher_era,
                   home_pitcher_xera, away_pitcher_xera
            FROM predictions
            WHERE (game_time_cst::date = %s OR created_at_cst::date = %s)
            ORDER BY
              CASE confidence_tier WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
              edge_pct DESC
            """,
            (recap_date, recap_date),
        )

        wins    = sum(1 for r in rows if r.get("status") == "win")
        losses  = sum(1 for r in rows if r.get("status") == "loss")
        pushes  = sum(1 for r in rows if r.get("status") == "push")
        pending = sum(1 for r in rows if r.get("status") == "pending")
        total_pl = sum(float(r.get("pl_units") or 0) for r in rows if r.get("pl_units") is not None)
        graded  = wins + losses + pushes
        win_rate = round(wins / graded * 100, 1) if graded > 0 else None

        return {
            "date": recap_date,
            "picks": rows,
            "summary": {
                "total": len(rows),
                "wins": wins,
                "losses": losses,
                "pushes": pushes,
                "pending": pending,
                "graded": graded,
                "win_rate": win_rate,
                "total_pl": round(total_pl, 2),
            },
        }
    except Exception as e:
        logger.error("get_predictions_recap: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
