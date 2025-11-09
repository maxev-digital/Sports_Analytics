"""
Closing Line Value (CLV) Tracker
Tracks whether user bets beat the closing line - the most important metric for long-term profitability

Key Concepts:
- Closing Line: The final line before game starts
- CLV: Difference between your bet line and closing line
- Positive CLV = You got a better number than closing (good!)
- Negative CLV = You got a worse number than closing (bad)

Why It Matters:
- Beating closing line = 53%+ win rate long-term
- Consistently positive CLV = profitable bettor
- The market is most efficient at closing (sharpest number)
- If you beat closing consistently, you WILL profit long-term

Industry Benchmarks:
- Sharp bettors: +2 to +5 points CLV average (NBA/NFL)
- Break-even bettors: -0.5 to +1 points CLV
- Losing bettors: -2+ points CLV (consistently getting worst of number)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BetType(str, Enum):
    """Type of bet"""
    SPREAD = "spread"
    TOTAL = "total"
    MONEYLINE = "moneyline"


class BetSide(str, Enum):
    """Which side of bet"""
    HOME = "home"
    AWAY = "away"
    OVER = "over"
    UNDER = "under"


@dataclass
class UserBet:
    """Represents a user's placed bet"""
    bet_id: str
    user_id: str
    game_id: str
    sport: str
    home_team: str
    away_team: str
    bet_type: BetType
    bet_side: BetSide
    line: float  # The line they got
    odds: int  # American odds (e.g., -110)
    stake: float  # Amount wagered
    bet_time: datetime
    game_start_time: datetime


@dataclass
class ClosingLine:
    """Closing line for a game"""
    game_id: str
    spread_home: Optional[float]
    spread_away: Optional[float]
    total: Optional[float]
    moneyline_home: Optional[int]
    moneyline_away: Optional[int]
    closing_time: datetime
    bookmaker_source: str  # Which sharp book (Pinnacle preferred)


@dataclass
class CLVResult:
    """CLV calculation result for a single bet"""
    bet_id: str
    user_id: str
    game_id: str
    sport: str
    home_team: str
    away_team: str
    bet_type: BetType
    bet_side: BetSide
    user_line: float
    closing_line: float
    clv: float  # Positive = good, Negative = bad
    clv_percentage: float  # As percentage
    clv_rating: str  # 'EXCELLENT', 'GOOD', 'NEUTRAL', 'BAD', 'TERRIBLE'
    odds_comparison: Dict[str, int]  # User odds vs closing odds
    bet_time: datetime
    game_start_time: datetime


@dataclass
class UserCLVStats:
    """Aggregate CLV statistics for a user"""
    user_id: str
    total_bets: int
    avg_clv: float
    median_clv: float
    positive_clv_count: int
    negative_clv_count: int
    positive_clv_percentage: float
    best_clv: float
    worst_clv: float
    clv_by_sport: Dict[str, float]
    clv_by_bet_type: Dict[str, float]
    sharp_rating: str  # 'SHARP', 'AVERAGE', 'SQUARE'
    expected_roi: float  # Based on CLV


