"""
News tool — fetches recent headlines and beat reporter updates via ESPN RSS feeds.

No API key required. Falls back to empty list on any error (fail open).
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 5.0

# ESPN RSS feed URLs by sport
_ESPN_RSS: dict[str, str] = {
    "nba":   "https://www.espn.com/espn/rss/nba/news",
    "nfl":   "https://www.espn.com/espn/rss/nfl/news",
    "mlb":   "https://www.espn.com/espn/rss/mlb/news",
    "nhl":   "https://www.espn.com/espn/rss/nhl/news",
    "ncaaf": "https://www.espn.com/espn/rss/ncf/news",
    "ncaab": "https://www.espn.com/espn/rss/ncb/news",
    "wnba":  "https://www.espn.com/espn/rss/wnba/news",
    "mma":   "https://www.espn.com/espn/rss/mma/news",
    "tennis":"https://www.espn.com/espn/rss/tennis/news",
}

_NS = {"content": "http://purl.org/rss/1.0/modules/content/"}


def _parse_pub_date(date_str: str) -> datetime | None:
    """Parse RFC 2822 date string from RSS to UTC datetime."""
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
    ):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def _hours_ago(dt: datetime) -> float:
    """Return how many hours ago a UTC-aware datetime is."""
    now = datetime.now(tz=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).total_seconds() / 3600


def get_news(teams: list[str], sport: str, hours: int = 24) -> dict[str, Any]:
    """
    Fetch recent headlines filtered to one or both teams from ESPN RSS.

    Args:
        teams: List of team name strings to filter headlines for.
        sport: Platform sport key (e.g. "nba", "nfl").
        hours: Only return articles published within this window.

    Returns:
        {
          "teams": list[str],
          "sport": str,
          "articles": [{"title": str, "summary": str, "published": str, "hours_ago": float}],
          "source": "espn_rss"
        }
        Returns empty articles list on any error (fail open).
    """
    sport_key = sport.lower()
    rss_url = _ESPN_RSS.get(sport_key)
    if not rss_url:
        return {"teams": teams, "sport": sport, "articles": [], "source": "unsupported"}

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(rss_url, headers={"User-Agent": "MaxEV-Agent/1.0"})
            resp.raise_for_status()
            xml_text = resp.text
    except httpx.HTTPError as exc:
        logger.warning("news_tool HTTP error: %s", exc)
        return {"teams": teams, "sport": sport, "articles": [], "source": "espn_rss_error"}
    except Exception as exc:
        logger.error("news_tool unexpected error: %s", exc)
        return {"teams": teams, "sport": sport, "articles": [], "source": "error"}

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.warning("news_tool XML parse error: %s", exc)
        return {"teams": teams, "sport": sport, "articles": [], "source": "parse_error"}

    search_terms = [t.lower() for t in teams]
    # Also add short names (last word of each team)
    for t in list(search_terms):
        last = t.split()[-1] if t else ""
        if last and last not in search_terms:
            search_terms.append(last)

    articles: list[dict[str, Any]] = []
    for item in root.iter("item"):
        title_el = item.find("title")
        desc_el = item.find("description")
        pub_el = item.find("pubDate")

        title = (title_el.text or "").strip() if title_el is not None else ""
        desc = (desc_el.text or "").strip() if desc_el is not None else ""
        pub_str = (pub_el.text or "").strip() if pub_el is not None else ""

        # Age filter
        pub_dt = _parse_pub_date(pub_str) if pub_str else None
        if pub_dt and _hours_ago(pub_dt) > hours:
            continue

        # Team relevance filter
        combined = (title + " " + desc).lower()
        if not any(term in combined for term in search_terms):
            continue

        articles.append({
            "title": title,
            "summary": desc[:300] if desc else "",
            "published": pub_str,
            "hours_ago": round(_hours_ago(pub_dt), 1) if pub_dt else 99.0,
        })

        if len(articles) >= 8:
            break

    articles.sort(key=lambda a: a["hours_ago"])

    return {
        "teams": teams,
        "sport": sport,
        "articles": articles,
        "source": "espn_rss",
    }
