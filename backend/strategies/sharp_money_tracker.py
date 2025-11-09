"""
Sharp Money Tracking Strategy
Detects professional betting action by analyzing line movements

Key Concepts:
- Reverse Line Movement (RLM): Line moves opposite to public betting
- Sharp Book Leadership: Pinnacle, Circa, Bookmaker lead the market
- Steam Moves: Rapid coordinated line movement across books
- Line magnitude: Significant moves (2+ points NBA, 0.5+ goals NHL, 3+ points NFL)

Historical Edge:
- Following sharp money: 56-58% win rate historically
- RLM situations: 54-56% ATS
- Steam moves: 60%+ win rate when caught early
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class BookmakerOdds:
    """Single bookmaker's odds for a game"""
    bookmaker: str
    spread_home: Optional[float]
    spread_away: Optional[float]
    spread_home_price: Optional[int]
    spread_away_price: Optional[int]
    total: Optional[float]
    over_price: Optional[int]
    under_price: Optional[int]
    moneyline_home: Optional[int]
    moneyline_away: Optional[int]
    last_update: datetime


@dataclass
class LineMovement:
    """Represents a line movement for a game"""
    game_id: str
    sport: str
    market_type: str  # 'spreads', 'totals', 'h2h'
    opening_line: float
    current_line: float
    movement: float  # Positive or negative
    movement_pct: float
    sharp_books_moved: List[str]  # Which sharp books moved
    total_books_moved: int
    movement_direction: str  # 'SHARP', 'PUBLIC', 'NEUTRAL'
    timestamp: datetime


@dataclass
class SharpMoneyAlert:
    """Alert for detected sharp money action"""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    alert_type: str  # 'RLM', 'STEAM', 'SHARP_BOOK', 'LINE_FREEZE'
    market_type: str  # 'spread', 'total', 'moneyline'
    recommendation: str  # Which side to bet
    opening_line: float
    current_line: float
    movement: float
    sharp_books_involved: List[str]
    confidence: float  # 0-1
    confidence_level: str  # 'HIGH', 'MEDIUM', 'LOW'
    reasoning: str
    key_factors: List[str]
    timestamp: datetime


