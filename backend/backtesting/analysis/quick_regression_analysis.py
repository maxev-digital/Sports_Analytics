"""
Quick Closing Total Regression Analysis
Fast version focusing on core insights
"""

import sys
from pathlib import Path
import statistics

sys.path.append(str(Path(__file__).parent.parent))
from database.backtest_db import BacktestDB


def main():
    print("\n" + "="*80)
    print("QUICK CLOSING TOTAL REGRESSION ANALYSIS")
    print("="*80)

    db = BacktestDB()
    conn = db.get_connection()
    cursor = conn.cursor()

    # Get games with matched closing totals (simple direct join)
    print("Loading games with closing totals...")

    # Get one closing total per game from FanDuel (most common line value per game)
    cursor.execute("""
        SELECT DISTINCT
            g.date,
            g.home_team,
            g.away_team,
            g.home_score + g.away_score as actual_total,
            g.q1_home + g.q1_away as q1_total,
            g.q2_home + g.q2_away as q2_total,
            g.q3_home + g.q3_away as q3_total,
            g.q4_home + g.q4_away as q4_total,
            (
                SELECT o2.line_value
                FROM odds_history o2
                WHERE o2.home_team = g.home_team
                  AND o2.away_team = g.away_team
                  AND date(o2.timestamp) = date(g.date)
                  AND o2.market_type = 'totals'
                  AND o2.bookmaker = 'fanduel'
                GROUP BY o2.line_value
                ORDER BY COUNT(*) DESC
                LIMIT 1
            ) as closing_total
        FROM historical_games g
        WHERE EXISTS (
            SELECT 1 FROM odds_history o
            WHERE o.home_team = g.home_team
              AND o.away_team = g.away_team
              AND date(o.timestamp) = date(g.date)
              AND o.market_type = 'totals'
              AND o.bookmaker = 'fanduel'
        )
        AND g.home_score IS NOT NULL
        AND g.q1_home IS NOT NULL
        ORDER BY g.date
        LIMIT 500
    """)

    games = []
    for row in cursor.fetchall():
        date, home, away, actual, q1, q2, q3, q4, closing = row
        games.append({
            'date': date,
            'home_team': home,
            'away_team': away,
            'actual_total': actual,
            'closing_total': closing,
            'deviation': actual - closing,
            'q1_total': q1,
            'half_total': q1 + q2,
            'q3_end_total': q1 + q2 + q3,
            'q4_total': q4
        })

    conn.close()

    if len(games) < 10:
        print(f"\n[WARNING] Only found {len(games)} matched games")
        print("Odds data is still being fetched in background...")
        return

    print(f"[OK] Analyzing {len(games)} games\n")

    # Calculate deviations
    deviations = [g['deviation'] for g in games]
    mean_dev = statistics.mean(deviations)
    std_dev = statistics.stdev(deviations) if len(deviations) > 1 else 0

    # Count distribution
    overs = sum(1 for d in deviations if d > 0)
    unders = sum(1 for d in deviations if d < 0)
    pushes = sum(1 for d in deviations if d == 0)

    # Analyze halftime patterns
    halftime_devs = []
    for g in games:
        expected_half = g['closing_total'] / 2
        actual_half = g['half_total']
        halftime_devs.append(actual_half - expected_half)

    half_mean = statistics.mean(halftime_devs)
    half_std = statistics.stdev(halftime_devs) if len(halftime_devs) > 1 else 0

    # Print results
    print("="*80)
    print("CORE REGRESSION STATISTICS")
    print("="*80)
    print(f"Sample Size: {len(games)} games\n")

    print(f"Mean Deviation (Actual - Closing): {mean_dev:+.2f} points")
    print(f"Standard Deviation: {std_dev:.2f} points\n")

    print("Normal Variance Windows:")
    print(f"  68% of games fall within: ±{std_dev:.1f} points")
    print(f"  95% of games fall within: ±{std_dev * 2:.1f} points")
    print(f"  99.7% of games fall within: ±{std_dev * 3:.1f} points\n")

    print("Distribution:")
    print(f"  Overs: {overs} ({overs/len(games)*100:.1f}%)")
    print(f"  Unders: {unders} ({unders/len(games)*100:.1f}%)")
    print(f"  Pushes: {pushes}\n")

    print("="*80)
    print("HALFTIME REGRESSION PATTERNS")
    print("="*80)
    print(f"Mean Halftime Deviation: {half_mean:+.2f} points")
    print(f"Halftime Std Deviation: {half_std:.2f} points\n")

    print("Interpretation:")
    if abs(half_mean) < 2:
        print("  [OK] Market efficiently prices halves (minimal bias)")
    else:
        bias = "OVER" if half_mean > 0 else "UNDER"
        print(f"  [!] Halves tend to go {bias} by {abs(half_mean):.1f} points")

    print("\n" + "="*80)
    print("LIVE BETTING STRATEGY IMPLICATIONS")
    print("="*80)
    print(f"\nWhen live total deviates beyond +/-{std_dev * 1.5:.1f} points from closing:")
    print("  -> Regression opportunity likely exists")
    print(f"\nExample triggers:")
    print(f"  Closing Total: 220.0")
    print(f"  Upper trigger: {220 + (std_dev * 1.5):.1f} (bet UNDER)")
    print(f"  Lower trigger: {220 - (std_dev * 1.5):.1f} (bet OVER)")

    print("\n" + "="*80)
    print("SAMPLE GAMES")
    print("="*80)
    for game in games[:5]:
        result = "OVER" if game['deviation'] > 0 else "UNDER" if game['deviation'] < 0 else "PUSH"
        print(f"{game['date']}: {game['away_team']} @ {game['home_team']}")
        print(f"  Closing: {game['closing_total']:.1f}, Actual: {game['actual_total']}, Dev: {game['deviation']:+.1f} ({result})")

    print("\n" + "="*80)
    print(f"ANALYSIS COMPLETE - {len(games)} games analyzed")
    print("="*80)


if __name__ == "__main__":
    main()
