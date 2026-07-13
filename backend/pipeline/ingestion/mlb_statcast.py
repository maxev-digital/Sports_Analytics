"""
MLB Statcast data ingestion from Baseball Savant.

Primary path:  pybaseball library (if installed) — confirms the library is
               present and usable, then fetches via the Savant CSV endpoint
               which exposes expected-statistics unavailable in pybaseball's
               convenience wrappers.
Fallback path: direct HTTP GET to the Baseball Savant leaderboard CSV
               endpoint — used automatically if pybaseball is not installed
               or raises an import-time exception.

Exported API
------------
fetch_pitching_statcast(season) -> pd.DataFrame
fetch_batting_statcast(season)  -> pd.DataFrame
get_pitcher_stats(name, season) -> dict | None
save_statcast_to_db(df, stat_type)
"""

from __future__ import annotations

import io
import json
import logging
from typing import Optional

import pandas as pd
import requests

from pipeline.config import CST, now_cst
from pipeline.db.connection import execute_many, execute_write

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional pybaseball import
# ---------------------------------------------------------------------------
try:
    import pybaseball  # noqa: F401 — imported to confirm availability

    _PYBASEBALL_AVAILABLE = True
    logger.debug("pybaseball is available.")
except ImportError:
    _PYBASEBALL_AVAILABLE = False
    logger.info(
        "pybaseball is not installed; using Baseball Savant HTTP fallback."
    )

# ---------------------------------------------------------------------------
# Baseball Savant CSV endpoint templates
# ---------------------------------------------------------------------------
_SAVANT_BASE = "https://baseballsavant.mlb.com/leaderboard/expected_statistics"

SAVANT_PITCHING_URL: str = (
    _SAVANT_BASE + "?type=pitcher&year={season}&position=&team=&min=50&csv=true"
)
SAVANT_BATTING_URL: str = (
    _SAVANT_BASE + "?type=batter&year={season}&position=&team=&min=50&csv=true"
)

# ---------------------------------------------------------------------------
# Expected column lists
# ---------------------------------------------------------------------------
# 2026 Baseball Savant simplified column names.
# The name column is "last_name,_first_name" (comma in header) — renamed
# to "player_name" immediately after fetching.
PITCHING_FIELDS: list[str] = [
    "player_id",
    "last_name,_first_name",  # renamed to player_name post-fetch
    "pa",
    "era",
    "xera",
    "era_minus_xera_diff",
    "ba",
    "est_ba",
    "est_ba_minus_ba_diff",
    "slg",
    "est_slg",
    "est_slg_minus_slg_diff",
    "woba",
    "est_woba",
    "est_woba_minus_woba_diff",
]

BATTING_FIELDS: list[str] = [
    "player_id",
    "last_name,_first_name",  # renamed to player_name post-fetch
    "pa",
    "ba",
    "est_ba",
    "est_ba_minus_ba_diff",
    "slg",
    "est_slg",
    "est_slg_minus_slg_diff",
    "woba",
    "est_woba",
    "est_woba_minus_woba_diff",
]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_SAVANT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; sports-analytics-pipeline/1.0; "
        "+https://github.com/maxev-digital)"
    )
}


def _current_season() -> int:
    """Return the current MLB season year (CST-aware)."""
    return now_cst().year


# ---------------------------------------------------------------------------
# Player -> team roster map (MLB Stats API)
# ---------------------------------------------------------------------------
# Baseball Savant's leaderboard CSV has no team column at all in the 2026 API
# (confirmed absent, not just blank) - so anything needing team affiliation
# (e.g. mlb_features.py's team-level wOBA-gap feature) has no source of truth
# for it without pulling from elsewhere. The official, free, unauthenticated
# MLB Stats API provides exactly this, keyed in the same "Last, First" name
# format Savant uses (lastFirstName), so it merges on directly with no name
# reformatting needed.

_MLB_STATSAPI_TEAMS_URL = "https://statsapi.mlb.com/api/v1/teams"
_MLB_STATSAPI_PLAYERS_URL = "https://statsapi.mlb.com/api/v1/sports/1/players"

_team_map_cache: dict[int, dict[str, str]] = {}  # season -> {player_name: team_abbr}


