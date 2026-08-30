"""
MLB Rolling Stats Service
Fetches team-level rolling form metrics and regression indicators:
  - Recent wOBA last 10 games (hot/cold streak vs season average)
  - Season xwOBA and BABIP per team (regression signals from Baseball Savant)
  - Team K% and BB% (discipline profile)
  - Run differential vs Pythagorean expectation (luck regression flag)

Data sources:
  - Baseball Savant team expected statistics leaderboard (free CSV endpoint)
  - MLB Stats API game log for rolling 10-game wOBA approximation

Exported API
------------
get_team_rolling_stats(team_name, season=None) -> dict
get_savant_team_batting(season=None) -> dict   -- all teams, cached
"""
from __future__ import annotations

import io
import logging
from datetime import date, datetime, timedelta
from typing import Optional

import httpx
import pandas as pd

from services.mlb_bullpen import TEAM_IDS

logger = logging.getLogger(__name__)

MLB_API = "https://statsapi.mlb.com/api/v1"
SAVANT_BATTING_URL = (
    "https://baseballsavant.mlb.com/leaderboard/expected_statistics"
    "?type=batter&year={season}&position=&team=&min=50&csv=true"
)

_CACHE_TTL_SAVANT = 43_200   # 12 hours — Savant updates daily
_CACHE_TTL_ROLLING = 10_800  # 3 hours — recent form can shift game to game

_savant_cache: dict[str, tuple[datetime, dict]] = {}
_rolling_cache: dict[str, tuple[datetime, dict]] = {}

# MLB team abbreviation → full name map (for Savant CSV team column)
_ABBR_TO_NAME: dict[str, str] = {
    "ARI": "Arizona Diamondbacks", "ATL": "Atlanta Braves",
    "BAL": "Baltimore Orioles",    "BOS": "Boston Red Sox",
    "CHC": "Chicago Cubs",         "CWS": "Chicago White Sox",
    "CIN": "Cincinnati Reds",      "CLE": "Cleveland Guardians",
    "COL": "Colorado Rockies",     "DET": "Detroit Tigers",
    "HOU": "Houston Astros",       "KC": "Kansas City Royals",
    "LAA": "Los Angeles Angels",   "LAD": "Los Angeles Dodgers",
    "MIA": "Miami Marlins",        "MIL": "Milwaukee Brewers",
    "MIN": "Minnesota Twins",      "NYM": "New York Mets",
    "NYY": "New York Yankees",     "OAK": "Oakland Athletics",
    "PHI": "Philadelphia Phillies","PIT": "Pittsburgh Pirates",
    "SD": "San Diego Padres",      "SF": "San Francisco Giants",
    "SEA": "Seattle Mariners",     "STL": "St. Louis Cardinals",
    "TB": "Tampa Bay Rays",        "TEX": "Texas Rangers",
    "TOR": "Toronto Blue Jays",    "WSH": "Washington Nationals",
}


async def get_team_rolling_stats(team_name: str, season: Optional[str] = None) -> dict:
    """
    Returns rolling batting stats + regression indicators for a team.

    Result keys:
      season_woba        float | None  -- full-season wOBA
      season_xwoba       float | None  -- expected wOBA (strips BABIP luck)
      woba_vs_xwoba      float | None  -- positive = over-performing (regression risk)
      babip              float | None  -- BABIP (>.320 = likely regression coming)
      k_pct              float | None  -- strikeout rate
      bb_pct             float | None  -- walk rate
      rolling_10g_woba   float | None  -- approximate wOBA last 10 games
      rolling_form       str           -- "HOT" | "COLD" | "NEUTRAL"
      pythagorean_diff   float | None  -- run diff: actual wins vs expected (luck)
    """
    ssn = season or str(date.today().year)
    cache_key = f"rolling:{team_name}:{ssn}"
    now = datetime.now()

    if cache_key in _rolling_cache:
        cached_at, data = _rolling_cache[cache_key]
        if (now - cached_at).total_seconds() < _CACHE_TTL_ROLLING:
            return data

    team_id = TEAM_IDS.get(team_name)
    rolling_woba = None
    pythagorean_diff = None
    season_stats: dict = {}

    if team_id:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                rolling_woba = await _get_rolling_woba(client, team_id, ssn)
                pythagorean_diff = await _get_pythagorean_diff(client, team_id, ssn)
                season_stats = await _get_season_hitting(client, team_id, ssn)
        except Exception as exc:
            logger.error("Rolling stats fetch failed for %s: %s", team_name, exc)

    season_woba = season_stats.get("woba")          # computed from season game log
    season_babip = season_stats.get("babip")
    season_k_pct = season_stats.get("k_pct")
    season_bb_pct = season_stats.get("bb_pct")
    season_ops = season_stats.get("ops")

    # Rolling form: compare last 10 games wOBA to season wOBA
    rolling_form = "NEUTRAL"
    if rolling_woba and season_woba:
        diff = rolling_woba - season_woba
        if diff >= 0.015:
            rolling_form = "HOT"
        elif diff <= -0.015:
            rolling_form = "COLD"

    result = {
        "team": team_name,
        "season_ops": season_ops,
        "season_woba": season_woba,
        "season_xwoba": None,       # requires Savant player lookup — future enhancement
        "woba_vs_xwoba": None,
        "babip": season_babip,
        "k_pct": season_k_pct,
        "bb_pct": season_bb_pct,
        "rolling_10g_woba": rolling_woba,
        "rolling_form": rolling_form,
        "pythagorean_diff": pythagorean_diff,
        "over_performing": False,   # set True if xwOBA wired; requires Savant player data
        "data_source": "MLB Stats API",
    }

    _rolling_cache[cache_key] = (now, result)
    return result


