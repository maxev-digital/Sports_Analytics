"""
One-time backfill: NFL historical lines + results (2023-2025) into
``nfl_historical_odds``.

Source: nflverse/nfldata games.csv (github.com/nflverse/nfldata) - free,
no auth, actively maintained. The task spec's original source
(sportsbookreviewsonline.com) is defunct (404 on every path as of
2026-07-08).

Usage
-----
    python scripts/backfill_nfl_historical.py [--seasons 2023 2024 2025]

Idempotent: safe to re-run (deletes existing sport='nfl' rows for the
requested seasons before inserting, rather than duplicating).
"""
from __future__ import annotations

import argparse
import csv
import io
import logging
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from pipeline.db.connection import execute_write, execute_query

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_GAMES_CSV_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"

_TEAM_NAMES: dict[str, str] = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LA": "Los Angeles Rams", "LAC": "Los Angeles Chargers",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}


def _team_name(abbr: str) -> str:
    return _TEAM_NAMES.get(abbr, abbr)


def _to_float(v: str) -> float | None:
    try:
        return float(v) if v not in (None, "", "NA") else None
    except ValueError:
        return None


def _to_int(v: str) -> int | None:
    try:
        return int(float(v)) if v not in (None, "", "NA") else None
    except ValueError:
        return None


def fetch_games_csv(local_path: str | None = None) -> list[dict]:
    if local_path:
        with open(local_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    resp = requests.get(_GAMES_CSV_URL, timeout=30)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    return list(reader)


def backfill(seasons: list[int], local_path: str | None = None) -> dict:
    rows = fetch_games_csv(local_path)
    season_strs = {str(s) for s in seasons}
    relevant = [r for r in rows if r.get("season") in season_strs]
    logger.info("Fetched %d total games, %d in requested seasons %s", len(rows), len(relevant), seasons)

    # Idempotency: clear existing nfl rows for these seasons first
    execute_write(
        "DELETE FROM nfl_historical_odds WHERE sport = 'nfl' AND season = ANY(%s)",
        (list(seasons),),
    )

    inserted = 0
    skipped_no_line = 0
    for r in relevant:
        spread_line = _to_float(r.get("spread_line"))
        total_line = _to_float(r.get("total_line"))
        home_score = _to_int(r.get("home_score"))
        away_score = _to_int(r.get("away_score"))

        if spread_line is None and total_line is None:
            skipped_no_line += 1
            continue

        home_covered = None
        if spread_line is not None and home_score is not None and away_score is not None:
            margin = home_score - away_score
            # nflverse spread_line convention: POSITIVE = home favored by
            # that many points (an "expected home margin" style, NOT the
            # traditional negative-for-favorite betting notation). Verified
            # empirically: home teams with spread_line > 6 win outright
            # 79.3% of the time (184 games); home teams with spread_line
            # < -6 win outright only 22.7% of the time (75 games). So the
            # direct formula margin > spread_line is correct HERE - do not
            # negate spread_line for this source (CFBD, used by the NCAAF
            # backfill, uses the opposite convention and does need negation -
            # see backfill_ncaaf_historical.py).
            if margin > spread_line:
                home_covered = True
            elif margin < spread_line:
                home_covered = False
            # else: push, leave NULL

        total_went_over = None
        actual_total = _to_float(r.get("total"))
        if total_line is not None and actual_total is not None:
            if actual_total > total_line:
                total_went_over = True
            elif actual_total < total_line:
                total_went_over = False

        execute_write(
            """INSERT INTO nfl_historical_odds
               (game_id, sport, season, week, home_team, away_team, game_date,
                spread_open, spread_close, total_open, total_close,
                home_score, away_score, home_covered, total_went_over, source)
               VALUES (%s,'nfl',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'nflverse')""",
            (
                r.get("game_id", ""),
                _to_int(r.get("season")),
                _to_int(r.get("week")),
                _team_name(r.get("home_team", "")),
                _team_name(r.get("away_team", "")),
                r.get("gameday") or None,
                None,  # spread_open not available in this free source
                spread_line,
                None,  # total_open not available in this free source
                total_line,
                home_score,
                away_score,
                home_covered,
                total_went_over,
                # note: source column fixed above via literal 'nflverse'
            ),
        )
        inserted += 1

    logger.info(
        "Backfill complete: %d inserted, %d skipped (no line data)", inserted, skipped_no_line
    )
    return {"inserted": inserted, "skipped_no_line": skipped_no_line}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", nargs="+", type=int, default=[2023, 2024, 2025])
    parser.add_argument("--csv-path", type=str, default=None, help="Local games.csv (skip network fetch)")
    args = parser.parse_args()

    result = backfill(args.seasons, local_path=args.csv_path)
    print(result)

    # Sanity check: report row count and covered/over rates
    check = execute_query(
        """SELECT season, COUNT(*) as games,
                  SUM(CASE WHEN home_covered THEN 1 ELSE 0 END) as home_covers,
                  SUM(CASE WHEN total_went_over THEN 1 ELSE 0 END) as overs
           FROM nfl_historical_odds WHERE sport = 'nfl' GROUP BY season ORDER BY season"""
    )
    for row in check:
        print(row)
