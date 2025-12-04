#!/usr/bin/env python3
"""
ESPN NHL Team Statistics Scraper
Fetches current season stats for all 32 NHL teams using ESPN's free API
Replaces BallDontLie dependency
"""

import httpx
import csv
import logging
from pathlib import Path
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ESPN team IDs for NHL
ESPN_NHL_TEAMS = {
    'ana': 25, 'bos': 6, 'buf': 7, 'cgy': 20, 'car': 12, 'chi': 16,
    'col': 21, 'cbj': 29, 'dal': 25, 'det': 17, 'edm': 22, 'fla': 13,
    'lak': 26, 'min': 30, 'mtl': 8, 'nsh': 18, 'njd': 1, 'nyi': 2,
    'nyr': 3, 'ott': 9, 'phi': 4, 'pit': 5, 'sjs': 28, 'sea': 55,
    'stl': 19, 'tbl': 14, 'tor': 10, 'uta': 54, 'van': 23, 'vgk': 37,
    'wsh': 15, 'wpg': 52
}

async def fetch_team_stats(team_id: int, team_abbr: str) -> Dict:
    """Fetch stats for a single team from ESPN"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{team_id}/statistics"
        response = await client.get(url)
        data = response.json()
        
        stats = {}
        stats['team_abbr'] = team_abbr
        
        # Parse stats from categories
        categories = data.get('results', {}).get('stats', {}).get('categories', [])
        
        for category in categories:
            cat_name = category.get('name', '')
            cat_stats = category.get('stats', [])
            
            for stat in cat_stats:
                name = stat.get('name', '')
                value = stat.get('value', 0.0)
                per_game = stat.get('perGameValue')
                
                # Extract key stats
                if name == 'games':
                    stats['games_played'] = int(value)
                elif name == 'goalsPerGame':
                    stats['goals_per_game'] = float(value)
                elif name == 'goalsAgainstPerGame':
                    stats['goals_against_per_game'] = float(value)
                elif name == 'powerPlayGoals':
                    stats['pp_goals'] = float(value)
                elif name == 'powerPlayOpportunities':
                    stats['pp_opportunities'] = float(value)
                elif name == 'penaltyKillGoals':
                    stats['pk_goals_allowed'] = float(value)
                elif name == 'timesShorthanded':
                    stats['times_shorthanded'] = float(value)
                elif name == 'shotsPerGame':
                    stats['shots_per_game'] = float(value)
                elif name == 'shotsAgainstPerGame':
                    stats['shots_against_per_game'] = float(value)
                elif name == 'faceOffWinPercentage':
                    stats['faceoff_win_pct'] = float(value)
                elif name == 'shootingPct':
                    stats['shooting_pct'] = float(value)
                elif name == 'savePercentage':
                    stats['save_pct'] = float(value)
        
        # Calculate PP% and PK%
        if 'pp_goals' in stats and 'pp_opportunities' in stats and stats['pp_opportunities'] > 0:
            stats['power_play_pct'] = (stats['pp_goals'] / stats['pp_opportunities']) * 100
        else:
            stats['power_play_pct'] = 0.0
            
        if 'pk_goals_allowed' in stats and 'times_shorthanded' in stats and stats['times_shorthanded'] > 0:
            stats['penalty_kill_pct'] = (1 - (stats['pk_goals_allowed'] / stats['times_shorthanded'])) * 100
        else:
            stats['penalty_kill_pct'] = 0.0
        
        return stats

async def fetch_all_teams() -> List[Dict]:
    """Fetch stats for all NHL teams"""
    all_stats = []
    
    for abbr, team_id in ESPN_NHL_TEAMS.items():
        try:
            logger.info(f"Fetching stats for {abbr.upper()}...")
            stats = await fetch_team_stats(team_id, abbr)
            all_stats.append(stats)
        except Exception as e:
            logger.error(f"Error fetching stats for {abbr}: {e}")
            continue
    
    return all_stats

async def main():
    """Main scraper function"""
    logger.info("="*60)
    logger.info("ESPN NHL TEAM STATS SCRAPER")
    logger.info("Fetching current season stats for all 32 NHL teams...")
    logger.info("="*60)
    
    teams = await fetch_all_teams()
    
    if not teams:
        logger.error("No teams fetched")
        return
    
    # Save to CSV
    output_dir = Path(__file__).parent.parent.parent / "data" / "raw" / "nhl"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "current_team_stats_espn.csv"
    
    # Define fields
    fields = ['team_abbr', 'games_played', 'goals_per_game', 'goals_against_per_game',
              'power_play_pct', 'penalty_kill_pct', 'shots_per_game', 'shots_against_per_game',
              'faceoff_win_pct', 'shooting_pct', 'save_pct']
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(teams)
    
    logger.info("="*60)
    logger.info(f"✅ Saved {len(teams)} teams to {output_file}")
    logger.info("="*60)
    
    # Print sample
    logger.info("\nSample data:")
    for team in sorted(teams, key=lambda x: x.get('goals_per_game', 0), reverse=True)[:5]:
        abbr = team.get('team_abbr', '').upper()
        gpg = team.get('goals_per_game', 0)
        pp = team.get('power_play_pct', 0)
        pk = team.get('penalty_kill_pct', 0)
        shots = team.get('shots_per_game', 0)
        logger.info(f"{abbr:5} GPG: {gpg:.2f}  PP%: {pp:.1f}  PK%: {pk:.1f}  Shots/G: {shots:.1f}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
