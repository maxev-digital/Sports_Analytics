"""
Bet Recommendation System with Variance-Adjusted Scoring

Provides BetOption class for representing betting opportunities and
recommendation engine for selecting best bets based on risk-adjusted returns.

Used across all betting strategies to generate multi-option recommendations.
"""

from typing import List, Dict, Literal, Optional
from dataclasses import dataclass
from strategies.kelly_sizing import (
    american_to_decimal,
    calculate_bet_amount,
    KELLY_FRACTIONS
)


# Variance factors by bet type
VARIANCE_FACTORS = {
    'moneyline': 1.2,       # Higher variance (win/lose)
    'spread': 1.0,          # Standard variance
    'total': 1.1,           # Medium variance
    'quarter_ml': 1.5,      # Very high variance (small sample)
    'quarter_spread': 1.0,  # Standard variance
    'quarter_total': 1.2,   # Higher variance
    'period_ml': 1.8,       # Extreme variance (NHL periods)
    'period_spread': 1.1,   # Medium-high variance
    'ot': 2.0,              # Extreme variance (OT is volatile)
}

# Risk profile variance multipliers
RISK_MULTIPLIERS = {
    'conservative': 1.5,    # Penalize variance heavily
    'balanced': 1.0,        # Standard variance penalty
    'aggressive': 0.7,      # Less variance penalty
}


@dataclass
class BetOption:
    """
    Represents a single betting opportunity with Kelly sizing and variance scoring

    Attributes:
        label: Human-readable bet description (e.g., "Lakers Q3 Win (ML)")
        odds_str: American odds (e.g., "+140", "-110")
        probability: Win probability (0-1 decimal)
        bet_type: Type of bet for variance calculation
        variance: Custom variance multiplier (overrides bet_type default)
        context: Additional context about the bet
        bookmaker: Primary bookmaker offering these odds (e.g., "fanduel")
        bookmaker_title: Display name of bookmaker (e.g., "FanDuel")
        alt_bookmakers: List of alternative bookmakers with similar odds
    """
    label: str
    odds_str: str
    probability: float
    bet_type: str = 'moneyline'
    variance: Optional[float] = None
    context: Optional[str] = None
    bookmaker: Optional[str] = None
    bookmaker_title: Optional[str] = None
    alt_bookmakers: Optional[List[Dict]] = None

    def __post_init__(self):
        """Calculate derived values after initialization"""
        # Use custom variance or lookup from bet_type
        if self.variance is None:
            self.variance = VARIANCE_FACTORS.get(self.bet_type, 1.0)

        # Calculate decimal odds
        self._decimal_odds = american_to_decimal(self.odds_str)

        # Calculate expected value
        self._ev = self.probability * (self._decimal_odds - 1) - (1 - self.probability)

    @property
    def decimal_odds(self) -> float:
        """Get decimal odds"""
        return self._decimal_odds

    @property
    def expected_value(self) -> float:
        """Get expected value (profit per dollar bet)"""
        return self._ev

    def kelly_size(
        self,
        bankroll: float,
        risk_profile: Literal['conservative', 'balanced', 'aggressive'] = 'balanced'
    ) -> Dict:
        """
        Calculate Kelly-sized bet amount

        Args:
            bankroll: Total bankroll in dollars
            risk_profile: Risk profile for sizing

        Returns:
            Dictionary with bet sizing details from kelly_sizing module
        """
        return calculate_bet_amount(
            self.probability,
            self.odds_str,
            bankroll,
            risk_profile
        )

    def variance_adjusted_score(
        self,
        risk_profile: Literal['conservative', 'balanced', 'aggressive'] = 'balanced'
    ) -> float:
        """
        Calculate risk-adjusted score for ranking bets

        Formula: score = EV / (variance * risk_multiplier)

        Higher scores are better (more EV per unit of risk)

        Args:
            risk_profile: Risk profile affects variance penalty

        Returns:
            Risk-adjusted score (higher is better)
        """
        risk_multiplier = RISK_MULTIPLIERS.get(risk_profile, 1.0)
        adjusted_variance = self.variance * risk_multiplier

        # Avoid division by zero
        if adjusted_variance == 0:
            adjusted_variance = 0.1

        # Score = EV / adjusted_variance
        # Only consider positive EV bets
        if self._ev <= 0:
            return -999.0  # Negative EV gets worst score

        return self._ev / adjusted_variance

    def to_dict(
        self,
        bankroll: Optional[float] = None,
        risk_profile: Literal['conservative', 'balanced', 'aggressive'] = 'balanced'
    ) -> Dict:
        """
        Convert to dictionary for API responses

        Args:
            bankroll: If provided, includes Kelly sizing
            risk_profile: Risk profile for sizing and scoring

        Returns:
            Dictionary representation
        """
        result = {
            'label': self.label,
            'odds': self.odds_str,
            'decimal_odds': round(self._decimal_odds, 3),
            'probability': round(self.probability, 3),
            'expected_value': round(self._ev, 3),
            'bet_type': self.bet_type,
            'variance': round(self.variance, 2),
            'score': round(self.variance_adjusted_score(risk_profile), 3),
        }

        # Add Kelly sizing if bankroll provided
        if bankroll is not None:
            kelly_data = self.kelly_size(bankroll, risk_profile)
            result.update({
                'kelly_size': kelly_data['bet_amount'],
                'kelly_pct': kelly_data['bet_pct'],
                'full_kelly_pct': kelly_data['kelly_pct'],
            })

        # Add context if available
        if self.context:
            result['context'] = self.context

        # Add bookmaker info if available
        if self.bookmaker:
            result['bookmaker'] = self.bookmaker
        if self.bookmaker_title:
            result['bookmaker_title'] = self.bookmaker_title
        if self.alt_bookmakers:
            result['alt_bookmakers'] = self.alt_bookmakers

        return result


