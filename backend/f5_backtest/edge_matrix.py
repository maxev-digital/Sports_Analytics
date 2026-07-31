"""
F5 Edge Matrix — Compute Actual Hit Rates Across All Bet Types

For every factor combination, compute:
  1. Tie rate
  2. F5 Under hit rate at 4.5, 5.5, 6.5, 7.5
  3. F5 Over hit rate at same thresholds
  4. Favorite leads rate (ERA-based proxy)
  5. Underdog leads rate
  6. Average F5 total
  7. F5 margin (how often 1-run vs blowout)

Output: a structured matrix that the daily scanner can query.

Usage:
  python3 edge_matrix.py               # full matrix
  python3 edge_matrix.py --top 20      # top 20 edges only
"""

import sqlite3
import json
import sys
from pathlib import Path
from itertools import product

DB_PATH = Path(__file__).parent / "f5_backtest.db"
MIN_SAMPLE = 30  # minimum games for a cell to be reportable

# Typical book implied probabilities for comparison
BOOK_PRICING = {
    "tie": {
        "implied_range": (0.17, 0.22),  # +350 to +470
        "typical_implied": 0.19,        # ~+420
        "vig_pct": 5,
    },
    "f5_under_4.5": {
        "typical_implied": 0.52,  # -110 on a 4.5 line
        "vig_pct": 4.5,
    },
    "f5_over_4.5": {
        "typical_implied": 0.52,
        "vig_pct": 4.5,
    },
    "f5_under_5.5": {
        "typical_implied": 0.52,
        "vig_pct": 4.5,
    },
    "f5_over_5.5": {
        "typical_implied": 0.52,
        "vig_pct": 4.5,
    },
    "f5_fav_ml": {
        "typical_implied": 0.55,  # slight fav ~-120
        "vig_pct": 4.5,
    },
    "f5_dog_ml": {
        "typical_implied": 0.40,
        "vig_pct": 4.5,
    },
}

