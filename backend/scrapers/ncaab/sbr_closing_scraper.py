#!/usr/bin/env python3
"""
NCAA Basketball Closing Lines Scraper - Sports Book Review
Adapted from cresswellkg/Sports_Utilities
Scrapes historical closing lines and totals from SBR
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from datetime import datetime, timedelta
import re

class SBRClosingScraper:
    """Scrapes NCAA basketball closing lines from Sports Book Review"""

    def __init__(self, season_year=2024):
        """
        Initialize scraper

        Args:
            season_year: End year of season (2024 = 2023-24 season)
        """
        self.season_year = season_year
        self.base_url = "https://classic.sportsbookreview.com/betting-odds/ncaa-basketball/?date="
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.all_games = []

    def get_season_dates(self):
        """Generate date range for NCAA season"""
        start_year = self.season_year - 1

        # NCAA season: November to early April
        start_date = datetime(start_year, 11, 1)
        end_date = datetime(self.season_year, 4, 10)

        # Create list of all dates
        dates = []
        current = start_date

        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)

        return dates

    def scrape_date(self, date):
        """
        Scrape closing lines for a specific date

        Args:
            date: datetime object

        Returns:
            List of games with closing lines
        """
        date_str = date.strftime("%Y%m%d")
        url = self.base_url + date_str

        try:
            response = requests.get(url, headers=self.headers, timeout=15)

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find game data containers
            # SBR uses specific div structure for games
            games = []

            # Look for game rows
            game_divs = soup.find_all('div', {'rel': '1096'})  # 1096 is NCAA basketball sport ID

            if not game_divs:
                # Try alternative selectors
                game_divs = soup.find_all('div', class_='eventLine')

            for game_div in game_divs:
                try:
                    game_data = self._parse_game_div(game_div, date)
                    if game_data:
                        games.append(game_data)
                except Exception as e:
                    continue

            return games

        except Exception as e:
            print(f"   ERROR: Error scraping {date_str}: {str(e)}")
            return []

    def _parse_game_div(self, game_div, date):
        """
        Parse game data from HTML div

        Args:
            game_div: BeautifulSoup div element
            date: datetime object

        Returns:
            Dictionary with game data
        """
        try:
            # Extract team names
            teams = game_div.find_all('span', class_='team-name')
            if len(teams) < 2:
                return None

            away_team = teams[0].text.strip()
            home_team = teams[1].text.strip()

            # Extract total (over/under)
            total_elem = game_div.find('span', class_='total')
            if not total_elem:
                total_elem = game_div.find('div', class_='total')

            if total_elem:
                total_text = total_elem.text.strip()
                # Extract numeric value
                total_match = re.search(r'(\d+\.?\d*)', total_text)
                if total_match:
                    closing_total = float(total_match.group(1))
                else:
                    return None
            else:
                return None

            return {
                'Date': date.strftime('%Y-%m-%d'),
                'Home_Team': home_team,
                'Away_Team': away_team,
                'Closing_Total': closing_total
            }

        except Exception as e:
            return None

    def scrape_season(self, max_requests_per_day=100, delay=2):
        """
        Scrape entire season

        Args:
            max_requests_per_day: Limit requests to avoid rate limiting
            delay: Seconds to wait between requests
        """
        print("="*70)
        print("NCAA BASKETBALL SBR CLOSING LINES SCRAPER")
        print("="*70)
        print(f"   Season: {self.season_year-1}-{self.season_year}")
        print(f"   Source: Sports Book Review")
        print("")

        dates = self.get_season_dates()
        print(f"   Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
        print(f"   Total dates: {len(dates)}")
        print(f"   Delay: {delay}s between requests")
        print("")

        # Sample dates if too many (every 3 days)
        if len(dates) > max_requests_per_day:
            print(f"   Sampling every 3 days to limit requests...")
            dates = dates[::3]
            print(f"   Adjusted dates: {len(dates)}")
            print("")

        total_games = 0

        for i, date in enumerate(dates, 1):
            print(f"   Progress: {i}/{len(dates)} - {date.strftime('%Y-%m-%d')}", end="")

            games = self.scrape_date(date)

            if games:
                self.all_games.extend(games)
                total_games += len(games)
                print(f" - Found {len(games)} games (Total: {total_games})")
            else:
                print(f" - No games")

            # Rate limiting
            if i < len(dates):
                time.sleep(delay)

        print(f"\n Scraping complete!")
        print(f"   Total games: {len(self.all_games)}")

        if len(self.all_games) > 0:
            return pd.DataFrame(self.all_games)
        else:
            return pd.DataFrame()

    def match_with_actuals(self, closing_df):
        """Match closing lines with actual results"""
        import glob

        print("\n MATCHING WITH ACTUAL RESULTS")
        print("-"*70)

        # Find game results
        results_pattern = "backend/data/historical/game_results_*_season_*.csv"
        results_files = glob.glob(results_pattern)

        if not results_files:
            print("ERROR: No game results found")
            return pd.DataFrame()

        results_file = max(results_files)
        print(f"   Loading: {os.path.basename(results_file)}")

        results_df = pd.read_csv(results_file)
        print(f"   Results: {len(results_df)} games")
        print(f"   Closing lines: {len(closing_df)} games")

        # Normalize team names
        closing_df['Home_Team_norm'] = closing_df['Home_Team'].str.strip().str.lower()
        closing_df['Away_Team_norm'] = closing_df['Away_Team'].str.strip().str.lower()
        results_df['Home_Team_norm'] = results_df['Home_Team'].str.strip().str.lower()
        results_df['Away_Team_norm'] = results_df['Away_Team'].str.strip().str.lower()

        # Merge
        merged = pd.merge(
            closing_df,
            results_df[['Date', 'Home_Team_norm', 'Away_Team_norm', 'Actual_Total']],
            on=['Date', 'Home_Team_norm', 'Away_Team_norm'],
            how='inner'
        )

        if len(merged) > 0:
            merged['Deviation'] = merged['Actual_Total'] - merged['Closing_Total']
            merged['Abs_Deviation'] = abs(merged['Deviation'])
            merged = merged.drop(columns=['Home_Team_norm', 'Away_Team_norm'])

            print(f"\n Matched: {len(merged)} games ({len(merged)/len(results_df)*100:.1f}%)")
            print(f"\n DEVIATION STATISTICS:")
            print(f"   Mean: {merged['Deviation'].mean():.2f} pts")
            print(f"   MAE: {merged['Abs_Deviation'].mean():.2f} pts")
            print(f"   Std: {merged['Deviation'].std():.2f} pts")
            print(f"   >20 pts: {(merged['Abs_Deviation'] > 20).sum()} ({(merged['Abs_Deviation'] > 20).sum()/len(merged)*100:.1f}%)")
            print(f"   >30 pts: {(merged['Abs_Deviation'] > 30).sum()} ({(merged['Abs_Deviation'] > 30).sum()/len(merged)*100:.1f}%)")

        return merged

    def save_results(self, df, output_dir='backend/data/analysis'):
        """Save results"""
        if df is None or df.empty:
            print("WARNING: No data to save")
            return None

        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/sbr_closing_vs_actual_{self.season_year}_{timestamp}.csv"

        df.to_csv(filename, index=False)
        print(f"\n Saved: {filename}")

        return filename


def main():
    """Main execution"""
    print("="*70)
    print("NCAA BASKETBALL - SBR CLOSING LINES SCRAPER")
    print("="*70)
    print("\nNOTE: This scraper uses Sports Book Review's public website")
    print("      Please be respectful with request rates")
    print("")

    # Initialize scraper for 2024 season
    scraper = SBRClosingScraper(season_year=2024)

    # Test with a single recent date first
    print("Testing with March 2024 games...")
    test_date = datetime(2024, 3, 15)
    test_games = scraper.scrape_date(test_date)

    if test_games:
        print(f"\n SUCCESS: Found {len(test_games)} games on {test_date.strftime('%Y-%m-%d')}")
        print("Sample game:")
        print(test_games[0])
        print("\nReady to scrape full season!")

        # Ask to continue
        proceed = input("\nScrape full season? (y/N): ").strip().lower()
        if proceed == 'y':
            closing_df = scraper.scrape_season(max_requests_per_day=100, delay=2)

            if not closing_df.empty:
                # Save raw closing lines
                scraper.save_results(closing_df, output_dir='backend/data/historical')

                # Match with actuals
                matched_df = scraper.match_with_actuals(closing_df)

                if not matched_df.empty:
                    scraper.save_results(matched_df)
                    print("\n SUCCESS! Ready for analysis!")
    else:
        print("\nERROR: Could not scrape test date")
        print("SBR may have changed their website structure")
        print("Alternative: Wait for Odds API Pro upgrade")


if __name__ == "__main__":
    main()
