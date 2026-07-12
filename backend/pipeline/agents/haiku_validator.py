"""
Haiku-powered validation layer for the Sports Betting Analytics pipeline.

Lightweight, fast validation checks using Claude Haiku.
All calls fail open — a validation error never blocks downstream processing.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic

from pipeline.config import ANTHROPIC_API_KEY, HAIKU

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Default pass-through responses used when any error occurs
_DEFAULT_RECORD_RESULT: dict[str, Any] = {"valid": True, "flags": [], "severity": "ok"}
_DEFAULT_ODDS_RESULT: dict[str, Any] = {"valid": True, "flags": [], "severity": "ok"}


def _strip_fences(text: str) -> str:
    """Strip markdown code fences from a Claude response before JSON parsing."""
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def validate_statcast_record(record: dict) -> dict:
    """
    Use Claude Haiku to validate a single Statcast data record.

    Checks for anomalous stat values, missing critical fields, and impossible
    combinations (e.g. xERA < 0, barrel% > 100, spin_rate > 4000).

    Args:
        record: Statcast row as a dict keyed by stat name.

    Returns:
        dict with keys:
            valid    (bool)                   – True if the record passes validation.
            flags    (list[str])              – Human-readable issue descriptions.
            severity ('ok'|'warning'|'error') – Worst-case severity across flags.
        On any API or parse error, returns the safe default
        ``{valid: True, flags: [], severity: 'ok'}`` so the pipeline continues.
    """
    try:
        prompt = (
            f"Validate this Statcast baseball record for data quality issues.\n\n"
            f"Record: {json.dumps(record, default=str)}\n\n"
            f"Check for:\n"
            f"- Missing critical fields: player_id, game_date, pitch_type\n"
            f"- Impossible values: xERA < 0 or > 10, barrel% < 0 or > 100, "
            f"exit_velocity < 0 or > 130, spin_rate < 0 or > 4000\n"
            f"- Statistical impossibilities (e.g. whiff_rate > 1.0)\n\n"
            f"Respond with ONLY valid JSON, no markdown fences:\n"
            f'{{ "valid": true, "flags": [], "severity": "ok" }}'
        )

        response = client.messages.create(
            model=HAIKU,
            max_tokens=200,
            system=(
                "You are a sports data quality analyst specializing in Statcast baseball metrics. "
                "Detect anomalous, impossible, or missing values in raw data records. "
                "Be strict about data integrity. "
                "Return ONLY valid JSON with no explanation, no markdown, no extra keys."
            ),
            messages=[{"role": "user", "content": prompt}],
        )

        raw = _strip_fences(response.content[0].text)
        result = json.loads(raw)

        severity = result.get("severity", "ok")
        if severity not in ("ok", "warning", "error"):
            severity = "ok"

        return {
            "valid": bool(result.get("valid", True)),
            "flags": list(result.get("flags", [])),
            "severity": severity,
        }

    except anthropic.APIStatusError as exc:
        logger.error(
            "Haiku API error validating statcast record: HTTP %s – %s",
            exc.status_code,
            exc.message,
        )
        return dict(_DEFAULT_RECORD_RESULT)
    except anthropic.APIConnectionError as exc:
        logger.error("Haiku connection error validating statcast record: %s", exc)
        return dict(_DEFAULT_RECORD_RESULT)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning("Failed to parse Haiku statcast validation response: %s", exc)
        return dict(_DEFAULT_RECORD_RESULT)
    except Exception as exc:
        logger.error("Unexpected error in validate_statcast_record: %s", exc)
        return dict(_DEFAULT_RECORD_RESULT)


def validate_game_odds(game: dict) -> dict:
    """
    Use Claude Haiku to validate a live odds snapshot for a game.

    Flags odds that appear stale, manipulated, or from a data-feed error:
    - Vig exceeding 8% (implied prob sum > 1.08)
    - Implied probability sum exceeding 1.15 (over 15% juice)
    - No bookmakers listed
    - Missing home/away teams
    - Negative or zero odds values

    Args:
        game: Odds snapshot dict containing at minimum ``home_team``,
              ``away_team``, ``bookmakers``, and ``market_lines``.

    Returns:
        dict with keys:
            valid    (bool)                   – True if odds appear clean.
            flags    (list[str])              – Descriptions of issues found.
            severity ('ok'|'warning'|'error') – Worst-case severity.
        On any API or parse error, returns the safe default (valid=True).
    """
    try:
        prompt = (
            f"Validate this sports betting odds record for data quality issues.\n\n"
            f"Game data: {json.dumps(game, default=str)}\n\n"
            f"Flag as issues:\n"
            f"- Vig > 8% (implied probability sum > 1.08) → severity: warning\n"
            f"- Implied probability sum > 1.15 (extreme juice) → severity: error\n"
            f"- No bookmakers listed → severity: error\n"
            f"- Missing home_team or away_team → severity: error\n"
            f"- Negative or zero odds values → severity: error\n\n"
            f"Respond with ONLY valid JSON, no markdown fences:\n"
            f'{{ "valid": true, "flags": [], "severity": "ok" }}'
        )

        response = client.messages.create(
            model=HAIKU,
            max_tokens=150,
            system=(
                "You are a sports betting data analyst checking live odds feeds for integrity. "
                "Detect stale data, feed errors, extreme vig, and missing bookmakers. "
                "Return ONLY valid JSON with no explanation and no markdown."
            ),
            messages=[{"role": "user", "content": prompt}],
        )

        raw = _strip_fences(response.content[0].text)
        result = json.loads(raw)

        severity = result.get("severity", "ok")
        if severity not in ("ok", "warning", "error"):
            severity = "ok"

        return {
            "valid": bool(result.get("valid", True)),
            "flags": list(result.get("flags", [])),
            "severity": severity,
        }

    except anthropic.APIStatusError as exc:
        logger.error(
            "Haiku API error validating game odds: HTTP %s – %s",
            exc.status_code,
            exc.message,
        )
        return dict(_DEFAULT_ODDS_RESULT)
    except anthropic.APIConnectionError as exc:
        logger.error("Haiku connection error validating game odds: %s", exc)
        return dict(_DEFAULT_ODDS_RESULT)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning("Failed to parse Haiku odds validation response: %s", exc)
        return dict(_DEFAULT_ODDS_RESULT)
    except Exception as exc:
        logger.error("Unexpected error in validate_game_odds: %s", exc)
        return dict(_DEFAULT_ODDS_RESULT)


def batch_validate(records: list[dict], record_type: str) -> list[dict]:
    """
    Validate a batch of records using the appropriate Haiku validator.

    Dispatches to ``validate_statcast_record`` for ``record_type="statcast"``
    and to ``validate_game_odds`` for any other value (typically ``"odds"``).

    Caps at 50 records to stay within sensible rate limits.  Any records
    beyond the cap receive the safe default pass-through result so the
    returned list always matches the input length.

    Args:
        records:     List of record dicts to validate.
        record_type: ``"statcast"`` or ``"odds"``.

    Returns:
        List of validation result dicts, one per input record, in the same order.
    """
    if not records:
        return []

    cap = 50
    if len(records) > cap:
        logger.warning(
            "batch_validate: received %d records (type=%s), capping at %d.",
            len(records),
            record_type,
            cap,
        )

    capped = records[:cap]
    overflow_count = len(records) - len(capped)

    validator = (
        validate_statcast_record
        if record_type == "statcast"
        else validate_game_odds
    )

    results: list[dict] = []
    for rec in capped:
        results.append(validator(rec))

    # Pad overflow with safe defaults so len(results) == len(records)
    default = _DEFAULT_RECORD_RESULT if record_type == "statcast" else _DEFAULT_ODDS_RESULT
    for _ in range(overflow_count):
        results.append(dict(default))

    return results