def recommend_best_bets(
    options: List[BetOption],
    bankroll: Optional[float] = None,
    risk_profile: Literal['conservative', 'balanced', 'aggressive'] = 'balanced',
    top_n: int = 3,
    min_ev: float = 0.0
) -> List[Dict]:
    """
    Rank and filter bet options by variance-adjusted score

    Args:
        options: List of BetOption objects to evaluate
        bankroll: Total bankroll for Kelly sizing (optional)
        risk_profile: Risk profile for variance adjustment
        top_n: Maximum number of recommendations to return
        min_ev: Minimum expected value filter (default 0 = positive EV only)

    Returns:
        List of top N bet option dictionaries, sorted by score (best first)

    Example:
        options = [
            BetOption("Lakers Q3 ML", "+140", 0.553, 'quarter_ml'),
            BetOption("Lakers +4.5 Q3", "-110", 0.553, 'quarter_spread'),
            BetOption("Lakers Q3 Over 28.5", "+105", 0.553, 'quarter_total'),
        ]
        recommendations = recommend_best_bets(options, 10000, 'balanced', top_n=3)
    """
    # Filter by minimum EV
    valid_options = [opt for opt in options if opt.expected_value >= min_ev]

    # Calculate scores and sort
    scored_options = [
        (opt, opt.variance_adjusted_score(risk_profile))
        for opt in valid_options
    ]

    # Sort by score (highest first)
    scored_options.sort(key=lambda x: x[1], reverse=True)

    # Take top N
    top_options = scored_options[:top_n]

    # Convert to dictionaries
    recommendations = [
        {
            **opt.to_dict(bankroll, risk_profile),
            'rank': i + 1,
        }
        for i, (opt, score) in enumerate(top_options)
    ]

    return recommendations


