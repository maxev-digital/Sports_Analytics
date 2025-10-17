"""Test script to see what the Odds API returns"""
import asyncio
import httpx
import json

async def test_api():
    async with httpx.AsyncClient() as client:
        # Test odds endpoint
        print("=" * 70)
        print("TESTING ODDS ENDPOINT")
        print("=" * 70)
        url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
        params = {
            "apiKey": "f573a2895848c38064be4af4ff5f728b",
            "regions": "us",
            "markets": "totals",
            "oddsFormat": "american"
        }
        response = await client.get(url, params=params)
        odds_data = response.json()
        print(f"\nOdds data type: {type(odds_data)}")
        print(f"Number of games: {len(odds_data)}")
        if odds_data:
            print(f"\nFirst game structure:")
            print(json.dumps(odds_data[0], indent=2))

        # Test scores endpoint
        print("\n" + "=" * 70)
        print("TESTING SCORES ENDPOINT")
        print("=" * 70)
        url = "https://api.the-odds-api.com/v4/sports/basketball_nba/scores"
        params = {
            "apiKey": "f573a2895848c38064be4af4ff5f728b",
            "daysFrom": 1
        }
        response = await client.get(url, params=params)
        scores_data = response.json()
        print(f"\nScores data type: {type(scores_data)}")
        print(f"Number of scores: {len(scores_data)}")
        if scores_data:
            print(f"\nFirst score structure:")
            print(json.dumps(scores_data[0], indent=2))

if __name__ == "__main__":
    asyncio.run(test_api())
