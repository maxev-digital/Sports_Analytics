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
    # Environment (computed from nfl_games)
    ot_rate: float | None = None
    dome_pct: float | None = None
    primetime_pct: float | None = None
    avg_temp: float | None = None
    avg_wind: float | None = None
    div_game_pct: float | None = None
    # Penalty (from nfl_referee_penalties — None until scraper runs)
    flags_per_game: float | None = None
    yards_per_game: float | None = None
    home_bias: float | None = None


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
