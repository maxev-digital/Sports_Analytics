"""
Verification API — exposes multi-model verification results.

GET /api/f5/verify/signals    — verify F5 MLB edge signals
GET /api/f5/verify/ratings    — verify NFL power ratings
GET /api/f5/verify/status     — last cached verification summary
POST /api/f5/verify/run       — trigger a fresh full verification
"""
from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Query
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/f5/verify", tags=["verification"])

CACHE_DIR = Path(__file__).parent.parent / "f5_backtest" / "verification_cache"
CACHE_DIR.mkdir(exist_ok=True)


def _load_latest(subject: str) -> dict | None:
    """Load today's cached result, then fall back to the most recent available."""
    today_file = CACHE_DIR / f"{subject}_{date.today().isoformat()}.json"
    if today_file.exists():
        try:
            return json.loads(today_file.read_text())
        except Exception:
            pass
    # Fall back to most recent file for this subject
    files = sorted(CACHE_DIR.glob(f"{subject}_*.json"), reverse=True)
    if files:
        try:
            return json.loads(files[0].read_text())
        except Exception:
            pass
    return None


def _summary(result: dict) -> dict:
    """Slim summary for the status endpoint."""
    return {
        "subject":     result.get("subject"),
        "verdict":     result.get("verdict"),
        "confidence":  result.get("confidence"),
        "verified_at": result.get("verified_at"),
        "flag_count":  sum(len(v) for v in result.get("pre_check_flags", {}).values()),
        "opus_note":   result.get("opus", {}).get("user_display_note", ""),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/status")
async def verification_status():
    """Return a quick summary of the last cached verification run for each subject."""
    subjects = ["signals", "ratings"]
    out: dict[str, dict | None] = {}
    for s in subjects:
        data = _load_latest(s)
        out[s] = _summary(data) if data else None
    return {"status": "ok", "verifications": out}


@router.get("/signals")
async def verify_signals_endpoint(force: bool = Query(default=False)):
    """
    Return the full multi-model verification report for F5 MLB signals.
    Cached daily; pass force=true to re-run.
    """
    cached = _load_latest("signals")
    if cached and not force:
        return {"cached": True, **cached}

    try:
        from verification.verifier import verify_signals
        result = verify_signals(force=force)
        return {"cached": False, **result}
    except Exception as exc:
        logger.error(f"Signal verification failed: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(exc)})


@router.get("/ratings")
async def verify_ratings_endpoint(force: bool = Query(default=False)):
    """
    Return the full multi-model verification report for NFL power ratings.
    Cached daily; pass force=true to re-run.
    """
    cached = _load_latest("ratings")
    if cached and not force:
        return {"cached": True, **cached}

    try:
        from verification.verifier import verify_power_ratings
        result = verify_power_ratings(force=force)
        return {"cached": False, **result}
    except Exception as exc:
        logger.error(f"Ratings verification failed: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(exc)})


@router.post("/run")
async def run_full_verification(background_tasks: BackgroundTasks):
    """
    Trigger a full verification run (both signals + ratings) in the background.
    Returns immediately; poll /status to see results.
    """
    def _run_all():
        try:
            from verification.verifier import verify_signals, verify_power_ratings
            verify_signals(force=True)
            verify_power_ratings(force=True)
            logger.info("Full verification run complete")
        except Exception as exc:
            logger.error(f"Background verification failed: {exc}", exc_info=True)

    background_tasks.add_task(_run_all)
    return {"queued": True, "message": "Verification running in background — poll /api/f5/verify/status"}