def fetch_player_team_map(season: Optional[int] = None) -> dict[str, str]:
    """
    Build a ``{"Last, First": team_abbreviation}`` map for the given season
    via the official MLB Stats API. Cached per season in-process - rosters
    don't change meaningfully within a single ingestion run, and this avoids
    two extra HTTP calls on every feature-build.

    Returns an empty dict (never raises) if the API is unreachable, so
    callers degrade to "no team info" rather than crashing ingestion.
    """
    if season is None:
        season = _current_season()
    if season in _team_map_cache:
        return _team_map_cache[season]

    team_map: dict[str, str] = {}
    try:
        teams_resp = requests.get(
            _MLB_STATSAPI_TEAMS_URL, params={"sportId": 1}, timeout=20
        )
        teams_resp.raise_for_status()
        id_to_abbr = {
            t["id"]: t.get("abbreviation", "")
            for t in teams_resp.json().get("teams", [])
        }

        players_resp = requests.get(
            _MLB_STATSAPI_PLAYERS_URL, params={"season": season}, timeout=20
        )
        players_resp.raise_for_status()
        for p in players_resp.json().get("people", []):
            name = p.get("lastFirstName")
            team_id = (p.get("currentTeam") or {}).get("id")
            abbr = id_to_abbr.get(team_id)
            if name and abbr:
                team_map[name] = abbr
    except (requests.RequestException, ValueError, KeyError) as exc:
        logger.warning("Failed to fetch MLB player-team roster map: %s", exc)
        return {}

    logger.info(
        "fetch_player_team_map: resolved %d player->team mappings for season %d.",
        len(team_map), season,
    )
    _team_map_cache[season] = team_map
    return team_map


