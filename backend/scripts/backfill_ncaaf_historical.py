"""
One-time backfill: NCAAF historical lines + results into
``nfl_historical_odds`` (sport='ncaaf').

Source: collegefootballdata.com /lines endpoint. Requires CFBD_API_KEY
(free registration at collegefootballdata.com/key) - the site added
required Bearer-token auth after this project's original notes were
written (previously documented as free/no-key).

Each game may carry multiple provider lines (DraftKings, consensus,
etc.). Prefers a 'consensus' line if CFBD provides one; otherwise
averages spread/total across all providers for that game - same
"average the field" approach used by nfl_ingestion.py for live odds.

Usage
-----
    python scripts/backfill_ncaaf_historical.py --seasons 2024 2025

Idempotent: deletes existing sport='ncaaf' rows for the requested
seasons before inserting, rather than duplicating.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from pipeline.db.connection import execute_write

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_LINES_URL = "https://api.collegefootballdata.com/lines"


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def fetch_lines(year: int, api_key: str, season_type: str = "regular") -> list[dict]:
    resp = requests.get(
        _LINES_URL,
        params={"year": year, "seasonType": season_type},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _consensus_line(lines: list[dict]) -> dict | None:
    """Prefer a 'consensus' provider line; otherwise average all providers."""
    if not lines:
        return None

    consensus = next((l for l in lines if l.get("provider", "").lower() == "consensus"), None)
    if consensus and consensus.get("spread") is not None:
        return {
            "spread_open": consensus.get("spreadOpen"),
            "spread_close": consensus.get("spread"),
            "total_open": consensus.get("overUnderOpen"),
            "total_close": consensus.get("overUnder"),
        }

    spreads = [l["spread"] for l in lines if l.get("spread") is not None]
    spread_opens = [l["spreadOpen"] for l in lines if l.get("spreadOpen") is not None]
    totals = [l["overUnder"] for l in lines if l.get("overUnder") is not None]
    total_opens = [l["overUnderOpen"] for l in lines if l.get("overUnderOpen") is not None]

    if not spreads and not totals:
        return None

    return {
        "spread_open": _avg(spread_opens),
        "spread_close": _avg(spreads),
        "total_open": _avg(total_opens),
        "total_close": _avg(totals),
    }


def backfill(seasons: list[int]) -> dict:
    api_key = os.environ.get("CFBD_API_KEY", "")
    if not api_key:
        msg = "CFBD_API_KEY not configured - register at collegefootballdata.com/key"
        logger.error(msg)
        return {"inserted": 0, "skipped_no_line": 0, "status": "skipped", "error_msg": msg}

    execute_write(
        "DELETE FROM nfl_historical_odds WHERE sport = 'ncaaf' AND season = ANY(%s)",
        (list(seasons),),
    )

    inserted = 0
    skipped_no_line = 0

    for year in seasons:
        games = fetch_lines(year, api_key)
        logger.info("Fetched %d NCAAF games with line data for %d", len(games), year)

        for g in games:
            line = _consensus_line(g.get("lines", []))
            if line is None:
                skipped_no_line += 1
                continue

            home_score, away_score = g.get("homeScore"), g.get("awayScore")
            spread_close, total_close = line["spread_close"], line["total_close"]

            home_covered = None
            if spread_close is not None and home_score is not None and away_score is not None:
                margin = home_score - away_score
                # CFBD spread convention: negative = home favored (same as our
                # schema). Correct ATS formula: margin > -spread_close (must
                # win by more than the spread to cover as favorite, or lose by
                # less than it to cover as underdog). margin > spread_close is
                # WRONG - verified empirically: heavy home "favorites" (per
                # this sign convention) win outright 94.4% of the time (808
                # games, spread_close < -14), confirming favored/underdog
                # sign is right, but the cover math itself was flipped.
                if margin > -spread_close:
                    home_covered = True
                elif margin < -spread_close:
                    home_covered = False

            total_went_over = None
            if total_close is not None and home_score is not None and away_score is not None:
                actual_total = home_score + away_score
                if actual_total > total_close:
                    total_went_over = True
                elif actual_total < total_close:
                    total_went_over = False

            execute_write(
                """INSERT INTO nfl_historical_odds
                   (game_id, sport, season, week, home_team, away_team, game_date,
                    spread_open, spread_close, total_open, total_close,
                    home_score, away_score, home_covered, total_went_over, source)
                   VALUES (%s,'ncaaf',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'cfbd')""",
                (
                    str(g.get("id", "")),
                    g.get("season"),
                    g.get("week"),
                    g.get("homeTeam", ""),
                    g.get("awayTeam", ""),
                    (g.get("startDate") or "")[:10] or None,
                    line["spread_open"],
                    spread_close,
                    line["total_open"],
                    total_close,
                    home_score,
                    away_score,
                    home_covered,
                    total_went_over,
                ),
            )
            inserted += 1

        time.sleep(1)  # be polite between season requests

    logger.info("Backfill complete: %d inserted, %d skipped (no line data)", inserted, skipped_no_line)
    return {"inserted": inserted, "skipped_no_line": skipped_no_line, "status": "ok", "error_msg": None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", nargs="+", type=int, default=[2024, 2025])
    args = parser.parse_args()

    result = backfill(args.seasons)
    print(result)