async def get_savant_team_batting(season: Optional[str] = None) -> dict:
    """
    Fetches and aggregates Baseball Savant expected batting stats per team.
    Returns dict keyed by full team name.

    Caches for 12 hours (Savant updates once per day).
    """
    ssn = season or str(date.today().year)
    cache_key = f"savant_batting:{ssn}"
    now = datetime.now()

    if cache_key in _savant_cache:
        cached_at, data = _savant_cache[cache_key]
        if (now - cached_at).total_seconds() < _CACHE_TTL_SAVANT:
            return data

    try:
        url = SAVANT_BATTING_URL.format(season=ssn)
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]

        # Aggregate per team: weighted averages by PA
        result = _aggregate_by_team(df)
    except Exception as exc:
        logger.error("Savant team batting fetch failed: %s", exc)
        result = {}

    _savant_cache[cache_key] = (now, result)
    return result


def _aggregate_by_team(df: pd.DataFrame) -> dict:
    """
    Groups player-level Savant data by team abbreviation, weights by PA.
    Returns {team_full_name: {woba, xwoba, babip, k_pct, bb_pct, ...}}
    """
    team_col = next((c for c in df.columns if "team" in c), None)
    if not team_col:
        return {}

    out: dict = {}
    for abbr, group in df.groupby(team_col):
        team_name = _ABBR_TO_NAME.get(str(abbr).upper(), str(abbr))
        pa_col = next((c for c in group.columns if c in ("pa", "plate_appearances")), None)
        pa = group[pa_col].fillna(1).astype(float) if pa_col else pd.Series([1.0] * len(group))
        pa_total = pa.sum()

        def wavg(col: str) -> Optional[float]:
            if col not in group.columns:
                return None
            vals = pd.to_numeric(group[col], errors="coerce")
            valid = vals.notna()
            if not valid.any():
                return None
            return round(float((vals[valid] * pa[valid]).sum() / pa[valid].sum()), 3)

        def col_pct(col: str) -> Optional[float]:
            """Handle percentage columns that may be stored as 0-100 or 0-1."""
            v = wavg(col)
            if v is None:
                return None
            return round(v / 100, 3) if v > 1.0 else v

        # Locate column names with fuzzy matching
        woba_col = _find_col(group, ["woba", "est_woba"])
        xwoba_col = _find_col(group, ["est_woba", "xwoba"])
        babip_col = _find_col(group, ["babip"])
        k_col = _find_col(group, ["k_percent", "k%", "strikeout_percent"])
        bb_col = _find_col(group, ["bb_percent", "bb%", "walk_percent"])

        out[team_name] = {
            "woba": wavg(woba_col) if woba_col else None,
            "xwoba": wavg(xwoba_col) if xwoba_col else None,
            "babip": wavg(babip_col) if babip_col else None,
            "k_pct": col_pct(k_col) if k_col else None,
            "bb_pct": col_pct(bb_col) if bb_col else None,
            "pa_total": int(pa_total),
        }

    return out


