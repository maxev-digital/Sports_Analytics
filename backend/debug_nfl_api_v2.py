"""Debug script to find the correct ESPN endpoints for W-L record and points allowed"""
import asyncio
import httpx
import json

async def test_endpoints():
    """Try different ESPN endpoints to find record and defensive stats"""
    client = httpx.AsyncClient(timeout=30.0)
    nfl_base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

    try:
        # Try 1: Get team detail page (not just list)
        print("="*60)
        print("TEST 1: Team Detail Endpoint")
        print("="*60)
        team_id = "22"  # Arizona Cardinals
        url = f"{nfl_base_url}/teams/{team_id}"
        response = await client.get(url)
        team_data = response.json()

        # Check for record
        team_info = team_data.get('team', {})
        record = team_info.get('record', {})
        print(f"\nTeam: {team_info.get('displayName', 'N/A')}")
        print(f"Record data: {json.dumps(record, indent=2)}")

        # Check for standing
        standing = team_info.get('standingSummary', 'N/A')
        print(f"Standing Summary: {standing}")

        # Try 2: Standings endpoint
        print("\n" + "="*60)
        print("TEST 2: Standings Endpoint")
        print("="*60)
        url = f"{nfl_base_url}/standings"
        response = await client.get(url)
        standings_data = response.json()

        # Find Cardinals in standings
        for conf in standings_data.get('children', []):
            for div in conf.get('standings', {}).get('entries', []):
                team = div.get('team', {})
                if team.get('id') == team_id:
                    print(f"\nFound in standings:")
                    print(f"Team: {team.get('displayName')}")
                    print(f"Stats: {json.dumps(div.get('stats', []), indent=2)[:500]}")
                    stats_dict = {s['name']: s['displayValue'] for s in div.get('stats', [])}
                    print(f"\nWins: {stats_dict.get('wins', 'N/A')}")
                    print(f"Losses: {stats_dict.get('losses', 'N/A')}")
                    print(f"Points For: {stats_dict.get('pointsFor', 'N/A')}")
                    print(f"Points Against: {stats_dict.get('pointsAgainst', 'N/A')}")
                    print(f"Differential: {stats_dict.get('differential', 'N/A')}")
                    break

        # Try 3: Scoreboard to see opponent scoring
        print("\n" + "="*60)
        print("TEST 3: Scoreboard/Schedule Endpoint")
        print("="*60)
        url = f"{nfl_base_url}/teams/{team_id}/schedule"
        response = await client.get(url)
        schedule_data = response.json()

        print("\nGames played:")
        games_played = 0
        total_points_allowed = 0

        for event in schedule_data.get('events', [])[:10]:  # First 10 games
            competition = event.get('competitions', [{}])[0]
            status = competition.get('status', {}).get('type', {}).get('completed', False)

            if not status:
                continue  # Skip future games

            games_played += 1
            for competitor in competition.get('competitors', []):
                is_cardinals = competitor.get('id') == team_id
                score = int(competitor.get('score', 0))
                home_away = "Home" if competitor.get('homeAway') == 'home' else "Away"

                if is_cardinals:
                    cardinals_score = score
                else:
                    opponent_score = score
                    opponent_name = competitor.get('team', {}).get('displayName', 'Unknown')

            total_points_allowed += opponent_score
            print(f"  Game {games_played}: vs {opponent_name} - Cardinals {cardinals_score}, Opponent {opponent_score}")

        if games_played > 0:
            avg_points_allowed = total_points_allowed / games_played
            print(f"\nCalculated PA/G: {avg_points_allowed:.1f}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_endpoints())
