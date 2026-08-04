"""
Pydantic response models for NFL Referee Tracking endpoints.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

TendencyLabel = Literal["OVER_HEAVY", "UNDER_HEAVY", "HOME_FRIENDLY", "NEUTRAL"]


class RefereeSummary(BaseModel):
    name: str
    games: int
    avg_total: float | None
    over_rate: float | None
    under_rate: float | None
    home_cover_pct: float | None
    tendency: TendencyLabel


class RefereeSeasonSplit(BaseModel):
    season: int
    games: int
    avg_total: float | None
    over_rate: float | None
    under_rate: float | None
    home_cover_pct: float | None


class RefereeProfile(BaseModel):
    name: str
    summary: RefereeSummary
    season_splits: list[RefereeSeasonSplit]


class RefereeListResponse(BaseModel):
    count: int
    referees: list[RefereeSummary]