def _fetch_savant_csv(url: str, fields: list[str]) -> pd.DataFrame:
    """
    Download a Baseball Savant leaderboard CSV and return a cleaned DataFrame.

    Steps
    -----
    1. GET the URL with a browser-like User-Agent (Savant blocks bare requests).
    2. Parse the raw CSV text.
    3. Normalise column names (strip whitespace, lowercase, spaces → underscores).
    4. Keep only requested *fields* that are present; log missing ones.
    5. Coerce every non-name column to numeric; drop all-NaN rows.

    Args:
        url:    Fully-formed Baseball Savant CSV endpoint URL.
        fields: Ordered list of column names to extract.

    Returns:
        DataFrame containing available columns from *fields*, with numerics
        coerced and fully-NaN rows dropped.

    Raises:
        requests.HTTPError: On non-2xx HTTP responses.
    """
    resp = requests.get(url, headers=_SAVANT_HEADERS, timeout=30)
    resp.raise_for_status()

    df = pd.read_csv(io.StringIO(resp.text), low_memory=False)

    # Normalise column names
    df.columns = [
        col.strip().lower().replace(" ", "_") for col in df.columns
    ]

    # Filter to requested fields; warn on gaps
    available = [f for f in fields if f in df.columns]
    missing = set(fields) - set(available)
    if missing:
        logger.warning(
            "Baseball Savant CSV is missing expected columns: %s — "
            "they will be absent from the returned DataFrame.",
            sorted(missing),
        )

    df = df[available].copy()

    # Rename the 2026 name column to a consistent "player_name"
    if "last_name,_first_name" in df.columns:
        df.rename(columns={"last_name,_first_name": "player_name"}, inplace=True)

    # Coerce numeric columns (everything except the name string)
    _str_cols = {"player_name", "team"}
    for col in df.columns:
        if col not in _str_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows that are entirely NaN (e.g. trailing blank lines in CSV)
    df.dropna(how="all", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


# ---------------------------------------------------------------------------
# Public fetch functions
# ---------------------------------------------------------------------------


def fetch_pitching_statcast(season: Optional[int] = None) -> pd.DataFrame:
    """
    Fetch MLB pitching expected-statistics from Baseball Savant.

    Uses pybaseball if installed (confirms the library is available and
    importable); in either case the actual data is pulled from the
    Baseball Savant CSV endpoint which exposes the full xERA / xFIP suite.

    Args:
        season: MLB season year.  Defaults to the current year (CST).

    Returns:
        DataFrame with columns from PITCHING_FIELDS (subset available in CSV)
        plus ``season`` and ``stat_type`` annotation columns.

    Raises:
        requests.HTTPError: On non-2xx responses from Baseball Savant.
    """
    if season is None:
        season = _current_season()

    if _PYBASEBALL_AVAILABLE:
        logger.debug(
            "pybaseball confirmed available; fetching pitching Statcast "
            "via Baseball Savant CSV for %d.",
            season,
        )
    else:
        logger.debug(
            "pybaseball not installed; fetching pitching Statcast via "
            "direct HTTP for %d.",
            season,
        )

    url = SAVANT_PITCHING_URL.format(season=season)
    logger.info("Fetching pitching Statcast: season=%d url=%s", season, url)

    df = _fetch_savant_csv(url, PITCHING_FIELDS)
    df["season"] = season
    df["stat_type"] = "pitching"

    logger.info(
        "Fetched %d pitching rows for season %d.", len(df), season
    )
    return df


def fetch_batting_statcast(season: Optional[int] = None) -> pd.DataFrame:
    """
    Fetch MLB batting expected-statistics from Baseball Savant.

    Args:
        season: MLB season year.  Defaults to the current year (CST).

    Returns:
        DataFrame with columns from BATTING_FIELDS (subset available in CSV)
        plus ``season`` and ``stat_type`` annotation columns.

    Raises:
        requests.HTTPError: On non-2xx responses from Baseball Savant.
    """
    if season is None:
        season = _current_season()

    url = SAVANT_BATTING_URL.format(season=season)
    logger.info("Fetching batting Statcast: season=%d url=%s", season, url)

    df = _fetch_savant_csv(url, BATTING_FIELDS)
    df["season"] = season
    df["stat_type"] = "batting"

    # Savant's own CSV has no team column - attach one via the MLB Stats API
    # roster map so team-level aggregation (mlb_features.py) has something
    # to filter on. Best-effort: an empty/partial map just leaves "team" NaN
    # for unmatched players rather than failing the whole fetch.
    if "player_name" in df.columns:
        team_map = fetch_player_team_map(season)
        if team_map:
            df["team"] = df["player_name"].map(team_map)

    logger.info(
        "Fetched %d batting rows for season %d.", len(df), season
    )
    return df


# ---------------------------------------------------------------------------
# Pitcher lookup
# ---------------------------------------------------------------------------


def get_pitcher_stats(
    player_name: str,
    season: Optional[int] = None,
) -> Optional[dict]:
    """
    Search the pitching Statcast DataFrame for a named pitcher.

    Performs a case-insensitive substring search on ``player_name``.
    If multiple pitchers match, the first result (highest PA) is returned.

    Args:
        player_name: Full or partial pitcher name (e.g. ``"Verlander"``).
        season:      MLB season year.  Defaults to the current year.

    Returns:
        Dict with keys:

        - ``player_name``  – matched pitcher's full name
        - ``team``         – team abbreviation
        - ``era``          – earned run average
        - ``xera``         – expected ERA
        - ``era_luck_gap`` – ERA - xERA  (positive → lucky / regression risk)
        - ``k_pct``        – strikeout percentage
        - ``bb_pct``       – walk percentage

        Returns ``None`` if no pitcher is found or the DataFrame is empty.
    """
    if not player_name or not player_name.strip():
        logger.warning("get_pitcher_stats called with empty player_name.")
        return None

    df = fetch_pitching_statcast(season=season)

    if df.empty or "player_name" not in df.columns:
        logger.warning(
            "Pitching DataFrame is empty or missing player_name column "
            "for season %d.",
            season or _current_season(),
        )
        return None

    mask = df["player_name"].str.contains(
        player_name.strip(), case=False, na=False
    )
    matches = df[mask]

    if matches.empty:
        logger.warning(
            "No pitcher found matching '%s' in %d data.",
            player_name,
            season or _current_season(),
        )
        return None

    # Sort by PA descending so the most-used pitcher wins on ties
    if "pa" in matches.columns:
        matches = matches.sort_values("pa", ascending=False)

    row = matches.iloc[0]

    def _float(col: str) -> float:
        val = pd.to_numeric(row.get(col), errors="coerce")
        return float(val) if pd.notna(val) else float("nan")

    era = _float("era")
    xera = _float("xera")
    era_luck_gap = (
        era - xera
        if not (pd.isna(era) or pd.isna(xera))
        else float("nan")
    )

    return {
        "player_name": str(row.get("player_name", "")),
        "team": str(row.get("team", "")),  # empty in 2026 API
        "era": era,
        "xera": xera,
        "era_luck_gap": era_luck_gap,
        "est_woba": _float("est_woba"),
        "woba": _float("woba"),
        "est_woba_minus_woba": _float("est_woba_minus_woba_diff"),
        "pa": _float("pa"),
    }


# ---------------------------------------------------------------------------
# Database persistence
# ---------------------------------------------------------------------------

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS statcast_cache (
    id              SERIAL          PRIMARY KEY,
    player_id       BIGINT,
    player_name     TEXT            NOT NULL,
    team            TEXT,
    season          INTEGER         NOT NULL,
    stat_type       TEXT            NOT NULL,
    stats_json      JSONB           NOT NULL,
    fetched_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    CONSTRAINT statcast_cache_uq UNIQUE (player_name, season, stat_type)
);
"""

_UPSERT_SQL = """
INSERT INTO statcast_cache
    (player_id, player_name, team, season, stat_type, stats_json, fetched_at)
VALUES
    (%(player_id)s, %(player_name)s, %(team)s, %(season)s,
     %(stat_type)s, %(stats_json)s, %(fetched_at)s)
ON CONFLICT (player_name, season, stat_type)
DO UPDATE SET
    team        = EXCLUDED.team,
    stats_json  = EXCLUDED.stats_json,
    fetched_at  = EXCLUDED.fetched_at;
"""

# Columns that are metadata, not stats (excluded from the JSON snapshot)
_META_COLS = {"player_id", "player_name", "team", "season", "stat_type", "year"}


def save_statcast_to_db(df: pd.DataFrame, stat_type: str) -> None:
    """
    Persist a Statcast DataFrame to the ``statcast_cache`` PostgreSQL table.

    Creates the table if it does not already exist.
    Upserts on (player_name, season, stat_type) so repeated ingestion runs
    are idempotent.

    Args:
        df:        DataFrame produced by :func:`fetch_pitching_statcast`
                   or :func:`fetch_batting_statcast`.
        stat_type: ``"pitching"`` or ``"batting"``.

    Side effects:
        Executes DDL + DML against the configured pipeline database.
    """
    # Ensure the destination table exists
    execute_write(_CREATE_TABLE_SQL)

    if df.empty:
        logger.warning(
            "save_statcast_to_db called with empty DataFrame for stat_type=%s "
            "— nothing written.",
            stat_type,
        )
        return

    fetched_at = now_cst().isoformat()
    stat_cols = [c for c in df.columns if c not in _META_COLS]

    rows: list[dict] = []
    for _, row in df.iterrows():
        # Build JSON snapshot of all stat columns
        stats_snapshot: dict = {}
        for col in stat_cols:
            val = row.get(col)
            stats_snapshot[col] = None if pd.isna(val) else val  # type: ignore[arg-type]

        player_id_raw = row.get("player_id")
        rows.append(
            {
                "player_id": (
                    int(player_id_raw)
                    if pd.notna(player_id_raw)
                    else None
                ),
                "player_name": str(row.get("player_name", "")),
                "team": str(row.get("team", "")) or None,
                "season": int(row.get("season", _current_season())),
                "stat_type": stat_type,
                "stats_json": json.dumps(stats_snapshot),
                "fetched_at": fetched_at,
            }
        )

    written = execute_many(_UPSERT_SQL, rows)
    logger.info(
        "save_statcast_to_db: wrote %d %s rows to statcast_cache.",
        written,
        stat_type,
    )


# ---------------------------------------------------------------------------
# Quick-test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s  %(name)s  %(message)s",
        stream=sys.stdout,
    )

    print("=" * 60)
    print("MLB Statcast Quick Fetch")
    print("=" * 60)

    print("\n--- Pitching (first 5 rows) ---")
    pitching_df = fetch_pitching_statcast()
    print(pitching_df.head(5).to_string(index=False))

    print("\n--- Batting (first 5 rows) ---")
    batting_df = fetch_batting_statcast()
    print(batting_df.head(5).to_string(index=False))

    print("\n--- Pitcher lookup: Verlander ---")
    stats = get_pitcher_stats("Verlander")
    if stats:
        for k, v in stats.items():
            print(f"  {k}: {v}")
    else:
        print("  Not found in current season data.")
