"""
Real Historical Props Backfill
Fetch actual sportsbook lines from The Odds API historical endpoints
Cost: 10 credits per region per market (expensive!)
"""
import httpx
import sqlite3
from datetime import datetime, date, timedelta
from config import ODDS_API_KEY

async def fetch_historical_props(game_date: date):
    """
    Fetch real historical prop lines from The Odds API
    
    Cost per date: 7 markets × 10 credits = 70 credits
    """
    url = "https://api.the-odds-api.com/v4/historical/sports/basketball_nba/odds"
    
    params = {
        "apiKey": ODDS_API_KEY,
        "date": f"{game_date}T12:00:00Z",  # Snapshot at noon ET
        "regions": "us",
        "markets": "player_points,player_rebounds,player_assists,player_points_rebounds_assists,player_threes,player_blocks,player_steals",
        "oddsFormat": "american"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

# Example usage:
# props_data = await fetch_historical_props(date(2025, 10, 29))
# Cost: 70 credits per date
