"""
Automatic Play Logger
Integrates with prediction systems to automatically log plays to the database
"""
import requests
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8001"

class AutoPlayLogger:
    """
    Automatically logs plays and results to the persistent database
    """

    def __init__(self, api_base_url: str = API_BASE_URL):
        self.api_base_url = api_base_url

    def log_prediction(self,
                      game_id: str,
                      sport: str,
                      home_team: str,
                      away_team: str,
                      game_time: str,
                      strategy_name: str,
                      play_type: str,
                      recommended_side: str,
                      recommended_line: float,
                      confidence_level: str,
                      our_probability: float,
                      market_odds: Dict[str, int],
                      edge_percentage: float,
                      expected_value: float,
                      bookmaker_data: List[Dict],
                      momentum_indicator: Optional[str] = None,
                      trend_data: Optional[Dict] = None,
                      notes: Optional[str] = None) -> Optional[str]:
        """
        Log a prediction to the database

        Args:
            game_id: Unique game identifier
            sport: NBA, NHL, NFL, MLB, etc.
            home_team: Home team name
            away_team: Away team name
            game_time: Game start time (ISO format)
            strategy_name: Name of strategy (pace_based, fatigue, etc.)
            play_type: TOTALS, SPREAD, MONEYLINE, PROP
            recommended_side: OVER, UNDER, HOME, AWAY, etc.
            recommended_line: The line value (e.g., 225.5)
            confidence_level: HIGH, MEDIUM, LOW
            our_probability: Our calculated probability (0-1)
            market_odds: Dict with 'over' and 'under' odds (American format)
            edge_percentage: Edge percentage (0-100)
            expected_value: Expected value in units
            bookmaker_data: List of all bookmaker odds at time of recommendation
            momentum_indicator: Optional momentum signal
            trend_data: Optional trend analysis data
            notes: Optional additional notes

        Returns:
            play_id if successful, None if failed
        """
        # Find best bookmaker for this play
        best_book, best_price, alternate_books = self._find_best_line(
            bookmaker_data, play_type, recommended_side, recommended_line
        )

        # Calculate market probability
        if play_type == "TOTALS":
            if recommended_side == "OVER":
                market_prob = self._american_to_prob(market_odds.get('over', -110))
            else:
                market_prob = self._american_to_prob(market_odds.get('under', -110))
        else:
            # For spread/ML, use appropriate odds
            market_prob = self._american_to_prob(best_price)

        # Determine strategy category
        strategy_category = self._get_strategy_category(strategy_name)

        play_data = {
            "game_id": game_id,
            "sport": sport.upper(),
            "home_team": home_team,
            "away_team": away_team,
            "game_time": game_time,
            "strategy_name": strategy_name,
            "strategy_category": strategy_category,
            "confidence_level": confidence_level,
            "play_type": play_type,
            "recommended_side": recommended_side,
            "recommended_line": recommended_line,
            "recommended_price": best_price,
            "best_book": best_book,
            "alternate_books": alternate_books,
            "our_probability": our_probability,
            "market_probability": market_prob,
            "edge_percentage": edge_percentage,
            "expected_value": expected_value,
            "momentum_indicator": momentum_indicator,
            "trend_data": trend_data,
            "notes": notes
        }

        try:
            response = requests.post(
                f"{self.api_base_url}/api/plays/log",
                json=play_data,
                timeout=5
            )

            if response.status_code == 200:
                result = response.json()
                play_id = result.get('play_id')
                logger.info(f"✓ Logged play: {play_id} - {sport} {strategy_name} {recommended_side} {recommended_line} @ {best_book}")
                return play_id
            else:
                logger.error(f"Failed to log play: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error logging play: {str(e)}")
            return None

    def record_result(self,
                     play_id: str,
                     result: str,
                     final_score_home: int,
                     final_score_away: int,
                     actual_total: Optional[float] = None,
                     closing_line: Optional[float] = None,
                     closing_price: Optional[int] = None,
                     profit_loss: float = 0.0,
                     roi: float = 0.0,
                     verified: bool = True) -> bool:
        """
        Record the result of a play

        Args:
            play_id: ID of the play from log_prediction
            result: 'won', 'lost', or 'push'
            final_score_home: Home team final score
            final_score_away: Away team final score
            actual_total: Actual game total
            closing_line: Closing line value
            closing_price: Closing odds (American format)
            profit_loss: Profit/loss in units
            roi: Return on investment percentage
            verified: Whether result is verified

        Returns:
            True if successful, False otherwise
        """
        result_data = {
            "play_id": play_id,
            "result": result,
            "final_score_home": final_score_home,
            "final_score_away": final_score_away,
            "actual_total": actual_total or (final_score_home + final_score_away),
            "closing_line": closing_line,
            "closing_price": closing_price,
            "line_movement": (closing_line - 0) if closing_line else 0.0,  # Will calculate properly
            "profit_loss": profit_loss,
            "roi": roi,
            "verified": verified
        }

        try:
            response = requests.post(
                f"{self.api_base_url}/api/plays/result",
                json=result_data,
                timeout=5
            )

            if response.status_code == 200:
                logger.info(f"✓ Recorded result: {play_id} - {result.upper()} ({profit_loss:+.2f} units)")
                return True
            else:
                logger.error(f"Failed to record result: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error recording result: {str(e)}")
            return False

    def _find_best_line(self, bookmaker_data: List[Dict], play_type: str,
                       recommended_side: str, target_line: float) -> tuple:
        """
        Find the best bookmaker and price for the recommended play

        Returns:
            (best_book, best_price, alternate_books)
        """
        if not bookmaker_data:
            return ("Unknown", -110, [])

        best_book = None
        best_price = -110  # Default
        alternate_books = []

        for book in bookmaker_data:
            book_name = book.get('title', book.get('bookmaker', 'Unknown'))

            if play_type == "TOTALS":
                # Find totals market
                for market in book.get('markets', []):
                    if market.get('key') == 'totals':
                        for outcome in market.get('outcomes', []):
                            # Check if this is the line we want
                            if abs(outcome.get('point', 0) - target_line) < 0.5:
                                price = outcome.get('price', -110)

                                # Check if this is the side we want
                                if (recommended_side == "OVER" and outcome.get('name') == "Over") or \
                                   (recommended_side == "UNDER" and outcome.get('name') == "Under"):

                                    # Track this book
                                    alternate_books.append({
                                        "bookmaker": book_name,
                                        "line": outcome.get('point'),
                                        "price": price
                                    })

                                    # Is this the best price so far?
                                    if best_book is None or price > best_price:
                                        best_book = book_name
                                        best_price = price

        if best_book is None:
            best_book = bookmaker_data[0].get('title', 'DraftKings')

        return (best_book, best_price, alternate_books[:5])  # Keep top 5 alternates

    def _get_strategy_category(self, strategy_name: str) -> str:
        """Map strategy name to category"""
        strategy_map = {
            'pace_based': 'pace_based',
            'fatigue': 'fatigue',
            'regression': 'regression',
            'moneyline': 'moneyline',
            'multi_sport_ensemble': 'multi_sport_ensemble',
            'live_betting': 'live_betting',
            'arbitrage': 'arbitrage',
            'steam_move': 'steam_move',
            'line_movement': 'line_movement',
            'sharp_action': 'sharp_action',
            'public_fade': 'public_fade',
            'weather_impact': 'weather_impact'
        }
        return strategy_map.get(strategy_name.lower(), strategy_name)

    def _american_to_prob(self, odds: int) -> float:
        """Convert American odds to implied probability"""
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)


