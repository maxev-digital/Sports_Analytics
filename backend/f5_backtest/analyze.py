"""
F5 Backtest Analysis — Query Real Data

Reads from the SQLite database populated by data_pipeline.py
and computes actual tie rates by every factor bucket.

Compares measured rates to our modeled estimates.

Usage:
  python3 analyze.py                    # full analysis
  python3 analyze.py --factor park_type # single factor breakdown
"""

import sqlite3
import json
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "f5_backtest.db"

# Our modeled estimates for comparison
MODELED_RATES = {
    "overall": 0.118,
    "park_type": {
        "pitcher_park": 0.138, "neutral": 0.116,
        "hitter_park": 0.091, "coors_field": 0.077,
    },
    "era_bucket": {
        "both_under_3": 0.158, "diff_under_0.5": 0.130,
        "diff_0.5_to_1.0": 0.113, "diff_1.0_to_1.5": 0.104,
        "diff_over_1.5": 0.088,
    },
    "total_bucket": {
        "under_7": 0.142, "7_to_8": 0.118,
        "8_to_9": 0.115, "over_9": 0.094,
        "over_10": 0.085,
    },
    "month": {
        4: 0.125, 5: 0.119, 6: 0.114,
        7: 0.110, 8: 0.113, 9: 0.121,
    },
}


def get_db():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Run data_pipeline.py first to populate the database.")
        sys.exit(1)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def query_tie_rate(conn, where_clause="1=1", params=None):
    """Get tie rate for a given filter"""
    sql = f"""
        SELECT
            COUNT(*) as total_games,
            SUM(tied_after_5) as ties,
            ROUND(CAST(SUM(tied_after_5) AS REAL) / COUNT(*) * 100, 2) as tie_rate_pct
        FROM games
        WHERE {where_clause}
    """
    row = conn.execute(sql, params or {}).fetchone()
    return {
        "total_games": row["total_games"],
        "ties": row["ties"],
        "tie_rate_pct": row["tie_rate_pct"],
    }


