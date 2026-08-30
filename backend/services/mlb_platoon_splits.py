"""
MLB Platoon Splits Service
Fetches team batting splits vs left-handed and right-handed pitchers
from the MLB Stats API (free, no key required).

This is the primary signal for run-scoring prediction when the opposing
starter's handedness is known — wOBA vs RHP can differ 30-40 points
from wOBA vs LHP for platoon-heavy lineups.

Exported API
------------
get_platoon_splits(team_name, season=None) -> dict
get_platoon_splits_for_matchup(home_team, away_team, away_sp_hand, home_sp_hand) -> dict
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

import httpx

from services.mlb_bullpen import TEAM_IDS

logger = logging.getLogger(__name__)

MLB_API = "https://statsapi.mlb.com/api/v1"
_CACHE_TTL_SECONDS = 21_600  # 6 hours — platoon splits don't shift day to day

_cache: dict[str, tuple[datetime, dict]] = {}


async def get_platoon_splits(team_name: str, season: Optional[str] = None) -> dict:
    """
    Returns batting splits for a team vs LHP and vs RHP.

    Result keys:
      vs_lhp_woba    float | None   -- team wOBA vs left-handed starters
      vs_rhp_woba    float | None   -- team wOBA vs right-handed starters
      vs_lhp_ops     float | None   -- OPS vs LHP
      vs_rhp_ops     float | None   -- OPS vs RHP
      vs_lhp_avg     float | None   -- BA vs LHP
      vs_rhp_avg     float | None   -- BA vs RHP
      platoon_gap    float | None   -- abs(vs_rhp_woba - vs_lhp_woba); > 0.030 = significant
      stronger_vs    str            -- "LHP" | "RHP" | "neutral"
    """
    ssn = season or str(date.today().year)
    cache_key = f"platoon:{team_name}:{ssn}"
    now = datetime.now()

    if cache_key in _cache:
        cached_at, data = _cache[cache_key]
        if (now - cached_at).total_seconds() < _CACHE_TTL_SECONDS:
            return data

    team_id = TEAM_IDS.get(team_name)
    if not team_id:
        return {"error": f"Unknown team: {team_name}", "team": team_name}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            result = await _fetch_splits(client, team_id, team_name, ssn)
    except Exception as exc:
        logger.error("Platoon splits fetch failed for %s: %s", team_name, exc)
        result = {
            "team": team_name, "error": str(exc),
            "vs_lhp_woba": None, "vs_rhp_woba": None,
            "vs_lhp_ops": None, "vs_rhp_ops": None,
            "platoon_gap": None, "stronger_vs": "neutral",
        }

    _cache[cache_key] = (now, result)
    return result


async def _fetch_splits(
    client: httpx.AsyncClient, team_id: int, team_name: str, season: str
) -> dict:
    vs_lhp: dict = {}
    vs_rhp: dict = {}

    for hand, store in [("L", vs_lhp), ("R", vs_rhp)]:
        try:
            r = await client.get(
                f"{MLB_API}/teams/{team_id}/stats",
                params={
                    "stats": "vsHandedness",
                    "pitcherHand": hand,
                    "season": season,
                    "group": "hitting",
                },
            )
            splits = r.json().get("stats", [{}])[0].get("splits", [])
            if splits:
                stat = splits[0].get("stat", {})
                store.update({
                    "avg": _safe_float(stat.get("avg")),
                    "obp": _safe_float(stat.get("obp")),
                    "slg": _safe_float(stat.get("slg")),
                    "ops": _safe_float(stat.get("ops")),
                    "woba": _safe_float(stat.get("wOba") or stat.get("woba")),
                    "k_pct": _k_pct(stat),
                    "bb_pct": _bb_pct(stat),
                    "pa": int(stat.get("plateAppearances", 0)),
                })
        except Exception as exc:
            logger.debug("Hand=%s split fetch error for team %s: %s", hand, team_id, exc)

    lhp_woba = vs_lhp.get("woba")
    rhp_woba = vs_rhp.get("woba")
    platoon_gap = round(abs(rhp_woba - lhp_woba), 3) if rhp_woba and lhp_woba else None

    if rhp_woba and lhp_woba:
        stronger_vs = "RHP" if rhp_woba > lhp_woba else "LHP"
    else:
        stronger_vs = "neutral"

    return {
        "team": team_name,
        "vs_lhp_woba": lhp_woba,
        "vs_rhp_woba": rhp_woba,
        "vs_lhp_ops": vs_lhp.get("ops"),
        "vs_rhp_ops": vs_rhp.get("ops"),
        "vs_lhp_avg": vs_lhp.get("avg"),
        "vs_rhp_avg": vs_rhp.get("avg"),
        "vs_lhp_k_pct": vs_lhp.get("k_pct"),
        "vs_rhp_k_pct": vs_rhp.get("k_pct"),
        "vs_lhp_pa": vs_lhp.get("pa", 0),
        "vs_rhp_pa": vs_rhp.get("pa", 0),
        "platoon_gap": platoon_gap,
        "stronger_vs": stronger_vs,
        "data_source": "MLB Stats API",
    }


async def get_platoon_splits_for_matchup(
    home_team: str,
    away_team: str,
    away_sp_hand: str,   # "L" or "R" — away starter's throwing hand
    home_sp_hand: str,   # "L" or "R" — home starter's throwing hand
    season: Optional[str] = None,
) -> dict:
    """
    Returns the relevant platoon split for each side of a matchup.
    home_offense_woba: home team's wOBA vs away starter's hand
    away_offense_woba: away team's wOBA vs home starter's hand
    """
    home_splits, away_splits = await _parallel_splits(home_team, away_team, season)

    away_hand_key = "vs_lhp_woba" if away_sp_hand == "L" else "vs_rhp_woba"
    home_hand_key = "vs_lhp_woba" if home_sp_hand == "L" else "vs_rhp_woba"

    return {
        "home_offense_woba": home_splits.get(away_hand_key),
        "away_offense_woba": away_splits.get(home_hand_key),
        "home_stronger_vs": home_splits.get("stronger_vs"),
        "away_stronger_vs": away_splits.get("stronger_vs"),
        "home_platoon_gap": home_splits.get("platoon_gap"),
        "away_platoon_gap": away_splits.get("platoon_gap"),
        "home_splits": home_splits,
        "away_splits": away_splits,
    }


async def _parallel_splits(
    home_team: str, away_team: str, season: Optional[str]
) -> tuple[dict, dict]:
    import asyncio
    home_task = asyncio.create_task(get_platoon_splits(home_team, season))
    away_task = asyncio.create_task(get_platoon_splits(away_team, season))
    home_splits, away_splits = await asyncio.gather(home_task, away_task)
    return home_splits, away_splits


def _safe_float(v) -> Optional[float]:
    try:
        return round(float(v), 3) if v is not None else None
    except (ValueError, TypeError):
        return None


def _k_pct(stat: dict) -> Optional[float]:
    pa = int(stat.get("plateAppearances", 0))
    k = int(stat.get("strikeOuts", 0))
    return round(k / pa, 3) if pa > 0 else None


def _bb_pct(stat: dict) -> Optional[float]:
    pa = int(stat.get("plateAppearances", 0))
    bb = int(stat.get("baseOnBalls", 0))
    return round(bb / pa, 3) if pa > 0 else None
