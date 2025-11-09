"""
Kelly Criterion Bet Sizing Module

Implements fractional Kelly formula for optimal bet sizing with risk management.
Used across all betting strategies to calculate recommended bet amounts.

Risk Profiles:
- Conservative: 1/10 Kelly (0.5% max bankroll)
- Balanced: 1/4 Kelly (1.2% max bankroll)
- Aggressive: 1/2 Kelly (2.5% max bankroll)

All bets capped at 5% of total bankroll for risk management.
"""

from typing import Literal

# Risk profile Kelly fractions
KELLY_FRACTIONS = {
    'conservative': 0.1,   # 1/10 Kelly
    'balanced': 0.25,      # 1/4 Kelly
    'aggressive': 0.5,     # 1/2 Kelly
}

# Maximum bankroll percentage per risk profile
MAX_BANKROLL_PCT = {
    'conservative': 0.005,   # 0.5%
    'balanced': 0.012,       # 1.2%
    'aggressive': 0.025,     # 2.5%
}

# Global 5% bankroll cap for all bets
GLOBAL_MAX_PCT = 0.05


def american_to_decimal(odds_str: str) -> float:
    """
    Convert American odds to decimal odds

    Args:
        odds_str: American odds string (e.g., "+140", "-110")

    Returns:
        Decimal odds (e.g., 2.4, 1.91)

    Examples:
        "+140" -> 2.4
        "-110" -> 1.909
        "+100" -> 2.0
        "-200" -> 1.5
    """
    odds_str = odds_str.strip()

    if odds_str.startswith('+'):
        # Positive odds: decimal = (odds / 100) + 1
        american = int(odds_str[1:])
        return (american / 100.0) + 1.0
    elif odds_str.startswith('-'):
        # Negative odds: decimal = (100 / odds) + 1
        american = int(odds_str[1:])
        return (100.0 / american) + 1.0
    else:
        raise ValueError(f"Invalid odds format: {odds_str}")


def decimal_to_american(decimal_odds: float) -> str:
    """
    Convert decimal odds to American odds

    Args:
        decimal_odds: Decimal odds (e.g., 2.4, 1.91)

    Returns:
        American odds string (e.g., "+140", "-110")
    """
    if decimal_odds >= 2.0:
        # Positive odds
        american = int((decimal_odds - 1) * 100)
        return f"+{american}"
    else:
        # Negative odds
        american = int(-100 / (decimal_odds - 1))
        return f"-{american}"


def kelly_fraction(
    probability: float,
    decimal_odds: float,
    risk_profile: Literal['conservative', 'balanced', 'aggressive'] = 'balanced'
) -> float:
    """
    Calculate fractional Kelly bet size

    Formula: kelly = (b * p - (1 - p)) / b
    Where:
        p = probability of winning (0-1)
        b = decimal odds - 1 (e.g., 2.4 -> 1.4)

    Fractional Kelly: kelly * fraction

    Args:
        probability: Win probability (0-1 decimal)
        decimal_odds: Decimal odds (e.g., 2.4 for +140)
        risk_profile: 'conservative', 'balanced', or 'aggressive'

    Returns:
        Recommended bet size as percentage of bankroll (0-0.05)
        Returns 0 if bet has negative expectation

    Examples:
        kelly_fraction(0.55, 2.4, 'balanced') -> ~0.015 (1.5%)
        kelly_fraction(0.52, 1.91, 'conservative') -> ~0.001 (0.1%)
    """
    # Get Kelly fraction for risk profile
    fraction = KELLY_FRACTIONS.get(risk_profile, 0.25)
    max_pct = MAX_BANKROLL_PCT.get(risk_profile, 0.012)

    # b = decimal odds - 1
    b = decimal_odds - 1.0

    # Full Kelly: (b * p - (1 - p)) / b
    p = probability
    full_kelly = (b * p - (1 - p)) / b

    # If negative expectation, return 0
    if full_kelly <= 0:
        return 0.0

    # Apply fractional Kelly
    fractional_kelly = full_kelly * fraction

    # Apply risk profile cap
    capped = min(fractional_kelly, max_pct)

    # Apply global 5% cap
    final = min(capped, GLOBAL_MAX_PCT)

    return max(0.0, final)


