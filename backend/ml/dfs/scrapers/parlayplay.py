# backend/ml/dfs/scrapers/parlayplay.py
import httpx
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/129 Safari/537.36",
]

async def scrape_parlayplay():
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
        "Referer": "https://parlayplay.io/",
        "Origin": "https://parlayplay.io"
    }

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        r = await client.get("https://api.parlayplay.io/v1/projections/active")
        data = r.json()

        plays = []
        for market in data.get("markets", []):
            player = market["player"]["full_name"]
            stat = market["stat_type"].replace("_", " ").title()
            line = float(market["line"])
            direction = "Higher" if market["selection"] == "over" else "Lower"

            plays.append({
                "player_name": player,
                "stat_type": stat,
                "line": line,
                "direction": direction,
                "legs": market.get("legs", 2),
                "site": "ParlayPlay"
            })
        return plays
