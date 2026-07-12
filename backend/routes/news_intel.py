"""
Injury & News Intelligence API — /api/news/*

Fetches from ESPN news + injury endpoints, runs two-agent analysis,
stores results in news_intel table, returns structured betting insights.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/news", tags=["news-intel"])

# ---------------------------------------------------------------------------
# ESPN endpoints
# ---------------------------------------------------------------------------

ESPN_SPORTS = {
    "mlb":  "baseball/mlb",
    "nba":  "basketball/nba",
    "nfl":  "football/nfl",
    "nhl":  "ice-hockey/nhl",
    "wnba": "basketball/wnba",
}

ESPN_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

_HTTP_TIMEOUT = 8.0


async def _espn_get(url: str) -> dict:
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as c:
        r = await c.get(url, headers=ESPN_HEADERS)
        r.raise_for_status()
        return r.json()


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------

async def _fetch_news(sport: str) -> list[dict]:
    path = ESPN_SPORTS.get(sport)
    if not path:
        return []
    try:
        d = await _espn_get(
            f"https://site.api.espn.com/apis/site/v2/sports/{path}/news?limit=20"
        )
        items = []
        for a in d.get("articles", []):
            items.append({
                "source": "espn_news",
                "external_id": str(a.get("id", "")),
                "headline": a.get("headline", ""),
                "summary": a.get("description", ""),
                "url": a.get("links", {}).get("web", {}).get("href", ""),
                "sport": sport,
                "published_at": a.get("published", ""),
                "news_type": "general",
                "teams": [t.get("displayName", "") for t in a.get("categories", []) if t.get("type") == "team"],
                "players": [],
                "injury_status": None,
            })
        return items
    except Exception as e:
        logger.warning("ESPN news fetch failed for %s: %s", sport, e)
        return []


async def _fetch_injuries(sport: str) -> list[dict]:
    path = ESPN_SPORTS.get(sport)
    if not path:
        return []
    try:
        d = await _espn_get(
            f"https://site.api.espn.com/apis/site/v2/sports/{path}/injuries"
        )
        items = []
        for team_block in d.get("injuries", []):
            team_name = team_block.get("displayName", "")
            for inj in team_block.get("injuries", []):
                athlete = inj.get("athlete", {})
                player_name = athlete.get("displayName", "")
                status = inj.get("status", "")
                short = inj.get("shortComment", "")
                long_c = inj.get("longComment", "")
                pub = inj.get("date", "")
                summary = short or long_c[:300]
                headline = f"{player_name} ({team_name}) — {status}: {short[:100]}" if short else f"{player_name} ({team_name}) listed as {status}"
                items.append({
                    "source": "espn_injuries",
                    "external_id": str(inj.get("id", "")),
                    "headline": headline,
                    "summary": long_c or short,
                    "url": "",
                    "sport": sport,
                    "published_at": pub,
                    "news_type": "injury",
                    "teams": [team_name],
                    "players": [player_name],
                    "injury_status": status,
                })
        return items
    except Exception as e:
        logger.warning("ESPN injuries fetch failed for %s: %s", sport, e)
        return []


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_db():
    from pipeline.db.connection import execute_query, execute_write
    return execute_query, execute_write


def _get_live_odds_for_teams(teams: list[str]) -> str:
    """Pull current odds context for given team names from the odds cache."""
    try:
        from pipeline.ingestion.live_odds import fetch_live_odds
        context_lines = []
        for sport_key in ("baseball_mlb", "basketball_wnba"):
            games = fetch_live_odds(sport_key)
            for g in games:
                home = g.get("home_team", "")
                away = g.get("away_team", "")
                if not any(t.lower() in home.lower() or t.lower() in away.lower() for t in teams):
                    continue
                books = g.get("bookmakers", [])
                if not books:
                    continue
                b = books[0]
                for mkt in b.get("markets", []):
                    mtype = mkt.get("market_key", "")
                    outcomes = mkt.get("outcomes", [])
                    if mtype == "h2h" and outcomes:
                        prices = {o["name"]: o["price"] for o in outcomes}
                        context_lines.append(
                            f"{away} @ {home} | ML: {away} {prices.get(away,'?')} / {home} {prices.get(home,'?')}"
                        )
                    elif mtype == "totals" and outcomes:
                        for o in outcomes:
                            if o.get("name") == "Over":
                                context_lines.append(
                                    f"{away} @ {home} | Total: O{o.get('point','?')} {o.get('price','?')}"
                                )
        return "\n".join(context_lines) if context_lines else ""
    except Exception:
        return ""


def _upsert_item(item: dict) -> Optional[int]:
    """Insert or update a news item in the DB. Returns the row id."""
    execute_query, execute_write = _get_db()
    try:
        rows = execute_query(
            "SELECT id FROM news_intel WHERE source=%s AND external_id=%s",
            (item["source"], item["external_id"])
        )
        pub = item.get("published_at") or None
        teams_arr = item.get("teams") or []
        players_arr = item.get("players") or []
        if rows:
            row_id = rows[0]["id"]
            execute_write(
                """UPDATE news_intel SET headline=%s, summary=%s, url=%s,
                   sport=%s, teams=%s, players=%s, injury_status=%s,
                   news_type=%s, published_at=%s
                   WHERE id=%s""",
                (item["headline"], item["summary"], item.get("url",""),
                 item["sport"], teams_arr, players_arr,
                 item.get("injury_status"), item["news_type"], pub, row_id)
            )
            return row_id
        else:
            rows2 = execute_query(
                """INSERT INTO news_intel
                   (source, external_id, headline, summary, url, sport,
                    teams, players, injury_status, news_type, published_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id""",
                (item["source"], item["external_id"], item["headline"],
                 item["summary"], item.get("url",""), item["sport"],
                 teams_arr, players_arr,
                 item.get("injury_status"), item["news_type"], pub)
            )
            return rows2[0]["id"] if rows2 else None
    except Exception as e:
        logger.error("DB upsert failed: %s", e)
        return None


def _row_to_dict(row: dict) -> dict:
    for k in ("published_at", "fetched_at", "analyzed_at"):
        if row.get(k) and hasattr(row[k], "isoformat"):
            row[k] = row[k].isoformat()
    return dict(row)


# ---------------------------------------------------------------------------
# Background analysis task
# ---------------------------------------------------------------------------

def _run_analysis_bg(news_id: int, headline: str, summary: str,
                     classification: dict, teams: list[str]):
    """Runs Sonnet analysis in background and saves to DB."""
    try:
        execute_query, execute_write = _get_db()
        from pipeline.agents.news_analyzer import analyze_betting_angle
        odds_ctx = _get_live_odds_for_teams(teams)
        analysis = analyze_betting_angle(headline, summary, classification, odds_ctx)
        if analysis:
            execute_write(
                "UPDATE news_intel SET sonnet_analysis=%s::jsonb, analyzed_at=NOW() WHERE id=%s",
                (json.dumps(analysis), news_id)
            )
            logger.info("Sonnet analysis saved for news_id=%s action=%s",
                        news_id, analysis.get("recommended_action","?"))
    except Exception as e:
        logger.error("Background Sonnet analysis failed id=%s: %s", news_id, e)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/feed")
async def get_news_feed(
    sport: str = Query("all", description="mlb|nba|nfl|nhl|wnba|all"),
    limit: int = Query(80, ge=1, le=200),
):
    """
    Return stored news/injury items from DB — fast, no ESPN fetch.
    Call POST /api/news/refresh to pull fresh ESPN data in the background.
    """
    execute_query, _ = _get_db()
    sport_filter = "" if sport == "all" else "AND sport = %s"
    params: tuple = (limit,) if sport == "all" else (sport, limit)
    rows = execute_query(
        f"""SELECT id, source, headline, summary, url, sport, teams, players,
               injury_status, news_type, published_at, fetched_at,
               haiku_classification, sonnet_analysis, analyzed_at
            FROM news_intel
            {sport_filter}
            ORDER BY COALESCE(published_at, fetched_at) DESC
            LIMIT %s""",
        params,
    )
    items = [_row_to_dict(dict(r)) for r in (rows or [])]
    return {"items": items, "total": len(items)}


async def _do_espn_refresh(sport: str) -> None:
    """ESPN fetch + DB upsert — runs as a background task so it never blocks."""
    sports = list(ESPN_SPORTS.keys()) if sport == "all" else [sport]
    for s in sports:
        items: list[dict] = []
        items.extend(await _fetch_injuries(s))
        items.extend(await _fetch_news(s))
        for item in items:
            if item.get("external_id"):
                _upsert_item(item)


@router.post("/refresh")
async def refresh_feed(
    sport: str = Query("all"),
    background_tasks: BackgroundTasks = None,
):
    """Trigger a background ESPN fetch + upsert. Returns immediately."""
    background_tasks.add_task(_do_espn_refresh, sport)
    return {"status": "refreshing", "sport": sport}


@router.post("/analyze/{news_id}")
async def analyze_item(news_id: int, background_tasks: BackgroundTasks):
    """
    Run two-agent analysis on a stored news item.
    Haiku classification runs synchronously (fast).
    Sonnet betting analysis runs in background (3-8 seconds).
    Returns haiku result immediately; poll /api/news/item/{id} for sonnet result.
    """
    execute_query, execute_write = _get_db()
    rows = execute_query(
        "SELECT * FROM news_intel WHERE id = %s", (news_id,)
    )
    if not rows:
        raise HTTPException(404, f"News item {news_id} not found")

    row = dict(rows[0])
    headline = row["headline"]
    summary = row.get("summary") or ""
    teams = row.get("teams") or []

    # Agent 1: Haiku classification (sync, fast)
    classification = row.get("haiku_classification") or {}
    if not classification:
        from pipeline.agents.news_analyzer import classify_news
        classification = classify_news(headline, summary)
        if classification:
            execute_write(
                "UPDATE news_intel SET haiku_classification=%s::jsonb WHERE id=%s",
                (json.dumps(classification), news_id)
            )

    # Agent 2: Sonnet analysis (background)
    if not row.get("sonnet_analysis"):
        background_tasks.add_task(
            _run_analysis_bg, news_id, headline, summary, classification, teams
        )

    return {
        "id": news_id,
        "headline": headline,
        "classification": classification,
        "analysis_status": "complete" if row.get("sonnet_analysis") else "pending",
        "analysis": row.get("sonnet_analysis"),
    }


@router.get("/item/{news_id}")
async def get_item(news_id: int):
    """Get a single news item with full analysis (poll after /analyze/{id})."""
    execute_query, _ = _get_db()
    rows = execute_query(
        """SELECT id, source, headline, summary, url, sport, teams, players,
               injury_status, news_type, published_at, fetched_at,
               haiku_classification, sonnet_analysis, analyzed_at
            FROM news_intel WHERE id = %s""",
        (news_id,)
    )
    if not rows:
        raise HTTPException(404, f"News item {news_id} not found")
    return _row_to_dict(dict(rows[0]))


@router.get("/insights")
async def get_insights(
    sport: str = Query("all"),
    confidence: str = Query("all", description="high|medium|low|all"),
    action: str = Query("all", description="BET NOW|MONITOR|AVOID|all"),
    limit: int = Query(30, ge=1, le=100),
):
    """
    Return analyzed items that have Sonnet betting analysis, newest first.
    Filterable by sport, confidence level, and recommended action.
    """
    execute_query, _ = _get_db()
    clauses = ["analyzed_at IS NOT NULL", "sonnet_analysis IS NOT NULL"]
    params: list = []

    if sport != "all":
        clauses.append("sport = %s")
        params.append(sport)
    if confidence != "all":
        clauses.append("sonnet_analysis->>'confidence' = %s")
        params.append(confidence)
    if action != "all":
        clauses.append("sonnet_analysis->>'recommended_action' = %s")
        params.append(action)

    params.append(limit)
    where = " AND ".join(clauses)
    rows = execute_query(
        f"""SELECT id, source, headline, sport, teams, players, injury_status,
               news_type, published_at, analyzed_at,
               haiku_classification, sonnet_analysis
            FROM news_intel
            WHERE {where}
            ORDER BY analyzed_at DESC
            LIMIT %s""",
        params
    )
    return {
        "insights": [_row_to_dict(dict(r)) for r in (rows or [])],
        "total": len(rows or [])
    }


@router.get("/stats")
async def get_feed_stats():
    """Summary stats for the news intel table."""
    execute_query, _ = _get_db()
    rows = execute_query(
        """SELECT
            COUNT(*) AS total_items,
            COUNT(CASE WHEN analyzed_at IS NOT NULL THEN 1 END) AS analyzed,
            COUNT(CASE WHEN news_type='injury' THEN 1 END) AS injuries,
            COUNT(CASE WHEN sonnet_analysis->>'recommended_action'='BET NOW' THEN 1 END) AS bet_now_count,
            MAX(fetched_at) AS last_fetch
           FROM news_intel"""
    )
    return dict(rows[0]) if rows else {}
