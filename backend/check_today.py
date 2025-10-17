import asyncio
import httpx
from datetime import datetime

async def check_today():
    async with httpx.AsyncClient(timeout=30) as client:
        # Check regular NBA endpoint
        resp = await client.get(
            'https://api.the-odds-api.com/v4/sports/basketball_nba/odds',
            params={
                'apiKey': 'f573a2895848c38064be4af4ff5f728b',
                'regions': 'us',
                'markets': 'totals',
                'oddsFormat': 'american'
            }
        )
        data = resp.json()
        print(f"\nNBA endpoint - Total games: {len(data)}")
        print(f"Today's date: {datetime.now().strftime('%Y-%m-%d')}")

        if data:
            print("\nFirst 5 games:")
            for g in data[:5]:
                print(f"  {g['away_team']} @ {g['home_team']}")
                print(f"  Time: {g['commence_time']}")
                print()

asyncio.run(check_today())
