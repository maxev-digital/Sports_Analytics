"""
Sonnet-powered reasoning layer for the Sports Betting Analytics pipeline.

Provides narrative generation, confidence-tier classification, and daily
pick summaries using Claude Sonnet. All calls fail open with sensible
default text responses so the pipeline never crashes due to an LLM error.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic

from pipeline.config import ANTHROPIC_API_KEY, SONNET

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Fallback strings returned on any API or parse error
_DEFAULT_NARRATIVE = (
    "Model-generated edge detected. Review feature inputs for full context."
)
_DEFAULT_CONFIDENCE = "low"
_DEFAULT_SUMMARY = (
    "Daily picks generated. Confidence distribution across sports varies. "
    "Review individual pick narratives for detail."
)


def _strip_fences(text: str) -> str:
    """Strip markdown code fences from a Claude response."""
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def generate_pick_narrative(pick: dict, features: dict) -> str:
    """
    Generate a concise 2-3 sentence data-driven reasoning narrative for a pick.

    Explains why the model sees edge in quantitative terms: xERA vs ERA gap,
    bullpen fatigue, line movement signals, ATS trends, or other sabermetric
    or market-based factors present in ``features``.

    Args:
        pick:     Pick metadata dict — at minimum should contain team, sport,
                  pick_type, edge_pct, line, and odds.
        features: Feature values used by the model — e.g. xERA, barrel%,
                  line_movement, rest_days, ats_record_road_last_10.

    Returns:
        A 2-3 sentence string suitable for display to end users.
        Returns ``_DEFAULT_NARRATIVE`` on any API or parse error.
    """
    try:
        prompt = (
            f"Pick details:\n{json.dumps(pick, default=str)}\n\n"
            f"Key model features:\n{json.dumps(features, default=str)}\n\n"
            f"Write exactly 2-3 sentences explaining the data-driven edge for this pick. "
            f"Reference specific statistics and market signals from the feature set. "
            f"Be precise and analytical — no promotional language, no hedging."
        )

        response = client.messages.create(
            model=SONNET,
            max_tokens=250,
            system=(
                "You are a professional sports betting analyst with deep expertise in "
                "sabermetrics, sharp-money tracking, and market inefficiency detection. "
                "Generate terse, data-driven reasoning for model picks. "
                "Never make explicit betting recommendations — explain WHY the model "
                "identifies value given the provided features. "
                "Write in third person (e.g. 'The model identifies...'). "
                "Output plain prose only — no bullet points, no headers."
            ),
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        return text if text else _DEFAULT_NARRATIVE

    except anthropic.APIStatusError as exc:
        logger.error(
            "Sonnet API error generating pick narrative: HTTP %s – %s",
            exc.status_code,
            exc.message,
        )
        return _DEFAULT_NARRATIVE
    except anthropic.APIConnectionError as exc:
        logger.error("Sonnet connection error generating pick narrative: %s", exc)
        return _DEFAULT_NARRATIVE
    except Exception as exc:
        logger.error("Unexpected error in generate_pick_narrative: %s", exc)
        return _DEFAULT_NARRATIVE


def assess_confidence_tier(pick: dict, features: dict) -> str:
    """
    Classify a pick's confidence tier as 'high', 'medium', or 'low'.

    Guidance for classification:
    - high:   edge >= 6%, strong feature alignment, liquid market, tight line.
    - medium: edge 4-6%, mixed signals, thinner market, or moderate data gaps.
    - low:    edge 3-4%, conflicting features, illiquid market, or stale data.

    Args:
        pick:     Pick metadata dict.
        features: Model feature values.

    Returns:
        One of ``'high'``, ``'medium'``, or ``'low'``.
        Returns ``'low'`` on any API or parse error (conservative default).
    """
    try:
        prompt = (
            f"Pick:\n{json.dumps(pick, default=str)}\n\n"
            f"Features:\n{json.dumps(features, default=str)}\n\n"
            f"Classify the confidence level for this pick.\n"
            f"high   = edge >= 6%, strong feature alignment, liquid market\n"
            f"medium = edge 4-6%, mixed signals, or moderate data gaps\n"
            f"low    = edge 3-4%, conflicting features, or stale/thin data\n\n"
            f"Respond with EXACTLY one word: high, medium, or low."
        )

        response = client.messages.create(
            model=SONNET,
            max_tokens=10,
            system=(
                "You are a risk analyst evaluating sports betting pick quality. "
                "Respond with ONLY one of these three words: high, medium, low. "
                "No punctuation, no explanation."
            ),
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip().lower()

        # Exact match first
        if raw in ("high", "medium", "low"):
            return raw

        # Partial match fallback (handles "high." or "**high**" etc.)
        for tier in ("high", "medium", "low"):
            if tier in raw:
                return tier

        logger.warning(
            "assess_confidence_tier: unexpected response %r — defaulting to 'low'", raw
        )
        return _DEFAULT_CONFIDENCE

    except anthropic.APIStatusError as exc:
        logger.error(
            "Sonnet API error assessing confidence tier: HTTP %s – %s",
            exc.status_code,
            exc.message,
        )
        return _DEFAULT_CONFIDENCE
    except anthropic.APIConnectionError as exc:
        logger.error("Sonnet connection error assessing confidence tier: %s", exc)
        return _DEFAULT_CONFIDENCE
    except Exception as exc:
        logger.error("Unexpected error in assess_confidence_tier: %s", exc)
        return _DEFAULT_CONFIDENCE


def generate_daily_summary(picks: list[dict]) -> str:
    """
    Generate a 3-4 sentence analyst briefing for the day's full pick slate.

    Synthesizes cross-pick themes: dominant sports/markets, overall confidence
    distribution, notable line-value clusters, and any standout single plays.

    Args:
        picks: List of pick dicts for the day, each containing at minimum
               team, sport, pick_type, edge_pct, and confidence_tier.

    Returns:
        A 3-4 sentence plain-text summary for the daily briefing.
        Returns ``_DEFAULT_SUMMARY`` on any API error.
        Returns a short "no picks" message if the input list is empty.
    """
    if not picks:
        return "No picks generated for today."

    try:
        prompt = (
            f"Today's picks ({len(picks)} total):\n"
            f"{json.dumps(picks, default=str)}\n\n"
            f"Write a 3-4 sentence daily analyst briefing. Cover:\n"
            f"1. Dominant themes or edge sources across today's slate\n"
            f"2. Which sports or markets are showing the most model confidence\n"
            f"3. Overall risk posture (aggressive, moderate, conservative)\n"
            f"4. One standout play if any pick has an unusually high edge_pct\n\n"
            f"Be analytical and terse. No promotional language. No bullet points."
        )

        response = client.messages.create(
            model=SONNET,
            max_tokens=400,
            system=(
                "You are the head sports betting analyst for a quantitative betting platform. "
                "Write concise, data-driven daily briefings for professional bettors and "
                "institutional clients. Synthesize patterns across picks into actionable "
                "intelligence. Never recommend specific bets — summarize the analytical "
                "picture and confidence landscape. Plain prose only."
            ),
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        return text if text else _DEFAULT_SUMMARY

    except anthropic.APIStatusError as exc:
        logger.error(
            "Sonnet API error generating daily summary: HTTP %s – %s",
            exc.status_code,
            exc.message,
        )
        return _DEFAULT_SUMMARY
    except anthropic.APIConnectionError as exc:
        logger.error("Sonnet connection error generating daily summary: %s", exc)
        return _DEFAULT_SUMMARY
    except Exception as exc:
        logger.error("Unexpected error in generate_daily_summary: %s", exc)
        return _DEFAULT_SUMMARY
