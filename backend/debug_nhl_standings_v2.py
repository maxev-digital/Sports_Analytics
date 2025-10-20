"""Debug script to find the correct NHL team standings endpoint with redirects"""
import asyncio
import httpx
import json

async def test_nhl_standings_with_redirects():
    """Test NHL API endpoints with redirect following"""
    client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    try:
        team_abbr = "bos"

        # Try 1: Standings endpoint (following redirects)
        print("="*60)
        print("TEST 1: NHL Standings Endpoint (with redirects)")
        print("="*60)
        url = "https://api-web.nhle.com/v1/standings/now"
        print(f"Fetching: {url}\n")

        response = await client.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Final URL: {response.url}\n")

        if response.status_code == 200:
            data = response.json()
            print(f"Top-level keys: {list(data.keys())}\n")

            # Look for Boston
            standings = data.get('standings', [])
            if standings:
                print(f"Found {len(standings)} teams in standings\n")
                for team in standings[:3]:  # Show first 3 teams
                    print(f"Team: {team.get('teamName', {}).get('default', 'N/A')}")
                    print(f"  Abbrev: {team.get('teamAbbrev', {}).get('default', 'N/A')}")

                # Find Boston specifically
                for team in standings:
                    team_abb = team.get('teamAbbrev', {}).get('default', '').lower()
                    if team_abb == team_abbr:
                        print("\n" + "="*60)
                        print("BOSTON BRUINS DETAILED STANDINGS:")
                        print("="*60)
                        print(json.dumps(team, indent=2))
                        break

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_nhl_standings_with_redirects())
