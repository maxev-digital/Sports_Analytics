"""
Signal Performance Logger

Appends daily recap results to a rolling log so the verification pipeline
can compare claimed edge rates vs actual hit rates over time.

Log file: f5_backtest/signal_performance_log.json
Structure:
{
  "2026-08-01": {
    "total_bets": 17, "wins": 10, "losses": 7, "win_rate": 58.8, "total_pl": 541.0,
    "by_signal": {
      "F5 Tie (Ace vs Ace)": {"bets": 2, "wins": 1, "losses": 1, "pl": 350.0},
      ...
    }
  }
}
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

LOG_PATH = Path(__file__).parent.parent / "f5_backtest" / "signal_performance_log.json"


def _load() -> dict[str, Any]:
    if LOG_PATH.exists():
        try:
            return json.loads(LOG_PATH.read_text())
        except Exception:
            pass
    return {}


def _save(data: dict[str, Any]) -> None:
    try:
        LOG_PATH.write_text(json.dumps(data, indent=2))
    except Exception as exc:
        logger.warning(f"signal_logger: write failed: {exc}")


def append_day(date_str: str, games: list[dict]) -> dict[str, Any]:
    """
    Extract per-signal performance from a list of recap game dicts and append
    to the rolling log. Safe to call multiple times — overwrites the date entry.

    Each game dict must have a 'signals' key: list of
      {"name": str, "tier": str, "won": bool, "pl": float, "result": str}
    """
    by_signal: dict[str, dict] = defaultdict(lambda: {"bets": 0, "wins": 0, "losses": 0, "pl": 0.0})
    total_bets = 0
    total_wins = 0
    total_pl = 0.0

    for game in games:
        for sig in game.get("signals", []):
            name = sig.get("name", "unknown")
            won = bool(sig.get("won", False))
            pl = float(sig.get("pl", 0))

            # Normalize signal name — strip dynamic parts like "— F5 Total: 4"
            base_name = name.split(" — ")[0].strip()

            by_signal[base_name]["bets"] += 1
            by_signal[base_name]["pl"] = round(by_signal[base_name]["pl"] + pl, 2)
            if won:
                by_signal[base_name]["wins"] += 1
            else:
                by_signal[base_name]["losses"] += 1

            total_bets += 1
            total_pl += pl
            if won:
                total_wins += 1

    entry = {
        "total_bets": total_bets,
        "wins": total_wins,
        "losses": total_bets - total_wins,
        "win_rate": round(total_wins / total_bets * 100, 1) if total_bets else 0,
        "total_pl": round(total_pl, 2),
        "by_signal": {k: v for k, v in sorted(by_signal.items())},
    }

    log = _load()
    log[date_str] = entry
    _save(log)

    logger.info(f"signal_logger: logged {total_bets} bets for {date_str} ({total_wins}W / {total_bets - total_wins}L, +${total_pl:.0f})")
    return entry


def load_rolling_stats(days: int = 30) -> dict[str, Any]:
    """
    Return per-signal aggregated stats for the last N days.
    Used by verifier.py to inject actual performance into prompts.
    """
    log = _load()
    cutoff = str(date.today() - timedelta(days=days))

    recent_entries = {d: v for d, v in log.items() if d >= cutoff}
    if not recent_entries:
        return {"days": 0, "entries": {}, "by_signal": {}, "totals": {}}

    by_signal: dict[str, dict] = defaultdict(lambda: {"bets": 0, "wins": 0, "losses": 0, "pl": 0.0})
    total_bets = total_wins = 0
    total_pl = 0.0

    for entry in recent_entries.values():
        total_bets += entry.get("total_bets", 0)
        total_wins += entry.get("wins", 0)
        total_pl += entry.get("total_pl", 0)
        for sig_name, stats in entry.get("by_signal", {}).items():
            by_signal[sig_name]["bets"] += stats.get("bets", 0)
            by_signal[sig_name]["wins"] += stats.get("wins", 0)
            by_signal[sig_name]["losses"] += stats.get("losses", 0)
            by_signal[sig_name]["pl"] = round(by_signal[sig_name]["pl"] + stats.get("pl", 0), 2)

    # Compute win rates
    for sig in by_signal.values():
        b = sig["bets"]
        sig["win_rate"] = round(sig["wins"] / b * 100, 1) if b else 0

    return {
        "days": days,
        "dates_covered": sorted(recent_entries.keys()),
        "by_signal": {
            k: v for k, v in sorted(
                by_signal.items(), key=lambda x: x[1]["bets"], reverse=True
            )
        },
        "totals": {
            "bets": total_bets,
            "wins": total_wins,
            "losses": total_bets - total_wins,
            "win_rate": round(total_wins / total_bets * 100, 1) if total_bets else 0,
            "total_pl": round(total_pl, 2),
        },
    }


def get_all_dates() -> list[str]:
    """Return all logged dates sorted ascending."""
    return sorted(_load().keys())
