"""
M2: HITL order execution. A human (or, later, an auto-trading loop gated by
kalshi_strategy_subscriptions.requires_approval) confirms a logged candidate
edge, and this module places the real order.

HARD RULE: no single trade may ever exceed MAX_CONTRACTS_PER_TRADE contracts.
This is enforced here, in the one place that calls kalshi_client.create_order
for strategy-driven trades - not left to caller-supplied config, which could
be misconfigured. Nothing in this module can push a request through above the
cap; it is silently floored, not just validated.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from kalshi.kalshi_client import get_market, create_order, kalshi_fee_cents, KalshiClientError

logger = logging.getLogger(__name__)

MAX_CONTRACTS_PER_TRADE = 2  # hard ceiling - see module docstring
MAX_PRICE_DRIFT_CENTS = 5    # re-check the edge is still real before firing


class ExecutionError(Exception):
    pass


def _enforce_contract_cap(requested: int) -> int:
    """Never returns more than MAX_CONTRACTS_PER_TRADE, regardless of input."""
    if requested is None or requested < 1:
        requested = 1
    if requested > MAX_CONTRACTS_PER_TRADE:
        logger.warning(
            "[kalshi.execution] Requested %d contracts, hard-capped to %d",
            requested, MAX_CONTRACTS_PER_TRADE,
        )
    return min(requested, MAX_CONTRACTS_PER_TRADE)


def execute_candidate_edge(
    client,
    username: str,
    candidate_edge_id: int,
    requested_contracts: int = 1,
) -> dict:
    """Place a real order against a previously-detected candidate edge.

    Re-fetches the live market price first and refuses to trade if it has
    moved meaningfully since detection - a logged candidate can go stale
    within seconds on a real order book, and trading a stale price would
    silently invalidate the whole point of the edge check.

    strategy_id is derived from the candidate row's own `detector` field
    rather than passed in separately - a caller-supplied strategy_id could
    mismatch the actual candidate (e.g. UI sends the wrong sport's strategy
    id for this row), which the audit trail should never allow.
    """
    from pipeline.db.connection import execute_query

    contracts = _enforce_contract_cap(requested_contracts)

    rows = execute_query(
        "SELECT * FROM kalshi_candidate_edges WHERE id = %(id)s",
        {"id": candidate_edge_id},
    )
    if not rows:
        raise ExecutionError(f"No candidate edge with id={candidate_edge_id}")
    candidate = rows[0]
    strategy_id = candidate["detector"]

    live_market = get_market(client, candidate["market_ticker"])
    live_price = live_market["yes_ask_cents"]
    if live_price is None:
        raise ExecutionError(f"No live quote for {candidate['market_ticker']} - cannot execute")

    logged_price = candidate["kalshi_price_cents"]
    if abs(live_price - logged_price) > MAX_PRICE_DRIFT_CENTS:
        raise ExecutionError(
            f"Price moved from {logged_price}c to {live_price}c since detection "
            f"(> {MAX_PRICE_DRIFT_CENTS}c drift) - refusing to trade a stale edge"
        )

    fee_cents = kalshi_fee_cents(contracts, live_price)

    inserted = execute_query(
        """
        INSERT INTO kalshi_orders
            (username, strategy_id, candidate_edge_id, market_ticker, side, action, count,
             price_cents, fee_cents, status, requires_approval, net_edge_pct, placed_at)
        VALUES
            (%(username)s, %(strategy_id)s, %(candidate_edge_id)s, %(ticker)s, 'yes', 'buy', %(count)s,
             %(price)s, %(fee)s, 'placing', true, %(net_edge)s, %(now)s)
        RETURNING id
        """,
        {
            "username": username, "strategy_id": strategy_id, "candidate_edge_id": candidate_edge_id,
            "ticker": candidate["market_ticker"],
            "count": contracts, "price": live_price, "fee": fee_cents,
            "net_edge": str(candidate["net_edge_pct"]), "now": datetime.now(timezone.utc),
        },
    )
    order_row_id = inserted[0]["id"]

    try:
        resp = create_order(
            client,
            ticker=candidate["market_ticker"],
            side="yes",
            action="buy",
            count=contracts,
            order_type="limit",
            yes_price=live_price,
        )
        kalshi_order_id = resp.get("order_id")  # V2 response: order_id is top-level
        execute_query(
            "UPDATE kalshi_orders SET status = 'placed', kalshi_order_id = %(oid)s "
            "WHERE id = %(id)s RETURNING id",
            {"oid": kalshi_order_id, "id": order_row_id},
        )
        return {
            "status": "placed",
            "market_ticker": candidate["market_ticker"],
            "contracts": contracts,
            "price_cents": live_price,
            "fee_cents": fee_cents,
            "kalshi_order_id": kalshi_order_id,
        }
    except KalshiClientError as exc:
        execute_query(
            "UPDATE kalshi_orders SET status = 'failed' WHERE id = %(id)s RETURNING id",
            {"id": order_row_id},
        )
        raise ExecutionError(str(exc)) from exc
