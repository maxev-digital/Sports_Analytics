"""
Referee analysis tool for the MAX EV Analyst agent.

Returns a structured summary of a referee's historical tendencies
for use in game script and betting analysis.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

NFL_AVG_FLAGS = 14.5


def get_referee_analysis(referee_name: str) -> dict:
    """
    Look up a referee by name and return their tendency profile.

    Args:
        referee_name: Full or partial referee name (e.g. 'Brad Allen', 'Allen').

    Returns:
        dict with: referee, found, tendency_summary, betting_context,
                   games, tendency (when found).
    """
    try:
        from services.referee_stats import get_referee_list, get_referee_profile

        # Exact match first
        profile = get_referee_profile(referee_name)

        # Fuzzy match if exact miss
        if profile is None:
            ref_list = get_referee_list(sort="games", min_games=5)
            name_low = referee_name.lower()
            matched = next(
                (r.name for r in ref_list.referees if name_low in r.name.lower()),
                None,
            )
            if matched:
                profile = get_referee_profile(matched)

        if profile is None:
            return {
                "referee": referee_name,
                "found": False,
                "tendency_summary": f"No data found for referee '{referee_name}'.",
                "betting_context": "",
            }

        s = profile.summary
        parts = [f"{s.name}: {s.games} games — {s.tendency}"]

        if s.over_rate is not None:
            parts.append(
                f"O/U: {s.over_rate * 100:.1f}% over / {(s.under_rate or 0) * 100:.1f}%"
                f" under (avg total {s.avg_total})"
            )

        if s.home_cover_pct is not None:
            parts.append(f"Home cover: {s.home_cover_pct * 100:.1f}%")

        if s.flags_per_game is not None:
            diff = s.flags_per_game - NFL_AVG_FLAGS
            parts.append(
                f"Flags: {s.flags_per_game:.1f}/game ({'+'if diff>=0 else ''}{diff:.1f} vs avg)"
            )
            if s.home_bias is not None:
                bias = (
                    "home-heavy" if s.home_bias > 0.52 else
                    "away-heavy" if s.home_bias < 0.48 else "neutral flag split"
                )
                parts.append(f"Flag bias: {bias} ({s.home_bias * 100:.0f}% on home team)")

        context_parts: list[str] = []
        if s.over_rate is not None and s.over_rate >= 0.58:
            context_parts.append("Strong over tendency — upgrade totals plays in the over direction.")
        elif s.over_rate is not None and s.over_rate <= 0.42:
            context_parts.append("Strong under tendency — downgrade overs, look for lower-scoring spots.")

        if s.flags_per_game is not None and s.flags_per_game > NFL_AVG_FLAGS + 2:
            context_parts.append(
                "High-flag ref: penalties break up drives and slow pace. Underdog cover rate typically improves."
            )
        elif s.flags_per_game is not None and s.flags_per_game < NFL_AVG_FLAGS - 2:
            context_parts.append("Low-flag ref: clean game flow boosts scoring opportunities for pace teams.")

        if s.home_cover_pct is not None and s.home_cover_pct >= 0.58:
            context_parts.append("Home teams cover at an elevated rate under this official.")

        return {
            "referee": s.name,
            "found": True,
            "tendency_summary": " | ".join(parts),
            "betting_context": " ".join(context_parts) if context_parts else "No strong tendency signal.",
            "games": s.games,
            "tendency": s.tendency,
            "over_rate": s.over_rate,
            "home_cover_pct": s.home_cover_pct,
            "flags_per_game": s.flags_per_game,
        }

    except Exception as exc:
        logger.error("get_referee_analysis error: %s", exc)
        return {
            "referee": referee_name,
            "found": False,
            "tendency_summary": "Referee analysis temporarily unavailable.",
            "betting_context": "",
        }
