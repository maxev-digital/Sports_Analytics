#!/usr/bin/env python3
"""ESPN NHL Team Statistics Scraper - FIXED with correct stat names"""

import httpx
import csv
import logging
from pathlib import Path
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ESP

N_NHL_TEAMS = {
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
        
        stats = {'team_abbr': team_abbr, 'games_played': 0}
        
        # Parse stats from categories
        categories = data.get('results', {}).get('stats', {}).get('categories', [])
        
        for category in categories:
            cat_stats = category.get('stats', [])
            
            for stat in cat_stats:
                name = stat.get('name', '')
                value = stat.get('value')
                
                # General
                if name == 'games' and value:
                    stats['games_played'] = int(value)
                # Offensive (already per-game from ESPN)
                elif name == 'avgGoalsFor' and value:
                    stats['goals_per_game'] = float(value)
                elif name == 'powerPlayGoals' and value:
                    stats['pp_goals'] = float(value)
                elif name == 'powerPlayOpportunities' and value:
                    stats['pp_opp'] = float(value)
                elif name == 'faceoffsWon' and value:
                    stats['fo_won'] = float(value)
                elif name == 'faceoffsLost' and value:
                    stats['fo_lost'] = float(value)
                elif name == 'shots' and value:
                    stats['total_shots'] = float(value)
                # Defensive
                elif name == 'avgGoalsAgainst' and value:
                    stats['goals_against_per_game'] = float(value)
                elif name == 'saves' and value:
                    stats['saves'] = float(value)
                elif name == 'savePct' and value:
                    stats['save_pct'] = float(value) * 100  # Convert to percentage
                elif name == 'goalsAgainst' and value:
                    stats['total_ga'] = float(value)
                elif name == 'shotsAgainst' and value:
                    stats['shots_against_total'] = float(value)
        
        # Calculate derived stats
        gp = stats.get('games_played', 1)
        if gp > 0:
            # Shots per game
            if 'total_shots' in stats:
                stats['shots_per_game'] = stats['total_shots'] / gp
            # Shots against per game
            if 'shots_against_total' in stats:
                stats['shots_against_per_game'] = stats['shots_against_total'] / gp
            # PP%
            if 'pp_goals' in stats and 'pp_opp' in stats and stats['pp_opp'] > 0:
                stats['power_play_pct'] = (stats['pp_goals'] / stats['pp_opp']) * 100
            # PK% (need to get from special teams page or calculate)
            # For now use a placeholder since ESPN doesn't give PK stats directly
            stats['penalty_kill_pct'] = 80.0  # Placeholder
            # Faceoff %
            fo_won = stats.get('fo_won', 0)
            fo_lost = stats.get('fo_lost', 0)
            if fo_won + fo_lost > 0:
                stats['faceoff_win_pct'] = (fo_won / (fo_won + fo_lost)) * 100
            # Shooting %
            if 'total_shots' in stats and stats['total_shots'] > 0 and 'total_ga' in stats:
                goals = stats.get('goals_per_game', 0) * gp
                stats['shooting_pct'] = (goals / stats['total_shots']) * 100
        
        return stats

async def fetch_all_teams() -> List[Dict]:
    """Fetch stats for all NHL teams"""
    all_stats = []
    
    for abbr, team_id in ESPN_NHL_TEAMS.items():
        try:
            logger.info(f"Fetching stats for {abbr.upper()}...")
            stats = await fetch_team_stats(team_id, abbr)
            if stats.get('games_played', 0) > 0:
                all_stats.append(stats)
        except Exception as e:
            logger.error(f"Error fetching stats for {abbr}: {e}")
            continue
    
    return all_stats

async def main():
    """Main scraper function"""
    logger.info("="*60)
    logger.info("ESPN NHL TEAM STATS SCRAPER - FIXED VERSION")
    logger.info("="*60)
    
    teams = await fetch_all_teams()
    
    if not teams:
        logger.error("No teams fetched")
        return
    
    # Save to CSV
    output_dir = Path(__file__).parent.parent.parent / "data" / "raw" / "nhl"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "current_team_stats_espn.csv"
    
    fields = ['team_abbr', 'games_played', 'goals_per_game', 'goals_against_per_game',
              'power_play_pct', 'penalty_kill_pct', 'shots_per_game', 'shots_against_per_game',
              'faceoff_win_pct', 'shooting_pct', 'save_pct']
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.headerheader()
        writer.writerows(teams)
    
    logger.info("="*60)
    logger.info(f"✅ Saved {len(teams)} teams to {output_file}")
    logger.info("="*60)
    
    # Print top 5
    logger.info("\nTop 5 by Goals Per Game:")
    for team in sorted(teams, key=lambda x: x.get('goals_per_game', 0), reverse=True)[:5]:
        abbr = team.get('team_abbr', '').upper()
        gpg = team.get('goals_per_game', 0)
        pp = team.get('power_play_pct', 0)
        shots = team.get('shots_per_game', 0)
        sv = team.get('save_pct', 0)
        logger.info(f"{abbr:5} GPG: {gpg:.2f}  PP%: {pp:.1f}  Shots/G: {shots:.1f}  SV%: {sv:.1f}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
