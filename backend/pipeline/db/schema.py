"""
PostgreSQL schema definitions using SQLAlchemy Core (table metadata only, no ORM).

Provides:
- All five pipeline tables as ``Table`` objects bound to a shared ``MetaData``.
- ``get_engine()``  – creates (or reuses) the SQLAlchemy engine from config.
- ``create_all_tables(engine)`` – issues CREATE TABLE IF NOT EXISTS for every table.
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    text,
)
from sqlalchemy.engine import Engine

from pipeline import config

# ---------------------------------------------------------------------------
# Shared metadata registry
# ---------------------------------------------------------------------------
metadata = MetaData()

# ---------------------------------------------------------------------------
# Table: predictions
# ---------------------------------------------------------------------------
predictions = Table(
    "predictions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("created_at_cst", DateTime(timezone=True), nullable=False),
    Column("sport", String(20), nullable=False),
    Column("home_team", String(100), nullable=False),
    Column("away_team", String(100), nullable=False),
    Column("game_time_cst", DateTime(timezone=True), nullable=False),
    # pick_side: 'home' | 'away' | 'over' | 'under'
    Column("pick_side", String(20), nullable=False),
    # pick_type: 'ml' | 'spread' | 'total'
    Column("pick_type", String(20), nullable=False),
    Column("our_probability", Float, nullable=False),
    Column("market_odds", Integer, nullable=False),       # American-style integer odds
    Column("market_implied_prob", Float, nullable=False),
    Column("edge_pct", Float, nullable=False),
    Column("detector", String(50), nullable=False),
    Column("reasoning", Text, nullable=False),
    # confidence_tier: 'high' | 'medium' | 'low'
    Column("confidence_tier", String(20), nullable=False),
    # status: 'pending' | 'graded' | 'void'
    Column("status", String(20), nullable=False, server_default=text("'pending'")),
    Column("result", String(10), nullable=True),          # 'win' | 'loss' | 'push'
    Column("pl_units", Float, nullable=True),
    Column("haiku_flags", Text, nullable=True),           # JSON string of flag list
    Column("sonnet_narrative", Text, nullable=True),
)

# ---------------------------------------------------------------------------
# Table: game_results
# ---------------------------------------------------------------------------
game_results = Table(
    "game_results",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sport", String(20), nullable=False),
    Column("home_team", String(100), nullable=False),
    Column("away_team", String(100), nullable=False),
    Column("game_date_cst", Date, nullable=False),
    Column("home_score", Integer, nullable=False),
    Column("away_score", Integer, nullable=False),
    Column("total", Float, nullable=False),
    Column("source", String(50), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

# ---------------------------------------------------------------------------
# Table: ingestion_log
# ---------------------------------------------------------------------------
ingestion_log = Table(
    "ingestion_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("run_at_cst", DateTime(timezone=True), nullable=False),
    Column("sport", String(20), nullable=False),
    Column("source", String(50), nullable=False),
    Column("records_fetched", Integer, nullable=False),
    Column("records_valid", Integer, nullable=False),
    Column("records_rejected", Integer, nullable=False),
    Column("haiku_flags", Text, nullable=True),           # JSON string of flag list
    Column("status", String(20), nullable=False),         # 'ok' | 'partial' | 'failed'
    Column("error_msg", Text, nullable=True),
)

# ---------------------------------------------------------------------------
# Table: reflection_reports
# ---------------------------------------------------------------------------
reflection_reports = Table(
    "reflection_reports",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("run_at_cst", DateTime(timezone=True), nullable=False),
    Column("report_date", Date, nullable=False),
    Column("sport", String(20), nullable=False),
    Column("total_picks", Integer, nullable=False),
    Column("flags_raised", Integer, nullable=False),
    # model_health: 'healthy' | 'warning' | 'critical'
    Column("model_health", String(20), nullable=False),
    Column("opus_narrative", Text, nullable=False),
    Column("action_items", Text, nullable=False),         # newline-delimited action list
)

# ---------------------------------------------------------------------------
# Table: model_performance
# ---------------------------------------------------------------------------
model_performance = Table(
    "model_performance",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sport", String(20), nullable=False),
    Column("model_name", String(100), nullable=False),
    Column("bet_type", String(20), nullable=False),       # 'ml' | 'spread' | 'total'
    Column("period_days", Integer, nullable=False),
    Column("total_picks", Integer, nullable=False),
    Column("wins", Integer, nullable=False),
    Column("losses", Integer, nullable=False),
    Column("pushes", Integer, nullable=False),
    Column("win_rate", Float, nullable=False),
    Column("roi_pct", Float, nullable=False),
    Column("avg_edge_pct", Float, nullable=False),
    Column("computed_at_cst", DateTime(timezone=True), nullable=False),
)

# ---------------------------------------------------------------------------
# Engine factory (singleton pattern)
# ---------------------------------------------------------------------------
_engine: Engine | None = None


def get_engine() -> Engine:
    """
    Return a SQLAlchemy engine connected to the configured database.

    The engine is created once and reused on subsequent calls (module-level
    singleton).  Connection pool settings match those in ``connection.py`` so
    that both modules draw from the same physical pool when the same process
    calls both.
    """
    global _engine
    if _engine is None:
        _engine = create_engine(
            config.DB_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            future=True,
        )
    return _engine


# ---------------------------------------------------------------------------
# DDL helper
# ---------------------------------------------------------------------------
def create_all_tables(engine: Engine) -> None:
    """
    Issue ``CREATE TABLE IF NOT EXISTS`` for every table defined in this module.

    Safe to call on every pipeline start-up; tables that already exist are
    left untouched.
    """
    metadata.create_all(engine, checkfirst=True)
