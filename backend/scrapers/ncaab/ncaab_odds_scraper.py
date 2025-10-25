#!/usr/bin/env python3
"""
NCAA Basketball Odds Scraper
Fetches betting lines from The Odds API
"""

import requests
import pandas as pd
from datetime import datetime

class NCAABOddsScraper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.sport = "basketball_ncaab"
        self.base_url = "https://api.the-odds-api.com/v4/sports"
        
    def fetch_odds(self):
        """Fetch current NCAA Basketball odds"""
        print("🔑 Using Odds API")
        
        url = f"{self.base_url}/{self.sport}/odds"
        
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'totals',
            'oddsFormat': 'american'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                print("   ⚠️  No games found (might be offseason)")
                return pd.DataFrame()
            
            games = []
            for game in data:
                home_team = game.get('home_team', '')
                away_team = game.get('away_team', '')
                commence_time = game.get('commence_time', '')
                
                # Get totals from bookmakers
                bookmakers = game.get('bookmakers', [])
                totals = []
                
                for book in bookmakers:
                    for market in book.get('markets', []):
                        if market.get('key') == 'totals':
                            for outcome in market.get('outcomes', []):
                                if outcome.get('name') == 'Over':
                                    totals.append(outcome.get('point'))
                
                if totals:
                    avg_total = sum(totals) / len(totals)
                    
                    games.append({
                        'Home_Team': home_team,
                        'Away_Team': away_team,
                        'DateTime': commence_time,
                        'Market_Total': avg_total,
                        'Num_Books': len(totals)
                    })
            
            df = pd.DataFrame(games)
            
            if len(df) > 0:
                # Parse datetime
                df['DateTime'] = pd.to_datetime(df['DateTime'])
                df['Date'] = df['DateTime'].dt.strftime('%m/%d')
                df['Time'] = df['DateTime'].dt.strftime('%I:%M %p')
            
            print(f"   ✅ Found {len(df)} games with odds")
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ API request failed: {str(e)}")
            return pd.DataFrame()
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return pd.DataFrame()
