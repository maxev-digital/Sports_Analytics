"""
Kalshi account connection + read-only account endpoints (M0).

Every route requires a valid platform session (Authorization: Bearer <token>,
verified via auth.verify_session - same pattern used by routes/influencer.py)
and every query is scoped to that session's username. No route accepts a
client-supplied username/user_id as the source of truth - this was the exact
gap that let the old build's trades execute against the wrong account.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel

from auth import verify_session
from kalshi import key_manager
from kalshi.key_manager import EncryptedCredential
from kalshi.kalshi_client import build_client, get_balance_cents, get_positions, KalshiClientError
from kalshi.kalshi_sharp_mispricing import detect_all_sports, log_candidate_edges, list_markets_for_sport
from kalshi.execution import execute_candidate_edge, ExecutionError, MAX_CONTRACTS_PER_TRADE

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/kalshi", tags=["kalshi"])


def _current_username(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "")
    username = verify_session(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return username


class ConnectRequest(BaseModel):
    api_key_id: str
    private_key_pem: str
    demo_mode: bool = False


def _get_client_for_user(username: str):
    from pipeline.db.connection import execute_query

    rows = execute_query(
        "SELECT nonce_b64, encrypted_api_key_id_b64, encrypted_private_key_b64, demo_mode "
        "FROM kalshi_credentials WHERE username = %(username)s",
        {"username": username},
    )
    if not rows:
        raise HTTPException(status_code=404, detail="No Kalshi account connected for this user")
    row = rows[0]
    cred = EncryptedCredential(
        nonce_b64=row["nonce_b64"],
        encrypted_api_key_id_b64=row["encrypted_api_key_id_b64"],
        encrypted_private_key_b64=row["encrypted_private_key_b64"],
    )
    api_key_id, private_key_pem = key_manager.decrypt_credentials(username, cred)
    return build_client(api_key_id, private_key_pem, demo_mode=row["demo_mode"])


@router.post("/connect")
async def connect_kalshi_account(body: ConnectRequest, authorization: Optional[str] = Header(None)):
    username = _current_username(authorization)
    from pipeline.db.connection import execute_write

    # Verify the credentials actually work before storing them.
    try:
        client = build_client(body.api_key_id, body.private_key_pem, demo_mode=body.demo_mode)
        balance_cents = get_balance_cents(client)
    except Exception as exc:
        logger.warning("[kalshi.connect] verification failed for %s: %s", username, exc)
        raise HTTPException(status_code=400, detail=f"Could not verify Kalshi credentials: {exc}")

    cred = key_manager.encrypt_credentials(username, body.api_key_id, body.private_key_pem)
    execute_write(
        """
        INSERT INTO kalshi_credentials
            (username, nonce_b64, encrypted_api_key_id_b64, encrypted_private_key_b64, demo_mode, created_at)
        VALUES (%(username)s, %(nonce)s, %(key_id)s, %(priv_key)s, %(demo)s, %(now)s)
        ON CONFLICT (username) DO UPDATE SET
            nonce_b64 = EXCLUDED.nonce_b64,
            encrypted_api_key_id_b64 = EXCLUDED.encrypted_api_key_id_b64,
            encrypted_private_key_b64 = EXCLUDED.encrypted_private_key_b64,
            demo_mode = EXCLUDED.demo_mode,
            rotated_at = %(now)s
        """,
        {
            "username": username,
            "nonce": cred.nonce_b64,
            "key_id": cred.encrypted_api_key_id_b64,
            "priv_key": cred.encrypted_private_key_b64,
            "demo": body.demo_mode,
            "now": datetime.now(timezone.utc),
        },
    )
    return {"status": "connected", "demo_mode": body.demo_mode, "balance_cents": balance_cents}


@router.get("/balance")
async def get_account_balance(authorization: Optional[str] = Header(None)):
    username = _current_username(authorization)
    client = _get_client_for_user(username)
    try:
        return {"balance_cents": get_balance_cents(client)}
    except KalshiClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/positions")
async def get_account_positions(authorization: Optional[str] = Header(None)):
    username = _current_username(authorization)
    client = _get_client_for_user(username)
    try:
        positions = get_positions(client)
        return {"positions": [p.to_dict() if hasattr(p, "to_dict") else p for p in positions]}
    except KalshiClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


def _run_detection_background(username: str):
    try:
        client = _get_client_for_user(username)
        candidates = detect_all_sports(client)
        saved = log_candidate_edges(candidates)
        logger.info("[kalshi.detect] %d candidates found, %d saved", len(candidates), saved)
    except Exception:
        logger.exception("[kalshi.detect] background detection run failed")


@router.post("/detect")
async def run_detection(background_tasks: BackgroundTasks, authorization: Optional[str] = Header(None)):
    """Scan every configured sport (see series_discovery.SPORT_SERIES_MAP) for
    moneyline mispricing and log candidates. Detect-only - never places an
    order. Runs in the background (a full scan takes longer than nginx's 30s
    /api proxy timeout) - poll GET /candidates for results."""
    username = _current_username(authorization)
    background_tasks.add_task(_run_detection_background, username)
    return {"status": "started", "message": "Scanning in background. Poll GET /api/kalshi/candidates for results."}


@router.get("/candidates")
async def list_candidates(
    sport: Optional[str] = None,  # e.g. "baseball_mlb"; omit or "all" for every sport
    only_our_picks: bool = False,  # only candidates whose game_id also has one of our own predictions
    authorization: Optional[str] = Header(None),
):
    username = _current_username(authorization)  # auth required even though data isn't user-scoped yet
    from pipeline.db.connection import execute_query

    where = []
    params: dict = {"username": username}
    if sport and sport != "all":
        where.append("e.sport = %(sport)s")
        params["sport"] = sport
    if only_our_picks:
        where.append("e.game_id IN (SELECT DISTINCT game_id FROM predictions WHERE game_id IS NOT NULL AND game_id != '')")
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    rows = execute_query(
        f"""
        SELECT e.*, o.status AS order_status, o.count AS order_contracts
        FROM kalshi_candidate_edges e
        LEFT JOIN kalshi_orders o ON o.candidate_edge_id = e.id AND o.username = %(username)s
        {where_sql}
        ORDER BY e.detected_at DESC LIMIT 50
        """,
        params,
    )
    # true_probability/raw_edge_pct/net_edge_pct/sharp_consensus_total/kalshi_strike are
    # Text columns (schema.py) - cast to float here so the API actually returns numbers,
    # matching what the frontend's TS interface already assumes. Left as string in the DB,
    # a real (non-empty) candidate row crashes the whole Kalshi page: fmtPct() calls
    # .toFixed() directly on the value, which throws on a string with no error boundary
    # to catch it.
    _numeric_fields = ("true_probability", "raw_edge_pct", "net_edge_pct", "sharp_consensus_total", "kalshi_strike")
    for row in rows:
        for field in _numeric_fields:
            if row.get(field) is not None:
                row[field] = float(row[field])
    return {"candidates": rows}


@router.get("/markets")
async def list_markets(
    sport: str,  # required, e.g. "baseball_mlb" - one series-fetch per sport, no "all" fan-out here
    authorization: Optional[str] = Header(None),
):
    """Browse view - every open Kalshi market for one sport, whether or not
    it clears the edge threshold. Unlike /detect + /candidates (which only
    ever surface qualifying mispricing candidates), this is what backs an
    "all games" table so the user can see full Kalshi coverage, not just
    what our detector flagged. Synchronous (single sport = 2 API calls,
    fast enough for nginx's proxy timeout) - unlike /detect's all-sport
    background scan."""
    username = _current_username(authorization)
    client = _get_client_for_user(username)
    try:
        return {"markets": list_markets_for_sport(client, sport)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except KalshiClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/sports")
async def list_supported_sports(authorization: Optional[str] = Header(None)):
    """Sport keys the candidates/detect endpoints support - drives the UI's
    sport filter dropdown so it never drifts out of sync with the backend."""
    _current_username(authorization)
    from kalshi.series_discovery import SPORT_SERIES_MAP
    return {"sports": list(SPORT_SERIES_MAP.keys())}


class ExecuteRequest(BaseModel):
    candidate_edge_id: int
    contracts: int = 1  # hard-capped server-side regardless of what's sent


@router.post("/execute")
async def execute_trade(body: ExecuteRequest, authorization: Optional[str] = Header(None)):
    """HITL confirm-and-place. The caller is the human confirmation - there is
    no separate approval step because reaching this endpoint IS the approval.
    Contract count is hard-capped at MAX_CONTRACTS_PER_TRADE inside
    execute_candidate_edge no matter what the caller requests."""
    username = _current_username(authorization)
    client = _get_client_for_user(username)
    try:
        result = execute_candidate_edge(client, username, body.candidate_edge_id, body.contracts)
        return result
    except ExecutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/disconnect")
async def disconnect_kalshi_account(authorization: Optional[str] = Header(None)):
    username = _current_username(authorization)
    from pipeline.db.connection import execute_write

    execute_write(
        "DELETE FROM kalshi_credentials WHERE username = %(username)s",
        {"username": username},
    )
    return {"status": "disconnected"}
