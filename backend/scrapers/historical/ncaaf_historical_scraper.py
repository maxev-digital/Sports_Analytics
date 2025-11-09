"""
NCAAF Historical Data Scraper
Collects game-by-game data with team stats for XGBoost training

Data Source: College-Football-Reference (cfbstats.com)
Seasons: 2022, 2023, 2024
Output: ~2,500 games with features
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

class NCAAFHistoricalScraper:
    """Scrape historical NCAAF games with team stats"""

    BASE_URL = "https://www.sports-reference.com/cfb"

    def __init__(self):
        self.output_dir = "backend/data/historical/ncaaf"
        os.makedirs(self.output_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_season_games(self, year=2023):
        """Get all games from a season"""
        logger.info(f"Fetching NCAAF {year} season games...")

        url = f"{self.BASE_URL}/years/{year}-schedule.html"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find games table (try different possible IDs)
            table = soup.find('table', {'id': 'schedule'})
            if not table:
                # Try alternative table IDs
                table = soup.find('table', {'id': 'games'})
            if not table:
                # Log available tables for debugging
                all_tables = soup.find_all('table')
                table_ids = [t.get('id') for t in all_tables if t.get('id')]
                logger.error(f"Could not find games table for {year}. Available tables: {table_ids}")
                return pd.DataFrame()  # Return empty DataFrame instead of None

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
                    # Parse game data
                    date = cells[1].text.strip() if len(cells) > 1 else ''
                    winner = cells[4].text.strip() if len(cells) > 4 else ''
                    pts_winner = cells[5].text.strip() if len(cells) > 5 else ''
                    loser = cells[6].text.strip() if len(cells) > 6 else ''
                    pts_loser = cells[7].text.strip() if len(cells) > 7 else ''

                    # Parse scores
                    if not pts_winner.isdigit() or not pts_loser.isdigit():
                        continue

                    pts_winner = int(pts_winner)
                    pts_loser = int(pts_loser)

                    # Determine home/away (@ symbol indicates neutral site or away)
                    at_symbol = cells[3].text.strip() if len(cells) > 3 else ''

                    if '@' in at_symbol:
                        away_team = winner
                        home_team = loser
                        away_score = pts_winner
                        home_score = pts_loser
                    else:
                        home_team = winner
                        away_team = loser
                        home_score = pts_winner
                        away_score = pts_loser

                    game = {
                        'year': year,
                        'date': date,
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_score': home_score,
                        'away_score': away_score,
                        'actual_total': home_score + away_score
                    }

                    games.append(game)

                except Exception as e:
                    logger.warning(f"Error parsing row: {e}")
                    continue

            logger.info(f"  Found {len(games)} games")
            return pd.DataFrame(games)

        except Exception as e:
            logger.error(f"Error fetching {year} games: {e}")
            return None

    def get_team_stats(self, year=2023):
        """Get team stats for the season"""
        logger.info(f"Fetching NCAAF {year} team stats...")

        # College Football Reference uses separate pages for offense and defense
        offense_url = f"{self.BASE_URL}/years/{year}-team-offense.html"
        defense_url = f"{self.BASE_URL}/years/{year}-team-defense.html"

        team_stats = {}

        # Fetch offense stats
        try:
            response = self.session.get(offense_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Team offense stats
            offense_table = soup.find('table', {'id': 'offense'})
            if offense_table:
                rows = offense_table.find('tbody').find_all('tr')
                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) < 8:
                        continue

                    try:
                        team = cells[0].text.strip()
                        stats = {
                            'ppg': float(cells[4].text) if cells[4].text.replace('.', '').isdigit() else 28.0,
                            'yards_pg': float(cells[5].text) if cells[5].text.replace('.', '').isdigit() else 380.0,
                            'yards_per_play': float(cells[6].text) if cells[6].text.replace('.', '').isdigit() else 5.5,
                        }
                        team_stats[team] = stats
                    except:
                        continue
        except Exception as e:
            logger.error(f"Error fetching offense stats: {e}")

        # Fetch defense stats
        try:
            response = self.session.get(defense_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Team defense stats
            defense_table = soup.find('table', {'id': 'defense'})
            if defense_table:
                rows = defense_table.find('tbody').find_all('tr')
                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) < 8:
                        continue

                    try:
                        team = cells[0].text.strip()
                        if team in team_stats:
                            team_stats[team]['opp_ppg'] = float(cells[4].text) if cells[4].text.replace('.', '').isdigit() else 28.0
                            team_stats[team]['opp_yards_pg'] = float(cells[5].text) if cells[5].text.replace('.', '').isdigit() else 380.0
                    except:
                        continue
        except Exception as e:
            logger.error(f"Error fetching defense stats: {e}")

        logger.info(f"  Found stats for {len(team_stats)} teams")
        return team_stats

    def engineer_features(self, game, team_stats):
        """Engineer features from game + team stats"""

        home_team = game['home_team']
        away_team = game['away_team']

        # Get team stats (or defaults)
        home_stats = team_stats.get(home_team, {
            'ppg': 28.0, 'opp_ppg': 28.0, 'yards_pg': 380.0,
            'opp_yards_pg': 380.0, 'yards_per_play': 5.5
        })

        away_stats = team_stats.get(away_team, {
            'ppg': 28.0, 'opp_ppg': 28.0, 'yards_pg': 380.0,
            'opp_yards_pg': 380.0, 'yards_per_play': 5.5
        })

        features = {
            # Game metadata
            'year': game['year'],
            'date': game['date'],
            'home_team': home_team,
            'away_team': away_team,
            'actual_total': game['actual_total'],
            'home_score': game['home_score'],
            'away_score': game['away_score'],

            # Home team stats
            'home_ppg': home_stats.get('ppg', 28.0),
            'home_opp_ppg': home_stats.get('opp_ppg', 28.0),
            'home_yards_pg': home_stats.get('yards_pg', 380.0),
            'home_opp_yards_pg': home_stats.get('opp_yards_pg', 380.0),
            'home_yards_per_play': home_stats.get('yards_per_play', 5.5),

            # Away team stats
            'away_ppg': away_stats.get('ppg', 28.0),
            'away_opp_ppg': away_stats.get('opp_ppg', 28.0),
            'away_yards_pg': away_stats.get('yards_pg', 380.0),
            'away_opp_yards_pg': away_stats.get('opp_yards_pg', 380.0),
            'away_yards_per_play': away_stats.get('yards_per_play', 5.5),
        }

        # Differentials
        features['ppg_diff'] = home_stats.get('ppg', 28.0) - away_stats.get('ppg', 28.0)
        features['yards_pg_diff'] = home_stats.get('yards_pg', 380.0) - away_stats.get('yards_pg', 380.0)
        features['point_diff'] = (home_stats.get('ppg', 28.0) - home_stats.get('opp_ppg', 28.0)) - \
                                  (away_stats.get('ppg', 28.0) - away_stats.get('opp_ppg', 28.0))

        # Expected totals
        features['expected_total_simple'] = home_stats.get('ppg', 28.0) + away_stats.get('ppg', 28.0)
        features['expected_total_vs_defense'] = home_stats.get('ppg', 28.0) + away_stats.get('opp_ppg', 28.0)

        return features

    def scrape_season(self, year=2023):
        """Scrape complete season"""
        logger.info(f"="*60)
        logger.info(f"Scraping NCAAF {year} season...")
        logger.info(f"="*60)

        # Get games
        games_df = self.get_season_games(year)
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
            if idx % 200 == 0:
                logger.info(f"  Progress: {idx}/{len(games_df)}")

            features = self.engineer_features(game, team_stats)
            games_with_features.append(features)

        df = pd.DataFrame(games_with_features)
        logger.info(f"[OK] Processed {len(df)} games")

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
        output_file = f"{self.output_dir}/ncaaf_historical_{timestamp}.csv"
        combined.to_csv(output_file, index=False)

        logger.info(f"\n{'='*60}")
        logger.info(f"[NCAAF SCRAPING COMPLETE]")
        logger.info(f"{'='*60}")
        logger.info(f"Total games: {len(combined)}")
        logger.info(f"Features: {len(combined.columns)}")
        logger.info(f"Saved to: {output_file}")

        # Also save as latest
        latest_file = f"{self.output_dir}/ncaaf_historical_latest.csv"
        combined.to_csv(latest_file, index=False)
        logger.info(f"Latest: {latest_file}")

        return combined


if __name__ == "__main__":
    scraper = NCAAFHistoricalScraper()

    # Scrape last 3 seasons
    df = scraper.scrape_multiple_seasons([2022, 2023, 2024])

    if df is not None and len(df) > 0:
        print("\n" + "="*60)
        print("NCAAF DATA SUMMARY")
        print("="*60)
        print(f"Games: {len(df)}")
        if 'actual_total' in df.columns:
            print(f"Average total: {df['actual_total'].mean():.1f} points")
            print(f"Total range: {df['actual_total'].min():.0f} - {df['actual_total'].max():.0f}")
        print("="*60)
    else:
        print("\n[WARNING] No games were scraped. Check the logs above for table ID errors.")
