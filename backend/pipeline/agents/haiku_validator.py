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
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("—", "-").replace("–", "-")
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

    truncated = text[:last_safe].rstrip(",").rstrip()
    closing = "}" * depth_brace + "]" * depth_bracket
    return truncated + closing


def validate_statcast_record(record: dict) -> dict:
    """
    Use Claude Haiku to validate a single Statcast data record.

    Checks for anomalous stat values, missing critical fields, and impossible
    combinations (e.g. xERA < 0, barrel% > 100, spin_rate > 4000).

    Args:
        record: Statcast row as a dict keyed by stat name.

    Returns:
        dict with keys:
            valid    (bool)                   - True if the record passes validation.
            flags    (list[str])              - Human-readable issue descriptions.
            severity ('ok'|'warning'|'error') - Worst-case severity across flags.
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
            '{ "valid": true, "flags": [], "severity": "ok" }'
        )

        response = client.messages.create(
            model=HAIKU,
            max_tokens=400,
            system=(
                "You are a sports data quality analyst specializing in Statcast baseball metrics. "
                "The current year is 2026. The 2026 MLB season is live and active — "
                "records with season=2026 or game_date in 2026 are CURRENT, not future data. "
                "Detect anomalous, impossible, or missing values in raw data records. "
                "Be strict about data integrity. "
                "Return ONLY valid JSON with no explanation, no markdown, no extra keys."
            ),
            messages=[{"role": "user", "content": prompt}],
        )

        raw = _extract_json(response.content[0].text)
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
            "Haiku API error validating statcast record: HTTP %s - %s",
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

    Returns only numeric/boolean/enum fields — no free-text string arrays
    that could contain colons or commas causing JSON parse failures.
    Flag descriptions are built from numeric values in Python.
    """
    try:
        home = game.get("home_team", "")
        away = game.get("away_team", "")
        bookmakers = game.get("bookmakers", [])
        bk_count = len(bookmakers)
        ml = game.get("market_lines", {})
        home_price = ml.get("home_ml") or ml.get("h2h_home")
        away_price = ml.get("away_ml") or ml.get("h2h_away")
        # Fallback: pull ML prices from bookmakers if market_lines absent (WNBA/NBA)
        if home_price is None and bookmakers:
            for bk in bookmakers:
                markets = bk.get("markets", {})
                if not isinstance(markets, dict):
                    continue
                h2h = markets.get("h2h", [])
                home_out = next((o for o in h2h if o.get("name") == home), None)
                away_out = next((o for o in h2h if o.get("name") == away), None)
                if home_out and away_out:
                    home_price = home_out.get("price")
                    away_price = away_out.get("price")
                    break

        prompt = (
            "Validate these betting odds for data quality.\n"
            f"home_team present: {bool(home)}\n"
            f"away_team present: {bool(away)}\n"
            f"bookmaker_count: {bk_count}\n"
            f"home_ml: {home_price}\n"
            f"away_ml: {away_price}\n\n"
            "Return ONLY this JSON with no other text:\n"
            '{"valid": true, "implied_prob_sum": 1.05, "severity": "ok"}\n'
            "severity must be exactly ok or warning or error.\n"
            "valid is false only when severity is error."
        )

        response = client.messages.create(
            model=HAIKU,
            max_tokens=80,
            system=(
                "You are a betting odds validator. "
                "Return ONLY a single JSON object with keys: valid (bool), "
                "implied_prob_sum (float), severity (ok/warning/error). "
                "No markdown. No explanation. No arrays. No extra keys."
            ),
            messages=[{"role": "user", "content": prompt}],
        )

        raw = _extract_json(response.content[0].text)
        result = json.loads(raw)

        severity = result.get("severity", "ok")
        if severity not in ("ok", "warning", "error"):
            severity = "ok"

        # Build flag descriptions from numeric results — no free-text from model
        flags: list[str] = []
        ips = float(result.get("implied_prob_sum", 1.0))
        if ips > 1.15:
            flags.append(f"Extreme vig: implied_prob_sum={ips:.3f}")
        elif ips > 1.08:
            flags.append(f"High vig: implied_prob_sum={ips:.3f}")
        if bk_count == 0:
            flags.append("No bookmakers")
        if not home or not away:
            flags.append("Missing team name(s)")

        return {
            "valid": bool(result.get("valid", True)),
            "flags": flags,
            "severity": severity,
        }

    except anthropic.APIStatusError as exc:
        logger.error(
            "Haiku API error validating game odds: HTTP %s - %s",
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
