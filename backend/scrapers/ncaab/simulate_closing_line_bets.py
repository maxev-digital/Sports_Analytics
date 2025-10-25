#!/usr/bin/env python3
"""
NCAA Basketball Closing Line Bet Simulation
Simulates live betting strategy based on line movement thresholds
Uses historical data to validate regression hypothesis
"""

import pandas as pd
import numpy as np
import glob
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, 'backend')


class ClosingLineBetSimulator:
    """Simulates betting strategy based on closing line regression"""

    def __init__(self, historical_games_path, predictions_path=None):
        """
        Initialize simulator with historical data

        Args:
            historical_games_path: Path to CSV with actual game results
            predictions_path: Path to model predictions (used as proxy closing lines)
        """
        self.historical_games_path = historical_games_path
        self.predictions_path = predictions_path

        # Load data
        print(f" Loading historical games from: {os.path.basename(historical_games_path)}")
        self.games = pd.read_csv(historical_games_path)
        print(f"    Loaded {len(self.games):,} games")

        # Load predictions if available (use as proxy closing lines)
        self.predictions = None
        if predictions_path and os.path.exists(predictions_path):
            print(f" Loading predictions from: {os.path.basename(predictions_path)}")
            self.predictions = pd.read_csv(predictions_path)
            print(f"    Loaded {len(self.predictions):,} predictions")

        # Betting thresholds and recommendations
        self.thresholds = {
            8: {'name': 'Pass', 'bet_size': 0.0},
            12: {'name': 'Consider', 'bet_size': 0.5},
            16: {'name': 'Good', 'bet_size': 1.0},
            20: {'name': 'Strong', 'bet_size': 1.5},
            24: {'name': 'Max', 'bet_size': 2.0},
            28: {'name': 'Historic', 'bet_size': 2.0}
        }

        # Results
        self.bet_log = []
        self.performance_summary = None

    def merge_data(self):
        """Merge games with predictions to get closing lines"""
        print("\n Merging games with predictions...")

        if self.predictions is None:
            print("   WARNING:  No predictions available - using simulated closing lines")
            self._add_simulated_closing_lines()
            return True

        # Merge on team names
        merged = pd.merge(
            self.games,
            self.predictions,
            left_on=['Home_Team', 'Away_Team'],
            right_on=['Home_Team', 'Away_Team'],
            how='inner'
        )

        # Rename model prediction to closing line
        if 'Model_Total' in merged.columns:
            merged['Closing_Line'] = merged['Model_Total']

        # Handle duplicate columns from merge
        if 'Actual_Total_x' in merged.columns:
            merged['Actual_Total'] = merged['Actual_Total_x']

        # Keep only needed columns
        keep_cols = ['Home_Team', 'Away_Team', 'Actual_Total', 'Closing_Line']
        drop_cols = [c for c in merged.columns if c not in keep_cols]
        merged = merged[keep_cols]

        print(f"    Matched {len(merged):,} games ({len(merged)/len(self.games)*100:.1f}%)")

        self.merged_data = merged
        return True

    def _add_simulated_closing_lines(self):
        """Add simulated closing lines for testing"""
        np.random.seed(42)

        # Use model-like predictions as closing lines
        # Add realistic noise (NCAA totals have ~8-10 point standard error)
        noise = np.random.normal(0, 8.5, len(self.games))

        # Round to nearest 0.5
        self.games['Closing_Line'] = np.round(
            (self.games['Actual_Total'] + noise) * 2
        ) / 2

        self.merged_data = self.games.copy()
        print(f"    Added simulated closing lines for {len(self.merged_data):,} games")

    def simulate_live_betting(self):
        """
        Simulate live betting opportunities
        Hypothesis: When live total moves X points from closing, bet regression back
        """
        print("\n Simulating live betting opportunities...")

        # For each game, simulate potential line movements
        for idx, game in self.merged_data.iterrows():
            home_team = game['Home_Team']
            away_team = game['Away_Team']
            closing_line = game['Closing_Line']
            actual_total = game['Actual_Total']

            # Simulate various line movement scenarios
            # In reality, you'd track actual live line movements
            # For simulation: assume line can move anywhere between closing and actual

            self._simulate_game_scenarios(
                game_id=idx,
                home_team=home_team,
                away_team=away_team,
                closing_line=closing_line,
                actual_total=actual_total
            )

        self.bet_log = pd.DataFrame(self.bet_log)

        if len(self.bet_log) == 0:
            print("   WARNING:  No betting opportunities found")
            return False

        print(f"    Found {len(self.bet_log):,} betting opportunities")
        return True

    def _simulate_game_scenarios(self, game_id, home_team, away_team, closing_line, actual_total):
        """
        Simulate potential live line movements for a game
        Test different thresholds
        """
        # Calculate how far actual deviated from closing
        deviation = actual_total - closing_line
        abs_deviation = abs(deviation)

        # For each threshold, check if this game would have triggered a bet
        for threshold, config in self.thresholds.items():
            if config['bet_size'] == 0:
                continue  # Skip "Pass" tier

            # Would we have seen a betting opportunity?
            # Simulating: if actual ended up X+ points away, we might have seen
            # the line move that far during live betting

            if abs_deviation >= threshold:
                # Simulate a live bet at this threshold
                live_line = closing_line + (threshold if deviation > 0 else -threshold)

                # Determine bet side (always bet back toward closing)
                if deviation > 0:
                    # Actual went OVER closing, so live line is HIGH
                    # Bet UNDER to regress back
                    bet_side = 'UNDER'
                    bet_total = live_line
                    bet_wins = actual_total < live_line
                else:
                    # Actual went UNDER closing, so live line is LOW
                    # Bet OVER to regress back
                    bet_side = 'OVER'
                    bet_total = live_line
                    bet_wins = actual_total > live_line

                # Handle push
                if actual_total == live_line:
                    result = 'PUSH'
                    profit_loss = 0.0
                elif bet_wins:
                    result = 'WIN'
                    profit_loss = config['bet_size'] * 0.91  # -110 odds
                else:
                    result = 'LOSS'
                    profit_loss = -config['bet_size']

                # Log the bet
                self.bet_log.append({
                    'game_id': game_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'closing_line': round(closing_line, 1),
                    'live_line': round(live_line, 1),
                    'actual_total': actual_total,
                    'threshold': threshold,
                    'movement': round(abs(live_line - closing_line), 1),
                    'tier': config['name'],
                    'bet_side': bet_side,
                    'bet_total': round(bet_total, 1),
                    'bet_size': config['bet_size'],
                    'result': result,
                    'profit_loss': round(profit_loss, 2),
                    'closing_error': round(abs(actual_total - closing_line), 1),
                    'regressed': abs(actual_total - closing_line) < abs(live_line - closing_line)
                })

    def calculate_performance(self):
        """Calculate performance metrics for the betting strategy"""
        print("\n Calculating performance metrics...")

        if len(self.bet_log) == 0:
            print("   WARNING:  No bets to analyze")
            return {}

        # Overall metrics
        total_bets = len(self.bet_log)
        wins = (self.bet_log['result'] == 'WIN').sum()
        losses = (self.bet_log['result'] == 'LOSS').sum()
        pushes = (self.bet_log['result'] == 'PUSH').sum()

        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

        # Profit metrics
        total_profit = self.bet_log['profit_loss'].sum()
        total_risked = self.bet_log['bet_size'].sum()
        roi = (total_profit / total_risked * 100) if total_risked > 0 else 0

        # Regression metrics
        regressed = (self.bet_log['regressed'] == True).sum()
        regression_rate = (regressed / total_bets * 100) if total_bets > 0 else 0

        # Performance by tier
        tier_performance = []
        for tier in ['Consider', 'Good', 'Strong', 'Max', 'Historic']:
            tier_bets = self.bet_log[self.bet_log['tier'] == tier]
            if len(tier_bets) > 0:
                tier_wins = (tier_bets['result'] == 'WIN').sum()
                tier_losses = (tier_bets['result'] == 'LOSS').sum()
                tier_wr = (tier_wins / (tier_wins + tier_losses) * 100) if (tier_wins + tier_losses) > 0 else 0
                tier_profit = tier_bets['profit_loss'].sum()
                tier_risked = tier_bets['bet_size'].sum()
                tier_roi = (tier_profit / tier_risked * 100) if tier_risked > 0 else 0

                tier_performance.append({
                    'tier': tier,
                    'threshold': tier_bets['threshold'].iloc[0],
                    'opportunities': len(tier_bets),
                    'wins': int(tier_wins),
                    'losses': int(tier_losses),
                    'win_rate': round(tier_wr, 1),
                    'profit': round(tier_profit, 2),
                    'roi': round(tier_roi, 1)
                })

        self.performance_summary = {
            'total_bets': total_bets,
            'wins': int(wins),
            'losses': int(losses),
            'pushes': int(pushes),
            'win_rate': round(win_rate, 1),
            'total_profit': round(total_profit, 2),
            'total_risked': round(total_risked, 2),
            'roi': round(roi, 1),
            'regression_rate': round(regression_rate, 1),
            'tier_performance': pd.DataFrame(tier_performance)
        }

        return self.performance_summary

    def display_results(self):
        """Display simulation results"""
        if not self.performance_summary:
            print("WARNING:  No results to display")
            return

        print("\n" + "="*70)
        print("BETTING STRATEGY BACKTEST RESULTS")
        print("="*70)

        print(f"\n Overall Performance:")
        print(f"   Total Opportunities: {self.performance_summary['total_bets']:,}")
        print(f"   Wins: {self.performance_summary['wins']}")
        print(f"   Losses: {self.performance_summary['losses']}")
        print(f"   Pushes: {self.performance_summary['pushes']}")
        print(f"   Win Rate: {self.performance_summary['win_rate']}%")
        print(f"   Total Profit: {self.performance_summary['total_profit']:+.2f} units")
        print(f"   Total Risked: {self.performance_summary['total_risked']:.2f} units")
        print(f"   ROI: {self.performance_summary['roi']:+.1f}%")
        print(f"   Regression Rate: {self.performance_summary['regression_rate']}%")

        print(f"\n Performance by Threshold:")
        print("-"*70)

        if not self.performance_summary['tier_performance'].empty:
            for _, tier in self.performance_summary['tier_performance'].iterrows():
                print(f"\n{tier['tier']} (±{tier['threshold']} points):")
                print(f"   Opportunities: {tier['opportunities']}")
                print(f"   Record: {tier['wins']}-{tier['losses']} ({tier['win_rate']}%)")
                print(f"   Profit: {tier['profit']:+.2f} units (ROI: {tier['roi']:+.1f}%)")

        # Breakeven analysis
        print(f"\n Key Insights:")
        breakeven_wr = 52.38  # Breakeven at -110 odds
        print(f"   Breakeven Win Rate: {breakeven_wr}%")

        if self.performance_summary['win_rate'] > breakeven_wr:
            print(f"    Strategy is PROFITABLE ({self.performance_summary['win_rate'] - breakeven_wr:+.1f}% above breakeven)")
        else:
            print(f"   ERROR: Strategy is UNPROFITABLE ({self.performance_summary['win_rate'] - breakeven_wr:.1f}% below breakeven)")

        # Best performing tier
        if not self.performance_summary['tier_performance'].empty:
            best_tier = self.performance_summary['tier_performance'].nlargest(1, 'roi').iloc[0]
            print(f"    Best Tier: {best_tier['tier']} (±{best_tier['threshold']} pts) with {best_tier['roi']:+.1f}% ROI")

        print("\n" + "="*70)

    def save_results(self, output_dir='backend/data/analysis'):
        """Save simulation results"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save bet log
        bet_log_file = f"{output_dir}/bet_simulation_log_{timestamp}.csv"
        self.bet_log.to_csv(bet_log_file, index=False)
        print(f"\n Saved bet log: {bet_log_file}")

        # Save performance summary
        summary_file = f"{output_dir}/bet_simulation_summary_{timestamp}.csv"
        summary_data = {
            'timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            'total_bets': [self.performance_summary['total_bets']],
            'wins': [self.performance_summary['wins']],
            'losses': [self.performance_summary['losses']],
            'pushes': [self.performance_summary['pushes']],
            'win_rate': [self.performance_summary['win_rate']],
            'total_profit': [self.performance_summary['total_profit']],
            'roi': [self.performance_summary['roi']],
            'regression_rate': [self.performance_summary['regression_rate']]
        }
        pd.DataFrame(summary_data).to_csv(summary_file, index=False)
        print(f" Saved summary: {summary_file}")

        # Save tier performance
        tier_file = f"{output_dir}/bet_simulation_tiers_{timestamp}.csv"
        self.performance_summary['tier_performance'].to_csv(tier_file, index=False)
        print(f" Saved tier analysis: {tier_file}")


def main():
    """Run bet simulation"""
    print("="*70)
    print("NCAA BASKETBALL CLOSING LINE BET SIMULATION")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    # Find most recent historical data
    historical_dir = "backend/data/historical"
    games_pattern = f"{historical_dir}/game_results_*_season_*.csv"
    games_files = glob.glob(games_pattern)

    if not games_files:
        print("ERROR: No historical game data found")
        print(f"   Run: python game_results_scraper.py")
        return False

    latest_games = max(games_files)

    # Find most recent backtest predictions (optional)
    backtest_dir = "backend/data/backtesting"
    pred_pattern = f"{backtest_dir}/predictions_*.csv"
    pred_files = glob.glob(pred_pattern)
    latest_predictions = max(pred_files) if pred_files else None

    # Initialize simulator
    simulator = ClosingLineBetSimulator(
        historical_games_path=latest_games,
        predictions_path=latest_predictions
    )

    # Step 1: Merge data
    if not simulator.merge_data():
        print("ERROR: Failed to merge data")
        return False

    # Step 2: Simulate betting
    if not simulator.simulate_live_betting():
        print("ERROR: Failed to simulate bets")
        return False

    # Step 3: Calculate performance
    simulator.calculate_performance()

    # Step 4: Display results
    simulator.display_results()

    # Step 5: Save results
    simulator.save_results()

    print("\n" + "="*70)
    print(" SIMULATION COMPLETE")
    print("="*70)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