class SharpMoneyTracker:
    """
    Track sharp money movement across bookmakers

    Sharp Books (market leaders):
    - Pinnacle: Sharpest book, highest limits, lowest vig
    - Circa Sports: Sharp NFL/NCAAF book
    - Bookmaker: Sharp offshore book
    - BetOnline: Often follows sharp action

    Square Books (public books):
    - DraftKings, FanDuel, BetMGM, Caesars
    - Higher vig, lower limits, recreational bettors
    """

    SHARP_BOOKS = ['pinnacle', 'circa', 'bookmaker', 'betonline']
    SQUARE_BOOKS = ['draftkings', 'fanduel', 'betmgm', 'williamhill_us', 'caesars']

    # Movement thresholds by sport
    MOVEMENT_THRESHOLDS = {
        'basketball_nba': {'spread': 2.0, 'total': 2.0},
        'basketball_ncaab': {'spread': 2.0, 'total': 2.0},
        'americanfootball_nfl': {'spread': 3.0, 'total': 3.0},
        'americanfootball_ncaaf': {'spread': 3.0, 'total': 3.0},
        'icehockey_nhl': {'spread': 0.5, 'total': 0.5},
        'baseball_mlb': {'spread': 0.5, 'total': 0.5},
    }

    def __init__(
        self,
        min_sharp_books: int = 2,  # Minimum sharp books that must agree
        min_movement_magnitude: float = 1.5,  # Minimum line movement
        steam_move_threshold: int = 5,  # Books moving together
    ):
        self.min_sharp_books = min_sharp_books
        self.min_movement_magnitude = min_movement_magnitude
        self.steam_move_threshold = steam_move_threshold

        # Store opening lines (game_id -> market_type -> value)
        self.opening_lines: Dict[str, Dict[str, float]] = {}

        # Store line movement history
        self.line_history: Dict[str, List[LineMovement]] = {}

    def analyze_game(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        bookmaker_odds: List[BookmakerOdds],
        opening_odds: Optional[List[BookmakerOdds]] = None
    ) -> List[SharpMoneyAlert]:
        """
        Analyze a game for sharp money indicators

        Args:
            game_id: Unique game identifier
            sport: Sport key (e.g., 'basketball_nba')
            home_team: Home team name
            away_team: Away team name
            bookmaker_odds: Current odds from all bookmakers
            opening_odds: Opening odds (if available)

        Returns:
            List of SharpMoneyAlert objects
        """
        alerts = []

        # Initialize opening lines if not already stored
        if game_id not in self.opening_lines and opening_odds:
            self._store_opening_lines(game_id, opening_odds)

        # 1. Check for spread sharp money
        spread_alert = self._check_spread_sharp_money(
            game_id, sport, home_team, away_team, bookmaker_odds
        )
        if spread_alert:
            alerts.append(spread_alert)

        # 2. Check for total sharp money
        total_alert = self._check_total_sharp_money(
            game_id, sport, home_team, away_team, bookmaker_odds
        )
        if total_alert:
            alerts.append(total_alert)

        # 3. Check for moneyline sharp money
        ml_alert = self._check_moneyline_sharp_money(
            game_id, sport, home_team, away_team, bookmaker_odds
        )
        if ml_alert:
            alerts.append(ml_alert)

        # 4. Check for steam moves (rapid coordinated movement)
        steam_alerts = self._check_steam_moves(
            game_id, sport, home_team, away_team, bookmaker_odds
        )
        alerts.extend(steam_alerts)

        return alerts

    def _store_opening_lines(self, game_id: str, opening_odds: List[BookmakerOdds]):
        """Store opening lines for comparison"""
        if game_id not in self.opening_lines:
            self.opening_lines[game_id] = {}

        # Use sharp book opening lines as baseline
        for odds in opening_odds:
            if odds.bookmaker.lower() in self.SHARP_BOOKS:
                if odds.spread_home is not None:
                    self.opening_lines[game_id]['spread'] = odds.spread_home
                if odds.total is not None:
                    self.opening_lines[game_id]['total'] = odds.total
                break

        # Fallback to any book if no sharp books found
        if 'spread' not in self.opening_lines[game_id] and opening_odds:
            if opening_odds[0].spread_home is not None:
                self.opening_lines[game_id]['spread'] = opening_odds[0].spread_home
        if 'total' not in self.opening_lines[game_id] and opening_odds:
            if opening_odds[0].total is not None:
                self.opening_lines[game_id]['total'] = opening_odds[0].total

    def _check_spread_sharp_money(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        bookmaker_odds: List[BookmakerOdds]
    ) -> Optional[SharpMoneyAlert]:
        """Check spread for sharp money indicators"""

        # Get opening and current lines
        opening_line = self.opening_lines.get(game_id, {}).get('spread')
        if opening_line is None:
            return None

        # Calculate consensus current line (average across all books)
        current_lines = [odds.spread_home for odds in bookmaker_odds if odds.spread_home is not None]
        if not current_lines:
            return None

        current_line = sum(current_lines) / len(current_lines)
        movement = current_line - opening_line

        # Get threshold for this sport
        threshold = self.MOVEMENT_THRESHOLDS.get(sport, {}).get('spread', 2.0)

        # Check if movement exceeds threshold
        if abs(movement) < threshold:
            return None

        # Identify which sharp books moved
        sharp_books_moved = []
        for odds in bookmaker_odds:
            if odds.bookmaker.lower() in self.SHARP_BOOKS:
                if odds.spread_home is not None and abs(odds.spread_home - opening_line) >= threshold:
                    sharp_books_moved.append(odds.bookmaker)

        # Must have minimum sharp books agreeing
        if len(sharp_books_moved) < self.min_sharp_books:
            return None

        # Determine which side sharp money is on
        if movement > 0:
            # Line moved in favor of home (away getting more points)
            recommendation = f"BET {away_team} +{current_line:.1f}"
            side = away_team
        else:
            # Line moved in favor of away (home getting more points)
            recommendation = f"BET {home_team} {current_line:+.1f}"
            side = home_team

        # Calculate confidence
        confidence = self._calculate_confidence(
            movement=abs(movement),
            threshold=threshold,
            sharp_books_count=len(sharp_books_moved),
            total_books=len(bookmaker_odds)
        )

        if confidence >= 0.75:
            confidence_level = 'HIGH'
        elif confidence >= 0.60:
            confidence_level = 'MEDIUM'
        else:
            confidence_level = 'LOW'

        # Generate reasoning
        key_factors = [
            f"Line moved {abs(movement):.1f} points from {opening_line:+.1f} to {current_line:+.1f}",
            f"{len(sharp_books_moved)} sharp books led the move: {', '.join(sharp_books_moved)}",
            f"Movement exceeds {threshold:.1f} point threshold",
            f"Sharp money on {side}"
        ]

        reasoning = f"Sharp books moved spread {abs(movement):.1f} points favoring {side}. {len(sharp_books_moved)} sharp books ({', '.join(sharp_books_moved)}) led this movement."

        return SharpMoneyAlert(
            game_id=game_id,
            sport=sport,
            home_team=home_team,
            away_team=away_team,
            alert_type='SHARP_BOOK',
            market_type='spread',
            recommendation=recommendation,
            opening_line=opening_line,
            current_line=current_line,
            movement=movement,
            sharp_books_involved=sharp_books_moved,
            confidence=confidence,
            confidence_level=confidence_level,
            reasoning=reasoning,
            key_factors=key_factors,
            timestamp=datetime.now()
        )

    def _check_total_sharp_money(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        bookmaker_odds: List[BookmakerOdds]
    ) -> Optional[SharpMoneyAlert]:
        """Check total for sharp money indicators"""

        # Get opening and current totals
        opening_total = self.opening_lines.get(game_id, {}).get('total')
        if opening_total is None:
            return None

        # Calculate consensus current total
        current_totals = [odds.total for odds in bookmaker_odds if odds.total is not None]
        if not current_totals:
            return None

        current_total = sum(current_totals) / len(current_totals)
        movement = current_total - opening_total

        # Get threshold
        threshold = self.MOVEMENT_THRESHOLDS.get(sport, {}).get('total', 2.0)

        if abs(movement) < threshold:
            return None

        # Check sharp books
        sharp_books_moved = []
        for odds in bookmaker_odds:
            if odds.bookmaker.lower() in self.SHARP_BOOKS:
                if odds.total is not None and abs(odds.total - opening_total) >= threshold:
                    sharp_books_moved.append(odds.bookmaker)

        if len(sharp_books_moved) < self.min_sharp_books:
            return None

        # Determine over/under
        if movement > 0:
            recommendation = f"BET OVER {current_total:.1f}"
            direction = "OVER"
        else:
            recommendation = f"BET UNDER {current_total:.1f}"
            direction = "UNDER"

        confidence = self._calculate_confidence(
            movement=abs(movement),
            threshold=threshold,
            sharp_books_count=len(sharp_books_moved),
            total_books=len(bookmaker_odds)
        )

        if confidence >= 0.75:
            confidence_level = 'HIGH'
        elif confidence >= 0.60:
            confidence_level = 'MEDIUM'
        else:
            confidence_level = 'LOW'

        key_factors = [
            f"Total moved {abs(movement):.1f} points from {opening_total:.1f} to {current_total:.1f}",
            f"{len(sharp_books_moved)} sharp books led: {', '.join(sharp_books_moved)}",
            f"Sharp money on {direction}"
        ]

        reasoning = f"Sharp books moved total {abs(movement):.1f} points to {current_total:.1f}. {len(sharp_books_moved)} sharp books ({', '.join(sharp_books_moved)}) indicate {direction} value."

        return SharpMoneyAlert(
            game_id=game_id,
            sport=sport,
            home_team=home_team,
            away_team=away_team,
            alert_type='SHARP_BOOK',
            market_type='total',
            recommendation=recommendation,
            opening_line=opening_total,
            current_line=current_total,
            movement=movement,
            sharp_books_involved=sharp_books_moved,
            confidence=confidence,
            confidence_level=confidence_level,
            reasoning=reasoning,
            key_factors=key_factors,
            timestamp=datetime.now()
        )

    def _check_moneyline_sharp_money(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        bookmaker_odds: List[BookmakerOdds]
    ) -> Optional[SharpMoneyAlert]:
        """Check moneyline for sharp money (primarily for underdogs)"""

        # Focus on underdog ML moves (sharps often bet dog MLs)
        # Look for significant price shortening on underdog

        sharp_ml_moves = []

        for odds in bookmaker_odds:
            if odds.bookmaker.lower() not in self.SHARP_BOOKS:
                continue

            if odds.moneyline_home and odds.moneyline_away:
                # Identify underdog
                if odds.moneyline_home > odds.moneyline_away:
                    # Home is underdog
                    # Sharp money would shorten home ML (make less plus money)
                    # We'd need opening ML to detect this properly
                    pass

        # Skip ML for now - needs opening ML data
        return None

    def _check_steam_moves(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        bookmaker_odds: List[BookmakerOdds]
    ) -> List[SharpMoneyAlert]:
        """
        Check for steam moves (rapid coordinated line movement)

        Steam move = 5+ books move line in same direction within short time
        """
        # This requires real-time tracking which we'll implement in game_tracker
        # For now, return empty list
        return []

    def _calculate_confidence(
        self,
        movement: float,
        threshold: float,
        sharp_books_count: int,
        total_books: int
    ) -> float:
        """Calculate confidence score for sharp money alert"""

        # Base confidence
        confidence = 0.50

        # More movement = more confidence (up to 2x threshold)
        movement_factor = min(movement / threshold, 2.0)
        confidence += 0.15 * (movement_factor - 1.0)

        # More sharp books = more confidence
        if sharp_books_count >= 3:
            confidence += 0.20
        elif sharp_books_count >= 2:
            confidence += 0.10

        # High percentage of books moved
        if total_books > 0:
            books_moved_pct = sharp_books_count / total_books
            if books_moved_pct > 0.5:
                confidence += 0.10

        return min(confidence, 0.95)


