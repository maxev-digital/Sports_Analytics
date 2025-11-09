"""
MLB Historical Data Scraper
Collects game-by-game data with team stats for XGBoost training

Data Source: Baseball-Reference.com
Seasons: 2022, 2023, 2024
Output: ~7,500 games with features
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from datetime import datetime
import time
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLBHistoricalScraper:
    """Scrape historical MLB games with team stats"""

    BASE_URL = "https://www.baseball-reference.com"

    def __init__(self):
        self.output_dir = "backend/data/historical/mlb"
        os.makedirs(self.output_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_season_schedule(self, year=2023):
        """Get all games from a season"""
        logger.info(f"Fetching MLB {year} season games...")

        url = f"{self.BASE_URL}/leagues/majors/{year}-schedule.shtml"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            games = []

            # Find all game rows
            game_divs = soup.find_all('p', {'class': 'game'})

            for game_div in game_divs:
                try:
                    # Extract teams and scores
                    teams_link = game_div.find_all('a')
                    if len(teams_link) < 2:
                        continue

                    away_team = teams_link[0].text.strip()
                    home_team = teams_link[1].text.strip()

                    # Extract scores from the text
                    game_text = game_div.text
                    # Format: "Away Team (score) @ Home Team (score)"

                    # Simple parsing - look for numbers in parentheses
                    import re
                    scores = re.findall(r'\((\d+)\)', game_text)

                    if len(scores) >= 2:
                        away_score = int(scores[0])
                        home_score = int(scores[1])

                        game = {
                            'away_team': away_team,
                            'home_team': home_team,
                            'away_score': away_score,
                            'home_score': home_score,
                            'actual_total': away_score + home_score,
                            'year': year
                        }

                        games.append(game)

                except Exception as e:
                    continue

            logger.info(f"  Found {len(games)} games")
            return pd.DataFrame(games)

        except Exception as e:
            logger.error(f"Error fetching {year} schedule: {e}")
            return None

    def get_team_stats(self, year=2023):
        """Get team stats for the season"""
        logger.info(f"Fetching MLB {year} team stats...")

        url = f"{self.BASE_URL}/leagues/majors/{year}.shtml"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            team_stats = {}

            # Team batting stats
            batting_table = soup.find('table', {'id': 'teams_standard_batting'})
            if batting_table:
                rows = batting_table.find('tbody').find_all('tr')
                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) < 10:
                        continue

                    try:
                        team = cells[0].text.strip()
                        stats = {
                            'runs_pg': float(cells[5].text) if cells[5].text.replace('.', '').isdigit() else 4.5,
                            'hits_pg': float(cells[6].text) if cells[6].text.replace('.', '').isdigit() else 8.5,
                            'batting_avg': float(cells[7].text) if cells[7].text.replace('.', '').isdigit() else 0.250,
                            'hr_pg': float(cells[8].text) if cells[8].text.replace('.', '').isdigit() else 1.0,
                        }
                        team_stats[team] = stats
                    except:
                        continue

            # Team pitching stats
            pitching_table = soup.find('table', {'id': 'teams_standard_pitching'})
            if pitching_table:
                rows = pitching_table.find('tbody').find_all('tr')
                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) < 8:
                        continue

                    try:
                        team = cells[0].text.strip()
                        if team in team_stats:
                            team_stats[team]['era'] = float(cells[4].text) if cells[4].text.replace('.', '').isdigit() else 4.00
                            team_stats[team]['runs_allowed_pg'] = float(cells[5].text) if cells[5].text.replace('.', '').isdigit() else 4.5
                    except:
                        continue

            logger.info(f"  Found stats for {len(team_stats)} teams")
            return team_stats

        except Exception as e:
            logger.error(f"Error fetching team stats: {e}")
            return {}

    def engineer_features(self, game, team_stats):
        """Engineer features from game + team stats"""

        home_team = game['home_team']
        away_team = game['away_team']

        # Get team stats (or defaults)
        home_stats = team_stats.get(home_team, {
            'runs_pg': 4.5, 'runs_allowed_pg': 4.5, 'era': 4.00,
            'batting_avg': 0.250, 'hits_pg': 8.5, 'hr_pg': 1.0
        })

        away_stats = team_stats.get(away_team, {
            'runs_pg': 4.5, 'runs_allowed_pg': 4.5, 'era': 4.00,
            'batting_avg': 0.250, 'hits_pg': 8.5, 'hr_pg': 1.0
        })

        features = {
            # Game metadata
            'year': game['year'],
            'home_team': home_team,
            'away_team': away_team,
            'actual_total': game['actual_total'],
            'home_score': game['home_score'],
            'away_score': game['away_score'],

            # Home team stats
            'home_runs_pg': home_stats.get('runs_pg', 4.5),
            'home_runs_allowed_pg': home_stats.get('runs_allowed_pg', 4.5),
            'home_era': home_stats.get('era', 4.00),
            'home_batting_avg': home_stats.get('batting_avg', 0.250),
            'home_hits_pg': home_stats.get('hits_pg', 8.5),
            'home_hr_pg': home_stats.get('hr_pg', 1.0),

            # Away team stats
            'away_runs_pg': away_stats.get('runs_pg', 4.5),
            'away_runs_allowed_pg': away_stats.get('runs_allowed_pg', 4.5),
            'away_era': away_stats.get('era', 4.00),
            'away_batting_avg': away_stats.get('batting_avg', 0.250),
            'away_hits_pg': away_stats.get('hits_pg', 8.5),
            'away_hr_pg': away_stats.get('hr_pg', 1.0),
        }

        # Differentials
        features['runs_pg_diff'] = home_stats.get('runs_pg', 4.5) - away_stats.get('runs_pg', 4.5)
        features['era_diff'] = away_stats.get('era', 4.00) - home_stats.get('era', 4.00)  # Lower is better
        features['batting_avg_diff'] = home_stats.get('batting_avg', 0.250) - away_stats.get('batting_avg', 0.250)

        # Expected totals
        features['expected_total_simple'] = home_stats.get('runs_pg', 4.5) + away_stats.get('runs_pg', 4.5)
        features['expected_total_vs_pitching'] = home_stats.get('runs_pg', 4.5) + away_stats.get('runs_allowed_pg', 4.5)

        return features

    def scrape_season(self, year=2023):
        """Scrape complete season"""
        logger.info(f"="*60)
        logger.info(f"Scraping MLB {year} season...")
        logger.info(f"="*60)

        # Get games
        games_df = self.get_season_schedule(year)
        if games_df is None:
            return None

        time.sleep(3)  # Be polite

        # Get team stats
        team_stats = self.get_team_stats(year)

        time.sleep(3)

        # Engineer features
        logger.info(f"Engineering features...")
        games_with_features = []

        for idx, game in games_df.iterrows():
            if idx % 500 == 0:
                logger.info(f"  Progress: {idx}/{len(games_df)}")

            features = self.engineer_features(game, team_stats)
            games_with_features.append(features)

        df = pd.DataFrame(games_with_features)
        logger.info(f"✅ Processed {len(df)} games")

        return df

    def scrape_multiple_seasons(self, years=[2022, 2023, 2024]):
        """Scrape multiple seasons"""
        all_data = []

        for year in years:
            logger.info(f"\n{'='*60}")
            logger.info(f"Year: {year}")
            logger.info(f"{'='*60}")

            df = self.scrape_season(year)
            if df is not None:
                all_data.append(df)

            # Delay between seasons
            time.sleep(5)

        if len(all_data) == 0:
            logger.error("No data collected!")
            return None

        # Combine
        combined = pd.concat(all_data, ignore_index=True)

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{self.output_dir}/mlb_historical_{timestamp}.csv"
        combined.to_csv(output_file, index=False)

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ MLB SCRAPING COMPLETE!")
        logger.info(f"{'='*60}")
        logger.info(f"Total games: {len(combined)}")
        logger.info(f"Features: {len(combined.columns)}")
        logger.info(f"Saved to: {output_file}")

        # Also save as latest
        latest_file = f"{self.output_dir}/mlb_historical_latest.csv"
        combined.to_csv(latest_file, index=False)
        logger.info(f"Latest: {latest_file}")

        return combined


if __name__ == "__main__":
    scraper = MLBHistoricalScraper()

    # Scrape last 3 seasons
    df = scraper.scrape_multiple_seasons([2022, 2023, 2024])

    if df is not None:
        print("\n" + "="*60)
        print("MLB DATA SUMMARY")
        print("="*60)
        print(f"Games: {len(df)}")
        print(f"Average total: {df['actual_total'].mean():.1f} runs")
        print(f"Total range: {df['actual_total'].min():.0f} - {df['actual_total'].max():.0f}")
        print("="*60)