# Factor values to test
FACTORS = {
    "era_bucket": [
        ("both_under_3", "Ace vs Ace"),
        ("diff_under_0.5", "ERA diff < 0.5"),
        ("diff_0.5_to_1.0", "ERA diff 0.5-1.0"),
        ("diff_1.0_to_1.5", "ERA diff 1.0-1.5"),
        ("diff_over_1.5", "Bad starter (1.5+)"),
    ],
    "park_type": [
        ("pitcher_park", "Pitcher park"),
        ("neutral", "Neutral park"),
        ("hitter_park", "Hitter park"),
        ("coors_field", "Coors Field"),
    ],
    "total_bucket": [
        ("under_7", "Low total (< 7 runs)"),
        ("7_to_8", "Medium total (7-8)"),
        ("over_9", "High total (9-10)"),
        ("over_10", "Very high total (10+)"),
    ],
    "month": [
        ("4", "April"),
        ("5", "May"),
        ("6", "June"),
        ("7", "July"),
        ("8", "August"),
        ("9", "September"),
    ],
}


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def compute_cell(conn, where_clause, params=None):
    """Compute all bet type rates for a given filter"""
    sql = f"""
        SELECT
            COUNT(*) as games,
            SUM(tied_after_5) as ties,
            AVG(f5_total) as avg_f5_total,
            AVG(f5_margin) as avg_f5_margin,

            -- F5 Total thresholds
            SUM(CASE WHEN f5_total <= 4 THEN 1 ELSE 0 END) as under_4_5,
            SUM(CASE WHEN f5_total >= 5 THEN 1 ELSE 0 END) as over_4_5,
            SUM(CASE WHEN f5_total <= 5 THEN 1 ELSE 0 END) as under_5_5,
            SUM(CASE WHEN f5_total >= 6 THEN 1 ELSE 0 END) as over_5_5,
            SUM(CASE WHEN f5_total <= 6 THEN 1 ELSE 0 END) as under_6_5,
            SUM(CASE WHEN f5_total >= 7 THEN 1 ELSE 0 END) as over_6_5,
            SUM(CASE WHEN f5_total <= 7 THEN 1 ELSE 0 END) as under_7_5,
            SUM(CASE WHEN f5_total >= 8 THEN 1 ELSE 0 END) as over_7_5,

            -- F5 Leader (ERA-based fav/dog)
            SUM(CASE WHEN f5_fav_covered = 1 THEN 1 ELSE 0 END) as fav_leads,
            SUM(CASE WHEN f5_dog_covered = 1 THEN 1 ELSE 0 END) as dog_leads,

            -- F5 Margin distribution
            SUM(CASE WHEN f5_margin = 0 THEN 1 ELSE 0 END) as margin_0,
            SUM(CASE WHEN f5_margin = 1 THEN 1 ELSE 0 END) as margin_1,
            SUM(CASE WHEN f5_margin = 2 THEN 1 ELSE 0 END) as margin_2,
            SUM(CASE WHEN f5_margin >= 3 THEN 1 ELSE 0 END) as margin_3plus

        FROM games
        WHERE {where_clause}
    """
    row = conn.execute(sql, params or {}).fetchone()
    games = row["games"]

    if games < MIN_SAMPLE:
        return None

    def rate(count):
        return round(count / games, 4) if games > 0 else 0

    def pct(count):
        return round(count / games * 100, 2) if games > 0 else 0

    return {
        "games": games,
        "avg_f5_total": round(row["avg_f5_total"], 2),
        "avg_f5_margin": round(row["avg_f5_margin"], 2),
        "rates": {
            "tie": rate(row["ties"]),
            "under_4_5": rate(row["under_4_5"]),
            "over_4_5": rate(row["over_4_5"]),
            "under_5_5": rate(row["under_5_5"]),
            "over_5_5": rate(row["over_5_5"]),
            "under_6_5": rate(row["under_6_5"]),
            "over_6_5": rate(row["over_6_5"]),
            "under_7_5": rate(row["under_7_5"]),
            "over_7_5": rate(row["over_7_5"]),
            "fav_leads": rate(row["fav_leads"]),
            "dog_leads": rate(row["dog_leads"]),
        },
        "pcts": {
            "tie": pct(row["ties"]),
            "under_4_5": pct(row["under_4_5"]),
            "over_4_5": pct(row["over_4_5"]),
            "under_5_5": pct(row["under_5_5"]),
            "over_5_5": pct(row["over_5_5"]),
            "under_6_5": pct(row["under_6_5"]),
            "over_6_5": pct(row["over_6_5"]),
            "under_7_5": pct(row["under_7_5"]),
            "over_7_5": pct(row["over_7_5"]),
            "fav_leads": pct(row["fav_leads"]),
            "dog_leads": pct(row["dog_leads"]),
        },
        "margin_dist": {
            "tied": pct(row["margin_0"]),
            "one_run": pct(row["margin_1"]),
            "two_runs": pct(row["margin_2"]),
            "three_plus": pct(row["margin_3plus"]),
        },
    }


def find_edges(cell_data):
    """Compare actual rates to book pricing, find +EV spots"""
    if not cell_data:
        return []

    edges = []
    rates = cell_data["rates"]

    comparisons = [
        ("F5 Tie", "tie", BOOK_PRICING["tie"]["typical_implied"]),
        ("F5 Under 4.5", "under_4_5", BOOK_PRICING["f5_under_4.5"]["typical_implied"]),
        ("F5 Over 4.5", "over_4_5", BOOK_PRICING["f5_over_4.5"]["typical_implied"]),
        ("F5 Under 5.5", "under_5_5", BOOK_PRICING["f5_under_5.5"]["typical_implied"]),
        ("F5 Over 5.5", "over_5_5", BOOK_PRICING["f5_over_5.5"]["typical_implied"]),
        ("F5 Fav ML", "fav_leads", BOOK_PRICING["f5_fav_ml"]["typical_implied"]),
        ("F5 Dog ML", "dog_leads", BOOK_PRICING["f5_dog_ml"]["typical_implied"]),
    ]

    for bet_name, rate_key, book_implied in comparisons:
        actual = rates[rate_key]
        edge = actual - book_implied

        if edge > 0.02:  # 2%+ edge threshold
            edges.append({
                "bet": bet_name,
                "actual_rate": round(actual * 100, 1),
                "book_implied": round(book_implied * 100, 1),
                "edge_pct": round(edge * 100, 1),
                "games": cell_data["games"],
            })

    return edges


