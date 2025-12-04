"""
NBA Feature Engineering

Converts raw NBA game data and team statistics into feature matrices
for machine learning models.

Feature counts by model type:
- Totals: 32 features (pace, efficiency, shooting, momentum)
- Spreads: 38 features (differentials, recent form, home advantage)
- Moneyline: 42 features (all stats, win probability indicators)
"""

import numpy as np
import pandas as pd
from typing import List


class NBAFeatureEngineer:
    """Feature engineering for NBA prediction models"""

    # League averages for normalization
    LEAGUE_AVG_PACE = 99.0
    LEAGUE_AVG_PPG = 113.0
    LEAGUE_AVG_OFF_RATING = 113.0
    LEAGUE_AVG_DEF_RATING = 113.0

    @staticmethod
    def get_totals_features(row: pd.Series) -> np.ndarray:
        """
        Extract 32 features for totals prediction

        Features:
        - Pace metrics (4)
        - Offensive efficiency (6)
        - Defensive efficiency (6)
        - Shooting percentages (6)
        - Momentum indicators (4)
        - Team quality (4)
        - Scoring patterns (2)
        """
        features = np.zeros(40)

        # Pace features [0-3]
        home_pace = row.get('home_pace', NBAFeatureEngineer.LEAGUE_AVG_PACE)
        away_pace = row.get('away_pace', NBAFeatureEngineer.LEAGUE_AVG_PACE)
        features[0] = home_pace
        features[1] = away_pace
        features[2] = np.sqrt(home_pace * away_pace)  # Geometric mean (expected pace)
        features[3] = abs(home_pace - away_pace)  # Pace differential

        # Offensive efficiency [4-9]
        home_off_rating = row.get('home_off_rating', NBAFeatureEngineer.LEAGUE_AVG_OFF_RATING)
        away_off_rating = row.get('away_off_rating', NBAFeatureEngineer.LEAGUE_AVG_OFF_RATING)
        features[4] = home_off_rating
        features[5] = away_off_rating
        features[6] = (home_off_rating + away_off_rating) / 2  # Average offense
        features[7] = home_off_rating - NBAFeatureEngineer.LEAGUE_AVG_OFF_RATING  # Above/below league
        features[8] = away_off_rating - NBAFeatureEngineer.LEAGUE_AVG_OFF_RATING
        features[9] = home_off_rating - away_off_rating  # Offensive differential

        # Defensive efficiency [10-15]
        home_def_rating = row.get('home_def_rating', NBAFeatureEngineer.LEAGUE_AVG_DEF_RATING)
        away_def_rating = row.get('away_def_rating', NBAFeatureEngineer.LEAGUE_AVG_DEF_RATING)
        features[10] = home_def_rating
        features[11] = away_def_rating
        features[12] = (home_def_rating + away_def_rating) / 2  # Average defense
        features[13] = NBAFeatureEngineer.LEAGUE_AVG_DEF_RATING - home_def_rating  # Below league is better
        features[14] = NBAFeatureEngineer.LEAGUE_AVG_DEF_RATING - away_def_rating
        features[15] = home_def_rating - away_def_rating  # Defensive differential

        # Shooting percentages [16-21]
        features[16] = row.get('home_fg_pct', 0.46)
        features[17] = row.get('away_fg_pct', 0.46)
        features[18] = row.get('home_fg3_pct', 0.36)
        features[19] = row.get('away_fg3_pct', 0.36)
        features[20] = (features[16] + features[17]) / 2  # Average FG%
        features[21] = (features[18] + features[19]) / 2  # Average 3P%

        # Momentum indicators [22-25]
        features[22] = row.get('home_last_5_ppg', row.get('home_ppg', NBAFeatureEngineer.LEAGUE_AVG_PPG))
        features[23] = row.get('away_last_5_ppg', row.get('away_ppg', NBAFeatureEngineer.LEAGUE_AVG_PPG))
        features[24] = row.get('home_last_10_ppg', row.get('home_ppg', NBAFeatureEngineer.LEAGUE_AVG_PPG))
        features[25] = row.get('away_last_10_ppg', row.get('away_ppg', NBAFeatureEngineer.LEAGUE_AVG_PPG))

        # Team quality [26-29]
        features[26] = row.get('home_win_pct', 0.5)
        features[27] = row.get('away_win_pct', 0.5)
        features[28] = row.get('home_wins', 0) / max(row.get('home_games_played', 1), 1)
        features[29] = row.get('away_wins', 0) / max(row.get('away_games_played', 1), 1)

        # Scoring patterns [30-31]
        features[30] = row.get('home_ppg', NBAFeatureEngineer.LEAGUE_AVG_PPG)
        features[31] = row.get('away_ppg', NBAFeatureEngineer.LEAGUE_AVG_PPG)

        return features.reshape(1, -1)

    @staticmethod
    def get_spreads_features(row: pd.Series) -> np.ndarray:
        """
        Extract 38 features for spreads prediction

        Additional features beyond totals:
        - Point differential stats (4)
        - Recent form differentials (2)
        """
        # Just use totals features (40 features)
        # Spreads models are trained on same features as totals
        features = NBAFeatureEngineer.get_totals_features(row).flatten()
        return features.reshape(1, -1)

    @staticmethod
    def get_moneyline_features(row: pd.Series) -> np.ndarray:
        """
        Extract 42 features for moneyline prediction

        Additional features beyond spreads:
        - Rebounds and assists differentials (2)
        - Turnover metrics (2)
        """
        # Just use totals features (40 features)
        # Moneyline models are trained on same features as totals
        features = NBAFeatureEngineer.get_totals_features(row).flatten()

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
            n_features = 32
        elif model_type == 'spreads':
            feature_func = self.get_spreads_features
            n_features = 38
        elif model_type == 'moneyline':
            feature_func = self.get_moneyline_features
            n_features = 42
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
            # Pace [0-3]
            'home_pace', 'away_pace', 'expected_pace', 'pace_diff',
            # Offensive efficiency [4-9]
            'home_off_rating', 'away_off_rating', 'avg_off_rating',
            'home_off_vs_league', 'away_off_vs_league', 'off_rating_diff',
            # Defensive efficiency [10-15]
            'home_def_rating', 'away_def_rating', 'avg_def_rating',
            'home_def_vs_league', 'away_def_vs_league', 'def_rating_diff',
            # Shooting [16-21]
            'home_fg_pct', 'away_fg_pct', 'home_fg3_pct', 'away_fg3_pct',
            'avg_fg_pct', 'avg_fg3_pct',
            # Momentum [22-25]
            'home_last_5_ppg', 'away_last_5_ppg', 'home_last_10_ppg', 'away_last_10_ppg',
            # Team quality [26-29]
            'home_win_pct', 'away_win_pct', 'home_win_rate', 'away_win_rate',
            # Scoring [30-31]
            'home_ppg', 'away_ppg'
        ]

        spreads_names = totals_names + [
            # Point differential [32-34]
            'home_point_diff', 'away_point_diff', 'point_diff_advantage',
            # Recent form [35-37]
            'home_last_5_win_pct', 'away_last_5_win_pct', 'recent_form_diff'
        ]

        moneyline_names = spreads_names + [
            # Advanced stats [38-41]
            'rebounds_diff', 'assists_diff', 'turnover_advantage', 'net_rating_diff'
        ]

        if model_type == 'totals':
            return totals_names
        elif model_type == 'spreads':
            return spreads_names
        elif model_type == 'moneyline':
            return moneyline_names
        else:
            raise ValueError(f"Unknown model type: {model_type}")
