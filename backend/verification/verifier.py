"""
Multi-model verification pipeline for Max EV Sports.

Stage 1 — Haiku:   Fast statistical sanity gate (cheap, synchronous)
Stage 2 — Sonnet:  Independent cross-validation against raw data
Stage 3 — Opus:    Binding verdict with confidence score and flags

Results cached to disk (one file per day per subject).
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import os
import anthropic

from verification.checks import run_signal_prechecks, run_rating_prechecks

# Model IDs — same as pipeline.config but self-contained for VPS deployment
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
HAIKU  = "claude-haiku-4-5-20251001"
SONNET = "claude-sonnet-4-6"
OPUS   = "claude-opus-4-6"

logger = logging.getLogger(__name__)

BACKTEST_DIR = Path(__file__).parent.parent / "f5_backtest"
CACHE_DIR = BACKTEST_DIR / "verification_cache"
CACHE_DIR.mkdir(exist_ok=True)

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

VERDICT_VERIFIED    = "VERIFIED"
VERDICT_CONDITIONAL = "CONDITIONAL"
VERDICT_REJECTED    = "REJECTED"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict[str, Any]:
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text).strip()
    if not text.startswith("{"):
        m = re.search(r"\{", text)
        if m:
            text = text[m.start():]
    try:
        return json.loads(text)
    except Exception:
        # Truncated JSON — extract fields via regex as best-effort fallback
        result: dict[str, Any] = {"raw": text}
        verdict_m = re.search(r'"verdict"\s*:\s*"(VERIFIED|CONDITIONAL|REJECTED)"', text)
        if verdict_m:
            result["verdict"] = verdict_m.group(1)
        conf_m = re.search(r'"confidence"\s*:\s*(\d+)', text)
        if conf_m:
            result["confidence"] = int(conf_m.group(1))
        note_m = re.search(r'"user_display_note"\s*:\s*"([^"]*)"', text)
        if note_m:
            result["user_display_note"] = note_m.group(1)
        return result


def _cache_path(subject: str) -> Path:
    return CACHE_DIR / f"{subject}_{date.today().isoformat()}.json"


def _load_cache(subject: str) -> dict | None:
    p = _cache_path(subject)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return None


def _save_cache(subject: str, result: dict) -> None:
    try:
        _cache_path(subject).write_text(json.dumps(result, indent=2))
    except Exception as exc:
        logger.warning(f"Verification cache write failed: {exc}")


# ---------------------------------------------------------------------------
# Stage helpers
# ---------------------------------------------------------------------------

def _call_haiku(prompt: str) -> dict[str, Any]:
    try:
        resp = _client.messages.create(
            model=HAIKU,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_json(resp.content[0].text)
    except Exception as exc:
        logger.warning(f"Haiku call failed: {exc}")
        return {"severity": "warn", "flags": [str(exc)]}


def _call_sonnet(prompt: str) -> dict[str, Any]:
    try:
        resp = _client.messages.create(
            model=SONNET,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_json(resp.content[0].text)
    except Exception as exc:
        logger.warning(f"Sonnet call failed: {exc}")
        return {"analysis": str(exc), "concerns": []}


def _call_opus(prompt: str) -> dict[str, Any]:
    try:
        resp = _client.messages.create(
            model=OPUS,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_json(resp.content[0].text)
    except Exception as exc:
        logger.warning(f"Opus call failed: {exc}")
        return {"verdict": VERDICT_CONDITIONAL, "confidence": 40, "notes": str(exc)}


# ---------------------------------------------------------------------------
# Signal verification
# ---------------------------------------------------------------------------

def verify_signals(force: bool = False) -> dict[str, Any]:
    cached = _load_cache("signals")
    if cached and not force:
        return cached

    edge_matrix = json.loads((BACKTEST_DIR / "edge_matrix.json").read_text())
    backtest_26  = json.loads((BACKTEST_DIR / "backtest_2026.json").read_text())

    baseline   = edge_matrix["baseline"]
    all_edges  = edge_matrix.get("all_edges", [])
    signals_26 = backtest_26.get("signals", [])

    # ── Stage 1: Haiku statistical pre-checks ────────────────────────────────
    pre_flag_summary: dict[str, list[str]] = {}
    for sig in signals_26[:20]:  # cap to avoid token bloat
        flags = run_signal_prechecks(sig)
        if flags:
            pre_flag_summary[sig.get("signal", "?")] = flags

    for edge in all_edges[:10]:
        flags = run_signal_prechecks(edge)
        if flags:
            pre_flag_summary[edge.get("condition", "?")] = flags

    haiku_prompt = f"""You are a sports betting data auditor. Review these statistical pre-check flags on F5 MLB betting signals.

