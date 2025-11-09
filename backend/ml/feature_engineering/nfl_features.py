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
- Totals: 21 features (scoring, yards, pace, turnovers)
- Spreads: 25 features (differentials, home advantage, key numbers)
- Moneyline: 29 features (all stats, win probability indicators)
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
        Extract 21 features for totals prediction

        Features:
        - Offensive production (6)
        - Defensive efficiency (6)
        - Scoring pace (3)
        - Turnovers (2)
        - Game situation (2)
        - Weather (2)
        """
        features = np.zeros(21)

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

        # Game situation [17-18]
        features[17] = row.get('is_division_game', 0)  # Division games tend lower scoring
        features[18] = row.get('is_primetime', 0)  # Primetime games can be different

        # Weather [19-20] (if available)
        features[19] = row.get('temperature', 70.0) / 100.0  # Normalize 0-100
        features[20] = row.get('wind_speed', 5.0) / 30.0  # Normalize 0-30 mph

        return features.reshape(1, -1)

    @staticmethod
    def get_spreads_features(row: pd.Series) -> np.ndarray:
        """
        Extract 25 features for spreads prediction

        Additional features beyond totals:
        - Power rating differentials (2)
        - Home field advantage (1)
        - Rest advantage (1)
        """
        features = np.zeros(25)

        # Start with totals features (first 21)
        totals_features = NFLFeatureEngineer.get_totals_features(row).flatten()
        features[:21] = totals_features

        # Spreads-specific features [21-24]
        # Power rating differential (most important for spreads)
        home_ppg = row.get('home_ppg', NFLFeatureEngineer.LEAGUE_AVG_PPG)
        away_ppg = row.get('away_ppg', NFLFeatureEngineer.LEAGUE_AVG_PPG)
        home_pa = row.get('home_points_allowed_per_game', NFLFeatureEngineer.LEAGUE_AVG_PPG)
        away_pa = row.get('away_points_allowed_per_game', NFLFeatureEngineer.LEAGUE_AVG_PPG)

        features[21] = home_ppg - away_ppg  # Offensive differential
        features[22] = away_pa - home_pa  # Defensive differential (lower PA is better)

        # Home field advantage
        features[23] = 1.0  # Binary home indicator

        # Rest advantage
        home_rest = row.get('home_rest_days', 7)
        away_rest = row.get('away_rest_days', 7)
        features[24] = (home_rest - away_rest) / 7.0  # Normalized rest differential

        return features.reshape(1, -1)

    @staticmethod
    def get_moneyline_features(row: pd.Series) -> np.ndarray:
        """
        Extract 29 features for moneyline prediction

        Additional features beyond spreads:
        - Win rates (2)
        - Recent form (2)
        """
        features = np.zeros(29)

        # Start with spreads features (first 25)
        spreads_features = NFLFeatureEngineer.get_spreads_features(row).flatten()
        features[:25] = spreads_features

        # Moneyline-specific features [25-28]
        # Win rates
        features[25] = row.get('home_win_pct', 0.5)
        features[26] = row.get('away_win_pct', 0.5)

        # Recent form (last 4 games in NFL is meaningful)
        features[27] = row.get('home_last_4_win_pct', 0.5)
        features[28] = row.get('away_last_4_win_pct', 0.5)

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
            n_features = 21
        elif model_type == 'spreads':
            feature_func = self.get_spreads_features
            n_features = 25
        elif model_type == 'moneyline':
            feature_func = self.get_moneyline_features
            n_features = 29
        else:
            raise ValueError(f"Unknown model type: {model_type}")

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
        totals_names = [
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
            # Game situation [17-18]
            'is_division_game', 'is_primetime',
            # Weather [19-20]
            'temperature_normalized', 'wind_speed_normalized'
        ]

        spreads_names = totals_names + [
            # Power ratings [21-22]
            'offensive_differential', 'defensive_differential',
            # Home advantage [23]
            'home_field_indicator',
            # Rest [24]
            'rest_differential'
        ]

        moneyline_names = spreads_names + [
            # Win rates [25-26]
            'home_win_pct', 'away_win_pct',
            # Recent form [27-28]
            'home_last_4_win_pct', 'away_last_4_win_pct'
        ]

        if model_type == 'totals':
            return totals_names
        elif model_type == 'spreads':
            return spreads_names
        elif model_type == 'moneyline':
            return moneyline_names
        else:
            raise ValueError(f"Unknown model type: {model_type}")