def find_best_odds(
    bookmakers: List[Dict],
    team: str,
    bet_type: str,
    spread: Optional[float] = None,
    total: Optional[float] = None,
    outcome: Optional[str] = None
) -> Dict:
    """
    Find best odds across all bookmakers for a specific bet

    Args:
        bookmakers: List of bookmaker data from game tracker
        team: Team name to find odds for
        bet_type: 'spread', 'total', or 'moneyline'
        spread: For spread bets, the line (e.g., -4.5)
        total: For total bets, the line (e.g., 225.5)
        outcome: For totals, 'Over' or 'Under'

    Returns:
        Dictionary with:
            - best_odds: Best American odds string (e.g., "-110")
            - bookmaker: Bookmaker key (e.g., "fanduel")
            - bookmaker_title: Display name (e.g., "FanDuel")
            - alt_bookmakers: List of other books with similar odds (within 5 points)
    """
    best_price = None
    best_book = None
    best_book_title = None
    all_books = []

    for book in bookmakers:
        book_title = book.get('title', '')
        book_key = book_title.lower().replace(' ', '_')

        for market in book.get('markets', []):
            if bet_type == 'spread' and market['key'] == 'spreads':
                for outcome in market.get('outcomes', []):
                    if outcome['name'] == team and outcome.get('point') == spread:
                        price = outcome.get('price')
                        if price:
                            all_books.append({
                                'bookmaker': book_key,
                                'bookmaker_title': book_title,
                                'odds': price
                            })
                            if best_price is None or price > best_price:
                                best_price = price
                                best_book = book_key
                                best_book_title = book_title

            elif bet_type == 'total' and market['key'] == 'totals':
                for out in market.get('outcomes', []):
                    if out['name'] == outcome and out.get('point') == total:
                        price = out.get('price')
                        if price:
                            all_books.append({
                                'bookmaker': book_key,
                                'bookmaker_title': book_title,
                                'odds': price
                            })
                            if best_price is None or price > best_price:
                                best_price = price
                                best_book = book_key
                                best_book_title = book_title

            elif bet_type == 'moneyline' and market['key'] == 'h2h':
                for out in market.get('outcomes', []):
                    if out['name'] == team:
                        price = out.get('price')
                        if price:
                            all_books.append({
                                'bookmaker': book_key,
                                'bookmaker_title': book_title,
                                'odds': price
                            })
                            if best_price is None or price > best_price:
                                best_price = price
                                best_book = book_key
                                best_book_title = book_title

    # Convert to American odds string
    best_odds_str = f"+{int(best_price)}" if best_price > 0 else str(int(best_price)) if best_price else None

    # Find alternative books with similar odds (within 5 points)
    alt_books = []
    if best_price:
        for book_data in all_books:
            if book_data['bookmaker'] != best_book and abs(book_data['odds'] - best_price) <= 5:
                alt_books.append({
                    'bookmaker': book_data['bookmaker'],
                    'bookmaker_title': book_data['bookmaker_title'],
                    'odds': f"+{int(book_data['odds'])}" if book_data['odds'] > 0 else str(int(book_data['odds']))
                })

    return {
        'best_odds': best_odds_str,
        'bookmaker': best_book,
        'bookmaker_title': best_book_title,
        'alt_bookmakers': alt_books[:2]  # Return top 2 alternatives
    }


def validate_price_limits(
    option: BetOption,
    max_odds: Optional[str] = None,
    max_spread_line: Optional[str] = None
) -> Dict:
    """
    Validate bet option against price limits

    Args:
        option: BetOption to validate
        max_odds: Maximum acceptable odds (e.g., "+160", "-110")
        max_spread_line: Maximum spread line (e.g., "-115")

    Returns:
        Dictionary with:
            - valid: Whether bet passes price limits
            - reason: Reason if invalid
            - max_allowed: Maximum allowed odds
    """
    result = {
        'valid': True,
        'reason': None,
        'max_allowed': None,
    }

    # Check moneyline/total price limits
    if max_odds and option.bet_type in ['moneyline', 'quarter_ml', 'period_ml', 'total', 'quarter_total', 'ot']:
        max_decimal = american_to_decimal(max_odds)
        if option.decimal_odds > max_decimal:
            result['valid'] = False
            result['reason'] = f"Odds {option.odds_str} exceed limit {max_odds}"
            result['max_allowed'] = max_odds
            return result

    # Check spread price limits
    if max_spread_line and option.bet_type in ['spread', 'quarter_spread', 'period_spread']:
        max_spread_decimal = american_to_decimal(max_spread_line)
        if option.decimal_odds < max_spread_decimal:  # Worse than -115 (lower decimal)
            result['valid'] = False
            result['reason'] = f"Spread line {option.odds_str} worse than limit {max_spread_line}"
            result['max_allowed'] = max_spread_line
            return result

    return result


