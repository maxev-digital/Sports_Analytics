"""
Kalshi trading tables - separate MetaData registry from the sports pipeline's
schema.py, sharing the same Postgres engine/connection.

Design notes (fixing what the old kalshi_bot build got wrong):
- Keyed on `username` (matching the platform's real auth.py session store,
  which is username-keyed, not a relational `users` table with integer IDs -
  there is no `users` SQL table to foreign-key against).
- Real FOREIGN KEY + ON DELETE CASCADE from kalshi_strategy_subscriptions and
  kalshi_orders back to kalshi_credentials.username, so deleting a user's
  connection cleans up everything downstream instead of leaving orphans.
- kalshi_orders has ONE order-id column (`kalshi_order_id`) - the old build
  had a migration defining `entry_order_id`/`exit_order_id` while the worker
  code inserted into a nonexistent `kalshi_order_id` column, which would have
  crashed on the first real trade.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.engine import Engine

metadata = MetaData()

kalshi_credentials = Table(
    "kalshi_credentials",
    metadata,
    Column("username", String(100), primary_key=True),
    Column("nonce_b64", Text, nullable=False),
    Column("encrypted_api_key_id_b64", Text, nullable=False),
    Column("encrypted_private_key_b64", Text, nullable=False),
    Column("demo_mode", Boolean, nullable=False, server_default=text("false")),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("rotated_at", DateTime(timezone=True), nullable=True),
)

kalshi_strategy_subscriptions = Table(
    "kalshi_strategy_subscriptions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(100), ForeignKey("kalshi_credentials.username", ondelete="CASCADE"), nullable=False),
    Column("strategy_id", String(50), nullable=False),
    Column("enabled", Boolean, nullable=False, server_default=text("false")),
    Column("requires_approval", Boolean, nullable=False, server_default=text("true")),
    Column("risk_config_json", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    UniqueConstraint("username", "strategy_id", name="uq_kalshi_strategy_subscriptions_user_strategy"),
)

kalshi_orders = Table(
    "kalshi_orders",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(100), ForeignKey("kalshi_credentials.username", ondelete="CASCADE"), nullable=False),
    Column("strategy_id", String(50), nullable=False),
    Column("candidate_edge_id", Integer, ForeignKey("kalshi_candidate_edges.id", ondelete="SET NULL"), nullable=True),
    Column("market_ticker", String(100), nullable=False),
    Column("kalshi_order_id", String(100), nullable=True),
    Column("side", String(10), nullable=False),     # "yes" | "no"
    Column("action", String(10), nullable=False),    # "buy" | "sell"
    Column("count", Integer, nullable=False),
    Column("price_cents", Integer, nullable=False),
    Column("fee_cents", Integer, nullable=False, server_default=text("0")),
    Column("status", String(20), nullable=False, server_default=text("'pending'")),
    Column("requires_approval", Boolean, nullable=False, server_default=text("true")),
    Column("net_edge_pct", Text, nullable=True),
    Column("placed_at", DateTime(timezone=True), nullable=True),
    Column("filled_at", DateTime(timezone=True), nullable=True),
    Column("settled_at", DateTime(timezone=True), nullable=True),
    Column("pnl_cents", Integer, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
)

kalshi_candidate_edges = Table(
    "kalshi_candidate_edges",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("detector", String(50), nullable=False),
    Column("market_ticker", String(100), nullable=False),
    Column("sport", String(20), nullable=False),
    Column("game_id", String(100), nullable=True),
    Column("sharp_consensus_total", Text, nullable=True),
    Column("kalshi_strike", Text, nullable=True),
    Column("true_probability", Text, nullable=False),
    Column("kalshi_price_cents", Integer, nullable=False),
    Column("raw_edge_pct", Text, nullable=False),
    Column("net_edge_pct", Text, nullable=False),
    Column("books_sampled", Integer, nullable=False),
    Column("detected_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
)


def create_all_tables(engine: Engine) -> None:
    """Issue CREATE TABLE IF NOT EXISTS for every Kalshi table. Safe to call
    on every startup."""
    metadata.create_all(engine, checkfirst=True)