class CLVTracker:
    """
    Track Closing Line Value for user bets

    CLV Formula:
    - Spread/Total: CLV = User Line - Closing Line (adjusted for side)
    - Moneyline: CLV = (User Odds - Closing Odds) converted to points

    Examples:
    1. Spread Bet:
       - User bets Lakers -3.5
       - Closing line: Lakers -5.5
       - CLV = +2.0 points (EXCELLENT - you got 2 extra points)

    2. Total Bet:
       - User bets Over 220.5
       - Closing line: 222.5
       - CLV = +2.0 points (EXCELLENT - you got 2 extra points to hit over)

    3. Spread Bet (Underdog):
       - User bets Warriors +7.5
       - Closing line: Warriors +5.5
       - CLV = +2.0 points (EXCELLENT - you got 2 extra points of cushion)
    """

    # CLV Rating thresholds (in points/goals)
    CLV_RATINGS = {
        'NBA': {
            'EXCELLENT': 2.5,  # +2.5 or better
            'GOOD': 1.0,       # +1.0 to +2.4
            'NEUTRAL': -1.0,   # -0.9 to +0.9
            'BAD': -2.5,       # -1.0 to -2.4
            'TERRIBLE': -999   # -2.5 or worse
        },
        'NFL': {
            'EXCELLENT': 3.0,
            'GOOD': 1.5,
            'NEUTRAL': -1.5,
            'BAD': -3.0,
            'TERRIBLE': -999
        },
        'NHL': {
            'EXCELLENT': 0.5,
            'GOOD': 0.25,
            'NEUTRAL': -0.25,
            'BAD': -0.5,
            'TERRIBLE': -999
        },
        'MLB': {
            'EXCELLENT': 0.5,
            'GOOD': 0.25,
            'NEUTRAL': -0.25,
            'BAD': -0.5,
            'TERRIBLE': -999
        }
    }

    def __init__(self):
        # Store user bets
        self.user_bets: Dict[str, UserBet] = {}  # bet_id -> UserBet

        # Store closing lines
        self.closing_lines: Dict[str, ClosingLine] = {}  # game_id -> ClosingLine

        # Store CLV results
        self.clv_results: Dict[str, CLVResult] = {}  # bet_id -> CLVResult

        # Cache user stats
        self.user_stats_cache: Dict[str, UserCLVStats] = {}

    def log_user_bet(self, bet: UserBet):
        """Log a user's bet for CLV tracking"""
        self.user_bets[bet.bet_id] = bet
        logger.info(f"Logged bet {bet.bet_id} for user {bet.user_id}: {bet.bet_type} {bet.bet_side} {bet.line}")

    def log_closing_line(self, closing_line: ClosingLine):
        """Log closing line for a game"""
        self.closing_lines[closing_line.game_id] = closing_line
        logger.info(f"Logged closing line for game {closing_line.game_id}")

        # Calculate CLV for any pending bets on this game
        self._calculate_clv_for_game(closing_line.game_id)

    def _calculate_clv_for_game(self, game_id: str):
        """Calculate CLV for all bets on a game once closing line is available"""
        closing_line = self.closing_lines.get(game_id)
        if not closing_line:
            return

        # Find all bets on this game
        game_bets = [bet for bet in self.user_bets.values() if bet.game_id == game_id]

        for bet in game_bets:
            # Skip if already calculated
            if bet.bet_id in self.clv_results:
                continue

            clv_result = self._calculate_clv(bet, closing_line)
            if clv_result:
                self.clv_results[bet.bet_id] = clv_result

                # Log significant CLV
                if clv_result.clv_rating in ['EXCELLENT', 'TERRIBLE']:
                    logger.warning(
                        f"📊 {clv_result.clv_rating} CLV: User {bet.user_id} - "
                        f"{bet.home_team} vs {bet.away_team} - "
                        f"{bet.bet_type} {bet.bet_side} @ {bet.line} "
                        f"(Closing: {clv_result.closing_line}) - CLV: {clv_result.clv:+.1f}"
                    )

                # Invalidate user stats cache
                if bet.user_id in self.user_stats_cache:
                    del self.user_stats_cache[bet.user_id]

    def _calculate_clv(self, bet: UserBet, closing_line: ClosingLine) -> Optional[CLVResult]:
        """Calculate CLV for a single bet"""

        user_line = bet.line
        closing_line_value = None

        # Get closing line based on bet type and side
        if bet.bet_type == BetType.SPREAD:
            if bet.bet_side == BetSide.HOME:
                closing_line_value = closing_line.spread_home
            else:  # AWAY
                closing_line_value = closing_line.spread_away

            if closing_line_value is None:
                return None

            # Calculate CLV for spread
            # If betting home favorite (-3.5 vs -5.5 closing) = +2.0 CLV (good)
            # If betting away underdog (+7.5 vs +5.5 closing) = +2.0 CLV (good)
            if bet.bet_side == BetSide.HOME:
                clv = closing_line_value - user_line  # More negative closing = better for home bettor
            else:  # AWAY
                clv = user_line - closing_line_value  # More positive user line = better for away bettor

        elif bet.bet_type == BetType.TOTAL:
            closing_line_value = closing_line.total
            if closing_line_value is None:
                return None

            # Calculate CLV for total
            if bet.bet_side == BetSide.OVER:
                clv = closing_line_value - user_line  # Lower user line = easier to hit over
            else:  # UNDER
                clv = user_line - closing_line_value  # Higher user line = easier to hit under

        elif bet.bet_type == BetType.MONEYLINE:
            if bet.bet_side == BetSide.HOME:
                closing_line_value = closing_line.moneyline_home
            else:
                closing_line_value = closing_line.moneyline_away

            if closing_line_value is None:
                return None

            # Convert odds difference to implied probability difference
            user_implied = self._odds_to_probability(bet.odds)
            closing_implied = self._odds_to_probability(closing_line_value)
            clv = (closing_implied - user_implied) * 100  # As percentage points

        else:
            return None

        # Calculate CLV percentage
        clv_percentage = (clv / abs(closing_line_value)) * 100 if closing_line_value != 0 else 0

        # Determine CLV rating
        sport = self._map_sport_key(bet.sport)
        clv_rating = self._get_clv_rating(clv, sport)

        return CLVResult(
            bet_id=bet.bet_id,
            user_id=bet.user_id,
            game_id=bet.game_id,
            sport=bet.sport,
            home_team=bet.home_team,
            away_team=bet.away_team,
            bet_type=bet.bet_type,
            bet_side=bet.bet_side,
            user_line=user_line,
            closing_line=closing_line_value,
            clv=clv,
            clv_percentage=clv_percentage,
            clv_rating=clv_rating,
            odds_comparison={
                'user_odds': bet.odds,
                'closing_odds': closing_line_value if bet.bet_type == BetType.MONEYLINE else None
            },
            bet_time=bet.bet_time,
            game_start_time=bet.game_start_time
        )

    def _odds_to_probability(self, american_odds: int) -> float:
        """Convert American odds to implied probability"""
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)

    def _map_sport_key(self, sport_key: str) -> str:
        """Map sport key to rating category"""
        if 'nba' in sport_key.lower() or 'ncaab' in sport_key.lower():
            return 'NBA'
        elif 'nfl' in sport_key.lower() or 'ncaaf' in sport_key.lower():
            return 'NFL'
        elif 'nhl' in sport_key.lower():
            return 'NHL'
        elif 'mlb' in sport_key.lower():
            return 'MLB'
        else:
            return 'NBA'  # Default

    def _get_clv_rating(self, clv: float, sport: str) -> str:
        """Get CLV rating based on value and sport"""
        thresholds = self.CLV_RATINGS.get(sport, self.CLV_RATINGS['NBA'])

        if clv >= thresholds['EXCELLENT']:
            return 'EXCELLENT'
        elif clv >= thresholds['GOOD']:
            return 'GOOD'
        elif clv >= thresholds['NEUTRAL']:
            return 'NEUTRAL'
        elif clv >= thresholds['BAD']:
            return 'BAD'
        else:
            return 'TERRIBLE'

    def get_user_clv_stats(self, user_id: str) -> Optional[UserCLVStats]:
        """Get aggregate CLV statistics for a user"""

        # Check cache
        if user_id in self.user_stats_cache:
            return self.user_stats_cache[user_id]

        # Get all CLV results for user
        user_results = [r for r in self.clv_results.values() if r.user_id == user_id]

        if not user_results:
            return None

        # Calculate statistics
        total_bets = len(user_results)
        clv_values = [r.clv for r in user_results]
        avg_clv = sum(clv_values) / total_bets
        median_clv = sorted(clv_values)[total_bets // 2]

        positive_clv_count = len([v for v in clv_values if v > 0])
        negative_clv_count = len([v for v in clv_values if v < 0])
        positive_clv_percentage = (positive_clv_count / total_bets) * 100

        best_clv = max(clv_values)
        worst_clv = min(clv_values)

        # CLV by sport
        clv_by_sport = {}
        for sport in set(r.sport for r in user_results):
            sport_clvs = [r.clv for r in user_results if r.sport == sport]
            clv_by_sport[sport] = sum(sport_clvs) / len(sport_clvs)

        # CLV by bet type
        clv_by_bet_type = {}
        for bet_type in set(r.bet_type for r in user_results):
            type_clvs = [r.clv for r in user_results if r.bet_type == bet_type]
            clv_by_bet_type[bet_type] = sum(type_clvs) / len(type_clvs)

        # Sharp rating
        if avg_clv >= 1.5:
            sharp_rating = 'SHARP'
        elif avg_clv >= -0.5:
            sharp_rating = 'AVERAGE'
        else:
            sharp_rating = 'SQUARE'

        # Expected ROI (rough estimate based on CLV)
        # Studies show ~0.1% ROI per 0.1 points of CLV
        expected_roi = avg_clv * 0.5  # Conservative estimate

        stats = UserCLVStats(
            user_id=user_id,
            total_bets=total_bets,
            avg_clv=avg_clv,
            median_clv=median_clv,
            positive_clv_count=positive_clv_count,
            negative_clv_count=negative_clv_count,
            positive_clv_percentage=positive_clv_percentage,
            best_clv=best_clv,
            worst_clv=worst_clv,
            clv_by_sport=clv_by_sport,
            clv_by_bet_type=clv_by_bet_type,
            sharp_rating=sharp_rating,
            expected_roi=expected_roi
        )

        # Cache result
        self.user_stats_cache[user_id] = stats

        return stats

    def get_recent_clv_results(self, user_id: Optional[str] = None, limit: int = 50) -> List[CLVResult]:
        """Get recent CLV results, optionally filtered by user"""
        results = list(self.clv_results.values())

        if user_id:
            results = [r for r in results if r.user_id == user_id]

        # Sort by bet time (most recent first)
        results.sort(key=lambda r: r.bet_time, reverse=True)

        return results[:limit]


# Example usage
if __name__ == "__main__":
    tracker = CLVTracker()

    # Example: User bets Lakers -3.5
    user_bet = UserBet(
        bet_id="bet_123",
        user_id="user_456",
        game_id="game_789",
        sport="basketball_nba",
        home_team="Los Angeles Lakers",
        away_team="Golden State Warriors",
        bet_type=BetType.SPREAD,
        bet_side=BetSide.HOME,
        line=-3.5,
        odds=-110,
        stake=100.0,
        bet_time=datetime.now(),
        game_start_time=datetime.now()
    )

    tracker.log_user_bet(user_bet)

    # Later: Closing line comes in at Lakers -5.5
    closing_line = ClosingLine(
        game_id="game_789",
        spread_home=-5.5,
        spread_away=5.5,
        total=220.5,
        moneyline_home=-200,
        moneyline_away=170,
        closing_time=datetime.now(),
        bookmaker_source="pinnacle"
    )

    tracker.log_closing_line(closing_line)

    # Get CLV result
    clv_result = tracker.clv_results.get("bet_123")
    if clv_result:
        print("="*70)
        print("CLV RESULT")
        print("="*70)
        print(f"Bet: {clv_result.home_team} vs {clv_result.away_team}")
        print(f"Type: {clv_result.bet_type} {clv_result.bet_side}")
        print(f"User Line: {clv_result.user_line}")
        print(f"Closing Line: {clv_result.closing_line}")
        print(f"CLV: {clv_result.clv:+.1f} points")
        print(f"Rating: {clv_result.clv_rating}")
        print("="*70)

    # Get user stats
    user_stats = tracker.get_user_clv_stats("user_456")
    if user_stats:
        print("\nUSER CLV STATS")
        print("="*70)
        print(f"Total Bets: {user_stats.total_bets}")
        print(f"Average CLV: {user_stats.avg_clv:+.2f}")
        print(f"Positive CLV %: {user_stats.positive_clv_percentage:.1f}%")
        print(f"Sharp Rating: {user_stats.sharp_rating}")
        print(f"Expected ROI: {user_stats.expected_roi:+.2f}%")
        print("="*70)
