#!/usr/bin/env python3
"""
Basketball-Reference NCAA Basketball Game Results Scraper
Gets actual game scores from Basketball-Reference (Sports-Reference.com)
More reliable than ESPN for historical data
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime
import os


class BasketballReferenceScraper:
    def __init__(self, delay_range=(2, 4)):
        self.delay_range = delay_range
        self.base_url = "https://www.sports-reference.com/cbb"
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        ]
    
    def rotate_headers(self):
        """Rotate user agent"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def smart_delay(self):
        """Intelligent delay with randomization"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def try_url_patterns(self, year=2024):
        """
        Try multiple URL patterns for Basketball-Reference
        Returns the first working URL
        """
        url_patterns = [
            f"{self.base_url}/seasons/men/{year}-schedule.html",
            f"{self.base_url}/seasons/{year}-schedule.html",
            f"{self.base_url}/seasons/men/{year}/schedule.html",
            f"{self.base_url}/boxscores/index.cgi?month=0&day=0&year={year}",
        ]
        
        print("🔍 Testing URL patterns...")
        
        for url in url_patterns:
            try:
                headers = self.rotate_headers()
                response = self.session.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    print(f"   ✅ Found working URL: {url}")
                    return url, response
                else:
                    print(f"   ❌ {response.status_code}: {url}")
                    
            except Exception as e:
                print(f"   ❌ Failed: {url}")
                continue
        
        return None, None
    
    def scrape_from_schedule_page(self, html_content):
        """
        Parse games from a schedule page
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        games = []
        
        # Method 1: Look for schedule table
        schedule_table = soup.find('table', {'id': 'schedule'})
        
        if schedule_table:
            print("   ✅ Found schedule table")
            
            rows = schedule_table.find_all('tr')
            
            for row in rows:
                try:
                    # Skip header rows
                    if row.find('th'):
                        continue
                    
                    cells = row.find_all('td')
                    
                    if len(cells) < 5:
                        continue
                    
                    # Extract data (typical format)
                    # Columns: Date, Away Team, Away Score, Home Team, Home Score
                    date_cell = cells[0] if len(cells) > 0 else None
                    visitor_cell = cells[1] if len(cells) > 1 else None
                    visitor_pts_cell = cells[2] if len(cells) > 2 else None
                    home_cell = cells[3] if len(cells) > 3 else None
                    home_pts_cell = cells[4] if len(cells) > 4 else None
                    
                    # Extract text
                    date = date_cell.get_text(strip=True) if date_cell else None
                    away_team = visitor_cell.get_text(strip=True) if visitor_cell else None
                    home_team = home_cell.get_text(strip=True) if home_cell else None
                    
                    # Extract scores
                    away_score = visitor_pts_cell.get_text(strip=True) if visitor_pts_cell else None
                    home_score = home_pts_cell.get_text(strip=True) if home_pts_cell else None
                    
                    # Validate
                    if not away_score or not home_score:
                        continue
                    
                    try:
                        away_score = int(away_score)
                        home_score = int(home_score)
                    except ValueError:
                        continue
                    
                    if away_score < 0 or home_score < 0:
                        continue
                    
                    games.append({
                        'Date': date,
                        'Away_Team': away_team,
                        'Home_Team': home_team,
                        'Away_Score': away_score,
                        'Home_Score': home_score,
                        'Actual_Total': away_score + home_score
                    })
                    
                except Exception as e:
                    continue
            
            return games
        
        # Method 2: Use pandas to read HTML tables
        print("   🔄 Trying pandas HTML parsing...")
        
        try:
            tables = pd.read_html(html_content)
            
            if not tables:
                return []
            
            # Look for table with game data
            for table in tables:
                # Check if table has expected columns
                if len(table.columns) >= 5:
                    # Try to process as game data
                    for idx, row in table.iterrows():
                        try:
                            # Flexible column detection
                            # Look for score-like numbers
                            scores = []
                            for val in row:
                                try:
                                    score = int(val)
                                    if 0 < score < 200:  # Valid basketball score
                                        scores.append(score)
                                except:
                                    continue
                            
                            if len(scores) >= 2:
                                away_score = scores[0]
                                home_score = scores[1]
                                
                                # Extract team names (non-numeric values)
                                teams = [str(val) for val in row if not str(val).isdigit() and val != '']
                                
                                if len(teams) >= 2:
                                    games.append({
                                        'Date': '',
                                        'Away_Team': teams[0],
                                        'Home_Team': teams[1],
                                        'Away_Score': away_score,
                                        'Home_Score': home_score,
                                        'Actual_Total': away_score + home_score
                                    })
                        except:
                            continue
            
            return games
            
        except Exception as e:
            print(f"   ❌ Pandas parsing failed: {str(e)}")
            return []
    
    def scrape_season(self, year=2024):
        """
        Scrape entire NCAA Basketball season
        
        Args:
            year: Season year (2024 = 2023-24 season)
        """
        print("="*70)
        print(f"🏀 Basketball-Reference Scraper - {year-1}-{year} Season")
        print("="*70)
        print(f"   Source: Sports-Reference.com/cbb")
        print(f"   ⚠️  This may take a few minutes...")
        print("")
        
        # Try to find working URL
        working_url, response = self.try_url_patterns(year)
        
        if not working_url:
            print("\n❌ Could not find working URL for Basketball-Reference")
            print("   The site structure may have changed")
            print("\n💡 Alternative options:")
            print("   1. Try a different year (2023, 2022)")
            print("   2. Use a paid API service")
            print("   3. Use a pre-compiled dataset from Kaggle")
            return pd.DataFrame()
        
        # Parse games from page
        print("\n📊 Parsing game data...")
        games = self.scrape_from_schedule_page(response.content)
        
        if not games:
            print("❌ No games found on page")
            print("   The page structure may be different than expected")
            return pd.DataFrame()
        
        print(f"✅ Found {len(games)} games")
        
        df = pd.DataFrame(games)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['Away_Team', 'Home_Team', 'Away_Score', 'Home_Score'])
        
        print(f"\n✅ Final dataset: {len(df)} unique games")
        
        if len(df) > 0:
            print(f"📈 Total points range: {df['Actual_Total'].min()} - {df['Actual_Total'].max()}")
            print(f"📈 Average total: {df['Actual_Total'].mean():.1f}")
        
        return df
    
    def save_results(self, df, year, output_dir='backend/data/historical'):
        """Save game results to CSV"""
        if df is None or df.empty:
            print("\n⚠️  No results to save")
            return None
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/game_results_{year}_season_{timestamp}.csv"
        
        df.to_csv(filename, index=False)
        print(f"\n💾 Saved: {filename}")
        
        return filename


