# backend/ml/dfs/scrapers/sleeper.py
import httpx

async def scrape_sleeper():
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.sleeper.com/projections/nba")
        data = r.json()
        
        plays = []
        for projection in data.get("projections", []):
            plays.append({
                "player_name": projection.get("player_name", ""),
                "stat_type": projection.get("stat_type", "").title(),
                "line": float(projection.get("line", 0)),
                "direction": "Higher" if projection.get("direction") == "over" else "Lower",
                "site": "Sleeper"
            })
        return plays
