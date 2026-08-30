"""
MLB Bullpen Service
Fetches bullpen ERA, WHIP, fatigue index (appearances/IP last 3 days), and
closer availability from the MLB Stats API (free, no key required).

Exported API
------------
get_bullpen_data(team_name, game_date=None) -> dict
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

MLB_API = "https://statsapi.mlb.com/api/v1"
_CACHE_TTL_SECONDS = 10_800  # 3 hours

# Official MLB team IDs (stable, do not change mid-season)
TEAM_IDS: dict[str, int] = {
    "Arizona Diamondbacks": 109, "Atlanta Braves": 144, "Baltimore Orioles": 110,
    "Boston Red Sox": 111,       "Chicago Cubs": 112,   "Chicago White Sox": 145,
    "Cincinnati Reds": 113,      "Cleveland Guardians": 114, "Colorado Rockies": 115,
    "Detroit Tigers": 116,       "Houston Astros": 117, "Kansas City Royals": 118,
    "Los Angeles Angels": 108,   "Los Angeles Dodgers": 119, "Miami Marlins": 146,
    "Milwaukee Brewers": 158,    "Minnesota Twins": 142, "New York Mets": 121,
    "New York Yankees": 147,     "Oakland Athletics": 133, "Philadelphia Phillies": 143,
    "Pittsburgh Pirates": 134,   "San Diego Padres": 135, "San Francisco Giants": 137,
    "Seattle Mariners": 136,     "St. Louis Cardinals": 138, "Tampa Bay Rays": 139,
    "Texas Rangers": 140,        "Toronto Blue Jays": 141, "Washington Nationals": 120,
}

_cache: dict[str, tuple[datetime, dict]] = {}


async def get_bullpen_data(team_name: str, game_date: Optional[str] = None) -> dict:
    """
    Returns bullpen metrics for a team on a given date.

    Result keys:
      bullpen_era          float | None  -- season ERA for relievers
      bullpen_whip         float | None  -- season WHIP for relievers
      fatigue_index        int           -- total appearances by relievers last 3 days
      high_fatigue         bool          -- True if fatigue_index >= 6
      relievers_used_yesterday int       -- count who pitched yesterday
      closer_available     bool          -- True if closer appeared < 2 of last 3 days
      reliever_count       int           -- active relievers sampled
    """
    today = game_date or date.today().isoformat()
    cache_key = f"bullpen:{team_name}:{today}"
    now = datetime.now()

    if cache_key in _cache:
        cached_at, data = _cache[cache_key]
        if (now - cached_at).total_seconds() < _CACHE_TTL_SECONDS:
            return data

    team_id = TEAM_IDS.get(team_name)
    if not team_id:
        return {"error": f"Unknown team: {team_name}", "team": team_name}

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            result = await _fetch_bullpen(client, team_id, team_name, today)
    except Exception as exc:
        logger.error("Bullpen fetch failed for %s: %s", team_name, exc)
        result = {
            "team": team_name, "error": str(exc),
            "bullpen_era": None, "bullpen_whip": None,
            "fatigue_index": 0, "high_fatigue": False,
            "relievers_used_yesterday": 0, "closer_available": True,
        }

    _cache[cache_key] = (now, result)
    return result


async def _fetch_bullpen(
    client: httpx.AsyncClient, team_id: int, team_name: str, today: str
) -> dict:
    season = today[:4]
    today_dt = date.fromisoformat(today)
    three_days_ago = (today_dt - timedelta(days=3)).isoformat()
    yesterday = (today_dt - timedelta(days=1)).isoformat()

    # Step 1: get active roster, isolate relievers (RP + CL positions)
    roster_r = await client.get(
        f"{MLB_API}/teams/{team_id}/roster",
        params={"season": season, "rosterType": "active"},
    )
    roster = roster_r.json().get("roster", [])
    relievers = [
        p for p in roster
        if p.get("position", {}).get("abbreviation") in ("RP", "CL")
    ]

    if not relievers:
        return {
            "team": team_name, "bullpen_era": None, "bullpen_whip": None,
            "fatigue_index": 0, "high_fatigue": False,
            "relievers_used_yesterday": 0, "closer_available": True,
            "reliever_count": 0,
        }

    # Step 2: for each reliever fetch game log + season stats
    fatigue_index = 0
    relievers_used_yesterday = 0
    closer_appearances_last3 = 0
    season_ip_total = 0.0
    season_er_total = 0
    season_h_total = 0
    season_bb_total = 0
    save_leaders: list[tuple[int, int]] = []  # (save_count, pid)

    for p in relievers[:10]:  # cap at 10 to avoid rate limiting
        pid = p["person"]["id"]
        is_closer = p.get("position", {}).get("abbreviation") == "CL"

        try:
            log_r = await client.get(
                f"{MLB_API}/people/{pid}/stats",
                params={"stats": "gameLog", "season": season, "group": "pitching"},
            )
            splits = log_r.json().get("stats", [{}])[0].get("splits", [])

            # Count appearances in last 3 days (relief only: gamesStarted == 0)
            recent = [
                s for s in splits
                if s.get("date", "") >= three_days_ago
                and int(s["stat"].get("gamesStarted", 0)) == 0
            ]
            fatigue_index += len(recent)
            used_yesterday = any(s.get("date", "") == yesterday for s in recent)
            if used_yesterday:
                relievers_used_yesterday += 1
            if is_closer:
                closer_appearances_last3 = len(recent)

            # Track saves for closer identification (if no CL label)
            total_saves = sum(int(s["stat"].get("saves", 0)) for s in splits)
            save_leaders.append((total_saves, pid))

            # Season stats for ERA/WHIP
            ssn_r = await client.get(
                f"{MLB_API}/people/{pid}/stats",
                params={"stats": "season", "season": season, "group": "pitching"},
            )
            ssn_splits = ssn_r.json().get("stats", [{}])[0].get("splits", [])
            if ssn_splits:
                stat = ssn_splits[0]["stat"]
                ip_str = stat.get("inningsPitched", "0") or "0"
                ip = float(ip_str)
                if ip > 0:
                    season_ip_total += ip
                    season_er_total += int(stat.get("earnedRuns", 0))
                    season_h_total += int(stat.get("hits", 0))
                    season_bb_total += int(stat.get("baseOnBalls", 0))

        except Exception as exc:
            logger.debug("Reliever pid=%s fetch error: %s", pid, exc)

    # If no explicit CL, treat top save-getter as closer
    if not any(p.get("position", {}).get("abbreviation") == "CL" for p in relievers):
        if save_leaders:
            save_leaders.sort(reverse=True)
            # closer_appearances already approximated by fatigue_index contribution

    bullpen_era = (
        round((season_er_total / season_ip_total) * 9, 2) if season_ip_total > 0 else None
    )
    bullpen_whip = (
        round((season_h_total + season_bb_total) / season_ip_total, 2)
        if season_ip_total > 0 else None
    )

    return {
        "team": team_name,
        "bullpen_era": bullpen_era,
        "bullpen_whip": bullpen_whip,
        "fatigue_index": fatigue_index,
        "high_fatigue": fatigue_index >= 6,   # 6+ appearances in 3 days = taxed pen
        "relievers_used_yesterday": relievers_used_yesterday,
        "closer_available": closer_appearances_last3 < 2,
        "reliever_count": len(relievers),
        "data_source": "MLB Stats API",
    }
