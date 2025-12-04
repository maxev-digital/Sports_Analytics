#!/usr/bin/env python3
"""
Fetch current NHL team stats from official NHL API
Replaces BallDontLie dependency with free NHL API
"""

import httpx
import json
import csv
from pathlib import Path

async def fetch_all_team_stats():
    """Fetch current season stats for all NHL teams"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get standings which has team stats
        url = "https://api-web.nhle.com/v1/standings/now"
        response = await client.get(url)
        data = response.json()
        
        teams_data = []
        
        for standing in data.get('standings', []):
            team_abbr = standing.get('teamAbbrev', {}).get('default', '').lower()
            team_name = standing.get('teamName', {}).get('default', '')
            
            # Get the team's detailed stats
            team_url = f"https://api-web.nhle.com/v1/club-stats/{team_abbr.upper()}/now"
            try:
                team_response = await client.get(team_url)
                team_stats = team_response.json()
                
                # Extract stats from skaters section
                skaters = team_stats.get('skaters', [])
                if skaters:
                    # Team totals are usually the last entry or aggregate
                    # But we need to calculate from standings data
                    pass
                    
            except:
                pass
            
            # Use standings data which has most of what we need
            games_played = standing.get('gamesPlayed', 0)
            goals_for = standing.get('goalFor', 0)
            goals_against = standing.get('goalAgainst', 0)
            
            # Calculate per-game stats
            gpg = goals_for / games_played if games_played > 0 else 0
            gapg = goals_against / games_played if games_played > 0 else 0
            
            # Get special teams stats from standings
            pp_pct = standing.get('powerPlayPct', 0.0)
            pk_pct = standing.get('penaltyKillPct', 0.0)
            
            # Get shots from standings if available
            shots_for_per_game = standing.get('shotsForPerGame', 0.0)
            shots_against_per_game = standing.get('shotsAgainstPerGame', 0.0)
            
            # Calculate shooting and save percentage
            faceoff_win_pct = standing.get('faceoffWinPct', 0.0)
            
            teams_data.append({
                'team_abbr': team_abbr,
                'team_name': team_name,
                'games_played': games_played,
                'goals_per_game': gpg,
                'goals_against_per_game': gapg,
                'power_play_pct': pp_pct,
                'penalty_kill_pct': pk_pct,
                'shots_per_game': shots_for_per_game,
                'shots_against_per_game': shots_against_per_game,
                'faceoff_win_pct': faceoff_win_pct
            })
        
        return teams_data

async def main():
    print("Fetching current NHL team stats from official NHL API...")
    teams = await fetch_all_team_stats()
    
    # Save to CSV
    output_file = Path("data/raw/nhl/current_team_stats.csv")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=teams[0].keys())
        writer.writeheader()
        writer.writerows(teams)
    
    print(f"✅ Saved {len(teams)} teams to {output_file}")
    
    # Print sample
    for team in teams[:5]:
        print(f"{team['team_name']}: GPG={team['goals_per_game']:.2f}, PP%={team['power_play_pct']:.1f}, Shots/G={team['shots_per_game']:.1f}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
