import asyncio
import httpx
from datetime import datetime

async def check_nhl():
    async with httpx.AsyncClient(timeout=30) as client:
        # Get all available sports
        resp = await client.get(
            'https://api.the-odds-api.com/v4/sports',
            params={'apiKey': 'f573a2895848c38064be4af4ff5f728b'}
        )
        data = resp.json()

        print("\nAll NHL/Hockey-related sports:")
        print("=" * 80)
        hockey_sports = [s for s in data if 'hockey' in s['key'].lower() or 'nhl' in s['key'].lower()]

        for sport in hockey_sports:
            print(f"\nKey: {sport['key']}")
            print(f"Title: {sport['title']}")
            print(f"Active: {sport['active']}")

        # Check today's NHL games
        print("\n" + "=" * 80)
        print("Checking NHL games for today...")
        print("=" * 80)

        resp = await client.get(
            'https://api.the-odds-api.com/v4/sports/icehockey_nhl/odds',
            params={
                'apiKey': 'f573a2895848c38064be4af4ff5f728b',
                'regions': 'us',
                'markets': 'totals',
                'oddsFormat': 'american'
            }
        )
        games = resp.json()
        print(f"\nTotal NHL games: {len(games)}")

        if games:
            print("\nFirst 5 NHL games:")
            for g in games[:5]:
                print(f"  {g['away_team']} @ {g['home_team']}")
                print(f"  Time: {g['commence_time']}")
                print()

asyncio.run(check_nhl())
