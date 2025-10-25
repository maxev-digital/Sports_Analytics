#!/usr/bin/env python3
"""
NCAA Basketball Historical Game Results Scraper - ESPN Version
Gets actual game scores from ESPN for backtesting
Works by scraping ESPN's scoreboard for each day of the season
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime, timedelta
import os


class ESPNGameResultsScraper:
    def __init__(self, delay_range=(2, 4)):
        self.delay_range = delay_range
        self.base_url = "https://www.espn.com/mens-college-basketball/scoreboard/_/date"
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
    
    def get_season_dates(self, year=2024):
        """
        Generate date range for NCAA Basketball season
        
        Args:
            year: End year of season (2024 = 2023-24 season)
        
        Returns:
            List of dates to scrape
        """
        # NCAA season runs roughly November to early April
        start_year = year - 1
        
        # Season start: November 6
        start_date = datetime(start_year, 11, 6)
        
        # Season end: Early April (regular season + conference tournaments)
        end_date = datetime(year, 4, 10)
        
        dates = []
        current = start_date
        
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)
        
        return dates
    
    def scrape_day(self, date):
        """
        Scrape games for a single day
        
        Args:
            date: datetime object
        
        Returns:
            List of game dictionaries
        """
        date_str = date.strftime("%Y%m%d")
        url = f"{self.base_url}/{date_str}"
        
        try:
            headers = self.rotate_headers()
            response = self.session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse with pandas (ESPN has tables)
            try:
                tables = pd.read_html(response.content)
                
                if not tables:
                    return []
                
                games = []
                
                # ESPN typically returns team pairs with scores
                # Format varies, so we'll parse flexibly
                for table in tables:
                    # Skip if table is too small
                    if len(table) < 2 or len(table.columns) < 2:
                        continue
                    
                    # Try to extract scores
                    # Typical format has team names and scores
                    for idx in range(0, len(table)-1, 2):
                        try:
                            row1 = table.iloc[idx]
                            row2 = table.iloc[idx+1]
                            
                            # Extract team names (usually first column)
                            team1 = str(row1.iloc[0]).strip()
                            team2 = str(row2.iloc[0]).strip()
                            
                            # Extract scores (usually last column or second to last)
                            score1 = None
                            score2 = None
                            
                            # Try last column
                            try:
                                score1 = float(row1.iloc[-1])
                                score2 = float(row2.iloc[-1])
                            except:
                                # Try second to last
                                try:
                                    score1 = float(row1.iloc[-2])
                                    score2 = float(row2.iloc[-2])
                                except:
                                    continue
                            
                            # Validate scores
                            if score1 is None or score2 is None:
                                continue
                            
                            if score1 < 0 or score2 < 0:
                                continue
                            
                            # Determine home/away (away team usually listed first)
                            games.append({
                                'Date': date.strftime('%Y-%m-%d'),
                                'Away_Team': team1,
                                'Home_Team': team2,
                                'Away_Score': int(score1),
                                'Home_Score': int(score2),
                                'Actual_Total': int(score1 + score2)
                            })
                            
                        except Exception as e:
                            continue
                
                return games
                
            except Exception as e:
                # If pandas parsing fails, try BeautifulSoup
                return self.scrape_day_beautifulsoup(response.content, date)
                
        except Exception as e:
            return []
    
    def scrape_day_beautifulsoup(self, html_content, date):
        """Fallback scraping method using BeautifulSoup"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # ESPN uses specific classes for scoreboards
            games = []
            
            # Find game containers
            game_containers = soup.find_all('section', class_='Card')
            
            for container in game_containers:
                try:
                    # Find team names
                    teams = container.find_all('div', class_='ScoreCell__TeamName')
                    if len(teams) != 2:
                        continue
                    
                    team1 = teams[0].get_text(strip=True)
                    team2 = teams[1].get_text(strip=True)
                    
                    # Find scores
                    scores = container.find_all('div', class_='ScoreCell__Score')
                    if len(scores) != 2:
                        continue
                    
                    score1 = int(scores[0].get_text(strip=True))
                    score2 = int(scores[1].get_text(strip=True))
                    
                    games.append({
                        'Date': date.strftime('%Y-%m-%d'),
                        'Away_Team': team1,
                        'Home_Team': team2,
                        'Away_Score': score1,
                        'Home_Score': score2,
                        'Actual_Total': score1 + score2
                    })
                    
                except Exception as e:
                    continue
            
            return games
            
        except Exception as e:
            return []
    
    def scrape_season(self, year=2024):
        """
        Scrape entire season
        
        Args:
            year: End year (2024 = 2023-24 season)
        """
        print(f"🏀 Scraping {year-1}-{year} season from ESPN...")
        print(f"   Source: ESPN.com scoreboard")
        print(f"   ⚠️  This will take 10-15 minutes (scraping ~150 days)")
        print("")
        
        dates = self.get_season_dates(year)
        
        print(f"   Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
        print(f"   Total days: {len(dates)}")
        print("")
        
        all_games = []
        days_with_games = 0
        
        for i, date in enumerate(dates, 1):
            # Progress indicator every 10 days
            if i % 10 == 0:
                print(f"   Progress: {i}/{len(dates)} days ({days_with_games} days with games, {len(all_games)} games found)")
            
            games = self.scrape_day(date)
            
            if games:
                all_games.extend(games)
                days_with_games += 1
            
            # Delay between requests
            if i < len(dates):
                self.smart_delay()
        
        print(f"\n✅ Scraping complete!")
        print(f"   Days scraped: {len(dates)}")
        print(f"   Days with games: {days_with_games}")
        print(f"   Total games found: {len(all_games)}")
        
        if len(all_games) > 0:
            df = pd.DataFrame(all_games)
            
            # Remove duplicates (same teams, same date)
            df = df.drop_duplicates(subset=['Date', 'Away_Team', 'Home_Team'])
            
            print(f"\n✅ Final dataset: {len(df)} unique games")
            print(f"📈 Total points range: {df['Actual_Total'].min()} - {df['Actual_Total'].max()}")
            print(f"📈 Average total: {df['Actual_Total'].mean():.1f}")
            
            return df
        else:
            print("\n❌ No games found")
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
    """Test ESPN game results scraper"""
    print("="*70)
    print("NCAA BASKETBALL GAME RESULTS SCRAPER - ESPN VERSION")
    print("="*70)
    print("\n⚠️  This scraper gets historical game scores from ESPN.com")
    print("   Will scrape each day of the season (10-15 minutes)")
    print("")
    
    print("Which season do you want?")
    print("  2024 = 2023-24 season (most recent)")
    print("  2023 = 2022-23 season")
    year_input = input("\nEnter year (default: 2024): ").strip()
    year = int(year_input) if year_input else 2024
    
    confirm = input(f"\nThis will scrape ~150 days of data. Continue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Aborted.")
        return
    
    scraper = ESPNGameResultsScraper()
    df = scraper.scrape_season(year=year)
    
    if df is not None and len(df) > 0:
        scraper.save_results(df, year=year)
        
        print("\n" + "="*70)
        print("SAMPLE GAMES:")
        print("="*70)
        print(df.head(20).to_string(index=False))
        
        print("\n💡 Next steps:")
        print("   1. Use this CSV with run_ncaab_backtest.py")
        print("   2. Model will compare predictions to actual totals")
    else:
        print("\n❌ No data collected")
        print("\n💡 Alternative:")
        print("   ESPN's page structure may have changed")
        print("   Try using a smaller sample of games manually")


if __name__ == "__main__":
    main()