BASELINE: {json.dumps(baseline, indent=2)}

PRE-CHECK FLAGS (auto-generated):
{json.dumps(pre_flag_summary, indent=2)}

SAMPLE SIGNALS (2026 season):
{json.dumps(signals_26[:8], indent=2)}

SAMPLE EDGE CONDITIONS:
{json.dumps(all_edges[:5], indent=2)}

Respond with ONLY valid JSON:
{{"severity": "ok|warn|fail", "critical_flags": ["..."], "data_quality_score": 0-100}}"""

    haiku_result = _call_haiku(haiku_prompt)

    # ── Stage 2: Sonnet cross-validation ─────────────────────────────────────
    sonnet_prompt = f"""You are an independent sports analytics verifier. The primary agent produced F5 MLB edge signals.
Your job: recalculate independently and flag any discrepancies.

HAIKU PRE-CHECK RESULT: {json.dumps(haiku_result)}

RAW BASELINE (4,857 games): {json.dumps(baseline)}

TOP EDGE CONDITIONS CLAIMED:
{json.dumps(all_edges[:10], indent=2)}

KEY QUESTION: The edge matrix shows "F5 Under 5.5" at 97-98% actual rate vs 52% book implied.
The natural baseline for F5 Under 5.5 is 60.4% (not 52%). Recalculate true edge vs realistic book line.

Also verify: Are sample sizes sufficient? Do seasonal signals hold across multiple years?

Respond with ONLY valid JSON:
{{"cross_validation": "pass|partial|fail", "recalculated_edges": [{{"condition": "...", "claimed_rate": 0, "true_edge_vs_market": 0, "verdict": "..."}}], "concerns": ["..."], "corrected_book_baseline": {{}}}}"""

    sonnet_result = _call_sonnet(sonnet_prompt)

    # ── Stage 3: Opus binding verdict ────────────────────────────────────────
    opus_prompt = f"""You are the final verification authority for Max EV Sports betting signals.
Two agents have reviewed the F5 MLB edge engine data. Issue your binding verdict.

HAIKU (statistical gates): {json.dumps(haiku_result)}
SONNET (cross-validation): {json.dumps(sonnet_result)}

CRITICAL ISSUE TO ADJUDICATE:
The edge matrix claims "F5 Under 5.5" has 97-98% win rate vs 52% book implied (45%+ edge).
In reality, F5 Under 5.5 hits ~60.4% naturally and books price it at roughly -160 to -180.
The real edge (if any) is 0-12% above that baseline, NOT 45%.

Issue a binding verdict on the entire signal set:
- Are the signals real but overstated?
- Which specific signals have genuine, defensible edges?
- What corrections must be applied before showing users?

Respond with ONLY valid JSON:
{{"verdict": "VERIFIED|CONDITIONAL|REJECTED", "confidence": 0-100, "verified_signals": ["..."], "rejected_signals": ["..."], "required_corrections": ["..."], "user_display_note": "..."}}"""

    opus_result = _call_opus(opus_prompt)

    result = {
        "subject": "f5_signals",
        "verified_at": datetime.utcnow().isoformat(),
        "haiku":  haiku_result,
        "sonnet": sonnet_result,
        "opus":   opus_result,
        "verdict": opus_result.get("verdict", VERDICT_CONDITIONAL),
        "confidence": opus_result.get("confidence", 50),
        "pre_check_flags": pre_flag_summary,
    }
    _save_cache("signals", result)
    return result


# ---------------------------------------------------------------------------
# NFL Power Ratings verification
# ---------------------------------------------------------------------------

def verify_power_ratings(force: bool = False) -> dict[str, Any]:
    cached = _load_cache("ratings")
    if cached and not force:
        return cached

    ratings_data = json.loads((BACKTEST_DIR / "nfl_power_ratings.json").read_text())
    ats_2024     = json.loads((BACKTEST_DIR / "nfl_ats_2024.json").read_text())
    ats_2025     = json.loads((BACKTEST_DIR / "nfl_ats_2025.json").read_text())

    current_ratings = ratings_data.get("current", [])
    ats_lookup_24 = {r["team"]: r for r in ats_2024}
    ats_lookup_25 = {r["team"]: r for r in ats_2025}

    # ── Stage 1: Haiku pre-checks ─────────────────────────────────────────────
    pre_flags: dict[str, list[str]] = {}
    for entry in current_ratings:
        team    = entry["team"]
        rating  = entry["rating"]
        ats_rec = ats_lookup_25.get(team) or ats_lookup_24.get(team)
        ats_pct = float(ats_rec["ats_cover_pct"]) if ats_rec else None
        flags   = run_rating_prechecks(team, rating, ats_pct)
        if flags:
            pre_flags[team] = flags

    haiku_prompt = f"""Review these NFL Walters power rating pre-check flags.

