"""
Edge Engine API — v2 endpoints for the new pipeline system.
Prefix: /api/v2/edges
"""

import logging
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/edges", tags=["edge-engine"])


# ── Lazy imports so the main app starts even if pipeline isn't fully set up ────

def _get_orchestrator():
    from pipeline.orchestrator import run_daily_pipeline
    return run_daily_pipeline

def _get_health_reporter():
    from pipeline.agents.health_reporter import compile_health_report, get_todays_picks, get_performance_history
    return compile_health_report, get_todays_picks, get_performance_history

def _get_mlb_predictor():
    from pipeline.models.prediction.mlb_predictor import rule_based_mlb_edges, generate_mlb_picks
    return rule_based_mlb_edges, generate_mlb_picks

def _get_wnba_predictor():
    from pipeline.models.prediction.wnba_predictor import rule_based_wnba_edges, generate_wnba_picks
    return rule_based_wnba_edges, generate_wnba_picks

def _get_db():
    from pipeline.db.connection import execute_query
    return execute_query


# ── Response models ────────────────────────────────────────────────────────────

class PickResponse(BaseModel):
    sport: str
    home_team: str
    away_team: str
    game_time_cst: Optional[str]
    pick_side: str
    pick_type: str
    our_probability: float
    market_odds: int
    market_implied_prob: float
    edge_pct: float
    detector: str
    confidence_tier: Optional[str]
    sonnet_narrative: Optional[str]
    features: Optional[dict]


class HealthResponse(BaseModel):
    date: str
    overall_status: str
    ingestion: dict
    predictions: dict
    model_performance: dict
    reflection_summary: Optional[str]
    action_items: list
    last_updated_cst: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/health")
async def get_system_health():
    """System health report — compiled from all agent outputs."""
    try:
        compile_health_report, _, _ = _get_health_reporter()
        report = compile_health_report()
        return report
    except Exception as e:
        logger.error(f"Health report failed: {e}")
        return {
            "date": date.today().isoformat(),
            "overall_status": "initializing",
            "ingestion": {},
            "predictions": {"total": 0},
            "model_performance": {},
            "reflection_summary": "System initializing — pipeline has not run yet.",
            "action_items": ["Run POST /api/v2/edges/run-pipeline to initialize"],
            "last_updated_cst": datetime.now().isoformat(),
        }


@router.get("/today")
async def get_todays_picks(
    sport: Optional[str] = Query(None, description="mlb or wnba"),
    min_edge: float = Query(3.0, description="Minimum edge percentage"),
    confidence: Optional[str] = Query(None, description="high, medium, or low"),
    pick_type: Optional[str] = Query(None, description="ml, spread, or total"),
):
    """
    Today's edge picks from the database.
    Returns picks already logged by the pipeline — not a live calculation.
    """
    try:
        _, get_todays_picks, _ = _get_health_reporter()
        picks = get_todays_picks(sport)
        # Apply additional filters
        if min_edge:
            picks = [p for p in picks if p.get("edge_pct", 0) >= min_edge]
        if confidence:
            picks = [p for p in picks if p.get("confidence_tier") == confidence]
        if pick_type:
            picks = [p for p in picks if p.get("pick_type") == pick_type]
        return {"picks": picks, "total": len(picks), "source": "database"}
    except Exception as e:
        logger.error(f"get_todays_picks failed: {e}")
        return {"picks": [], "total": 0, "source": "database", "error": str(e)}


@router.get("/live")
async def get_live_edges(
    sport: Optional[str] = Query("mlb", description="mlb or wnba"),
    min_edge: float = Query(3.0),
    use_ml: bool = Query(False, description="Use ML models (requires trained models)"),
):
    """
    Live edge calculation — runs detectors in real-time against current odds.
    Slower than /today (live API calls). Use for real-time refresh.
    """
    try:
        if sport == "mlb":
            rule_based, generate = _get_mlb_predictor()
            picks = generate() if use_ml else rule_based(min_edge=min_edge)
        elif sport == "wnba":
            rule_based, generate = _get_wnba_predictor()
            picks = generate() if use_ml else rule_based(min_edge=min_edge)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")

        picks = [p for p in picks if p.get("edge_pct", 0) >= min_edge]
        picks.sort(key=lambda p: p.get("edge_pct", 0), reverse=True)
        return {"picks": picks, "total": len(picks), "source": "live"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Live edge calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance(
    sport: Optional[str] = Query(None),
    days: int = Query(30, ge=7, le=365),
):
    """Rolling performance history — win rate, ROI, P&L by sport and pick type."""
    try:
        _, _, get_performance_history = _get_health_reporter()
        history = get_performance_history(sport, days)

        # Aggregate summary
        graded = [h for h in history if h.get("result") in ("W", "L", "P")]
        wins   = sum(1 for h in graded if h.get("result") == "W")
        total  = len(graded)
        roi    = sum(h.get("pl_units", 0) for h in graded)

        return {
            "summary": {
                "sport": sport or "all",
                "days": days,
                "total_picks": total,
                "wins": wins,
                "losses": total - wins,
                "win_rate": round(wins / total, 3) if total else 0,
                "total_units": round(roi, 2),
                "roi_pct": round((roi / total) * 100, 1) if total else 0,
            },
            "history": history,
        }
    except Exception as e:
        logger.error(f"Performance fetch failed: {e}")
        return {"summary": {"total_picks": 0, "win_rate": 0, "total_units": 0}, "history": []}


@router.get("/reflection")
async def get_reflection_reports(
    days: int = Query(7, ge=1, le=90),
    sport: Optional[str] = Query(None),
):
    """Opus reflection reports — the system's self-audit history."""
    try:
        execute_query = _get_db()
        sport_filter = "AND sport = %s" if sport else ""
        params = (days, sport) if sport else (days,)
        rows = execute_query(
            f"""SELECT run_at_cst, report_date, sport, total_picks,
                       flags_raised, model_health, opus_narrative, action_items
                FROM reflection_reports
                WHERE run_at_cst >= now() - INTERVAL '%s days'
                {sport_filter}
                ORDER BY run_at_cst DESC""",
            params,
        )
        return {"reports": rows, "total": len(rows)}
    except Exception as e:
        logger.error(f"Reflection fetch failed: {e}")
        return {"reports": [], "total": 0}


@router.post("/run-pipeline")
async def trigger_pipeline(
    background_tasks: BackgroundTasks,
    use_ml: bool = Query(False, description="Use ML models — requires trained models"),
):
    """
    Manually trigger the full daily pipeline.
    Runs in the background — poll /health for results.
    """
    run_daily_pipeline = _get_orchestrator()
    background_tasks.add_task(run_daily_pipeline, use_ml=use_ml)
    return {
        "status": "started",
        "message": "Pipeline running in background. Poll /api/v2/edges/health for status.",
        "use_ml": use_ml,
    }


@router.get("/ingestion-log")
async def get_ingestion_log(days: int = Query(7, ge=1, le=30)):
    """Recent data ingestion history — what was fetched, what was flagged."""
    try:
        execute_query = _get_db()
        rows = execute_query(
            """SELECT run_at_cst, sport, source, records_fetched,
                      records_valid, records_rejected, haiku_flags, status, error_msg
               FROM ingestion_log
               WHERE run_at_cst >= now() - INTERVAL '%s days'
               ORDER BY run_at_cst DESC
               LIMIT 100""",
            (days,),
        )
        return {"log": rows, "total": len(rows)}
    except Exception as e:
        return {"log": [], "total": 0, "error": str(e)}
