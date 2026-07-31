"""
Backtest the NFL rating-overlay ATS detector against real historical
results (Task 13).

Methodology
-----------
For each season, process games in chronological (week) order. Maintain
a running power rating per team = point differential per game across
that team's PRIOR games *this season only* (no lookahead: a team's
rating going into week N only reflects weeks 1..N-1). Teams with fewer
than MIN_GAMES_PLAYED prior games are skipped (rating too noisy).

For every remaining game, compute:
    gap = (home_rating - away_rating) - (-spread_line)
and check whether the side the gap favors actually covered.

Sweeps a grid of (min_rating_gap, max_spread) thresholds - including
the task spec's original starting point (7, 4) - and reports hit rate
+ sample size for each, so the detector's thresholds can be tuned
against real data instead of guessed.

Usage
-----
    python scripts/backtest_nfl_rating_overlay.py --seasons 2023 2024 2025
"""
from __future__ import annotations

import argparse
import logging
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from pipeline.db.connection import execute_query

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MIN_GAMES_PLAYED = 3

# Threshold grid to sweep - includes the task spec's original (7, 4) starting point
GAP_THRESHOLDS = [5.0, 7.0, 9.0, 11.0, 13.0]
SPREAD_CEILINGS = [3.0, 4.0, 5.0, 6.0]


def load_games(seasons: list[int]) -> list[dict]:
    return execute_query(
        """SELECT season, week, home_team, away_team, spread_close,
                  home_score, away_score, home_covered
           FROM nfl_historical_odds
           WHERE sport = 'nfl' AND season = ANY(%s)
             AND spread_close IS NOT NULL AND home_covered IS NOT NULL
           ORDER BY season, week, game_date""",
        (seasons,),
    )


def compute_flagged_bets(games: list[dict]) -> list[dict]:
    """
    Walk games in chronological order, maintaining running ratings, and
    return one row per game with the rating gap at that point in time
    plus the actual cover outcome - ready to be filtered by any
    threshold combination without recomputing ratings.
    """
    flagged: list[dict] = []

    for season in sorted({g["season"] for g in games}):
        season_games = [g for g in games if g["season"] == season]
        # team -> list of point differentials from completed games this season
        history: dict[str, list[float]] = defaultdict(list)

        for g in season_games:
            home, away = g["home_team"], g["away_team"]
            home_hist, away_hist = history[home], history[away]

            if len(home_hist) >= MIN_GAMES_PLAYED and len(away_hist) >= MIN_GAMES_PLAYED:
                home_rating = sum(home_hist) / len(home_hist)
                away_rating = sum(away_hist) / len(away_hist)
                spread_line = float(g["spread_close"])
                expected_margin = home_rating - away_rating
                market_margin = -spread_line
                gap = expected_margin - market_margin
                pick_side = "home" if gap > 0 else "away"
                covered = g["home_covered"] if pick_side == "home" else (not g["home_covered"])

                flagged.append({
                    "season": season,
                    "week": g["week"],
                    "gap": abs(gap),
                    "spread": abs(spread_line),
                    "pick_side": pick_side,
                    "covered": covered,
                })

            # Update history with this game's actual point differential
            margin = g["home_score"] - g["away_score"]
            history[home].append(margin)
            history[away].append(-margin)

    return flagged


def sweep_thresholds(flagged: list[dict]) -> list[dict]:
    results = []
    for gap_thresh in GAP_THRESHOLDS:
        for spread_ceil in SPREAD_CEILINGS:
            matches = [
                f for f in flagged if f["gap"] >= gap_thresh and f["spread"] < spread_ceil
            ]
            n = len(matches)
            if n == 0:
                continue
            wins = sum(1 for m in matches if m["covered"])
            hit_rate = wins / n
            results.append({
                "min_gap": gap_thresh,
                "max_spread": spread_ceil,
                "n": n,
                "wins": wins,
                "hit_rate": round(hit_rate, 4),
            })
    return sorted(results, key=lambda r: (-r["hit_rate"], -r["n"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", nargs="+", type=int, default=[2023, 2024, 2025])
    args = parser.parse_args()

    games = load_games(args.seasons)
    logger.info("Loaded %d historical games with spread + result data", len(games))

    flagged = compute_flagged_bets(games)
    logger.info("Computed rating gap for %d games (after %d-game warmup per team)", len(flagged), MIN_GAMES_PLAYED)

    print(f"\nBaseline (all games, no filter): {sum(1 for f in flagged if f['covered'])}/{len(flagged)} "
          f"= {sum(1 for f in flagged if f['covered']) / len(flagged):.4f} hit rate\n")

    print(f"{'min_gap':>8} {'max_spread':>11} {'n':>5} {'wins':>5} {'hit_rate':>9}")
    for r in sweep_thresholds(flagged):
        print(f"{r['min_gap']:>8.1f} {r['max_spread']:>11.1f} {r['n']:>5} {r['wins']:>5} {r['hit_rate']:>9.4f}")

    # Task spec's original starting point, called out explicitly
    spec = [f for f in flagged if f["gap"] >= 7.0 and f["spread"] < 4.0]
    if spec:
        wins = sum(1 for f in spec if f["covered"])
        print(f"\nTask spec starting point (gap>=7, spread<4): {wins}/{len(spec)} = {wins/len(spec):.4f} hit rate")
    else:
        print("\nTask spec starting point (gap>=7, spread<4): 0 matching games")
