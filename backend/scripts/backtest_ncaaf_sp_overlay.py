"""
Backtest the NCAAF SP+ overlay ATS detector against real historical
results (Task 13, NCAAF half).

Unlike the NFL backtest (which derives a rolling power rating week-by-
week from game results, avoiding lookahead), NCAAF SP+ ratings are a
season-level snapshot from CFBD - there's no free week-by-week history.
This backtest therefore uses each season's SEASON-FINAL SP+ rating
against that season's games, which has some lookahead bias for
early-season games (SP+ partly reflects results not yet known at
kickoff). This is a real limitation, not hidden: the live detector has
the same constraint (it only has "whatever SP+ is currently loaded",
not a historical time series either).

Fetches SP+ per season directly from CFBD rather than reading the
`team_ratings` table, since that table only holds one current
snapshot (would mismatch older backtest seasons).

Usage
-----
    python scripts/backtest_ncaaf_sp_overlay.py --seasons 2024 2025
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from pipeline.db.connection import execute_query

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_CFBD_SP_URL = "https://api.collegefootballdata.com/ratings/sp"

GAP_THRESHOLDS = [10.0, 15.0, 20.0, 25.0]
SPREAD_CEILINGS = [5.0, 7.0, 9.0, 11.0]


def fetch_sp_ratings(year: int, api_key: str) -> dict[str, float]:
    resp = requests.get(
        _CFBD_SP_URL, params={"year": year},
        headers={"Authorization": f"Bearer {api_key}"}, timeout=20,
    )
    resp.raise_for_status()
    return {r["team"]: r["rating"] for r in resp.json() if r.get("rating") is not None}


def load_games(seasons: list[int]) -> list[dict]:
    return execute_query(
        """SELECT season, home_team, away_team, spread_close, home_covered
           FROM nfl_historical_odds
           WHERE sport = 'ncaaf' AND season = ANY(%s)
             AND spread_close IS NOT NULL AND home_covered IS NOT NULL""",
        (seasons,),
    )


def compute_flagged_bets(games: list[dict], ratings_by_season: dict[int, dict[str, float]]) -> list[dict]:
    flagged: list[dict] = []
    for g in games:
        ratings = ratings_by_season.get(g["season"], {})
        home_r, away_r = ratings.get(g["home_team"]), ratings.get(g["away_team"])
        if home_r is None or away_r is None:
            continue

        spread_close = float(g["spread_close"])
        # CFBD convention: negative spread_close = home favored (verified in
        # the Task 11 sign-bug fix commit).
        expected_margin = home_r - away_r
        market_margin = -spread_close
        gap = expected_margin - market_margin
        pick_side = "home" if gap > 0 else "away"
        covered = g["home_covered"] if pick_side == "home" else (not g["home_covered"])

        flagged.append({
            "season": g["season"], "gap": abs(gap), "spread": abs(spread_close),
            "pick_side": pick_side, "covered": covered,
        })
    return flagged


def sweep_thresholds(flagged: list[dict]) -> list[dict]:
    results = []
    for gap_thresh in GAP_THRESHOLDS:
        for spread_ceil in SPREAD_CEILINGS:
            matches = [f for f in flagged if f["gap"] >= gap_thresh and f["spread"] < spread_ceil]
            n = len(matches)
            if n == 0:
                continue
            wins = sum(1 for m in matches if m["covered"])
            results.append({
                "min_gap": gap_thresh, "max_spread": spread_ceil,
                "n": n, "wins": wins, "hit_rate": round(wins / n, 4),
            })
    return sorted(results, key=lambda r: (-r["hit_rate"], -r["n"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", nargs="+", type=int, default=[2024, 2025])
    args = parser.parse_args()

    api_key = os.environ.get("CFBD_API_KEY", "")
    if not api_key:
        print("CFBD_API_KEY not set - register at collegefootballdata.com/key")
        sys.exit(1)

    ratings_by_season = {s: fetch_sp_ratings(s, api_key) for s in args.seasons}
    for s, r in ratings_by_season.items():
        logger.info("Fetched SP+ for %d teams in %d", len(r), s)

    games = load_games(args.seasons)
    logger.info("Loaded %d historical NCAAF games with spread + result data", len(games))

    flagged = compute_flagged_bets(games, ratings_by_season)
    logger.info("Computed SP+ gap for %d games (both teams rated)", len(flagged))

    baseline_wins = sum(1 for f in flagged if f["covered"])
    baseline_rate = baseline_wins / len(flagged)
    print(f"\nBaseline (all games, no filter): {baseline_wins}/{len(flagged)} "
          f"= {baseline_rate:.4f} hit rate\n")

    if baseline_rate > 0.55 or baseline_rate < 0.45:
        print(
            "*** WARNING: baseline hit rate is far from the ~50% expected in an\n"
            "*** efficient spread market. This almost certainly means LOOKAHEAD\n"
            "*** BIAS, not a real edge: CFBD's SP+ rating is partly DERIVED FROM\n"
            "*** that season's own game results (there's no free week-by-week SP+\n"
            "*** history to avoid this - see module docstring). DO NOT use these\n"
            "*** numbers to tune detector thresholds or as evidence of a real\n"
            "*** signal. This differs fundamentally from the NFL backtest, which\n"
            "*** computes ratings from ONLY prior games (genuinely no lookahead).\n"
        )

    print(f"{'min_gap':>8} {'max_spread':>11} {'n':>5} {'wins':>5} {'hit_rate':>9}")
    for r in sweep_thresholds(flagged):
        print(f"{r['min_gap']:>8.1f} {r['max_spread']:>11.1f} {r['n']:>5} {r['wins']:>5} {r['hit_rate']:>9.4f}")

    spec = [f for f in flagged if f["gap"] >= 15.0 and f["spread"] < 7.0]
    if spec:
        wins = sum(1 for f in spec if f["covered"])
        print(f"\nTask spec starting point (gap>=15, spread<7): {wins}/{len(spec)} = {wins/len(spec):.4f} hit rate")
    else:
        print("\nTask spec starting point (gap>=15, spread<7): 0 matching games")