RATING METHOD: {ratings_data.get('method')} | Formula: {ratings_data.get('formula')}
HOME FIELD: {ratings_data.get('home_field')} pts | Seasons: 2015-2025

PRE-CHECK FLAGS:
{json.dumps(pre_flags, indent=2)}

NOTABLE ANOMALY: KC (Chiefs) rated -0.85 (rank 18) despite recent Super Bowl wins.
Walters method uses margin of victory — KC wins close games so the model underrates them.

Respond with ONLY valid JSON:
{{"severity": "ok|warn|fail", "anomalies": ["..."], "methodology_assessment": "..."}}"""

    haiku_result = _call_haiku(haiku_prompt)

    # ── Stage 2: Sonnet cross-validation ─────────────────────────────────────
    # Sample top/bottom ratings vs ATS records for cross-check
    sample = []
    for entry in current_ratings[:16]:
        t = entry["team"]
        a25 = ats_lookup_25.get(t, {})
        a24 = ats_lookup_24.get(t, {})
        sample.append({
            "team": t, "rating": entry["rating"], "tier": entry["tier"],
            "ats_2025": a25.get("ats_record"), "ats_cover_pct_2025": a25.get("ats_cover_pct"),
            "ats_2024": a24.get("ats_record"), "ats_cover_pct_2024": a24.get("ats_cover_pct"),
        })

    sonnet_prompt = f"""You are independently verifying NFL Walters power ratings for the 2026 pre-season.
These ratings drive the Survivor Helper tool and NFL handicapping.

HAIKU PRE-CHECK: {json.dumps(haiku_result)}

RATINGS vs ATS RECORDS (top 16 teams):
{json.dumps(sample, indent=2)}

Verify: Does each team's rating correlate with its ATS performance?
Flag any team where the rating seems systematically wrong.
Specifically analyze KC at -0.85 and SEA at +10.57 — are these defensible?

Respond with ONLY valid JSON:
{{"cross_validation": "pass|partial|fail", "team_verdicts": [{{"team":"", "rating":0, "verdict":"ok|warn|flag", "reason":""}}], "systemic_issues": ["..."]}}"""

    sonnet_result = _call_sonnet(sonnet_prompt)

    # ── Stage 3: Opus verdict ─────────────────────────────────────────────────
    opus_prompt = f"""You are the final verification authority for NFL power ratings used in a sports betting platform.

HAIKU: {json.dumps(haiku_result)}
SONNET: {json.dumps(sonnet_result)}

SYSTEM CONTEXT:
- Walters method: margin-of-victory based, exponential decay (0.90 factor)
- 11 seasons of history baked in (2015-2025)
- Current ratings used for: Survivor win probabilities, First Half handicapping
- KC at -0.85 (rank 18) despite back-to-back-to-back Super Bowl appearances
- SEA at +10.57 (rank 1) — is this the current Seattle or old LOB era bleeding in?

Issue binding verdict: Are these ratings trustworthy enough to serve to users?
What caveats or corrections must accompany them?

Respond with ONLY valid JSON:
{{"verdict": "VERIFIED|CONDITIONAL|REJECTED", "confidence": 0-100, "trusted_for": ["..."], "not_trusted_for": ["..."], "required_corrections": ["..."], "user_display_note": "..."}}"""

    opus_result = _call_opus(opus_prompt)

    result = {
        "subject": "nfl_power_ratings",
        "verified_at": datetime.utcnow().isoformat(),
        "haiku":  haiku_result,
        "sonnet": sonnet_result,
        "opus":   opus_result,
        "verdict": opus_result.get("verdict", VERDICT_CONDITIONAL),
        "confidence": opus_result.get("confidence", 50),
        "pre_check_flags": pre_flags,
    }
    _save_cache("ratings", result)
    return result
