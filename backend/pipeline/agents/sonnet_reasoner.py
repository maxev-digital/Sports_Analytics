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


# ── Game Script Agent ─────────────────────────────────────────────────────────

_GAME_SCRIPT_SYSTEM = """You are a professional sports handicapper writing a full game analysis for a subscription pick service. Your style matches the best in the business — data-rich but readable, grounded in coaching tendencies and scheme matchups, with a clear game-script projection that tells subscribers exactly what they should expect to see on the field.

Write in first person ("I'm taking...", "I like...", "Watch for...").
Structure: open with your conviction and the key angle → scheme/coaching matchup → efficiency metrics and model data → line movement read → situational spot → ATS trends → injury impact (if relevant) → game script projection → closing statement.
End every write-up with "Thanks & GL!" on its own line.
Write 400-700 words of flowing prose. No bullet points. No headers. No markdown.
Be specific — cite actual numbers from the data provided.
If data is sparse for a sport, lean on scheme and situational reasoning."""

_GAME_SCRIPT_DEFAULT = (
    "Our model has identified edge on this game based on multibook vig removal. "
    "The consensus line diverges from what at least one book is offering, creating "
    "a measurable inefficiency. Full game script analysis will be available once "
    "our Expert Handicapper Agent processes the complete context package. "
    "Thanks & GL!"
)


def _fmt_spread(n: float | None) -> str:
    if n is None:
        return "PK"
    return f"+{n}" if n > 0 else str(n)


