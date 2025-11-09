"""
Generate mock backtest data for all "pending" strategies
This provides realistic historical performance data for display purposes
"""

import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path to import BacktestDB
sys.path.append(str(Path(__file__).parent.parent))

from backtesting.database.backtest_db import BacktestDB


# Strategy definitions from strategies.py
PENDING_STRATEGIES = [
    {"id": 1, "name": "The Hot-Shooting Fade", "sports": ["NBA", "NCAA Basketball"], "difficulty": "EASY"},
    {"id": 2, "name": "Momentum Shift Betting", "sports": ["NBA", "NFL", "NHL"], "difficulty": "MEDIUM"},
    {"id": 3, "name": "Injury Cascade Props", "sports": ["NBA", "NFL"], "difficulty": "HARD"},
    {"id": 4, "name": "The Pace Trap", "sports": ["NBA", "NCAA Basketball"], "difficulty": "EASY"},
    {"id": 5, "name": "Foul Trouble Overs", "sports": ["NBA", "NCAA Basketball"], "difficulty": "MEDIUM"},
    {"id": 7, "name": "Blowout Contrarian Spreads", "sports": ["NBA", "NFL"], "difficulty": "MEDIUM"},
    {"id": 9, "name": "Overtime Total Resets", "sports": ["NBA", "NFL", "NHL"], "difficulty": "MEDIUM"},
    {"id": 10, "name": "Fatigue Spreads (Back-to-Backs)", "sports": ["NBA", "NHL"], "difficulty": "EASY"},
    {"id": 11, "name": "Coaching Timeout Value", "sports": ["NBA", "NFL"], "difficulty": "HARD"},
    {"id": 12, "name": "Weather-Driven Live Totals", "sports": ["NFL", "MLB"], "difficulty": "MEDIUM"},
    {"id": 13, "name": "Favorite Comeback Detection", "sports": ["NBA"], "difficulty": "MEDIUM"},
    {"id": 15, "name": "Line Movement Arbitrage", "sports": ["NBA", "NFL", "NHL", "MLB"], "difficulty": "MEDIUM"},
    {"id": 16, "name": "Middle Opportunity Detection", "sports": ["NBA", "NFL", "NHL", "MLB"], "difficulty": "EASY"},
    {"id": 17, "name": "Sharp Money Tracking", "sports": ["NBA", "NFL", "NHL", "MLB"], "difficulty": "HARD"},
    {"id": 18, "name": "CLV Tracker (Closing Line Value)", "sports": ["NBA", "NFL", "NHL", "MLB"], "difficulty": "MEDIUM"},
    {"id": 19, "name": "Home/Away Splits Strategy", "sports": ["NBA", "NFL", "NHL", "MLB"], "difficulty": "MEDIUM"},
    {"id": 20, "name": "Divisional Rivalries Strategy", "sports": ["NBA", "NFL", "NHL"], "difficulty": "MEDIUM"},
    {"id": 21, "name": "Key Numbers Strategy (NFL)", "sports": ["NFL"], "difficulty": "EASY"},
    {"id": 22, "name": "Low-Hold Opportunities", "sports": ["NBA", "NFL", "NHL", "MLB"], "difficulty": "EASY"},
]


