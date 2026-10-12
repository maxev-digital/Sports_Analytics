"""
Live Player Props — fetches from The Odds API per-event endpoint.

GET /api/f5/live-props?sport=baseball_mlb&markets=pitcher_strikeouts,batter_hits_over_under
"""
import os
import time
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)
router = APIRouter()

ODDS_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API = "https://api.the-odds-api.com/v4"

# Cache props for 10 minutes to conserve credits
_PROPS_CACHE: dict = {}
CACHE_TTL = 600

# Available prop markets by sport
SPORT_MARKETS: dict[str, list[str]] = {
    "baseball_mlb": [
        "pitcher_strikeouts",
        "batter_home_runs",
        "batter_hits_over_under",
        "batter_total_bases",
        "batter_rbis",
        "batter_runs_scored",
        "batter_stolen_bases",
    ],
    "americanfootball_nfl": [
        "player_pass_yds",
        "player_pass_tds",
        "player_rush_yds",
        "player_receptions",
        "player_reception_yds",
        "player_anytime_td",
    ],
    "americanfootball_ncaaf": [
        "player_pass_yds",
        "player_pass_tds",
        "player_rush_yds",
        "player_receptions",
        "player_reception_yds",
    ],
    "basketball_nba": [
        "player_points",
        "player_rebounds",
        "player_assists",
        "player_threes",
        "player_points_rebounds_assists",
    ],
}


@router.get("/live-props")
async def get_live_props(
    sport: str = "baseball_mlb",
    markets: Optional[str] = None,
    limit: int = 100,
):
    """
    Fetch live player props from The Odds API.
    Returns props grouped by player with lines from multiple books.
    """
    if not ODDS_KEY:
        return {"props": [], "error": "No ODDS_API_KEY configured"}

    cache_key = f"{sport}:{markets or 'default'}"
    now = time.time()
    cached = _PROPS_CACHE.get(cache_key)
    if cached and (now - cached["ts"]) < CACHE_TTL:
        return {**cached["data"], "cached": True}

    # Get available markets for this sport
    available = SPORT_MARKETS.get(sport, [])
    if not available:
        return {"props": [], "error": f"No prop markets configured for {sport}"}

    # Use requested markets or default to first 3
    if markets:
        requested = [m.strip() for m in markets.split(",")]
    else:
        requested = available[:3]

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Step 1: Get today's events for this sport
            events_resp = await client.get(
                f"{ODDS_API}/sports/{sport}/events",
                params={"apiKey": ODDS_KEY},
            )
            if events_resp.status_code != 200:
                return {"props": [], "error": f"Events API error: {events_resp.status_code}"}

            events = events_resp.json()
            if not isinstance(events, list):
                return {"props": [], "error": "No events found"}

            # Step 2: Fetch props per market per event
            # Odds API sometimes fails on multi-market requests, so fetch each market separately
            all_props: list[dict] = []

            for event in events[:6]:
                event_id = event.get("id", "")
                home = event.get("home_team", "")
                away = event.get("away_team", "")
                commence = event.get("commence_time", "")

                # Fetch each market individually to avoid API rejecting multi-market combos
                combined_bookmakers: list[dict] = []
                for market in requested:
                    resp = await client.get(
                        f"{ODDS_API}/sports/{sport}/events/{event_id}/odds",
                        params={
                            "apiKey": ODDS_KEY,
                            "regions": "us",
                            "markets": market,
                            "oddsFormat": "american",
                        },
                    )
                    if resp.status_code != 200:
                        continue
                    bks = resp.json().get("bookmakers", [])
                    combined_bookmakers.extend(bks)

                event_data = {"bookmakers": combined_bookmakers}
                bookmakers = event_data.get("bookmakers", [])

                # Aggregate outcomes across books by player+market+point
                player_lines: dict[str, dict] = {}

                for bk in bookmakers:
                    book_key = bk.get("key", "")
                    for mkt in bk.get("markets", []):
                        market_key = mkt.get("key", "")
                        for outcome in mkt.get("outcomes", []):
                            player = outcome.get("description", "")
                            name = outcome.get("name", "")  # Over/Under
                            point = outcome.get("point")
                            price = outcome.get("price")

                            if not player or point is None:
                                continue

                            prop_key = f"{player}|{market_key}|{point}"
                            if prop_key not in player_lines:
                                player_lines[prop_key] = {
                                    "player": player,
                                    "market": market_key,
                                    "line": point,
                                    "home_team": home,
                                    "away_team": away,
                                    "commence_time": commence,
                                    "books": {},
                                }

                            if book_key not in player_lines[prop_key]["books"]:
                                player_lines[prop_key]["books"][book_key] = {}
                            player_lines[prop_key]["books"][book_key][name.lower()] = price

                # Convert to list and compute best lines
                for pk, prop in player_lines.items():
                    books = prop["books"]
                    over_prices = [b.get("over", 0) for b in books.values() if "over" in b]
                    under_prices = [b.get("under", 0) for b in books.values() if "under" in b]

                    all_props.append({
                        "player": prop["player"],
                        "market": prop["market"],
                        "line": prop["line"],
                        "home_team": prop["home_team"],
                        "away_team": prop["away_team"],
                        "commence_time": prop["commence_time"],
                        "book_count": len(books),
                        "best_over": max(over_prices) if over_prices else None,
                        "best_under": max(under_prices) if under_prices else None,
                        "books": {
                            bk: {"over": vals.get("over"), "under": vals.get("under")}
                            for bk, vals in books.items()
                        },
                    })

            # Sort by player name
            all_props.sort(key=lambda p: (p["commence_time"], p["player"], p["market"]))

            result = {
                "sport": sport,
                "markets_requested": requested,
                "prop_count": len(all_props),
                "games_scanned": min(len(events), 6),
                "props": all_props[:limit],
                "cached": False,
            }

            _PROPS_CACHE[cache_key] = {"ts": now, "data": result}
            return result

    except Exception as exc:
        logger.error("live_props error: %s", exc)
        return {"props": [], "error": str(exc)}
