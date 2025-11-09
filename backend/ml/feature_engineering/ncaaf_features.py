"""
NCAAF (College Football) Feature Engineering

Converts raw NCAAF game data and team statistics into feature matrices
for machine learning models.

NCAAF-specific considerations:
- Larger talent gaps than NFL (Alabama vs FCS teams)
- Conference strength critical (SEC, Big 10, Big 12 vs smaller)
- Home field advantage larger (~3.5-4.0 points vs NFL's 2.5)
- More variance in styles (triple option, air raid, etc.)
- Recruiting rankings indicate future performance

Feature counts by model type:
- Totals: 24 features (scoring, pace, conference, talent)
- Spreads: 29 features (differentials, home advantage, recruiting)
- Moneyline: 33 features (all stats, win probability, upset potential)
"""

import numpy as np
import pandas as pd
from typing import List


class NCAAFFeatureEngineer:
    """Feature engineering for NCAAF prediction models"""

    # League averages for normalization
    LEAGUE_AVG_PPG = 28.0  # College football is higher scoring
    LEAGUE_AVG_YPP = 5.8
    LEAGUE_AVG_THIRD_DOWN = 40.0
    HOME_FIELD_ADVANTAGE = 3.5  # Larger than NFL

    # Power 5 conferences
    POWER_5 = ['SEC', 'B10', 'B12', 'ACC', 'P12']

    @staticmethod
    def get_totals_features(row: pd.Series) -> np.ndarray:
        """
        Extract 24 features for totals prediction

        Features:
        - Offensive production (6)
        - Defensive efficiency (6)
        - Scoring pace (3)
        - Turnovers (2)
        - Conference strength (3)
        - Game situation (2)
        - Tempo indicators (2)
        """
        features = np.zeros(24)

        # Offensive production [0-5]
        features[0] = row.get('home_ppg', NCAAFFeatureEngineer.LEAGUE_AVG_PPG)
        features[1] = row.get('away_ppg', NCAAFFeatureEngineer.LEAGUE_AVG_PPG)
        features[2] = row.get('home_yards_per_play', NCAAFFeatureEngineer.LEAGUE_AVG_YPP)
        features[3] = row.get('away_yards_per_play', NCAAFFeatureEngineer.LEAGUE_AVG_YPP)
        features[4] = row.get('home_third_down_pct', NCAAFFeatureEngineer.LEAGUE_AVG_THIRD_DOWN)
        features[5] = row.get('away_third_down_pct', NCAAFFeatureEngineer.LEAGUE_AVG_THIRD_DOWN)

        # Defensive efficiency [6-11]
        features[6] = row.get('home_points_allowed_per_game', NCAAFFeatureEngineer.LEAGUE_AVG_PPG)
        features[7] = row.get('away_points_allowed_per_game', NCAAFFeatureEngineer.LEAGUE_AVG_PPG)
        features[8] = row.get('home_yards_per_play_allowed', NCAAFFeatureEngineer.LEAGUE_AVG_YPP)
        features[9] = row.get('away_yards_per_play_allowed', NCAAFFeatureEngineer.LEAGUE_AVG_YPP)
        features[10] = row.get('home_third_down_pct_defense', NCAAFFeatureEngineer.LEAGUE_AVG_THIRD_DOWN)
        features[11] = row.get('away_third_down_pct_defense', NCAAFFeatureEngineer.LEAGUE_AVG_THIRD_DOWN)

        # Scoring pace [12-14]
        features[12] = features[0] + features[1]  # Combined PPG
        features[13] = (features[0] + features[7]) / 2  # Expected home scoring
        features[14] = (features[1] + features[6]) / 2  # Expected away scoring

        # Turnovers [15-16]
        features[15] = row.get('home_turnover_margin', 0.0)
        features[16] = row.get('away_turnover_margin', 0.0)

        # Conference strength [17-19]
        home_conf = row.get('home_conference', 'Other')
        away_conf = row.get('away_conference', 'Other')
        features[17] = 1 if home_conf in NCAAFFeatureEngineer.POWER_5 else 0
        features[18] = 1 if away_conf in NCAAFFeatureEngineer.POWER_5 else 0
        features[19] = features[17] + features[18]  # Total Power 5 teams

        # Game situation [20-21]
        features[20] = row.get('is_rivalry_game', 0)  # Rivalry games different
        features[21] = row.get('is_conference_game', 0)  # Conference games more competitive

        # Tempo indicators [22-23] (college has more variance in pace)
        features[22] = row.get('home_plays_per_game', 70.0) / 80.0  # Normalized
        features[23] = row.get('away_plays_per_game', 70.0) / 80.0

        return features.reshape(1, -1)

    @staticmethod
    def get_spreads_features(row: pd.Series) -> np.ndarray:
        """
        Extract 29 features for spreads prediction

        Additional features beyond totals:
        - Power rating differentials (2)
        - Home field advantage (1)
        - Talent gap indicators (2)
        """
        features = np.zeros(29)

        # Start with totals features (first 24)
        totals_features = NCAAFFeatureEngineer.get_totals_features(row).flatten()
        features[:24] = totals_features

        # Spreads-specific features [24-28]
        # Power rating differential
        home_ppg = row.get('home_ppg', NCAAFFeatureEngineer.LEAGUE_AVG_PPG)
        away_ppg = row.get('away_ppg', NCAAFFeatureEngineer.LEAGUE_AVG_PPG)
        home_pa = row.get('home_points_allowed_per_game', NCAAFFeatureEngineer.LEAGUE_AVG_PPG)
        away_pa = row.get('away_points_allowed_per_game', NCAAFFeatureEngineer.LEAGUE_AVG_PPG)

        features[24] = home_ppg - away_ppg  # Offensive differential
        features[25] = away_pa - home_pa  # Defensive differential (lower PA is better)

        # Home field advantage (larger in college)
        features[26] = 1.0  # Binary home indicator

        # Talent gap indicators (recruiting rankings if available)
        home_talent = row.get('home_talent_composite', 0.5)  # 0-1 scale
        away_talent = row.get('away_talent_composite', 0.5)
        features[27] = home_talent - away_talent  # Talent differential

        # Conference mismatch (Power 5 vs Group of 5)
        is_mismatch = (features[17] == 1 and features[18] == 0) or (features[17] == 0 and features[18] == 1)
        features[28] = 1 if is_mismatch else 0

        return features.reshape(1, -1)

    @staticmethod
    def get_moneyline_features(row: pd.Series) -> np.ndarray:
        """
        Extract 33 features for moneyline prediction

        Additional features beyond spreads:
        - Win rates (2)
        - Recent form (2)
        """
        features = np.zeros(33)

        # Start with spreads features (first 29)
        spreads_features = NCAAFFeatureEngineer.get_spreads_features(row).flatten()
        features[:29] = spreads_features

        # Moneyline-specific features [29-32]
        # Win rates
        features[29] = row.get('home_win_pct', 0.5)
        features[30] = row.get('away_win_pct', 0.5)

        # Recent form (last 3 games in college is meaningful due to weekly schedule)
        features[31] = row.get('home_last_3_win_pct', 0.5)
        features[32] = row.get('away_last_3_win_pct', 0.5)

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
            n_features = 24
        elif model_type == 'spreads':
            feature_func = self.get_spreads_features
            n_features = 29
        elif model_type == 'moneyline':
            feature_func = self.get_moneyline_features
            n_features = 33
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
            # Conference [17-19]
            'home_is_power5', 'away_is_power5', 'total_power5_teams',
            # Game situation [20-21]
            'is_rivalry_game', 'is_conference_game',
            # Tempo [22-23]
            'home_plays_per_game_norm', 'away_plays_per_game_norm'
        ]

        spreads_names = totals_names + [
            # Power ratings [24-25]
            'offensive_differential', 'defensive_differential',
            # Home advantage [26]
            'home_field_indicator',
            # Talent [27-28]
            'talent_differential', 'conference_mismatch'
        ]

        moneyline_names = spreads_names + [
            # Win rates [29-30]
            'home_win_pct', 'away_win_pct',
            # Recent form [31-32]
            'home_last_3_win_pct', 'away_last_3_win_pct'
        ]

        if model_type == 'totals':
            return totals_names
        elif model_type == 'spreads':
            return spreads_names
        elif model_type == 'moneyline':
            return moneyline_names
        else:
            raise ValueError(f"Unknown model type: {model_type}")