def generate_mock_backtest(strategy_id: int, strategy_name: str, sport: str, difficulty: str) -> dict:
    """
    Generate realistic mock backtest data for a strategy

    Args:
        strategy_id: Strategy ID
        strategy_name: Strategy name
        sport: Sport (NBA, NFL, NHL, MLB)
        difficulty: EASY, MEDIUM, or HARD

    Returns:
        Dictionary with backtest results
    """

    # Date range: 2023-24 season (Nov 2023 - Apr 2024)
    end_date = datetime(2024, 4, 15)
    start_date = datetime(2023, 11, 1)

    # Sample sizes based on difficulty and sport
    if difficulty == "EASY":
        bets_placed = random.randint(200, 400)
        win_rate = random.uniform(54.0, 58.0)  # Higher win rate for easier strategies
        roi = random.uniform(10.0, 20.0)
    elif difficulty == "MEDIUM":
        bets_placed = random.randint(150, 300)
        win_rate = random.uniform(52.0, 56.0)
        roi = random.uniform(6.0, 14.0)
    else:  # HARD
        bets_placed = random.randint(100, 200)
        win_rate = random.uniform(51.0, 54.0)  # Slightly lower but still profitable
        roi = random.uniform(5.0, 12.0)

    # Calculate wins/losses/pushes
    wins = int(bets_placed * (win_rate / 100))
    pushes = random.randint(int(bets_placed * 0.02), int(bets_placed * 0.06))  # 2-6% push rate
    losses = bets_placed - wins - pushes

    # Ensure realistic numbers
    if losses < 0:
        losses = 0
        pushes = bets_placed - wins

    # Recalculate actual win rate
    actual_win_rate = (wins / bets_placed * 100) if bets_placed > 0 else 0

    # Calculate profit/loss (assuming $100 per bet at -110 odds)
    profit_per_win = 100 * (100/110)  # ~90.91
    loss_per_loss = 100
    total_profit = (wins * profit_per_win) - (losses * loss_per_loss)

    # Recalculate ROI based on actual profit
    actual_roi = (total_profit / (bets_placed * 100)) * 100 if bets_placed > 0 else 0

    # Avg edge (typically 2-8% for profitable strategies)
    avg_edge = roi / 10  # Approximate relationship

    # Total opportunities (strategies detect more than they bet on)
    total_opportunities = int(bets_placed * random.uniform(1.3, 2.0))

    # Best situations (example descriptions)
    best_situations_templates = [
        "Best results in close games (within 5 points)",
        "Higher ROI when applied to home favorites",
        "Strongest edge in primetime games",
        "Best performance with elite teams",
        "Most profitable in divisional matchups",
        "Higher win rate with rested teams",
        "Best results in low-total games",
        "Strongest edge after blowouts"
    ]
    best_situations = random.choice(best_situations_templates)

    return {
        "strategy_id": strategy_id,
        "sport": sport,
        "date_range_start": start_date.strftime("%Y-%m-%d"),
        "date_range_end": end_date.strftime("%Y-%m-%d"),
        "total_opportunities": total_opportunities,
        "bets_placed": bets_placed,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "win_rate": round(actual_win_rate, 1),
        "roi": round(actual_roi, 1),
        "avg_edge": round(avg_edge, 2),
        "profit_loss": round(total_profit, 2),
        "confidence_interval": "95% CI: +/- 3.5%",
        "best_situations": best_situations,
        "data_source": "mock_simulation"
    }


def main():
    """Generate mock backtest data for all pending strategies"""
    db = BacktestDB()

    print("=" * 80)
    print("GENERATING MOCK BACKTEST DATA")
    print("=" * 80)

    total_generated = 0

    for strategy in PENDING_STRATEGIES:
        strategy_id = strategy["id"]
        strategy_name = strategy["name"]
        difficulty = strategy["difficulty"]
        sports = strategy["sports"]

        print(f"\n[{strategy_id:2d}] {strategy_name}")
        print(f"     Difficulty: {difficulty}, Sports: {', '.join(sports)}")

        # Generate backtest for primary sport
        primary_sport = sports[0]

        # Generate mock data
        backtest_data = generate_mock_backtest(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            sport=primary_sport,
            difficulty=difficulty
        )

        # Save to database
        try:
            backtest_id = db.save_backtest_result(backtest_data)
            print(f"     [OK] Generated: {backtest_data['bets_placed']} bets, "
                  f"{backtest_data['win_rate']}% win rate, "
                  f"{backtest_data['roi']:+.1f}% ROI")
            print(f"     Backtest ID: {backtest_id}")
            total_generated += 1
        except Exception as e:
            print(f"     [ERROR] {e}")

    print("\n" + "=" * 80)
    print(f"COMPLETE: Generated {total_generated} mock backtests")
    print(f"Database: {db.db_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
