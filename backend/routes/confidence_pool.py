"""
NFL Confidence Pool — /api/f5/confidence-pool

GET /api/f5/confidence-pool?week=1
Returns all games for the requested week with model picks, confidence ranks (1-16),
power rating differentials, ATS trends, and situational flags.
"""
from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

router = APIRouter()
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "f5_backtest"

# Situational adjustments (points toward confidence score)
SITUATIONAL_RULES = [
    # (flag_key, flag_label, condition_fn, confidence_delta)
    # Applied in score_game() — condition receives home_ats, away_ats, rating_diff
]


def _load_json(name: str) -> Any:
    p = DATA_DIR / name
    if p.exists():
        return json.loads(p.read_text())
    return {}


def _ats_lookup(ats_data: list[dict]) -> dict[str, dict]:
    return {r["team"]: r for r in ats_data}


def _walters_lookup(ratings_data: dict) -> dict[str, dict]:
    return {r["team"]: r for r in ratings_data.get("current", [])}


def _team_abbr_to_name_map(schedule_week: list[dict]) -> dict[str, str]:
    """Build abbr→full name map from the schedule entries."""
    m: dict[str, str] = {}
    for g in schedule_week:
        m[g["home"]] = g.get("home_name", g["home"])
        m[g["away"]] = g.get("away_name", g["away"])
    return m


def _situational_flags(
    home: str, away: str, game_date: str,
    home_ats: dict, away_ats: dict,
    rating_diff: float,
) -> list[str]:
    flags: list[str] = []

    # Home dog spot (home team has lower power rating)
    if rating_diff < -3:
        flags.append("Home dog spot")

    # Big fav ATS risk (favorites historically underperform)
    if rating_diff > 7:
        home_fav_pct = home_ats.get("fav_cover_pct", 50)
        if home_fav_pct < 45:
            flags.append("Heavy fav — ATS risk")

    # Dog ATS edge (away team covers as dog)
    away_dog_pct = away_ats.get("dog_cover_pct", 50)
    if rating_diff > 3 and away_dog_pct and float(away_dog_pct) > 60:
        flags.append(f"Away dog covers {away_dog_pct:.0f}%")

    # Try to detect primetime from date string (Thu/Mon/Sun night)
    try:
        d = date.fromisoformat(game_date[:10])
        if d.weekday() == 3:  # Thursday
            flags.append("Short week — Thu game")
        elif d.weekday() == 0:  # Monday
            flags.append("Primetime — MNF")
    except Exception:
        pass

    return flags


def _confidence_score(
    rating_diff: float,
    home_ats_pct: float,
    away_ats_pct: float,
    flags: list[str],
) -> float:
    """
    Produce a raw confidence score for the MODEL's preferred pick.
    Higher = more confident. Scaled to produce clean 1-16 rankings.
    """
    # Base: absolute power rating advantage (bigger gap = more confident)
    base = abs(rating_diff) * 4.0

    # ATS edge for the predicted side
    if rating_diff >= 0:
        # Model favors home — use home ATS%
        ats_boost = (home_ats_pct - 50) * 0.4
    else:
        # Model favors away — use away dog ATS%
        away_dog_pct = away_ats_pct  # using overall for now
        ats_boost = (away_dog_pct - 50) * 0.4

    # Situational discounts
    flag_adj = 0.0
    if "Heavy fav — ATS risk" in flags:
        flag_adj -= 5.0
    if "Home dog spot" in flags:
        flag_adj += 3.0  # contrarian value
    if "Short week — Thu game" in flags:
        flag_adj -= 2.0

    return max(0.0, base + ats_boost + flag_adj)


def _model_pick(home: str, away: str, rating_diff: float) -> dict[str, str]:
    """Return model's preferred side and brief reasoning."""
    if rating_diff >= 0:
        return {
            "pick": home,
            "side": "HOME",
            "reasoning": f"{home} rated {rating_diff:+.1f} pts above {away} by Walters method",
        }
    else:
        return {
            "pick": away,
            "side": "AWAY",
            "reasoning": f"{away} rated {abs(rating_diff):.1f} pts above {home} by Walters method",
        }


@router.get("/confidence-pool")
def confidence_pool(week: int = Query(default=1, ge=1, le=18)):
    schedule = _load_json("nfl_schedule_2026.json")
    ratings_data = _load_json("nfl_power_ratings.json")
    ats_2025 = _load_json("nfl_ats_2025.json")
    ats_2024 = _load_json("nfl_ats_2024.json")

    week_games: list[dict] = schedule.get(str(week), [])
    walters = _walters_lookup(ratings_data)

    ats25 = _ats_lookup(ats_2025 if isinstance(ats_2025, list) else [])
    ats24 = _ats_lookup(ats_2024 if isinstance(ats_2024, list) else [])

    def get_ats(team_abbr: str) -> dict:
        # Try abbr first, then full name fallback
        return ats25.get(team_abbr) or ats24.get(team_abbr) or {}

    def get_rating(team_abbr: str) -> float:
        entry = walters.get(team_abbr)
        return float(entry["rating"]) if entry else 0.0

    results: list[dict] = []
    for game in week_games:
        home = game["home"]
        away = game["away"]
        game_date = game.get("date", "")

        home_r = get_rating(home)
        away_r = get_rating(away)
        # Positive = home team advantage, negative = away team advantage
        # Add 2.5 pts home field per Walters method
        rating_diff = (home_r - away_r) + 2.5

        home_ats = get_ats(home)
        away_ats = get_ats(away)

        home_ats_pct = float(home_ats.get("ats_cover_pct") or 50)
        away_ats_pct = float(away_ats.get("ats_cover_pct") or 50)

        flags = _situational_flags(home, away, game_date, home_ats, away_ats, rating_diff)
        score = _confidence_score(rating_diff, home_ats_pct, away_ats_pct, flags)
        pick = _model_pick(home, away, rating_diff)

        results.append({
            "home": home,
            "away": away,
            "home_name": game.get("home_name", home),
            "away_name": game.get("away_name", away),
            "date": game_date,
            "home_rating": home_r,
            "away_rating": away_r,
            "rating_diff": round(rating_diff, 2),
            "home_ats_pct": home_ats_pct,
            "away_ats_pct": away_ats_pct,
            "home_ats_record": home_ats.get("ats_record", "—"),
            "away_ats_record": away_ats.get("ats_record", "—"),
            "situational_flags": flags,
            "raw_score": round(score, 2),
            "model_pick": pick,
        })

    # Sort by raw_score descending → assign confidence points 16 down to 1
    results.sort(key=lambda x: x["raw_score"], reverse=True)
    total = len(results)
    for i, game in enumerate(results):
        game["confidence_points"] = total - i  # 16 for top pick, 1 for bottom

    # Season week metadata
    first_date = results[0]["date"] if results else ""
    last_date = results[-1]["date"] if results else ""

    return {
        "week": week,
        "game_count": total,
        "week_start": first_date,
        "week_end": last_date,
        "method": "Walters power rating differential + ATS trend + situational flags",
        "games": results,
    }