# Example usage
if __name__ == "__main__":
    tracker = SharpMoneyTracker()

    # Example: NBA game with sharp money on away team
    game_id = "test_nba_123"
    sport = "basketball_nba"
    home_team = "Los Angeles Lakers"
    away_team = "Golden State Warriors"

    # Mock bookmaker odds
    bookmaker_odds = [
        BookmakerOdds(
            bookmaker="pinnacle",
            spread_home=-3.5,
            spread_away=3.5,
            spread_home_price=-105,
            spread_away_price=-105,
            total=220.5,
            over_price=-110,
            under_price=-110,
            moneyline_home=-160,
            moneyline_away=140,
            last_update=datetime.now()
        ),
        BookmakerOdds(
            bookmaker="circa",
            spread_home=-3.5,
            spread_away=3.5,
            spread_home_price=-108,
            spread_away_price=-102,
            total=220.5,
            over_price=-110,
            under_price=-110,
            moneyline_home=-165,
            moneyline_away=145,
            last_update=datetime.now()
        ),
        BookmakerOdds(
            bookmaker="draftkings",
            spread_home=-1.5,
            spread_away=1.5,
            spread_home_price=-110,
            spread_away_price=-110,
            total=222.5,
            over_price=-110,
            under_price=-110,
            moneyline_home=-125,
            moneyline_away=105,
            last_update=datetime.now()
        ),
    ]

    # Mock opening odds (Lakers opened -1.5)
    opening_odds = [
        BookmakerOdds(
            bookmaker="pinnacle",
            spread_home=-1.5,
            spread_away=1.5,
            spread_home_price=-105,
            spread_away_price=-105,
            total=218.5,
            over_price=-110,
            under_price=-110,
            moneyline_home=-135,
            moneyline_away=115,
            last_update=datetime.now()
        ),
    ]

    # Analyze
    alerts = tracker.analyze_game(
        game_id=game_id,
        sport=sport,
        home_team=home_team,
        away_team=away_team,
        bookmaker_odds=bookmaker_odds,
        opening_odds=opening_odds
    )

    if alerts:
        print("="*70)
        print("SHARP MONEY ALERTS")
        print("="*70)
        for alert in alerts:
            print(f"\nAlert Type: {alert.alert_type}")
            print(f"Market: {alert.market_type}")
            print(f"Game: {alert.away_team} @ {alert.home_team}")
            print(f"Recommendation: {alert.recommendation}")
            print(f"Line Movement: {alert.opening_line:.1f} → {alert.current_line:.1f} ({alert.movement:+.1f})")
            print(f"Sharp Books: {', '.join(alert.sharp_books_involved)}")
            print(f"Confidence: {alert.confidence_level} ({alert.confidence:.0%})")
            print(f"\nReasoning: {alert.reasoning}")
            print(f"\nKey Factors:")
            for factor in alert.key_factors:
                print(f"  • {factor}")
        print("="*70)
    else:
        print("No sharp money detected")
