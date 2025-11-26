"""
Volatility Arbitrage Data Models
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List


@dataclass
class EntryOpportunity:
    """Entry opportunity for first leg of volatility arbitrage"""
    game_id: str
    sport: str
    home_team: str
    away_team: str

    # Entry details
    entry_team: str  # Team to bet on
    entry_side: str  # 'home' or 'away'
    entry_odds: int  # American odds (e.g., +200)

    # Edge calculation
    implied_prob: float  # Market implied probability
    true_prob: float  # ML model estimated probability
    edge: float  # true_prob - implied_prob
    ev_percent: float  # Expected value as % of stake

    # Game state
    quarter: str
    time_remaining: str
    score_home: int
    score_away: int

    # Recommended action
    recommended_stake: float
    confidence: str  # 'LOW', 'MEDIUM', 'HIGH'

    # Metadata
    timestamp: datetime
    bookmaker: str
    bookmaker_title: str

    # Trigger suggestion
    suggested_trigger_odds: int  # Suggested opposite side target
    min_locked_profit: float  # Min profit to hedge


@dataclass
class VolatilityPosition:
    """Active volatility arbitrage position"""
    id: str
    user_id: str
    game_id: str
    sport: str
    home_team: str
    away_team: str

    # First leg (entry)
    first_team: str
    first_side: str  # 'home' or 'away'
    first_odds: int
    first_stake: float
    first_timestamp: datetime
    first_bookmaker: str

    # Trigger conditions
    trigger_price: int  # Target odds for opposite side
    trigger_min_profit: float  # Min locked profit to alert

    # Second leg (hedge) - populated when executed
    second_team: Optional[str] = None
    second_odds: Optional[int] = None
    second_stake: Optional[float] = None
    second_timestamp: Optional[datetime] = None
    second_bookmaker: Optional[str] = None

    # Status
    status: str = 'open'  # 'open', 'hedged', 'closed_won', 'closed_lost', 'expired'
    locked_profit: Optional[float] = None
    actual_profit: Optional[float] = None

    # Game state when opened
    entry_quarter: str = ''
    entry_score: str = ''

    # Metadata
    created_at: datetime = None
    updated_at: datetime = None
    closed_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'game_id': self.game_id,
            'sport': self.sport,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'first_leg': {
                'team': self.first_team,
                'side': self.first_side,
                'odds': self.first_odds,
                'stake': self.first_stake,
                'timestamp': self.first_timestamp.isoformat() if self.first_timestamp else None,
                'bookmaker': self.first_bookmaker,
                'potential_win': self.calculate_potential_win(self.first_odds, self.first_stake)
            },
            'trigger': {
                'target_odds': self.trigger_price,
                'min_profit': self.trigger_min_profit
            },
            'second_leg': {
                'team': self.second_team,
                'odds': self.second_odds,
                'stake': self.second_stake,
                'timestamp': self.second_timestamp.isoformat() if self.second_timestamp else None,
                'bookmaker': self.second_bookmaker
            } if self.second_team else None,
            'status': self.status,
            'locked_profit': self.locked_profit,
            'actual_profit': self.actual_profit,
            'entry_state': {
                'quarter': self.entry_quarter,
                'score': self.entry_score
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None
        }

    @staticmethod
    def calculate_potential_win(odds: int, stake: float) -> float:
        """Calculate potential winnings from American odds"""
        if odds > 0:
            return stake * (odds / 100)
        else:
            return stake * (100 / abs(odds))


@dataclass
class HedgeAlert:
    """Alert when second-leg hedge opportunity is available"""
    position_id: str
    game_id: str
    user_id: str

    # Position details
    home_team: str
    away_team: str
    first_team: str
    first_odds: int
    first_stake: float

    # Hedge opportunity
    hedge_team: str
    hedge_odds: int  # Current available odds
    hedge_bookmaker: str
    hedge_bookmaker_title: str

    # Calculations
    recommended_stake: float  # Optimal hedge stake
    profit_if_first_wins: float
    profit_if_hedge_wins: float
    locked_profit: float  # Guaranteed profit both sides

    # EV comparison
    ev_if_hedge: float  # EV of taking hedge
    ev_if_hold: float  # EV of holding original position

    # Game state
    current_quarter: str
    current_score: str
    time_remaining: str

    # Alert metadata
    timestamp: datetime
    expires_in: int  # Seconds until game ends
    priority: str = 'high'

    def to_dict(self) -> Dict:
        """Convert to dictionary for API/Toast alert"""
        return {
            'position_id': self.position_id,
            'game_id': self.game_id,
            'user_id': self.user_id,
            'game': {
                'home_team': self.home_team,
                'away_team': self.away_team,
                'quarter': self.current_quarter,
                'score': self.current_score,
                'time_remaining': self.time_remaining
            },
            'your_position': {
                'team': self.first_team,
                'odds': self.first_odds,
                'stake': self.first_stake,
                'potential_win': VolatilityPosition.calculate_potential_win(self.first_odds, self.first_stake)
            },
            'hedge_opportunity': {
                'team': self.hedge_team,
                'odds': self.hedge_odds,
                'bookmaker': self.hedge_bookmaker,
                'bookmaker_title': self.hedge_bookmaker_title,
                'recommended_stake': round(self.recommended_stake, 2)
            },
            'payoff_table': {
                'if_first_wins': round(self.profit_if_first_wins, 2),
                'if_hedge_wins': round(self.profit_if_hedge_wins, 2),
                'locked_profit': round(self.locked_profit, 2)
            },
            'ev_comparison': {
                'hedge_now': round(self.ev_if_hedge, 2),
                'hold_position': round(self.ev_if_hold, 2),
                'recommendation': 'HEDGE' if self.ev_if_hedge > self.ev_if_hold else 'HOLD'
            },
            'timestamp': self.timestamp.isoformat(),
            'expires_in': self.expires_in,
            'priority': self.priority
        }


@dataclass
class PositionResult:
    """Result of a closed volatility arbitrage position"""
    position_id: str
    user_id: str
    game_id: str

    # Position summary
    first_team: str
    first_odds: int
    first_stake: float

    second_team: Optional[str]
    second_odds: Optional[int]
    second_stake: Optional[float]

    # Outcome
    winning_team: str
    was_hedged: bool
    locked_profit: Optional[float]  # If hedged
    actual_profit: float

    # Performance vs expectation
    expected_ev: float
    actual_ev: float
    variance: float  # actual - expected

    # Metadata
    closed_at: datetime
    duration_minutes: int


@dataclass
class PerformanceStats:
    """Volatility arbitrage performance statistics"""
    user_id: str
    timeframe: str  # 'week', 'month', 'season', 'all'

    # Position counts
    total_positions: int
    hedged_positions: int
    held_and_won: int
    held_and_lost: int
    expired: int

    # Financials
    total_wagered: float
    total_profit: float
    roi_percent: float

    # vs Projections
    expected_profit: float
    variance: float  # actual - expected
    variance_percent: float

    # Trigger rate
    actual_trigger_rate: float  # % of positions that hit hedge
    expected_trigger_rate: float  # From config (35%)

    # Edge validation
    avg_ev_per_attempt: float
    expected_avg_ev: float  # From config (15.7%)

    # Risk metrics
    largest_win: float
    largest_loss: float
    max_drawdown: float

    # Metadata
    start_date: datetime
    end_date: datetime
    last_updated: datetime