def build_full_matrix(conn):
    """Build the complete matrix: single factors + key combinations"""
    results = {
        "baseline": None,
        "single_factors": {},
        "combinations": [],
        "all_edges": [],
    }

    # Baseline (all games)
    results["baseline"] = compute_cell(conn, "1=1")

    # Single factors
    for factor_name, values in FACTORS.items():
        results["single_factors"][factor_name] = []
        for value, label in values:
            if factor_name == "month":
                where = f"month = {value}"
            else:
                where = f"{factor_name} = '{value}'"

            cell = compute_cell(conn, where)
            if cell:
                edges = find_edges(cell)
                results["single_factors"][factor_name].append({
                    "value": value,
                    "label": label,
                    **cell,
                    "edges": edges,
                })
                for e in edges:
                    e["condition"] = f"{factor_name}={label}"
                    results["all_edges"].append(e)

    # Key combinations (2-factor)
    combo_tests = [
        ("Ace vs Ace + Pitcher Park", "era_bucket = 'both_under_3' AND park_type = 'pitcher_park'"),
        ("Ace vs Ace + Low Total", "era_bucket = 'both_under_3' AND total_bucket = 'under_7'"),
        ("Ace vs Ace + April", "era_bucket = 'both_under_3' AND month = 4"),
        ("Bad Starter + High Total", "era_bucket = 'diff_over_1.5' AND total_bucket IN ('over_9','over_10')"),
        ("Bad Starter + Hitter Park", "era_bucket = 'diff_over_1.5' AND park_type IN ('hitter_park','coors_field')"),
        ("Bad Starter + July/Aug", "era_bucket = 'diff_over_1.5' AND month IN (7,8)"),
        ("Hitter Park + High Total", "park_type IN ('hitter_park','coors_field') AND total_bucket IN ('over_9','over_10')"),
        ("Pitcher Park + Low Total", "park_type = 'pitcher_park' AND total_bucket = 'under_7'"),
        ("Pitcher Park + April", "park_type = 'pitcher_park' AND month = 4"),
        ("Even ERA + Low Total", "ml_proximity_bucket = 'even' AND total_bucket = 'under_7'"),
        ("Even ERA + Pitcher Park", "ml_proximity_bucket = 'even' AND park_type = 'pitcher_park'"),
        ("Coors + High Total", "park_type = 'coors_field' AND total_bucket IN ('over_9','over_10')"),
        ("Coors + Bad Starter", "park_type = 'coors_field' AND era_bucket = 'diff_over_1.5'"),
        # 3-factor combos
        ("Ace + Pitcher Park + Low Total", "era_bucket = 'both_under_3' AND park_type = 'pitcher_park' AND total_bucket = 'under_7'"),
        ("Ace + Pitcher Park + April", "era_bucket = 'both_under_3' AND park_type = 'pitcher_park' AND month = 4"),
        ("Ace + Low Total + April", "era_bucket = 'both_under_3' AND total_bucket = 'under_7' AND month = 4"),
        ("Bad Starter + Hitter Park + High Total", "era_bucket = 'diff_over_1.5' AND park_type IN ('hitter_park','coors_field') AND total_bucket IN ('over_9','over_10')"),
        ("Bad Starter + Hitter Park + July/Aug", "era_bucket = 'diff_over_1.5' AND park_type IN ('hitter_park','coors_field') AND month IN (7,8)"),
    ]

    for name, where in combo_tests:
        cell = compute_cell(conn, where)
        if cell:
            edges = find_edges(cell)
            results["combinations"].append({
                "name": name,
                "where": where,
                **cell,
                "edges": edges,
            })
            for e in edges:
                e["condition"] = name
                results["all_edges"].append(e)

    # Sort all edges by edge size
    results["all_edges"].sort(key=lambda x: x["edge_pct"], reverse=True)

    return results


