"""
NFL Historical Data Loader

Fetches historical NFL game data for model training:
- Game results (scores, totals, margins)
- Team statistics (PPG, yards/play, turnovers)
- Advanced metrics (3rd down%, red zone%, time of possession)
- Rest days and scheduling factors

Data Sources:
1. Historical CSV files in backend/data/historical/nfl/
2. Pro Football Reference scraper (backend/scrapers/historical/nfl_historical_scraper.py)
3. Synthetic game generation for testing
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class NFLDataLoader:
    """Load and preprocess historical NFL data for model training"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data" / "historical" / "nfl"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_historical_csv(self, filepath: str = None) -> pd.DataFrame:
        """
        Load historical NFL game data from CSV

        Args:
            filepath: Path to CSV file. If None, looks for latest file.

        Returns:
            DataFrame with historical games
        """
        if filepath is None:
            # Find latest historical file
            files = list(self.data_dir.glob("nfl_historical_*.csv"))
            if not files:
                logger.warning("No NFL historical data files found")
                return pd.DataFrame()

            # Use most recent file
            filepath = sorted(files)[-1]

        logger.info(f"Loading NFL historical data from {filepath}")

        try:
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {len(df)} games from historical data")
            return df
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return pd.DataFrame()

    def generate_sample_nfl_data(self, n_games: int = 1000) -> pd.DataFrame:
        """
        Generate realistic synthetic NFL game data for testing

        NFL has ~272 games per season (17 weeks x 16 games)
        3 seasons = ~800 games

        Args:
            n_games: Number of games to generate

        Returns:
            DataFrame with synthetic NFL games
        """
        logger.info(f"Generating {n_games} synthetic NFL games...")

        np.random.seed(42)

        teams = [
            'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
            'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
            'LAC', 'LAR', 'LV', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
            'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
        ]

        games = []

        for i in range(n_games):
            # Random matchup
            home_team = np.random.choice(teams)
            away_team = np.random.choice([t for t in teams if t != home_team])

            # Team strength (PPG)
            home_ppg = np.random.uniform(18.0, 28.0)
            away_ppg = np.random.uniform(18.0, 28.0)
            home_pa = np.random.uniform(18.0, 28.0)
            away_pa = np.random.uniform(18.0, 28.0)

            # Home field advantage ~2.5 points
            home_advantage = 2.5

            # Expected score based on team stats
            home_expected = (home_ppg + (22.0 - away_pa)) / 2 + home_advantage
            away_expected = (away_ppg + (22.0 - home_pa)) / 2

            # Add variance (NFL games have ~13-14 point standard deviation)
            home_score = max(0, int(np.random.normal(home_expected, 7.0)))
            away_score = max(0, int(np.random.normal(away_expected, 7.0)))

            # Team stats
            home_ypp = np.random.uniform(4.8, 6.2)
            away_ypp = np.random.uniform(4.8, 6.2)
            home_third_down = np.random.uniform(32.0, 48.0)
            away_third_down = np.random.uniform(32.0, 48.0)

            # Week and season
            week = (i % 272) // 16 + 1  # 17 weeks, ~16 games per week
            season = 2022 + (i // 272)  # Spread across seasons

            game = {
                'game_id': f'NFL_{season}_W{week:02d}_{i:04d}',
                'season': season,
                'week': week,
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'total': home_score + away_score,
                'home_margin': home_score - away_score,
                'home_win': 1 if home_score > away_score else 0,

                # Home team stats
                'home_ppg': home_ppg,
                'home_points_allowed_per_game': home_pa,
                'home_yards_per_play': home_ypp,
                'home_yards_per_play_allowed': 6.5 - home_ypp,
                'home_third_down_pct': home_third_down,
                'home_third_down_pct_defense': 42.0 - (home_third_down - 40.0),
                'home_turnover_margin': np.random.uniform(-1.0, 1.0),
                'home_win_pct': np.random.uniform(0.2, 0.8),
                'home_last_4_win_pct': np.random.uniform(0.0, 1.0),
                'home_rest_days': np.random.choice([3, 7, 7, 7, 7, 7, 14]),  # Mostly 7, some Thursday/bye

                # Away team stats
                'away_ppg': away_ppg,
                'away_points_allowed_per_game': away_pa,
                'away_yards_per_play': away_ypp,
                'away_yards_per_play_allowed': 6.5 - away_ypp,
                'away_third_down_pct': away_third_down,
                'away_third_down_pct_defense': 42.0 - (away_third_down - 40.0),
                'away_turnover_margin': np.random.uniform(-1.0, 1.0),
                'away_win_pct': np.random.uniform(0.2, 0.8),
                'away_last_4_win_pct': np.random.uniform(0.0, 1.0),
                'away_rest_days': np.random.choice([3, 7, 7, 7, 7, 7, 14]),

                # Game context
                'is_division_game': np.random.choice([0, 0, 0, 1]),  # ~25% division games
                'is_primetime': np.random.choice([0, 0, 0, 0, 0, 1]),  # ~16% primetime
                'temperature': np.random.uniform(40.0, 85.0),
                'wind_speed': np.random.uniform(0.0, 15.0),
            }

            games.append(game)

        df = pd.DataFrame(games)

        # Save to cache
        cache_file = self.data_dir / "sample_training_data.csv"
        df.to_csv(cache_file, index=False)
        logger.info(f"Saved sample data to {cache_file}")

        logger.info(f"Generated {len(df)} synthetic NFL games")
        logger.info(f"  Average total: {df['total'].mean():.1f}")
        logger.info(f"  Home win %: {df['home_win'].mean():.1%}")

        return df

    def prepare_training_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and prepare data for model training

        - Remove games with missing crucial data
        - Fill missing stats with league averages
        - Create derived features
        - Ensure correct data types

        Returns:
            Clean training-ready DataFrame
        """
        logger.info("Preparing NFL training data...")

        # Remove rows with missing target data
        original_len = len(df)
        df = df.dropna(subset=['total', 'home_score', 'away_score'])

        if len(df) < original_len:
            logger.info(f"Removed {original_len - len(df)} rows with missing target data")

        # Fill missing stats with league averages
        df['home_ppg'] = df['home_ppg'].fillna(22.0)
        df['away_ppg'] = df['away_ppg'].fillna(22.0)
        df['home_points_allowed_per_game'] = df['home_points_allowed_per_game'].fillna(22.0)
        df['away_points_allowed_per_game'] = df['away_points_allowed_per_game'].fillna(22.0)
        df['home_yards_per_play'] = df['home_yards_per_play'].fillna(5.5)
        df['away_yards_per_play'] = df['away_yards_per_play'].fillna(5.5)
        df['home_third_down_pct'] = df['home_third_down_pct'].fillna(40.0)
        df['away_third_down_pct'] = df['away_third_down_pct'].fillna(40.0)
        df['home_turnover_margin'] = df['home_turnover_margin'].fillna(0.0)
        df['away_turnover_margin'] = df['away_turnover_margin'].fillna(0.0)

        # Ensure target variables exist
        if 'home_margin' not in df.columns:
            df['home_margin'] = df['home_score'] - df['away_score']
        if 'home_win' not in df.columns:
            df['home_win'] = (df['home_margin'] > 0).astype(int)

        logger.info(f"Training dataset prepared: {len(df)} games")

        return df

    def load_historical_data(self, seasons: List[str] = None) -> pd.DataFrame:
        """
        Load and prepare historical NFL data

        Args:
            seasons: List of seasons like ["2022", "2023", "2024"]
                    If None, loads all available data

        Returns:
            Training-ready DataFrame
        """
        # Try to load historical CSV
        df = self.load_historical_csv()

        if df.empty:
            # Fall back to sample data
            logger.info("No historical data found, generating sample data...")
            cache_file = self.data_dir / "sample_training_data.csv"

            if cache_file.exists():
                logger.info(f"Loading cached sample data from {cache_file}")
                df = pd.read_csv(cache_file)
            else:
                df = self.generate_sample_nfl_data(n_games=1000)

        # Filter to specific seasons if requested
        if seasons and 'season' in df.columns:
            seasons_int = [int(s) for s in seasons]
            df = df[df['season'].isin(seasons_int)]
            logger.info(f"Filtered to {len(df)} games from seasons: {seasons}")

        # Prepare for training
        df = self.prepare_training_data(df)

        return df


def load_nfl_training_data(seasons: List[str] = None) -> pd.DataFrame:
    """
    Convenience function to load NFL training data

    Args:
        seasons: List of season strings. If None, uses available data.

    Returns:
        Training-ready DataFrame
    """
    if seasons is None:
        # Default to recent seasons
        seasons = ["2022", "2023", "2024"]

    loader = NFLDataLoader()
    training_df = loader.load_historical_data(seasons)

    if training_df.empty:
        logger.error("No NFL training data available")
        return pd.DataFrame()

    logger.info(f"Loaded {len(training_df)} NFL games for training")

    return training_df
