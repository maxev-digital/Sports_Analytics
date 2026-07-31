"""
Two-agent news/injury intelligence analyzer.

Agent 1 (Haiku)  — fast classifier: sport, player, severity, market impact.
Agent 2 (Sonnet) — betting analyst: which market, direction, edge, reasoning.

Both fail open; errors return safe empty dicts, never raise.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic

from pipeline.config import ANTHROPIC_API_KEY, HAIKU, SONNET

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ---------------------------------------------------------------------------
# JSON helpers (copied from haiku_validator pattern)
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    text = text.strip()
    if not text.startswith(("{", "[")):
        m = re.search(r"[\{\[]", text)
        if m:
            text = text[m.start():]
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("“", '"').replace("”", '"')
    try:
        return json.loads(text)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Agent 1: Haiku classifier
# ---------------------------------------------------------------------------

_CLASSIFY_SYSTEM = """You are a sports news classifier for a betting analytics platform.
Given a news headline and summary, return ONLY a JSON object — no prose, no markdown fences.

Required fields:
{
  "sport": "mlb" | "nba" | "nfl" | "nhl" | "wnba" | "other",
  "news_type": "injury" | "lineup" | "trade" | "suspension" | "weather" | "general",
  "severity": "out" | "limited" | "probable" | "doubtful" | "day_to_day" | "none",
  "players": ["Player Name", ...],
  "teams_affected": ["Team Name", ...],
  "betting_relevance": "high" | "medium" | "low" | "none",
  "markets_affected": ["moneyline", "spread", "total", "props"],
  "direction_hint": "favor_team" | "fade_team" | "lower_total" | "higher_total" | "props_play" | "unclear",
  "one_line": "One sentence summary of betting implication"
}

Severity guide:
- out: confirmed out for game(s), placed on IL/injured reserve
- limited: practicing limited, game-time decision
- probable: listed as probable, expected to play
- doubtful: listed as doubtful
- day_to_day: day-to-day, short-term uncertainty
- none: not an injury or lineup item

Betting relevance guide:
- high: star player out, major lineup change, significant weather
- medium: rotation player, backup starter, secondary weather effect
- low: minor news, practice squad move
- none: transaction, award, schedule note with no betting impact"""


def classify_news(headline: str, summary: str) -> dict[str, Any]:
    """Run Haiku classification on a news item. Returns empty dict on failure."""
    try:
        resp = client.messages.create(
            model=HAIKU,
            max_tokens=512,
            system=_CLASSIFY_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"Headline: {headline}\n\nSummary: {summary or 'No summary available.'}"
            }]
        )
        return _extract_json(resp.content[0].text)
    except Exception as e:
        logger.warning("Haiku classification failed: %s", e)
        return {}


# ---------------------------------------------------------------------------
# Agent 2: Sonnet betting analyst
# ---------------------------------------------------------------------------

_ANALYZE_SYSTEM = """You are a sharp sports bettor and analyst. You receive a classified news item
plus current odds for the affected teams. Produce a betting analysis as ONLY a JSON object.

Required fields:
{
  "headline_summary": "Brief restatement of what happened",
  "bet_type": "moneyline" | "spread" | "total" | "props" | "avoid" | "monitor",
  "direction": "home" | "away" | "over" | "under" | "player_over" | "player_under" | "none",
  "target_team": "Team name or player name, or null",
  "confidence": "high" | "medium" | "low",
  "edge_estimate": "e.g. '+3 to +5%' or 'unknown'",
  "reasoning": "2-4 sentences: why this news creates a market edge",
  "contrarian_risk": "1-2 sentences: biggest reason NOT to bet this",
  "time_sensitivity": "immediate" | "pre-game" | "next_game" | "season-long",
  "key_factors": ["factor1", "factor2", "factor3"],
  "recommended_action": "BET NOW" | "MONITOR" | "AVOID" | "WAIT FOR LINE"
}

Be conservative. Only recommend "BET NOW" when the edge is clear and the news is likely
NOT yet fully priced in. Recency of news matters — breaking news has more edge.
If odds data is empty, still analyze but note the uncertainty."""


def analyze_betting_angle(
    headline: str,
    summary: str,
    classification: dict,
    odds_context: str = "",
) -> dict[str, Any]:
    """Run Sonnet deep betting analysis. Returns empty dict on failure."""
    try:
        user_msg = f"""News Item:
Headline: {headline}
Summary: {summary or 'No summary.'}

Classification:
{json.dumps(classification, indent=2)}

Current odds context:
{odds_context or 'No odds data available for affected teams.'}

Provide your betting analysis."""

        resp = client.messages.create(
            model=SONNET,
            max_tokens=1024,
            system=_ANALYZE_SYSTEM,
            messages=[{"role": "user", "content": user_msg}]
        )
        return _extract_json(resp.content[0].text)
    except Exception as e:
        logger.warning("Sonnet analysis failed: %s", e)
        return {}
