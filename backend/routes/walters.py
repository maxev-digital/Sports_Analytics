"""
Walters Power Rating Engine — API routes.

GET /api/f5/walters-ratings          — current ratings + engine state
GET /api/f5/walters-ratings/week/:w  — ratings snapshot for a specific week
POST /api/f5/walters-ratings/update  — trigger weekly recalc (admin)
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()
logger = logging.getLogger(__name__)

DATA_DIR     = Path(__file__).parent.parent / "f5_backtest"
RATINGS_FILE = DATA_DIR / "nfl_power_ratings.json"
ENGINE_SCRIPT = Path(__file__).parent.parent / "walters_engine.py"


def _load() -> dict[str, Any]:
    if RATINGS_FILE.exists():
        return json.loads(RATINGS_FILE.read_text())
    return {}


@router.get("/walters-ratings")
def walters_ratings():
    """Current ratings, engine state, week history summary."""
    data = _load()
    if not data:
        raise HTTPException(status_code=503, detail="Ratings data not available")

    week_ratings = data.get("week_ratings", {})
    weeks_processed = sorted(week_ratings.keys())

    # Build week-over-week change summary (last processed week vs preseason)
    changes: list[dict] = []
    if weeks_processed:
        latest_week_key = weeks_processed[-1]
        latest = week_ratings[latest_week_key].get("ratings", {})
        # Compare against preseason (current if no prior week)
        prev_key = weeks_processed[-2] if len(weeks_processed) > 1 else None
        prev = week_ratings[prev_key].get("ratings", {}) if prev_key else {
            r["team"]: r["rating"] for r in data.get("current", [])
        }
        for team, rating in latest.items():
            old = prev.get(team, rating)
            changes.append({
                "team": team,
                "rating": rating,
                "change": round(rating - old, 2),
            })
        changes.sort(key=lambda x: x["rating"], reverse=True)

    return {
        "season": data.get("season", "2026"),
        "season_start": data.get("season_start", "2026-09-10"),
        "last_updated_week": data.get("last_updated_week", 0),
        "updated_at": data.get("updated_at", None),
        "method": data.get("method", "walters"),
        "formula": data.get("formula", ""),
        "home_field": data.get("home_field", 2.0),
        "weeks_processed": weeks_processed,
        "current": data.get("current", []),
        "week_changes": changes,
        "week_ratings": {
            k: {"processed_at": v.get("processed_at"), "games": v.get("games", 0)}
            for k, v in week_ratings.items()
        },
    }


@router.get("/walters-ratings/week/{week_num}")
def walters_ratings_week(week_num: int):
    """Ratings snapshot for a specific week, with rank changes vs previous week."""
    data = _load()
    week_key = f"week_{week_num}"
    week_ratings = data.get("week_ratings", {})

    if week_key not in week_ratings:
        # Return preseason ratings with week 0
        if week_num == 0:
            return {
                "week": 0,
                "label": "Preseason",
                "ratings": [
                    {"rank": r["rank"], "team": r["team"], "team_name": r["team_name"],
                     "rating": r["rating"], "tier": r["tier"], "change": 0.0, "rank_change": 0}
                    for r in data.get("current", [])
                ],
            }
        raise HTTPException(status_code=404, detail=f"Week {week_num} not yet processed")

    this_week = week_ratings[week_key].get("ratings", {})

    # Find previous week for comparison
    all_weeks = sorted([int(k.replace("week_", "")) for k in week_ratings.keys()])
    prev_week_num = max([w for w in all_weeks if w < week_num], default=0)
    if prev_week_num > 0:
        prev_ratings = week_ratings[f"week_{prev_week_num}"].get("ratings", {})
    else:
        prev_ratings = {r["team"]: r["rating"] for r in data.get("current", [])}

    # Build ranked snapshot
    ranked = sorted(this_week.items(), key=lambda x: x[1], reverse=True)
    prev_ranked = {t: i + 1 for i, (t, _) in enumerate(
        sorted(prev_ratings.items(), key=lambda x: x[1], reverse=True)
    )}

    result = []
    for rank, (team, rating) in enumerate(ranked, 1):
        prev_rating = prev_ratings.get(team, rating)
        prev_rank = prev_ranked.get(team, rank)
        team_name = next((r["team_name"] for r in data.get("current", []) if r["team"] == team), team)
        result.append({
            "rank": rank,
            "team": team,
            "team_name": team_name,
            "rating": rating,
            "tier": _tier(rating),
            "change": round(rating - prev_rating, 2),
            "rank_change": prev_rank - rank,  # positive = moved up
        })

    return {
        "week": week_num,
        "label": f"Week {week_num}",
        "processed_at": week_ratings[week_key].get("processed_at"),
        "games": week_ratings[week_key].get("games", 0),
        "ratings": result,
    }


@router.post("/walters-ratings/update")
def walters_ratings_update(week: int = Query(..., ge=1, le=18)):
    """Trigger weekly Walters recalculation. Runs engine script synchronously."""
    if not ENGINE_SCRIPT.exists():
        raise HTTPException(status_code=503, detail="Engine script not found")
    try:
        result = subprocess.run(
            [sys.executable, str(ENGINE_SCRIPT), "--week", str(week)],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            logger.error("Engine error: %s", result.stderr)
            raise HTTPException(status_code=500, detail=f"Engine failed: {result.stderr[:300]}")
        return {"ok": True, "week": week, "output": result.stdout[-500:]}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Engine timed out")


def _tier(rating: float) -> str:
    if rating >= 8:   return "ELITE"
    if rating >= 4:   return "CONTENDER"
    if rating >= 0:   return "AVERAGE"
    if rating >= -4:  return "BELOW"
    return "BOTTOM"
