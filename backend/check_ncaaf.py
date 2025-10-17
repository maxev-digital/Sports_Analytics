import asyncio
import httpx

async def check_ncaaf():
    async with httpx.AsyncClient(timeout=30) as client:
        # Get all available sports
        resp = await client.get(
            'https://api.the-odds-api.com/v4/sports',
            params={'apiKey': 'f573a2895848c38064be4af4ff5f728b'}
        )
        data = resp.json()

        print("\nAll Football-related sports:")
        print("=" * 80)
        football_sports = [s for s in data if 'football' in s['key'].lower() or 'ncaaf' in s['key'].lower()]

        for sport in football_sports:
            print(f"\nKey: {sport['key']}")
            print(f"Title: {sport['title']}")
            print(f"Active: {sport['active']}")

        # Check NCAAF games
        print("\n" + "=" * 80)
        print("Checking NCAAF games for today...")
        print("=" * 80)

        # Try americanfootball_ncaaf
        try:
            resp = await client.get(
                'https://api.the-odds-api.com/v4/sports/americanfootball_ncaaf/odds',
                params={
                    'apiKey': 'f573a2895848c38064be4af4ff5f728b',
                    'regions': 'us',
                    'markets': 'totals',
                    'oddsFormat': 'american'
                }
            )
            games = resp.json()
            print(f"\nTotal NCAAF games: {len(games)}")

            if games:
                print("\nFirst 5 NCAAF games:")
                for g in games[:5]:
                    print(f"  {g['away_team']} @ {g['home_team']}")
                    print(f"  Time: {g['commence_time']}")
                    print()
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(check_ncaaf())
