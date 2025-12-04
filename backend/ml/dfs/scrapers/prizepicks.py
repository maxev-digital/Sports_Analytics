"""
PrizePicks Scraper - Gets player prop lines from PrizePicks
"""
import requests
import json
from datetime import datetime
from typing import List, Dict

def scrape_prizepicks() -> List[Dict]:
    """
    Scrape PrizePicks NBA props from their API
    
    Returns list of props with player, stat, line, direction
    """
    plays = []
    
    try:
        # PrizePicks public API endpoint
        url = "https://api.prizepicks.com/projections"
        params = {
            'league_id': '7',  # NBA
            'per_page': 250
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse projections
        for projection in data.get('data', []):
            attrs = projection.get('attributes', {})
            
            player_name = attrs.get('description', '')
            line = float(attrs.get('line_score', 0))
            stat_type = attrs.get('stat_type', '').replace('_', ' ').title()
            
            # PrizePicks doesn't have over/under, just the line
            plays.append({
                'player_name': player_name,
                'stat_type': stat_type,
                'line': line,
                'direction': 'Higher',  # Default to Higher
                'legs': 1,
                'site': 'PrizePicks',
                'scraped_at': datetime.now().isoformat()
            })
        
        print(f"[PrizePicks] Scraped {len(plays)} props")
        return plays
        
    except Exception as e:
        print(f"[PrizePicks] Error scraping: {e}")
        return []

if __name__ == "__main__":
    props = scrape_prizepicks()
    print(f"Found {len(props)} PrizePicks props")
    if props:
        print(f"Sample: {props[0]}")
