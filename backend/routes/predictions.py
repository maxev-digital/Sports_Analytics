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
async def get_today_predictions(
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
async def get_recent_predictions(
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
async def get_predictions_by_sport(
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
async def get_prediction_stats():
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
async def get_pending_predictions(
    sport: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """Picks awaiting grading."""
    try:
        where = ["status IN ('pending', 'needs_review')"]
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
async def get_graded_predictions(
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


@router.get("/edges")
async def get_predictions_with_edges(
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
