"""User Bet Tracking Model"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class UserBet(BaseModel):
    """Model for tracking user bets"""
    id: str
    user_id: str

    # Game Info
    game_id: str
    sport: str
    home_team: str
    away_team: str
    commence_time: str

    # Bet Details
    bet_type: Literal['spread', 'total', 'moneyline', 'prop']
    bet_side: str  # "OVER", "UNDER", "Lakers", "Cowboys +3.5", etc.
    stake: Optional[float] = None  # Amount wagered (None if pending)
    odds: float  # American odds (-110, +150, etc.)
    bookmaker: str  # "DraftKings", "FanDuel", etc.

    # System Data
    alert_id: Optional[str] = None  # Link to original alert if from system
    confidence: Optional[Literal['HIGH', 'MEDIUM', 'LOW']] = None
    edge_percent: Optional[float] = None
    strategy: Optional[str] = None  # "RLM", "Fade Public", etc.

    # Tracking
    clicked_at: str  # ISO timestamp when deep link was clicked
    logged_at: Optional[str] = None  # When user entered stake
    status: Literal['pending', 'active', 'won', 'lost', 'push', 'cancelled'] = 'pending'

    # Settlement
    result: Optional[Literal['win', 'loss', 'push']] = None
    payout: Optional[float] = None  # Amount returned if won
    profit_loss: Optional[float] = None  # Net profit or loss
    settled_at: Optional[str] = None  # When bet was graded


class CreateBetRequest(BaseModel):
    """Request model for creating a new bet via click tracking"""
    user_id: str
    game_id: str
    sport: str
    home_team: str
    away_team: str
    commence_time: str
    bet_type: Literal['spread', 'total', 'moneyline', 'prop']
    bet_side: str
    odds: float
    bookmaker: str
    alert_id: Optional[str] = None
    confidence: Optional[Literal['HIGH', 'MEDIUM', 'LOW']] = None
    edge_percent: Optional[float] = None
    strategy: Optional[str] = None


class ManualBetRequest(BaseModel):
    """Request model for manually adding a complete bet entry"""
    user_id: str
    sport: str
    home_team: str
    away_team: str
    commence_time: str
    bet_type: Literal['spread', 'total', 'moneyline', 'prop']
    bet_side: str
    odds: float
    stake: float = Field(gt=0, description="Stake amount must be greater than 0")
    bookmaker: str
    confidence: Optional[Literal['HIGH', 'MEDIUM', 'LOW']] = None
    edge_percent: Optional[float] = None
    notes: Optional[str] = None


class AddStakeRequest(BaseModel):
    """Request model for adding stake to a pending bet"""
    stake: float = Field(gt=0, description="Stake amount must be greater than 0")


class SettleBetRequest(BaseModel):
    """Request model for settling a bet"""
    result: Literal['win', 'loss', 'push']
    actual_score: Optional[dict] = None  # Optional score details for verification


def calculate_payout(stake: float, odds: float) -> float:
    """
    Calculate payout from American odds

    Args:
        stake: Amount wagered
        odds: American odds (e.g., -110, +150)

    Returns:
        Total payout including stake
    """
    if odds > 0:
        # Positive odds: profit = (stake * odds) / 100
        profit = (stake * odds) / 100
    else:
        # Negative odds: profit = (stake * 100) / abs(odds)
        profit = (stake * 100) / abs(odds)

    return stake + profit


def calculate_profit_loss(stake: float, odds: float, result: str) -> tuple[float, float]:
    """
    Calculate profit/loss and payout for a settled bet

    Args:
        stake: Amount wagered
        odds: American odds
        result: 'win', 'loss', or 'push'

    Returns:
        Tuple of (payout, profit_loss)
    """
    if result == 'push':
        return stake, 0.0  # Get stake back, no profit/loss
    elif result == 'win':
        payout = calculate_payout(stake, odds)
        profit = payout - stake
        return payout, profit
    else:  # loss
        return 0.0, -stake
