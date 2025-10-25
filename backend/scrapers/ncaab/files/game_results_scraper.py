#!/usr/bin/env python3
"""
NCAA Basketball Historical Game Results Scraper
Gets actual game scores from sports-reference.com for backtesting
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime
import os


class GameResultsScraper:
    def __init__(self, delay_range=(3, 6)):
        self.delay_range = delay_range
        self.base_url = "https://www.sports-reference.com/cbb"
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        ]
    
    def rotate_headers(self):
        """Rotate user agent"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    
    def smart_delay(self):
        """Intelligent delay"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def scrape_season_results(self, year=2024):
        """
        Scrape game results for a season
        
        Args:
            year: Season year (e.g., 2024 for 2023-24 season)
        
        Returns:
            DataFrame with Home_Team, Away_Team, Home_Score, Away_Score, Total
        """
        print(f"🏀 Scraping game results for {year-1}-{year} season...")
        print(f"   Source: Sports-Reference.com")
        print(f"   ⚠️ This may take several minutes...")
        
        # Sports-Reference URL format for schedule
        url = f"{self.base_url}/seasons/{year}-schedule.html"
        print(f"   URL: {url}\n")
        
        try:
            headers = self.rotate_headers()
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find schedule table
            table = soup.find('table', {'id': 'schedule'})
            
            if not table:
                print("❌ Could not find schedule table")
                return pd.DataFrame()
            
            # Parse table with pandas
            df = pd.read_html(str(table))[0]
            
            # Clean column names
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(-1)
            
            df.columns = df.columns.str.strip()
            
            print(f"   ✅ Found {len(df)} games")
            
            # Extract relevant columns
            # Typical columns: Date, Visitor, PTS (visitor), Home, PTS (home)
            
            # Map columns (may vary by year)
            home_team_col = next((col for col in df.columns if 'home' in col.lower()), None)
            away_team_col = next((col for col in df.columns if 'visitor' in col.lower() or 'away' in col.lower()), None)
            
            # Find score columns
            pts_cols = [col for col in df.columns if 'pts' in str(col).lower()]
            
            if len(pts_cols) >= 2:
                away_score_col = pts_cols[0]
                home_score_col = pts_cols[1]
            else:
                print("❌ Could not find score columns")
                return pd.DataFrame()
            
            if not home_team_col or not away_team_col:
                print("❌ Could not find team columns")
                print(f"   Available columns: {list(df.columns)}")
                return pd.DataFrame()
            
            # Create clean dataframe
            games = []
            
            for _, row in df.iterrows():
                try:
                    home_team = row[home_team_col]
                    away_team = row[away_team_col]
                    home_score = row[home_score_col]
                    away_score = row[away_score_col]
                    
                    # Skip if missing data
                    if pd.isna(home_score) or pd.isna(away_score):
                        continue
                    
                    # Convert to numeric
                    home_score = float(home_score)
                    away_score = float(away_score)
                    total = home_score + away_score
                    
                    games.append({
                        'Home_Team': str(home_team).strip(),
                        'Away_Team': str(away_team).strip(),
                        'Home_Score': int(home_score),
                        'Away_Score': int(away_score),
                        'Actual_Total': int(total)
                    })
                    
                except Exception as e:
                    continue
            
            results_df = pd.DataFrame(games)
            
            print(f"\n✅ Successfully parsed {len(results_df)} complete games")
            
            if len(results_df) > 0:
                print(f"📈 Total points range: {results_df['Actual_Total'].min()} - {results_df['Actual_Total'].max()}")
                print(f"📈 Average total: {results_df['Actual_Total'].mean():.1f}")
            
            return results_df
            
        except Exception as e:
            print(f"❌ Error scraping game results: {str(e)}")
            import traceback
            print(f"   Details: {traceback.format_exc()}")
            return pd.DataFrame()
    
    def save_results(self, df, year, output_dir='backend/data/historical'):
        """Save game results to CSV"""
        if df is None or df.empty:
            print("⚠️ No results to save")
            return None
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/game_results_{year}_season_{timestamp}.csv"
        
        df.to_csv(filename, index=False)
        print(f"\n💾 Saved: {filename}")
        
        return filename


def main():
    """Test game results scraper"""
    print("="*70)
    print("NCAA BASKETBALL GAME RESULTS SCRAPER")
    print("="*70)
    print("\n⚠️ This scraper gets historical game scores from Sports-Reference.com")
    print("   Free to use, but please be respectful with requests\n")
    
    print("Which season do you want?")
    print("  2024 = 2023-24 season (most recent)")
    print("  2023 = 2022-23 season")
    year_input = input("\nEnter year (default: 2024): ").strip()
    year = int(year_input) if year_input else 2024
    
    scraper = GameResultsScraper()
    df = scraper.scrape_season_results(year=year)
    
    if df is not None and len(df) > 0:
        scraper.save_results(df, year=year)
        
        print("\n" + "="*70)
        print("SAMPLE GAMES:")
        print("="*70)
        print(df.head(15).to_string(index=False))
        
        print("\n💡 Next steps:")
        print("   1. Use this CSV with the backtesting script")
        print("   2. Compare model predictions to actual totals")
        print("   3. Calculate accuracy metrics (MAE, RMSE)")


if __name__ == "__main__":
    main()
