"""Models for user bankroll tracking"""
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class BookmakerBankroll(BaseModel):
    """Individual bookmaker bankroll"""
    bookmaker: str
    amount: float = Field(ge=0, description="Amount in this bookmaker account")


class BankrollData(BaseModel):
    """User's complete bankroll data"""
    user_id: str
    total_bankroll: float = Field(ge=0, description="Total bankroll across all books")
    bookmaker_bankrolls: List[BookmakerBankroll] = Field(default_factory=list)
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class UpdateBankrollRequest(BaseModel):
    """Request to update bankroll"""
    total_bankroll: float = Field(ge=0)
    bookmaker_bankrolls: List[BookmakerBankroll] = Field(default_factory=list)


def calculate_kelly_bet_size(
    bankroll: float,
    edge: float,
    odds: float,
    kelly_fraction: float = 0.25
) -> float:
    """
    Calculate optimal bet size using Kelly Criterion (fractional Kelly method)

    Args:
        bankroll: Total bankroll in dollars
        edge: Edge as decimal (e.g., 0.05 for 5% edge). This is the difference between
              your true win probability and the implied probability from odds.
              Example: If odds are -110 (52.38% implied) and you think true prob is 55%,
              your edge is 0.0262 (2.62%)
        odds: American odds (e.g., -110, +150, -200)
        kelly_fraction: Fraction of full Kelly to use (default 0.25 for 1/4 Kelly).
                       Most sharp bettors use 0.25-0.5 to reduce variance.

    Returns:
        Recommended bet size in dollars (capped at 5% of bankroll for safety)

    Formula: Kelly % = (b × p - q) / b
    where b = decimal odds - 1, p = true win probability, q = 1 - p
    """
    # Convert American odds to decimal
    if odds > 0:
        decimal_odds = (odds / 100) + 1
    else:
        decimal_odds = (100 / abs(odds)) + 1

    # Calculate true win probability from implied probability + edge
    # Edge is the difference: true_prob - implied_prob
    # Example: -110 odds = 52.38% implied, if true prob = 55%, edge = 2.62%
    implied_prob = 1 / decimal_odds
    true_prob = implied_prob + edge  # edge already as decimal (e.g., 0.0262)

    # Kelly formula: (bp - q) / b
    # where b = decimal odds - 1, p = win probability, q = lose probability
    b = decimal_odds - 1
    p = true_prob
    q = 1 - p

    kelly_percentage = (b * p - q) / b

    # Apply Kelly fraction for safety
    kelly_percentage = kelly_percentage * kelly_fraction

    # Ensure non-negative and cap at 5% of bankroll
    kelly_percentage = max(0, min(kelly_percentage, 0.05))

    return bankroll * kelly_percentage
