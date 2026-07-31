"""
F5 Edge Validation — Join Actual Odds With Game Outcomes

This is the definitive test. For every game where we have BOTH:
  1. What the book was actually pricing (from Odds API)
  2. What actually happened (from MLB Stats API)

We compute: did the bet win? Was it +EV? What was the actual ROI?

This proves or disproves every edge in the matrix with real money math.

Usage:
  python3 validate_edges.py
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "f5_backtest.db"


def american_to_decimal(american: int) -> float:
    if american > 0:
        return 1 + american / 100
    return 1 + 100 / abs(american)


def implied_prob(american: int) -> float:
    return 1 / american_to_decimal(american)


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def validate(conn):
    """Join odds data with game outcomes and compute actual P&L"""

    # Check if we have odds data
    odds_count = conn.execute("SELECT COUNT(*) as c FROM f5_odds WHERE f5_3way_tie_odds IS NOT NULL").fetchone()["c"]
    total_count = conn.execute("SELECT COUNT(*) as c FROM f5_odds WHERE f5_total_line IS NOT NULL").fetchone()["c"]

    if odds_count == 0 and total_count == 0:
        print("No odds data found. Run pull_historical_odds.py first.")
        return None

    print(f"Odds data available: {odds_count} games with F5 3-way, {total_count} with F5 totals")

    results = {}

    # ─── 1. TIE BET VALIDATION ─────────────────────────────────────
    # Join: f5_odds (tie odds) + games (did it tie after 5?)
    tie_data = conn.execute("""
        SELECT
            o.game_date,
            o.away_team as odds_away,
            o.home_team as odds_home,
            o.f5_3way_tie_odds,
            o.f5_3way_away_odds,
            o.f5_3way_home_odds,
            o.f5_3way_best_tie_odds,
            g.tied_after_5,
            g.era_bucket,
            g.park_type,
            g.month,
            g.away_pitcher_era,
            g.home_pitcher_era
        FROM f5_odds o
        JOIN games g ON o.game_date = g.game_date
            AND o.away_team = g.away_team
            AND o.home_team = g.home_team
        WHERE o.f5_3way_tie_odds IS NOT NULL
    """).fetchall()

    if tie_data:
        results["tie_bets"] = _analyze_tie_bets(tie_data)

    # ─── 2. F5 TOTAL VALIDATION ────────────────────────────────────
    total_data = conn.execute("""
        SELECT
            o.game_date,
            o.away_team as odds_away,
            o.home_team as odds_home,
            o.f5_total_line,
            o.f5_over_odds,
            o.f5_under_odds,
            g.f5_total,
            g.era_bucket,
            g.park_type,
            g.month,
            g.away_pitcher_era,
            g.home_pitcher_era
        FROM f5_odds o
        JOIN games g ON o.game_date = g.game_date
            AND o.away_team = g.away_team
            AND o.home_team = g.home_team
        WHERE o.f5_total_line IS NOT NULL
    """).fetchall()

    if total_data:
        results["total_bets"] = _analyze_total_bets(total_data)

    # ─── 3. F5 ML VALIDATION ──────────────────────────────────────
    ml_data = conn.execute("""
        SELECT
            o.game_date,
            o.away_team as odds_away,
            o.home_team as odds_home,
            o.f5_ml_away_odds,
            o.f5_ml_home_odds,
            g.f5_leader,
            g.f5_fav_covered,
            g.era_bucket,
            g.park_type,
            g.month,
            g.away_pitcher_era,
            g.home_pitcher_era,
            g.lower_era
        FROM f5_odds o
        JOIN games g ON o.game_date = g.game_date
            AND o.away_team = g.away_team
            AND o.home_team = g.home_team
        WHERE o.f5_ml_away_odds IS NOT NULL
    """).fetchall()

    if ml_data:
        results["ml_bets"] = _analyze_ml_bets(ml_data)

    return results


def _analyze_tie_bets(data):
    """Simulate betting the tie on every qualifying game"""
    results = {"overall": {}, "by_condition": []}

    # Overall
    unit = 100
    total_pl = 0
    wins = 0
    losses = 0
    total_implied = 0

    for row in data:
        odds = row["f5_3way_tie_odds"]
        dec = american_to_decimal(odds)
        imp = implied_prob(odds)
        total_implied += imp

        if row["tied_after_5"]:
            pl = unit * (dec - 1)
            wins += 1
        else:
            pl = -unit
            losses += 1
        total_pl += pl

    n = len(data)
    actual_tie_rate = wins / n if n > 0 else 0
    avg_implied = total_implied / n if n > 0 else 0

    results["overall"] = {
        "games": n,
        "wins": wins,
        "losses": losses,
        "actual_tie_rate": round(actual_tie_rate * 100, 2),
        "avg_book_implied": round(avg_implied * 100, 2),
        "edge": round((actual_tie_rate - avg_implied) * 100, 2),
        "total_pl": round(total_pl, 2),
        "roi_pct": round(total_pl / (n * unit) * 100, 2) if n > 0 else 0,
        "unit_size": unit,
    }

    # By condition
    conditions = [
        ("Ace vs Ace", lambda r: r["era_bucket"] == "both_under_3"),
        ("Ace vs Ace + Pitcher Park", lambda r: r["era_bucket"] == "both_under_3" and r["park_type"] == "pitcher_park"),
        ("Ace vs Ace + April", lambda r: r["era_bucket"] == "both_under_3" and r["month"] == 4),
        ("Bad Starter", lambda r: r["era_bucket"] == "diff_over_1.5"),
        ("Pitcher Park", lambda r: r["park_type"] == "pitcher_park"),
        ("Hitter Park", lambda r: r["park_type"] in ("hitter_park", "coors_field")),
        ("April", lambda r: r["month"] == 4),
        ("July/August", lambda r: r["month"] in (7, 8)),
    ]

    for name, filter_fn in conditions:
        filtered = [r for r in data if filter_fn(r)]
        if len(filtered) < 10:
            continue

        w = sum(1 for r in filtered if r["tied_after_5"])
        l = len(filtered) - w
        pl = sum(
            unit * (american_to_decimal(r["f5_3way_tie_odds"]) - 1) if r["tied_after_5"] else -unit
            for r in filtered
        )
        avg_imp = sum(implied_prob(r["f5_3way_tie_odds"]) for r in filtered) / len(filtered)
        actual_rate = w / len(filtered)

        results["by_condition"].append({
            "condition": name,
            "games": len(filtered),
            "wins": w,
            "actual_tie_rate": round(actual_rate * 100, 2),
            "avg_book_implied": round(avg_imp * 100, 2),
            "edge": round((actual_rate - avg_imp) * 100, 2),
            "total_pl": round(pl, 2),
            "roi_pct": round(pl / (len(filtered) * unit) * 100, 2),
        })

    results["by_condition"].sort(key=lambda x: x["roi_pct"], reverse=True)
    return results


def _analyze_total_bets(data):
    """Simulate betting F5 unders and overs based on the actual line"""
    results = {"under_overall": {}, "over_overall": {}, "by_condition": []}

    unit = 100
    under_pl = 0
    over_pl = 0
    under_wins = 0
    over_wins = 0
    pushes = 0

    for row in data:
        line = row["f5_total_line"]
        actual = row["f5_total"]
        under_odds = row["f5_under_odds"]
        over_odds = row["f5_over_odds"]

        if actual < line:
            # Under wins
            under_pl += unit * (american_to_decimal(under_odds) - 1)
            over_pl -= unit
            under_wins += 1
        elif actual > line:
            # Over wins
            over_pl += unit * (american_to_decimal(over_odds) - 1)
            under_pl -= unit
            over_wins += 1
        else:
            pushes += 1  # Push — no P&L

    n = len(data) - pushes
    results["under_overall"] = {
        "games": len(data),
        "graded": n,
        "wins": under_wins,
        "win_rate": round(under_wins / n * 100, 2) if n > 0 else 0,
        "total_pl": round(under_pl, 2),
        "roi_pct": round(under_pl / (n * unit) * 100, 2) if n > 0 else 0,
    }
    results["over_overall"] = {
        "games": len(data),
        "graded": n,
        "wins": over_wins,
        "win_rate": round(over_wins / n * 100, 2) if n > 0 else 0,
        "total_pl": round(over_pl, 2),
        "roi_pct": round(over_pl / (n * unit) * 100, 2) if n > 0 else 0,
    }

    # By condition — under bets
    conditions = [
        ("Ace vs Ace", lambda r: r["era_bucket"] == "both_under_3"),
        ("Ace vs Ace + Pitcher Park", lambda r: r["era_bucket"] == "both_under_3" and r["park_type"] == "pitcher_park"),
        ("Bad Starter", lambda r: r["era_bucket"] == "diff_over_1.5"),
        ("Bad Starter + Hitter Park", lambda r: r["era_bucket"] == "diff_over_1.5" and r["park_type"] in ("hitter_park", "coors_field")),
        ("Pitcher Park", lambda r: r["park_type"] == "pitcher_park"),
        ("Coors Field", lambda r: r["park_type"] == "coors_field"),
    ]

    for name, filter_fn in conditions:
        filtered = [r for r in data if filter_fn(r)]
        if len(filtered) < 10:
            continue

        u_wins = sum(1 for r in filtered if r["f5_total"] < r["f5_total_line"])
        o_wins = sum(1 for r in filtered if r["f5_total"] > r["f5_total_line"])
        p = sum(1 for r in filtered if r["f5_total"] == r["f5_total_line"])
        graded = len(filtered) - p

        u_pl = sum(
            unit * (american_to_decimal(r["f5_under_odds"]) - 1) if r["f5_total"] < r["f5_total_line"]
            else (-unit if r["f5_total"] > r["f5_total_line"] else 0)
            for r in filtered
        )
        o_pl = sum(
            unit * (american_to_decimal(r["f5_over_odds"]) - 1) if r["f5_total"] > r["f5_total_line"]
            else (-unit if r["f5_total"] < r["f5_total_line"] else 0)
            for r in filtered
        )

        results["by_condition"].append({
            "condition": name,
            "games": len(filtered),
            "graded": graded,
            "under_wins": u_wins,
            "over_wins": o_wins,
            "pushes": p,
            "under_rate": round(u_wins / graded * 100, 2) if graded > 0 else 0,
            "over_rate": round(o_wins / graded * 100, 2) if graded > 0 else 0,
            "under_pl": round(u_pl, 2),
            "over_pl": round(o_pl, 2),
            "under_roi": round(u_pl / (graded * unit) * 100, 2) if graded > 0 else 0,
            "over_roi": round(o_pl / (graded * unit) * 100, 2) if graded > 0 else 0,
            "avg_line": round(sum(r["f5_total_line"] for r in filtered) / len(filtered), 2),
            "avg_actual": round(sum(r["f5_total"] for r in filtered) / len(filtered), 2),
        })

    return results


def _analyze_ml_bets(data):
    """Simulate F5 ML bets — bet the favorite (lower ERA side)"""
    results = {"fav_overall": {}, "dog_overall": {}, "by_condition": []}

    unit = 100
    fav_pl = 0
    dog_pl = 0
    fav_wins = 0
    dog_wins = 0
    ties_skipped = 0

    for row in data:
        if row["f5_leader"] == "tie":
            ties_skipped += 1
            # In F5 2-way ML, ties are typically graded as a push or loss
            # depending on the book. We'll treat as a loss (most common)
            fav_pl -= unit
            dog_pl -= unit
            continue

        lower_era = row["lower_era"]
        if lower_era == "unknown" or lower_era == "even":
            continue

        # Determine which side is the favorite (lower ERA)
        if lower_era == "away":
            fav_odds = row["f5_ml_away_odds"]
            dog_odds = row["f5_ml_home_odds"]
            fav_won = row["f5_leader"] == "away"
        else:
            fav_odds = row["f5_ml_home_odds"]
            dog_odds = row["f5_ml_away_odds"]
            fav_won = row["f5_leader"] == "home"

        if fav_odds is None or dog_odds is None:
            continue

        if fav_won:
            fav_pl += unit * (american_to_decimal(fav_odds) - 1)
            dog_pl -= unit
            fav_wins += 1
        else:
            fav_pl -= unit
            dog_pl += unit * (american_to_decimal(dog_odds) - 1)
            dog_wins += 1

    n = fav_wins + dog_wins
    results["fav_overall"] = {
        "graded": n,
        "wins": fav_wins,
        "win_rate": round(fav_wins / n * 100, 2) if n > 0 else 0,
        "total_pl": round(fav_pl, 2),
        "roi_pct": round(fav_pl / (n * unit) * 100, 2) if n > 0 else 0,
        "ties_as_losses": ties_skipped,
    }
    results["dog_overall"] = {
        "graded": n,
        "wins": dog_wins,
        "win_rate": round(dog_wins / n * 100, 2) if n > 0 else 0,
        "total_pl": round(dog_pl, 2),
        "roi_pct": round(dog_pl / (n * unit) * 100, 2) if n > 0 else 0,
    }

    return results


def print_validation(results):
    if not results:
        return

    print(f"\n{'='*80}")
    print(f"F5 EDGE VALIDATION — ACTUAL BOOK ODDS vs ACTUAL OUTCOMES")
    print(f"{'='*80}")

    if "tie_bets" in results:
        t = results["tie_bets"]
        o = t["overall"]
        print(f"\n--- F5 TIE BETS (straight bet on tie every game) ---")
        print(f"  Games: {o['games']} | Wins: {o['wins']} | Tie Rate: {o['actual_tie_rate']}%")
        print(f"  Avg Book Implied: {o['avg_book_implied']}% | Edge: {o['edge']}pp")
        print(f"  P&L: ${o['total_pl']:,.2f} | ROI: {o['roi_pct']}%")

        if t["by_condition"]:
            print(f"\n  {'Condition':<30} {'Games':>6} {'Wins':>5} {'Rate':>6} {'Book':>6} {'Edge':>6} {'P&L':>10} {'ROI':>7}")
            print(f"  {'-'*80}")
            for c in t["by_condition"]:
                print(f"  {c['condition']:<30} {c['games']:>6} {c['wins']:>5} {c['actual_tie_rate']:>5.1f}% "
                      f"{c['avg_book_implied']:>5.1f}% {c['edge']:>+5.1f}% ${c['total_pl']:>9,.2f} {c['roi_pct']:>+6.1f}%")

    if "total_bets" in results:
        t = results["total_bets"]
        print(f"\n--- F5 TOTAL BETS (under/over at book's line) ---")
        u = t["under_overall"]
        o = t["over_overall"]
        print(f"  Under: {u['wins']}/{u['graded']} ({u['win_rate']}%) | P&L: ${u['total_pl']:,.2f} | ROI: {u['roi_pct']}%")
        print(f"  Over:  {o['wins']}/{o['graded']} ({o['win_rate']}%) | P&L: ${o['total_pl']:,.2f} | ROI: {o['roi_pct']}%")

        if t["by_condition"]:
            print(f"\n  {'Condition':<30} {'Games':>6} {'U Rate':>7} {'O Rate':>7} {'AvgLine':>8} {'AvgAct':>7} {'U P&L':>9} {'O P&L':>9}")
            print(f"  {'-'*85}")
            for c in t["by_condition"]:
                print(f"  {c['condition']:<30} {c['graded']:>6} {c['under_rate']:>6.1f}% {c['over_rate']:>6.1f}% "
                      f"{c['avg_line']:>8.1f} {c['avg_actual']:>6.1f} ${c['under_pl']:>8,.2f} ${c['over_pl']:>8,.2f}")

    if "ml_bets" in results:
        m = results["ml_bets"]
        f = m["fav_overall"]
        d = m["dog_overall"]
        print(f"\n--- F5 ML BETS (fav = lower ERA side) ---")
        print(f"  Fav: {f['wins']}/{f['graded']} ({f['win_rate']}%) | P&L: ${f['total_pl']:,.2f} | ROI: {f['roi_pct']}%")
        print(f"  Dog: {d['wins']}/{d['graded']} ({d['win_rate']}%) | P&L: ${d['total_pl']:,.2f} | ROI: {d['roi_pct']}%")
        print(f"  Ties graded as loss: {f['ties_as_losses']}")


if __name__ == "__main__":
    conn = get_db()
    results = validate(conn)
    if results:
        print_validation(results)
        # Save
        json_path = Path(__file__).parent / "validation_results.json"
        with open(json_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to {json_path}")
    conn.close()
