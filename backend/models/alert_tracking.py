"""Alert Tracking Model for Performance Analytics"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class TrackedAlert(BaseModel):
    """Model for tracking alert performance"""
    id: str
    alert_type: Literal['arbitrage', 'steam_move', 'middle', 'goalie_pull',
                       'favorite_comeback', 'halftime_tracker', 'momentum_shift',
                       'late_line_movement', 'quarter_reversal']

    # Game Info
    game_id: str
    sport: str
    home_team: str
    away_team: str
    commence_time: str

    # Alert Details
    market_type: str  # 'spreads', 'totals', 'h2h', 'props'
    recommended_side: str  # "OVER 220.5", "Lakers -3.5", etc.
    recommended_odds: float  # American odds
    recommended_bookmaker: str

    # Alert Metadata
    confidence: Optional[Literal['HIGH', 'MEDIUM', 'LOW']] = None
    edge_percent: Optional[float] = None
    profit_potential: Optional[float] = None  # Expected profit

    # Tracking
    generated_at: str  # ISO timestamp when alert was created
    expires_at: Optional[str] = None  # When alert is no longer valid

    # Settlement (updated after game finishes)
    status: Literal['pending', 'active', 'won', 'lost', 'push', 'expired'] = 'pending'
    outcome: Optional[Literal['win', 'loss', 'push']] = None
    actual_result: Optional[str] = None  # Actual game outcome for verification
    settled_at: Optional[str] = None

    # Performance
    times_clicked: int = 0  # How many users clicked this alert
    times_bet: int = 0  # How many users actually bet on this

    # Additional context
    strategy_details: Optional[dict] = None  # Strategy-specific data
    notes: Optional[str] = None


class SettleAlertRequest(BaseModel):
    """Request model for settling an alert"""
    outcome: Literal['win', 'loss', 'push']
    actual_result: Optional[str] = None


class AlertPerformanceStats(BaseModel):
    """Performance statistics for an alert type"""
    alert_type: str
    total_alerts: int = 0
    pending_alerts: int = 0
    active_alerts: int = 0
    settled_alerts: int = 0

    successful_alerts: int = 0  # Won
    failed_alerts: int = 0  # Lost
    push_alerts: int = 0  # Push
    expired_alerts: int = 0  # Expired without being bet

    win_rate: float = 0.0  # successful / (successful + failed)
    avg_profit: float = 0.0
    total_profit: float = 0.0

    # Engagement metrics
    total_clicks: int = 0
    total_bets: int = 0
    click_to_bet_rate: float = 0.0  # bets / clicks

    last_updated: str


def calculate_alert_profit(odds: float, stake: float, outcome: str) -> float:
    """
    Calculate profit/loss for an alert outcome

    Args:
        odds: American odds
        stake: Amount that would be wagered (using avg or assuming 1 unit)
        outcome: 'win', 'loss', or 'push'

    Returns:
        Profit or loss amount
    """
    if outcome == 'push':
        return 0.0
    elif outcome == 'win':
        if odds > 0:
            profit = (stake * odds) / 100
        else:
            profit = (stake * 100) / abs(odds)
        return profit
    else:  # loss
        return -stake
