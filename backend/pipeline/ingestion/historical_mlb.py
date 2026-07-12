"""
Historical MLB data ingestion — 2023 through 2025 seasons.

Fetches and stores:
  1. Baseball Savant pitcher Statcast per season (era, xera, k_pct, bb_pct)
  2. Baseball Savant batter Statcast per season (woba, xwoba)
  3. MLB StatsAPI completed game results per season (scores, SPs, venue)

All three sources are stored in new tables:
  hist_mlb_statcast_pitching  — one row per pitcher per season
  hist_mlb_statcast_batting   — one row per batter per season
  hist_mlb_games              — one row per completed regular-season game

Rate limiting (gentle, not all data needed today):
  - Baseball Savant: 1 request per stat-type per season → 6 total calls
  - StatsAPI games:  1 request per month per season    → ~21 total calls
  - Delays: 4 s between Savant calls, 2 s between statsapi monthly calls,
            15 s between seasons

Run manually via:
    cd /root/sporttrader/backend
    python3 -m pipeline.ingestion.historical_mlb --seasons 2023 2024 2025

Or via API:  POST /api/v2/edges/ingest-historical?seasons=2023,2024,2025
"""

from __future__ import annotations

import argparse
import calendar
import io
import logging
import time
from datetime import date, datetime
from typing import Optional

import pandas as pd
import requests

from pipeline.db.connection import execute_many, execute_query, execute_write, get_connection

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Baseball Savant endpoints (same base as mlb_statcast.py)
# ---------------------------------------------------------------------------
_SAVANT_BASE = "https://baseballsavant.mlb.com/leaderboard/expected_statistics"
_SAVANT_PITCH_URL = _SAVANT_BASE + "?type=pitcher&year={season}&position=&team=&min=30&csv=true"
_SAVANT_BAT_URL   = _SAVANT_BASE + "?type=batter&year={season}&position=&team=&min=30&csv=true"

_SESSION = requests.Session()
_SESSION.headers["User-Agent"] = "SportTrader/1.0 historical-ingest research"

# Delays (seconds)
_DELAY_SAVANT   = 4.0   # between Baseball Savant calls
_DELAY_STATSAPI = 2.0   # between monthly statsapi calls
_DELAY_SEASON   = 15.0  # between seasons

# Regular season approximate date ranges
_SEASON_MONTHS = list(range(3, 11))  # March (spring training ends) to October


# ---------------------------------------------------------------------------
# DDL — create tables if absent
# ---------------------------------------------------------------------------

def _ensure_tables() -> None:
    stmts = [
        """
        CREATE TABLE IF NOT EXISTS hist_mlb_statcast_pitching (
            id          SERIAL PRIMARY KEY,
            season      INT          NOT NULL,
            player_name VARCHAR(120) NOT NULL,
            era         FLOAT,
            xera        FLOAT,
            era_gap     FLOAT,          -- era - xera
            k_percent   FLOAT,
            bb_percent  FLOAT,
            pa          INT,
            created_at  TIMESTAMP WITH TIME ZONE DEFAULT now(),
            UNIQUE (season, player_name)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS hist_mlb_statcast_batting (
            id          SERIAL PRIMARY KEY,
            season      INT          NOT NULL,
            player_name VARCHAR(120) NOT NULL,
            woba        FLOAT,
            xwoba       FLOAT,
            woba_gap    FLOAT,         -- woba - xwoba
            pa          INT,
            created_at  TIMESTAMP WITH TIME ZONE DEFAULT now(),
            UNIQUE (season, player_name)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS hist_mlb_games (
            id          SERIAL PRIMARY KEY,
            season      INT          NOT NULL,
            game_date   DATE         NOT NULL,
            home_team   VARCHAR(100) NOT NULL,
            away_team   VARCHAR(100) NOT NULL,
            home_score  INT,
            away_score  INT,
            home_sp     VARCHAR(120),   -- "First Last" from statsapi
            away_sp     VARCHAR(120),
            home_sp_lf  VARCHAR(120),   -- "Last, First" — Statcast lookup key
            away_sp_lf  VARCHAR(120),
            venue_name  VARCHAR(100),
            status      VARCHAR(30),
            created_at  TIMESTAMP WITH TIME ZONE DEFAULT now(),
            UNIQUE (season, game_date, home_team, away_team)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS hist_mlb_ingest_log (
            id       SERIAL PRIMARY KEY,
            season   INT         NOT NULL,
            step     VARCHAR(50) NOT NULL,  -- 'pitching' | 'batting' | 'games_YYYY-MM'
            rows     INT,
            status   VARCHAR(20) NOT NULL,  -- 'ok' | 'error' | 'skipped'
            error    TEXT,
            run_at   TIMESTAMP WITH TIME ZONE DEFAULT now()
        )
        """,
    ]
    for stmt in stmts:
        execute_write(stmt.strip())
    logger.info("[historical_mlb] Tables ensured.")


