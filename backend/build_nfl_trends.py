"""
NFL Trends & Stats Pipeline
Pulls data from nflverse GitHub files — no paid API required.

Sources:
  games.csv   → ATS records, O/U trends, schedule metadata
  team_stats  → EPA, efficiency stats (parquet via nflverse releases)

Outputs:
  /var/www/max-ev-sports-api/f5_backtest/nfl_trends.db  (SQLite)

Tables:
  nfl_games          — raw game results with spread/total
  nfl_ats_records    — aggregated ATS by team/season/situation
  nfl_ou_records     — aggregated O/U by team/season/situation
  nfl_team_epa       — weekly team EPA from play-by-play aggregates
  nfl_pipeline_meta  — last run timestamp, row counts

Usage:
  python3 build_nfl_trends.py             # full rebuild (2022–present)
  python3 build_nfl_trends.py --update    # update only (current season)
"""
from __future__ import annotations

import argparse
import io
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DB_PATH   = Path(__file__).parent / "f5_backtest" / "nfl_trends.db"
SEASONS   = [2022, 2023, 2024, 2025]
GAMES_URL = "https://github.com/nflverse/nfldata/raw/master/data/games.csv"
TEAM_STATS_URL = "https://github.com/nflverse/nflverse-data/releases/download/team_stats/team_stats.parquet"
HEADERS   = {"User-Agent": "MaxEVSports/1.0"}


# ── Fetch helpers ─────────────────────────────────────────────────────────────

def _fetch_csv(url: str) -> pd.DataFrame:
    logger.info("Fetching %s", url)
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text), low_memory=False)


def _fetch_parquet(url: str) -> pd.DataFrame:
    logger.info("Fetching %s", url)
    r = requests.get(url, headers=HEADERS, timeout=120)
    r.raise_for_status()
    return pd.read_parquet(io.BytesIO(r.content))


# ── ATS / O/U computation ─────────────────────────────────────────────────────

