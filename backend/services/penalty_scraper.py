"""
NFLpenalties.com scraper — per-referee, per-season penalty aggregates.

Fetches: https://www.nflpenalties.com/referee/{slug}?year={year}
Parses tfoot totals row, divides by game count for per-game rates.

Rate limit: 1 req/second. Retries once on transient HTTP errors.
Returns None on 404 (referee not in their DB for that season).
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.nflpenalties.com/referee"
HEADERS = {"User-Agent": "MaxEVSports/1.0 (research; contact maxevdigital.com)"}
REQUEST_DELAY = 1.1  # seconds between requests
TIMEOUT = 30


@dataclass
class PenaltyRecord:
    referee: str
    season: int
    games: int
    flags_per_game: float
    yards_per_game: float
    home_flags_per_game: float
    away_flags_per_game: float
    home_bias: float           # home_flags / total_flags (>0.5 = more on home team)
    declined_per_game: float
    offsetting_per_game: float


def name_to_slug(name: str) -> str:
    """'Brad Allen' → 'brad-allen'"""
    import re
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9 ]", "", slug)
    return slug.replace(" ", "-")


def _safe_int(cells: list, idx: int | None) -> int:
    if idx is None or idx >= len(cells):
        return 0
    try:
        return int(cells[idx].get_text(strip=True).replace(",", "") or 0)
    except (ValueError, AttributeError):
        return 0


def _find_col(headers: list[str], *candidates: str) -> int | None:
    for cand in candidates:
        for i, h in enumerate(headers):
            if cand in h:
                return i
    return None


def _parse_table(html: str, referee: str, season: int) -> PenaltyRecord | None:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        logger.debug("%s %d: no table found", referee, season)
        return None

    thead = table.find("thead")
    if not thead:
        return None

    headers = [th.get_text(strip=True).lower() for th in thead.find_all(["th", "td"])]

    home_flags_col = _find_col(headers, "home count", "home pen", "home flag", "hm pen")
    home_yards_col = _find_col(headers, "home yards", "home yds", "home yard")
    away_flags_col = _find_col(headers, "away count", "away pen", "away flag", "aw pen")
    away_yards_col = _find_col(headers, "away yards", "away yds", "away yard")
    dec_col        = _find_col(headers, "declined", "dec")
    offs_col       = _find_col(headers, "offsetting", "offs")

    if home_flags_col is None or away_flags_col is None:
        logger.warning("%s %d: could not identify flag columns in: %s", referee, season, headers)
        return None

    # Count games from tbody rows that have data cells
    tbody = table.find("tbody")
    if not tbody:
        return None
    game_count = sum(1 for tr in tbody.find_all("tr") if tr.find("td"))
    if game_count == 0:
        return None

    # Read aggregate totals from tfoot
    tfoot = table.find("tfoot")
    if not tfoot:
        return None
    tfoot_cells = tfoot.find("tr").find_all("td") if tfoot.find("tr") else []
    if not tfoot_cells:
        return None

    home_flags  = _safe_int(tfoot_cells, home_flags_col)
    home_yards  = _safe_int(tfoot_cells, home_yards_col)
    away_flags  = _safe_int(tfoot_cells, away_flags_col)
    away_yards  = _safe_int(tfoot_cells, away_yards_col)
    declined    = _safe_int(tfoot_cells, dec_col)
    offsetting  = _safe_int(tfoot_cells, offs_col)

    total_flags = home_flags + away_flags
    total_yards = home_yards + away_yards

    return PenaltyRecord(
        referee=referee,
        season=season,
        games=game_count,
        flags_per_game=round(total_flags / game_count, 2),
        yards_per_game=round(total_yards / game_count, 1),
        home_flags_per_game=round(home_flags / game_count, 2),
        away_flags_per_game=round(away_flags / game_count, 2),
        home_bias=round(home_flags / total_flags, 3) if total_flags > 0 else 0.5,
        declined_per_game=round(declined / game_count, 2),
        offsetting_per_game=round(offsetting / game_count, 2),
    )


def scrape_referee_season(
    referee: str,
    season: int,
    dry_run: bool = False,
) -> PenaltyRecord | None:
    """
    Fetch and parse one referee-season from NFLpenalties.com.

    Returns None on 404 or parse failure.
    Sleeps REQUEST_DELAY seconds before the HTTP call (caller should not add extra delay).
    """
    slug = name_to_slug(referee)
    url = f"{BASE_URL}/{slug}?year={season}"

    if dry_run:
        logger.info("[dry-run] Would fetch: %s", url)
        return None

    time.sleep(REQUEST_DELAY)
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 404:
            logger.debug("404 %s — %s %d not in NFLpenalties.com", url, referee, season)
            return None
        r.raise_for_status()
    except requests.HTTPError as exc:
        logger.warning("HTTP error for %s %d: %s", referee, season, exc)
        # One retry after a brief pause
        time.sleep(5)
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
        except Exception:
            logger.error("Retry also failed for %s %d", referee, season)
            return None
    except requests.RequestException as exc:
        logger.error("Request failed for %s %d: %s", referee, season, exc)
        return None

    record = _parse_table(r.text, referee, season)
    if record:
        logger.info(
            "  %s %d — %d games, %.1f flags/g, home_bias %.2f",
            referee, season, record.games, record.flags_per_game, record.home_bias,
        )
    return record