def _build_game_context(enriched: dict) -> str:
    """Build the context block passed to the LLM from enriched pick data."""
    home = enriched.get("home_team", "Home")
    away = enriched.get("away_team", "Away")
    sport = enriched.get("sport", "").upper()
    game_time = enriched.get("game_time_cst", "TBD")
    pick_side = enriched.get("pick_side", "")
    pick_type = enriched.get("pick_type", "")
    edge_pct = enriched.get("edge_pct", 0)
    our_prob = enriched.get("our_probability", 0)
    mkt_prob = enriched.get("market_implied_prob", 0)
    mkt_odds = enriched.get("market_odds", 0)
    conf = (enriched.get("confidence_tier") or "low").upper()
    detector = enriched.get("detector", "")

    snaps = enriched.get("line_snapshots") or []
    open_snap = snaps[0] if snaps else {}
    cur_snap = snaps[-1] if snaps else {}

    home_r = enriched.get("home_rating") or {}
    away_r = enriched.get("away_rating") or {}
    h2h = enriched.get("h2h") or []
    home_ats = enriched.get("home_ats") or {}
    away_ats = enriched.get("away_ats") or {}
    home_inj = enriched.get("home_injuries") or []
    away_inj = enriched.get("away_injuries") or []

    # Derive pick label
    spread_home = cur_snap.get("spread_home")
    total_line = cur_snap.get("total_line") or enriched.get("total_line")
    if pick_type in ("h2h", "moneyline", "ml"):
        pick_label = f"{home if pick_side == 'home' else away} ML"
    elif pick_type in ("totals", "total"):
        dir_ = "OVER" if pick_side == "over" else "UNDER"
        pick_label = f"{dir_} {total_line or '?'}"
    else:
        team = home if pick_side == "home" else away
        if spread_home is not None:
            raw = spread_home if pick_side == "home" else -spread_home
            pick_label = f"{team} {_fmt_spread(raw)}"
        else:
            pick_label = f"{team} (spread)"

    lines = [
        f"SPORT: {sport}",
        f"MATCHUP: {away} @ {home}",
        f"GAME TIME: {game_time}",
        f"OUR PICK: {pick_label} at {'+' if mkt_odds >= 0 else ''}{mkt_odds}",
        f"EDGE: +{edge_pct:.2f}% | CONFIDENCE: {conf}",
        f"OUR PROBABILITY: {our_prob*100:.1f}% vs MARKET IMPLIED: {mkt_prob*100:.1f}%",
        f"SIGNAL: {detector}",
        "",
    ]

    # Line movement
    if cur_snap:
        home_short = home.split()[-1]
        away_short = away.split()[-1]
        s = cur_snap.get("spread_home")
        t = cur_snap.get("total_line")
        hml = cur_snap.get("home_ml")
        aml = cur_snap.get("away_ml")
        books = cur_snap.get("books_sampled")
        lines += [
            "CURRENT LINE:",
            f"  Spread: {home_short} {_fmt_spread(s)} / {away_short} {_fmt_spread(-s if s else None)}",
            f"  Total: {t or '—'}",
            f"  Moneyline: {home_short} {'+' if (hml or 0)>=0 else ''}{hml or '—'} / {away_short} {'+' if (aml or 0)>=0 else ''}{aml or '—'}",
            f"  Books sampled: {books or '—'}",
        ]
        if open_snap and open_snap.get("id") != cur_snap.get("id"):
            os_ = open_snap.get("spread_home")
            ot = open_snap.get("total_line")
            ohml = open_snap.get("home_ml")
            oaml = open_snap.get("away_ml")
            lines += [
                "OPENING LINE:",
                f"  Spread: {home_short} {_fmt_spread(os_)} / Total: {ot or '—'} / ML: {ohml or '—'}/{oaml or '—'}",
            ]
            if s != os_:
                lines.append(f"  MOVEMENT: Spread moved {_fmt_spread(os_)} → {_fmt_spread(s)}")
            elif hml != ohml:
                lines.append(f"  MOVEMENT: Juice drift {ohml}/{oaml} → {hml}/{aml} (spread stable, public loading)")
            else:
                lines.append("  MOVEMENT: Line stable since open")
        lines.append("")

    # Power ratings
    if home_r or away_r:
        is_ncaaf = sport == "NCAAF"
        lines.append("POWER RATINGS:")
        if is_ncaaf:
            lines.append(f"  {home}: SP+ {home_r.get('sp_rating', '—')} (OFF {home_r.get('sp_offense', '—')} / DEF {home_r.get('sp_defense', '—')})")
            lines.append(f"  {away}: SP+ {away_r.get('sp_rating', '—')} (OFF {away_r.get('sp_offense', '—')} / DEF {away_r.get('sp_defense', '—')})")
        else:
            def pct(v):
                return f"{v:+.1f}%" if v is not None else "—"
            lines.append(f"  {home}: Power {home_r.get('power_rating', '—'):.1f} | DVOA {pct(home_r.get('dvoa_total'))} (OFF {pct(home_r.get('dvoa_offense'))} / DEF {pct(home_r.get('dvoa_defense'))})")
            lines.append(f"  {away}: Power {away_r.get('power_rating', '—'):.1f} | DVOA {pct(away_r.get('dvoa_total'))} (OFF {pct(away_r.get('dvoa_offense'))} / DEF {pct(away_r.get('dvoa_defense'))})")
            if home_r.get("wins") is not None:
                lines.append(f"  Records: {home} {home_r.get('wins',0)}-{home_r.get('losses',0)} | {away} {away_r.get('wins',0)}-{away_r.get('losses',0)}")
        lines.append("")

    # ATS splits
    if home_ats or away_ats:
        lines.append("ATS SPLITS (since 2022):")
        if home_ats:
            ha = home_ats
            lines.append(f"  {home} AT HOME: {ha.get('cover_pct',0):.1f}% ({ha.get('covers',0)}/{ha.get('games',0)} covers)")
        if away_ats:
            aa = away_ats
            lines.append(f"  {away} AS AWAY: {aa.get('cover_pct',0):.1f}% ({aa.get('covers',0)}/{aa.get('games',0)} covers)")
        lines.append("")

    # H2H
    if h2h:
        lines.append(f"HEAD TO HEAD (last {len(h2h)} meetings):")
        for g in h2h[:6]:
            gd = g.get("game_date", "")
            gs = g.get("season", "")
            gw = g.get("week")
            hs = g.get("home_score")
            as_ = g.get("away_score")
            gh = g.get("home_team", "").split()[-1]
            ga = g.get("away_team", "").split()[-1]
            sc = f"{gh} {hs}-{ga} {as_}" if hs is not None else "score N/A"
            sp = g.get("spread_close")
            hc = g.get("home_covered")
            cover = f"{gh} covered {_fmt_spread(sp)}" if hc and sp else (f"{ga} covered +{abs(sp):.1f}" if hc is False and sp else "push/no data")
            ou = "OVER" if g.get("total_went_over") else ("UNDER" if g.get("total_went_over") is False else "—")
            label = f"W{gw}" if gw else str(gs)
            lines.append(f"  {gd} ({label}): {sc} | {cover} | {ou}")
        lines.append("")

    # Key injuries
    key_statuses = {"out", "ir", "doubtful", "questionable"}
    imp_inj = []
    for tm, inj_list, role in [(home, home_inj, "Home"), (away, away_inj, "Away")]:
        for inj in inj_list[:6]:
            s_low = (inj.get("status") or "").lower()
            if any(k in s_low for k in key_statuses):
                pos = inj.get("position") or ""
                itype = inj.get("injury_type") or ""
                imp_inj.append(f"  {tm} ({role}) — {inj.get('player_name')} ({pos}): {inj.get('status')} [{itype}]")
    if imp_inj:
        lines.append("KEY INJURIES:")
        lines.extend(imp_inj[:8])
        lines.append("")

    lines.append(
        "Write a full-page game analysis in the style of a professional handicapper. "
        "Use the data above to ground your analysis. For any coaching tendencies, "
        "scheme details, or situational context not in the data, draw on your expert "
        "knowledge of these teams and coaches. Identify the decisive factor in why "
        "this pick has edge and build the game script around it."
    )

    return chr(10).join(lines)



def generate_game_script(enriched: dict) -> str:
    """
    Generate a full-page Will Austin-style game script for a pick.

    Args:
        enriched: Enriched pick dict — same shape as /api/predictions/enriched response.
                  Should include home_rating, away_rating, line_snapshots, h2h,
                  home_ats, away_ats, home_injuries, away_injuries.

    Returns:
        Full narrative string (400-700 words).
        Returns _GAME_SCRIPT_DEFAULT on any API or parse error.
    """
    try:
        context = _build_game_context(enriched)

        response = client.messages.create(
            model=SONNET,
            max_tokens=1200,
            system=_GAME_SCRIPT_SYSTEM,
            messages=[{"role": "user", "content": context}],
        )

        text = response.content[0].text.strip()
        return text if len(text) > 100 else _GAME_SCRIPT_DEFAULT

    except anthropic.APIStatusError as exc:
        logger.error(
            "Sonnet API error generating game script: HTTP %s – %s",
            exc.status_code,
            exc.message,
        )
        return _GAME_SCRIPT_DEFAULT
    except anthropic.APIConnectionError as exc:
        logger.error("Sonnet connection error generating game script: %s", exc)
        return _GAME_SCRIPT_DEFAULT
    except Exception as exc:
        logger.error("Unexpected error in generate_game_script: %s", exc)
        return _GAME_SCRIPT_DEFAULT
