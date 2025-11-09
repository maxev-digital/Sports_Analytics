"""
NCAAB Historical Data Scraper
Collects game-by-game data with team stats for XGBoost training

Data Source: Sports-Reference.com (College Basketball)
Seasons: 2022-23, 2023-24, 2024-25
Output: ~5,000 games with features

Note: Uses Sports-Reference stats as approximation since KenPom doesn't
provide historical time-series data. Stats won't be as good as KenPom's
adjusted metrics, but will have proper time-series (stats at time of game).
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

class NCAABHistoricalScraper:
    """Scrape historical NCAAB games with team stats"""

    BASE_URL = "https://www.sports-reference.com/cbb"

    def __init__(self):
        self.output_dir = "backend/data/historical/ncaab"
        os.makedirs(self.output_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_season_games(self, season="2024"):
        """Get all games from a season"""
        logger.info(f"Fetching NCAAB {season} season games...")

        # Sports-Reference uses end year for season (2023-24 = 2024)
        url = f"{self.BASE_URL}/seasons/{season}-schedule.html"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find games table
            table = soup.find('table', {'id': 'schedule'})
            if not table:
                logger.error(f"Could not find games table for {season}")
                return None

            games = []
            rows = table.find('tbody').find_all('tr')

            for row in rows:
                # Skip header rows
                if row.get('class') and 'thead' in row.get('class'):
                    continue

                cells = row.find_all(['th', 'td'])
                if len(cells) < 7:
                    continue

                try:
                    # Parse game data
                    date = cells[0].text.strip() if len(cells) > 0 else ''
                    visitor = cells[2].text.strip() if len(cells) > 2 else ''
                    visitor_pts = cells[3].text.strip() if len(cells) > 3 else ''
                    home = cells[4].text.strip() if len(cells) > 4 else ''
                    home_pts = cells[5].text.strip() if len(cells) > 5 else ''

                    # Parse scores
                    if not visitor_pts.isdigit() or not home_pts.isdigit():
                        continue

                    game = {
                        'season': season,
                        'date': date,
                        'home_team': home,
                        'away_team': visitor,
                        'home_score': int(home_pts),
                        'away_score': int(visitor_pts),
                        'actual_total': int(home_pts) + int(visitor_pts)
                    }

                    games.append(game)

                except Exception as e:
                    logger.warning(f"Error parsing row: {e}")
                    continue

            logger.info(f"  Found {len(games)} games")
            return pd.DataFrame(games)

        except Exception as e:
            logger.error(f"Error fetching {season} games: {e}")
            return None

    def get_team_stats(self, season="2024"):
        """Get team stats for the season"""
        logger.info(f"Fetching NCAAB {season} team stats...")

        url = f"{self.BASE_URL}/seasons/{season}-school-stats.html"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            team_stats = {}

            # Team stats table
            table = soup.find('table', {'id': 'basic_school_stats'})
            if table:
                rows = table.find('tbody').find_all('tr')
                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) < 10:
                        continue

                    try:
                        team = cells[0].text.strip()

                        # Extract stats
                        stats = {
                            'games': int(cells[1].text) if cells[1].text.isdigit() else 30,
                            'wins': int(cells[2].text) if cells[2].text.isdigit() else 15,
                            'losses': int(cells[3].text) if cells[3].text.isdigit() else 15,
                            'win_pct': float(cells[4].text) if cells[4].text.replace('.', '').isdigit() else 0.500,
                            'ppg': float(cells[7].text) if cells[7].text.replace('.', '').isdigit() else 70.0,
                            'opp_ppg': float(cells[8].text) if cells[8].text.replace('.', '').isdigit() else 70.0,
                        }

                        # Calculate approximate efficiency (points per 100 possessions)
                        # Rough estimate: assume ~70 possessions per game
                        possessions_estimate = 70.0
                        stats['off_eff'] = (stats['ppg'] / possessions_estimate) * 100
                        stats['def_eff'] = (stats['opp_ppg'] / possessions_estimate) * 100
                        stats['tempo'] = possessions_estimate  # Can't calculate without play-by-play

                        team_stats[team] = stats
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
            'ppg': 70.0, 'opp_ppg': 70.0, 'win_pct': 0.500,
            'off_eff': 100.0, 'def_eff': 100.0, 'tempo': 70.0
        })

        away_stats = team_stats.get(away_team, {
            'ppg': 70.0, 'opp_ppg': 70.0, 'win_pct': 0.500,
            'off_eff': 100.0, 'def_eff': 100.0, 'tempo': 70.0
        })

        features = {
            # Game metadata
            'season': game['season'],
            'date': game['date'],
            'home_team': home_team,
            'away_team': away_team,
            'actual_total': game['actual_total'],
            'home_score': game['home_score'],
            'away_score': game['away_score'],

            # Home team stats (approximations)
            'home_ppg': home_stats.get('ppg', 70.0),
            'home_opp_ppg': home_stats.get('opp_ppg', 70.0),
            'home_win_pct': home_stats.get('win_pct', 0.500),
            'home_off_eff': home_stats.get('off_eff', 100.0),
            'home_def_eff': home_stats.get('def_eff', 100.0),
            'home_tempo': home_stats.get('tempo', 70.0),

            # Away team stats (approximations)
            'away_ppg': away_stats.get('ppg', 70.0),
            'away_opp_ppg': away_stats.get('opp_ppg', 70.0),
            'away_win_pct': away_stats.get('win_pct', 0.500),
            'away_off_eff': away_stats.get('off_eff', 100.0),
            'away_def_eff': away_stats.get('def_eff', 100.0),
            'away_tempo': away_stats.get('tempo', 70.0),
        }

        # Differentials
        features['ppg_diff'] = home_stats.get('ppg', 70.0) - away_stats.get('ppg', 70.0)
        features['win_pct_diff'] = home_stats.get('win_pct', 0.500) - away_stats.get('win_pct', 0.500)
        features['off_eff_diff'] = home_stats.get('off_eff', 100.0) - away_stats.get('off_eff', 100.0)
        features['def_eff_diff'] = away_stats.get('def_eff', 100.0) - home_stats.get('def_eff', 100.0)

        # Expected totals (similar to KenPom approach)
        avg_tempo = (home_stats.get('tempo', 70.0) + away_stats.get('tempo', 70.0)) / 2
        features['avg_tempo'] = avg_tempo
        features['expected_total_simple'] = home_stats.get('ppg', 70.0) + away_stats.get('ppg', 70.0)
        features['expected_total_eff'] = ((home_stats.get('off_eff', 100.0) + away_stats.get('off_eff', 100.0)) / 200) * avg_tempo

        return features

    def scrape_season(self, season="2024"):
        """Scrape complete season"""
        logger.info(f"="*60)
        logger.info(f"Scraping NCAAB {season} season...")
        logger.info(f"="*60)

        # Get games
        games_df = self.get_season_games(season)
        if games_df is None:
            return None

        time.sleep(3)  # Be polite

        # Get team stats
        team_stats = self.get_team_stats(season)

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

    def scrape_multiple_seasons(self, seasons=["2023", "2024", "2025"]):
        """Scrape multiple seasons"""
        all_data = []

        for season in seasons:
            logger.info(f"\n{'='*60}")
            logger.info(f"Season: {season}")
            logger.info(f"{'='*60}")

            df = self.scrape_season(season)
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
        output_file = f"{self.output_dir}/ncaab_historical_{timestamp}.csv"
        combined.to_csv(output_file, index=False)

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ NCAAB SCRAPING COMPLETE!")
        logger.info(f"{'='*60}")
        logger.info(f"Total games: {len(combined)}")
        logger.info(f"Features: {len(combined.columns)}")
        logger.info(f"Saved to: {output_file}")

        # Also save as latest
        latest_file = f"{self.output_dir}/ncaab_historical_latest.csv"
        combined.to_csv(latest_file, index=False)
        logger.info(f"Latest: {latest_file}")

        logger.info(f"\n📊 NOTE: Stats are approximations from Sports-Reference")
        logger.info(f"   Not as accurate as KenPom adjusted metrics")
        logger.info(f"   But includes proper time-series data!")

        return combined


if __name__ == "__main__":
    scraper = NCAABHistoricalScraper()

    # Scrape last 3 seasons (using end year: 2022-23 = 2023, etc.)
    df = scraper.scrape_multiple_seasons(["2023", "2024", "2025"])

    if df is not None:
        print("\n" + "="*60)
        print("NCAAB DATA SUMMARY")
        print("="*60)
        print(f"Games: {len(df)}")
        print(f"Average total: {df['actual_total'].mean():.1f} points")
        print(f"Total range: {df['actual_total'].min():.0f} - {df['actual_total'].max():.0f}")
        print("="*60)
