"""
Referee context provider for the MAX EV Analyst agent.

Extracts a referee name from a user message (Haiku) then formats
their historical tendency data as a text block for injection into
the Sonnet system prompt when analyzing NFL games.
"""
from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

NFL_AVG_FLAGS = 14.5  # approximate league average flags/game


def _current_season() -> int:
    now = datetime.utcnow()
    return now.year if now.month >= 9 else now.year - 1


def _extract_referee_name(message: str) -> str | None:
    """Use Haiku to extract a referee name from the user message. Returns None on miss."""
    try:
        from pipeline.config import ANTHROPIC_API_KEY, HAIKU
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=HAIKU,
            max_tokens=50,
            system=(
                "Extract the NFL referee name from the user message. "
                "Return ONLY the full name (e.g. 'Brad Allen') or the word null. "
                "No markdown. No explanation."
            ),
            messages=[{"role": "user", "content": message}],
        )
        name = resp.content[0].text.strip()
        return None if name.lower() in ("null", "none", "") else name
    except Exception as exc:
        logger.warning("_extract_referee_name error: %s", exc)
        return None


def _fuzzy_match(extracted: str, known: list[str]) -> str | None:
    low = extracted.lower()
    for ref in known:
        if low in ref.lower() or ref.lower() in low:
            return ref
    return None


def get_referee_context_block(message: str) -> str:
    """
    Build a formatted context block describing the referee's tendencies.

    Designed for injection into the agent system prompt under
    '## Assigned Referee'. Returns empty string if no referee found.
    """
    try:
        extracted = _extract_referee_name(message)
        if not extracted:
            return ""

        from services.referee_stats import get_referee_list, get_referee_profile
        ref_list = get_referee_list(sort="games", min_games=5)
        known = [r.name for r in ref_list.referees]
        matched = _fuzzy_match(extracted, known)
        if not matched:
            logger.info("No DB match for extracted referee %r", extracted)
            return ""

        profile = get_referee_profile(matched)
        if not profile:
            return ""

        s = profile.summary
        lines: list[str] = [f"Referee: {s.name} ({s.games} career reg-season games, {s.tendency})"]

        if s.over_rate is not None:
            lines.append(
                f"O/U: {s.over_rate * 100:.1f}% over / {(s.under_rate or 0) * 100:.1f}% under"
                f" — avg combined total {s.avg_total or '—'}"
            )

        if s.home_cover_pct is not None:
            lines.append(f"Home cover rate: {s.home_cover_pct * 100:.1f}%")

        if s.flags_per_game is not None:
            diff = s.flags_per_game - NFL_AVG_FLAGS
            sign = "+" if diff >= 0 else ""
            lines.append(
                f"Flags: {s.flags_per_game:.1f}/game ({sign}{diff:.1f} vs NFL avg {NFL_AVG_FLAGS})"
            )

        if s.home_bias is not None:
            bias_label = (
                "home-heavy" if s.home_bias > 0.52 else
                "away-heavy" if s.home_bias < 0.48 else "neutral"
            )
            lines.append(
                f"Flag split: {s.home_bias * 100:.0f}% home / {(1 - s.home_bias) * 100:.0f}%"
                f" away ({bias_label})"
            )

        if s.ot_rate is not None and s.ot_rate > 0.05:
            lines.append(f"OT rate: {s.ot_rate * 100:.1f}%")

        # Game script implication
        if s.flags_per_game is not None and s.flags_per_game > NFL_AVG_FLAGS + 2:
            lines.append(
                "Game script note: High-flag ref slows pace and interrupts scoring momentum."
                " Lean under; fade teams reliant on tempo."
            )
        elif s.flags_per_game is not None and s.flags_per_game < NFL_AVG_FLAGS - 2:
            lines.append(
                "Game script note: Clean-game ref enables free-flowing offense."
                " Overs and pace-dependent teams get a slight lift."
            )

        return "\n".join(lines)

    except Exception as exc:
        logger.error("get_referee_context_block error: %s", exc)
        return ""