def print_matrix(results, top_n=None):
    """Print the edge matrix"""
    b = results["baseline"]
    print(f"\n{'='*90}")
    print(f"F5 EDGE MATRIX — 4,857 Games (2023-2024)")
    print(f"{'='*90}")
    print(f"\nBASELINE (all games): Avg F5 total: {b['avg_f5_total']}  |  Tie: {b['pcts']['tie']}%  |  "
          f"U4.5: {b['pcts']['under_4_5']}%  |  O4.5: {b['pcts']['over_4_5']}%  |  "
          f"Fav leads: {b['pcts']['fav_leads']}%  |  Dog leads: {b['pcts']['dog_leads']}%")

    # Single factors
    for factor_name, cells in results["single_factors"].items():
        print(f"\n--- {factor_name.upper()} ---")
        print(f"  {'Value':<22} {'Games':>6} {'AvgTot':>7} {'Tie%':>6} {'U4.5':>6} {'U5.5':>6} {'O5.5':>6} {'O7.5':>6} {'Fav%':>6} {'Dog%':>6} {'Edges':>6}")
        print(f"  {'-'*88}")
        for c in cells:
            edge_count = len(c["edges"])
            edge_mark = f"  {edge_count}" if edge_count > 0 else "   -"
            print(f"  {c['label']:<22} {c['games']:>6} {c['avg_f5_total']:>7.1f} "
                  f"{c['pcts']['tie']:>5.1f}% {c['pcts']['under_4_5']:>5.1f}% "
                  f"{c['pcts']['under_5_5']:>5.1f}% {c['pcts']['over_5_5']:>5.1f}% "
                  f"{c['pcts']['over_7_5']:>5.1f}% {c['pcts']['fav_leads']:>5.1f}% "
                  f"{c['pcts']['dog_leads']:>5.1f}% {edge_mark}")

    # Combinations
    print(f"\n--- KEY COMBINATIONS ---")
    print(f"  {'Condition':<40} {'Games':>6} {'AvgTot':>7} {'Tie%':>6} {'U4.5':>6} {'U5.5':>6} {'O5.5':>6} {'Fav%':>6} {'Dog%':>6}")
    print(f"  {'-'*88}")
    for c in results["combinations"]:
        print(f"  {c['name']:<40} {c['games']:>6} {c['avg_f5_total']:>7.1f} "
              f"{c['pcts']['tie']:>5.1f}% {c['pcts']['under_4_5']:>5.1f}% "
              f"{c['pcts']['under_5_5']:>5.1f}% {c['pcts']['over_5_5']:>5.1f}% "
              f"{c['pcts']['fav_leads']:>5.1f}% {c['pcts']['dog_leads']:>5.1f}%")

    # Top edges
    edges = results["all_edges"]
    if top_n:
        edges = edges[:top_n]
    print(f"\n{'='*90}")
    print(f"TOP +EV EDGES (actual rate > book implied by 2%+)")
    print(f"{'='*90}")
    print(f"  {'Condition':<40} {'Bet':<16} {'Actual':>7} {'Book':>7} {'Edge':>7} {'Games':>6}")
    print(f"  {'-'*88}")
    for e in edges:
        print(f"  {e['condition']:<40} {e['bet']:<16} {e['actual_rate']:>5.1f}%  {e['book_implied']:>5.1f}%  "
              f"+{e['edge_pct']:>4.1f}%  {e['games']:>5}")


if __name__ == "__main__":
    conn = get_db()
    results = build_full_matrix(conn)
    top_n = None
    if "--top" in sys.argv:
        idx = sys.argv.index("--top") + 1
        top_n = int(sys.argv[idx])
    print_matrix(results, top_n)

    # Save
    json_path = Path(__file__).parent / "edge_matrix.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nFull matrix saved to {json_path}")
    conn.close()
