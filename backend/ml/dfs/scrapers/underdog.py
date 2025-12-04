# backend/ml/dfs/scrapers/underdog.py
import httpx
from . import random_ua

async def scrape_underdog():
    headers = {
        "User-Agent": random_ua(),
        "Accept": "application/json"
    }

    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.underdogfantasy.com/v1/prop_markets?league=nba", headers=headers)
        data = r.json()

        plays = []
        for market in data.get("markets", []):
            for outcome in market["outcomes"]:
                plays.append({
                    "player_name": outcome["player"]["name"],
                    "stat_type": outcome["stat_type"].title(),
                    "line": outcome["value"],
                    "direction": "Higher" if outcome["type"] == "over" else "Lower",
                    "site": "Underdog"
                })
        return plays
