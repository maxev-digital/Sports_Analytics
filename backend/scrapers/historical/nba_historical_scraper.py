"""
NBA Historical Data Scraper
Collects game-by-game data with team stats for XGBoost training

Data Source: NBA Official API (via nba_api)
Seasons: 2022-23, 2023-24, 2024-25
Output: ~4,000 games with features
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import os
import sys

# Try importing nba_api
try:
    from nba_api.stats.endpoints import LeagueGameLog, TeamGameLog, LeagueStandings
    from nba_api.stats.static import teams as nba_teams
except ImportError:
    print("ERROR: nba_api not installed")
    print("Install with: pip install nba-api")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NBAHistoricalScraper:
    """Scrape historical NBA games with team stats at time of game"""

    def __init__(self):
        self.output_dir = "backend/data/historical/nba"
        os.makedirs(self.output_dir, exist_ok=True)

    def get_all_games(self, season="2023-24"):
        """Get all games from a season"""
        logger.info(f"Fetching games for {season} season...")

        try:
            game_log = LeagueGameLog(
                season=season,
                season_type_all_star="Regular Season",
                timeout=60
            )

            df = game_log.get_data_frames()[0]
            logger.info(f"  Found {len(df)} game records")

            # Each game appears twice (once per team), so actual games = len/2
            unique_games = len(df['GAME_ID'].unique())
            logger.info(f"  Unique games: {unique_games}")

            return df

        except Exception as e:
            logger.error(f"Error fetching games: {e}")
            return None

    def calculate_team_stats_to_date(self, team_id, season, game_date, all_games):
        """
        Calculate team's stats up to (but not including) a specific game
        This gives us team's form AT THE TIME of the game
        """
        # Filter to this team's games before this date
        team_games = all_games[
            (all_games['TEAM_ID'] == team_id) &
            (all_games['GAME_DATE'] < game_date)
        ].sort_values('GAME_DATE')

        if len(team_games) == 0:
            # First game of season - use league averages
            return {
                'games_played': 0,
                'wins': 0,
                'losses': 0,
                'win_pct': 0.5,
                'ppg': 110.0,
                'opp_ppg': 110.0,
                'point_diff': 0.0,
                'fg_pct': 0.460,
                'fg3_pct': 0.360,
                'ft_pct': 0.780,
                'rebounds': 43.0,
                'assists': 25.0,
                'turnovers': 14.0,
                'steals': 7.5,
                'blocks': 5.0,
                'plus_minus': 0.0,
                'last_5_ppg': 110.0,
                'last_10_ppg': 110.0,
                'last_5_wins': 0,
                'last_10_wins': 0,
            }

        # Calculate cumulative stats
        stats = {
            'games_played': len(team_games),
            'wins': (team_games['WL'] == 'W').sum(),
            'losses': (team_games['WL'] == 'L').sum(),
            'win_pct': (team_games['WL'] == 'W').mean(),
            'ppg': team_games['PTS'].mean(),
            'opp_ppg': team_games['PTS'].mean() - team_games['PLUS_MINUS'].mean(),  # Approximate
            'point_diff': team_games['PLUS_MINUS'].mean(),
            'fg_pct': team_games['FG_PCT'].mean(),
            'fg3_pct': team_games['FG3_PCT'].mean(),
            'ft_pct': team_games['FT_PCT'].mean(),
            'rebounds': team_games['REB'].mean(),
            'assists': team_games['AST'].mean(),
            'turnovers': team_games['TOV'].mean(),
            'steals': team_games['STL'].mean(),
            'blocks': team_games['BLK'].mean(),
            'plus_minus': team_games['PLUS_MINUS'].mean(),
        }

        # Recent form (last 5 and last 10 games)
        last_5 = team_games.tail(5)
        last_10 = team_games.tail(10)

        stats['last_5_ppg'] = last_5['PTS'].mean() if len(last_5) > 0 else stats['ppg']
        stats['last_10_ppg'] = last_10['PTS'].mean() if len(last_10) > 0 else stats['ppg']
        stats['last_5_wins'] = (last_5['WL'] == 'W').sum() if len(last_5) > 0 else 0
        stats['last_10_wins'] = (last_10['WL'] == 'W').sum() if len(last_10) > 0 else 0

        return stats

    def engineer_features(self, row, home_stats, away_stats, season):
        """Engineer features for XGBoost from game + team stats"""

        features = {
            # Game metadata
            'season': season,
            'game_date': row['GAME_DATE'],
            'home_team': row['MATCHUP'].split('@')[0].strip() if '@' in row['MATCHUP'] else row['TEAM_ABBREVIATION'],
            'away_team': row['MATCHUP'].split('@')[1].strip() if '@' in row['MATCHUP'] else '',

            # Actual result will be added later from both team records

            # Home team stats
            'home_games_played': home_stats['games_played'],
            'home_wins': home_stats['wins'],
            'home_win_pct': home_stats['win_pct'],
            'home_ppg': home_stats['ppg'],
            'home_opp_ppg': home_stats['opp_ppg'],
            'home_point_diff': home_stats['point_diff'],
            'home_fg_pct': home_stats['fg_pct'],
            'home_fg3_pct': home_stats['fg3_pct'],
            'home_ft_pct': home_stats['ft_pct'],
            'home_rebounds': home_stats['rebounds'],
            'home_assists': home_stats['assists'],
            'home_turnovers': home_stats['turnovers'],
            'home_steals': home_stats['steals'],
            'home_blocks': home_stats['blocks'],
            'home_plus_minus': home_stats['plus_minus'],
            'home_last_5_ppg': home_stats['last_5_ppg'],
            'home_last_10_ppg': home_stats['last_10_ppg'],
            'home_last_5_wins': home_stats['last_5_wins'],
            'home_last_10_wins': home_stats['last_10_wins'],

            # Away team stats
            'away_games_played': away_stats['games_played'],
            'away_wins': away_stats['wins'],
            'away_win_pct': away_stats['win_pct'],
            'away_ppg': away_stats['ppg'],
            'away_opp_ppg': away_stats['opp_ppg'],
            'away_point_diff': away_stats['point_diff'],
            'away_fg_pct': away_stats['fg_pct'],
            'away_fg3_pct': away_stats['fg3_pct'],
            'away_ft_pct': away_stats['ft_pct'],
            'away_rebounds': away_stats['rebounds'],
            'away_assists': away_stats['assists'],
            'away_turnovers': away_stats['turnovers'],
            'away_steals': away_stats['steals'],
            'away_blocks': away_stats['blocks'],
            'away_plus_minus': away_stats['plus_minus'],
            'away_last_5_ppg': away_stats['last_5_ppg'],
            'away_last_10_ppg': away_stats['last_10_ppg'],
            'away_last_5_wins': away_stats['last_5_wins'],
            'away_last_10_wins': away_stats['last_10_wins'],
        }

        # Differentials
        features['win_pct_diff'] = home_stats['win_pct'] - away_stats['win_pct']
        features['ppg_diff'] = home_stats['ppg'] - away_stats['ppg']
        features['point_diff_diff'] = home_stats['point_diff'] - away_stats['point_diff']
        features['fg_pct_diff'] = home_stats['fg_pct'] - away_stats['fg_pct']
        features['fg3_pct_diff'] = home_stats['fg3_pct'] - away_stats['fg3_pct']
        features['turnover_diff'] = away_stats['turnovers'] - home_stats['turnovers']  # Lower is better
        features['rebound_diff'] = home_stats['rebounds'] - away_stats['rebounds']

        # Expected totals
        features['expected_total_simple'] = home_stats['ppg'] + away_stats['ppg']
        features['expected_total_vs_defense'] = home_stats['ppg'] + away_stats['opp_ppg']

        # Recent form
        features['home_momentum'] = home_stats['last_5_wins'] - 2.5  # Centered at .500
        features['away_momentum'] = away_stats['last_5_wins'] - 2.5

        return features

    def scrape_season(self, season="2023-24"):
        """Scrape complete season with features"""
        logger.info(f"=" * 60)
        logger.info(f"Scraping NBA {season} season...")
        logger.info(f"=" * 60)

        # Get all games
        all_games = self.get_all_games(season)
        if all_games is None:
            return None

        # Process each unique game
        unique_game_ids = all_games['GAME_ID'].unique()
        logger.info(f"Processing {len(unique_game_ids)} games...")

        games_with_features = []

        for idx, game_id in enumerate(unique_game_ids):
            if idx % 100 == 0:
                logger.info(f"  Progress: {idx}/{len(unique_game_ids)} games")

            # Get both teams' records for this game
            game_records = all_games[all_games['GAME_ID'] == game_id]

            if len(game_records) != 2:
                continue  # Skip incomplete games

            # Identify home and away teams
            # In MATCHUP field: "vs." means home, "@" means away
            home_record = game_records[game_records['MATCHUP'].str.contains('vs.')].iloc[0] if any(game_records['MATCHUP'].str.contains('vs.')) else game_records.iloc[0]
            away_record = game_records[game_records['MATCHUP'].str.contains('@')].iloc[0] if any(game_records['MATCHUP'].str.contains('@')) else game_records.iloc[1]

            # Calculate team stats up to this game
            home_stats = self.calculate_team_stats_to_date(
                home_record['TEAM_ID'],
                season,
                home_record['GAME_DATE'],
                all_games
            )

            away_stats = self.calculate_team_stats_to_date(
                away_record['TEAM_ID'],
                season,
                away_record['GAME_DATE'],
                all_games
            )

            # Engineer features
            features = self.engineer_features(home_record, home_stats, away_stats, season)

            # Add actual total from both teams
            features['actual_total'] = home_record['PTS'] + away_record['PTS']
            features['home_score'] = home_record['PTS']
            features['away_score'] = away_record['PTS']
            features['game_id'] = game_id

            games_with_features.append(features)

        df = pd.DataFrame(games_with_features)
        logger.info(f"[OK] Processed {len(df)} games with features")

        return df

    def scrape_multiple_seasons(self, seasons=["2022-23", "2023-24", "2024-25"]):
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
            time.sleep(2)

        if len(all_data) == 0:
            logger.error("No data collected!")
            return None

        # Combine all seasons
        combined = pd.concat(all_data, ignore_index=True)

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{self.output_dir}/nba_historical_{timestamp}.csv"
        combined.to_csv(output_file, index=False)

        logger.info(f"\n{'='*60}")
        logger.info(f"[COMPLETE]")
        logger.info(f"{'='*60}")
        logger.info(f"Total games: {len(combined)}")
        logger.info(f"Features: {len(combined.columns)}")
        logger.info(f"Saved to: {output_file}")
        logger.info(f"File size: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")

        # Also save as "latest"
        latest_file = f"{self.output_dir}/nba_historical_latest.csv"
        combined.to_csv(latest_file, index=False)
        logger.info(f"Latest: {latest_file}")

        return combined


if __name__ == "__main__":
    scraper = NBAHistoricalScraper()

    # Scrape last 3 seasons
    df = scraper.scrape_multiple_seasons(["2022-23", "2023-24", "2024-25"])

    if df is not None:
        print("\n" + "="*60)
        print("DATA SUMMARY")
        print("="*60)
        print(f"Games: {len(df)}")
        print(f"Date range: {df['game_date'].min()} to {df['game_date'].max()}")
        print(f"Average total: {df['actual_total'].mean():.1f} points")
        print(f"Total range: {df['actual_total'].min():.0f} - {df['actual_total'].max():.0f}")
        print("="*60)
