"""
Live odds ingestion from The Odds API (v4).

Fetches current odds for MLB and WNBA games, normalises the multi-bookmaker
payload into a consistent structure, and computes consensus lines with
vig-removed implied probabilities.

Exported API
------------
fetch_live_odds(sport_key, markets)       -> list[dict]
extract_consensus_line(game, market)      -> dict | None
american_to_prob(odds)                    -> float
remove_vig(home_prob, away_prob)          -> tuple[float, float]
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional

import pytz
import requests

from pipeline.config import CST, ODDS_API_KEY

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ODDS_API_ODDS_URL = (
    "https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
)
_DEFAULT_MARKETS: list[str] = ["h2h", "spreads", "totals"]
_SUPPORTED_MARKETS: frozenset[str] = frozenset({"h2h", "spreads", "totals"})

# ---------------------------------------------------------------------------
# TTL cache — keeps each (sport_key, markets) result for 30 minutes so the
# live-edge endpoint can be polled frequently without draining API credits.
# ---------------------------------------------------------------------------
_CACHE_TTL: int = 1800  # seconds (30 min)
_odds_cache: dict[tuple, tuple[float, list]] = {}  # key -> (ts, data)

# ---------------------------------------------------------------------------
# Probability helpers
# ---------------------------------------------------------------------------


def american_to_prob(odds: int) -> float:
    """
    Convert American-format odds to an implied probability (0 < p < 1).

    Formula
    -------
    Negative odds (favourite):  p = |odds| / (|odds| + 100)
    Positive odds (underdog):   p = 100 / (odds + 100)

    Args:
        odds: American odds integer (e.g. ``-110``, ``+150``, ``200``).

    Returns:
        Implied probability as a float strictly between 0 and 1.

    Raises:
        ValueError: If *odds* is 0 (mathematically undefined).
    """
    if odds == 0:
        raise ValueError(
            "American odds of 0 are undefined — cannot convert to probability."
        )
    if odds < 0:
        abs_odds = -odds
        return abs_odds / (abs_odds + 100.0)
    return 100.0 / (odds + 100.0)


def remove_vig(home_prob: float, away_prob: float) -> tuple[float, float]:
    """
    Remove the bookmaker's overround so that probabilities sum to 1.0.

    Args:
        home_prob: Raw implied probability for the home side.
        away_prob: Raw implied probability for the away side.

    Returns:
        ``(home_prob_normed, away_prob_normed)`` — a pair of floats summing
        exactly to 1.0.

    Raises:
        ValueError: If the combined probability is zero.
    """
    total = home_prob + away_prob
    if total == 0.0:
        raise ValueError(
            "Combined implied probability is zero — cannot remove vig."
        )
    return home_prob / total, away_prob / total


# ---------------------------------------------------------------------------
# Timestamp helper
# ---------------------------------------------------------------------------


def _utc_str_to_cst(raw: str) -> str:
    """
    Parse a UTC ISO-8601 timestamp from The Odds API and return CST.

    The Odds API returns timestamps in the form ``"2024-04-07T17:05:00Z"``.
    On parse failure the original string is returned unchanged.

    Args:
        raw: UTC timestamp string from The Odds API.

    Returns:
        CST-aware ISO-8601 string, or *raw* unchanged on failure.
    """
    if not raw:
        return ""
    try:
        # The 'Z' suffix means UTC; strip it and localise explicitly
        dt_utc = datetime.strptime(raw.rstrip("Z"), "%Y-%m-%dT%H:%M:%S")
        dt_utc = pytz.utc.localize(dt_utc)
        return dt_utc.astimezone(CST).isoformat()
    except ValueError:
        logger.warning("Could not parse commence_time %r — returning raw value.", raw)
        return raw


# ---------------------------------------------------------------------------
# Bookmaker normaliser
# ---------------------------------------------------------------------------


def _normalise_bookmakers(raw_bookmakers: list[dict]) -> list[dict]:
    """
    Normalise the bookmakers list from an Odds API game response.

    Each element in the returned list:

    .. code-block:: python

        {
            "key":   "draftkings",
            "title": "DraftKings",
            "markets": {
                "h2h": [
                    {"name": "Texas Rangers", "price": -130, "point": None},
                    {"name": "Houston Astros", "price": 110,  "point": None},
                ],
                "spreads": [...],
                "totals":  [...],
            }
        }

    Args:
        raw_bookmakers: The ``bookmakers`` list from one Odds API game dict.

    Returns:
        Normalised list of bookmaker dicts.
    """
    result: list[dict] = []
    for bk in raw_bookmakers:
        markets_map: dict[str, list[dict]] = {}
        for mkt in bk.get("markets", []):
            market_key = mkt.get("key", "")
            outcomes = [
                {
                    "name": o.get("name", ""),
                    "price": o.get("price"),
                    # "point" is present for spreads/totals, None for h2h
                    "point": o.get("point"),
                }
                for o in mkt.get("outcomes", [])
            ]
            markets_map[market_key] = outcomes

        result.append(
            {
                "key": bk.get("key", ""),
                "title": bk.get("title", ""),
                "markets": markets_map,
            }
        )
    return result


# ---------------------------------------------------------------------------
# Core fetcher
# ---------------------------------------------------------------------------


def fetch_live_odds(
    sport_key: str,
    markets: Optional[list[str]] = None,
) -> list[dict]:
    """
    Fetch current odds for all live / upcoming games of a sport.

    Args:
        sport_key: The Odds API sport key, e.g. ``'baseball_mlb'``,
                   ``'basketball_wnba'``.
        markets:   Market keys to request.  Defaults to
                   ``['h2h', 'spreads', 'totals']``.

    Returns:
        List of normalised game dicts.  Each dict contains:

        .. code-block:: python

            {
                "game_id":      "abc123",
                "sport_key":    "baseball_mlb",
                "home_team":    "Texas Rangers",
                "away_team":    "Houston Astros",
                "commence_time": "2024-04-07T12:05:00-05:00",  # CST
                "bookmakers":   [...]   # see _normalise_bookmakers
            }

    Raises:
        RuntimeError:       If ``ODDS_API_KEY`` is empty.
        requests.HTTPError: On non-2xx Odds API responses.
    """
    if not ODDS_API_KEY:
        raise RuntimeError(
            "ODDS_API_KEY is not configured.  Set it in the environment or "
            "in pipeline/config.py."
        )

    if markets is None:
        markets = list(_DEFAULT_MARKETS)

    cache_key = (sport_key, tuple(sorted(markets)))
    now = time.monotonic()
    cached = _odds_cache.get(cache_key)
    if cached is not None:
        ts, data = cached
        if now - ts < _CACHE_TTL:
            logger.debug("Odds cache hit — sport=%s (%.0fs old)", sport_key, now - ts)
            return data

    url = _ODDS_API_ODDS_URL.format(sport_key=sport_key)
    params: dict[str, str] = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": ",".join(markets),
        "oddsFormat": "american",
    }

    logger.info(
        "Fetching live odds — sport=%s markets=%s", sport_key, markets
    )
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()

    remaining = resp.headers.get("x-requests-remaining", "?")
    used = resp.headers.get("x-requests-used", "?")

    raw_games: list[dict] = resp.json()
    logger.info(
        "Odds API: %d games returned | requests used=%s remaining=%s",
        len(raw_games),
        used,
        remaining,
    )

    games: list[dict] = []
    for raw in raw_games:
        games.append(
            {
                "game_id": raw.get("id", ""),
                "sport_key": raw.get("sport_key", sport_key),
                "home_team": raw.get("home_team", ""),
                "away_team": raw.get("away_team", ""),
                "commence_time": _utc_str_to_cst(
                    raw.get("commence_time", "")
                ),
                "bookmakers": _normalise_bookmakers(
                    raw.get("bookmakers", [])
                ),
            }
        )

    _odds_cache[cache_key] = (time.monotonic(), games)
    return games


# ---------------------------------------------------------------------------
# Outcome price lookup
# ---------------------------------------------------------------------------


def _find_outcome_price(
    outcomes: list[dict], team_name: str
) -> Optional[float]:
    """
    Find the American-odds price for *team_name* in an outcomes list.

    Tries exact match first; falls back to case-insensitive containment.

    Args:
        outcomes:  List of outcome dicts with ``name`` and ``price`` keys.
        team_name: Team name to look for.

    Returns:
        Price as a float, or ``None`` if not found.
    """
    # Exact match
    for o in outcomes:
        if o.get("name", "") == team_name and o.get("price") is not None:
            return float(o["price"])

    # Case-insensitive substring fallback
    team_lower = team_name.lower()
    for o in outcomes:
        if (
            team_lower in o.get("name", "").lower()
            and o.get("price") is not None
        ):
            return float(o["price"])

    return None


# ---------------------------------------------------------------------------
# Consensus builders (internal)
# ---------------------------------------------------------------------------


def _consensus_h2h_or_spread(
    bookmakers: list[dict],
    home_team: str,
    away_team: str,
    market: str,
) -> Optional[dict]:
    """
    Compute average home/away American odds across books and derive
    vig-removed implied probabilities.

    Args:
        bookmakers: Normalised bookmakers list from a game dict.
        home_team:  Home team name.
        away_team:  Away team name.
        market:     ``'h2h'`` or ``'spreads'``.

    Returns:
        Consensus dict or ``None`` if no bookmaker offers the market.
    """
    home_prices: list[float] = []
    away_prices: list[float] = []
    home_probs: list[float] = []
    away_probs: list[float] = []

    for bk in bookmakers:
        outcomes = bk.get("markets", {}).get(market, [])
        home_price = _find_outcome_price(outcomes, home_team)
        away_price = _find_outcome_price(outcomes, away_team)
        if home_price is not None and away_price is not None:
            home_prices.append(home_price)
            away_prices.append(away_price)
            # Convert THIS book's odds to probability before combining across
            # books - American odds cannot be arithmetically averaged once
            # books disagree on which side is favored (mixed positive/
            # negative signs for the same team), which previously produced
            # nonsensical results (e.g. a negative vig_pct, which is
            # impossible for a real two-way market).
            home_probs.append(american_to_prob(int(round(home_price))))
            away_probs.append(american_to_prob(int(round(away_price))))

    if not home_prices:
        logger.debug(
            "No bookmakers offer market '%s' for %s vs %s.",
            market,
            away_team,
            home_team,
        )
        return None

    avg_home = sum(home_prices) / len(home_prices)
    avg_away = sum(away_prices) / len(away_prices)

    # Average each book's already-converted probability, then remove vig once
    # on the combined average.
    home_raw = sum(home_probs) / len(home_probs)
    away_raw = sum(away_probs) / len(away_probs)
    vig_pct = (home_raw + away_raw - 1.0) * 100.0
    home_normed, away_normed = remove_vig(home_raw, away_raw)

    return {
        "market": market,
        "home_odds": round(avg_home, 1),
        "away_odds": round(avg_away, 1),
        "home_implied_prob": round(home_normed, 4),
        "away_implied_prob": round(away_normed, 4),
        "vig_pct": round(vig_pct, 3),
    }


def _consensus_totals(bookmakers: list[dict]) -> Optional[dict]:
    """
    Compute average O/U line and over/under prices across all books.

    Args:
        bookmakers: Normalised bookmakers list from a game dict.

    Returns:
        Consensus totals dict or ``None`` if no book offers totals.
    """
    over_prices: list[float] = []
    under_prices: list[float] = []
    over_probs: list[float] = []
    under_probs: list[float] = []
    lines: list[float] = []

    for bk in bookmakers:
        outcomes = bk.get("markets", {}).get("totals", [])
        over = next(
            (o for o in outcomes if o.get("name", "").lower() == "over"),
            None,
        )
        under = next(
            (o for o in outcomes if o.get("name", "").lower() == "under"),
            None,
        )
        if over is None or under is None:
            continue
        if over.get("price") is not None:
            over_prices.append(float(over["price"]))
        if under.get("price") is not None:
            under_prices.append(float(under["price"]))
        if over.get("price") is not None and under.get("price") is not None:
            # Convert THIS book's odds to probability before combining across
            # books - see the matching fix in _consensus_h2h_or_spread for why
            # arithmetic-averaging raw American odds is invalid.
            over_probs.append(american_to_prob(int(round(float(over["price"])))))
            under_probs.append(american_to_prob(int(round(float(under["price"])))))
        if over.get("point") is not None:
            lines.append(float(over["point"]))

    if not over_prices:
        return None

    avg_over = sum(over_prices) / len(over_prices)
    avg_under = sum(under_prices) / len(under_prices)
    avg_line = sum(lines) / len(lines) if lines else None

    over_raw = sum(over_probs) / len(over_probs)
    under_raw = sum(under_probs) / len(under_probs)
    vig_pct = (over_raw + under_raw - 1.0) * 100.0

    return {
        "market": "totals",
        "consensus_total": round(avg_line, 1) if avg_line is not None else None,
        "over_odds": round(avg_over, 1),
        "under_odds": round(avg_under, 1),
        "vig_pct": round(vig_pct, 3),
    }


# ---------------------------------------------------------------------------
# Public consensus extractor
# ---------------------------------------------------------------------------


def extract_consensus_line(game: dict, market: str) -> Optional[dict]:
    """
    Compute a consensus line for *market* across all bookmakers in *game*.

    Supported markets
    -----------------
    ``'h2h'``
        Head-to-head moneyline.  Returns home_odds, away_odds,
        home_implied_prob, away_implied_prob, vig_pct.

    ``'spreads'``
        Point spread.  Same fields as h2h (odds are spread-adjusted prices).

    ``'totals'``
        Over/under.  Returns consensus_total, over_odds, under_odds, vig_pct.

    Args:
        game:   A normalised game dict from :func:`fetch_live_odds`.
        market: One of ``'h2h'``, ``'spreads'``, or ``'totals'``.

    Returns:
        Consensus dict for the requested market, or ``None`` if no bookmaker
        offers the market for this game.

    Raises:
        ValueError: If *market* is not a supported key.
    """
    if market not in _SUPPORTED_MARKETS:
        raise ValueError(
            f"Unsupported market '{market}'.  "
            f"Choose from: {sorted(_SUPPORTED_MARKETS)}."
        )

    bookmakers = game.get("bookmakers", [])
    if not bookmakers:
        logger.debug(
            "Game %s has no bookmakers — cannot compute consensus.",
            game.get("game_id", "?"),
        )
        return None

    if market in ("h2h", "spreads"):
        return _consensus_h2h_or_spread(
            bookmakers,
            game.get("home_team", ""),
            game.get("away_team", ""),
            market,
        )

    return _consensus_totals(bookmakers)
