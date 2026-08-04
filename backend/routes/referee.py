"""
NFL Referee Tracking routes.

GET /api/f5/referees?sort=games&min_games=10
GET /api/f5/referees/{name}
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from models.referee import RefereeListResponse, RefereeProfile
from services.referee_stats import get_referee_list, get_referee_profile

router = APIRouter()
logger = logging.getLogger(__name__)

VALID_SORTS = {"games", "avg_total", "over_rate", "home_cover_pct"}


@router.get("/referees", response_model=RefereeListResponse)
def list_referees(
    sort: str = Query("games", description="games|avg_total|over_rate|home_cover_pct"),
    min_games: int = Query(10, ge=1, le=100, description="Minimum games to appear in list"),
) -> RefereeListResponse:
    if sort not in VALID_SORTS:
        sort = "games"
    result = get_referee_list(sort=sort, min_games=min_games)
    if result.count == 0:
        logger.info("Referee list returned 0 results — DB may need rebuild with referee column")
    return result


@router.get("/referees/{name}", response_model=RefereeProfile)
def get_referee(name: str) -> RefereeProfile:
    decoded = name.replace("-", " ").replace("_", " ").strip()
    profile = get_referee_profile(decoded)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for referee '{decoded}'. Ensure DB was rebuilt with referee column.",
        )
    return profile
