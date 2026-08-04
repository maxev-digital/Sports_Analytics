"""
Expert Sports Analyst Agent — orchestration layer.

Phase 1: Haiku intent classification + RAG context assembly + Sonnet response.
Phase 3 will wire in live data tool execution (injury/lineup/weather/news).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any

import anthropic
import pytz

from pipeline.config import ANTHROPIC_API_KEY, HAIKU, SONNET

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
CST = pytz.timezone("America/Chicago")

AGENT_SYSTEM_PROMPT = """You are MAX EV Analyst, the expert sports betting analyst built into the MAX EV platform.

You have access to:
- Live game data, current betting lines, and odds from all major sportsbooks
- Proprietary ML model projections (60 models: RF, XGBoost, LightGBM)
- Proven edge signals (statistically validated, p<0.05, +11.2% ROI on F5 MLB backtests)
- Platform predictions with edge percentages and confidence tiers

When recommending a bet, use this format:
  [TEAM/SIDE] [MARKET] — Edge: X.X% | Confidence: [tier] | Kelly: X.X units
  Why: [2-3 sentences citing the specific data source and model signal]

Rules:
- Always cite the edge source (ML model, F5 signal, line value, situational)
- Show Kelly unit sizing when our_probability > 50%
- Be direct — users are here for actionable intelligence, not disclaimers
- Acknowledge when data is unavailable rather than guessing
- Never use markdown headers (###, ##, #) — plain text and dashes only"""


def _extract_json_safe(text: str) -> dict[str, Any]:
    """Extract JSON from a Claude response. Returns empty dict on any failure."""
    try:
        text = text.strip()
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        m = re.search(r"\{", text)
        if m:
            text = text[m.start():]
        return json.loads(text)  # type: ignore[return-value]
    except Exception:
        return {}


def classify_intent(message: str) -> dict[str, Any]:
    """
    Use Haiku to classify user intent and extract routing metadata.

    Returns:
        sport (str|None), needs_live_data (bool), is_bet_question (bool),
        is_game_analysis (bool) — True when user wants a full game breakdown/write-up.
    Fails open with safe defaults on any API error.
    """
    try:
        prompt = (
            f"User message: {message!r}\n\n"
            "Return ONLY this JSON (fill in values):\n"
            '{"sport": "nba|nfl|mlb|nhl|ncaaf|ncaab|wnba|tennis|mma|null", '
            '"needs_live_data": false, "is_bet_question": true, "is_game_analysis": false}'
        )
        resp = client.messages.create(
            model=HAIKU,
            max_tokens=100,
            system=(
                "Classify a sports betting platform user message. "
                "sport: the sport mentioned or the string null. "
                "needs_live_data: true if asking about injuries, lineups, weather, or breaking news. "
                "is_bet_question: true if asking for a recommendation or analysis. "
                "is_game_analysis: true if the user wants a full game breakdown, write-up, handicap, "
                "or analysis of a specific matchup (e.g. 'break down Chiefs vs Eagles', "
                "'handicap the Lakers game', 'give me a write-up on tonight\\'s Dodgers game'). "
                "Return ONLY valid JSON. No markdown. No explanation."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        result = _extract_json_safe(resp.content[0].text)
        sport = result.get("sport")
        is_game_analysis = bool(result.get("is_game_analysis", False))
        return {
            "sport": sport if sport and sport != "null" else None,
            # game analysis always routes through the tool loop (needs get_game_script)
            "needs_live_data": bool(result.get("needs_live_data", False)) or is_game_analysis,
            "is_bet_question": bool(result.get("is_bet_question", True)),
            "is_game_analysis": is_game_analysis,
        }
    except anthropic.APIStatusError as exc:
        logger.warning("classify_intent API error %s: %s", exc.status_code, exc.message)
        return {"sport": None, "needs_live_data": False, "is_bet_question": True, "is_game_analysis": False}
    except Exception as exc:
        logger.warning("classify_intent error: %s", exc)
        return {"sport": None, "needs_live_data": False, "is_bet_question": True, "is_game_analysis": False}


def _db_rows(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    from pipeline.db.connection import execute_query
    return execute_query(sql, params)


def _db_write(sql: str, params: tuple = ()) -> int:
    from pipeline.db.connection import execute_write
    return execute_write(sql, params)


def assemble_rag_context(sport: str | None = None, game_id: str | None = None) -> str:
    """
    Pull relevant context from the platform DB for the agent response.

    Returns a formatted string block. Returns a fallback message on any DB error.
    """
    try:
        today = datetime.now(CST).strftime("%Y-%m-%d")
        parts: list[str] = []

        sport_clause = "AND LOWER(sport) = LOWER(%s)" if sport else ""
        params: list[Any] = [today, today]
        if sport:
            params.append(sport)
        params.append(10)

        picks = _db_rows(
            f"""
            SELECT sport, home_team, away_team, pick_side, pick_type,
                   edge_pct, confidence_tier, market_odds, our_probability,
                   detector, sonnet_narrative, total_line
            FROM predictions
            WHERE status IN ('pending', 'needs_review')
              AND (game_time_cst::date = %s OR created_at_cst::date = %s)
              AND edge_pct >= 3.0
              {sport_clause}
            ORDER BY edge_pct DESC
            LIMIT %s
            """,
            tuple(params),
        )

        if picks:
            parts.append("=== TODAY'S MODEL PICKS (by edge) ===")
            for pk in picks:
                side = (pk.get("pick_side") or "").upper()
                ptype = (pk.get("pick_type") or "").upper()
                conf = (pk.get("confidence_tier") or "low").upper()
                prob = float(pk.get("our_probability") or 0) * 100
                line = (
                    f"{(pk['sport'] or '').upper()} | "
                    f"{pk['away_team']} @ {pk['home_team']} | "
                    f"{side} {ptype} | Edge: +{pk['edge_pct']:.1f}% | "
                    f"Conf: {conf} | Odds: {pk['market_odds']:+d} | Our P: {prob:.1f}%"
                )
                if pk.get("total_line"):
                    line += f" | Total: {pk['total_line']}"
                parts.append(line)
                if pk.get("sonnet_narrative"):
                    parts.append(f"  Analysis: {pk['sonnet_narrative'][:220]}")
            parts.append("")

        record = _db_rows(
            """
            SELECT
              COUNT(*) FILTER (WHERE status='win')  AS wins,
              COUNT(*) FILTER (WHERE status='loss') AS losses,
              COUNT(*) FILTER (WHERE status='push') AS pushes,
              ROUND(SUM(pl_units)::numeric, 2)      AS total_pl
            FROM predictions
            WHERE status IN ('win','loss','push')
              AND created_at_cst >= now() - INTERVAL '7 days'
            """
        )
        if record:
            r = record[0]
            w = int(r.get("wins") or 0)
            l = int(r.get("losses") or 0)
            push = int(r.get("pushes") or 0)
            pl = float(r.get("total_pl") or 0)
            wr = f"{w / (w + l) * 100:.1f}%" if (w + l) > 0 else "N/A"
            parts.append("=== PLATFORM RECORD (last 7 days) ===")
            parts.append(f"Record: {w}-{l}-{push} ({wr} ATS) | P&L: {pl:+.2f} units")
            parts.append("")

        return "\n".join(parts) if parts else "No picks in the DB for today."

    except Exception as exc:
        logger.error("assemble_rag_context error: %s", exc)
        return "Platform data temporarily unavailable."


def _run_tool_loop(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    system: str = AGENT_SYSTEM_PROMPT,
) -> tuple[str, list[str]]:
    """
    Execute a Sonnet tool-use loop until the model stops calling tools.

    Returns: (final_response_text, list_of_tool_names_called).
    Raises on API errors (caller handles).
    """
    from tools.tool_registry import execute_tool

    tool_names_called: list[str] = []
    current_messages = list(messages)

    for _ in range(5):  # max 5 tool-call rounds
        resp = client.messages.create(
            model=SONNET,
            max_tokens=700,
            system=system,
            tools=tools,
            messages=current_messages,
        )

        # Check stop reason
        if resp.stop_reason == "end_turn":
            text = next(
                (b.text for b in resp.content if hasattr(b, "text")),
                "",
            )
            return text.strip(), tool_names_called

        if resp.stop_reason != "tool_use":
            # Unexpected stop — return whatever text is present
            text = next((b.text for b in resp.content if hasattr(b, "text")), "")
            return text.strip(), tool_names_called

        # Process tool calls
        tool_results: list[dict[str, Any]] = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            tool_names_called.append(block.name)
            result = execute_tool(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, default=str),
            })

        # Append assistant turn + tool results
        current_messages.append({"role": "assistant", "content": resp.content})
        current_messages.append({"role": "user", "content": tool_results})

    # Fallback after max rounds
    text = next((b.text for b in resp.content if hasattr(b, "text")), "")  # type: ignore[possibly-undefined]
    return text.strip(), tool_names_called


def chat(
    message: str,
    history: list[dict[str, str]],
    game_id: str | None = None,
) -> dict[str, Any]:
    """
    Main agent chat handler.

    Haiku classifies intent -> RAG context assembled -> Sonnet responds.
    If Haiku flags needs_live_data, Sonnet runs with tool access (injury/lineup/weather/news).
    Returns: response (str), sources (list), intent (dict), tool_calls_made (list).
    Always returns a valid dict — fails open with an error message.
    """
    try:
        intent = classify_intent(message)
        rag = assemble_rag_context(sport=intent.get("sport"), game_id=game_id)

        system_prompt = AGENT_SYSTEM_PROMPT
        if intent.get("sport") == "nfl" and intent.get("is_game_analysis"):
            try:
                from services.referee_context_provider import get_referee_context_block
                ref_ctx = get_referee_context_block(message)
                if ref_ctx:
                    system_prompt = f"{AGENT_SYSTEM_PROMPT}\n\n## Assigned Referee\n{ref_ctx}"
            except Exception as ref_exc:
                logger.warning("referee context error: %s", ref_exc)

        user_content = f"PLATFORM CONTEXT:\n{rag}\n\nUSER QUESTION:\n{message}"

        messages: list[dict[str, Any]] = []
        for h in history[-8:]:
            role = h.get("role", "")
            content = h.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_content})

        sources = ["platform_predictions", "db_7day_record"]
        if intent.get("sport"):
            sources.append(f"sport_filter:{intent['sport']}")

        if intent.get("needs_live_data"):
            from tools.tool_registry import TOOLS
            response_text, tool_names = _run_tool_loop(messages, TOOLS, system=system_prompt)
            for tn in tool_names:
                sources.append(f"live:{tn}")
        else:
            resp = client.messages.create(
                model=SONNET,
                max_tokens=600,
                system=system_prompt,
                messages=messages,
            )
            response_text = resp.content[0].text.strip()
            tool_names = []

        return {
            "response": response_text,
            "sources": sources,
            "intent": intent,
            "tool_calls_made": tool_names,
        }

    except anthropic.APIStatusError as exc:
        logger.error("Sonnet API error in agent chat: HTTP %s — %s", exc.status_code, exc.message)
        return {
            "response": "The analysis engine is temporarily unavailable. Please try again in a moment.",
            "sources": [], "intent": {}, "tool_calls_made": [],
        }
    except Exception as exc:
        logger.error("Unexpected error in agent chat: %s", exc)
        return {
            "response": "An unexpected error occurred. Please try again.",
            "sources": [], "intent": {}, "tool_calls_made": [],
        }


