"""
NFL Feature Engineering

Converts raw NFL game data and team statistics into feature matrices
for machine learning models.

NFL-specific considerations:
- Key numbers: 3, 7, 10 points (field goal, touchdown, TD+FG)
- Home field advantage: ~2.5 points
- Weather impact (outdoor stadiums)
- Rest days (Thursday games, bye weeks)
- Turnover differential critical

Feature counts by model type:
- Totals: 20 features (scoring, yards, pace, turnovers)
- Spreads: 20 features (same as totals)
- Moneyline: 20 features (same as totals)
"""

import numpy as np
import pandas as pd
from typing import List


class NFLFeatureEngineer:
    """Feature engineering for NFL prediction models"""

    # League averages for normalization
    LEAGUE_AVG_PPG = 22.0
    LEAGUE_AVG_YPP = 5.5
    LEAGUE_AVG_THIRD_DOWN = 40.0
    HOME_FIELD_ADVANTAGE = 2.5

    @staticmethod
    def get_totals_features(row: pd.Series) -> np.ndarray:
        """
        Extract 20 features for totals prediction

        Features:
        - Offensive production (6)
        - Defensive efficiency (6)
        - Scoring pace (3)
        - Turnovers (2)
        - Game situation (3)
        """
        features = np.zeros(20)

        # Offensive production [0-5]
        features[0] = row.get('home_ppg', NFLFeatureEngineer.LEAGUE_AVG_PPG)
        features[1] = row.get('away_ppg', NFLFeatureEngineer.LEAGUE_AVG_PPG)
        features[2] = row.get('home_yards_per_play', NFLFeatureEngineer.LEAGUE_AVG_YPP)
        features[3] = row.get('away_yards_per_play', NFLFeatureEngineer.LEAGUE_AVG_YPP)
        features[4] = row.get('home_third_down_pct', NFLFeatureEngineer.LEAGUE_AVG_THIRD_DOWN)
        features[5] = row.get('away_third_down_pct', NFLFeatureEngineer.LEAGUE_AVG_THIRD_DOWN)

        # Defensive efficiency [6-11]
        features[6] = row.get('home_points_allowed_per_game', NFLFeatureEngineer.LEAGUE_AVG_PPG)
        features[7] = row.get('away_points_allowed_per_game', NFLFeatureEngineer.LEAGUE_AVG_PPG)
        features[8] = row.get('home_yards_per_play_allowed', NFLFeatureEngineer.LEAGUE_AVG_YPP)
        features[9] = row.get('away_yards_per_play_allowed', NFLFeatureEngineer.LEAGUE_AVG_YPP)
        features[10] = row.get('home_third_down_pct_defense', NFLFeatureEngineer.LEAGUE_AVG_THIRD_DOWN)
        features[11] = row.get('away_third_down_pct_defense', NFLFeatureEngineer.LEAGUE_AVG_THIRD_DOWN)

        # Scoring pace [12-14]
        features[12] = features[0] + features[1]  # Combined PPG
        features[13] = (features[0] + features[7]) / 2  # Expected home scoring (off vs def)
        features[14] = (features[1] + features[6]) / 2  # Expected away scoring

        # Turnovers [15-16]
        features[15] = row.get('home_turnover_margin', 0.0)
        features[16] = row.get('away_turnover_margin', 0.0)

        # Game situation [17-19]
        features[17] = row.get('is_division_game', 0)  # Division games tend lower scoring
        features[18] = row.get('is_primetime', 0)  # Primetime games can be different
        features[19] = 1.0  # Home field indicator

        return features.reshape(1, -1)

    @staticmethod
    def get_spreads_features(row: pd.Series) -> np.ndarray:
        """
        Extract 20 features for spreads prediction
        
        Spreads models are trained on same features as totals
        """
        # Just use totals features (20 features)
        features = NFLFeatureEngineer.get_totals_features(row).flatten()
        return features.reshape(1, -1)

    @staticmethod
    def get_moneyline_features(row: pd.Series) -> np.ndarray:
        """
        Extract 20 features for moneyline prediction
        
        Moneyline models are trained on same features as totals
        """
        # Just use totals features (20 features)
        features = NFLFeatureEngineer.get_totals_features(row).flatten()
        return features.reshape(1, -1)

    def create_feature_matrix(self, df: pd.DataFrame, model_type: str) -> np.ndarray:
        """
        Create feature matrix for a dataset

        Args:
            df: DataFrame with game data
            model_type: 'totals', 'spreads', or 'moneyline'

        Returns:
            Numpy array of shape (n_games, n_features)
        """
        if model_type == 'totals':
            feature_func = self.get_totals_features
        elif model_type == 'spreads':
            feature_func = self.get_spreads_features
        elif model_type == 'moneyline':
            feature_func = self.get_moneyline_features
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        n_features = 20  # All bet types use 20 features

        features = np.zeros((len(df), n_features))

        for i, (_, row) in enumerate(df.iterrows()):
            features[i] = feature_func(row).flatten()

        return features

    def get_feature_names(self, model_type: str) -> List[str]:
        """
        Get feature names for a model type

        Args:
            model_type: 'totals', 'spreads', or 'moneyline'

        Returns:
            List of feature names
        """
        # All model types use same features
        return [
            # Offensive [0-5]
            'home_ppg', 'away_ppg', 'home_yards_per_play', 'away_yards_per_play',
            'home_third_down_pct', 'away_third_down_pct',
            # Defensive [6-11]
            'home_points_allowed', 'away_points_allowed',
            'home_yards_per_play_allowed', 'away_yards_per_play_allowed',
            'home_third_down_pct_defense', 'away_third_down_pct_defense',
            # Scoring pace [12-14]
            'combined_ppg', 'expected_home_scoring', 'expected_away_scoring',
            # Turnovers [15-16]
            'home_turnover_margin', 'away_turnover_margin',
            # Game situation [17-19]
            'is_division_game', 'is_primetime', 'home_field_indicator'
        ]
