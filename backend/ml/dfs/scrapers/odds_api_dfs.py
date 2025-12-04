"""
The Odds API DFS Scraper
Fetches player props from PrizePicks, Underdog, Betr, and DraftKings Pick6
"""
import os
import requests
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# DFS bookmaker keys from The Odds API
DFS_BOOKMAKERS = {
    'prizepicks': 'PrizePicks',
    'underdog': 'Underdog Fantasy',
    'betr': 'Betr Picks',
    'draftkings_pick6': 'DraftKings Pick6'
}

# Player prop markets to fetch
PROP_MARKETS = [
    'player_points',
    'player_rebounds', 
    'player_assists',
    'player_threes',
    'player_blocks',
    'player_steals',
    'player_points_rebounds_assists',  # PRA
    'player_pass_tds',  # NFL
    'player_pass_yds',  # NFL
    'player_rush_yds',  # NFL
    'player_receptions',  # NFL
]

def fetch_dfs_props_from_odds_api(
    sport: str = 'basketball_nba',
    api_key: str = None
) -> List[Dict]:
    """
    Fetch DFS player props from The Odds API
    
    Args:
        sport: Sport key (basketball_nba, americanfootball_nfl, icehockey_nhl)
        api_key: The Odds API key (get from environment or config)
    
    Returns:
        List of prop dictionaries
    """
    if not api_key:
        api_key = os.getenv('ODDS_API_KEY')
        
    if not api_key:
        logger.error("No Odds API key provided")
        return []
    
    all_props = []
    base_url = "https://api.the-odds-api.com/v4"
    
    try:
        # First, get upcoming games
        events_url = f"{base_url}/sports/{sport}/events"
        events_params = {
            'apiKey': api_key,
            'dateFormat': 'iso'
        }
        
        events_response = requests.get(events_url, params=events_params, timeout=30)
        events_response.raise_for_status()
        events = events_response.json()
        
        logger.info(f"Found {len(events)} upcoming {sport} events")
        
        # For each event, fetch player props from DFS bookmakers
        for event in events[:10]:  # Limit to first 10 events to save API calls
            event_id = event['id']
            
            for market in PROP_MARKETS[:3]:  # Start with main markets
                odds_url = f"{base_url}/sports/{sport}/events/{event_id}/odds"
                odds_params = {
                    'apiKey': api_key,
                    'regions': 'us',
                    'markets': market,
                    'bookmakers': ','.join(DFS_BOOKMAKERS.keys()),
                    'oddsFormat': 'american'
                }
                
                try:
                    odds_response = requests.get(odds_url, params=odds_params, timeout=30)
                    odds_response.raise_for_status()
                    odds_data = odds_response.json()
                    
                    # Parse bookmakers data
                    for bookmaker_data in odds_data.get('bookmakers', []):
                        bookmaker_key = bookmaker_data['key']
                        bookmaker_name = DFS_BOOKMAKERS.get(bookmaker_key, bookmaker_key)
                        
                        for market_data in bookmaker_data.get('markets', []):
                            for outcome in market_data.get('outcomes', []):
                                prop = {
                                    'site': bookmaker_name,
                                    'player_name': outcome.get('description', ''),
                                    'stat_type': market.replace('player_', '').replace('_', ' ').title(),
                                    'line': float(outcome.get('point', 0)),
                                    'direction': 'Over' if outcome.get('name') == 'Over' else 'Under',
                                    'price': outcome.get('price', -110),
                                    'event_id': event_id,
                                    'game': f"{event['home_team']} vs {event['away_team']}",
                                    'commence_time': event['commence_time'],
                                    'scraped_at': datetime.now().isoformat()
                                }
                                all_props.append(prop)
                                
                except Exception as e:
                    logger.error(f"Error fetching odds for event {event_id}, market {market}: {e}")
                    continue
        
        logger.info(f"[Odds API] Scraped {len(all_props)} DFS props")
        return all_props
        
    except Exception as e:
        logger.error(f"[Odds API] Error: {e}")
        return []

def scrape_all_dfs_sports() -> Dict[str, List[Dict]]:
    """
    Scrape DFS props from all supported sports
    
    Returns:
        Dictionary with sport keys and prop lists
    """
    sports = {
        'nba': 'basketball_nba',
        'nfl': 'americanfootball_nfl',
        'nhl': 'icehockey_nhl'
    }
    
    results = {}
    api_key = os.getenv('ODDS_API_KEY')
    
    for sport_name, sport_key in sports.items():
        logger.info(f"Scraping {sport_name.upper()} DFS props...")
        props = fetch_dfs_props_from_odds_api(sport_key, api_key)
        results[sport_name] = props
        
    return results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test the scraper
    props = fetch_dfs_props_from_odds_api('basketball_nba')
    print(f"Fetched {len(props)} NBA DFS props")
    
    if props:
        print(f"Sample prop: {props[0]}")
