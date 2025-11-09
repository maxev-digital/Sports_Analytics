"""
NCAAB Historical Data Loader

Fetches historical NCAAB game data for model training:
- KenPom efficiency ratings (AdjOE, AdjDE, AdjEM, AdjTempo)
- Team statistics (conference strength, records)
- Historical game results

Data Sources:
1. KenPom CSV files in backend/data/raw/ncaab/
2. Sports-Reference for game results (optional)
3. Synthetic game generation based on efficiency ratings
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class NCAABDataLoader:
    """Load and preprocess historical NCAAB data for model training"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data" / "raw" / "ncaab"
        self.historical_dir = Path(__file__).parent.parent.parent / "data" / "historical" / "ncaab"
        self.historical_dir.mkdir(parents=True, exist_ok=True)

    def load_kenpom_season(self, season: str) -> pd.DataFrame:
        """
        Load KenPom data for a specific season

        Args:
            season: Season year like "2023", "2024", "2025"

        Returns:
            DataFrame with KenPom ratings
        """
        logger.info(f"Loading KenPom data for {season} season...")

        # Find most recent KenPom file for this season
        pattern = f"kenpom_{season}_*.csv"
        files = list(self.data_dir.glob(pattern))

        if not files:
            logger.warning(f"No KenPom data found for {season}")
            return pd.DataFrame()

        # Use most recent file
        kenpom_file = sorted(files)[-1]
        logger.info(f"Loading from {kenpom_file}")

        df = pd.read_csv(kenpom_file)

        # Clean team names (remove rankings)
        df['Team'] = df['Team'].str.replace(r'\s+\d+$', '', regex=True).str.strip()

        # Normalize team names for matching
        df['team_normalized'] = df['Team'].str.lower().str.replace(' ', '_')

        # Add season column
        df['season'] = season

        logger.info(f"Loaded {len(df)} teams for {season} season")

        return df

    def generate_synthetic_games(self, kenpom_df: pd.DataFrame, n_games_per_team: int = 30) -> pd.DataFrame:
        """
        Generate synthetic game results based on KenPom efficiency ratings

        Uses adjusted efficiency metrics to simulate realistic game outcomes
        with appropriate variance for college basketball.

        Args:
            kenpom_df: DataFrame with KenPom ratings
            n_games_per_team: Average games per team to generate

        Returns:
            DataFrame with synthetic game results
        """
        logger.info(f"Generating synthetic games for {len(kenpom_df)} teams...")

        games = []
        teams = kenpom_df.to_dict('records')
        n_teams = len(teams)

        # Calculate total games
        total_games = (n_teams * n_games_per_team) // 2

        for game_idx in range(total_games):
            # Random matchup
            home_idx = np.random.randint(0, n_teams)
            away_idx = np.random.randint(0, n_teams)

            while away_idx == home_idx:
                away_idx = np.random.randint(0, n_teams)

            home_team = teams[home_idx]
            away_team = teams[away_idx]

            # Calculate expected performance based on KenPom metrics
            # Home court advantage in college: ~3.5 points
            home_advantage = 3.5

            # Expected possessions (use geometric mean of tempos)
            home_tempo = home_team.get('AdjTempo', 68.0)
            away_tempo = away_team.get('AdjTempo', 68.0)
            expected_possessions = np.sqrt(home_tempo * away_tempo)

            # Expected points per possession
            home_off_eff = home_team.get('AdjOffEff', 105.0)
            away_def_eff = away_team.get('AdjDefEff', 100.0)
            home_expected_ppp = (home_off_eff + (100 - away_def_eff)) / 100.0 * 1.05  # Normalize + HCA

            away_off_eff = away_team.get('AdjOffEff', 105.0)
            home_def_eff = home_team.get('AdjDefEff', 100.0)
            away_expected_ppp = (away_off_eff + (100 - home_def_eff)) / 100.0

            # Expected points
            home_expected = home_expected_ppp * expected_possessions
            away_expected = away_expected_ppp * expected_possessions

            # Add variance (college has higher variance than NBA)
            home_score = max(40, int(np.random.normal(home_expected, 10)))
            away_score = max(40, int(np.random.normal(away_expected, 10)))

            # Create game record
            game = {
                'game_id': f"NCAAB_{home_team['season']}_{game_idx:04d}",
                'date': f"{home_team['season']}-11-{15 + (game_idx % 120) // 4:02d}",
                'season': home_team['season'],
                'home_team': home_team['team_normalized'],
                'away_team': away_team['team_normalized'],
                'home_score': home_score,
                'away_score': away_score,
                'total': home_score + away_score,
                'home_margin': home_score - away_score,
                'home_win': 1 if home_score > away_score else 0
            }

            games.append(game)

        df = pd.DataFrame(games)
        logger.info(f"Generated {len(df)} synthetic games")

        return df

    def load_historical_data(self, seasons: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load historical data for multiple seasons

        Args:
            seasons: List of season strings like ["2023", "2024", "2025"]

        Returns:
            Tuple of (games_df, kenpom_stats_df)
        """
        all_kenpom = []
        all_games = []

        for season in seasons:
            kenpom = self.load_kenpom_season(season)

            if kenpom.empty:
                logger.warning(f"Skipping {season} - no KenPom data")
                continue

            # Check for cached games
            cache_file = self.historical_dir / f"games_{season}.csv"
            if cache_file.exists():
                logger.info(f"Loading cached games from {cache_file}")
                games = pd.read_csv(cache_file)
            else:
                # Generate synthetic games
                games = self.generate_synthetic_games(kenpom)
                games.to_csv(cache_file, index=False)
                logger.info(f"Saved {len(games)} games to {cache_file}")

            all_kenpom.append(kenpom)
            all_games.append(games)

        kenpom_df = pd.concat(all_kenpom, ignore_index=True) if all_kenpom else pd.DataFrame()
        games_df = pd.concat(all_games, ignore_index=True) if all_games else pd.DataFrame()

        logger.info(f"Loaded {len(games_df)} total games across {len(seasons)} seasons")
        logger.info(f"Loaded KenPom data for {len(kenpom_df)} team-seasons")

        return games_df, kenpom_df

    def prepare_training_data(self, games_df: pd.DataFrame, kenpom_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge games with KenPom stats to create training dataset

        Returns:
            DataFrame ready for model training with features and targets
        """
        logger.info("Preparing NCAAB training data...")

        training_data = []

        for _, game in games_df.iterrows():
            season = game['season']
            home_team = game['home_team']
            away_team = game['away_team']

            # Get KenPom stats for both teams
            home_stats = kenpom_df[
                (kenpom_df['season'] == season) &
                (kenpom_df['team_normalized'] == home_team)
            ]
            away_stats = kenpom_df[
                (kenpom_df['season'] == season) &
                (kenpom_df['team_normalized'] == away_team)
            ]

            if home_stats.empty or away_stats.empty:
                continue

            home_stats = home_stats.iloc[0]
            away_stats = away_stats.iloc[0]

            # Create feature row
            row = {
                'game_id': game['game_id'],
                'date': game['date'],
                'season': season,

                # Home team KenPom stats
                'home_team': home_team,
                'home_adj_em': home_stats.get('AdjEM', 0.0),
                'home_adj_off_eff': home_stats.get('AdjOffEff', 105.0),
                'home_adj_def_eff': home_stats.get('AdjDefEff', 100.0),
                'home_adj_tempo': home_stats.get('AdjTempo', 68.0),
                'home_rank': home_stats.get('Rank', 150),
                'home_conference': home_stats.get('Conference', 'Unknown'),

                # Away team KenPom stats
                'away_team': away_team,
                'away_adj_em': away_stats.get('AdjEM', 0.0),
                'away_adj_off_eff': away_stats.get('AdjOffEff', 105.0),
                'away_adj_def_eff': away_stats.get('AdjDefEff', 100.0),
                'away_adj_tempo': away_stats.get('AdjTempo', 68.0),
                'away_rank': away_stats.get('Rank', 150),
                'away_conference': away_stats.get('Conference', 'Unknown'),

                # Target variables
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'total': game['total'],
                'home_margin': game['home_margin'],
                'home_win': game['home_win']
            }

            training_data.append(row)

        df = pd.DataFrame(training_data)
        logger.info(f"Created training dataset with {len(df)} games")

        return df


def load_ncaab_training_data(seasons: List[str] = None) -> pd.DataFrame:
    """
    Convenience function to load NCAAB training data

    Args:
        seasons: List of seasons to load. Defaults to last 3 seasons.

    Returns:
        Training-ready DataFrame
    """
    if seasons is None:
        # Default to available seasons
        seasons = ["2023", "2024", "2025"]

    loader = NCAABDataLoader()
    games_df, kenpom_df = loader.load_historical_data(seasons)

    if games_df.empty or kenpom_df.empty:
        logger.error("No NCAAB data available")
        return pd.DataFrame()

    training_df = loader.prepare_training_data(games_df, kenpom_df)

    return training_df