def create_quarter_reversal_options(
    reversal_team: str,
    quarter: str,
    probability: float,
    strategy_type: str,
    bookmakers: Optional[List[Dict]] = None
) -> List[BetOption]:
    """
    Generate standard bet options for NBA Quarter Reversal triggers

    Args:
        reversal_team: Team expected to reverse (e.g., "Lakers")
        quarter: Quarter to bet on (e.g., "Q3", "Q4", "OT")
        probability: Win probability for reversal
        strategy_type: "Q1-Q2_to_Q3", "Q2-Q3_to_Q4", or "Q3-Q4_to_OT"
        bookmakers: Optional list of bookmaker data to find best odds

    Returns:
        List of 3-5 BetOption objects with appropriate odds and bet types

    Based on NBA Quarter Reversal.md specification:
        Q3: ML +120-+150, Spread +4.5 -110, Total Over 28.5 +105
        Q4: ML +130-+160, Spread +4.5 -110, Total Over 27.5 +105
        OT: ML +250-+350, Spread +2.5 -110, Total Over 10.5 +105
    """
    options = []

    # Get best odds from bookmakers if available
    def get_best_odds_for_bet(team, bet_type, spread=None, total=None, outcome=None, fallback_odds="-110"):
        if bookmakers:
            odds_data = find_best_odds(bookmakers, team, bet_type, spread, total, outcome)
            if odds_data['best_odds']:
                return {
                    'odds': odds_data['best_odds'],
                    'bookmaker': odds_data['bookmaker'],
                    'bookmaker_title': odds_data['bookmaker_title'],
                    'alt_bookmakers': odds_data['alt_bookmakers']
                }
        return {
            'odds': fallback_odds,
            'bookmaker': None,
            'bookmaker_title': None,
            'alt_bookmakers': None
        }

    if strategy_type == 'Q1-Q2_to_Q3':
        # Q3 Reversal Options - try to find real odds
        ml_odds = get_best_odds_for_bet(reversal_team, 'moneyline', fallback_odds="+140")
        spread_odds = get_best_odds_for_bet(reversal_team, 'spread', spread=4.5, fallback_odds="-110")
        total_odds = get_best_odds_for_bet(reversal_team, 'total', total=28.5, outcome='Over', fallback_odds="+105")

        options = [
            BetOption(
                label=f"{reversal_team} Q3 Win (ML)",
                odds_str=ml_odds['odds'],
                probability=probability,
                bet_type='quarter_ml',
                context="Halftime adjustments favor opponent",
                bookmaker=ml_odds['bookmaker'],
                bookmaker_title=ml_odds['bookmaker_title'],
                alt_bookmakers=ml_odds['alt_bookmakers']
            ),
            BetOption(
                label=f"{reversal_team} +4.5 Q3",
                odds_str=spread_odds['odds'],
                probability=probability,
                bet_type='quarter_spread',
                context="Lower risk spread option",
                bookmaker=spread_odds['bookmaker'],
                bookmaker_title=spread_odds['bookmaker_title'],
                alt_bookmakers=spread_odds['alt_bookmakers']
            ),
            BetOption(
                label=f"{reversal_team} Q3 Over 28.5",
                odds_str=total_odds['odds'],
                probability=probability,
                bet_type='quarter_total',
                context="Opponent expected to score more in Q3",
                bookmaker=total_odds['bookmaker'],
                bookmaker_title=total_odds['bookmaker_title'],
                alt_bookmakers=total_odds['alt_bookmakers']
            ),
        ]

    elif strategy_type == 'Q2-Q3_to_Q4':
        # Q4 Reversal Options
        ml_odds = get_best_odds_for_bet(reversal_team, 'moneyline', fallback_odds="+150")
        spread_odds = get_best_odds_for_bet(reversal_team, 'spread', spread=4.5, fallback_odds="-110")
        total_odds = get_best_odds_for_bet(reversal_team, 'total', total=27.5, outcome='Over', fallback_odds="+105")

        options = [
            BetOption(
                label=f"{reversal_team} Q4 Win (ML)",
                odds_str=ml_odds['odds'],
                probability=probability,
                bet_type='quarter_ml',
                context="Star fatigue and garbage time factor",
                bookmaker=ml_odds['bookmaker'],
                bookmaker_title=ml_odds['bookmaker_title'],
                alt_bookmakers=ml_odds['alt_bookmakers']
            ),
            BetOption(
                label=f"{reversal_team} +4.5 Q4",
                odds_str=spread_odds['odds'],
                probability=probability,
                bet_type='quarter_spread',
                context="Lower risk spread option",
                bookmaker=spread_odds['bookmaker'],
                bookmaker_title=spread_odds['bookmaker_title'],
                alt_bookmakers=spread_odds['alt_bookmakers']
            ),
            BetOption(
                label=f"{reversal_team} Q4 Over 27.5",
                odds_str=total_odds['odds'],
                probability=probability,
                bet_type='quarter_total',
                context="Opponent expected to score more in Q4",
                bookmaker=total_odds['bookmaker'],
                bookmaker_title=total_odds['bookmaker_title'],
                alt_bookmakers=total_odds['alt_bookmakers']
            ),
        ]

    elif strategy_type == 'Q3-Q4_to_OT':
        # OT Reversal Options (HIGHEST ROI)
        ml_odds = get_best_odds_for_bet(reversal_team, 'moneyline', fallback_odds="+300")
        spread_odds = get_best_odds_for_bet(reversal_team, 'spread', spread=2.5, fallback_odds="-110")
        total_odds = get_best_odds_for_bet(reversal_team, 'total', total=10.5, outcome='Over', fallback_odds="+105")

        options = [
            BetOption(
                label=f"{reversal_team} OT Win (ML)",
                odds_str=ml_odds['odds'],
                probability=probability,
                bet_type='ot',
                context="Extreme fatigue after 48 minutes (60.7% reversal rate)",
                bookmaker=ml_odds['bookmaker'],
                bookmaker_title=ml_odds['bookmaker_title'],
                alt_bookmakers=ml_odds['alt_bookmakers']
            ),
            BetOption(
                label=f"{reversal_team} +2.5 OT",
                odds_str=spread_odds['odds'],
                probability=probability,
                bet_type='quarter_spread',
                context="Lower risk OT spread",
                bookmaker=spread_odds['bookmaker'],
                bookmaker_title=spread_odds['bookmaker_title'],
                alt_bookmakers=spread_odds['alt_bookmakers']
            ),
            BetOption(
                label=f"{reversal_team} OT Over 10.5",
                odds_str=total_odds['odds'],
                probability=probability,
                bet_type='quarter_total',
                context="High-scoring OT expected",
                bookmaker=total_odds['bookmaker'],
                bookmaker_title=total_odds['bookmaker_title'],
                alt_bookmakers=total_odds['alt_bookmakers']
            ),
        ]

    return options


