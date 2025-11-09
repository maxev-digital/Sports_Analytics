"""
Basketball Reversal Strategy - Backtest Engine
Analyzes Q1-Q2 → Q3 reversal pattern across all leagues
"""

import pandas as pd
import json
import logging
from typing import Dict, List, Tuple
from pathlib import Path
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data" / "reversal_backtesting"


class ReversalBacktester:
    """Backtest Q1-Q2 → Q3 reversal strategy"""

    def __init__(self):
        self.results = {}

    def load_data(self, filename: str) -> pd.DataFrame:
        """Load game data from CSV"""
        filepath = DATA_DIR / filename
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return pd.DataFrame()

        df = pd.DataFrame(pd.read_csv(filepath))
        logger.info(f"Loaded {len(df)} games from {filename}")
        return df

    def identify_reversal_triggers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify games where team won Q1 and Q2 (reversal trigger)

        Returns DataFrame with additional columns:
        - trigger_team: 'home' or 'away' (who won Q1 & Q2)
        - q3_winner: 'home' or 'away' (who won Q3)
        - reversal_occurred: True if opponent won Q3
        """
        triggers = []

        for idx, row in df.iterrows():
            # Skip if missing quarter data
            if pd.isna(row.get('Q1_home')) or pd.isna(row.get('Q3_home')):
                continue

            # Check home team won Q1 and Q2
            home_q1_win = row['Q1_home'] > row['Q1_away']
            home_q2_win = row['Q2_home'] > row['Q2_away']

            # Check away team won Q1 and Q2
            away_q1_win = row['Q1_away'] > row['Q1_home']
            away_q2_win = row['Q2_away'] > row['Q2_home']

            trigger_team = None
            if home_q1_win and home_q2_win:
                trigger_team = 'home'
            elif away_q1_win and away_q2_win:
                trigger_team = 'away'

            if trigger_team:
                # Who won Q3?
                q3_winner = 'home' if row['Q3_home'] > row['Q3_away'] else 'away'

                # Did reversal occur? (opponent won Q3)
                reversal_occurred = (trigger_team == 'home' and q3_winner == 'away') or \
                                   (trigger_team == 'away' and q3_winner == 'home')

                # Calculate Q3 margin
                q3_margin = abs(row['Q3_home'] - row['Q3_away'])

                trigger_row = row.copy()
                trigger_row['trigger_team'] = trigger_team
                trigger_row['q3_winner'] = q3_winner
                trigger_row['reversal_occurred'] = reversal_occurred
                trigger_row['q3_margin'] = q3_margin

                triggers.append(trigger_row)

        trigger_df = pd.DataFrame(triggers)
        logger.info(f"Found {len(trigger_df)} Q1-Q2 reversal triggers")

        return trigger_df

    def calculate_betting_performance(self, trigger_df: pd.DataFrame, spread: float = 4.5, odds: int = -110) -> Dict:
        """
        Calculate betting performance

        Strategy: Bet opponent +4.5 spread @ -110 when team wins Q1 & Q2

        Args:
            trigger_df: DataFrame with reversal triggers
            spread: Point spread (default 4.5)
            odds: American odds (default -110)

        Returns:
            Dict with win rate, ROI, EV, avg margin, etc.
        """
        if len(trigger_df) == 0:
            return {
                'total_triggers': 0,
                'bets_placed': 0,
                'wins': 0,
                'losses': 0,
                'pushes': 0,
                'win_rate': 0.0,
                'roi': 0.0,
                'ev': 0.0,
                'avg_margin': 0.0
            }

        total_triggers = len(trigger_df)

        # Simulate betting opponent spread
        wins = 0
        losses = 0
        pushes = 0

        for idx, row in trigger_df.iterrows():
            # We bet on the opponent to cover +spread
            # If trigger team is home, we bet away +4.5
            # If trigger team is away, we bet home +4.5

            if row['trigger_team'] == 'home':
                # Bet away +4.5
                # Away covers if: away_q3 + 4.5 > home_q3
                away_adjusted = row['Q3_away'] + spread
                if away_adjusted > row['Q3_home']:
                    wins += 1
                elif away_adjusted == row['Q3_home']:
                    pushes += 1
                else:
                    losses += 1
            else:
                # Bet home +4.5
                home_adjusted = row['Q3_home'] + spread
                if home_adjusted > row['Q3_away']:
                    wins += 1
                elif home_adjusted == row['Q3_away']:
                    pushes += 1
                else:
                    losses += 1

        bets_placed = wins + losses + pushes

        # Calculate metrics
        win_rate = (wins / bets_placed * 100) if bets_placed > 0 else 0.0

        # ROI calculation (assuming -110 odds)
        # Win = +$0.91 per $1 bet
        # Loss = -$1.00 per $1 bet
        profit_per_win = 0.91
        loss_per_loss = 1.0

        total_profit = (wins * profit_per_win) - (losses * loss_per_loss)
        roi = (total_profit / bets_placed * 100) if bets_placed > 0 else 0.0

        # EV calculation
        # EV = (win_prob * win_amount) - (loss_prob * loss_amount)
        win_prob = wins / bets_placed if bets_placed > 0 else 0
        loss_prob = losses / bets_placed if bets_placed > 0 else 0
        ev = (win_prob * profit_per_win) - (loss_prob * loss_per_loss)
        ev_pct = ev * 100

        # Average margin
        avg_margin = trigger_df['q3_margin'].mean()

        return {
            'total_triggers': total_triggers,
            'bets_placed': bets_placed,
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'win_rate': round(win_rate, 2),
            'roi': round(roi, 2),
            'ev': round(ev_pct, 2),
            'avg_margin': round(avg_margin, 2),
            'total_profit_units': round(total_profit, 2)
        }

    def run_backtest(self, league: str, filename: str) -> Dict:
        """Run complete backtest for a league"""
        logger.info(f"\n{'='*60}")
        logger.info(f"BACKTESTING {league.upper()}")
        logger.info(f"{'='*60}")

        # Load data
        df = self.load_data(filename)
        if df.empty:
            logger.error(f"No data available for {league}")
            return {}

        # Find triggers
        trigger_df = self.identify_reversal_triggers(df)

        # Calculate performance
        results = self.calculate_betting_performance(trigger_df)
        results['league'] = league

        # Log results
        logger.info(f"\n{league} RESULTS:")
        logger.info(f"  Total Games: {len(df)}")
        logger.info(f"  Triggers (Q1-Q2 wins): {results['total_triggers']}")
        logger.info(f"  Bets Placed: {results['bets_placed']}")
        logger.info(f"  Wins: {results['wins']}")
        logger.info(f"  Losses: {results['losses']}")
        logger.info(f"  Pushes: {results['pushes']}")
        logger.info(f"  Win Rate: {results['win_rate']}%")
        logger.info(f"  ROI: {results['roi']}%")
        logger.info(f"  EV: +{results['ev']}%")
        logger.info(f"  Avg Q3 Margin: {results['avg_margin']} pts")
        logger.info(f"  Total Profit: +{results['total_profit_units']} units")

        self.results[league] = results
        return results

    def save_results(self, filename: str = "backtest_results.json"):
        """Save backtest results to JSON"""
        filepath = DATA_DIR / filename

        # Add summary
        all_results = {
            'leagues': self.results,
            'summary': self._calculate_summary()
        }

        with open(filepath, 'w') as f:
            json.dump(all_results, f, indent=2)

        logger.info(f"\nResults saved to {filepath}")

    def _calculate_summary(self) -> Dict:
        """Calculate overall summary across all leagues"""
        if not self.results:
            return {}

        total_triggers = sum(r['total_triggers'] for r in self.results.values())
        total_bets = sum(r['bets_placed'] for r in self.results.values())
        total_wins = sum(r['wins'] for r in self.results.values())
        total_losses = sum(r['losses'] for r in self.results.values())
        total_pushes = sum(r['pushes'] for r in self.results.values())
        total_profit = sum(r['total_profit_units'] for r in self.results.values())

        win_rate = (total_wins / total_bets * 100) if total_bets > 0 else 0
        roi = (total_profit / total_bets * 100) if total_bets > 0 else 0

        # Weighted average EV
        weighted_ev = sum(r['ev'] * r['bets_placed'] for r in self.results.values()) / total_bets if total_bets > 0 else 0

        return {
            'total_games_analyzed': sum(1 for r in self.results.values()),  # placeholder
            'total_triggers': total_triggers,
            'total_bets': total_bets,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'total_pushes': total_pushes,
            'overall_win_rate': round(win_rate, 2),
            'overall_roi': round(roi, 2),
            'overall_ev': round(weighted_ev, 2),
            'total_profit_units': round(total_profit, 2)
        }


def main():
    """Run backtests on all leagues"""
    backtester = ReversalBacktester()

    # Run backtests
    backtester.run_backtest('NBA', 'nba_2023_24.csv')
    backtester.run_backtest('NCAA', 'ncaa_2023_24.csv')
    # backtester.run_backtest('WNBA', 'wnba_2023_24.csv')
    # backtester.run_backtest('Euroleague', 'euroleague_2023_24.csv')

    # Save results
    backtester.save_results()

    # Print summary
    summary = backtester._calculate_summary()
    logger.info(f"\n{'='*60}")
    logger.info("OVERALL SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total Triggers: {summary['total_triggers']}")
    logger.info(f"Total Bets: {summary['total_bets']}")
    logger.info(f"Overall Win Rate: {summary['overall_win_rate']}%")
    logger.info(f"Overall ROI: {summary['overall_roi']}%")
    logger.info(f"Overall EV: +{summary['overall_ev']}%")
    logger.info(f"Total Profit: +{summary['total_profit_units']} units")


if __name__ == "__main__":
    main()