# ---------------------------------------------------------------------------
# Progress tracking — skip already-ingested steps
# ---------------------------------------------------------------------------

def _is_done(season: int, step: str) -> bool:
    rows = execute_query(
        "SELECT id FROM hist_mlb_ingest_log WHERE season=%s AND step=%s AND status='ok' LIMIT 1",
        (season, step),
    )
    return bool(rows)


def _log_step(season: int, step: str, rows: int, status: str, error: Optional[str] = None) -> None:
    execute_write(
        "INSERT INTO hist_mlb_ingest_log (season, step, rows, status, error) VALUES (%s,%s,%s,%s,%s)",
        (season, step, rows, status, error),
    )


# ---------------------------------------------------------------------------
# Baseball Savant fetch helpers
# ---------------------------------------------------------------------------

def _fetch_savant_csv(url: str, timeout: int = 30) -> pd.DataFrame:
    """Download a Savant CSV and return as DataFrame."""
    resp = _SESSION.get(url, timeout=timeout)
    resp.raise_for_status()
    return pd.read_csv(io.StringIO(resp.text))


def _savant_player_name(df: pd.DataFrame) -> pd.DataFrame:
    """Rename the awkward comma-header column to player_name."""
    rename = {}
    for col in df.columns:
        if "last_name" in col.lower() and "first_name" in col.lower():
            rename[col] = "player_name"
            break
    if rename:
        df = df.rename(columns=rename)
    return df


def _to_float(val) -> Optional[float]:
    try:
        f = float(val)
        return f if pd.notna(f) else None
    except (TypeError, ValueError):
        return None


def _to_int(val) -> Optional[int]:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Ingest Baseball Savant pitching for one season
# ---------------------------------------------------------------------------

def ingest_pitching(season: int) -> int:
    step = "pitching"
    if _is_done(season, step):
        logger.info("[historical_mlb] Pitching %d already ingested — skipping.", season)
        return 0

    url = _SAVANT_PITCH_URL.format(season=season)
    logger.info("[historical_mlb] Fetching Savant pitching %d …", season)
    try:
        df = _fetch_savant_csv(url)
        df = _savant_player_name(df)
    except Exception as exc:
        _log_step(season, step, 0, "error", str(exc))
        logger.error("[historical_mlb] Savant pitching %d failed: %s", season, exc)
        return 0

    rows_written = 0
    records: list[tuple] = []
    for _, row in df.iterrows():
        name = str(row.get("player_name", "")).strip()
        if not name:
            continue
        era      = _to_float(row.get("era"))
        xera     = _to_float(row.get("xera"))
        era_gap  = round(era - xera, 4) if (era is not None and xera is not None) else None
        k_pct    = _to_float(row.get("k_percent"))
        bb_pct   = _to_float(row.get("bb_percent"))
        pa       = _to_int(row.get("pa"))
        records.append((season, name, era, xera, era_gap, k_pct, bb_pct, pa))

    if records:
        execute_many(
            """INSERT INTO hist_mlb_statcast_pitching
               (season, player_name, era, xera, era_gap, k_percent, bb_percent, pa)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (season, player_name) DO UPDATE SET
                 era=EXCLUDED.era, xera=EXCLUDED.xera, era_gap=EXCLUDED.era_gap,
                 k_percent=EXCLUDED.k_percent, bb_percent=EXCLUDED.bb_percent, pa=EXCLUDED.pa""",
            records,
        )
        rows_written = len(records)

    _log_step(season, step, rows_written, "ok")
    logger.info("[historical_mlb] Pitching %d: %d rows saved.", season, rows_written)
    return rows_written


