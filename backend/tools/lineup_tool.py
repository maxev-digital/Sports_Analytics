"""
Starting lineup tool — fetches confirmed starters via ESPN public API.

Critical for:
  - NBA: load management decisions
  - MLB: confirmed starting pitcher
  - NFL: key skill position starters
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

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


def get_starting_lineup(team_name: str, sport: str, game_date: str | None = None) -> dict[str, Any]:
    """
    Fetch probable/confirmed starters for a team from ESPN.

    Args:
        team_name: Full or partial team name.
        sport: Platform sport key (e.g. "nba", "mlb").
        game_date: Optional ISO date string (YYYY-MM-DD) to scope to a specific day.

    Returns:
        {
          "team": str,
          "sport": str,
          "starters": [{"player": str, "position": str, "status": str}],
          "source": "espn"
        }
        Returns empty starters list on any error (fail open).
    """
    sport_key = sport.lower()
    sport_path = _ESPN_SPORT_PATHS.get(sport_key)
    if not sport_path:
        return {"team": team_name, "sport": sport, "starters": [], "source": "unsupported"}

    # ESPN scoreboard API includes lineup info per event
    params: dict[str, str] = {}
    if game_date:
        params["dates"] = game_date.replace("-", "")

    url = f"{_ESPN_BASE}/{sport_path}/scoreboard"
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.warning("lineup_tool HTTP error: %s", exc)
        return {"team": team_name, "sport": sport, "starters": [], "source": "espn_error"}
    except Exception as exc:
        logger.error("lineup_tool unexpected error: %s", exc)
        return {"team": team_name, "sport": sport, "starters": [], "source": "error"}

    search = team_name.lower()
    starters: list[dict[str, str]] = []

    for event in data.get("events", []):
        for competition in event.get("competitions", []):
            for competitor in competition.get("competitors", []):
                tm = competitor.get("team", {})
                display = (tm.get("displayName") or tm.get("name") or "").lower()
                abbrev = (tm.get("abbreviation") or "").lower()
                last_word = search.split()[-1] if search else ""

                if search not in display and search not in abbrev:
                    if not last_word or last_word not in display:
                        continue

                # Probable pitcher (MLB)
                pp = competitor.get("probables") or []
                for prob in pp:
                    athlete = prob.get("athlete", {})
                    pos = (athlete.get("position") or {}).get("abbreviation") or ""
                    starters.append({
                        "player":   athlete.get("displayName") or "Unknown",
                        "position": pos,
                        "status":   "probable starter",
                    })

                # Roster / lineup (NBA/NFL/NHL)
                roster = competitor.get("roster") or []
                for player in roster[:12]:
                    athlete = player.get("athlete", {})
                    pos = (athlete.get("position") or {}).get("abbreviation") or ""
                    starter = player.get("starter", False)
                    if starter or sport_key == "mlb":
                        starters.append({
                            "player":   athlete.get("displayName") or "Unknown",
                            "position": pos,
                            "status":   "starter" if starter else "active",
                        })

    return {
        "team": team_name,
        "sport": sport,
        "starters": starters[:15],
        "source": "espn",
    }
