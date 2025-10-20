"""Debug script to examine NHL API response structure"""
import asyncio
import httpx
import json

async def test_nhl_api():
    """Test NHL API endpoints to understand response structure"""
    client = httpx.AsyncClient(timeout=30.0)

    try:
        # Test Boston Bruins
        team_abbr = "bos"
        season = "20242025"

        print("="*60)
        print(f"Testing NHL API for {team_abbr.upper()} - Season {season}")
        print("="*60)

        # Test the club-stats endpoint
        url = f"https://api-web.nhle.com/v1/club-stats/{team_abbr}/{season}/2"
        print(f"\nFetching: {url}")

        response = await client.get(url)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # Print the entire response structure
            print("\n" + "="*60)
            print("FULL API RESPONSE:")
            print("="*60)
            print(json.dumps(data, indent=2)[:3000])  # First 3000 chars

            print("\n" + "="*60)
            print("EXTRACTING KEY FIELDS:")
            print("="*60)

            # Try to find standings data
            if 'standings' in data:
                print("\nStandings found:")
                print(json.dumps(data['standings'], indent=2))
            else:
                print("\nNo 'standings' key found")
                print(f"Top-level keys: {list(data.keys())}")

            # Try to find skaters data
            if 'skaters' in data:
                print("\nSkaters found (first entry):")
                if data['skaters']:
                    print(json.dumps(data['skaters'][0], indent=2))
            else:
                print("\nNo 'skaters' key found")

            # Try to find goalies data
            if 'goalies' in data:
                print("\nGoalies found (first entry):")
                if data['goalies']:
                    print(json.dumps(data['goalies'][0], indent=2))
            else:
                print("\nNo 'goalies' key found")
        else:
            print(f"\nError: Status {response.status_code}")
            print(response.text[:500])

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_nhl_api())
