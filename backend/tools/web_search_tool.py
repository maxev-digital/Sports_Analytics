"""
Web search tool — fetches real-time search results via Tavily API.

Used by the AI analyst agent when it needs information beyond ESPN RSS feeds:
beat reporter updates, breaking news, injury timelines, coaching decisions, etc.

Fail open: returns empty results on any error.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 10.0
_TAVILY_URL = "https://api.tavily.com/search"
_MAX_RESULTS = 5


def web_search(query: str, max_results: int = _MAX_RESULTS) -> dict[str, Any]:
    """
    Search the web for real-time information using Tavily.

    Args:
        query: Natural language search query.
        max_results: Maximum number of results to return (1-10).

    Returns:
        {
          "query": str,
          "results": [{"title": str, "url": str, "content": str}],
          "source": "tavily"
        }
        Returns empty results list on any error (fail open).
    """
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        logger.warning("web_search_tool: TAVILY_API_KEY not set")
        return {"query": query, "results": [], "source": "no_api_key"}

    max_results = min(max(max_results, 1), 10)

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(
                _TAVILY_URL,
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic",
                    "include_answer": True,
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.warning("web_search_tool HTTP error: %s", exc)
        return {"query": query, "results": [], "source": "tavily_error"}
    except Exception as exc:
        logger.error("web_search_tool unexpected error: %s", exc)
        return {"query": query, "results": [], "source": "error"}

    results = []
    for item in data.get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": item.get("content", "")[:500],
        })

    answer = data.get("answer", "")

    return {
        "query": query,
        "answer": answer[:800] if answer else "",
        "results": results,
        "source": "tavily",
    }
