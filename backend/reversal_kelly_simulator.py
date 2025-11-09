"""
Basketball Reversal Strategy - Kelly Criterion Bankroll Simulator
Simulates 1/4 Kelly growth with 1,044 bets from $20,000 starting bankroll
"""

import json
import logging
import numpy as np
from typing import Dict, List
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data" / "reversal_backtesting"


class KellySimulator:
    """Simulate bankroll growth using Kelly Criterion"""

    def __init__(
        self,
        starting_bankroll: float = 20000.0,
        win_rate: float = 0.556,
        odds: int = -110,
        kelly_fraction: float = 0.25,
        total_bets: int = 1044
    ):
        self.starting_bankroll = starting_bankroll
        self.win_rate = win_rate
        self.loss_rate = 1 - win_rate
        self.odds = odds
        self.kelly_fraction = kelly_fraction
        self.total_bets = total_bets

        # Calculate payouts from American odds
        if odds < 0:
            self.payout_per_dollar = 100 / abs(odds)  # -110 → $0.91 per $1
        else:
            self.payout_per_dollar = odds / 100

        # Full Kelly calculation
        self.full_kelly = self._calculate_full_kelly()

    def _calculate_full_kelly(self) -> float:
        """
        Calculate full Kelly percentage

        Formula: f = (bp - q) / b
        where:
        - b = net odds received (0.91 for -110)
        - p = probability of win
        - q = probability of loss
        """
        b = self.payout_per_dollar
        p = self.win_rate
        q = self.loss_rate

        kelly = (b * p - q) / b
        return kelly

    def calculate_bet_size(self, current_bankroll: float) -> float:
        """Calculate bet size using fractional Kelly"""
        bet_size = current_bankroll * self.full_kelly * self.kelly_fraction

        # Cap at 5% of bankroll for safety
        max_bet = current_bankroll * 0.05
        return min(bet_size, max_bet)

    def simulate_single_run(self, seed: int = None) -> Dict:
        """
        Simulate a single run of all bets

        Returns:
            Dict with bankroll history, final bankroll, ROI, drawdown, etc.
        """
        if seed is not None:
            np.random.seed(seed)

        bankroll = self.starting_bankroll
        bankroll_history = [bankroll]
        bet_history = []

        max_bankroll = bankroll
        max_drawdown = 0.0

        wins = 0
        losses = 0

        for bet_num in range(1, self.total_bets + 1):
            # Calculate bet size
            bet_size = self.calculate_bet_size(bankroll)

            # Determine outcome (win/loss based on win rate)
            is_win = np.random.random() < self.win_rate

            if is_win:
                profit = bet_size * self.payout_per_dollar
                bankroll += profit
                wins += 1
            else:
                bankroll -= bet_size
                losses += 1

            # Track max bankroll and drawdown
            if bankroll > max_bankroll:
                max_bankroll = bankroll

            current_drawdown = (max_bankroll - bankroll) / max_bankroll * 100
            if current_drawdown > max_drawdown:
                max_drawdown = current_drawdown

            bankroll_history.append(bankroll)
            bet_history.append({
                'bet_num': bet_num,
                'bet_size': round(bet_size, 2),
                'outcome': 'win' if is_win else 'loss',
                'bankroll': round(bankroll, 2)
            })

            # Stop if bankroll drops too low
            if bankroll < 100:
                logger.warning(f"Bankroll depleted at bet {bet_num}")
                break

        roi = (bankroll - self.starting_bankroll) / self.starting_bankroll * 100

        return {
            'final_bankroll': round(bankroll, 2),
            'starting_bankroll': self.starting_bankroll,
            'roi': round(roi, 2),
            'total_bets': bet_num,
            'wins': wins,
            'losses': losses,
            'win_rate_actual': round(wins / bet_num * 100, 2),
            'max_drawdown': round(max_drawdown, 2),
            'bankroll_history': bankroll_history,
            'bet_history': bet_history
        }

    def run_monte_carlo(self, num_simulations: int = 100) -> Dict:
        """
        Run Monte Carlo simulation

        Args:
            num_simulations: Number of simulations to run

        Returns:
            Dict with aggregated results
        """
        logger.info(f"Running {num_simulations} Monte Carlo simulations...")

        all_results = []

        for i in range(num_simulations):
            result = self.simulate_single_run(seed=i)
            all_results.append(result)

            if (i + 1) % 10 == 0:
                logger.info(f"  Completed {i + 1}/{num_simulations} simulations")

        # Aggregate results
        final_bankrolls = [r['final_bankroll'] for r in all_results]
        rois = [r['roi'] for r in all_results]
        drawdowns = [r['max_drawdown'] for r in all_results]

        # Calculate statistics
        avg_final = np.mean(final_bankrolls)
        median_final = np.median(final_bankrolls)
        best_final = np.max(final_bankrolls)
        worst_final = np.min(final_bankrolls)

        avg_roi = np.mean(rois)
        median_roi = np.median(rois)

        avg_drawdown = np.mean(drawdowns)
        max_drawdown = np.max(drawdowns)

        # Ruin risk (bankroll < starting)
        ruins = sum(1 for r in all_results if r['final_bankroll'] < self.starting_bankroll)
        ruin_risk = ruins / num_simulations * 100

        summary = {
            'simulations': num_simulations,
            'starting_bankroll': self.starting_bankroll,
            'total_bets': self.total_bets,
            'win_rate': self.win_rate * 100,
            'kelly_fraction': self.kelly_fraction,
            'avg_final_bankroll': round(avg_final, 2),
            'median_final_bankroll': round(median_final, 2),
            'best_case': round(best_final, 2),
            'worst_case': round(worst_final, 2),
            'avg_roi': round(avg_roi, 2),
            'median_roi': round(median_roi, 2),
            'avg_max_drawdown': round(avg_drawdown, 2),
            'max_drawdown_observed': round(max_drawdown, 2),
            'ruin_risk': round(ruin_risk, 2),
            'sample_run': all_results[0]  # Include first run as example
        }

        return summary

    def simulate_monthly_growth(self) -> List[Dict]:
        """
        Simulate month-by-month bankroll growth
        Assumes bets are distributed evenly across 12 months
        """
        bets_per_month = self.total_bets // 12
        remainder_bets = self.total_bets % 12

        monthly_results = []
        current_bankroll = self.starting_bankroll

        for month in range(1, 13):
            month_bets = bets_per_month + (1 if month <= remainder_bets else 0)

            # Simulate this month
            np.random.seed(month)  # For reproducibility

            month_start = current_bankroll
            wins = 0
            losses = 0

            for _ in range(month_bets):
                bet_size = self.calculate_bet_size(current_bankroll)
                is_win = np.random.random() < self.win_rate

                if is_win:
                    current_bankroll += bet_size * self.payout_per_dollar
                    wins += 1
                else:
                    current_bankroll -= bet_size
                    losses += 1

            month_roi = (current_bankroll - month_start) / month_start * 100

            monthly_results.append({
                'month': month,
                'bets': month_bets,
                'starting': round(month_start, 2),
                'ending': round(current_bankroll, 2),
                'avg_bet': round(self.calculate_bet_size(month_start), 2),
                'wins': wins,
                'losses': losses,
                'monthly_roi': round(month_roi, 2)
            })

        return monthly_results

    def save_results(self, monte_carlo_results: Dict, monthly_results: List[Dict], filename: str = "kelly_projection.json"):
        """Save simulation results to JSON"""
        filepath = DATA_DIR / filename

        output = {
            'monte_carlo': monte_carlo_results,
            'monthly_projection': monthly_results,
            'parameters': {
                'starting_bankroll': self.starting_bankroll,
                'win_rate': self.win_rate,
                'odds': self.odds,
                'kelly_fraction': self.kelly_fraction,
                'total_bets': self.total_bets,
                'full_kelly': round(self.full_kelly, 4),
                'fractional_kelly': round(self.full_kelly * self.kelly_fraction, 4)
            }
        }

        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(f"\nSimulation results saved to {filepath}")