# Global instance
auto_logger = AutoPlayLogger()


def log_nba_prediction(prediction_data: Dict, bookmaker_data: List[Dict]) -> Optional[str]:
    """
    Helper function to log NBA predictions

    Args:
        prediction_data: Dict with prediction details from your NBA model
        bookmaker_data: List of bookmaker odds from Odds API

    Returns:
        play_id if logged, None otherwise
    """
    return auto_logger.log_prediction(
        game_id=prediction_data['game_id'],
        sport='NBA',
        home_team=prediction_data['home_team'],
        away_team=prediction_data['away_team'],
        game_time=prediction_data['game_time'],
        strategy_name=prediction_data.get('strategy', 'pace_based'),
        play_type='TOTALS',
        recommended_side=prediction_data['recommendation'],
        recommended_line=prediction_data['market_total'],
        confidence_level=prediction_data['confidence'],
        our_probability=prediction_data.get('our_probability', 0.55),
        market_odds={'over': -110, 'under': -110},
        edge_percentage=prediction_data['edge'],
        expected_value=prediction_data.get('expected_value', prediction_data['edge'] * 0.1),
        bookmaker_data=bookmaker_data,
        notes=prediction_data.get('notes', '')
    )


def record_nba_result(play_id: str, game_result: Dict) -> bool:
    """
    Helper function to record NBA results

    Args:
        play_id: ID from log_prediction
        game_result: Dict with final score and outcome

    Returns:
        True if recorded successfully
    """
    # Determine if bet won/lost/push
    actual_total = game_result['home_score'] + game_result['away_score']

    # You'll implement the win/loss logic based on your bet
    # This is a simplified example
    result = game_result.get('result', 'pending')
    profit_loss = game_result.get('profit_loss', 0.0)
    roi = game_result.get('roi', 0.0)

    return auto_logger.record_result(
        play_id=play_id,
        result=result,
        final_score_home=game_result['home_score'],
        final_score_away=game_result['away_score'],
        actual_total=actual_total,
        profit_loss=profit_loss,
        roi=roi
    )
