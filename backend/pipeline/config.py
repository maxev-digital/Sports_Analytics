"""
Central configuration for the Sports Betting Analytics pipeline.

Reads all secrets and settings from environment variables with sensible defaults.
"""

import os, pathlib as _pl

# Load .env from backend root for standalone scripts (systemd uses EnvironmentFile)
_env_path = _pl.Path(__file__).parent.parent / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

from datetime import datetime

import pytz

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DB_URL: str = os.environ.get("DATABASE_URL", "")

# ---------------------------------------------------------------------------
# API keys
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
ODDS_API_KEY: str = os.environ.get("ODDS_API_KEY", "")

# ---------------------------------------------------------------------------
# Claude model name constants
# ---------------------------------------------------------------------------
HAIKU: str = "claude-haiku-4-5-20251001"   # lightweight validation pass
SONNET: str = "claude-sonnet-4-6"           # probabilistic reasoning
OPUS: str = "claude-opus-4-8"               # deep reflection / audit

# ---------------------------------------------------------------------------
# Pipeline decision thresholds
# ---------------------------------------------------------------------------
MIN_EDGE_PCT: float = 3.0    # minimum edge percentage to qualify a pick
MIN_CONFIDENCE: float = 0.52  # minimum model probability to qualify a pick

# ---------------------------------------------------------------------------
# Timezone
# ---------------------------------------------------------------------------
CST: pytz.BaseTzInfo = pytz.timezone("America/Chicago")


def now_cst() -> datetime:
    """Return the current wall-clock time as a timezone-aware CST datetime."""
    return datetime.now(tz=CST)


def to_cst(dt: datetime) -> datetime:
    """
    Convert *any* datetime object to a timezone-aware CST datetime.

    - If ``dt`` is already timezone-aware, it is converted to CST.
    - If ``dt`` is naive, it is assumed to be UTC and then converted to CST.
    """
    if dt.tzinfo is None:
        # Treat naive datetimes as UTC before converting
        dt = pytz.utc.localize(dt)
    return dt.astimezone(CST)