def main():
    """Test Basketball-Reference scraper"""
    print("="*70)
    print("NCAA BASKETBALL GAME RESULTS SCRAPER - BASKETBALL-REFERENCE")
    print("="*70)
    print("\n⚠️  This scraper gets historical game scores from Basketball-Reference")
    print("   More reliable than ESPN for complete season data")
    print("")
    
    print("Which season do you want?")
    print("  2024 = 2023-24 season (most recent)")
    print("  2023 = 2022-23 season")
    year_input = input("\nEnter year (default: 2024): ").strip()
    year = int(year_input) if year_input else 2024
    
    scraper = BasketballReferenceScraper()
    df = scraper.scrape_season(year=year)
    
    if df is not None and len(df) > 0:
        scraper.save_results(df, year=year)
        
        print("\n" + "="*70)
        print("SAMPLE GAMES:")
        print("="*70)
        print(df.head(20).to_string(index=False))
        
        print("\n💡 Next steps:")
        print("   1. Run: python check_backtest_ready.py")
        print("   2. Then: python run_ncaab_backtest.py")
    else:
        print("\n❌ Scraping failed")
        print("\n💡 What to try next:")
        print("   1. Try a different year (2023 or 2022)")
        print("   2. Check if Basketball-Reference is accessible")
        print("   3. Consider using a pre-compiled CSV from Kaggle")


if __name__ == "__main__":
    main()
