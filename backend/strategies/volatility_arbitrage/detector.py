"""
Volatility Arbitrage Detector

Identifies +EV entry opportunities for volatility arbitrage positions
"""

from typing import List, Dict, Optional
from datetime import datetime
import logging

from .models import EntryOpportunity
from .config import (
    MIN_ENTRY_ODDS,
    MAX_ENTRY_ODDS,
    MIN_EV_THRESHOLD,
    DEFAULT_TRIGGER_OFFSET,
    SUPPORTED_SPORTS,
    MIN_LOCKED_PROFIT_PCT
)
from .calculator import VolatilityArbCalculator

logger = logging.getLogger(__name__)


class VolatilityArbDetector:
    """Detects volatility arbitrage entry opportunities"""

    def __init__(self):
        self.calculator = VolatilityArbCalculator()

    def detect_entry_opportunities(
        self,
        game: Dict,
        ml_predictions: Optional[Dict] = None
    ) -> List[EntryOpportunity]:
        """
        Detect +EV entry opportunities for volatility arbitrage

        Args:
            game: Live game data with odds
            ml_predictions: ML model win probabilities (optional)

        Returns:
            List of EntryOpportunity objects
        """
        opportunities = []

        game_id = game.get('id')
        sport_key = game.get('sport_key')

        # Only supported sports
        if sport_key not in SUPPORTED_SPORTS:
            return opportunities

        # Must be live game
        if not game.get('is_live', False):
            return opportunities

        home_team = game.get('home_team')
        away_team = game.get('away_team')
        bookmakers = game.get('bookmakers', [])

        # Get ML predictions if available
        home_win_prob = None
        away_win_prob = None

        if ml_predictions:
            home_win_prob = ml_predictions.get('home_win_probability')
            away_win_prob = ml_predictions.get('away_win_probability')

        # Get current game state
        quarter = game.get('quarter', '')
        time_remaining = game.get('time_remaining', '')
        score_home = game.get('score_home', 0)
        score_away = game.get('score_away', 0)

        # Check moneyline markets at each book
        for book in bookmakers:
            book_key = book.get('key')
            book_title = book.get('title', book_key)
            markets = book.get('markets', [])

            for market in markets:
                if market.get('key') != 'h2h':  # Only moneylines
                    continue

                outcomes = market.get('outcomes', [])

                for outcome in outcomes:
                    team = outcome.get('name')
                    odds = outcome.get('price')

                    if not team or not odds:
                        continue

                    # Must be +money (underdog)
                    if odds < MIN_ENTRY_ODDS or odds > MAX_ENTRY_ODDS:
                        continue

                    # Determine if home or away
                    is_home = team == home_team
                    side = 'home' if is_home else 'away'

                    # Get ML prediction for this side
                    if is_home and home_win_prob:
                        true_prob = home_win_prob
                    elif not is_home and away_win_prob:
                        true_prob = away_win_prob
                    else:
                        # No ML prediction, skip
                        continue

                    # Calculate edge
                    implied_prob = self.calculator.american_to_implied_prob(odds)
                    edge, ev_percent = self.calculator.calculate_edge(true_prob, implied_prob)

                    # Must have positive edge above threshold
                    if edge < MIN_EV_THRESHOLD:
                        continue

                    # Determine confidence based on edge size
                    if edge >= 0.10:
                        confidence = 'HIGH'
                    elif edge >= 0.07:
                        confidence = 'MEDIUM'
                    else:
                        confidence = 'LOW'

                    # Suggest trigger price for opposite side
                    suggested_trigger = self.calculator.suggest_trigger_price(
                        odds, DEFAULT_TRIGGER_OFFSET
                    )

                    # Calculate recommended stake (could integrate with Kelly)
                    # For now, use placeholder
                    recommended_stake = 200.0  # Will be replaced with Kelly sizing

                    # Calculate min locked profit
                    min_locked_profit = self.calculator.calculate_min_locked_profit(
                        recommended_stake, MIN_LOCKED_PROFIT_PCT
                    )

                    # Create opportunity
                    opportunity = EntryOpportunity(
                        game_id=game_id,
                        sport=sport_key,
                        home_team=home_team,
                        away_team=away_team,
                        entry_team=team,
                        entry_side=side,
                        entry_odds=odds,
                        implied_prob=implied_prob,
                        true_prob=true_prob,
                        edge=edge,
                        ev_percent=ev_percent,
                        quarter=quarter,
                        time_remaining=time_remaining,
                        score_home=score_home,
                        score_away=score_away,
                        recommended_stake=recommended_stake,
                        confidence=confidence,
                        timestamp=datetime.now(),
                        bookmaker=book_key,
                        bookmaker_title=book_title,
                        suggested_trigger_odds=suggested_trigger,
                        min_locked_profit=min_locked_profit
                    )

                    opportunities.append(opportunity)

        return opportunities

    def filter_best_opportunities(
        self,
        opportunities: List[EntryOpportunity],
        max_per_game: int = 1
    ) -> List[EntryOpportunity]:
        """
        Filter to best opportunities per game

        Args:
            opportunities: List of all opportunities
            max_per_game: Maximum opportunities per game (default 1)

        Returns:
            Filtered list of best opportunities
        """
        # Group by game
        by_game = {}
        for opp in opportunities:
            game_id = opp.game_id
            if game_id not in by_game:
                by_game[game_id] = []
            by_game[game_id].append(opp)

        # Take best from each game (highest EV)
        filtered = []
        for game_id, opps in by_game.items():
            # Sort by EV descending
            opps_sorted = sorted(opps, key=lambda x: x.ev_percent, reverse=True)
            filtered.extend(opps_sorted[:max_per_game])

        return filtered

    def should_enter_position(
        self,
        opportunity: EntryOpportunity,
        user_bankroll: float,
        user_open_positions: int,
        max_open_positions: int = 10
    ) -> Dict:
        """
        Validate if user should enter this position

        Returns:
            {
                'should_enter': bool,
                'reason': str,
                'warnings': List[str]
            }
        """
        warnings = []
        should_enter = True
        reason = ""

        # Check position limit
        if user_open_positions >= max_open_positions:
            should_enter = False
            reason = f"Already have {user_open_positions} open positions (max {max_open_positions})"
            return {'should_enter': should_enter, 'reason': reason, 'warnings': warnings}

        # Check bankroll
        bankroll_check = self.calculator.validate_bankroll(
            opportunity.recommended_stake,
            user_bankroll,
            'standard'
        )

        if not bankroll_check['valid']:
            should_enter = False
            reason = bankroll_check['warning']
            return {'should_enter': should_enter, 'reason': reason, 'warnings': warnings}

        if bankroll_check['warning']:
            warnings.append(bankroll_check['warning'])

        # Check confidence
        if opportunity.confidence == 'LOW':
            warnings.append("Low confidence entry - edge is small")

        return {
            'should_enter': should_enter,
            'reason': "Position meets all criteria" if should_enter else reason,
            'warnings': warnings
        }
