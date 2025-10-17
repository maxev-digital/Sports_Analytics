import asyncio
import httpx
import json

async def check_sports():
    async with httpx.AsyncClient(timeout=30) as client:
        # Get all available sports
        resp = await client.get(
            'https://api.the-odds-api.com/v4/sports',
            params={'apiKey': 'f573a2895848c38064be4af4ff5f728b'}
        )
        data = resp.json()

        print("\nAll Basketball-related sports:")
        print("=" * 80)
        basketball_sports = [s for s in data if 'basketball' in s['key'].lower() or 'nba' in s['key'].lower()]

        for sport in basketball_sports:
            print(f"\nKey: {sport['key']}")
            print(f"Title: {sport['title']}")
            print(f"Active: {sport['active']}")
            print(f"Has Outrights: {sport.get('has_outrights', False)}")

asyncio.run(check_sports())
