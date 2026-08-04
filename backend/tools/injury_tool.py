"""
Injury report tool — fetches current player injury designations via ESPN public API.

Endpoint: site.api.espn.com/apis/site/v2/sports/{sport_path}/injuries
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Map platform sport keys to ESPN API path segments
_ESPN_SPORT_PATHS: dict[str, str] = {
    "nba":   "basketball/nba",
    "nfl":   "football/nfl",
    "mlb":   "baseball/mlb",
    "nhl":   "hockey/nhl",
    "ncaaf": "football/college-football",
    "ncaab": "basketball/mens-college-basketball",
    "wnba":  "basketball/wnba",
}

_ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
_TIMEOUT = 5.0


def get_injury_report(team_name: str, sport: str) -> dict[str, Any]:
    """
    Fetch injury designations for a team from ESPN.

    Args:
        team_name: Full or partial team name (e.g. "Boston Celtics", "Celtics").
        sport: Platform sport key (e.g. "nba", "nfl").

    Returns:
        {
          "team": str,
          "sport": str,
          "injuries": [{"player": str, "position": str, "status": str, "type": str}],
          "source": "espn"
        }
        Returns empty injuries list on any error (fail open).
    """
    sport_key = sport.lower()
    sport_path = _ESPN_SPORT_PATHS.get(sport_key)
    if not sport_path:
        logger.warning("injury_tool: unsupported sport %r", sport)
        return {"team": team_name, "sport": sport, "injuries": [], "source": "unsupported"}

    url = f"{_ESPN_BASE}/{sport_path}/injuries"
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.warning("injury_tool HTTP error: %s", exc)
        return {"team": team_name, "sport": sport, "injuries": [], "source": "espn_error"}
    except Exception as exc:
        logger.error("injury_tool unexpected error: %s", exc)
        return {"team": team_name, "sport": sport, "injuries": [], "source": "error"}

    # ESPN injuries endpoint returns a list of team injury blocks
    search = team_name.lower()
    injuries: list[dict[str, str]] = []

    items = data if isinstance(data, list) else data.get("injuries", [])
    for item in items:
        # ESPN structure: item["team"]["displayName"] + item["injuries"]
        team_info = item.get("team", {})
        display_name = (team_info.get("displayName") or team_info.get("name") or "").lower()
        abbreviation = (team_info.get("abbreviation") or "").lower()

        if search not in display_name and search not in abbreviation:
            # Partial match on last word (e.g. "Celtics" matches "Boston Celtics")
            last_word = search.split()[-1] if search else ""
            if last_word and last_word not in display_name:
                continue

        for inj in item.get("injuries", []):
            athlete = inj.get("athlete", {})
            injuries.append({
                "player":   athlete.get("displayName") or athlete.get("fullName") or "Unknown",
                "position": (athlete.get("position") or {}).get("abbreviation") or "",
                "status":   inj.get("status") or "",
                "type":     inj.get("type") or "",
            })

    return {
        "team": team_name,
        "sport": sport,
        "injuries": injuries[:12],
        "source": "espn",
    }