def full_analysis(conn):
    """Run complete analysis across all factor buckets"""
    results = {}

    # 1. Overall
    overall = query_tie_rate(conn)
    modeled = MODELED_RATES["overall"] * 100
    results["overall"] = {
        **overall,
        "modeled_pct": modeled,
        "difference": round(overall["tie_rate_pct"] - modeled, 2) if overall["tie_rate_pct"] else None,
    }

    # 2. By season
    results["by_season"] = []
    seasons = conn.execute("SELECT DISTINCT season FROM games ORDER BY season").fetchall()
    for row in seasons:
        s = row["season"]
        sr = query_tie_rate(conn, "season = :s", {"s": s})
        results["by_season"].append({"season": s, **sr})

    # 3. By park type
    results["by_park_type"] = _bucket_analysis(conn, "park_type", MODELED_RATES.get("park_type", {}))

    # 4. By ERA bucket
    results["by_era_bucket"] = _bucket_analysis(conn, "era_bucket", MODELED_RATES.get("era_bucket", {}))

    # 5. By total bucket (using final game total as proxy for O/U line)
    results["by_total_bucket"] = _bucket_analysis(conn, "total_bucket", MODELED_RATES.get("total_bucket", {}))

    # 6. By month
    results["by_month"] = []
    months = conn.execute("SELECT DISTINCT month FROM games WHERE month BETWEEN 4 AND 9 ORDER BY month").fetchall()
    month_names = {4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
    for row in months:
        m = row["month"]
        mr = query_tie_rate(conn, "month = :m", {"m": m})
        modeled_m = MODELED_RATES.get("month", {}).get(m, None)
        results["by_month"].append({
            "month": m,
            "month_name": month_names.get(m, str(m)),
            **mr,
            "modeled_pct": modeled_m * 100 if modeled_m else None,
            "difference": round(mr["tie_rate_pct"] - modeled_m * 100, 2) if modeled_m and mr["tie_rate_pct"] else None,
        })

    # 7. KEY COMBOS — the ones that matter for the strategy
    results["key_combinations"] = []

    combos = [
        {
            "name": "Ace vs Ace (both ERA < 3.50)",
            "where": "era_bucket = 'both_under_3'",
        },
        {
            "name": "Ace vs Ace + Pitcher Park",
            "where": "era_bucket = 'both_under_3' AND park_type = 'pitcher_park'",
        },
        {
            "name": "Ace vs Ace + Pitcher Park + Low Total (<7 runs)",
            "where": "era_bucket = 'both_under_3' AND park_type = 'pitcher_park' AND total_bucket = 'under_7'",
        },
        {
            "name": "Ace vs Ace + Pitcher Park + April",
            "where": "era_bucket = 'both_under_3' AND park_type = 'pitcher_park' AND month = 4",
        },
        {
            "name": "Ace vs Ace + Any Low Total Game",
            "where": "era_bucket = 'both_under_3' AND total_bucket = 'under_7'",
        },
        {
            "name": "Bad Starter (ERA diff > 1.5) + High Total (>9 runs)",
            "where": "era_bucket = 'diff_over_1.5' AND total_bucket IN ('over_9', 'over_10')",
        },
        {
            "name": "Hitter Park + High Total (>9 runs)",
            "where": "park_type IN ('hitter_park', 'coors_field') AND total_bucket IN ('over_9', 'over_10')",
        },
        {
            "name": "Coors Field Only",
            "where": "park_type = 'coors_field'",
        },
        {
            "name": "Coors Field + High Total",
            "where": "park_type = 'coors_field' AND total_bucket IN ('over_9', 'over_10')",
        },
        {
            "name": "Pitcher Park + Low Total + April",
            "where": "park_type = 'pitcher_park' AND total_bucket = 'under_7' AND month = 4",
        },
        {
            "name": "ALL FAVORABLE: Ace+Ace, Pitcher Park, Low Total, April",
            "where": "era_bucket = 'both_under_3' AND park_type = 'pitcher_park' AND total_bucket = 'under_7' AND month = 4",
        },
        {
            "name": "ALL UNFAVORABLE: Bad Starter, Hitter Park, High Total, July",
            "where": "era_bucket = 'diff_over_1.5' AND park_type IN ('hitter_park', 'coors_field') AND total_bucket IN ('over_9', 'over_10') AND month = 7",
        },
    ]

    for combo in combos:
        cr = query_tie_rate(conn, combo["where"])
        results["key_combinations"].append({
            "name": combo["name"],
            **cr,
        })

    return results


def _bucket_analysis(conn, column, modeled_dict):
    rows = conn.execute(
        f"SELECT DISTINCT {column} FROM games WHERE {column} != 'unknown' ORDER BY {column}"
    ).fetchall()

    results = []
    for row in rows:
        val = row[column]
        br = query_tie_rate(conn, f"{column} = :val", {"val": val})
        modeled = modeled_dict.get(val, None)
        results.append({
            "value": val,
            **br,
            "modeled_pct": modeled * 100 if modeled else None,
            "difference": round(br["tie_rate_pct"] - modeled * 100, 2) if modeled and br["tie_rate_pct"] else None,
        })

    return results


def print_analysis(results):
    """Pretty print the analysis"""
    o = results["overall"]
    print(f"\n{'='*70}")
    print(f"F5 TIE RATE BACKTEST — ACTUAL vs MODELED")
    print(f"{'='*70}")
    print(f"\nOVERALL: {o['tie_rate_pct']}% actual ({o['ties']:,} ties in {o['total_games']:,} games)")
    print(f"  Modeled: {o['modeled_pct']}%  |  Difference: {o['difference']:+.2f}pp")

    print(f"\nBY SEASON:")
    for s in results["by_season"]:
        print(f"  {s['season']}: {s['tie_rate_pct']}% ({s['ties']:,}/{s['total_games']:,})")

    for label, key in [
        ("BY PARK TYPE", "by_park_type"),
        ("BY ERA BUCKET", "by_era_bucket"),
        ("BY TOTAL RUNS (proxy for O/U)", "by_total_bucket"),
    ]:
        print(f"\n{label}:")
        print(f"  {'Value':<20} {'Actual':>7} {'Modeled':>8} {'Diff':>7} {'Games':>8} {'Ties':>6}")
        print(f"  {'-'*60}")
        for b in results[key]:
            mod = f"{b['modeled_pct']:.1f}%" if b.get('modeled_pct') else "  N/A"
            diff = f"{b['difference']:+.2f}" if b.get('difference') is not None else "  N/A"
            print(f"  {b['value']:<20} {b['tie_rate_pct']:>6.2f}% {mod:>8} {diff:>6}pp {b['total_games']:>7,} {b['ties']:>5,}")

    print(f"\nBY MONTH:")
    for m in results["by_month"]:
        mod = f"{m['modeled_pct']:.1f}%" if m.get('modeled_pct') else "N/A"
        diff = f"{m['difference']:+.2f}" if m.get('difference') is not None else "N/A"
        print(f"  {m['month_name']:<12} {m['tie_rate_pct']:>6.2f}% (modeled: {mod}, diff: {diff}pp) — {m['total_games']:,} games")

    print(f"\n{'='*70}")
    print(f"KEY COMBINATIONS — Strategy Validation")
    print(f"{'='*70}")
    print(f"  {'Condition':<55} {'Tie%':>7} {'Games':>7} {'Ties':>5}")
    print(f"  {'-'*78}")
    for c in results["key_combinations"]:
        rate = f"{c['tie_rate_pct']:.2f}%" if c["total_games"] > 0 else "N/A"
        print(f"  {c['name']:<55} {rate:>7} {c['total_games']:>7,} {c['ties']:>5,}")

    # Verdict
    print(f"\n{'='*70}")
    print("MODEL VALIDATION VERDICT")
    print(f"{'='*70}")

    ace_ace = next((c for c in results["key_combinations"] if "Ace vs Ace (" in c["name"]), None)
    peak = next((c for c in results["key_combinations"] if "ALL FAVORABLE" in c["name"]), None)
    coors = next((c for c in results["key_combinations"] if c["name"] == "Coors Field Only"), None)

    if ace_ace and ace_ace["total_games"] > 0:
        print(f"  Ace vs Ace: {ace_ace['tie_rate_pct']}% actual vs 15.8% modeled — "
              f"{'VALIDATED' if abs(ace_ace['tie_rate_pct'] - 15.8) < 3 else 'NEEDS ADJUSTMENT'}")
    if coors and coors["total_games"] > 0:
        print(f"  Coors Field: {coors['tie_rate_pct']}% actual vs 7.7% modeled — "
              f"{'VALIDATED' if abs(coors['tie_rate_pct'] - 7.7) < 3 else 'NEEDS ADJUSTMENT'}")
    if peak and peak["total_games"] > 0:
        print(f"  Peak Stack: {peak['tie_rate_pct']}% actual vs ~22% modeled — "
              f"{'VALIDATED' if peak['tie_rate_pct'] > 18 else 'NEEDS ADJUSTMENT'}")
        print(f"  (Sample size: {peak['total_games']} games — "
              f"{'adequate' if peak['total_games'] > 50 else 'SMALL — interpret with caution'})")


if __name__ == "__main__":
    conn = get_db()
    results = full_analysis(conn)
    print_analysis(results)

    # Save to JSON for the API
    json_path = Path(__file__).parent / "backtest_results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {json_path}")
    conn.close()
