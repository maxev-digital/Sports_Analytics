"""
Opus-powered deep reflection layer for the Sports Betting Analytics pipeline.

Provides daily risk assessment and weekly methodology audits using Claude Opus.
These are the most expensive AI calls in the pipeline — they run once per day
and once per week respectively, not once per pick.

All calls fail open: a Claude error returns a conservative default that does
NOT block the pipeline but always logs at CRITICAL level so the operator knows
the gate ran without AI oversight.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic

from pipeline.config import ANTHROPIC_API_KEY, OPUS, now_cst
from pipeline.db.connection import execute_write

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Conservative fallback for daily reflection — proceed=True so the pipeline
# is not blocked, but model_health=warning so operators know to check.
_DEFAULT_DAILY_REFLECTION: dict[str, Any] = {
    "proceed": True,
    "flags": ["Daily reflection unavailable — Claude API error."],
    "picks_to_skip": [],
    "narrative": (
        "Reflection gate failed due to Claude API error. "
        "Pipeline is proceeding with all picks. Manual review recommended."
    ),
    "action_items": [
        "Review Claude API status.",
        "Manually audit picks before publishing.",
    ],
    "model_health": "warning",
}

# Conservative fallback for weekly audit
_DEFAULT_WEEKLY_AUDIT: dict[str, Any] = {
    "methodology_assessment": "Weekly audit unavailable — Claude API error. Manual review required.",
    "improvement_suggestions": [],
    "risk_flags": ["Audit failed — no automated analysis available for this week."],
    "recommended_threshold_changes": {},
}


def _extract_json(text: str) -> str:
    """Robustly extract JSON from a Claude response.
    Handles: markdown fences, leading prose, truncated responses, smart quotes.
    """
    text = text.strip()
    # Strip markdown code fences
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    text = text.strip()
    # If response starts with prose, find the first { or [
    if not text.startswith(("{", "[")):
        m = re.search(r"[\{\[]", text)
        if m:
            text = text[m.start():]
    # Replace curly/smart quotes that break JSON
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '\"').replace("\u201d", '\"')
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    # If JSON is truncated (unterminated string), try to repair
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        # Try truncating to last complete key-value pair
        repaired = _repair_truncated_json(text)
        return repaired


def _repair_truncated_json(text: str) -> str:
    """Attempt to close a truncated JSON object by finding the last valid position."""
    # Walk backwards finding the last comma or opening brace
    # Then close all open brackets
    depth_brace = 0
    depth_bracket = 0
    in_string = False
    escape_next = False
    last_safe = 0

    for i, ch in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"' and not in_string:
            in_string = True
            continue
        if ch == '"' and in_string:
            in_string = False
            last_safe = i + 1
            continue
        if in_string:
            continue
        if ch in ("{", "["):
            if ch == "{":
                depth_brace += 1
            else:
                depth_bracket += 1
        elif ch in ("}", "]"):
            if ch == "}":
                depth_brace -= 1
            else:
                depth_bracket -= 1
            last_safe = i + 1
        elif ch == ",":
            last_safe = i

    # Truncate to last safe position and close open brackets
    truncated = text[:last_safe].rstrip(",").rstrip()
    closing = "}" * depth_brace + "]" * depth_bracket
    return truncated + closing




def reflect_on_daily_picks(
    picks: list[dict],
    ingestion_report: dict,
    model_perf: dict,
) -> dict:
    """
    Run a daily risk reflection over all picks before they are published.

    Acts as the pipeline's Chief Risk Officer: reviews pick concentration,
    model performance trends, data quality flags from ingestion, and market
    exposure to decide whether the full slate should proceed and which
    individual picks (if any) should be withheld.

    This is the final gate before picks reach clients. A false positive
    (blocking good picks) is acceptable. A false negative (publishing bad
    picks) is catastrophic.

    Args:
        picks:            List of today's pick dicts, fully featured.
        ingestion_report: Summary dict from the ingestion layer — should
                          include record counts, API error counts, and data
                          freshness timestamps.
        model_perf:       Recent model performance metrics — should include
                          ROI, accuracy, Brier score, and sample size by sport.

    Returns:
        dict with keys:
            proceed       (bool)      – True if the pipeline should publish picks.
            flags         (list[str]) – Risk flags identified.
            picks_to_skip (list[int]) – 0-based indices of picks to withhold.
            narrative     (str)       – Human-readable risk assessment summary.
            action_items  (list[str]) – Steps for the operator to take today.
            model_health  (str)       – 'healthy' | 'warning' | 'critical'
        On any API or parse error, returns ``_DEFAULT_DAILY_REFLECTION``.
    """
    try:
        payload = {
            "picks": picks,
            "ingestion_report": ingestion_report,
            "model_performance": model_perf,
        }

        prompt = (
            f"SYSTEM CONTEXT: This is a brand-new pipeline launched June 2026. The 2026 MLB season is currently ACTIVE (started March 2026). Season=2026 data from Baseball Savant is CURRENT data, not future/synthetic. model_performance being zero/empty is EXPECTED because no game results are settled yet (new system, < 30 days old). Do NOT flag empty model_performance as a blocker.\n\n"
            f"SYSTEM CONTEXT: This is a brand-new pipeline launched June 2026. The 2026 MLB season is currently ACTIVE (started March 2026). Season=2026 data from Baseball Savant is CURRENT data, not future/synthetic. model_performance being zero/empty is EXPECTED because no game results are settled yet (new system, < 30 days old). Do NOT flag empty model_performance as a blocker.\n\n"
            f"Today's pipeline data for risk review:\n"
            f"{json.dumps(payload, default=str)}\n\n"
            f"As Chief Risk Officer, evaluate the following:\n"
            f"1. Pick concentration risk — are too many bets on one sport, team, or market?\n"
            f"2. Data quality — are error rates or staleness concerning? NOTE: ignore any 'future season 2026' flags — 2026 is the current active season.\n"
            f"3. Model health trends — is accuracy degrading, is Brier score drifting?\n"
            f"4. Individual pick outliers — any picks that look like data artifacts or "
            f"model misfires (e.g. impossibly high edge_pct, extreme lines)?\n\n"
            f"Return ONLY valid JSON matching this exact schema:\n"
            f"{{\n"
            f'  "proceed": true,\n'
            f'  "flags": ["..."],\n'
            f'  "picks_to_skip": [],\n'
            f'  "narrative": "...",\n'
            f'  "action_items": ["..."],\n'
            f'  "model_health": "healthy"\n'
            f"}}"
        )

        response = client.messages.create(
            model=OPUS,
            max_tokens=2000,
            system=(
                "You are the Chief Risk Officer for a quantitative sports betting operation. "
                "Your daily reflection is the final automated gate before picks are published "
                "to paying clients. Be rigorous and conservative: err on the side of caution. "
                "Flag pick concentration, model degradation, and data quality issues aggressively. "
                "When in doubt, add a flag and an action item rather than silently passing. "
                "Return ONLY valid JSON — no prose outside the JSON object."
            ),
            messages=[{"role": "user", "content": prompt}],
        )

        raw = _extract_json(response.content[0].text)
        result = json.loads(raw)

        health = result.get("model_health", "warning")
        if health not in ("healthy", "warning", "critical"):
            health = "warning"

        return {
            "proceed": bool(result.get("proceed", True)),
            "flags": list(result.get("flags", [])),
            "picks_to_skip": [int(i) for i in result.get("picks_to_skip", []) if str(i).strip().lstrip("-").isdigit()],
            "narrative": str(result.get("narrative", "")),
            "action_items": list(result.get("action_items", [])),
            "model_health": health,
        }

    except anthropic.APIStatusError as exc:
        logger.critical(
            "Opus API error during daily reflection: HTTP %s – %s",
            exc.status_code,
            exc.message,
        )
        return dict(_DEFAULT_DAILY_REFLECTION)
    except anthropic.APIConnectionError as exc:
        logger.critical("Opus connection error during daily reflection: %s", exc)
        return dict(_DEFAULT_DAILY_REFLECTION)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.critical(
            "Failed to parse Opus daily reflection response: %s", exc
        )
        return dict(_DEFAULT_DAILY_REFLECTION)
    except Exception as exc:
        logger.critical(
            "Unexpected error in reflect_on_daily_picks: %s", exc
        )
        return dict(_DEFAULT_DAILY_REFLECTION)


def weekly_deep_audit(
    week_picks: list[dict],
    week_results: list[dict],
    model_perf_history: list[dict],
) -> dict:
    """
    Run a comprehensive weekly audit of methodology and model performance.

    Reviews all picks from the prior 7 days, their graded outcomes, and the
    model's 30-day performance trajectory to identify systemic weaknesses,
    overfitting signals, and regime changes. Recommends specific threshold
    adjustments with justification.

    Args:
        week_picks:         All picks from the prior 7 days.
        week_results:       Graded outcomes for those picks — should include
                            result ('win'/'loss'/'push'), pl_units, and the
                            closing line for CLV calculation.
        model_perf_history: Daily model performance snapshots for the past
                            30+ days — accuracy, ROI, Brier score per day.

    Returns:
        dict with keys:
            methodology_assessment        (str)         – High-level methodology grade.
            improvement_suggestions       (list[str])   – Actionable changes.
            risk_flags                    (list[str])   – Systemic risks identified.
            recommended_threshold_changes (dict)        – Suggested changes to thresholds
                                                          (e.g. MIN_EDGE_PCT, MIN_CONFIDENCE,
                                                          per-sport overrides).
        On any API or parse error, returns ``_DEFAULT_WEEKLY_AUDIT``.
    """
    try:
        payload = {
            "week_picks": week_picks,
            "week_results": week_results,
            "model_performance_history_30d": model_perf_history,
        }

        prompt = (
            f"Weekly pipeline data for methodology audit:\n"
            f"{json.dumps(payload, default=str)}\n\n"
            f"Conduct a rigorous weekly methodology review:\n"
            f"1. Assess overall methodology quality — ROI, win rate, CLV capture, Brier score\n"
            f"2. Identify sport/market/pick-type combinations underperforming expectations\n"
            f"3. Flag systemic risks: overfitting signals, data leakage patterns, regime changes\n"
            f"4. Recommend specific threshold changes with explicit justification "
            f"(e.g. raise MIN_EDGE_PCT from 3.0 to 4.5 for NBA totals because ROI < -5% on 60+ sample)\n\n"
            f"Return ONLY valid JSON matching this exact schema:\n"
            f"{{\n"
            f'  "methodology_assessment": "...",\n'
            f'  "improvement_suggestions": ["..."],\n'
            f'  "risk_flags": ["..."],\n'
            f'  "recommended_threshold_changes": {{"MIN_EDGE_PCT": 3.0}}\n'
            f"}}"
        )

        response = client.messages.create(
            model=OPUS,
            max_tokens=2000,
            system=(
                "You are the Chief Analytics Officer conducting a weekly methodology review "
                "for a quantitative sports betting platform. Your analysis determines whether "
                "the pipeline's models are generating genuine edge or chasing noise. "
                "Be brutally honest about underperformance — do not soften findings. "
                "Recommend precise, data-justified threshold changes. "
                "Return ONLY valid JSON — no prose outside the JSON object."
            ),
            messages=[{"role": "user", "content": prompt}],
        )

        raw = _extract_json(response.content[0].text)
        result = json.loads(raw)

        return {
            "methodology_assessment": str(result.get("methodology_assessment", "")),
            "improvement_suggestions": list(result.get("improvement_suggestions", [])),
            "risk_flags": list(result.get("risk_flags", [])),
            "recommended_threshold_changes": dict(
                result.get("recommended_threshold_changes", {})
            ),
        }

    except anthropic.APIStatusError as exc:
        logger.critical(
            "Opus API error during weekly audit: HTTP %s – %s",
            exc.status_code,
            exc.message,
        )
        return dict(_DEFAULT_WEEKLY_AUDIT)
    except anthropic.APIConnectionError as exc:
        logger.critical("Opus connection error during weekly audit: %s", exc)
        return dict(_DEFAULT_WEEKLY_AUDIT)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.critical("Failed to parse Opus weekly audit response: %s", exc)
        return dict(_DEFAULT_WEEKLY_AUDIT)
    except Exception as exc:
        logger.critical("Unexpected error in weekly_deep_audit: %s", exc)
        return dict(_DEFAULT_WEEKLY_AUDIT)


def save_reflection_report(report: dict, sport: str) -> None:
    """
    Persist a daily reflection report to the ``reflection_reports`` PostgreSQL table.

    Uses an UPSERT so re-running the daily pipeline on the same date is safe.
    Logs an error on DB failure but never raises — the pipeline must not crash
    because a reflection write failed.

    Args:
        report: The dict returned by ``reflect_on_daily_picks``.
        sport:  Sport code (e.g. 'MLB', 'NBA', 'NFL', 'ALL').
    """
    sql = """
        INSERT INTO reflection_reports (
            report_date,
            sport,
            total_picks,
            flags_raised,
            opus_narrative,
            proceed,
            flags,
            picks_to_skip,
            narrative,
            action_items,
            model_health,
            created_at
        ) VALUES (
            %(report_date)s,
            %(sport)s,
            %(total_picks)s,
            %(flags_raised)s,
            %(narrative)s,
            %(proceed)s,
            %(flags)s,
            %(picks_to_skip)s,
            %(narrative)s,
            %(action_items)s,
            %(model_health)s,
            %(created_at)s
        )
        ON CONFLICT (report_date, sport)
        DO UPDATE SET
            total_picks    = EXCLUDED.total_picks,
            flags_raised   = EXCLUDED.flags_raised,
            opus_narrative = EXCLUDED.opus_narrative,
            proceed        = EXCLUDED.proceed,
            flags          = EXCLUDED.flags,
            picks_to_skip  = EXCLUDED.picks_to_skip,
            narrative      = EXCLUDED.narrative,
            action_items   = EXCLUDED.action_items,
            model_health   = EXCLUDED.model_health,
            created_at     = EXCLUDED.created_at
    """

    now = now_cst()
    flags_list = report.get("flags", [])
    params: dict[str, Any] = {
        "report_date": now.date(),
        "sport": sport.upper(),
        "total_picks": len(report.get("picks_to_skip", [])) + len(flags_list),
        "flags_raised": len(flags_list),
        "proceed": report.get("proceed", True),
        "flags": json.dumps(flags_list),
        "picks_to_skip": json.dumps(report.get("picks_to_skip", [])),
        "narrative": report.get("narrative", ""),
        "action_items": json.dumps(report.get("action_items", [])),
        "model_health": report.get("model_health", "warning"),
        "created_at": now,
    }

    try:
        rows_affected = execute_write(sql, params)
        logger.info(
            "Saved reflection report for sport=%s on %s (rows_affected=%d)",
            sport.upper(),
            now.date(),
            rows_affected,
        )
    except Exception as exc:
        logger.error(
            "Failed to save reflection report for sport=%s on %s: %s",
            sport.upper(),
            now.date(),
            exc,
        )