def main():
    """Run Kelly simulations"""
    logger.info("="*60)
    logger.info("KELLY CRITERION BANKROLL SIMULATION")
    logger.info("="*60)

    simulator = KellySimulator(
        starting_bankroll=20000.0,
        win_rate=0.556,
        odds=-110,
        kelly_fraction=0.25,
        total_bets=1044
    )

    # Run Monte Carlo
    monte_carlo = simulator.run_monte_carlo(num_simulations=100)

    # Monthly projection
    monthly = simulator.simulate_monthly_growth()

    # Log results
    logger.info(f"\n{'='*60}")
    logger.info("MONTE CARLO RESULTS (100 simulations)")
    logger.info(f"{'='*60}")
    logger.info(f"Starting Bankroll: ${monte_carlo['starting_bankroll']:,.2f}")
    logger.info(f"Average Final: ${monte_carlo['avg_final_bankroll']:,.2f}")
    logger.info(f"Median Final: ${monte_carlo['median_final_bankroll']:,.2f}")
    logger.info(f"Best Case: ${monte_carlo['best_case']:,.2f}")
    logger.info(f"Worst Case: ${monte_carlo['worst_case']:,.2f}")
    logger.info(f"Average ROI: {monte_carlo['avg_roi']}%")
    logger.info(f"Median ROI: {monte_carlo['median_roi']}%")
    logger.info(f"Avg Max Drawdown: {monte_carlo['avg_max_drawdown']}%")
    logger.info(f"Ruin Risk: {monte_carlo['ruin_risk']}%")

    logger.info(f"\n{'='*60}")
    logger.info("MONTHLY PROJECTION")
    logger.info(f"{'='*60}")
    for month_data in monthly:
        logger.info(
            f"Month {month_data['month']:2d}: "
            f"${month_data['starting']:>10,.2f} → ${month_data['ending']:>10,.2f} "
            f"(+{month_data['monthly_roi']:>6.2f}%) "
            f"[{month_data['wins']}-{month_data['losses']}]"
        )

    # Save results
    simulator.save_results(monte_carlo, monthly)


if __name__ == "__main__":
    main()