# ---------------------------------------------------------------------------
# Ingest Baseball Savant batting for one season
# ---------------------------------------------------------------------------

def ingest_batting(season: int) -> int:
    step = "batting"
    if _is_done(season, step):
        logger.info("[historical_mlb] Batting %d already ingested — skipping.", season)
        return 0

    url = _SAVANT_BAT_URL.format(season=season)
    logger.info("[historical_mlb] Fetching Savant batting %d …", season)
    try:
        df = _fetch_savant_csv(url)
        df = _savant_player_name(df)
    except Exception as exc:
        _log_step(season, step, 0, "error", str(exc))
        logger.error("[historical_mlb] Savant batting %d failed: %s", season, exc)
        return 0

    records: list[tuple] = []
    for _, row in df.iterrows():
        name = str(row.get("player_name", "")).strip()
        if not name:
            continue
        woba     = _to_float(row.get("woba") or row.get("est_woba"))
        xwoba    = _to_float(row.get("est_woba") or row.get("xwoba"))
        # prefer actual woba and estimated woba columns
        actual_woba = _to_float(row.get("woba"))
        est_woba    = _to_float(row.get("est_woba"))
        if actual_woba is not None and est_woba is not None:
            woba  = actual_woba
            xwoba = est_woba
        woba_gap = round(woba - xwoba, 4) if (woba is not None and xwoba is not None) else None
        pa = _to_int(row.get("pa"))
        records.append((season, name, woba, xwoba, woba_gap, pa))

    if records:
        execute_many(
            """INSERT INTO hist_mlb_statcast_batting
               (season, player_name, woba, xwoba, woba_gap, pa)
               VALUES (%s,%s,%s,%s,%s,%s)
               ON CONFLICT (season, player_name) DO UPDATE SET
                 woba=EXCLUDED.woba, xwoba=EXCLUDED.xwoba,
                 woba_gap=EXCLUDED.woba_gap, pa=EXCLUDED.pa""",
            records,
        )

    rows_written = len(records)
    _log_step(season, step, rows_written, "ok")
    logger.info("[historical_mlb] Batting %d: %d rows saved.", season, rows_written)
    return rows_written


# ---------------------------------------------------------------------------
# Ingest game results for one season via MLB StatsAPI
# ---------------------------------------------------------------------------

def _name_to_lf(name: str) -> str:
    """Convert 'First Last' → 'Last, First' for Statcast lookup."""
    parts = name.rsplit(" ", 1)
    if len(parts) == 2:
        return f"{parts[1]}, {parts[0]}"
    return name


