"""
Thin wrapper around the official kalshi-python SDK (v2.1.4+).

The SDK's KalshiClient already implements Kalshi's RSA-PSS request signing
internally (see its update_params_for_auth) - it just needs `api_key_id` and
`private_key_pem` set as attributes on the Configuration object. This module
does not re-implement signing; it only builds a client per-user and exposes
the handful of calls the trading strategies need.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from typing import Optional

import kalshi_python
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

logger = logging.getLogger(__name__)

# The installed kalshi-python SDK's Pydantic response models still expect the
# old integer-cents price fields (yes_ask, yes_bid, no_ask, no_bid). Kalshi's
# live API has moved to string-dollar fields instead (yes_ask_dollars, etc.)
# for market/orderbook pricing, so the SDK's typed fields silently come back
# as None even on genuinely liquid markets - confirmed by comparing the SDK's
# parsed result against the raw HTTP response for the same request. Anything
# involving live prices below reads the raw JSON directly rather than trusting
# the SDK's model. Account-level fields (balance) are unaffected and still
# use the typed SDK response.


def _dollars_to_cents(value) -> Optional[int]:
    if value in (None, ""):
        return None
    return round(float(value) * 100)

LIVE_API_BASE = "https://api.elections.kalshi.com/trade-api/v2"
DEMO_API_BASE = "https://demo-api.kalshi.co/trade-api/v2"

# Order placement specifically must go through the V2 orders endpoint on its
# own documented host - confirmed directly that the SDK's own create_order
# hits the deprecated /portfolio/orders (v1) path and returns 410 Gone.
ORDERS_V2_HOST = "https://external-api.kalshi.com/trade-api/v2"
ORDERS_V2_DEMO_HOST = "https://external-api.demo.kalshi.co/trade-api/v2"


class KalshiClientError(Exception):
    pass


def build_client(api_key_id: str, private_key_pem: str, demo_mode: bool = False) -> kalshi_python.KalshiClient:
    """Build a fresh, credential-scoped Kalshi client instance.

    Callers must key any cache of these by username and never share one
    instance's credentials across users.
    """
    config = kalshi_python.Configuration(
        host=DEMO_API_BASE if demo_mode else LIVE_API_BASE,
    )
    config.api_key_id = api_key_id
    config.private_key_pem = private_key_pem
    client = kalshi_python.KalshiClient(config)
    client._kalshi_demo_mode = demo_mode
    return client


def get_balance_cents(client: kalshi_python.KalshiClient) -> int:
    resp = client.get_balance()
    return resp.balance


def get_positions(client: kalshi_python.KalshiClient, ticker: Optional[str] = None) -> list:
    """Returns a list of {ticker, contracts, exposure_cents, realized_pnl_cents,
    fees_paid_cents, last_updated_ts}. Reads the raw JSON directly - the SDK's
    typed GetPositionsResponse.positions field doesn't match the API's real
    key (market_positions), so it always silently returned an empty list even
    for genuinely open positions (confirmed directly against a real position
    opened during testing)."""
    raw_resp = client.get_positions_without_preload_content(ticker=ticker) if ticker else client.get_positions_without_preload_content()
    data = json.loads(raw_resp.data)
    return [
        {
            "ticker": p.get("ticker"),
            "contracts": float(p.get("position_fp", 0)),
            "exposure_cents": _dollars_to_cents(p.get("market_exposure_dollars")),
            "realized_pnl_cents": _dollars_to_cents(p.get("realized_pnl_dollars")),
            "fees_paid_cents": _dollars_to_cents(p.get("fees_paid_dollars")),
            "last_updated_ts": p.get("last_updated_ts"),
        }
        for p in data.get("market_positions", [])
    ]


def _market_pricing_from_raw(raw: dict) -> dict:
    """Normalize a raw /markets JSON market object into cents-based fields,
    reading the modern *_dollars string fields (see module docstring)."""
    return {
        "ticker": raw.get("ticker"),
        "event_ticker": raw.get("event_ticker"),
        "title": raw.get("title"),
        # The readable team/player name this specific market's "yes" side
        # refers to (e.g. "Minnesota", "Toronto", "Sesko") - confirmed
        # present on every market checked (MLB, WNBA, tennis). Matching
        # against this directly is far more reliable than reverse-engineering
        # team names from ticker abbreviation codes, and needs no per-sport
        # or per-team dictionary at all.
        "yes_sub_title": raw.get("yes_sub_title"),
        "status": raw.get("status"),
        "close_time": raw.get("close_time"),
        # close_time/expiration_time include a multi-day settlement buffer
        # (observed: several days after the actual game) - expected_expiration_time
        # is the field that actually tracks real game start/end time, and is
        # what any date-based game matching should use instead.
        "expected_expiration_time": raw.get("expected_expiration_time"),
        "yes_ask_cents": _dollars_to_cents(raw.get("yes_ask_dollars")),
        "yes_bid_cents": _dollars_to_cents(raw.get("yes_bid_dollars")),
        "no_ask_cents": _dollars_to_cents(raw.get("no_ask_dollars")),
        "no_bid_cents": _dollars_to_cents(raw.get("no_bid_dollars")),
        "last_price_cents": _dollars_to_cents(raw.get("last_price_dollars")),
        "volume": raw.get("volume_fp"),
        "liquidity_dollars": raw.get("liquidity_dollars"),
    }


def get_events(client: kalshi_python.KalshiClient, series_ticker: str, status: str = "open",
                limit: int = 200) -> list:
    """Returns a list of {event_ticker, title, markets: [market dicts]}.

    Uses the raw JSON response, not the SDK's typed get_events() - confirmed
    it throws a pydantic ValidationError on markets with status='finalized'
    (not in the SDK's enum), on top of the same *_dollars pricing-field
    mismatch every other typed response here has. One call per series
    ticker returns every event AND its nested markets - this is the
    efficient per-sport fetch, not a per-game/per-bet call."""
    raw_resp = client.get_events_without_preload_content(
        series_ticker=series_ticker, status=status, limit=limit, with_nested_markets=True,
    )
    data = json.loads(raw_resp.data)
    events = []
    for e in data.get("events", []):
        events.append({
            "event_ticker": e.get("event_ticker"),
            "title": e.get("title"),
            "markets": [_market_pricing_from_raw(m) for m in e.get("markets", [])],
        })
    return events


def get_markets(client: kalshi_python.KalshiClient, event_ticker: Optional[str] = None,
                 series_ticker: Optional[str] = None, status: str = "open", limit: int = 100) -> list:
    raw_resp = client.get_markets_without_preload_content(
        event_ticker=event_ticker, series_ticker=series_ticker, status=status, limit=limit,
    )
    data = json.loads(raw_resp.data)
    return [_market_pricing_from_raw(m) for m in data.get("markets", [])]


def get_market(client: kalshi_python.KalshiClient, ticker: str) -> dict:
    raw_resp = client.get_market_without_preload_content(ticker=ticker)
    data = json.loads(raw_resp.data)
    return _market_pricing_from_raw(data.get("market", {}))


def get_market_orderbook(client: kalshi_python.KalshiClient, ticker: str, depth: int = 5) -> dict:
    """Returns {"yes": [(price_cents, size), ...], "no": [(price_cents, size), ...]}
    sorted as returned by Kalshi (best price first is not guaranteed - callers
    should sort/select as needed)."""
    raw_resp = client.get_market_orderbook_without_preload_content(ticker=ticker, depth=depth)
    data = json.loads(raw_resp.data)
    book = data.get("orderbook_fp") or data.get("orderbook") or {}

    def _levels(levels):
        out = []
        for price_str, size_str in (levels or []):
            out.append((_dollars_to_cents(price_str), float(size_str)))
        return out

    return {"yes": _levels(book.get("yes_dollars") or book.get("yes")),
            "no": _levels(book.get("no_dollars") or book.get("no"))}


def _sign_request(api_key_id: str, private_key_pem: str, method: str, path: str) -> dict:
    """Kalshi's RSA-PSS-SHA256 request signature, same scheme the SDK itself
    implements (see kalshi_python.KalshiClient.update_params_for_auth) -
    reimplemented here only because order placement must bypass the SDK's
    request path entirely (see create_order docstring)."""
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode() if isinstance(private_key_pem, str) else private_key_pem,
        password=None, backend=default_backend(),
    )
    ts = str(int(time.time() * 1000))
    msg = f"{ts}{method.upper()}{path}".encode("utf-8")
    signature = private_key.sign(
        msg,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256(),
    )
    return {
        "KALSHI-ACCESS-KEY": api_key_id,
        "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode("utf-8"),
        "KALSHI-ACCESS-TIMESTAMP": ts,
        "Content-Type": "application/json",
    }


def create_order(
    client: kalshi_python.KalshiClient,
    *,
    ticker: str,
    side: str,          # "yes" | "no"
    action: str,        # "buy" | "sell"
    count: int,
    order_type: str = "limit",
    yes_price: Optional[int] = None,   # cents
    no_price: Optional[int] = None,    # cents
    expiration_ts: Optional[int] = None,
) -> dict:
    """Place a real order via Kalshi's V2 orders endpoint.

    The SDK's own create_order() hits the deprecated /portfolio/orders (v1)
    path and returns 410 Gone - confirmed directly against the live API
    before this was written, with zero funds moved (the request was
    rejected cleanly). V2 collapses side+action into a single field, always
    quoted from the YES perspective: side="bid" buys yes, side="ask" sells
    yes (economically equivalent to buying no at 1 - price). There is no
    separate yes/no toggle in V2.

    Callers are responsible for HITL confirmation and risk-cap checks
    *before* calling this - this function does not gate anything itself.
    """
    if side == "yes" and action == "buy":
        v2_side, price_cents = "bid", yes_price
    elif side == "yes" and action == "sell":
        v2_side, price_cents = "ask", yes_price
    elif side == "no" and action == "buy":
        v2_side, price_cents = "ask", (100 - no_price) if no_price is not None else None
    elif side == "no" and action == "sell":
        v2_side, price_cents = "bid", (100 - no_price) if no_price is not None else None
    else:
        raise KalshiClientError(f"Unsupported side/action combination: side={side!r}, action={action!r}")
    if price_cents is None:
        raise KalshiClientError("A price is required (yes_price or no_price)")

    body = {
        "ticker": ticker,
        "client_order_id": f"kalshi_mispricing_{int(time.time() * 1000)}",
        "side": v2_side,
        "count": f"{count:.2f}",
        "price": f"{price_cents / 100.0:.4f}",
        "time_in_force": "immediate_or_cancel" if order_type == "market" else "good_till_canceled",
        "self_trade_prevention_type": "taker_at_cross",
    }
    if expiration_ts is not None:
        body["expiration_time"] = expiration_ts

    host = ORDERS_V2_DEMO_HOST if getattr(client, "_kalshi_demo_mode", False) else ORDERS_V2_HOST
    path = "/trade-api/v2/portfolio/events/orders"
    headers = _sign_request(client.api_key_id, client.private_key_pem, "POST", path)

    resp = requests.post(host + "/portfolio/events/orders", headers=headers, json=body, timeout=30)
    if resp.status_code not in (200, 201):
        logger.error("[kalshi_client] create_order failed: HTTP %s %s", resp.status_code, resp.text)
        raise KalshiClientError(f"HTTP {resp.status_code}: {resp.text}")
    return resp.json()


def cancel_order(client: kalshi_python.KalshiClient, order_id: str):
    return client.cancel_order(order_id=order_id)


def get_fills(client: kalshi_python.KalshiClient, ticker: Optional[str] = None, limit: int = 100) -> list:
    resp = client.get_fills(ticker=ticker, limit=limit) if ticker else client.get_fills(limit=limit)
    return resp.fills or []


def kalshi_fee_cents(contracts: int, price_cents: int) -> int:
    """Kalshi's standard trading fee: ceil(0.07 * contracts * price * (1-price)),
    price expressed as a probability in [0,1]. Charged on both entry and exit.
    This is the piece the old strategies never accounted for."""
    import math
    price = price_cents / 100.0
    fee_dollars = 0.07 * contracts * price * (1 - price)
    return math.ceil(fee_dollars * 100)
