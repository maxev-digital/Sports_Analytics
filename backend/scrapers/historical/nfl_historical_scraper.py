"""
NFL Historical Data Scraper
Collects game-by-game data with team stats for XGBoost training

Data Source: Pro-Football-Reference.com
Seasons: 2022, 2023, 2024
Output: ~800 games with features
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

class NFLHistoricalScraper:
    """Scrape historical NFL games with team stats"""

    BASE_URL = "https://www.pro-football-reference.com"

    def __init__(self):
        self.output_dir = "backend/data/historical/nfl"
        os.makedirs(self.output_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_season_games(self, year=2023):
        """Get all games from a season"""
        logger.info(f"Fetching NFL {year} season games...")

        url = f"{self.BASE_URL}/years/{year}/games.htm"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find games table
            table = soup.find('table', {'id': 'games'})
            if not table:
                logger.error(f"Could not find games table for {year}")
                return None

            # Parse table
            games = []
            rows = table.find('tbody').find_all('tr')

            for row in rows:
                # Skip header rows
                if row.get('class') and 'thead' in row.get('class'):
                    continue

                cells = row.find_all(['th', 'td'])
                if len(cells) < 8:
                    continue

                try:
                    game = {
                        'week': cells[0].text.strip(),
                        'day': cells[1].text.strip(),
                        'date': cells[2].text.strip(),
                        'time': cells[3].text.strip() if len(cells) > 3 else '',
                        'winner': cells[4].text.strip() if len(cells) > 4 else '',
                        'at': cells[5].text.strip() if len(cells) > 5 else '',
                        'loser': cells[6].text.strip() if len(cells) > 6 else '',
                        'pts_winner': cells[7].text.strip() if len(cells) > 7 else '',
                        'pts_loser': cells[8].text.strip() if len(cells) > 8 else '',
                        'yds_winner': cells[9].text.strip() if len(cells) > 9 else '',
                        'yds_loser': cells[11].text.strip() if len(cells) > 11 else '',
                        'to_winner': cells[10].text.strip() if len(cells) > 10 else '',
                        'to_loser': cells[12].text.strip() if len(cells) > 12 else '',
                    }

                    # Parse scores
                    game['pts_winner'] = int(game['pts_winner']) if game['pts_winner'].isdigit() else 0
                    game['pts_loser'] = int(game['pts_loser']) if game['pts_loser'].isdigit() else 0
                    game['actual_total'] = game['pts_winner'] + game['pts_loser']

                    # Determine home/away
                    if game['at'] == '@':
                        game['away_team'] = game['winner']
                        game['home_team'] = game['loser']
                        game['away_score'] = game['pts_winner']
                        game['home_score'] = game['pts_loser']
                    else:
                        game['home_team'] = game['winner']
                        game['away_team'] = game['loser']
                        game['home_score'] = game['pts_winner']
                        game['away_score'] = game['pts_loser']

                    game['year'] = year
                    games.append(game)

                except Exception as e:
                    logger.warning(f"Error parsing row: {e}")
                    continue

            logger.info(f"  Found {len(games)} games")
            return pd.DataFrame(games)

        except Exception as e:
            logger.error(f"Error fetching {year} games: {e}")
            return None

    def get_team_stats_by_week(self, year=2023):
        """Get team stats for each week of the season"""
        logger.info(f"Fetching team stats for {year}...")

        url = f"{self.BASE_URL}/years/{year}/"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Team stats table
            table = soup.find('table', {'id': 'team_stats'})
            if not table:
                logger.warning(f"Could not find team stats for {year}")
                return {}

            team_stats = {}
            rows = table.find('tbody').find_all('tr')

            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) < 10:
                    continue

                try:
                    team = cells[0].text.strip()
                    stats = {
                        'games': int(cells[1].text) if cells[1].text.isdigit() else 0,
                        'ppg': float(cells[2].text) if cells[2].text.replace('.', '').isdigit() else 20.0,
                        'opp_ppg': float(cells[3].text) if cells[3].text.replace('.', '').isdigit() else 20.0,
                        'point_diff': float(cells[4].text) if cells[4].text.replace('-', '').replace('.', '').isdigit() else 0.0,
                        'mo': float(cells[5].text) if cells[5].text.replace('.', '').isdigit() else 0.0,
                        'yards_pg': float(cells[6].text) if cells[6].text.replace('.', '').isdigit() else 330.0,
                        'opp_yards_pg': float(cells[7].text) if cells[7].text.replace('.', '').isdigit() else 330.0,
                    }
                    team_stats[team] = stats

                except Exception as e:
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

        # Get team stats (or use defaults)
        home_stats = team_stats.get(home_team, {
            'ppg': 20.0, 'opp_ppg': 20.0, 'point_diff': 0.0,
            'yards_pg': 330.0, 'opp_yards_pg': 330.0
        })

        away_stats = team_stats.get(away_team, {
            'ppg': 20.0, 'opp_ppg': 20.0, 'point_diff': 0.0,
            'yards_pg': 330.0, 'opp_yards_pg': 330.0
        })

        features = {
            # Game metadata
            'year': game['year'],
            'week': game['week'],
            'date': game['date'],
            'home_team': home_team,
            'away_team': away_team,
            'actual_total': game['actual_total'],
            'home_score': game['home_score'],
            'away_score': game['away_score'],

            # Home team stats
            'home_ppg': home_stats.get('ppg', 20.0),
            'home_opp_ppg': home_stats.get('opp_ppg', 20.0),
            'home_point_diff': home_stats.get('point_diff', 0.0),
            'home_yards_pg': home_stats.get('yards_pg', 330.0),
            'home_opp_yards_pg': home_stats.get('opp_yards_pg', 330.0),

            # Away team stats
            'away_ppg': away_stats.get('ppg', 20.0),
            'away_opp_ppg': away_stats.get('opp_ppg', 20.0),
            'away_point_diff': away_stats.get('point_diff', 0.0),
            'away_yards_pg': away_stats.get('yards_pg', 330.0),
            'away_opp_yards_pg': away_stats.get('opp_yards_pg', 330.0),
        }

        # Differentials
        features['ppg_diff'] = home_stats.get('ppg', 20.0) - away_stats.get('ppg', 20.0)
        features['point_diff_diff'] = home_stats.get('point_diff', 0.0) - away_stats.get('point_diff', 0.0)
        features['yards_pg_diff'] = home_stats.get('yards_pg', 330.0) - away_stats.get('yards_pg', 330.0)

        # Expected totals
        features['expected_total_simple'] = home_stats.get('ppg', 20.0) + away_stats.get('ppg', 20.0)
        features['expected_total_vs_defense'] = home_stats.get('ppg', 20.0) + away_stats.get('opp_ppg', 20.0)

        return features

    def scrape_season(self, year=2023):
        """Scrape complete season"""
        logger.info(f"="*60)
        logger.info(f"Scraping NFL {year} season...")
        logger.info(f"="*60)

        # Get games
        games_df = self.get_season_games(year)
        if games_df is None:
            return None

        time.sleep(2)  # Be polite

        # Get team stats
        team_stats = self.get_team_stats_by_week(year)

        time.sleep(2)

        # Engineer features for each game
        logger.info(f"Engineering features...")
        games_with_features = []

        for idx, game in games_df.iterrows():
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
            time.sleep(5)  # Be extra polite to Pro-Football-Reference

        if len(all_data) == 0:
            logger.error("No data collected!")
            return None

        # Combine
        combined = pd.concat(all_data, ignore_index=True)

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{self.output_dir}/nfl_historical_{timestamp}.csv"
        combined.to_csv(output_file, index=False)

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ NFL SCRAPING COMPLETE!")
        logger.info(f"{'='*60}")
        logger.info(f"Total games: {len(combined)}")
        logger.info(f"Features: {len(combined.columns)}")
        logger.info(f"Saved to: {output_file}")

        # Also save as latest
        latest_file = f"{self.output_dir}/nfl_historical_latest.csv"
        combined.to_csv(latest_file, index=False)
        logger.info(f"Latest: {latest_file}")

        return combined


if __name__ == "__main__":
    scraper = NFLHistoricalScraper()

    # Scrape last 3 seasons
    df = scraper.scrape_multiple_seasons([2022, 2023, 2024])

    if df is not None:
        print("\n" + "="*60)
        print("NFL DATA SUMMARY")
        print("="*60)
        print(f"Games: {len(df)}")
        print(f"Average total: {df['actual_total'].mean():.1f} points")
        print(f"Total range: {df['actual_total'].min():.0f} - {df['actual_total'].max():.0f}")
        print("="*60)
