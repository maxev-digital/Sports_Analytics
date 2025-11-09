"""
NBA Historical Data Loader

Fetches historical NBA game data for model training:
- Game results (scores, totals, margins)
- Team statistics (pace, offensive/defensive ratings)
- Advanced metrics (fg%, 3pt%, turnovers, rebounds)
- Momentum indicators (last 5, last 10 games)

Data Sources:
1. Historical CSV files in backend/data/historical/nba/
2. NBA API (nba_api package) for additional seasons
3. Cached team stats
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Tuple, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class NBADataLoader:
    """Load and preprocess historical NBA data for model training"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data" / "historical" / "nba"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_historical_csv(self, filepath: str = None) -> pd.DataFrame:
        """
        Load historical NBA game data from CSV

        Args:
            filepath: Path to CSV file. If None, uses latest file.

        Returns:
            DataFrame with historical games
        """
        if filepath is None:
            # Find latest historical file
            files = list(self.data_dir.glob("nba_historical_*.csv"))
            if not files:
                logger.error("No NBA historical data files found")
                return pd.DataFrame()

            # Use most recent file
            filepath = sorted(files)[-1]

        logger.info(f"Loading NBA historical data from {filepath}")

        try:
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {len(df)} games from historical data")
            return df
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return pd.DataFrame()

    def filter_by_seasons(self, df: pd.DataFrame, seasons: List[str]) -> pd.DataFrame:
        """
        Filter DataFrame to specific NBA seasons

        Args:
            df: Historical games DataFrame
            seasons: List of season strings like ["2022-23", "2023-24"]

        Returns:
            Filtered DataFrame
        """
        if not seasons:
            return df

        filtered = df[df['season'].isin(seasons)]
        logger.info(f"Filtered to {len(filtered)} games from seasons: {seasons}")

        return filtered

    def prepare_training_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and prepare data for model training

        - Remove games with missing data
        - Calculate derived features
        - Ensure correct data types
        - Create target variables

        Returns:
            Clean training-ready DataFrame
        """
        logger.info("Preparing NBA training data...")

        # Remove rows with missing crucial data
        original_len = len(df)
        df = df.dropna(subset=['actual_total', 'home_score', 'away_score'])

        if len(df) < original_len:
            logger.info(f"Removed {original_len - len(df)} rows with missing target data")

        # Fill missing stats with league averages
        league_avg_pace = 99.0
        league_avg_ppg = 113.0
        league_avg_fg_pct = 0.46
        league_avg_fg3_pct = 0.36

        df['home_ppg'] = df['home_ppg'].fillna(league_avg_ppg)
        df['away_ppg'] = df['away_ppg'].fillna(league_avg_ppg)
        df['home_fg_pct'] = df['home_fg_pct'].fillna(league_avg_fg_pct)
        df['away_fg_pct'] = df['away_fg_pct'].fillna(league_avg_fg_pct)
        df['home_fg3_pct'] = df['home_fg3_pct'].fillna(league_avg_fg3_pct)
        df['away_fg3_pct'] = df['away_fg3_pct'].fillna(league_avg_fg3_pct)

        # Calculate derived features if not present
        if 'total' not in df.columns:
            df['total'] = df['actual_total']
        if 'home_margin' not in df.columns:
            df['home_margin'] = df['home_score'] - df['away_score']
        if 'home_win' not in df.columns:
            df['home_win'] = (df['home_margin'] > 0).astype(int)

        # Add estimated pace if missing
        if 'home_pace' not in df.columns:
            # Estimate from points per game
            df['home_pace'] = (df['home_ppg'] / 110.0) * league_avg_pace
            df['away_pace'] = (df['away_ppg'] / 110.0) * league_avg_pace

        # Add offensive/defensive ratings if missing
        if 'home_off_rating' not in df.columns:
            df['home_off_rating'] = (df['home_ppg'] / df.get('home_pace', league_avg_pace)) * 100
            df['away_off_rating'] = (df['away_ppg'] / df.get('away_pace', league_avg_pace)) * 100

        if 'home_def_rating' not in df.columns:
            df['home_def_rating'] = (df['home_opp_ppg'] / df.get('home_pace', league_avg_pace)) * 100
            df['away_def_rating'] = (df['away_opp_ppg'] / df.get('away_pace', league_avg_pace)) * 100

        logger.info(f"Training dataset prepared: {len(df)} games")

        return df

    def load_historical_data(self, seasons: List[str] = None) -> pd.DataFrame:
        """
        Load and prepare historical NBA data

        Args:
            seasons: List of seasons like ["2022-23", "2023-24", "2024-25"]
                    If None, loads all available data

        Returns:
            Training-ready DataFrame
        """
        # Load historical CSV
        df = self.load_historical_csv()

        if df.empty:
            logger.error("No historical data available")
            return pd.DataFrame()

        # Filter to specific seasons if requested
        if seasons:
            df = self.filter_by_seasons(df, seasons)

        # Prepare for training
        df = self.prepare_training_data(df)

        return df


def load_nba_training_data(seasons: List[str] = None) -> pd.DataFrame:
    """
    Convenience function to load NBA training data

    Args:
        seasons: List of season strings. If None, uses last 3 seasons.

    Returns:
        Training-ready DataFrame
    """
    if seasons is None:
        # Default to recent seasons
        seasons = ["2022-23", "2023-24", "2024-25"]

    loader = NBADataLoader()
    training_df = loader.load_historical_data(seasons)

    if training_df.empty:
        logger.warning("No NBA training data available")
        return pd.DataFrame()

    logger.info(f"Loaded {len(training_df)} NBA games for training")

    return training_df
