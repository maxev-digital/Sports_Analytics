"""
MLB Batter vs Pitcher (BvP) Matchup Service
Fetches career and current-season batter-vs-pitcher matchup data from
Baseball Savant's Statcast search endpoint (free, no key required).

BvP is the sharpest single signal tier in MLB modeling. A lineup full of batters
who historically destroy a specific pitcher's repertoire changes expected run
scoring by 0.5-1.0 runs even controlling for overall team quality.

Key metrics:
  - Career wOBA vs this specific pitcher
  - K% vs this pitcher (does the pitcher miss bats on this lineup?)
  - Hard hit % (barrel + solid contact)
  - Sample size (PA count — thin samples < 15 PA are noisy)

Exported API
------------
get_lineup_bvp_summary(lineup_names, pitcher_name, pitcher_id=None) -> dict
get_bvp_for_game(home_lineup, away_lineup, home_pitcher_id, away_pitcher_id) -> dict
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

MLB_API = "https://statsapi.mlb.com/api/v1"
SAVANT_SEARCH_URL = "https://baseballsavant.mlb.com/statcast_search/csv"

_CACHE_TTL_SECONDS = 43_200  # 12 hours
_cache: dict[str, tuple[datetime, dict]] = {}

# Minimum PA for BvP stats to be signal-grade (below this = noise)
MIN_PA_FOR_SIGNAL = 12


async def get_lineup_bvp_summary(
    lineup_names: list[str],
    pitcher_name: str,
    pitcher_id: Optional[int] = None,
    season: Optional[str] = None,
) -> dict:
    """
    Aggregates BvP matchup data for a lineup vs a specific pitcher.

    Result keys:
      weighted_woba      float | None  -- PA-weighted average career wOBA vs this SP
      avg_k_pct          float | None  -- average K% of lineup vs this SP
      avg_hard_hit_pct   float | None  -- average hard hit % vs this SP
      signal_pa          int           -- total PA with reliable sample
      matchup_lean       str           -- "OFFENSE" | "PITCHER" | "NEUTRAL"
      bvp_note           str           -- narrative for agent context
      batter_matchups    list          -- per-batter breakdown
    """
    ssn = season or str(date.today().year)
    cache_key = f"bvp:{pitcher_name}:{','.join(sorted(lineup_names))}:{ssn}"
    now = datetime.now()

    if cache_key in _cache:
        cached_at, data = _cache[cache_key]
        if (now - cached_at).total_seconds() < _CACHE_TTL_SECONDS:
            return data

    # Resolve pitcher ID if not provided
    if not pitcher_id:
        pitcher_id = await _lookup_player_id(pitcher_name)

    if not pitcher_id:
        result = _no_data_result(pitcher_name)
        _cache[cache_key] = (now, result)
        return result

    # Fetch BvP for each batter in parallel
    import asyncio
    tasks = [
        asyncio.create_task(_fetch_batter_vs_pitcher(name, pitcher_id))
        for name in lineup_names[:9]  # cap at 9 (batting order)
    ]
    batter_results = await asyncio.gather(*tasks)

    # Aggregate
    total_numerator = 0.0
    total_pa = 0
    signal_pa = 0
    k_pa = 0
    k_total = 0
    hh_pa = 0
    hh_total = 0
    batter_matchups = []

    for matchup in batter_results:
        if not matchup or "error" in matchup:
            continue
        pa = matchup.get("pa", 0)
        woba = matchup.get("woba")
        k_pct = matchup.get("k_pct")
        hh_pct = matchup.get("hard_hit_pct")

        batter_matchups.append(matchup)

        if pa >= MIN_PA_FOR_SIGNAL and woba is not None:
            total_numerator += woba * pa
            total_pa += pa
            signal_pa += pa

        if pa >= MIN_PA_FOR_SIGNAL and k_pct is not None:
            k_total += k_pct * pa
            k_pa += pa

        if pa >= MIN_PA_FOR_SIGNAL and hh_pct is not None:
            hh_total += hh_pct * pa
            hh_pa += pa

    weighted_woba = round(total_numerator / total_pa, 3) if total_pa > 0 else None
    avg_k_pct = round(k_total / k_pa, 3) if k_pa > 0 else None
    avg_hh_pct = round(hh_total / hh_pa, 3) if hh_pa > 0 else None

    # Classify matchup lean
    matchup_lean = "NEUTRAL"
    bvp_note = f"BvP vs {pitcher_name}: insufficient sample (< {MIN_PA_FOR_SIGNAL} PA)"

    if weighted_woba is not None and signal_pa >= MIN_PA_FOR_SIGNAL:
        if weighted_woba >= 0.360:
            matchup_lean = "OFFENSE"
            bvp_note = (
                f"Lineup has historically hit {pitcher_name} well "
                f"(career wOBA .{int(weighted_woba*1000):03d}, {signal_pa} PA)"
            )
        elif weighted_woba <= 0.290:
            matchup_lean = "PITCHER"
            bvp_note = (
                f"{pitcher_name} has historically dominated this lineup "
                f"(career wOBA .{int(weighted_woba*1000):03d}, {signal_pa} PA)"
            )
        else:
            bvp_note = (
                f"Neutral BvP history vs {pitcher_name} "
                f"(career wOBA .{int(weighted_woba*1000):03d}, {signal_pa} PA)"
            )

    result = {
        "pitcher": pitcher_name,
        "pitcher_id": pitcher_id,
        "weighted_woba": weighted_woba,
        "avg_k_pct": avg_k_pct,
        "avg_hard_hit_pct": avg_hh_pct,
        "signal_pa": signal_pa,
        "matchup_lean": matchup_lean,
        "bvp_note": bvp_note,
        "batter_matchups": batter_matchups,
        "data_source": "Baseball Savant Statcast",
    }

    _cache[cache_key] = (now, result)
    return result


async def _fetch_batter_vs_pitcher(batter_name: str, pitcher_id: int) -> dict:
    """
    Fetches career Statcast BvP data for a specific batter vs pitcher.
    Uses Baseball Savant statcast_search CSV endpoint.
    """
    batter_id = await _lookup_player_id(batter_name)
    if not batter_id:
        return {"batter": batter_name, "error": "Player ID not found", "pa": 0}

    params = {
        "player_type": "batter",
        "player_id": batter_id,
        "pitcher_throws": "",
        "pitcher_id": pitcher_id,
        "game_type": "R",
        "csv": "true",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                SAVANT_SEARCH_URL, params=params,
                headers={"User-Agent": "Mozilla/5.0"},
            )

        if r.status_code != 200 or not r.text.strip():
            return {"batter": batter_name, "pa": 0}

        import io
        import pandas as pd
        df = pd.read_csv(io.StringIO(r.text))

        if df.empty:
            return {"batter": batter_name, "pa": 0}

        # Compute metrics from pitch-level data
        pa = int(df["at_bat_number"].nunique()) if "at_bat_number" in df.columns else 0
        k_events = df[df.get("events", pd.Series()).isin(["strikeout", "strikeout_double_play"])]
        k_count = len(k_events["at_bat_number"].unique()) if "at_bat_number" in k_events.columns else 0

        # Hard hit: launch_speed >= 95 mph
        hh_col = next((c for c in df.columns if "launch_speed" in c), None)
        hh_count = 0
        hh_pa_count = 0
        if hh_col:
            balls_in_play = df[pd.to_numeric(df[hh_col], errors="coerce").notna()]
            hh_count = (pd.to_numeric(balls_in_play[hh_col], errors="coerce") >= 95).sum()
            hh_pa_count = len(balls_in_play)

        # wOBA — use estimated_woba_using_speedangle if available, else compute
        woba_col = next(
            (c for c in df.columns if "estimated_woba" in c or "woba_value" in c), None
        )
        woba = None
        if woba_col and pa > 0:
            vals = pd.to_numeric(df[woba_col], errors="coerce").dropna()
            if not vals.empty:
                woba = round(float(vals.mean()), 3)

        return {
            "batter": batter_name,
            "batter_id": batter_id,
            "pa": pa,
            "woba": woba,
            "k_pct": round(k_count / pa, 3) if pa > 0 else None,
            "hard_hit_pct": round(hh_count / hh_pa_count, 3) if hh_pa_count > 0 else None,
            "signal_grade": "HIGH" if pa >= 20 else "MEDIUM" if pa >= 12 else "LOW",
        }
    except Exception as exc:
        logger.debug("BvP fetch failed batter=%s pitcher=%s: %s", batter_name, pitcher_id, exc)
        return {"batter": batter_name, "pa": 0, "error": str(exc)}


async def _lookup_player_id(player_name: str) -> Optional[int]:
    """Looks up MLB player ID by name from MLB Stats API people search."""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                f"{MLB_API}/people/search",
                params={"names": player_name, "sport.id": 1},
            )
            people = r.json().get("people", [])
            if people:
                return int(people[0]["id"])
    except Exception as exc:
        logger.debug("Player ID lookup failed for %s: %s", player_name, exc)
    return None


def _no_data_result(pitcher_name: str) -> dict:
    return {
        "pitcher": pitcher_name,
        "pitcher_id": None,
        "weighted_woba": None,
        "avg_k_pct": None,
        "avg_hard_hit_pct": None,
        "signal_pa": 0,
        "matchup_lean": "NEUTRAL",
        "bvp_note": f"BvP data unavailable for {pitcher_name}",
        "batter_matchups": [],
        "data_source": "none",
    }


async def get_bvp_for_game(
    home_lineup: list[str],
    away_lineup: list[str],
    home_pitcher_name: str,
    away_pitcher_name: str,
    home_pitcher_id: Optional[int] = None,
    away_pitcher_id: Optional[int] = None,
) -> dict:
    """
    Convenience wrapper: fetches both sides of a game's BvP matchups in parallel.
    Returns home_offense_bvp (away lineup vs home SP) and away_offense_bvp.
    """
    import asyncio
    # Away offense vs home pitcher, Home offense vs away pitcher
    away_bvp_task = asyncio.create_task(
        get_lineup_bvp_summary(away_lineup, home_pitcher_name, home_pitcher_id)
    )
    home_bvp_task = asyncio.create_task(
        get_lineup_bvp_summary(home_lineup, away_pitcher_name, away_pitcher_id)
    )
    away_offense_bvp, home_offense_bvp = await asyncio.gather(away_bvp_task, home_bvp_task)

    return {
        "home_offense_bvp": home_offense_bvp,
        "away_offense_bvp": away_offense_bvp,
    }
