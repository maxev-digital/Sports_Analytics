"""
NCAAB Historical Data Loader - FIXED

Loads REAL historical NCAAB game data and enriches with KenPom ratings
"""

import pandas as pd
import numpy as np
import logging
from typing import List
from pathlib import Path

logger = logging.getLogger(__name__)


class NCAABDataLoader:
    """Load and preprocess historical NCAAB data for model training"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data" / "raw" / "ncaab"
        self.historical_dir = Path(__file__).parent.parent.parent / "data" / "historical" / "ncaab"

    def load_historical_games(self, seasons: List[str] = None) -> pd.DataFrame:
        """
        Load real historical NCAAB games
        
        Args:
            seasons: List of seasons like ["2023", "2024", "2025"]
                    If None, loads all available seasons
        
        Returns:
            DataFrame with historical games
        """
        if seasons is None:
            seasons = ["2023", "2024", "2025"]
        
        all_games = []
        
        for season in seasons:
            game_file = self.historical_dir / f"games_{season}.csv"
            if game_file.exists():
                logger.info(f"Loading NCAAB games from {game_file}")
                df = pd.read_csv(game_file)
                all_games.append(df)
                logger.info(f"  Loaded {len(df)} games from {season} season")
            else:
                logger.warning(f"No game data found for {season} season")
        
        if not all_games:
            logger.error("No NCAAB historical game data found")
            return pd.DataFrame()
        
        # Combine all seasons
        combined = pd.concat(all_games, ignore_index=True)
        logger.info(f"Total NCAAB games loaded: {len(combined)}")
        
        return combined

    def load_kenpom_ratings(self, season: str) -> pd.DataFrame:
        """
        Load KenPom efficiency ratings for a season
        
        Args:
            season: Season year like "2023", "2024", "2025"
        
        Returns:
            DataFrame with KenPom ratings
        """
        # Find most recent KenPom file for this season
        pattern = f"kenpom_{season}_*.csv"
        files = list(self.data_dir.glob(pattern))
        
        if not files:
            logger.warning(f"No KenPom data found for {season}")
            return pd.DataFrame()
        
        # Use most recent file
        kenpom_file = sorted(files)[-1]
        df = pd.read_csv(kenpom_file)
        
        # Normalize team names for matching
        if 'Team' in df.columns:
            df['team_normalized'] = df['Team'].str.lower().str.replace(' ', '_').str.replace(r'\d+', '', regex=True).str.strip('_')
        
        return df

    def enrich_with_kenpom(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich game data with KenPom efficiency ratings
        
        Args:
            games_df: DataFrame with game results
        
        Returns:
            DataFrame with added KenPom metrics
        """
        enriched = games_df.copy()
        
        # Get unique seasons
        seasons = enriched['season'].unique() if 'season' in enriched.columns else []
        
        for season in seasons:
            kenpom_df = self.load_kenpom_ratings(str(season))
            
            if kenpom_df.empty:
                continue
            
            # Create mapping dict from KenPom
            if 'AdjOE' in kenpom_df.columns:
                season_mask = enriched['season'] == season
                
                # Merge home team stats
                for col in ['AdjOE', 'AdjDE', 'AdjTempo']:
                    if col in kenpom_df.columns:
                        mapping = dict(zip(kenpom_df['team_normalized'], kenpom_df[col]))
                        enriched.loc[season_mask, f'home_{col.lower()}'] = enriched.loc[season_mask, 'home_team'].map(mapping)
                        enriched.loc[season_mask, f'away_{col.lower()}'] = enriched.loc[season_mask, 'away_team'].map(mapping)
        
        # Fill missing KenPom data with league averages
        league_avg_adjoe = 105.0
        league_avg_adjde = 105.0
        league_avg_tempo = 68.0
        
        for prefix in ['home', 'away']:
            if f'{prefix}_adjoe' not in enriched.columns:
                enriched[f'{prefix}_adjoe'] = league_avg_adjoe
            else:
                enriched[f'{prefix}_adjoe'] = enriched[f'{prefix}_adjoe'].fillna(league_avg_adjoe)
            
            if f'{prefix}_adjde' not in enriched.columns:
                enriched[f'{prefix}_adjde'] = league_avg_adjde
            else:
                enriched[f'{prefix}_adjde'] = enriched[f'{prefix}_adjde'].fillna(league_avg_adjde)
            
            if f'{prefix}_adjtempo' not in enriched.columns:
                enriched[f'{prefix}_adjtempo'] = league_avg_tempo
            else:
                enriched[f'{prefix}_adjtempo'] = enriched[f'{prefix}_adjtempo'].fillna(league_avg_tempo)
        
        return enriched

    def prepare_training_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for model training
        
        - Add derived features
        - Calculate expected totals
        - Create target variables
        
        Returns:
            Training-ready DataFrame
        """
        df = df.copy()
        
        # Ensure target variable exists
        if 'total' not in df.columns and 'home_score' in df.columns and 'away_score' in df.columns:
            df['total'] = df['home_score'] + df['away_score']
        
        df['actual_total'] = df['total']
        
        # Calculate efficiency differentials
        if 'home_adjoe' in df.columns:
            df['adjoe_diff'] = df['home_adjoe'] - df['away_adjoe']
            df['adjde_diff'] = df['home_adjde'] - df['away_adjde']
            df['tempo_avg'] = (df['home_adjtempo'] + df['away_adjtempo']) / 2
        
        # Remove rows with missing targets
        df = df.dropna(subset=['actual_total'])
        
        logger.info(f"Prepared {len(df)} NCAAB games for training")
        
        return df


def load_ncaab_training_data(seasons: List[str] = None) -> pd.DataFrame:
    """
    Main function to load NCAAB training data
    
    Args:
        seasons: List of seasons to load (default: ["2023", "2024", "2025"])
    
    Returns:
        DataFrame ready for model training
    """
    loader = NCAABDataLoader()
    
    # Load historical games
    games_df = loader.load_historical_games(seasons)
    
    if games_df.empty:
        logger.error("Failed to load NCAAB historical games")
        return pd.DataFrame()
    
    # Enrich with KenPom ratings
    enriched_df = loader.enrich_with_kenpom(games_df)
    
    # Prepare for training
    training_df = loader.prepare_training_data(enriched_df)
    
    return training_df