if __name__ == "__main__":
    # Test the module
    print("=" * 80)
    print("BET RECOMMENDATION SYSTEM - TEST")
    print("=" * 80)

    # Create sample bet options
    print("\n1. CREATE BET OPTIONS:")
    print("-" * 80)

    options = create_quarter_reversal_options(
        reversal_team="Lakers",
        quarter="Q3",
        probability=0.553,
        strategy_type="Q1-Q2_to_Q3"
    )

    for opt in options:
        print(f"\n{opt.label}")
        print(f"  Odds: {opt.odds_str} (decimal: {opt.decimal_odds:.2f})")
        print(f"  EV: {opt.expected_value:.3f}")
        print(f"  Variance: {opt.variance:.2f}")
        print(f"  Score (balanced): {opt.variance_adjusted_score('balanced'):.3f}")

    # Test recommendations
    print("\n2. RANKED RECOMMENDATIONS:")
    print("-" * 80)

    bankroll = 10000
    recommendations = recommend_best_bets(
        options,
        bankroll=bankroll,
        risk_profile='balanced',
        top_n=3
    )

    print(f"\nBankroll: ${bankroll:,} | Risk Profile: Balanced\n")
    print(f"{'Rank':<6} {'Bet':<30} {'Odds':<8} {'EV':<8} {'Kelly $':<10} {'Score':<8}")
    print("-" * 80)

    for rec in recommendations:
        print(f"{rec['rank']:<6} {rec['label']:<30} {rec['odds']:<8} {rec['expected_value']:<8.3f} ${rec['kelly_size']:<9.2f} {rec['score']:<8.3f}")

    # Test price limits
    print("\n3. PRICE LIMIT VALIDATION:")
    print("-" * 80)

    test_option = BetOption("Test Bet", "+200", 0.55, 'quarter_ml')
    validation = validate_price_limits(test_option, max_odds="+160")
    print(f"Bet: {test_option.label} @ {test_option.odds_str}")
    print(f"Max Allowed: +160")
    print(f"Valid: {validation['valid']}")
    if not validation['valid']:
        print(f"Reason: {validation['reason']}")

    print("\n" + "=" * 80)