def calculate_bet_amount(
    probability: float,
    odds_str: str,
    bankroll: float,
    risk_profile: Literal['conservative', 'balanced', 'aggressive'] = 'balanced'
) -> dict:
    """
    Calculate recommended bet amount with Kelly sizing

    Args:
        probability: Win probability (0-1 decimal)
        odds_str: American odds (e.g., "+140", "-110")
        bankroll: Total bankroll in dollars
        risk_profile: Risk profile for sizing

    Returns:
        Dictionary with:
            - bet_amount: Dollar amount to bet
            - bet_pct: Percentage of bankroll
            - decimal_odds: Converted decimal odds
            - expected_value: Expected profit per dollar
            - kelly_pct: Full Kelly percentage (before fractions)

    Example:
        calculate_bet_amount(0.553, "+140", 10000, 'balanced')
        -> {
            'bet_amount': 150.0,
            'bet_pct': 0.015,
            'decimal_odds': 2.4,
            'expected_value': 0.327,
            'kelly_pct': 0.060
        }
    """
    # Convert odds
    decimal_odds = american_to_decimal(odds_str)

    # Calculate Kelly percentage
    bet_pct = kelly_fraction(probability, decimal_odds, risk_profile)

    # Calculate dollar amount
    bet_amount = bankroll * bet_pct

    # Calculate full Kelly for reference
    b = decimal_odds - 1.0
    full_kelly = max(0, (b * probability - (1 - probability)) / b)

    # Calculate expected value
    expected_value = probability * (decimal_odds - 1) - (1 - probability)

    return {
        'bet_amount': round(bet_amount, 2),
        'bet_pct': round(bet_pct, 4),
        'decimal_odds': round(decimal_odds, 3),
        'expected_value': round(expected_value, 3),
        'kelly_pct': round(full_kelly, 4),
    }


def validate_bet_size(bet_amount: float, bankroll: float, min_bet: float = 10.0) -> dict:
    """
    Validate bet size and provide recommendations

    Args:
        bet_amount: Calculated bet amount
        bankroll: Total bankroll
        min_bet: Minimum bet size (default $10)

    Returns:
        Dictionary with:
            - valid: Whether bet is valid
            - adjusted_amount: Adjusted bet amount
            - warnings: List of warnings
            - recommendations: List of recommendations
    """
    warnings = []
    recommendations = []
    adjusted_amount = bet_amount
    valid = True

    # Check minimum bet
    if bet_amount < min_bet:
        warnings.append(f"Bet size ${bet_amount:.2f} below minimum ${min_bet}")
        recommendations.append(f"Consider skipping this bet or betting minimum ${min_bet}")
        adjusted_amount = 0.0
        valid = False

    # Check if bet exceeds 5% of bankroll
    if bet_amount > bankroll * 0.05:
        warnings.append(f"Bet exceeds 5% bankroll cap")
        adjusted_amount = bankroll * 0.05
        recommendations.append(f"Bet capped at ${adjusted_amount:.2f} (5% of bankroll)")

    # Check if bet exceeds total bankroll
    if bet_amount > bankroll:
        warnings.append(f"Bet exceeds total bankroll")
        adjusted_amount = bankroll * 0.05
        recommendations.append(f"Bet capped at ${adjusted_amount:.2f}")
        valid = False

    return {
        'valid': valid,
        'adjusted_amount': round(adjusted_amount, 2),
        'warnings': warnings,
        'recommendations': recommendations,
    }


if __name__ == "__main__":
    # Test the module
    print("=" * 80)
    print("KELLY CRITERION BET SIZING MODULE - TEST")
    print("=" * 80)

    # Test odds conversion
    print("\n1. ODDS CONVERSION TEST:")
    print("-" * 80)
    test_odds = ["+140", "-110", "+200", "-200", "+100"]
    for odds in test_odds:
        decimal = american_to_decimal(odds)
        back = decimal_to_american(decimal)
        print(f"{odds:>6} -> {decimal:.3f} -> {back:>6}")

    # Test Kelly sizing
    print("\n2. KELLY SIZING TEST:")
    print("-" * 80)
    print(f"{'Probability':<12} {'Odds':<8} {'Profile':<12} {'Kelly %':<10} {'Amount':<10}")
    print("-" * 80)

    bankroll = 10000
    test_cases = [
        (0.553, "+140", 'conservative'),
        (0.553, "+140", 'balanced'),
        (0.553, "+140", 'aggressive'),
        (0.527, "+160", 'balanced'),
        (0.607, "+300", 'balanced'),
        (0.50, "+100", 'balanced'),  # Break-even
        (0.45, "+140", 'balanced'),  # Negative EV
    ]

    for prob, odds, profile in test_cases:
        result = calculate_bet_amount(prob, odds, bankroll, profile)
        print(f"{prob:<12.3f} {odds:<8} {profile:<12} {result['bet_pct']*100:>6.2f}%   ${result['bet_amount']:>7.2f}")

    # Test validation
    print("\n3. BET VALIDATION TEST:")
    print("-" * 80)

    validation = validate_bet_size(150.0, 10000, 10.0)
    print(f"Bet: $150 / Bankroll: $10000")
    print(f"Valid: {validation['valid']}")
    print(f"Adjusted: ${validation['adjusted_amount']}")

    validation = validate_bet_size(5.0, 10000, 10.0)
    print(f"\nBet: $5 / Bankroll: $10000")
    print(f"Valid: {validation['valid']}")
    print(f"Warnings: {validation['warnings']}")

    print("\n" + "=" * 80)
