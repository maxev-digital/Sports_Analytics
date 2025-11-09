"""
Fix ROI calculations for backtest results
Recalculate ROI based on actual wins/losses/odds
"""
import sqlite3
import json

# Connect to database
conn = sqlite3.connect('database/backtests.db')
cursor = conn.cursor()

def american_to_decimal(american_odds):
    """Convert American odds to decimal multiplier"""
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1

def calculate_roi(wins, losses, pushes, avg_odds_american):
    """
    Calculate actual ROI based on wins/losses
    Assumes $100 flat bets
    """
    total_bets = wins + losses + pushes
    if total_bets == 0:
        return 0.0

    # Convert odds to decimal
    decimal_multiplier = american_to_decimal(avg_odds_american)

    # Calculate profit/loss
    total_wagered = total_bets * 100
    profit_from_wins = wins * (decimal_multiplier * 100 - 100)  # Win amount minus stake
    loss_from_losses = losses * 100  # Lose full stake

    net_profit = profit_from_wins - loss_from_losses
    roi = (net_profit / total_wagered) * 100

    return round(roi, 1)

# Get all backtest results
cursor.execute("""
    SELECT id, strategy_id, sport, bets_placed, wins, losses, pushes,
           win_rate, roi, avg_edge
    FROM backtest_results
    WHERE bets_placed > 0
""")

results = cursor.fetchall()

print("Checking ROI calculations...\n")
print(f"{'ID':<4} {'Strat':<6} {'Sport':<6} {'W-L-P':<12} {'WR%':<7} {'AvgOdds':<10} {'Old ROI':<9} {'New ROI':<9} {'Status'}")
print("=" * 100)

fixes_needed = []

for row in results:
    result_id, strat_id, sport, bets, wins, losses, pushes, win_rate, old_roi, avg_edge = row

    # Estimate average odds from edge
    # If edge is 10%, and we're betting at -110, that's roughly correct
    # This is an approximation - ideally we'd store actual odds
    if avg_edge > 0:
        # Positive edge strategies likely at negative odds
        estimated_odds = -110 - (avg_edge * 5)  # Rough estimate
    else:
        estimated_odds = -110

    # Calculate correct ROI
    new_roi = calculate_roi(wins, losses, pushes or 0, estimated_odds)

    # Check if ROI is way off
    roi_diff = abs(new_roi - old_roi)

    # Flag suspicious results
    status = "✅ OK"
    if win_rate == 100.0:
        status = "🔴 IMPOSSIBLE (100% WR)"
        fixes_needed.append((result_id, strat_id, new_roi))
    elif win_rate < 40.0 and old_roi > 0:
        status = "🔴 MATH ERROR"
        fixes_needed.append((result_id, strat_id, new_roi))
    elif roi_diff > 10.0:
        status = "⚠️ LARGE DIFF"
        fixes_needed.append((result_id, strat_id, new_roi))

    wl_display = f"{wins}-{losses}-{pushes or 0}"
    print(f"{result_id:<4} {strat_id:<6} {sport:<6} {wl_display:<12} {win_rate:<6.1f}% "
          f"{estimated_odds:<10.0f} {old_roi:<8.1f}% {new_roi:<8.1f}% {status}")

print("\n" + "=" * 100)
print(f"\n📊 Summary: {len(fixes_needed)} results need fixing\n")

# Ask user if they want to apply fixes
if fixes_needed:
    print("Strategies that need ROI recalculation:")
    for result_id, strat_id, new_roi in fixes_needed:
        print(f"  - Result ID {result_id} (Strategy {strat_id}): Update ROI to {new_roi:.1f}%")

    response = input("\nApply these fixes? (yes/no): ")
    if response.lower() == 'yes':
        for result_id, strat_id, new_roi in fixes_needed:
            cursor.execute("""
                UPDATE backtest_results
                SET roi = ?
                WHERE id = ?
            """, (new_roi, result_id))
        conn.commit()
        print(f"✅ Updated {len(fixes_needed)} results!")
    else:
        print("❌ No changes made.")

conn.close()