async def _get_rolling_woba(
    client: httpx.AsyncClient, team_id: int, season: str
) -> Optional[float]:
    """
    Approximates rolling wOBA over last 10 games from team game log batting stats.
    wOBA ≈ (0.69*BB + 0.89*1B + 1.27*2B + 1.62*3B + 2.10*HR) / (AB + BB + SF + HBP)
    """
    try:
        r = await client.get(
            f"{MLB_API}/teams/{team_id}/stats",
            params={"stats": "gameLog", "season": season, "group": "hitting"},
        )
        splits = r.json().get("stats", [{}])[0].get("splits", [])
        last10 = splits[-10:] if len(splits) >= 10 else splits
        if not last10:
            return None

        total_numerator = 0.0
        total_denom = 0

        for s in last10:
            stat = s.get("stat", {})
            h = int(stat.get("hits", 0))
            doubles = int(stat.get("doubles", 0))
            triples = int(stat.get("triples", 0))
            hr = int(stat.get("homeRuns", 0))
            bb = int(stat.get("baseOnBalls", 0))
            hbp = int(stat.get("hitByPitch", 0))
            ab = int(stat.get("atBats", 0))
            sf = int(stat.get("sacFlies", 0))

            singles = h - doubles - triples - hr
            numerator = (0.69 * bb + 0.89 * singles + 1.27 * doubles
                         + 1.62 * triples + 2.10 * hr + 0.72 * hbp)
            denom = ab + bb + sf + hbp
            total_numerator += numerator
            total_denom += denom

        return round(total_numerator / total_denom, 3) if total_denom > 0 else None
    except Exception as exc:
        logger.debug("Rolling wOBA fetch failed: %s", exc)
        return None


async def _get_pythagorean_diff(
    client: httpx.AsyncClient, team_id: int, season: str
) -> Optional[float]:
    """
    Computes actual win% minus Pythagorean expected win% (RS^2 / (RS^2 + RA^2)).
    Positive = team winning more than expected (regression risk).
    """
    try:
        r = await client.get(
            f"{MLB_API}/teams/{team_id}/stats",
            params={"stats": "season", "season": season, "group": "hitting"},
        )
        splits = r.json().get("stats", [{}])[0].get("splits", [])
        if not splits:
            return None
        stat = splits[0].get("stat", {})
        rs = int(stat.get("runs", 0))

        r2 = await client.get(
            f"{MLB_API}/teams/{team_id}/stats",
            params={"stats": "season", "season": season, "group": "pitching"},
        )
        splits2 = r2.json().get("stats", [{}])[0].get("splits", [])
        if not splits2:
            return None
        stat2 = splits2[0].get("stat", {})
        ra = int(stat2.get("runs", 0))

        if rs <= 0 or ra <= 0:
            return None

        pyth_win = rs ** 2 / (rs ** 2 + ra ** 2)

        # Get actual record
        r3 = await client.get(f"{MLB_API}/teams/{team_id}", params={"season": season})
        teams = r3.json().get("teams", [{}])
        record = teams[0].get("record", {}) if teams else {}
        wins = int(record.get("wins", 0))
        losses = int(record.get("losses", 0))
        games = wins + losses
        actual_win = wins / games if games > 0 else 0.5

        return round(actual_win - pyth_win, 3)
    except Exception as exc:
        logger.debug("Pythagorean diff fetch failed: %s", exc)
        return None


async def _get_season_hitting(
    client: httpx.AsyncClient, team_id: int, season: str
) -> dict:
    """
    Fetches team season hitting stats from MLB Stats API.
    Returns BABIP, OPS, K%, BB%, and approximate wOBA from counting stats.
    """
    try:
        r = await client.get(
            f"{MLB_API}/teams/{team_id}/stats",
            params={"stats": "season", "season": season, "group": "hitting"},
        )
        splits = r.json().get("stats", [{}])[0].get("splits", [])
        if not splits:
            return {}
        stat = splits[0].get("stat", {})
        pa = int(stat.get("plateAppearances", 0))
        k = int(stat.get("strikeOuts", 0))
        bb = int(stat.get("baseOnBalls", 0))
        h = int(stat.get("hits", 0))
        doubles = int(stat.get("doubles", 0))
        triples = int(stat.get("triples", 0))
        hr = int(stat.get("homeRuns", 0))
        hbp = int(stat.get("hitByPitch", 0))
        ab = int(stat.get("atBats", 0))
        sf = int(stat.get("sacFlies", 0))
        singles = h - doubles - triples - hr

        # Compute wOBA from counting stats (2026 weights)
        denom = ab + bb + sf + hbp
        woba = None
        if denom > 0:
            numerator = (0.69 * bb + 0.89 * singles + 1.27 * doubles
                         + 1.62 * triples + 2.10 * hr + 0.72 * hbp)
            woba = round(numerator / denom, 3)

        return {
            "ops": _sf(stat.get("ops")),
            "babip": _sf(stat.get("babip")),
            "k_pct": round(k / pa, 3) if pa > 0 else None,
            "bb_pct": round(bb / pa, 3) if pa > 0 else None,
            "woba": woba,
        }
    except Exception as exc:
        logger.debug("Season hitting fetch failed team_id=%s: %s", team_id, exc)
        return {}


def _sf(v) -> Optional[float]:
    try:
        return round(float(v), 3) if v is not None else None
    except (ValueError, TypeError):
        return None


def _find_col(df: pd.DataFrame, candidates: list) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    # Partial match
    for c in candidates:
        match = next((col for col in df.columns if c in col), None)
        if match:
            return match
    return None
