#!/usr/bin/env python3
"""
Sports-Reference.com Scraper for Complete NCAA Basketball Results
Scrapes all Men's D1 games for 2023-24 season
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import re

class SportsReferenceScraper:
    """Scrape complete NCAA basketball results from Sports-Reference"""

    def __init__(self):
        self.base_url = "https://www.sports-reference.com/cbb/boxscores/index.cgi"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.games = []

    def scrape_date(self, date):
        """Scrape all games for a specific date"""
        params = {
            'month': date.month,
            'day': date.day,
            'year': date.year
        }

        try:
            response = requests.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all game summaries
            summaries = soup.find_all('div', class_='game_summary')

            for summary in summaries:
                game_data = self.parse_game(summary, date)
                if game_data:
                    self.games.append(game_data)

            return len(summaries)

        except Exception as e:
            print(f"   Error scraping {date}: {e}")
            return 0

    def parse_game(self, summary, date):
        """Parse a single game summary"""
        try:
            # Find winner and loser
            winner_div = summary.find('tr', class_='winner')
            loser_div = summary.find('tr', class_='loser')

            if not winner_div or not loser_div:
                return None

            # Extract team names and scores
            winner_team = winner_div.find('a').text.strip()
            winner_score_td = winner_div.find('td', class_='right')
            winner_score = int(winner_score_td.text.strip()) if winner_score_td else None

            loser_team = loser_div.find('a').text.strip()
            loser_score_td = loser_div.find('td', class_='right')
            loser_score = int(loser_score_td.text.strip()) if loser_score_td else None

            if winner_score is None or loser_score is None:
                return None

            # Determine home/away (usually second team listed is home)
            # In Sports-Reference, loser is typically listed second
            table = summary.find('table')
            rows = table.find_all('tr')

            # Check if first row is winner or loser
            first_team_link = rows[0].find('a')
            first_is_winner = first_team_link and first_team_link.text.strip() == winner_team

            if first_is_winner:
                away_team = winner_team
                away_score = winner_score
                home_team = loser_team
                home_score = loser_score
            else:
                away_team = loser_team
                away_score = loser_score
                home_team = winner_team
                home_score = winner_score

            total_points = away_score + home_score

            return {
                'Date': date.strftime('%Y-%m-%d'),
                'Home_Team': home_team,
                'Away_Team': away_team,
                'Home_Score': home_score,
                'Away_Score': away_score,
                'Actual_Total': total_points
            }

        except Exception as e:
            return None

    def scrape_season(self, start_date, end_date):
        """Scrape entire season date by date"""
        print("="*70)
        print("SPORTS-REFERENCE SCRAPER - NCAA MEN'S BASKETBALL")
        print("="*70)
        print(f"\nScraping from {start_date} to {end_date}")

        current_date = start_date
        total_days = 0
        total_games = 0

        while current_date <= end_date:
            games_found = self.scrape_date(current_date)
            total_games += games_found

            if games_found > 0:
                print(f"   {current_date.strftime('%Y-%m-%d')}: {games_found} games")

            total_days += 1
            current_date += timedelta(days=1)

            # Be respectful to server
            time.sleep(1)

            # Progress update every 30 days
            if total_days % 30 == 0:
                print(f"\n   Progress: {total_days} days scraped, {total_games} games found\n")

        print(f"\n COMPLETE: {total_games} games from {total_days} days")
        return total_games

    def save_results(self):
        """Save results to CSV"""
        if len(self.games) == 0:
            print("\nNo games to save")
            return None

        df = pd.DataFrame(self.games)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"backend/data/historical/sports_reference_2024_season_{timestamp}.csv"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        df.to_csv(output_file, index=False)

        print(f"\n Saved {len(df)} games to: {output_file}")
        print(f"\n Statistics:")
        print(f"   Unique teams: {len(set(df['Home_Team'].tolist() + df['Away_Team'].tolist()))}")
        print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
        print(f"   Avg total points: {df['Actual_Total'].mean():.1f}")

        return output_file


def main():
    """Main execution"""
    scraper = SportsReferenceScraper()

    # 2023-24 NCAA season: Nov 6, 2023 to Apr 8, 2024 (National Championship)
    start_date = datetime(2023, 11, 6)
    end_date = datetime(2024, 4, 8)

    scraper.scrape_season(start_date, end_date)
    output_file = scraper.save_results()

    if output_file:
        print("\n" + "="*70)
        print("SUCCESS - Ready to match with closing lines")
        print("="*70)
        return True
    else:
        print("\nERROR: No data scraped")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
