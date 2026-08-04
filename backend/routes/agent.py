"""
Expert Sports Analyst Agent — API routes.

POST /api/v1/agent/chat        — freeform conversational Q&A with MAX EV Analyst
POST /api/v1/agent/chat/stream — streaming SSE version
POST /api/v1/agent/picks       — top pending picks for the proactive widget panel
"""

from collections import defaultdict
from datetime import datetime
from time import time as _time
from typing import Optional, Generator
import json
import logging

import anthropic
import pytz
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth import verify_session
from pipeline.config import ANTHROPIC_API_KEY, SONNET

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])
CST = pytz.timezone("America/Chicago")

# Module-level Anthropic client — one instance shared across all requests
_anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# In-memory sliding-window rate limiter (20 req/min per user)
_RATE_WINDOW = 60.0
_RATE_MAX = 20
_rate_buckets: dict[str, list[float]] = defaultdict(list)


def _require_session(authorization: Optional[str] = None) -> str:
    """Validate platform Bearer token. Returns username or raises 401."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.removeprefix("Bearer ")
    username = verify_session(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return username


def _check_rate(username: str) -> None:
    """Sliding-window rate limit: 20 requests per 60 seconds per user."""
    now = _time()
    _rate_buckets[username] = [t for t in _rate_buckets[username] if now - t < _RATE_WINDOW]
    if len(_rate_buckets[username]) >= _RATE_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait before sending more requests.")
    _rate_buckets[username].append(now)


# ── Request / Response models ────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    game_id: Optional[str] = None
    history: list[Message] = Field(default_factory=list)


class ChatResponse(BaseModel):
    response: str
    tool_calls_made: list[str]
    sources: list[str]
    generated_at: str


class PicksRequest(BaseModel):
    sport: Optional[str] = None
    limit: int = Field(default=5, ge=1, le=10)


class PickCard(BaseModel):
    id: int
    sport: str
    home_team: str
    away_team: str
    pick_side: Optional[str] = None
    pick_type: Optional[str] = None
    edge_pct: float
    confidence_tier: str
    market_odds: int
    ml_confidence_pct: float
    kelly_units: float
    detector: str
    narrative: str
    total_line: Optional[float] = None
    game_time_cst: Optional[str] = None


class PicksResponse(BaseModel):
    picks: list[PickCard]
    count: int
    generated_at: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
def agent_chat(req: ChatRequest, authorization: Optional[str] = Header(None)):
    """Freeform conversational Q&A with the MAX EV Analyst agent."""
    username = _require_session(authorization)
    _check_rate(username)
    try:
        from services.agent_service import chat
        result = chat(
            message=req.message,
            history=[h.model_dump() for h in req.history],
            game_id=req.game_id,
        )
        return ChatResponse(
            response=result["response"],
            tool_calls_made=result.get("tool_calls_made", []),
            sources=result.get("sources", []),
            generated_at=datetime.now(CST).isoformat(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("agent_chat endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Agent temporarily unavailable.")


@router.post("/chat/stream")
def agent_chat_stream(req: ChatRequest, authorization: Optional[str] = Header(None)):
    """
    Streaming SSE version of agent chat.
    Emits: data: {"text": "..."} per token, then data: [DONE]
    """
    username = _require_session(authorization)
    _check_rate(username)

    def generate() -> Generator[str, None, None]:
        try:
            from services.agent_service import (
                classify_intent, assemble_rag_context, AGENT_SYSTEM_PROMPT
            )
            intent = classify_intent(req.message)
            rag = assemble_rag_context(sport=intent.get("sport"), game_id=req.game_id)
            user_content = f"PLATFORM CONTEXT:\n{rag}\n\nUSER QUESTION:\n{req.message}"

            messages = []
            for h in req.history[-8:]:
                if h.role in ("user", "assistant") and h.content:
                    messages.append({"role": h.role, "content": h.content})
            messages.append({"role": "user", "content": user_content})

            with _anthropic_client.messages.stream(
                model=SONNET,
                max_tokens=600,
                system=AGENT_SYSTEM_PROMPT,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text})}\n\n"

        except Exception as exc:
            logger.error("agent_chat_stream error: %s", exc)
            yield f"data: {json.dumps({'text': 'The analysis engine encountered an error. Please try again.'})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/picks", response_model=PicksResponse)
def agent_picks(req: PicksRequest, authorization: Optional[str] = Header(None)):
    """Return top pending picks formatted as PickCards for the proactive widget."""
    username = _require_session(authorization)
    _check_rate(username)
    try:
        from services.agent_service import get_top_picks
        picks = get_top_picks(sport=req.sport, limit=req.limit)
        return PicksResponse(
            picks=[PickCard(**p) for p in picks],
            count=len(picks),
            generated_at=datetime.now(CST).isoformat(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("agent_picks endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Picks temporarily unavailable.")
