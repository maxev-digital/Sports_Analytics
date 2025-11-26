"""
Volatility Arbitrage Calculator

Handles stake sizing, profit calculations, and EV analysis
"""

from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class VolatilityArbCalculator:
    """Calculator for volatility arbitrage positions"""

    @staticmethod
    def american_to_decimal(odds: int) -> float:
        """Convert American odds to decimal"""
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1

    @staticmethod
    def american_to_implied_prob(odds: int) -> float:
        """Convert American odds to implied probability"""
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)

    @staticmethod
    def calculate_potential_win(odds: int, stake: float) -> float:
        """Calculate potential winnings (profit only, not including stake)"""
        if odds > 0:
            return stake * (odds / 100)
        else:
            return stake * (100 / abs(odds))

    @staticmethod
    def calculate_edge(
        true_win_prob: float,
        implied_prob: float
    ) -> Tuple[float, float]:
        """
        Calculate edge and EV%

        Returns:
            (edge, ev_percent)
        """
        edge = true_win_prob - implied_prob
        ev_percent = edge * 100
        return edge, ev_percent

    @staticmethod
    def calculate_hedge_stake(
        first_odds: int,
        first_stake: float,
        second_odds: int,
        target_locked_profit: Optional[float] = None
    ) -> Dict:
        """
        Calculate optimal hedge stake for second leg

        Args:
            first_odds: Odds of first position (e.g., +200)
            first_stake: Stake on first position (e.g., 200)
            second_odds: Odds available for hedge (e.g., +300)
            target_locked_profit: Optional target for locked profit
                                 If None, calculates for max even profit

        Returns:
            {
                'second_stake': float,
                'profit_if_first_wins': float,
                'profit_if_second_wins': float,
                'locked_profit': float,
                'payoff_skew': float  # How skewed the payoff is
            }
        """
        # Calculate first leg potential win
        first_win = VolatilityArbCalculator.calculate_potential_win(first_odds, first_stake)

        if target_locked_profit is not None:
            # Calculate stake needed to lock specific profit
            # If first wins: first_win - second_stake = target_profit
            # If second wins: second_win - first_stake = target_profit
            #
            # From second equation:
            # second_stake * (second_odds/100) - first_stake = target_profit
            # second_stake = (target_profit + first_stake) / (second_odds/100)

            if second_odds > 0:
                second_stake = (target_locked_profit + first_stake) / (second_odds / 100)
            else:
                second_stake = (target_locked_profit + first_stake) / (100 / abs(second_odds))
        else:
            # Calculate for maximum even profit (both sides equal)
            # Set: first_win - second_stake = second_win - first_stake
            # Where second_win = second_stake * (second_odds/100) for +odds
            #
            # first_win - second_stake = second_stake * (second_odds/100) - first_stake
            # first_win + first_stake = second_stake * (1 + second_odds/100)
            # second_stake = (first_win + first_stake) / (1 + second_odds/100)

            decimal_odds = VolatilityArbCalculator.american_to_decimal(second_odds)
            second_stake = (first_win + first_stake) / decimal_odds

        # Calculate profits both ways
        second_win = VolatilityArbCalculator.calculate_potential_win(second_odds, second_stake)

        profit_if_first_wins = first_win - second_stake
        profit_if_second_wins = second_win - first_stake

        # Locked profit is the minimum of both
        locked_profit = min(profit_if_first_wins, profit_if_second_wins)

        # Payoff skew (0 = perfectly even, higher = more skewed)
        payoff_skew = abs(profit_if_first_wins - profit_if_second_wins) / max(abs(profit_if_first_wins), abs(profit_if_second_wins))

        return {
            'second_stake': round(second_stake, 2),
            'profit_if_first_wins': round(profit_if_first_wins, 2),
            'profit_if_second_wins': round(profit_if_second_wins, 2),
            'locked_profit': round(locked_profit, 2),
            'payoff_skew': round(payoff_skew, 3)
        }

    @staticmethod
    def calculate_ev_comparison(
        first_odds: int,
        first_stake: float,
        first_true_prob: float,
        second_odds: int,
        hedge_calc: Dict
    ) -> Dict:
        """
        Compare EV of hedging vs holding original position

        Args:
            first_odds: Odds of first position
            first_stake: Stake on first position
            first_true_prob: ML model estimated win probability for first side
            second_odds: Odds for hedge
            hedge_calc: Result from calculate_hedge_stake()

        Returns:
            {
                'ev_if_hedge': float,  # Guaranteed locked profit
                'ev_if_hold': float,   # EV of riding first bet
                'recommendation': str  # 'HEDGE' or 'HOLD'
            }
        """
        # EV of hedging = locked profit (guaranteed)
        ev_if_hedge = hedge_calc['locked_profit']

        # EV of holding = probability weighted outcome
        # EV = (win_prob × first_win) - (lose_prob × first_stake)
        first_win = VolatilityArbCalculator.calculate_potential_win(first_odds, first_stake)
        ev_if_hold = (first_true_prob * first_win) - ((1 - first_true_prob) * first_stake)

        recommendation = 'HEDGE' if ev_if_hedge > ev_if_hold else 'HOLD'

        return {
            'ev_if_hedge': round(ev_if_hedge, 2),
            'ev_if_hold': round(ev_if_hold, 2),
            'ev_difference': round(ev_if_hedge - ev_if_hold, 2),
            'recommendation': recommendation
        }

    @staticmethod
    def validate_bankroll(
        stake: float,
        bankroll: float,
        risk_profile: str = 'standard'
    ) -> Dict:
        """
        Validate if stake is appropriate for bankroll

        Args:
            stake: Proposed stake size
            bankroll: Total bankroll
            risk_profile: 'aggressive' (50u), 'standard' (100u), 'conservative' (150u)

        Returns:
            {
                'valid': bool,
                'required_bankroll': float,
                'units': int,
                'warning': str | None
            }
        """
        unit_requirements = {
            'aggressive': 50,
            'standard': 100,
            'conservative': 150
        }

        required_units = unit_requirements.get(risk_profile, 100)
        required_bankroll = stake * required_units

        valid = bankroll >= required_bankroll
        current_units = int(bankroll / stake) if stake > 0 else 0

        warning = None
        if not valid:
            warning = f"Insufficient bankroll for {risk_profile} sizing. Need ${required_bankroll:,.0f}, have ${bankroll:,.0f}"
        elif current_units < 75:
            warning = f"Bankroll is on the low side ({current_units} units). Consider reducing stake or increasing bankroll."

        return {
            'valid': valid,
            'required_bankroll': required_bankroll,
            'current_units': current_units,
            'required_units': required_units,
            'warning': warning
        }

    @staticmethod
    def calculate_position_result(
        first_odds: int,
        first_stake: float,
        second_odds: Optional[int],
        second_stake: Optional[float],
        winning_side: str  # 'first' or 'second'
    ) -> Dict:
        """
        Calculate final profit/loss for a closed position

        Args:
            first_odds: Odds of first position
            first_stake: Stake on first position
            second_odds: Odds of second position (None if not hedged)
            second_stake: Stake on second position (None if not hedged)
            winning_side: Which side won ('first' or 'second')

        Returns:
            {
                'was_hedged': bool,
                'actual_profit': float,
                'roi_percent': float
            }
        """
        was_hedged = second_odds is not None and second_stake is not None

        if not was_hedged:
            # Simple: first bet either won or lost
            if winning_side == 'first':
                win = VolatilityArbCalculator.calculate_potential_win(first_odds, first_stake)
                actual_profit = win
                total_wagered = first_stake
            else:
                actual_profit = -first_stake
                total_wagered = first_stake
        else:
            # Hedged position
            if winning_side == 'first':
                first_win = VolatilityArbCalculator.calculate_potential_win(first_odds, first_stake)
                actual_profit = first_win - second_stake
            else:
                second_win = VolatilityArbCalculator.calculate_potential_win(second_odds, second_stake)
                actual_profit = second_win - first_stake

            total_wagered = first_stake + second_stake

        roi_percent = (actual_profit / total_wagered * 100) if total_wagered > 0 else 0

        return {
            'was_hedged': was_hedged,
            'actual_profit': round(actual_profit, 2),
            'total_wagered': round(total_wagered, 2),
            'roi_percent': round(roi_percent, 2)
        }

    @staticmethod
    def suggest_trigger_price(
        entry_odds: int,
        offset: int = 80
    ) -> int:
        """
        Suggest target trigger price for opposite side

        Args:
            entry_odds: Odds you entered at (e.g., +200)
            offset: How much better to target (default 80, so +200 → +280)

        Returns:
            Suggested trigger price
        """
        return entry_odds + offset

    @staticmethod
    def calculate_min_locked_profit(
        stake: float,
        min_profit_pct: float = 0.10
    ) -> float:
        """
        Calculate minimum locked profit to justify hedge

        Args:
            stake: Position stake size
            min_profit_pct: Minimum profit as % of stake (default 10%)

        Returns:
            Minimum locked profit in dollars
        """
        return stake * min_profit_pct
