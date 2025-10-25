#!/usr/bin/env python3
"""
The Odds API Scraper
Collects betting lines for NBA totals
"""

import requests
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OddsAPIScraper:
    """The Odds API - FREE TIER: 500 requests/month"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('ODDS_API_KEY')
        self.base_url = 'https://api.the-odds-api.com/v4'
        
        if not self.api_key:
            raise ValueError("ODDS_API_KEY not found in .env file")
    
    def get_nba_odds(self):
        """Get current NBA totals from multiple sportsbooks"""
        print("Fetching NBA odds from The Odds API...")
        
        url = f'{self.base_url}/sports/basketball_nba/odds/'
        
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'totals',
            'oddsFormat': 'american'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Error: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return pd.DataFrame()
            
            data = response.json()
            
            # Check remaining requests
            remaining = response.headers.get('x-requests-remaining')
            used = response.headers.get('x-requests-used')
            print(f"API Usage: {used} used, {remaining} remaining")
            
            if not data:
                print("⚠️  No NBA games scheduled today")
                return pd.DataFrame()
            
            # Parse odds data
            odds_data = []
            
            for game in data:
                game_id = game['id']
                home_team = game['home_team']
                away_team = game['away_team']
                commence_time = game['commence_time']
                
                # Get totals from each bookmaker
                for bookmaker in game.get('bookmakers', []):
                    sportsbook = bookmaker['key']
                    
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'totals':
                            for outcome in market.get('outcomes', []):
                                odds_data.append({
                                    'game_id': game_id,
                                    'home_team': home_team,
                                    'away_team': away_team,
                                    'commence_time': commence_time,
                                    'sportsbook': sportsbook,
                                    'total_line': outcome.get('point'),
                                    'side': outcome.get('name'),
                                    'price': outcome.get('price'),
                                    'timestamp': datetime.now().isoformat()
                                })
            
            df = pd.DataFrame(odds_data)
            
            if not df.empty:
                print(f"✓ Retrieved odds for {df['game_id'].nunique()} NBA games")
                print(f"✓ Sportsbooks: {df['sportsbook'].unique().tolist()}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return pd.DataFrame()
    
    def get_consensus_total(self, game_id, df):
        """Calculate consensus total across sportsbooks"""
        game_odds = df[df['game_id'] == game_id]
        
        if game_odds.empty:
            return None
        
        # Get most common line
        consensus = game_odds['total_line'].mode()
        
        if len(consensus) > 0:
            return float(consensus.iloc[0])
        else:
            return float(game_odds['total_line'].mean())
    
    def save_odds(self, sport):
        """Scrape and save odds"""
        if sport.upper() == 'NBA':
            odds_df = self.get_nba_odds()
        else:
            raise ValueError(f"Unknown sport: {sport}")
        
        if odds_df.empty:
            print(f"⚠️  No {sport} odds to save")
            return None
        
        # Create output directory
        output_dir = 'backend/data/raw/odds'
        os.makedirs(output_dir, exist_ok=True)
        
        # Save to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{output_dir}/{sport.lower()}_odds_{timestamp}.csv'
        odds_df.to_csv(filename, index=False)
        
        print(f"✓ Saved: {filename}")
        
        # Also save as latest
        latest_file = f'{output_dir}/{sport.lower()}_odds_latest.csv'
        odds_df.to_csv(latest_file, index=False)
        print(f"✓ Saved: {latest_file}")
        
        return odds_df


if __name__ == "__main__":
    print("="*60)
    print("ODDS API SCRAPER")
    print("="*60)
    
    try:
        scraper = OddsAPIScraper()
        
        # Get NBA odds
        nba_odds = scraper.save_odds('NBA')
        
        if nba_odds is not None and not nba_odds.empty:
            print("\n📊 Sample games:")
            for game_id in nba_odds['game_id'].unique()[:3]:
                game = nba_odds[nba_odds['game_id'] == game_id].iloc[0]
                consensus = scraper.get_consensus_total(game_id, nba_odds)
                print(f"  {game['away_team']} @ {game['home_team']}")
                print(f"    Total: {consensus}")
        
        print("\n✅ COMPLETE")
        
    except ValueError as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nGet your free API key:")
        print("1. Go to: https://the-odds-api.com/")
        print("2. Sign up (free)")
        print("3. Copy your API key")
        print("4. Add to .env: ODDS_API_KEY=your_key_here")