def verify_pick_with_opus(pick: dict[str, Any]) -> dict[str, Any]:
    """
    Use Opus to verify a high-confidence pick. Only called for kelly_units > 0.05.

    Returns: {verdict: "PASS"|"HOLD", reasoning: str}
    Defaults to PASS on any API error (fail open).
    """
    from pipeline.config import OPUS
    try:
        prompt = (
            f"Pick summary:\n"
            f"  Sport: {pick.get('sport')}\n"
            f"  Matchup: {pick.get('away_team')} @ {pick.get('home_team')}\n"
            f"  Recommendation: {pick.get('pick_side')} {pick.get('pick_type')}\n"
            f"  Edge: +{pick.get('edge_pct', 0):.1f}%\n"
            f"  Model confidence: {pick.get('ml_confidence_pct', 0):.1f}%\n"
            f"  Kelly size: {pick.get('kelly_units', 0):.3f} units\n"
            f"  Signal: {pick.get('detector')}\n\n"
            f"Should this pick be surfaced to users with high confidence? "
            f"Reply with PASS or HOLD and one sentence of reasoning."
        )
        resp = client.messages.create(
            model=OPUS,
            max_tokens=100,
            system=(
                "You are a senior betting risk officer auditing a high-confidence model pick. "
                "PASS if the edge and confidence are consistent with the signal source. "
                "HOLD if the edge seems inflated, the signal is unreliable, or data quality is suspect. "
                "Reply with exactly: PASS: <reason> or HOLD: <reason>."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        verdict = "PASS" if raw.upper().startswith("PASS") else "HOLD" if raw.upper().startswith("HOLD") else "PASS"
        return {"verdict": verdict, "reasoning": raw}
    except Exception as exc:
        logger.warning("verify_pick_with_opus error: %s", exc)
        return {"verdict": "PASS", "reasoning": "Verification unavailable — defaulting to PASS."}


def get_top_picks(sport: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
    """
    Fetch top pending picks from the DB, formatted as PickCards for the proactive widget.

    Returns empty list on any error (fail open).
    """
    try:
        today = datetime.now(CST).strftime("%Y-%m-%d")
        sport_clause = "AND LOWER(sport) = LOWER(%s)" if sport else ""
        params: list[Any] = [today, today]
        if sport:
            params.append(sport)
        params.append(limit)

        rows = _db_rows(
            f"""
            SELECT id, sport, home_team, away_team, pick_side, pick_type,
                   edge_pct, confidence_tier, market_odds, our_probability,
                   detector, sonnet_narrative, total_line, game_time_cst,
                   opus_verdict, opus_reasoning
            FROM predictions
            WHERE status IN ('pending', 'needs_review')
              AND (game_time_cst::date = %s OR created_at_cst::date = %s)
              AND edge_pct >= 3.0
              {sport_clause}
            ORDER BY
              CASE confidence_tier WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
              edge_pct DESC
            LIMIT %s
            """,
            tuple(params),
        )

        picks: list[dict[str, Any]] = []
        for r in rows:
            our_prob = float(r.get("our_probability") or 0)
            kelly = round(max(0.0, (our_prob - (1 - our_prob)) * 0.25), 3) if our_prob > 0.5 else 0.0
            gt = r.get("game_time_cst")
            picks.append({
                "id": r["id"],
                "sport": (r.get("sport") or "").upper(),
                "home_team": r.get("home_team") or "",
                "away_team": r.get("away_team") or "",
                "pick_side": r.get("pick_side"),
                "pick_type": r.get("pick_type"),
                "edge_pct": float(r.get("edge_pct") or 0),
                "confidence_tier": r.get("confidence_tier") or "low",
                "market_odds": int(r.get("market_odds") or 0),
                "ml_confidence_pct": round(our_prob * 100, 1),
                "kelly_units": kelly,
                "detector": r.get("detector") or "",
                "narrative": r.get("sonnet_narrative") or "",
                "total_line": r.get("total_line"),
                "game_time_cst": gt.isoformat() if gt else None,
            })

        # Opus verification: only for the top pick if kelly_units > 0.05
        # Cached in DB — runs once per pick, not on every API call
        if picks and picks[0].get("kelly_units", 0) > 0.05:
            top = picks[0]
            cached_verdict = top.get("opus_verdict")

            if not cached_verdict:
                verification = verify_pick_with_opus(top)
                verdict = verification["verdict"]
                reasoning = verification["reasoning"]
                try:
                    _db_write(
                        "UPDATE predictions SET opus_verdict = %s, opus_reasoning = %s WHERE id = %s",
                        (verdict, reasoning, top["id"]),
                    )
                except Exception as write_exc:
                    logger.warning("Failed to cache opus_verdict for pick %d: %s", top["id"], write_exc)
                picks[0]["opus_verdict"] = verdict
                picks[0]["opus_reasoning"] = reasoning
                logger.info(
                    "Opus %s on pick %d (%s @ %s)",
                    verdict, top["id"], top["away_team"], top["home_team"],
                )
            else:
                verdict = cached_verdict

            # Demote confidence tier if Opus issued HOLD
            if verdict == "HOLD":
                picks[0]["confidence_tier"] = "medium"

        return picks

    except Exception as exc:
        logger.error("get_top_picks error: %s", exc)
        return []
