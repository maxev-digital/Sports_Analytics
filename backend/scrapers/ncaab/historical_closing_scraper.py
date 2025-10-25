#!/usr/bin/env python3
"""
NCAA Basketball Historical Closing Lines Scraper
Uses Odds API Pro plan to fetch historical closing totals
Then matches with actual game results for regression analysis
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import glob

class HistoricalClosingLinesScraper:
    def __init__(self, api_key, season_year=2024):
        """
        Initialize scraper
        
        Args:
            api_key: Your Odds API key (Pro plan)
            season_year: End year of season (2024 = 2023-24 season)
        """
        self.api_key = api_key
        self.season_year = season_year
        self.base_url = "https://api.the-odds-api.com/v4/historical/sports/basketball_ncaab/odds"
        self.requests_used = 0
        self.requests_remaining = None
        
    def get_season_dates(self):
        """Generate date range for NCAA season"""
        start_year = self.season_year - 1
        
        # NCAA season: November to early April
        start_date = datetime(start_year, 11, 1)
        end_date = datetime(self.season_year, 4, 10)
        
        # Create list of dates to query (sample every 3 days to save API calls)
        dates = []
        current = start_date
        
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=3)  # Sample every 3 days
        
        return dates
    
    def fetch_closing_lines_for_date(self, date):
        """
        Fetch closing lines for a specific date
        
        Args:
            date: datetime object
        
        Returns:
            List of games with closing totals
        """
        # Format date for API (12:00 PM on game day to catch most closings)
        date_str = date.replace(hour=12, minute=0, second=0).isoformat() + 'Z'
        
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'totals',
            'oddsFormat': 'american',
            'dateFormat': 'iso',
            'date': date_str
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            
            # Track API usage
            self.requests_used += 1
            if 'x-requests-remaining' in response.headers:
                self.requests_remaining = response.headers['x-requests-remaining']
            
            if response.status_code != 200:
                print(f"   WARNING: API error {response.status_code} for {date.strftime('%Y-%m-%d')}")
                print(f"   Response: {response.text[:200]}")
                return []

            response_json = response.json()

            # Check if API returned an error message
            if isinstance(response_json, dict) and 'message' in response_json:
                print(f"   API message: {response_json['message']}")
                return []

            # Historical API wraps data in 'data' field
            if isinstance(response_json, dict) and 'data' in response_json:
                data = response_json['data']
            else:
                data = response_json

            if not data:
                return []

            games = []

            for game in data:
                home_team = game.get('home_team', '')
                away_team = game.get('away_team', '')
                game_date = game.get('commence_time', '')
                
                # Parse game date
                if game_date:
                    game_dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                    game_date_str = game_dt.strftime('%Y-%m-%d')
                else:
                    game_date_str = date.strftime('%Y-%m-%d')
                
                # Extract closing totals from all bookmakers
                bookmakers = game.get('bookmakers', [])
                closing_totals = []
                
                for book in bookmakers:
                    for market in book.get('markets', []):
                        if market.get('key') == 'totals':
                            for outcome in market.get('outcomes', []):
                                if outcome.get('name') == 'Over':
                                    closing_totals.append(outcome.get('point'))
                
                if closing_totals:
                    # Use consensus (average) closing total
                    avg_closing = sum(closing_totals) / len(closing_totals)
                    
                    games.append({
                        'Date': game_date_str,
                        'Home_Team': home_team,
                        'Away_Team': away_team,
                        'Closing_Total': round(avg_closing, 1),
                        'Num_Books': len(closing_totals)
                    })
            
            return games
            
        except Exception as e:
            print(f"   ERROR: Error fetching {date.strftime('%Y-%m-%d')}: {str(e)}")
            return []
    
    def scrape_season(self, save_frequency=10, auto_confirm=False):
        """
        Scrape entire season of closing lines
        
        Args:
            save_frequency: Save progress every N requests
        """
        print("="*70)
        print(f"NCAA BASKETBALL HISTORICAL CLOSING LINES SCRAPER")
        print("="*70)
        print(f"   Season: {self.season_year-1}-{self.season_year}")
        print(f"   Source: Odds API (Pro Plan)")
        print("")

        dates = self.get_season_dates()
        print(f"   Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
        print(f"   Total dates to query: {len(dates)}")
        print(f"   WARNING: This will use ~{len(dates)} API requests")
        print("")
        
        if not auto_confirm:
            confirm = input("Continue? (y/N): ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                return pd.DataFrame()
        else:
            print("   Auto-confirmed - starting scrape...")
        
        all_games = []
        
        for i, date in enumerate(dates, 1):
            print(f"   Progress: {i}/{len(dates)} - {date.strftime('%Y-%m-%d')}", end="")
            
            games = self.fetch_closing_lines_for_date(date)
            
            if games:
                all_games.extend(games)
                print(f" - Found {len(games)} games")
            else:
                print(f" - No games")
            
            # Show API usage
            if self.requests_remaining:
                print(f"      API Requests Remaining: {self.requests_remaining}")
            
            # Save progress periodically
            if i % save_frequency == 0:
                self._save_progress(all_games, i)
            
            # Rate limiting (1 request per second)
            if i < len(dates):
                time.sleep(1)
        
        print(f"\n Scraping complete!")
        print(f"   Total requests used: {self.requests_used}")
        print(f"   Games with closing lines: {len(all_games)}")
        
        if len(all_games) > 0:
            df = pd.DataFrame(all_games)
            
            # Remove duplicates
            df = df.drop_duplicates(subset=['Date', 'Home_Team', 'Away_Team'])
            
            print(f"   Unique games: {len(df)}")
            print(f"   Closing total range: {df['Closing_Total'].min():.1f} - {df['Closing_Total'].max():.1f}")
            print(f"   Average closing total: {df['Closing_Total'].mean():.1f}")
            
            return df
        else:
            print("ERROR: No games found")
            return pd.DataFrame()
    
    def _save_progress(self, games, checkpoint):
        """Save progress checkpoint"""
        if not games:
            return
        
        output_dir = 'backend/data/historical'
        os.makedirs(output_dir, exist_ok=True)
        
        df = pd.DataFrame(games)
        filename = f"{output_dir}/closing_lines_checkpoint_{checkpoint}.csv"
        df.to_csv(filename, index=False)
        print(f"      Saved checkpoint: {filename}")
    
    def match_with_actual_results(self, closing_lines_df):
        """
        Match closing lines with actual game results
        
        Args:
            closing_lines_df: DataFrame with closing lines
        
        Returns:
            DataFrame with closing lines and actual results merged
        """
        print("\n MATCHING CLOSING LINES WITH ACTUAL RESULTS")
        print("-"*70)

        # Find actual game results file
        results_pattern = "backend/data/historical/game_results_*_season_*.csv"
        results_files = glob.glob(results_pattern)

        if not results_files:
            print("ERROR: No game results file found")
            print(f"   Expected pattern: {results_pattern}")
            return pd.DataFrame()
        
        results_file = max(results_files)
        print(f"   Loading results from: {os.path.basename(results_file)}")
        
        results_df = pd.read_csv(results_file)
        print(f"   Results games: {len(results_df)}")
        print(f"   Closing lines: {len(closing_lines_df)}")
        
        # Normalize team names for matching
        closing_lines_df['Home_Team_norm'] = closing_lines_df['Home_Team'].str.strip().str.lower()
        closing_lines_df['Away_Team_norm'] = closing_lines_df['Away_Team'].str.strip().str.lower()
        results_df['Home_Team_norm'] = results_df['Home_Team'].str.strip().str.lower()
        results_df['Away_Team_norm'] = results_df['Away_Team'].str.strip().str.lower()
        
        # Merge on date and teams
        merged = pd.merge(
            closing_lines_df,
            results_df[['Date', 'Home_Team_norm', 'Away_Team_norm', 'Actual_Total']],
            on=['Date', 'Home_Team_norm', 'Away_Team_norm'],
            how='inner'
        )
        
        # Calculate deviation
        merged['Deviation'] = merged['Actual_Total'] - merged['Closing_Total']
        merged['Abs_Deviation'] = abs(merged['Deviation'])
        
        # Drop normalized columns
        merged = merged.drop(columns=['Home_Team_norm', 'Away_Team_norm'])
        
        print(f"\n Matched {len(merged)} games")
        print(f"   Match rate: {len(merged)/len(results_df)*100:.1f}%")

        if len(merged) > 0:
            print(f"\n DEVIATION STATISTICS:")
            print(f"   Mean deviation: {merged['Deviation'].mean():.2f} points")
            print(f"   Mean absolute deviation: {merged['Abs_Deviation'].mean():.2f} points")
            print(f"   Std deviation: {merged['Deviation'].std():.2f} points")
            print(f"   Games >20 pts from closing: {(merged['Abs_Deviation'] > 20).sum()} ({(merged['Abs_Deviation'] > 20).sum()/len(merged)*100:.1f}%)")
            print(f"   Games >30 pts from closing: {(merged['Abs_Deviation'] > 30).sum()} ({(merged['Abs_Deviation'] > 30).sum()/len(merged)*100:.1f}%)")
        
        return merged
    
    def save_results(self, df, output_dir='backend/data/analysis'):
        """Save final matched dataset"""
        if df is None or df.empty:
            print("WARNING: No data to save")
            return None
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/closing_vs_actual_{self.season_year}_{timestamp}.csv"
        
        df.to_csv(filename, index=False)
        print(f"\n Saved: {filename}")
        
        return filename


def main():
    """Main execution"""
    print("="*70)
    print("NCAA BASKETBALL - HISTORICAL CLOSING LINES SCRAPER")
    print("="*70)
    print("\nWARNING: IMPORTANT:")
    print("   - This uses your Odds API Pro plan")
    print("   - Pro plan has request limits (check dashboard)")
    print("   - Sampling every 3 days to conserve API calls")
    print("   - Estimated: ~50 API requests for full season")
    print("")

    # Get API key from config
    try:
        import sys
        sys.path.insert(0, 'backend')
        from config import ODDS_API_KEY
        print(" API key loaded from config")
    except:
        print("ERROR: Could not load API key from config")
        print("   Update backend/config.py with your Pro API key")
        return
    
    # Get season year
    year_input = input("Enter season end year (default: 2024): ").strip()
    year = int(year_input) if year_input else 2024
    
    # Initialize scraper
    scraper = HistoricalClosingLinesScraper(
        api_key=ODDS_API_KEY,
        season_year=year
    )
    
    # Scrape closing lines
    closing_lines_df = scraper.scrape_season(save_frequency=10)
    
    if closing_lines_df is not None and len(closing_lines_df) > 0:
        # Save raw closing lines
        closing_file = scraper.save_results(
            closing_lines_df,
            output_dir='backend/data/historical'
        )
        
        # Match with actual results
        matched_df = scraper.match_with_actual_results(closing_lines_df)
        
        if matched_df is not None and len(matched_df) > 0:
            # Save matched dataset for analysis
            analysis_file = scraper.save_results(matched_df)
            
            print("\n" + "="*70)
            print(" SUCCESS!")
            print("="*70)
            print(f"\nYou now have:")
            print(f"1. Raw closing lines: {closing_file}")
            print(f"2. Matched with actuals: {analysis_file}")
            print(f"\n Ready for regression analysis!")
            print(f"   - {len(matched_df)} games with closing lines + actual results")
            print(f"   - Can analyze deviation patterns")
            print(f"   - Can test 20+ point regression hypothesis")
        else:
            print("\nWARNING: Could not match closing lines with actual results")
            print("   Check that game_results file exists in backend/data/historical/")
    else:
        print("\nERROR: No closing lines retrieved")
        print("\n Troubleshooting:")
        print("   1. Check API key is correct (Pro plan)")
        print("   2. Check API request limits in dashboard")
        print("   3. Try smaller date range")


if __name__ == "__main__":
    main()