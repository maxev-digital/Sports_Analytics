#!/usr/bin/env python3
"""Test script for NBA ESPNs client"""
import sys
sys.path.append('.')
from espn_nba_client import ESPNnbaClient

# Test NBA ESPNs client
client = ESPNnbaClient()

print('Testing ESPNs NBA client...')

# Test a few teams
teams_to_test = ['BOS', 'LAL', 'GSW', 'MIA']  # Boston, Lakers, Warriors, Heat

for team_abbr in teams_to_test:
    try:
        print(f'\n--- Testing {team_abbr} ---')
        stats = client.fetch_team_season_stats(team_abbr)

        if stats:
            print(f'✅ {stats.get("team_name", "Unknown")}')
            print(f'  Record: {stats.get("wins", 0)}-{stats.get("losses", 0)}')
            print(f'  PPG: {stats.get("season_stats", {}).get("points_per_game", 0):.1f}')
            print(f'  FG%: {stats.get("season_stats", {}).get("fg_pct", 0):.1f}%')
            print(f'  DS: {stats.get("form_trend", "UNKNOWN")}')
        else:
            print(f'❌ No stats for {team_abbr}')

    except Exception as e:
        print(f'❌ Error testing {team_abbr}: {e}')

print('\nNBA ESPNs client test complete!')