def compute_game_results(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add ATS and O/U result columns to games dataframe.

    Convention (nflverse):
      spread_line > 0  → home team is favored by that amount
      spread_line < 0  → away team is favored
      result           → home_score - away_score

    Home covers when: result > spread_line
    Push:             result == spread_line
    Away covers:      result < spread_line
    """
    g = df.copy()

    # Only compute for completed games with spread data
    has_result = g["away_score"].notna() & g["home_score"].notna()
    has_spread = g["spread_line"].notna()
    has_total  = g["total_line"].notna()

    g["total_actual"] = g["home_score"] + g["away_score"]

    # ATS — home perspective
    g["home_cover"] = None
    g["away_cover"] = None
    g["ats_push"]   = None

    mask = has_result & has_spread
    g.loc[mask & (g["result"] > g["spread_line"]),  "home_cover"] = True
    g.loc[mask & (g["result"] > g["spread_line"]),  "away_cover"] = False
    g.loc[mask & (g["result"] < g["spread_line"]),  "home_cover"] = False
    g.loc[mask & (g["result"] < g["spread_line"]),  "away_cover"] = True
    g.loc[mask & (g["result"] == g["spread_line"]), "home_cover"] = None  # push
    g.loc[mask & (g["result"] == g["spread_line"]), "away_cover"] = None
    g.loc[mask & (g["result"] == g["spread_line"]), "ats_push"]   = True
    g.loc[mask & (g["result"] != g["spread_line"]), "ats_push"]   = False

    # O/U
    g["went_over"]  = None
    g["went_under"] = None
    g["ou_push"]    = None

    mask2 = has_result & has_total
    g.loc[mask2 & (g["total_actual"] > g["total_line"]),  "went_over"]  = True
    g.loc[mask2 & (g["total_actual"] > g["total_line"]),  "went_under"] = False
    g.loc[mask2 & (g["total_actual"] < g["total_line"]),  "went_over"]  = False
    g.loc[mask2 & (g["total_actual"] < g["total_line"]),  "went_under"] = True
    g.loc[mask2 & (g["total_actual"] == g["total_line"]), "went_over"]  = None
    g.loc[mask2 & (g["total_actual"] == g["total_line"]), "went_under"] = None
    g.loc[mask2 & (g["total_actual"] == g["total_line"]), "ou_push"]    = True
    g.loc[mask2 & (g["total_actual"] != g["total_line"]), "ou_push"]    = False

    return g


def build_team_ats_records(games: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate ATS records per team across multiple dimensions.
    Returns one row per (team, season, situation).
    """
    rows = []
    completed = games[games["away_score"].notna() & games["spread_line"].notna()].copy()

    def _agg(subset: pd.DataFrame, team: str, season: int, situation: str) -> dict:
        if subset.empty:
            return {}
        ats_w = int(subset["ats_win"].sum())
        ats_l = int(subset["ats_loss"].sum())
        ats_p = int(subset["ats_push"].fillna(False).sum())
        total_g = ats_w + ats_l + ats_p
        ou_o  = int(subset["went_over"].dropna().sum())
        ou_u  = int(subset["went_under"].dropna().sum())
        ou_p  = int(subset["ou_push"].fillna(False).sum())
        avg_spread = float(subset["spread_line"].mean()) if not subset.empty else None
        avg_total  = float(subset["total_line"].mean()) if not subset.empty else None
        avg_pts_scored = float(subset["pts_scored"].mean()) if not subset.empty else None
        avg_pts_allowed = float(subset["pts_allowed"].mean()) if not subset.empty else None
        return {
            "team": team, "season": season, "situation": situation,
            "games": total_g,
            "ats_wins": ats_w, "ats_losses": ats_l, "ats_pushes": ats_p,
            "ats_pct": round(ats_w / (ats_w + ats_l), 3) if (ats_w + ats_l) > 0 else None,
            "ou_over": ou_o, "ou_under": ou_u, "ou_pushes": ou_p,
            "over_pct": round(ou_o / (ou_o + ou_u), 3) if (ou_o + ou_u) > 0 else None,
            "avg_spread": round(avg_spread, 2) if avg_spread is not None else None,
            "avg_total": round(avg_total, 2) if avg_total is not None else None,
            "avg_pts_scored": round(avg_pts_scored, 1) if avg_pts_scored is not None else None,
            "avg_pts_allowed": round(avg_pts_allowed, 1) if avg_pts_allowed is not None else None,
        }

    teams = set(completed["home_team"].unique()) | set(completed["away_team"].unique())

    for season in SEASONS:
        season_games = completed[completed["season"] == season]
        if season_games.empty:
            continue

        for team in teams:
            # Build team-centric view
            home_g = season_games[season_games["home_team"] == team].copy()
            away_g = season_games[season_games["away_team"] == team].copy()

            home_g["ats_win"]    = home_g["home_cover"]
            home_g["ats_loss"]   = home_g["away_cover"]
            home_g["pts_scored"] = home_g["home_score"]
            home_g["pts_allowed"]= home_g["away_score"]

            away_g["ats_win"]    = away_g["away_cover"]
            away_g["ats_loss"]   = away_g["home_cover"]
            away_g["pts_scored"] = away_g["away_score"]
            away_g["pts_allowed"]= away_g["home_score"]

            all_g  = pd.concat([home_g, away_g])
            div_g  = all_g[all_g["div_game"] == 1]
            fav_g  = all_g[
                ((all_g["home_team"] == team) & (all_g["spread_line"] > 0)) |
                ((all_g["away_team"] == team) & (all_g["spread_line"] < 0))
            ]
            dog_g  = all_g[
                ((all_g["home_team"] == team) & (all_g["spread_line"] < 0)) |
                ((all_g["away_team"] == team) & (all_g["spread_line"] > 0))
            ]

            for subset, sit in [
                (all_g,  "overall"),
                (home_g, "home"),
                (away_g, "away"),
                (div_g,  "divisional"),
                (fav_g,  "as_favorite"),
                (dog_g,  "as_underdog"),
            ]:
                rec = _agg(subset, team, season, sit)
                if rec:
                    rows.append(rec)

    return pd.DataFrame(rows)


# ── EPA from team stats parquet ───────────────────────────────────────────────

def build_team_epa(seasons: list[int]) -> pd.DataFrame:
    """Pull pre-aggregated team stats from nflverse (weekly EPA)."""
    try:
        df = _fetch_parquet(TEAM_STATS_URL)
        logger.info("team_stats columns: %s", list(df.columns)[:30])
        df = df[df["season"].isin(seasons)]

        # Map nflverse column names (may vary by release)
        epa_cols = [c for c in df.columns if "epa" in c.lower() or "cpoe" in c.lower()]
        keep = ["season", "week", "team", "game_id"] + epa_cols
        keep = [c for c in keep if c in df.columns]
        return df[keep].copy()
    except Exception as exc:
        logger.warning("team_stats parquet failed (%s) — EPA will be empty", exc)
        return pd.DataFrame()


# ── SQLite persistence ────────────────────────────────────────────────────────

def init_db(con: sqlite3.Connection) -> None:
    con.executescript("""
        CREATE TABLE IF NOT EXISTS nfl_games (
            game_id TEXT PRIMARY KEY,
            season INTEGER, week INTEGER, game_type TEXT,
            gameday TEXT, gametime TEXT,
            away_team TEXT, home_team TEXT,
            away_score REAL, home_score REAL,
            result REAL, total_actual REAL,
            spread_line REAL, total_line REAL,
            away_moneyline REAL, home_moneyline REAL,
            home_cover INTEGER, away_cover INTEGER, ats_push INTEGER,
            went_over INTEGER, went_under INTEGER, ou_push INTEGER,
            div_game INTEGER, location TEXT, roof TEXT, surface TEXT,
            temp REAL, wind REAL, overtime INTEGER,
            away_qb_name TEXT, home_qb_name TEXT,
            away_coach TEXT, home_coach TEXT,
            away_rest INTEGER, home_rest INTEGER
        );

        CREATE TABLE IF NOT EXISTS nfl_ats_records (
            team TEXT, season INTEGER, situation TEXT,
            games INTEGER,
            ats_wins INTEGER, ats_losses INTEGER, ats_pushes INTEGER,
            ats_pct REAL,
            ou_over INTEGER, ou_under INTEGER, ou_pushes INTEGER,
            over_pct REAL,
            avg_spread REAL, avg_total REAL,
            avg_pts_scored REAL, avg_pts_allowed REAL,
            PRIMARY KEY (team, season, situation)
        );

        CREATE TABLE IF NOT EXISTS nfl_team_epa (
            season INTEGER, week INTEGER, team TEXT, game_id TEXT,
            off_epa REAL, def_epa REAL, st_epa REAL,
            pass_epa REAL, rush_epa REAL, cpoe REAL,
            PRIMARY KEY (season, week, team)
        );

        CREATE TABLE IF NOT EXISTS nfl_pipeline_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    con.commit()


def save_games(con: sqlite3.Connection, games: pd.DataFrame) -> int:
    cols = [
        "game_id", "season", "week", "game_type", "gameday", "gametime",
        "away_team", "home_team", "away_score", "home_score",
        "result", "total_actual", "spread_line", "total_line",
        "away_moneyline", "home_moneyline",
        "home_cover", "away_cover", "ats_push",
        "went_over", "went_under", "ou_push",
        "div_game", "location", "roof", "surface",
        "temp", "wind", "overtime",
        "away_qb_name", "home_qb_name", "away_coach", "home_coach",
        "away_rest", "home_rest",
    ]
    present = [c for c in cols if c in games.columns]
    subset  = games[present].copy()

    # Convert booleans → int for SQLite
    for c in ["home_cover", "away_cover", "ats_push", "went_over", "went_under", "ou_push"]:
        if c in subset.columns:
            subset[c] = subset[c].map({True: 1, False: 0, None: None})

    subset.to_sql("nfl_games", con, if_exists="replace", index=False)
    return len(subset)


def save_ats(con: sqlite3.Connection, ats: pd.DataFrame) -> int:
    ats.to_sql("nfl_ats_records", con, if_exists="replace", index=False)
    return len(ats)


def save_epa(con: sqlite3.Connection, epa: pd.DataFrame) -> int:
    if epa.empty:
        return 0
    col_map = {
        "offense_epa": "off_epa", "defense_epa": "def_epa",
        "special_teams_epa": "st_epa",
        "passing_epa": "pass_epa", "rushing_epa": "rush_epa",
        "avg_cpoe": "cpoe",
    }
    epa = epa.rename(columns=col_map)
    keep = ["season", "week", "team", "game_id", "off_epa", "def_epa",
            "st_epa", "pass_epa", "rush_epa", "cpoe"]
    keep = [c for c in keep if c in epa.columns]
    epa[keep].to_sql("nfl_team_epa", con, if_exists="replace", index=False)
    return len(epa)


# ── Main ──────────────────────────────────────────────────────────────────────

def run(update_only: bool = False) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    init_db(con)

    t0 = time.time()
    logger.info("Pulling games data from nflverse…")
    raw = _fetch_csv(GAMES_URL)

    target_seasons = [max(SEASONS)] if update_only else SEASONS
    raw = raw[raw["season"].isin(target_seasons)].copy()

    logger.info("Computing ATS and O/U results for %d games…", len(raw))
    games = compute_game_results(raw)
    n_games = save_games(con, games)
    logger.info("Saved %d game records", n_games)

    logger.info("Aggregating ATS records…")
    ats = build_team_ats_records(games)
    n_ats = save_ats(con, ats)
    logger.info("Saved %d ATS record rows", n_ats)

    logger.info("Pulling team EPA stats…")
    epa = build_team_epa(target_seasons)
    n_epa = save_epa(con, epa)
    logger.info("Saved %d EPA rows", n_epa)

    # Write metadata
    meta = {
        "last_run": datetime.utcnow().isoformat(),
        "games_count": str(n_games),
        "ats_rows": str(n_ats),
        "epa_rows": str(n_epa),
        "seasons": ",".join(map(str, target_seasons)),
        "elapsed_s": str(round(time.time() - t0, 1)),
    }
    con.executemany(
        "INSERT OR REPLACE INTO nfl_pipeline_meta (key, value) VALUES (?,?)",
        meta.items()
    )
    con.commit()
    con.close()

    logger.info("Done in %.1fs — DB at %s", time.time() - t0, DB_PATH)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true", help="Current season only")
    args = parser.parse_args()
    run(update_only=args.update)
