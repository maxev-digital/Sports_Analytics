"""
SQLAlchemy ORM models for player props ML system
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from backend.database.connection import Base


class PlayerPropsLine(Base):
    """
    Daily props lines from bookmakers
    Stores opening lines for historical tracking
    """
    __tablename__ = "player_props_lines"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    game_id = Column(String(50), nullable=True)
    player_id = Column(String(50), nullable=False, index=True)
    player_name = Column(String(100), nullable=False)
    team = Column(String(10), nullable=False)
    opponent = Column(String(10), nullable=False)
    home_away = Column(String(4), nullable=True)  # 'HOME' or 'AWAY'
    prop_type = Column(String(20), nullable=False, index=True)  # 'points', 'rebounds', etc.
    market_line = Column(Float, nullable=False)
    over_odds = Column(Integer, nullable=True)  # American odds
    under_odds = Column(Integer, nullable=True)
    bookmaker = Column(String(50), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint: one line per player/prop/bookmaker per day
    __table_args__ = (
        UniqueConstraint('date', 'player_id', 'prop_type', 'bookmaker', name='uix_daily_prop_line'),
    )

    def __repr__(self):
        return f"<PropLine {self.player_name} {self.prop_type} {self.market_line} on {self.date}>"


class PlayerPropsResult(Base):
    """
    Actual game results for grading props
    Stores final stats after games complete
    """
    __tablename__ = "player_props_results"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    game_id = Column(String(50), nullable=True)
    player_id = Column(String(50), nullable=False, index=True)
    player_name = Column(String(100), nullable=False)
    team = Column(String(10), nullable=False)
    opponent = Column(String(10), nullable=False)
    prop_type = Column(String(20), nullable=False)
    market_line = Column(Float, nullable=False)
    actual_value = Column(Float, nullable=False)
    hit = Column(Boolean, nullable=False)  # TRUE if actual > line (for OVER)
    difference = Column(Float, nullable=True)  # actual - line
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint: one result per player/prop per day
    __table_args__ = (
        UniqueConstraint('date', 'player_id', 'prop_type', name='uix_daily_prop_result'),
    )

    def __repr__(self):
        hit_str = "HIT" if self.hit else "MISS"
        return f"<PropResult {self.player_name} {self.prop_type}: {self.actual_value} vs {self.market_line} - {hit_str}>"


class PlayerPropsPrediction(Base):
    """
    ML model predictions for player props
    Stores daily predictions with confidence and edge analysis
    """
    __tablename__ = "player_props_predictions"

    id = Column(Integer, primary_key=True, index=True)
    prediction_date = Column(Date, nullable=False, index=True)
    game_date = Column(Date, nullable=False, index=True)
    player_id = Column(String(50), nullable=False, index=True)
    player_name = Column(String(100), nullable=False)
    team = Column(String(10), nullable=False)
    opponent = Column(String(10), nullable=False)
    prop_type = Column(String(20), nullable=False, index=True)
    market_line = Column(Float, nullable=False)
    predicted_value = Column(Float, nullable=False)
    confidence = Column(Float, nullable=True)  # 0-100 score
    model_type = Column(String(50), nullable=True)  # 'xgboost', 'lightgbm', 'ensemble'
    edge_pct = Column(Float, nullable=True)  # (predicted - line) / line * 100
    recommendation = Column(String(10), nullable=True)  # 'OVER', 'UNDER', 'PASS'

    # Results (filled after game completes)
    actual_value = Column(Float, nullable=True)
    result = Column(String(10), nullable=True)  # 'WIN', 'LOSS', 'PUSH'

    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint: one prediction per player/prop/model per day
    __table_args__ = (
        UniqueConstraint('prediction_date', 'player_id', 'prop_type', 'model_type',
                        name='uix_daily_prediction'),
    )

    def __repr__(self):
        return f"<PropPrediction {self.player_name} {self.prop_type}: {self.predicted_value} vs {self.market_line} ({self.confidence}%)>"


class PlayerStatsCache(Base):
    """
    Cache for player statistics to avoid redundant API calls
    Stores daily player stats snapshots
    """
    __tablename__ = "player_stats_cache"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(String(50), nullable=False, index=True)
    player_name = Column(String(100), nullable=False)
    team = Column(String(10), nullable=False)
    date = Column(Date, nullable=False, index=True)

    # Season stats
    games_played = Column(Integer, nullable=True)
    minutes_per_game = Column(Float, nullable=True)
    points_per_game = Column(Float, nullable=True)
    rebounds_per_game = Column(Float, nullable=True)
    assists_per_game = Column(Float, nullable=True)
    fg3_per_game = Column(Float, nullable=True)
    blocks_per_game = Column(Float, nullable=True)
    steals_per_game = Column(Float, nullable=True)
    fg_pct = Column(Float, nullable=True)

    # Recent form (last 10 games)
    last_10_ppg = Column(Float, nullable=True)
    last_10_rpg = Column(Float, nullable=True)
    last_10_apg = Column(Float, nullable=True)

    # Trend indicators
    trend_direction = Column(String(20), nullable=True)  # 'increasing', 'decreasing', 'stable'

    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('player_id', 'date', name='uix_player_stats_cache'),
    )

    def __repr__(self):
        return f"<StatsCache {self.player_name} on {self.date}>"
