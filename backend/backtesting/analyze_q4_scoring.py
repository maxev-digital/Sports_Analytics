"""
Analyze actual Q4 scoring to calibrate the End-Game Unders strategy
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from database.backtest_db import BacktestDB

def analyze_q4():
    """Calculate actual Q4 averages from our database"""
    db = BacktestDB()
    games = db.get_games(sport='NBA', limit=10000)

    print("="*60)
    print("Q4 SCORING ANALYSIS")
    print("="*60)
    print(f"Total games analyzed: {len(games)}\n")

    # Calculate Q4 totals
    q4_totals = []
    blowout_q4 = []  # Q4 scoring in blowouts only
    close_q4 = []    # Q4 scoring in close games

    for game in games:
        q4_total = game['q4_home'] + game['q4_away']
        q4_totals.append(q4_total)

        # Check if blowout after Q3
        home_q3 = game['q1_home'] + game['q2_home'] + game['q3_home']
        away_q3 = game['q1_away'] + game['q2_away'] + game['q3_away']
        q3_diff = abs(home_q3 - away_q3)

        if q3_diff >= 15:
            blowout_q4.append(q4_total)
        else:
            close_q4.append(q4_total)

    # Calculate averages
    avg_q4 = sum(q4_totals) / len(q4_totals) if q4_totals else 0
    avg_blowout = sum(blowout_q4) / len(blowout_q4) if blowout_q4 else 0
    avg_close = sum(close_q4) / len(close_q4) if close_q4 else 0

    print(f"Overall Q4 Average: {avg_q4:.1f} points")
    print(f"\nBlowout games (15+ pts after Q3):")
    print(f"  Count: {len(blowout_q4)}")
    print(f"  Avg Q4: {avg_blowout:.1f} points")
    print(f"\nClose games (<15 pts after Q3):")
    print(f"  Count: {len(close_q4)}")
    print(f"  Avg Q4: {avg_close:.1f} points")

    # Find optimal line
    print(f"\n" + "="*60)
    print("OPTIMAL LINE ANALYSIS")
    print("="*60)

    for line in range(48, 66, 2):
        wins = sum(1 for total in blowout_q4 if total < line)
        losses = sum(1 for total in blowout_q4 if total > line)
        pushes = sum(1 for total in blowout_q4 if total == line)

        total_bets = wins + losses
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
        profit = (wins * 0.91) - losses
        roi = (profit / total_bets * 100) if total_bets > 0 else 0

        if total_bets > 0:
            status = "+" if roi > 0 else " "
            print(f"{status} Line {line}: {win_rate:.1f}% WR, {roi:+.1f}% ROI ({wins}W-{losses}L-{pushes}P)")

if __name__ == "__main__":
    analyze_q4()
