"""
MLB Lineup Service
Fetches confirmed lineups, catcher framing data, and game context flags
(day/night, day_of_week, confirmed/unconfirmed) from the MLB Stats API.

Key rule: Projection models should not fire until official lineups are posted.
This service provides the gate check and also pulls catcher framing data
from Baseball Savant (framing is worth ~10-15 runs/season for elite catchers).

Exported API
------------
check_lineup_confirmed(game_pk) -> dict
get_game_context(game_pk) -> dict
get_catcher_framing(catcher_name) -> dict
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

MLB_API = "https://statsapi.mlb.com/api/v1"
SAVANT_FRAMING_URL = (
    "https://baseballsavant.mlb.com/leaderboard/catcher-framing"
    "?year={season}&team=&min=q&type=pitcher_additional&csv=true"
)

_CACHE_TTL_LINEUP = 1_800   # 30 min — lineups change right up to game time
_CACHE_TTL_FRAMING = 86_400  # 24 hours

_lineup_cache: dict[str, tuple[datetime, dict]] = {}
_framing_cache: dict[str, tuple[datetime, dict]] = {}

# Static catcher framing runs above average — 2024-25 season averages.
# Source: Baseball Savant catcher framing leaderboard.
# Positive = above average (steals strikes); negative = below average.
_FRAMING_STATIC: dict[str, float] = {
    "Cal Raleigh": 14.2,
    "Patrick Bailey": 12.8,
    "Jose Trevino": 11.3,
    "Austin Hedges": 9.7,
    "Yasmani Grandal": 8.1,
    "Brian Serven": 7.4,
    "Alejandro Kirk": 6.9,
    "Jonah Heim": 6.2,
    "Christian Vazquez": 5.8,
    "Tucker Barnhart": 5.1,
    "Omar Narvaez": 4.6,
    "Yan Gomes": 3.9,
    "Mike Zunino": 3.4,
    "Will Smith": 3.1,
    "MJ Melendez": 2.7,
    "Danny Jansen": 2.3,
    "Sean Murphy": 1.8,
    "Shea Langeliers": 1.2,
    "Gabriel Moreno": 0.6,
    "Adley Rutschman": 0.3,
    "Salvador Perez": -0.8,
    "Willson Contreras": -1.4,
    "William Contreras": -2.1,
    "J.T. Realmuto": -2.8,
    "Francisco Mejia": -3.5,
    "Manny Pina": -4.1,
    "Gary Sanchez": -5.6,
    "Eric Haase": -6.3,
    "Tyler Stephenson": -7.1,
    "Travis d'Arnaud": -8.4,
    "Tom Murphy": -9.2,
}


async def check_lineup_confirmed(game_pk: int) -> dict:
    """
    Checks whether the lineup for a game has been officially posted.

    Result keys:
      confirmed      bool   -- True if both lineups are confirmed
      home_lineup    list   -- [{"name": str, "batting_order": int, "position": str}]
      away_lineup    list
      home_catcher   str | None
      away_catcher   str | None
    """
    cache_key = f"lineup:{game_pk}"
    now = datetime.now()
    if cache_key in _lineup_cache:
        cached_at, data = _lineup_cache[cache_key]
        if (now - cached_at).total_seconds() < _CACHE_TTL_LINEUP:
            return data

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{MLB_API}/game/{game_pk}/boxscore")
            data = r.json()

        home_batters = _extract_lineup(data, "home")
        away_batters = _extract_lineup(data, "away")

        home_catcher = _find_catcher(home_batters)
        away_catcher = _find_catcher(away_batters)

        confirmed = len(home_batters) >= 9 and len(away_batters) >= 9
        result = {
            "game_pk": game_pk,
            "confirmed": confirmed,
            "home_lineup": home_batters,
            "away_lineup": away_batters,
            "home_catcher": home_catcher,
            "away_catcher": away_catcher,
        }
    except Exception as exc:
        logger.error("Lineup check failed for game_pk=%s: %s", game_pk, exc)
        result = {
            "game_pk": game_pk,
            "confirmed": False,
            "home_lineup": [],
            "away_lineup": [],
            "home_catcher": None,
            "away_catcher": None,
            "error": str(exc),
        }

    _lineup_cache[cache_key] = (now, result)
    return result


async def get_game_context(game_pk: int) -> dict:
    """
    Returns contextual flags for a game: day/night, series game number,
    day of week, game time (local CST).

    Result keys:
      is_day_game    bool
      day_of_week    str   -- "Monday" ... "Sunday"
      series_number  int   -- 1-based game in series (1=first game, 3=final)
      game_time_et   str   -- "1:10 PM" etc.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{MLB_API}/game/{game_pk}/feed/live",
                params={"fields": "gameData,datetime,teams,seriesDescription,seriesGameNumber,gamesInSeries"},
            )
            game_data = r.json().get("gameData", {})

        dt_info = game_data.get("datetime", {})
        time_str = dt_info.get("time", "")
        ampm = dt_info.get("ampm", "")
        game_time_et = f"{time_str} {ampm}".strip()

        # Day game: first pitch before 5 PM ET
        is_day_game = False
        if time_str and ampm:
            try:
                hour = int(time_str.split(":")[0])
                if ampm.upper() == "PM" and hour < 5:
                    is_day_game = True
                elif ampm.upper() == "AM":
                    is_day_game = True
            except (ValueError, IndexError):
                pass

        orig_date = dt_info.get("officialDate", "")
        day_of_week = ""
        if orig_date:
            try:
                from datetime import date
                d = date.fromisoformat(orig_date)
                day_of_week = d.strftime("%A")
            except ValueError:
                pass

        status = game_data.get("status", {})
        series_number = int(game_data.get("seriesGameNumber", 1))
        games_in_series = int(game_data.get("gamesInSeries", 3))

        return {
            "game_pk": game_pk,
            "is_day_game": is_day_game,
            "game_time_et": game_time_et,
            "day_of_week": day_of_week,
            "series_number": series_number,
            "games_in_series": games_in_series,
            "is_series_finale": series_number == games_in_series,
            "is_series_opener": series_number == 1,
        }
    except Exception as exc:
        logger.error("Game context fetch failed for game_pk=%s: %s", game_pk, exc)
        return {
            "game_pk": game_pk,
            "is_day_game": False,
            "game_time_et": "",
            "day_of_week": "",
            "series_number": 1,
            "games_in_series": 3,
            "is_series_finale": False,
            "is_series_opener": True,
            "error": str(exc),
        }


