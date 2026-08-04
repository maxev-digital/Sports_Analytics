"""
Referee Penalty Pipeline — NFLpenalties.com → nfl_trends.db

Fetches per-game flag, yard, and bias data for every referee-season
found in nfl_games, then writes to nfl_referee_penalties table.

Usage:
  python3 build_referee_penalties.py                  # all seasons in DB
  python3 build_referee_penalties.py --seasons 2024   # specific year(s)
  python3 build_referee_penalties.py --dry-run        # print URLs, no requests
"""
from __future__ import annotations

import argparse
import logging
import sqlite3
from pathlib import Path

from services.penalty_scraper import PenaltyRecord, scrape_referee_season

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "f5_backtest" / "nfl_trends.db"


def _init_penalty_table(con: sqlite3.Connection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS nfl_referee_penalties (
            referee             TEXT    NOT NULL,
            season              INTEGER NOT NULL,
            games               INTEGER NOT NULL,
            flags_per_game      REAL,
            yards_per_game      REAL,
            home_flags_per_game REAL,
            away_flags_per_game REAL,
            home_bias           REAL,
            declined_per_game   REAL,
            offsetting_per_game REAL,
            PRIMARY KEY (referee, season)
        )
    """)
    con.commit()


def _get_referee_seasons(con: sqlite3.Connection, seasons: list[int] | None) -> list[tuple[str, int]]:
    """Return distinct (referee, season) pairs that exist in nfl_games."""
    season_clause = ""
    params: tuple = ()
    if seasons:
        placeholders = ",".join("?" * len(seasons))
        season_clause = f"AND season IN ({placeholders})"
        params = tuple(seasons)

    rows = con.execute(
        f"""
        SELECT DISTINCT referee, season
        FROM nfl_games
        WHERE referee IS NOT NULL AND referee != ''
          AND game_type = 'REG'
          {season_clause}
        ORDER BY season, referee
        """,
        params,
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def _upsert(con: sqlite3.Connection, rec: PenaltyRecord) -> None:
    con.execute(
        """
        INSERT OR REPLACE INTO nfl_referee_penalties
          (referee, season, games, flags_per_game, yards_per_game,
           home_flags_per_game, away_flags_per_game, home_bias,
           declined_per_game, offsetting_per_game)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            rec.referee, rec.season, rec.games,
            rec.flags_per_game, rec.yards_per_game,
            rec.home_flags_per_game, rec.away_flags_per_game, rec.home_bias,
            rec.declined_per_game, rec.offsetting_per_game,
        ),
    )
    con.commit()


def run(seasons: list[int] | None = None, dry_run: bool = False) -> None:
    if not DB_PATH.exists():
        logger.error("DB not found at %s — run build_nfl_trends.py first", DB_PATH)
        return

    con = sqlite3.connect(DB_PATH)
    _init_penalty_table(con)

    pairs = _get_referee_seasons(con, seasons)
    logger.info("Fetching %d referee-season combinations from NFLpenalties.com", len(pairs))

    fetched = skipped = failed = 0
    for referee, season in pairs:
        logger.info("Scraping %s — %d…", referee, season)
        rec = scrape_referee_season(referee, season, dry_run=dry_run)
        if rec is None:
            skipped += 1
            continue
        if not dry_run:
            _upsert(con, rec)
            fetched += 1
        else:
            fetched += 1

    con.close()
    logger.info(
        "Done — %d fetched, %d skipped/not-found, %d errors",
        fetched, skipped, failed,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build nfl_referee_penalties table")
    parser.add_argument("--seasons", nargs="+", type=int, help="Seasons to fetch (default: all in DB)")
    parser.add_argument("--dry-run", action="store_true", help="Print URLs only, no HTTP requests")
    args = parser.parse_args()
    run(seasons=args.seasons, dry_run=args.dry_run)
