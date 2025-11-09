"""
NCAAF Historical Data Loader

Fetches historical NCAAF game data for model training:
- Game results (scores, totals, margins)
- Team statistics (PPG, yards/play, turnovers)
- Conference information
- Recruiting/talent composites

Data Sources:
1. Historical CSV files in backend/data/historical/ncaaf/
2. ESPN API for college football
3. Synthetic game generation for testing
"""

import pandas as pd
import numpy as np
import logging
from typing import List
from pathlib import Path

logger = logging.getLogger(__name__)


class NCAAFDataLoader:
    """Load and preprocess historical NCAAF data for model training"""

    # Power 5 conferences
    POWER_5 = ['SEC', 'B10', 'B12', 'ACC', 'P12']

    # FBS conferences
    ALL_CONFERENCES = POWER_5 + ['AAC', 'MWC', 'CUSA', 'MAC', 'SBC', 'IND']

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data" / "historical" / "ncaaf"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_historical_csv(self, filepath: str = None) -> pd.DataFrame:
        """
        Load historical NCAAF game data from CSV

        Args:
            filepath: Path to CSV file. If None, looks for latest file.

        Returns:
            DataFrame with historical games
        """
        if filepath is None:
            # Find latest historical file
            files = list(self.data_dir.glob("ncaaf_historical_*.csv"))
            if not files:
                logger.warning("No NCAAF historical data files found")
                return pd.DataFrame()

            # Use most recent file
            filepath = sorted(files)[-1]

        logger.info(f"Loading NCAAF historical data from {filepath}")

        try:
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {len(df)} games from historical data")
            return df
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return pd.DataFrame()

    def generate_sample_ncaaf_data(self, n_games: int = 1500) -> pd.DataFrame:
        """
        Generate realistic synthetic NCAAF game data for testing

        NCAAF has ~850 FBS games per season (130 teams x 12 games / 2)
        2 seasons = ~1700 games

        Args:
            n_games: Number of games to generate

        Returns:
            DataFrame with synthetic NCAAF games
        """
        logger.info(f"Generating {n_games} synthetic NCAAF games...")

        np.random.seed(42)

        # Representative Power 5 + Group of 5 teams
        power5_teams = [
            ('Alabama', 'SEC'), ('Georgia', 'SEC'), ('LSU', 'SEC'), ('Texas', 'SEC'),
            ('Ohio State', 'B10'), ('Michigan', 'B10'), ('Penn State', 'B10'), ('USC', 'B10'),
            ('Oklahoma', 'B12'), ('Texas Tech', 'B12'), ('Kansas State', 'B12'),
            ('Clemson', 'ACC'), ('Florida State', 'ACC'), ('Miami', 'ACC'),
            ('Oregon', 'P12'), ('Washington', 'P12'), ('UCLA', 'P12'),
        ]

        group5_teams = [
            ('Boise State', 'MWC'), ('San Diego State', 'MWC'), ('Air Force', 'MWC'),
            ('Memphis', 'AAC'), ('Cincinnati', 'AAC'), ('UCF', 'AAC'),
            ('Appalachian State', 'SBC'), ('Coastal Carolina', 'SBC'),
            ('Western Michigan', 'MAC'), ('Toledo', 'MAC'),
            ('Louisiana Tech', 'CUSA'), ('UTSA', 'CUSA'),
        ]

        all_teams = power5_teams + group5_teams

        games = []

        for i in range(n_games):
            # Random matchup (70% same conference, 30% out of conference)
            if np.random.random() < 0.7:
                # Same conference matchup
                conference = np.random.choice(self.ALL_CONFERENCES)
                conf_teams = [t for t in all_teams if t[1] == conference]
                if len(conf_teams) < 2:
                    conf_teams = all_teams  # Fallback
                home_team, home_conf = conf_teams[np.random.randint(0, len(conf_teams))]
                away_team, away_conf = conf_teams[np.random.randint(0, len(conf_teams))]
                while away_team == home_team:
                    away_team, away_conf = conf_teams[np.random.randint(0, len(conf_teams))]
                is_conference_game = 1
            else:
                # Out of conference
                home_team, home_conf = all_teams[np.random.randint(0, len(all_teams))]
                away_team, away_conf = all_teams[np.random.randint(0, len(all_teams))]
                while away_team == home_team:
                    away_team, away_conf = all_teams[np.random.randint(0, len(all_teams))]
                is_conference_game = 0

            # Team strength varies widely in college
            # Power 5 teams average ~30 PPG, Group of 5 ~26 PPG
            home_ppg = np.random.uniform(20.0, 40.0) if home_conf in self.POWER_5 else np.random.uniform(18.0, 34.0)
            away_ppg = np.random.uniform(20.0, 40.0) if away_conf in self.POWER_5 else np.random.uniform(18.0, 34.0)
            home_pa = np.random.uniform(18.0, 35.0)
            away_pa = np.random.uniform(18.0, 35.0)

            # Home field advantage ~3.5-4 points in college
            home_advantage = 3.5

            # Expected score
            home_expected = (home_ppg + (28.0 - away_pa)) / 2 + home_advantage
            away_expected = (away_ppg + (28.0 - home_pa)) / 2

            # College has MORE variance (blowouts common)
            home_score = max(0, int(np.random.normal(home_expected, 10.0)))
            away_score = max(0, int(np.random.normal(away_expected, 10.0)))

            # Team stats
            home_ypp = np.random.uniform(5.0, 7.0)
            away_ypp = np.random.uniform(5.0, 7.0)
            home_third_down = np.random.uniform(32.0, 50.0)
            away_third_down = np.random.uniform(32.0, 50.0)

            # Talent composite (0-1 scale, Power 5 typically higher)
            home_talent = np.random.uniform(0.6, 0.95) if home_conf in self.POWER_5 else np.random.uniform(0.3, 0.7)
            away_talent = np.random.uniform(0.6, 0.95) if away_conf in self.POWER_5 else np.random.uniform(0.3, 0.7)

            # Week and season
            week = (i % 850) // 70 + 1  # ~12 weeks
            season = 2023 + (i // 850)  # Spread across seasons

            game = {
                'game_id': f'NCAAF_{season}_W{week:02d}_{i:04d}',
                'season': season,
                'week': week,
                'home_team': home_team,
                'away_team': away_team,
                'home_conference': home_conf,
                'away_conference': away_conf,
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
                'home_turnover_margin': np.random.uniform(-1.5, 1.5),
                'home_win_pct': np.random.uniform(0.1, 0.95),
                'home_last_3_win_pct': np.random.uniform(0.0, 1.0),
                'home_talent_composite': home_talent,
                'home_plays_per_game': np.random.uniform(60.0, 85.0),

                # Away team stats
                'away_ppg': away_ppg,
                'away_points_allowed_per_game': away_pa,
                'away_yards_per_play': away_ypp,
                'away_yards_per_play_allowed': 6.5 - away_ypp,
                'away_third_down_pct': away_third_down,
                'away_third_down_pct_defense': 42.0 - (away_third_down - 40.0),
                'away_turnover_margin': np.random.uniform(-1.5, 1.5),
                'away_win_pct': np.random.uniform(0.1, 0.95),
                'away_last_3_win_pct': np.random.uniform(0.0, 1.0),
                'away_talent_composite': away_talent,
                'away_plays_per_game': np.random.uniform(60.0, 85.0),

                # Game context
                'is_conference_game': is_conference_game,
                'is_rivalry_game': np.random.choice([0, 0, 0, 0, 1]),  # ~20% rivalry games
            }

            games.append(game)

        df = pd.DataFrame(games)

        # Save to cache
        cache_file = self.data_dir / "sample_training_data.csv"
        df.to_csv(cache_file, index=False)
        logger.info(f"Saved sample data to {cache_file}")

        logger.info(f"Generated {len(df)} synthetic NCAAF games")
        logger.info(f"  Average total: {df['total'].mean():.1f}")
        logger.info(f"  Home win %: {df['home_win'].mean():.1%}")

        return df

    def prepare_training_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and prepare data for model training

        Returns:
            Clean training-ready DataFrame
        """
        logger.info("Preparing NCAAF training data...")

        # Remove rows with missing target data
        original_len = len(df)
        df = df.dropna(subset=['total', 'home_score', 'away_score'])

        if len(df) < original_len:
            logger.info(f"Removed {original_len - len(df)} rows with missing target data")

        # Fill missing stats with league averages
        df['home_ppg'] = df['home_ppg'].fillna(28.0)
        df['away_ppg'] = df['away_ppg'].fillna(28.0)
        df['home_points_allowed_per_game'] = df['home_points_allowed_per_game'].fillna(28.0)
        df['away_points_allowed_per_game'] = df['away_points_allowed_per_game'].fillna(28.0)
        df['home_yards_per_play'] = df['home_yards_per_play'].fillna(5.8)
        df['away_yards_per_play'] = df['away_yards_per_play'].fillna(5.8)
        df['home_talent_composite'] = df['home_talent_composite'].fillna(0.5)
        df['away_talent_composite'] = df['away_talent_composite'].fillna(0.5)

        # Ensure target variables exist
        if 'home_margin' not in df.columns:
            df['home_margin'] = df['home_score'] - df['away_score']
        if 'home_win' not in df.columns:
            df['home_win'] = (df['home_margin'] > 0).astype(int)

        logger.info(f"Training dataset prepared: {len(df)} games")

        return df

    def load_historical_data(self, seasons: List[str] = None) -> pd.DataFrame:
        """
        Load and prepare historical NCAAF data

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
                df = self.generate_sample_ncaaf_data(n_games=1500)

        # Filter to specific seasons if requested
        if seasons and 'season' in df.columns:
            seasons_int = [int(s) for s in seasons]
            df = df[df['season'].isin(seasons_int)]
            logger.info(f"Filtered to {len(df)} games from seasons: {seasons}")

        # Prepare for training
        df = self.prepare_training_data(df)

        return df


def load_ncaaf_training_data(seasons: List[str] = None) -> pd.DataFrame:
    """
    Convenience function to load NCAAF training data

    Args:
        seasons: List of season strings. If None, uses available data.

    Returns:
        Training-ready DataFrame
    """
    if seasons is None:
        # Default to recent seasons
        seasons = ["2023", "2024"]

    loader = NCAAFDataLoader()
    training_df = loader.load_historical_data(seasons)

    if training_df.empty:
        logger.error("No NCAAF training data available")
        return pd.DataFrame()

    logger.info(f"Loaded {len(training_df)} NCAAF games for training")

    return training_df