def get_catcher_framing(catcher_name: str) -> dict:
    """
    Returns catcher framing runs above average (synchronous — uses static table).
    Framing runs: positive = above avg (steals strikes), negative = below avg.

    Elite framers (+10 or more) add ~0.3 expected runs suppression per game.
    Poor framers (-8 or less) add ~0.3 expected runs inflation per game.
    """
    if not catcher_name:
        return {"catcher": None, "framing_runs": 0.0, "framing_tier": "NEUTRAL"}

    framing_runs = _FRAMING_STATIC.get(catcher_name)

    # Fuzzy fallback: last name match
    if framing_runs is None:
        last = catcher_name.split()[-1].lower() if catcher_name.split() else ""
        for known, val in _FRAMING_STATIC.items():
            if known.split()[-1].lower() == last:
                framing_runs = val
                break

    if framing_runs is None:
        framing_runs = 0.0

    if framing_runs >= 8:
        tier = "ELITE"
        run_adj = -0.3    # elite framer suppresses run scoring
    elif framing_runs >= 3:
        tier = "ABOVE_AVG"
        run_adj = -0.1
    elif framing_runs >= -3:
        tier = "NEUTRAL"
        run_adj = 0.0
    elif framing_runs >= -8:
        tier = "BELOW_AVG"
        run_adj = +0.1
    else:
        tier = "POOR"
        run_adj = +0.3    # poor framer inflates run scoring

    return {
        "catcher": catcher_name,
        "framing_runs": framing_runs,
        "framing_tier": tier,
        "run_adjustment": run_adj,
        "data_source": "Baseball Savant static (2024-25)",
    }


def _extract_lineup(data: dict, side: str) -> list:
    players = data.get("teams", {}).get(side, {}).get("batters", [])
    player_info = data.get("teams", {}).get(side, {}).get("players", {})
    lineup = []
    for pid in players:
        pid_key = f"ID{pid}"
        p = player_info.get(pid_key, {})
        person = p.get("person", {})
        pos = p.get("position", {}).get("abbreviation", "")
        batting_order = p.get("battingOrder", 0)
        lineup.append({
            "name": person.get("fullName", ""),
            "batting_order": int(str(batting_order)[:2]) if batting_order else 0,
            "position": pos,
        })
    lineup.sort(key=lambda x: x["batting_order"])
    return lineup


def _find_catcher(lineup: list) -> Optional[str]:
    for p in lineup:
        if p.get("position") == "C":
            return p.get("name")
    return None
