"""Debug script to examine ESPN NFL API response structure"""
import asyncio
import httpx
import json

async def debug_nfl_api():
    """Examine what the ESPN API actually returns"""
    client = httpx.AsyncClient(timeout=30.0)
    nfl_base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

    try:
        # Get team list
        print("="*60)
        print("FETCHING NFL TEAMS LIST")
        print("="*60)

        url = f"{nfl_base_url}/teams"
        response = await client.get(url)
        response.raise_for_status()
        teams_data = response.json()

        # Get first team (e.g., CIN Bengals)
        teams = teams_data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])

        if not teams:
            print("No teams found!")
            return

        first_team = teams[0].get('team', {})
        team_abbr = first_team.get('abbreviation', '')
        team_id = first_team.get('id', '')
        team_name = first_team.get('displayName', '')

        print(f"\nFirst team: {team_name} ({team_abbr})")
        print(f"Team ID: {team_id}")

        # Check what record info is available
        print("\n" + "="*60)
        print("TEAM INFO - RECORD SECTION")
        print("="*60)
        record_data = first_team.get('record', {})
        print(json.dumps(record_data, indent=2))

        # Fetch team statistics
        print("\n" + "="*60)
        print(f"FETCHING STATISTICS FOR {team_name}")
        print("="*60)

        stats_url = f"{nfl_base_url}/teams/{team_id}/statistics"
        response = await client.get(stats_url)
        response.raise_for_status()
        stats_data = response.json()

        # Extract all stat names
        print("\nALL AVAILABLE STATS:")
        print("="*60)
        for category in stats_data.get('results', {}).get('stats', {}).get('categories', []):
            category_name = category.get('name', 'Unknown')
            print(f"\n[{category_name}]")
            for stat in category.get('stats', []):
                stat_name = stat.get('name', '')
                stat_value = stat.get('value', 0)
                stat_rank = stat.get('rank', 'N/A')
                print(f"  {stat_name}: {stat_value} (Rank: {stat_rank})")

        # Look specifically for defensive stats
        print("\n" + "="*60)
        print("SEARCHING FOR DEFENSIVE STATS (points allowed, etc.)")
        print("="*60)

        all_stats = {}
        for category in stats_data.get('results', {}).get('stats', {}).get('categories', []):
            for stat in category.get('stats', []):
                stat_name = stat.get('name', '')
                all_stats[stat_name] = stat.get('value', 0)

        # Check for various possible names
        possible_pa_names = [
            'pointsAllowed',
            'pointsAllowedPerGame',
            'ppgAllowed',
            'defensivePoints',
            'oppPoints',
            'opposingPoints',
            'totalPointsAllowed'
        ]

        print("\nChecking for points allowed stat names:")
        for name in possible_pa_names:
            if name in all_stats:
                print(f"  ✓ FOUND: {name} = {all_stats[name]}")
            else:
                print(f"  ✗ NOT FOUND: {name}")

        # Save full response for analysis
        with open('C:/Users/nashr/backend/scrapers/nba/backend/debug_nfl_api_response.json', 'w') as f:
            json.dump({
                'team_info': first_team,
                'stats_data': stats_data,
                'all_stat_names': list(all_stats.keys())
            }, f, indent=2)

        print("\n✓ Full response saved to debug_nfl_api_response.json")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(debug_nfl_api())