def ingest_games_month(season: int, month: int) -> int:
    step = f"games_{season}-{month:02d}"
    if _is_done(season, step):
        return 0

    import statsapi

    last_day = calendar.monthrange(season, month)[1]
    start_dt = f"{season}-{month:02d}-01"
    end_dt   = f"{season}-{month:02d}-{last_day:02d}"

    logger.info("[historical_mlb] Fetching games %s → %s …", start_dt, end_dt)
    try:
        games = statsapi.schedule(start_date=start_dt, end_date=end_dt, sportId=1)
    except Exception as exc:
        _log_step(season, step, 0, "error", str(exc))
        logger.error("[historical_mlb] statsapi games %d-%02d failed: %s", season, month, exc)
        return 0

    records: list[tuple] = []
    for g in games:
        status = g.get("status", "")
        # Only include finished games
        if status not in ("Final", "Completed Early", "Game Over"):
            continue
        game_type = g.get("game_type", "R")
        if game_type != "R":  # regular season only
            continue

        home_score = g.get("home_score")
        away_score = g.get("away_score")
        if home_score is None or away_score is None:
            continue

        home_sp_ff = g.get("home_probable_pitcher") or ""
        away_sp_ff = g.get("away_probable_pitcher") or ""
        home_sp_lf = _name_to_lf(home_sp_ff) if home_sp_ff else ""
        away_sp_lf = _name_to_lf(away_sp_ff) if away_sp_ff else ""

        gdate = g.get("game_date", "")
        try:
            gdate_obj = date.fromisoformat(gdate)
        except ValueError:
            continue

        records.append((
            season, gdate_obj,
            g.get("home_name", ""), g.get("away_name", ""),
            int(home_score), int(away_score),
            home_sp_ff or None, away_sp_ff or None,
            home_sp_lf or None, away_sp_lf or None,
            g.get("venue_name") or None,
            status,
        ))

    if records:
        execute_many(
            """INSERT INTO hist_mlb_games
               (season, game_date, home_team, away_team,
                home_score, away_score,
                home_sp, away_sp, home_sp_lf, away_sp_lf,
                venue_name, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (season, game_date, home_team, away_team) DO NOTHING""",
            records,
        )

    rows_written = len(records)
    _log_step(season, step, rows_written, "ok")
    logger.info("[historical_mlb] Games %d-%02d: %d completed games.", season, month, rows_written)
    return rows_written


# ---------------------------------------------------------------------------
# Full season orchestrator
# ---------------------------------------------------------------------------

def ingest_season(season: int) -> dict:
    logger.info("[historical_mlb] ===== Ingesting season %d =====", season)
    result = {"season": season, "pitching_rows": 0, "batting_rows": 0, "game_rows": 0}

    # 1 — Savant pitching
    result["pitching_rows"] = ingest_pitching(season)
    time.sleep(_DELAY_SAVANT)

    # 2 — Savant batting
    result["batting_rows"] = ingest_batting(season)
    time.sleep(_DELAY_SAVANT)

    # 3 — Game results month by month
    current_year = datetime.utcnow().year
    current_month = datetime.utcnow().month

    game_rows = 0
    for month in _SEASON_MONTHS:
        # Don't fetch future months
        if season == current_year and month >= current_month:
            break
        rows = ingest_games_month(season, month)
        game_rows += rows
        time.sleep(_DELAY_STATSAPI)

    result["game_rows"] = game_rows
    logger.info(
        "[historical_mlb] Season %d done: %d pitching, %d batting, %d games.",
        season, result["pitching_rows"], result["batting_rows"], result["game_rows"],
    )
    return result


def ingest_historical(seasons: list[int] | None = None) -> list[dict]:
    """
    Main entry point.  Call with seasons=[2023, 2024, 2025] or default.

    Rate-limited: already-completed steps are skipped (idempotent).
    """
    if seasons is None:
        seasons = [2023, 2024, 2025]

    _ensure_tables()
    results = []

    for i, season in enumerate(seasons):
        res = ingest_season(season)
        results.append(res)
        if i < len(seasons) - 1:
            logger.info("[historical_mlb] Sleeping %ss before next season …", _DELAY_SEASON)
            time.sleep(_DELAY_SEASON)

    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Ingest historical MLB data")
    parser.add_argument("--seasons", nargs="+", type=int, default=[2023, 2024, 2025])
    args = parser.parse_args()
    results = ingest_historical(args.seasons)
    for r in results:
        print(r)
