"""
Pure-Python statistical pre-checks — no API calls, no I/O.
These run as the Haiku-tier "sanity gate" before any Claude call is made.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CheckResult:
    passed: bool
    severity: str          # "ok" | "warn" | "fail"
    flags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def check_sample_size(n: int, min_strong: int = 100, min_basic: int = 30) -> CheckResult:
    if n < min_basic:
        return CheckResult(False, "fail", [f"Sample too small: n={n} (min {min_basic})"])
    if n < min_strong:
        return CheckResult(True, "warn", [f"Marginal sample: n={n} (strong claims need {min_strong}+)"])
    return CheckResult(True, "ok")


def check_win_rate_plausibility(rate_pct: float, bet_type: str) -> CheckResult:
    """Bet-type-aware plausibility bounds."""
    limits: dict[str, tuple[float, float]] = {
        "tie":        (5.0,  40.0),
        "under":      (45.0, 72.0),
        "over":       (28.0, 55.0),
        "spread":     (40.0, 65.0),
        "moneyline":  (30.0, 80.0),
        "total":      (40.0, 72.0),
    }
    key = next((k for k in limits if k in bet_type.lower()), "total")
    lo, hi = limits[key]
    flags: list[str] = []
    if rate_pct < lo:
        flags.append(f"Win rate {rate_pct:.1f}% below floor {lo}% for {bet_type}")
        return CheckResult(False, "fail", flags)
    if rate_pct > hi:
        flags.append(f"Win rate {rate_pct:.1f}% above ceiling {hi}% for {bet_type} — likely calculation error")
        return CheckResult(False, "fail", flags)
    return CheckResult(True, "ok")


def check_roi_plausibility(roi_pct: float, n: int) -> CheckResult:
    """
    High ROI on large samples is suspicious — books would have adjusted.
    Sliding scale: more samples → tighter ROI ceiling.
    """
    if n <= 0:
        return CheckResult(False, "fail", ["n=0"])
    # Allowable ROI ceiling shrinks as sample grows
    ceiling = max(8.0, 60.0 - 0.25 * n)
    if roi_pct > ceiling:
        return CheckResult(False, "warn", [
            f"ROI {roi_pct:.1f}% implausibly high for n={n} (ceiling {ceiling:.0f}%) "
            f"— book would have already adjusted lines"
        ])
    if roi_pct < -30.0:
        return CheckResult(False, "warn", [f"ROI {roi_pct:.1f}% extremely negative"])
    return CheckResult(True, "ok")


def check_book_baseline(actual_pct: float, book_implied_pct: float, bet_type: str) -> CheckResult:
    """
    Verify that the book_implied baseline is realistic for this bet type.
    'F5 Under 5.5 at 52% implied' is wrong — it naturally hits 60%+.
    """
    natural_rates: dict[str, float] = {
        "f5 under 5.5": 60.4,
        "f5 under 4.5": 48.6,
        "f5 under 6.5": 70.5,
        "f5 under 7.5": 78.6,
        "f5 tie":       14.5,
        "f5 over 4.5":  51.4,
    }
    key = next((k for k in natural_rates if k in bet_type.lower()), None)
    if key is None:
        return CheckResult(True, "ok")  # no baseline to check

    natural = natural_rates[key]
    if abs(book_implied_pct - natural) > 10.0:
        return CheckResult(False, "warn", [
            f"Book implied {book_implied_pct:.1f}% for '{bet_type}' looks wrong "
            f"(natural baseline ≈{natural:.1f}%) — edge calc may be inflated"
        ])
    true_edge = actual_pct - natural
    return CheckResult(True, "ok" if true_edge > 3 else "warn", [
        f"True edge vs natural baseline: {true_edge:+.1f}%"
    ] if true_edge <= 3 else [])


def check_rating_vs_record(rating: float, ats_win_pct: float, team: str) -> CheckResult:
    """
    Power rating and ATS win% should be loosely correlated.
    A team rated +10 going 40% ATS (or vice versa) is a red flag.
    """
    expected_ats = 50.0 + rating * 1.5   # rough heuristic
    divergence = abs(expected_ats - ats_win_pct)
    if divergence > 20:
        return CheckResult(False, "warn", [
            f"{team}: rating {rating:+.1f} implies ~{expected_ats:.0f}% ATS "
            f"but actual {ats_win_pct:.0f}% (gap {divergence:.0f}pts)"
        ])
    return CheckResult(True, "ok")


# ---------------------------------------------------------------------------
# Batch runner — returns all flags consolidated
# ---------------------------------------------------------------------------

def run_signal_prechecks(signal: dict[str, Any]) -> list[str]:
    """Run all statistical gates on a single signal dict. Returns list of flag strings."""
    flags: list[str] = []

    n = signal.get("bets", signal.get("games", signal.get("sample_size", 0)))
    win_rate = signal.get("win_rate", signal.get("actual_rate", 0.0))
    roi = signal.get("roi", 0.0)
    bet_type = signal.get("signal", signal.get("bet", signal.get("name", "")))
    book_implied = signal.get("book_implied", None)

    for chk in [
        check_sample_size(int(n)),
        check_win_rate_plausibility(float(win_rate), bet_type),
        check_roi_plausibility(float(roi), int(n)),
    ]:
        flags.extend(chk.flags)

    if book_implied is not None:
        chk = check_book_baseline(float(win_rate), float(book_implied), bet_type)
        flags.extend(chk.flags)

    return flags


def run_rating_prechecks(team: str, rating: float, ats_win_pct: float | None) -> list[str]:
    flags: list[str] = []
    if abs(rating) > 15:
        flags.append(f"{team}: extreme rating {rating:+.1f} — verify data source")
    if ats_win_pct is not None:
        flags.extend(check_rating_vs_record(rating, ats_win_pct, team).flags)
    return flags
