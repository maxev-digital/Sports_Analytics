"""
Weather tool — fetches game-day forecasts via Open-Meteo (free, no API key required).

Used for outdoor sports (NFL, MLB) where weather meaningfully impacts totals.

Known stadium coordinates:
  NFL stadiums — all included
  MLB stadiums — all included (excludes dome stadiums)
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT = 5.0

# Approximate coordinates for major outdoor NFL + MLB stadiums
# Dome/retractable-roof venues excluded (weather is irrelevant)
_STADIUM_COORDS: dict[str, tuple[float, float]] = {
    # NFL outdoor
    "buffalo bills": (42.774, -78.787),
    "new england patriots": (42.091, -71.264),
    "new york giants": (40.814, -74.074),
    "new york jets": (40.814, -74.074),
    "philadelphia eagles": (39.901, -75.168),
    "pittsburgh steelers": (40.446, -80.016),
    "cleveland browns": (41.506, -81.700),
    "baltimore ravens": (39.278, -76.623),
    "cincinnati bengals": (39.095, -84.516),
    "chicago bears": (41.862, -87.617),
    "green bay packers": (44.501, -88.062),
    "minnesota vikings": (44.974, -93.258),
    "detroit lions": (42.340, -83.045),
    "denver broncos": (39.744, -105.020),
    "kansas city chiefs": (39.049, -94.484),
    "seattle seahawks": (47.595, -122.332),
    "san francisco 49ers": (37.403, -121.970),
    "los angeles rams": (33.953, -118.339),
    "los angeles chargers": (33.953, -118.339),
    "tennessee titans": (36.166, -86.771),
    "jacksonville jaguars": (30.324, -81.638),
    "miami dolphins": (25.958, -80.239),
    "tampa bay buccaneers": (27.976, -82.503),
    "carolina panthers": (35.225, -80.853),
    "atlanta falcons": (33.755, -84.401),
    "washington commanders": (38.908, -76.865),
    "arizona cardinals": (33.528, -112.263),
    # MLB outdoor (excludes Tropicana, T-Mobile, Globe Life, Minute Maid, Rogers, Chase, etc.)
    "boston red sox": (42.347, -71.097),
    "chicago cubs": (41.948, -87.655),
    "chicago white sox": (41.830, -87.634),
    "new york yankees": (40.829, -73.926),
    "new york mets": (40.757, -73.846),
    "san francisco giants": (37.779, -122.389),
    "oakland athletics": (37.752, -122.201),
    "los angeles dodgers": (34.074, -118.240),
    "pittsburgh pirates": (40.447, -80.006),
    "cincinnati reds": (39.097, -84.507),
    "cleveland guardians": (41.496, -81.685),
    "baltimore orioles": (39.284, -76.622),
    "washington nationals": (38.873, -77.008),
    "detroit tigers": (42.339, -83.049),
    "colorado rockies": (39.756, -104.994),
    "seattle mariners": (47.591, -122.333),
    "kansas city royals": (39.052, -94.481),
    "toronto blue jays": (43.641, -79.389),
    "philadelphia phillies": (39.906, -75.166),
    "milwaukee brewers": (43.028, -87.971),
    "minnesota twins": (44.982, -93.278),
    "texas rangers": (32.751, -97.083),
}


def _find_coords(team_name: str) -> tuple[float, float] | None:
    search = team_name.lower()
    # Exact match
    if search in _STADIUM_COORDS:
        return _STADIUM_COORDS[search]
    # Partial match on last word (e.g. "Chiefs" matches "Kansas City Chiefs")
    for key, coords in _STADIUM_COORDS.items():
        if search in key or key.split()[-1] in search:
            return coords
    return None


def get_weather(home_team: str, game_date: str) -> dict[str, Any]:
    """
    Fetch weather forecast for a home team's stadium on game day.

    Args:
        home_team: Home team name (used to look up stadium coordinates).
        game_date: ISO date string (YYYY-MM-DD).

    Returns:
        {
          "team": str,
          "date": str,
          "temp_f": float,
          "wind_mph": float,
          "precipitation_chance": int,
          "conditions": str,
          "is_dome": bool,
          "source": "open-meteo"
        }
        Returns is_dome=True if stadium not found (treat as irrelevant).
        Returns is_dome=False with zeroed data on any API error.
    """
    coords = _find_coords(home_team)
    if not coords:
        return {
            "team": home_team, "date": game_date,
            "temp_f": 0.0, "wind_mph": 0.0,
            "precipitation_chance": 0, "conditions": "dome/unknown",
            "is_dome": True, "source": "not_found",
        }

    lat, lon = coords
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,wind_speed_10m_max,precipitation_probability_max,weathercode",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "timezone": "America/Chicago",
        "start_date": game_date,
        "end_date": game_date,
    }

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(_OPEN_METEO_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.warning("weather_tool HTTP error: %s", exc)
        return {
            "team": home_team, "date": game_date,
            "temp_f": 0.0, "wind_mph": 0.0,
            "precipitation_chance": 0, "conditions": "unavailable",
            "is_dome": False, "source": "error",
        }
    except Exception as exc:
        logger.error("weather_tool unexpected error: %s", exc)
        return {
            "team": home_team, "date": game_date,
            "temp_f": 0.0, "wind_mph": 0.0,
            "precipitation_chance": 0, "conditions": "error",
            "is_dome": False, "source": "error",
        }

    daily = data.get("daily", {})
    temps = daily.get("temperature_2m_max", [0])
    winds = daily.get("wind_speed_10m_max", [0])
    precip = daily.get("precipitation_probability_max", [0])
    codes = daily.get("weathercode", [0])

    temp_f = float(temps[0]) if temps else 0.0
    wind_mph = float(winds[0]) if winds else 0.0
    precip_pct = int(precip[0]) if precip else 0
    code = int(codes[0]) if codes else 0

    # WMO weather code → readable condition
    if code == 0:
        cond = "Clear"
    elif code <= 3:
        cond = "Partly Cloudy"
    elif code <= 49:
        cond = "Foggy"
    elif code <= 67:
        cond = "Rain"
    elif code <= 77:
        cond = "Snow"
    elif code <= 82:
        cond = "Showers"
    elif code <= 99:
        cond = "Thunderstorm"
    else:
        cond = "Unknown"

    return {
        "team": home_team,
        "date": game_date,
        "temp_f": round(temp_f, 1),
        "wind_mph": round(wind_mph, 1),
        "precipitation_chance": precip_pct,
        "conditions": cond,
        "is_dome": False,
        "source": "open-meteo",
    }
