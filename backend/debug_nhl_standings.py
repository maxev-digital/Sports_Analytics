"""Debug script to find the correct NHL team standings endpoint"""
import asyncio
import httpx
import json

async def test_nhl_standings_endpoints():
    """Test different NHL API endpoints to find team standings"""
    client = httpx.AsyncClient(timeout=30.0)

    try:
        team_abbr = "bos"
        season = "20242025"

        # Try 1: Standings endpoint
        print("="*60)
        print("TEST 1: NHL Standings Endpoint")
        print("="*60)
        url = "https://api-web.nhle.com/v1/standings/now"
        print(f"Fetching: {url}\n")

        response = await client.get(url)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Top-level keys: {list(data.keys())}\n")

            # Look for Boston
            standings = data.get('standings', [])
            for team in standings:
                if team.get('teamAbbrev', {}).get('default', '').lower() == team_abbr:
                    print(f"Found Boston in standings:")
                    print(json.dumps(team, indent=2)[:1500])
                    break

        # Try 2: Team schedule/stats endpoint
        print("\n" + "="*60)
        print("TEST 2: NHL Team Season Stats")
        print("="*60)
        url = f"https://api-web.nhle.com/v1/club-schedule-season/{team_abbr}/{season}"
        print(f"Fetching: {url}\n")

        response = await client.get(url)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Top-level keys: {list(data.keys())}\n")
            print(json.dumps(data, indent=2)[:1000])

        # Try 3: Standings by date
        print("\n" + "="*60)
        print("TEST 3: NHL Standings (by date)")
        print("="*60)
        url = f"https://api-web.nhle.com/v1/standings/{season}"
        print(f"Fetching: {url}\n")

        response = await client.get(url)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Top-level keys: {list(data.keys())}\n")
            print(json.dumps(data, indent=2)[:1000])

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_nhl_standings_endpoints())
