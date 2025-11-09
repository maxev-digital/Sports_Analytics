"""
Low-Hold Opportunities Strategy

"Hold" or "Vig" is the bookmaker's edge built into the odds.

Example:
- Team A: -110 (52.4% implied probability)
- Team B: -110 (52.4% implied probability)
- Total: 104.8% (4.8% hold/vig)

The "hold" is the 4.8% edge the bookmaker has over bettors.

Why Low Hold Matters:
1. Lower hold = Better value for bettors
2. Sharp books (Pinnacle, Circa) have low holds (2-3%)
3. Square books (DraftKings, FanDuel) have high holds (5-8%)
4. Low-hold games are best for:
   - Arbitrage opportunities
   - Middle opportunities
   - General betting (less bookmaker edge)

Strategy:
- Find games with <3% hold (excellent)
- Find games with 3-4% hold (good)
- Avoid games with >6% hold (bad value)

Historical Data:
- Average NFL hold: 4.5%
- Average NBA hold: 4.3%
- Average NHL hold: 4.6%
- Pinnacle average: 2.1%
- DraftKings average: 5.2%

Sharp Betting Edge:
- Betting only <3% hold games improves expected ROI by 1-2%
- Combined with other edges = significant advantage
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class HoldCategory(Enum):
    """Categories of hold percentage"""
    EXCELLENT = "EXCELLENT"  # <2%
    GOOD = "GOOD"  # 2-3%
    FAIR = "FAIR"  # 3-4%
    AVERAGE = "AVERAGE"  # 4-5%
    POOR = "POOR"  # 5-6%
    TERRIBLE = "TERRIBLE"  # >6%


class MarketType(Enum):
    """Types of betting markets"""
    SPREAD = "spread"
    TOTAL = "total"
    MONEYLINE = "moneyline"


@dataclass
class LowHoldOpportunity:
    """Represents a low-hold betting opportunity"""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    commence_time: datetime

    # Market information
    market_type: MarketType
    bookmaker: str

    # Odds information
    home_odds: int  # American odds
    away_odds: int
    home_line: Optional[float] = None  # Spread/total line
    away_line: Optional[float] = None

    # Hold calculation
    hold_percentage: float = 0.0
    hold_category: HoldCategory = HoldCategory.AVERAGE
    implied_probability_total: float = 0.0

    # Comparison
    market_average_hold: float = 0.0
    hold_difference: float = 0.0  # vs market average
    percentile_rank: int = 0  # 1-100 (100 = best)

    # Value metrics
    estimated_true_odds: Optional[Dict[str, int]] = None
    value_edge: float = 0.0  # Expected value boost from low hold
    confidence: float = 0.0
    confidence_level: str = "MEDIUM"

    # Reasoning
    key_factors: List[str] = field(default_factory=list)
    reasoning: str = ""
    recommendation: str = ""
    why_low_hold: str = ""


class LowHoldStrategy:
    """
    Identifies betting opportunities with low bookmaker hold (vig)

    Lower hold = better value for bettors

    Detects:
    1. Games with exceptionally low hold (<2%)
    2. Games with good hold (2-3%)
    3. Bookmaker-specific low-hold opportunities
    4. Market inefficiencies
    """

    # Average holds by sport (from historical data)
    AVERAGE_HOLDS = {
        'basketball_nba': 0.045,
        'americanfootball_nfl': 0.045,
        'icehockey_nhl': 0.046,
        'baseball_mlb': 0.050,
        'basketball_ncaab': 0.048,
        'americanfootball_ncaaf': 0.047
    }

    # Bookmaker typical holds
    BOOKMAKER_HOLDS = {
        'pinnacle': 0.021,  # Sharpest book
        'circa': 0.028,
        'bookmaker': 0.032,
        'betonline': 0.038,
        'betmgm': 0.045,
        'draftkings': 0.052,
        'fanduel': 0.051,
        'caesars': 0.053,
        'williamhill_us': 0.048
    }

    def __init__(self, max_hold_threshold: float = 0.035):
        """
        Initialize Low Hold Strategy

        Args:
            max_hold_threshold: Maximum hold to report (default 3.5%)
        """
        self.max_hold_threshold = max_hold_threshold

    def american_to_implied_probability(self, american_odds: int) -> float:
        """
        Convert American odds to implied probability

        Args:
            american_odds: American odds (e.g., -110, +150)

        Returns:
            Implied probability (0-1)
        """
        if american_odds < 0:
            # Favorite
            return abs(american_odds) / (abs(american_odds) + 100)
        else:
            # Underdog
            return 100 / (american_odds + 100)

    def calculate_hold(self, odds_a: int, odds_b: int) -> float:
        """
        Calculate the hold (vig) from two-sided odds

        Args:
            odds_a: American odds for side A
            odds_b: American odds for side B

        Returns:
            Hold percentage (e.g., 0.048 = 4.8%)
        """
        prob_a = self.american_to_implied_probability(odds_a)
        prob_b = self.american_to_implied_probability(odds_b)

        total_probability = prob_a + prob_b
        hold = total_probability - 1.0

        return max(0.0, hold)  # Ensure non-negative

    def categorize_hold(self, hold: float) -> HoldCategory:
        """Categorize hold percentage"""
        if hold < 0.02:
            return HoldCategory.EXCELLENT
        elif hold < 0.03:
            return HoldCategory.GOOD
        elif hold < 0.04:
            return HoldCategory.FAIR
        elif hold < 0.05:
            return HoldCategory.AVERAGE
        elif hold < 0.06:
            return HoldCategory.POOR
        else:
            return HoldCategory.TERRIBLE

    def calculate_percentile_rank(
        self,
        hold: float,
        all_holds: List[float]
    ) -> int:
        """
        Calculate percentile rank (lower hold = higher rank)

        Args:
            hold: The hold to rank
            all_holds: List of all holds in the market

        Returns:
            Percentile rank (1-100, 100 = best/lowest hold)
        """
        if not all_holds:
            return 50

        # Count how many holds are worse (higher)
        worse_count = sum(1 for h in all_holds if h > hold)
        total_count = len(all_holds)

        percentile = int((worse_count / total_count) * 100)
        return percentile

    def estimate_true_odds(
        self,
        odds_a: int,
        odds_b: int,
        hold: float
    ) -> Dict[str, int]:
        """
        Estimate "true" odds by removing the hold

        Args:
            odds_a: American odds for side A
            odds_b: American odds for side B
            hold: Calculated hold

        Returns:
            Dictionary with estimated true odds
        """
        prob_a = self.american_to_implied_probability(odds_a)
        prob_b = self.american_to_implied_probability(odds_b)

        # Remove hold proportionally
        total = prob_a + prob_b
        true_prob_a = prob_a / total
        true_prob_b = prob_b / total

        # Convert back to American odds
        if true_prob_a >= 0.5:
            true_odds_a = int(-100 * true_prob_a / (1 - true_prob_a))
        else:
            true_odds_a = int(100 * (1 - true_prob_a) / true_prob_a)

        if true_prob_b >= 0.5:
            true_odds_b = int(-100 * true_prob_b / (1 - true_prob_b))
        else:
            true_odds_b = int(100 * (1 - true_prob_b) / true_prob_b)

        return {
            'side_a': true_odds_a,
            'side_b': true_odds_b
        }

    def analyze_market(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        market_type: MarketType,
        commence_time: datetime,
        bookmakers_odds: List[Dict]
    ) -> List[LowHoldOpportunity]:
        """
        Analyze all bookmakers for a specific market to find low-hold opportunities

        Args:
            game_id: Unique game identifier
            sport: Sport key
            home_team: Home team name
            away_team: Away team name
            market_type: Type of market (spread, total, moneyline)
            commence_time: Game start time
            bookmakers_odds: List of dicts with bookmaker, home_odds, away_odds, etc.

        Returns:
            List of LowHoldOpportunity objects
        """
        opportunities = []
        all_holds = []

        # Calculate hold for each bookmaker
        for book_data in bookmakers_odds:
            bookmaker = book_data.get('bookmaker')
            home_odds = book_data.get('home_odds')
            away_odds = book_data.get('away_odds')

            if not all([bookmaker, home_odds, away_odds]):
                continue

            hold = self.calculate_hold(home_odds, away_odds)
            all_holds.append(hold)

            # Only report if below threshold
            if hold <= self.max_hold_threshold:
                # Calculate metrics
                hold_category = self.categorize_hold(hold)
                implied_prob_total = (
                    self.american_to_implied_probability(home_odds) +
                    self.american_to_implied_probability(away_odds)
                )

                # Get market average
                market_avg_hold = self.AVERAGE_HOLDS.get(sport, 0.045)
                hold_difference = market_avg_hold - hold

                # Estimate true odds
                true_odds = self.estimate_true_odds(home_odds, away_odds, hold)

                # Value edge (how much better than average)
                value_edge = hold_difference

                # Confidence scoring
                confidence, confidence_level = self._calculate_confidence(
                    hold, hold_category, bookmaker, market_type
                )

                # Build recommendation
                recommendation = self._build_recommendation(
                    home_team, away_team, bookmaker, hold, hold_category,
                    market_type, home_odds, away_odds
                )

                # Key factors
                key_factors = self._build_key_factors(
                    bookmaker, hold, market_avg_hold, hold_category,
                    home_odds, away_odds
                )

                # Reasoning
                reasoning = self._build_reasoning(
                    bookmaker, hold, hold_category, value_edge
                )

                # Why low hold
                why_low_hold = self._explain_why_low_hold(
                    bookmaker, hold, market_type
                )

                opportunities.append(LowHoldOpportunity(
                    game_id=game_id,
                    sport=sport,
                    home_team=home_team,
                    away_team=away_team,
                    commence_time=commence_time,
                    market_type=market_type,
                    bookmaker=bookmaker,
                    home_odds=home_odds,
                    away_odds=away_odds,
                    home_line=book_data.get('home_line'),
                    away_line=book_data.get('away_line'),
                    hold_percentage=hold,
                    hold_category=hold_category,
                    implied_probability_total=implied_prob_total,
                    market_average_hold=market_avg_hold,
                    hold_difference=hold_difference,
                    percentile_rank=0,  # Will calculate below
                    estimated_true_odds=true_odds,
                    value_edge=value_edge,
                    confidence=confidence,
                    confidence_level=confidence_level,
                    key_factors=key_factors,
                    reasoning=reasoning,
                    recommendation=recommendation,
                    why_low_hold=why_low_hold
                ))

        # Calculate percentile ranks
        for opp in opportunities:
            opp.percentile_rank = self.calculate_percentile_rank(
                opp.hold_percentage, all_holds
            )

        # Sort by hold (lowest first)
        opportunities.sort(key=lambda x: x.hold_percentage)

        return opportunities

    def _calculate_confidence(
        self,
        hold: float,
        hold_category: HoldCategory,
        bookmaker: str,
        market_type: MarketType
    ) -> tuple[float, str]:
        """Calculate confidence score"""
        confidence = 0.50  # Base

        # Hold-based confidence
        if hold_category == HoldCategory.EXCELLENT:
            confidence += 0.35
        elif hold_category == HoldCategory.GOOD:
            confidence += 0.25
        elif hold_category == HoldCategory.FAIR:
            confidence += 0.15

        # Bookmaker-based confidence
        sharp_books = ['pinnacle', 'circa', 'bookmaker']
        if bookmaker.lower() in sharp_books:
            confidence += 0.10  # Sharp books naturally have low hold

        # Market type
        if market_type == MarketType.SPREAD:
            confidence += 0.05  # Spreads are most efficient

        confidence = min(0.95, confidence)

        if confidence >= 0.80:
            level = 'HIGH'
        elif confidence >= 0.65:
            level = 'MEDIUM'
        else:
            level = 'LOW'

        return confidence, level

    def _build_recommendation(
        self,
        home_team: str,
        away_team: str,
        bookmaker: str,
        hold: float,
        hold_category: HoldCategory,
        market_type: MarketType,
        home_odds: int,
        away_odds: int
    ) -> str:
        """Build betting recommendation"""
        if hold_category == HoldCategory.EXCELLENT:
            action = "EXCELLENT VALUE"
        elif hold_category == HoldCategory.GOOD:
            action = "GOOD VALUE"
        else:
            action = "FAIR VALUE"

        return (
            f"{action} - Bet at {bookmaker} ({hold*100:.1f}% hold). "
            f"Best market for this game."
        )

    def _build_key_factors(
        self,
        bookmaker: str,
        hold: float,
        market_avg_hold: float,
        hold_category: HoldCategory,
        home_odds: int,
        away_odds: int
    ) -> List[str]:
        """Build list of key factors"""
        factors = [
            f"{bookmaker} hold: {hold*100:.1f}% ({hold_category.value})",
            f"Market average: {market_avg_hold*100:.1f}%",
            f"Savings vs average: {(market_avg_hold - hold)*100:.1f}%",
            f"Odds: {home_odds:+d} / {away_odds:+d}"
        ]

        if hold < 0.025:
            factors.append("Among the best holds available!")

        return factors

    def _build_reasoning(
        self,
        bookmaker: str,
        hold: float,
        hold_category: HoldCategory,
        value_edge: float
    ) -> str:
        """Build reasoning text"""
        return (
            f"{bookmaker} is offering {hold*100:.1f}% hold on this market, "
            f"which is {hold_category.value.lower()} compared to industry standards. "
            f"This provides {value_edge*100:.1f}% better value than the average book. "
            f"Lower hold means less bookmaker edge and more potential profit for you."
        )

    def _explain_why_low_hold(
        self,
        bookmaker: str,
        hold: float,
        market_type: MarketType
    ) -> str:
        """Explain why this hold is low"""
        sharp_books = ['pinnacle', 'circa', 'bookmaker']

        if bookmaker.lower() in sharp_books:
            return (
                f"{bookmaker} is a sharp book that targets professional bettors "
                f"with low holds and high limits. Their {hold*100:.1f}% hold is "
                f"typical for sharp books and offers excellent value."
            )
        else:
            return (
                f"{bookmaker} is offering an unusually low {hold*100:.1f}% hold "
                f"on this {market_type.value} market. This could indicate market "
                f"inefficiency or promotional pricing. Take advantage while available."
            )


# Example usage and testing
if __name__ == "__main__":
    from datetime import datetime, timedelta

    strategy = LowHoldStrategy(max_hold_threshold=0.04)

    # Test scenario: NBA game with multiple bookmakers
    bookmakers_spread = [
        {'bookmaker': 'pinnacle', 'home_odds': -108, 'away_odds': -102, 'home_line': -5.5, 'away_line': 5.5},
        {'bookmaker': 'draftkings', 'home_odds': -110, 'away_odds': -110, 'home_line': -5.5, 'away_line': 5.5},
        {'bookmaker': 'fanduel', 'home_odds': -112, 'away_odds': -108, 'home_line': -5.5, 'away_line': 5.5},
        {'bookmaker': 'betmgm', 'home_odds': -115, 'away_odds': -105, 'home_line': -5.5, 'away_line': 5.5},
    ]

    print("=" * 80)
    print("LOW-HOLD STRATEGY - TEST RESULTS")
    print("=" * 80)

    opportunities = strategy.analyze_market(
        game_id='nba_001',
        sport='basketball_nba',
        home_team='Los Angeles Lakers',
        away_team='Boston Celtics',
        market_type=MarketType.SPREAD,
        commence_time=datetime.now() + timedelta(days=1),
        bookmakers_odds=bookmakers_spread
    )

    print(f"\nFound {len(opportunities)} low-hold opportunities:\n")

    for i, opp in enumerate(opportunities, 1):
        print(f"{'='*80}")
        print(f"Opportunity #{i}: {opp.bookmaker}")
        print(f"{'='*80}")
        print(f"Hold: {opp.hold_percentage*100:.2f}% ({opp.hold_category.value})")
        print(f"Market Average: {opp.market_average_hold*100:.2f}%")
        print(f"Savings: {opp.hold_difference*100:.2f}%")
        print(f"Percentile Rank: {opp.percentile_rank}th percentile")
        print(f"\nOdds: {opp.home_team} {opp.home_odds:+d} / {opp.away_team} {opp.away_odds:+d}")
        print(f"Line: {opp.home_line:+.1f}")
        print(f"\nRecommendation: {opp.recommendation}")
        print(f"Confidence: {opp.confidence_level} ({opp.confidence*100:.0f}%)")
        print(f"\nReasoning: {opp.reasoning}")
        print(f"\nWhy Low Hold: {opp.why_low_hold}")
        print(f"\nKey Factors:")
        for factor in opp.key_factors:
            print(f"  • {factor}")
        print()

    print(f"{'='*80}")
    print("Strategy test complete!")
