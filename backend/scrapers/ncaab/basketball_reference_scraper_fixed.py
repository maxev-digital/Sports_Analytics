#!/usr/bin/env python3
"""
NCAA Basketball Historical Game Results Scraper - Basketball-Reference FIXED
Gets actual game scores from Basketball-Reference for backtesting

This version properly handles Basketball-Reference's actual HTML structure
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime, timedelta
import os
import re


class BasketballReferenceScraper:
    def __init__(self, delay_range=(3, 6)):
        self.delay_range = delay_range
        self.base_url = "https://www.sports-reference.com/cbb"
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
    
    def rotate_headers(self):
        """Rotate user agent"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def smart_delay(self):
        """Intelligent delay"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def get_season_dates(self, year=2024):
        """
        Generate date range for NCAA Basketball season
        
        Args:
            year: End year of season (2024 = 2023-24 season)
        
        Returns:
            List of dates to scrape
        """
        start_year = year - 1
        
        # NCAA season runs roughly November to early April
        start_date = datetime(start_year, 11, 6)
        end_date = datetime(year, 4, 10)
        
        dates = []
        current = start_date
        
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)
        
        return dates
    
    def scrape_day_boxscores(self, date):
        """
        Scrape games for a single day using boxscores index
        
        Args:
            date: datetime object
        
        Returns:
            List of game dictionaries
        """
        # Basketball-Reference boxscores URL format
        # https://www.sports-reference.com/cbb/boxscores/index.cgi?month=11&day=15&year=2023
        url = f"{self.base_url}/boxscores/index.cgi?month={date.month}&day={date.day}&year={date.year}"
        
        try:
            headers = self.rotate_headers()
            response = self.session.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            games = []
            
            # Basketball-Reference uses tables with class "teams"
            # Each game is in a separate table row
            game_tables = soup.find_all('table', class_='teams')
            
            if not game_tables:
                # Try alternative parsing - look for game summaries
                game_summaries = soup.find_all('div', class_='game_summary')
                
                for summary in game_summaries:
                    try:
                        # Extract teams and scores from game summary
                        teams = summary.find_all('tr')
                        
                        if len(teams) >= 2:
                            # First row is away team
                            away_row = teams[0]
                            away_team_elem = away_row.find('a')
                            away_score_elem = away_row.find('td', class_='right')
                            
                            # Second row is home team
                            home_row = teams[1]
                            home_team_elem = home_row.find('a')
                            home_score_elem = home_row.find('td', class_='right')
                            
                            if away_team_elem and home_team_elem and away_score_elem and home_score_elem:
                                away_team = away_team_elem.get_text(strip=True)
                                home_team = home_team_elem.get_text(strip=True)
                                
                                # Extract scores
                                away_score_text = away_score_elem.get_text(strip=True)
                                home_score_text = home_score_elem.get_text(strip=True)
                                
                                # Parse scores (might be like "75" or "75 (OT)")
                                away_score = int(re.search(r'\d+', away_score_text).group())
                                home_score = int(re.search(r'\d+', home_score_text).group())
                                
                                games.append({
                                    'Date': date.strftime('%Y-%m-%d'),
                                    'Away_Team': away_team,
                                    'Home_Team': home_team,
                                    'Away_Score': away_score,
                                    'Home_Score': home_score,
                                    'Actual_Total': away_score + home_score
                                })
                    except Exception as e:
                        continue
            
            else:
                # Parse using tables structure
                for table in game_tables:
                    try:
                        rows = table.find_all('tr')
                        
                        if len(rows) >= 2:
                            # Away team (first row)
                            away_row = rows[0]
                            away_cells = away_row.find_all('td')
                            
                            if len(away_cells) >= 2:
                                away_team_elem = away_cells[0].find('a')
                                away_team = away_team_elem.get_text(strip=True) if away_team_elem else away_cells[0].get_text(strip=True)
                                away_score = int(away_cells[1].get_text(strip=True))
                            else:
                                continue
                            
                            # Home team (second row)
                            home_row = rows[1]
                            home_cells = home_row.find_all('td')
                            
                            if len(home_cells) >= 2:
                                home_team_elem = home_cells[0].find('a')
                                home_team = home_team_elem.get_text(strip=True) if home_team_elem else home_cells[0].get_text(strip=True)
                                home_score = int(home_cells[1].get_text(strip=True))
                            else:
                                continue
                            
                            games.append({
                                'Date': date.strftime('%Y-%m-%d'),
                                'Away_Team': away_team,
                                'Home_Team': home_team,
                                'Away_Score': away_score,
                                'Home_Score': home_score,
                                'Actual_Total': away_score + home_score
                            })
                    except Exception as e:
                        continue
            
            return games
            
        except requests.exceptions.RequestException as e:
            return []
        except Exception as e:
            return []
    
    def scrape_season(self, year=2024, sample_days=None):
        """
        Scrape entire season or sample days
        
        Args:
            year: End year (2024 = 2023-24 season)
            sample_days: If set, only scrape this many days (for testing)
        """
        print(f"🏀 Scraping {year-1}-{year} season from Basketball-Reference...")
        print(f"   Source: Sports-Reference.com/cbb")
        
        dates = self.get_season_dates(year)
        
        if sample_days:
            # Sample evenly throughout season
            step = len(dates) // sample_days
            dates = dates[::step][:sample_days]
            print(f"   📊 Sampling {len(dates)} days from season")
        else:
            print(f"   ⚠️  This will take 10-15 minutes (scraping {len(dates)} days)")
        
        print(f"   Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
        print("")
        
        all_games = []
        days_with_games = 0
        failed_days = 0
        
        for i, date in enumerate(dates, 1):
            # Progress indicator
            if i % 10 == 0 or i == len(dates):
                print(f"   Progress: {i}/{len(dates)} days ({days_with_games} days with games, {len(all_games)} games found)")
            
            games = self.scrape_day_boxscores(date)
            
            if games:
                all_games.extend(games)
                days_with_games += 1
            
            # Delay between requests (be respectful!)
            if i < len(dates):
                self.smart_delay()
        
        print(f"\n✅ Scraping complete!")
        print(f"   Days scraped: {len(dates)}")
        print(f"   Days with games: {days_with_games}")
        print(f"   Total games found: {len(all_games)}")
        
        if len(all_games) > 0:
            df = pd.DataFrame(all_games)
            
            # Remove duplicates
            df = df.drop_duplicates(subset=['Date', 'Away_Team', 'Home_Team'])
            
            print(f"\n✅ Final dataset: {len(df)} unique games")
            print(f"📈 Total points range: {df['Actual_Total'].min()} - {df['Actual_Total'].max()}")
            print(f"📈 Average total: {df['Actual_Total'].mean():.1f}")
            
            return df
        else:
            print("\n❌ No games found")
            print("\n💡 Possible issues:")
            print("   1. Basketball-Reference may be blocking requests")
            print("   2. Page structure changed")
            print("   3. Try sampling fewer days first")
            return pd.DataFrame()
    
    def save_results(self, df, year, output_dir='backend/data/historical'):
        """Save game results to CSV"""
        if df is None or df.empty:
            print("⚠️  No results to save")
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
    print("NCAA BASKETBALL GAME RESULTS SCRAPER - BASKETBALL-REFERENCE FIXED")
    print("="*70)
    print("\n⚠️  This scraper gets historical game scores from Basketball-Reference")
    print("   More reliable structure parsing than previous version")
    print("")
    
    print("Which season do you want?")
    print("  2024 = 2023-24 season (most recent)")
    print("  2023 = 2022-23 season")
    year_input = input("\nEnter year (default: 2024): ").strip()
    year = int(year_input) if year_input else 2024
    
    print("\nOptions:")
    print("  1. Full season (~157 days, 10-15 minutes)")
    print("  2. Sample 30 days (faster test)")
    option = input("Choose option (1 or 2): ").strip()
    
    sample_days = None
    if option == "2":
        sample_days = 30
        print(f"\n📊 Will sample 30 days evenly from season")
    
    scraper = BasketballReferenceScraper()
    df = scraper.scrape_season(year=year, sample_days=sample_days)
    
    if df is not None and len(df) > 0:
        scraper.save_results(df, year=year)
        
        print("\n" + "="*70)
        print("SAMPLE GAMES:")
        print("="*70)
        print(df.head(20).to_string(index=False))
        
        print("\n💡 Next steps:")
        print("   1. Use this CSV with run_ncaab_backtest.py")
        print("   2. Model will compare predictions to actual totals")
        print(f"\n✅ You now have {len(df)} games for backtesting!")
    else:
        print("\n❌ Scraping failed")
        print("\n💡 What to try:")
        print("   1. Try option 2 (sample 30 days) to test")
        print("   2. Check if Basketball-Reference is accessible in browser")
        print("   3. May need to adjust delay_range if getting rate limited")


if __name__ == "__main__":
    main()
