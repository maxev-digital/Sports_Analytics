"""
Volatility Arbitrage Position Tracker

Tracks open positions and monitors for hedge trigger opportunities
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import uuid

from .models import VolatilityPosition, HedgeAlert
from .calculator import VolatilityArbCalculator
from .config import (
    POSITION_EXPIRY_HOURS,
    TOAST_ALERT_ENABLED,
    TOAST_ALERT_PRIORITY,
    HEDGE_TRIGGER_RATE,
    SINGLE_LEG_EV
)

logger = logging.getLogger(__name__)


class VolatilityPositionTracker:
    """Tracks and monitors volatility arbitrage positions"""

    def __init__(self):
        self.calculator = VolatilityArbCalculator()
        self.open_positions: Dict[str, VolatilityPosition] = {}
        self.recent_alerts: Dict[str, datetime] = {}  # Prevent spam

    def create_position(
        self,
        user_id: str,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        entry_team: str,
        entry_side: str,
        entry_odds: int,
        entry_stake: float,
        entry_bookmaker: str,
        trigger_price: int,
        trigger_min_profit: float,
        entry_quarter: str = '',
        entry_score: str = ''
    ) -> VolatilityPosition:
        """
        Create and track new volatility arbitrage position

        Returns:
            VolatilityPosition object
        """
        position_id = f"vol_{uuid.uuid4().hex[:12]}"
        now = datetime.now()

        position = VolatilityPosition(
            id=position_id,
            user_id=user_id,
            game_id=game_id,
            sport=sport,
            home_team=home_team,
            away_team=away_team,
            first_team=entry_team,
            first_side=entry_side,
            first_odds=entry_odds,
            first_stake=entry_stake,
            first_timestamp=now,
            first_bookmaker=entry_bookmaker,
            trigger_price=trigger_price,
            trigger_min_profit=trigger_min_profit,
            status='open',
            entry_quarter=entry_quarter,
            entry_score=entry_score,
            created_at=now,
            updated_at=now
        )

        self.open_positions[position_id] = position

        logger.info(
            f"Created volatility position {position_id}: "
            f"{entry_team} {entry_odds:+d} (${entry_stake}), "
            f"trigger at {trigger_price:+d}"
        )

        return position

    def check_hedge_triggers(
        self,
        live_games: List[Dict],
        ml_predictions: Optional[Dict] = None
    ) -> List[HedgeAlert]:
        """
        Check all open positions for hedge trigger opportunities

        Args:
            live_games: List of live game data with current odds
            ml_predictions: Optional ML predictions for EV comparison

        Returns:
            List of HedgeAlert objects when triggers hit
        """
        alerts = []

        for position_id, position in list(self.open_positions.items()):
            # Skip if already hedged or closed
            if position.status != 'open':
                continue

            # Find the game for this position
            game = next((g for g in live_games if g.get('id') == position.game_id), None)

            if not game:
                # Game not found, might have ended
                self._check_position_expiry(position)
                continue

            # Check if game has ended
            if game.get('completed', False):
                self._close_position_on_game_end(position, game)
                continue

            # Check for hedge opportunity
            hedge_alert = self._check_for_hedge_trigger(position, game, ml_predictions)

            if hedge_alert:
                # Prevent duplicate alerts (wait 60 seconds between alerts for same position)
                last_alert_time = self.recent_alerts.get(position_id)
                if last_alert_time and (datetime.now() - last_alert_time).total_seconds() < 60:
                    continue

                alerts.append(hedge_alert)
                self.recent_alerts[position_id] = datetime.now()

                logger.info(
                    f"HEDGE TRIGGER: Position {position_id} - "
                    f"{hedge_alert.hedge_team} at {hedge_alert.hedge_odds:+d} "
                    f"(locked profit: ${hedge_alert.locked_profit:.2f})"
                )

        return alerts

    def _check_for_hedge_trigger(
        self,
        position: VolatilityPosition,
        game: Dict,
        ml_predictions: Optional[Dict]
    ) -> Optional[HedgeAlert]:
        """
        Check if opposite side has hit trigger price

        Returns:
            HedgeAlert if trigger hit, None otherwise
        """
        bookmakers = game.get('bookmakers', [])

        # Determine opposite team
        opposite_team = position.away_team if position.first_side == 'home' else position.home_team
        opposite_side = 'away' if position.first_side == 'home' else 'home'

        best_odds = None
        best_bookmaker = None
        best_bookmaker_title = None

        # Find best available odds for opposite side
        for book in bookmakers:
            book_key = book.get('key')
            book_title = book.get('title', book_key)
            markets = book.get('markets', [])

            for market in markets:
                if market.get('key') != 'h2h':
                    continue

                outcomes = market.get('outcomes', [])

                for outcome in outcomes:
                    team = outcome.get('name')
                    odds = outcome.get('price')

                    if team == opposite_team and odds:
                        # Take best (highest) odds
                        if best_odds is None or odds > best_odds:
                            best_odds = odds
                            best_bookmaker = book_key
                            best_bookmaker_title = book_title

        # Check if trigger hit
        if best_odds is None or best_odds < position.trigger_price:
            return None

        # Calculate hedge stake and profits
        hedge_calc = self.calculator.calculate_hedge_stake(
            position.first_odds,
            position.first_stake,
            best_odds
        )

        # Check if locked profit meets minimum
        if hedge_calc['locked_profit'] < position.trigger_min_profit:
            return None

        # Calculate EV comparison (if we have ML predictions)
        ev_if_hedge = hedge_calc['locked_profit']  # Guaranteed
        ev_if_hold = position.first_stake * SINGLE_LEG_EV  # 8% default

        if ml_predictions:
            # Get ML prediction for first side
            first_true_prob = ml_predictions.get(f'{position.first_side}_win_probability')
            if first_true_prob:
                ev_comparison = self.calculator.calculate_ev_comparison(
                    position.first_odds,
                    position.first_stake,
                    first_true_prob,
                    best_odds,
                    hedge_calc
                )
                ev_if_hold = ev_comparison['ev_if_hold']

        # Get game state
        quarter = game.get('quarter', '')
        score_home = game.get('score_home', 0)
        score_away = game.get('score_away', 0)
        current_score = f"{score_away}-{score_home}"
        time_remaining = game.get('time_remaining', '')

        # Calculate time until game ends (rough estimate)
        expires_in = 3600  # Default 1 hour

        # Create hedge alert
        alert = HedgeAlert(
            position_id=position.id,
            game_id=position.game_id,
            user_id=position.user_id,
            home_team=position.home_team,
            away_team=position.away_team,
            first_team=position.first_team,
            first_odds=position.first_odds,
            first_stake=position.first_stake,
            hedge_team=opposite_team,
            hedge_odds=best_odds,
            hedge_bookmaker=best_bookmaker,
            hedge_bookmaker_title=best_bookmaker_title,
            recommended_stake=hedge_calc['second_stake'],
            profit_if_first_wins=hedge_calc['profit_if_first_wins'],
            profit_if_hedge_wins=hedge_calc['profit_if_second_wins'],
            locked_profit=hedge_calc['locked_profit'],
            ev_if_hedge=ev_if_hedge,
            ev_if_hold=ev_if_hold,
            current_quarter=quarter,
            current_score=current_score,
            time_remaining=time_remaining,
            timestamp=datetime.now(),
            expires_in=expires_in,
            priority=TOAST_ALERT_PRIORITY
        )

        return alert

    def execute_hedge(
        self,
        position_id: str,
        hedge_stake: float,
        hedge_odds: int,
        hedge_bookmaker: str
    ) -> Optional[VolatilityPosition]:
        """
        Execute hedge on an open position

        Returns:
            Updated VolatilityPosition or None if not found
        """
        position = self.open_positions.get(position_id)

        if not position or position.status != 'open':
            logger.warning(f"Cannot execute hedge on position {position_id}: not found or not open")
            return None

        # Determine opposite team
        opposite_team = position.away_team if position.first_side == 'home' else position.home_team

        # Calculate locked profit
        hedge_calc = self.calculator.calculate_hedge_stake(
            position.first_odds,
            position.first_stake,
            hedge_odds
        )

        # Update position
        position.second_team = opposite_team
        position.second_odds = hedge_odds
        position.second_stake = hedge_stake
        position.second_timestamp = datetime.now()
        position.second_bookmaker = hedge_bookmaker
        position.status = 'hedged'
        position.locked_profit = hedge_calc['locked_profit']
        position.updated_at = datetime.now()

        logger.info(
            f"Executed hedge on position {position_id}: "
            f"{opposite_team} {hedge_odds:+d} (${hedge_stake}), "
            f"locked profit: ${hedge_calc['locked_profit']:.2f}"
        )

        return position

    def close_position(
        self,
        position_id: str,
        winning_team: str
    ) -> Optional[VolatilityPosition]:
        """
        Close position and calculate final profit

        Args:
            position_id: Position ID
            winning_team: Team that won the game

        Returns:
            Updated VolatilityPosition or None if not found
        """
        position = self.open_positions.get(position_id)

        if not position:
            logger.warning(f"Cannot close position {position_id}: not found")
            return None

        # Determine which side won
        winning_side = 'first' if winning_team == position.first_team else 'second'

        # Calculate result
        result = self.calculator.calculate_position_result(
            position.first_odds,
            position.first_stake,
            position.second_odds,
            position.second_stake,
            winning_side
        )

        # Update position
        position.actual_profit = result['actual_profit']
        position.status = 'closed_won' if result['actual_profit'] > 0 else 'closed_lost'
        position.closed_at = datetime.now()
        position.updated_at = datetime.now()

        # Remove from open positions
        del self.open_positions[position_id]

        logger.info(
            f"Closed position {position_id}: "
            f"Winner={winning_team}, Profit=${result['actual_profit']:.2f}, "
            f"ROI={result['roi_percent']:.1f}%"
        )

        return position

    def _check_position_expiry(self, position: VolatilityPosition):
        """Check if position should be expired (game ended but we missed it)"""
        age = datetime.now() - position.created_at

        if age > timedelta(hours=POSITION_EXPIRY_HOURS):
            logger.warning(
                f"Position {position.id} expired after {POSITION_EXPIRY_HOURS} hours"
            )
            position.status = 'expired'
            position.closed_at = datetime.now()
            position.updated_at = datetime.now()
            del self.open_positions[position.id]

    def _close_position_on_game_end(self, position: VolatilityPosition, game: Dict):
        """Close position when game ends"""
        # Determine winner from game
        score_home = game.get('score_home', 0)
        score_away = game.get('score_away', 0)

        if score_home > score_away:
            winning_team = position.home_team
        else:
            winning_team = position.away_team

        self.close_position(position.id, winning_team)

    def get_open_positions(self, user_id: Optional[str] = None) -> List[VolatilityPosition]:
        """
        Get all open positions, optionally filtered by user

        Returns:
            List of VolatilityPosition objects
        """
        positions = list(self.open_positions.values())

        if user_id:
            positions = [p for p in positions if p.user_id == user_id]

        return positions

    def get_position(self, position_id: str) -> Optional[VolatilityPosition]:
        """Get specific position by ID"""
        return self.open_positions.get(position_id)
