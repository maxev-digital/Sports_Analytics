"""
NCAAB Feature Engineering

Converts raw NCAAB game data and KenPom statistics into feature matrices
for machine learning models.

Feature counts by model type:
- Totals: 25 features (tempo, efficiency, conference strength)
- Spreads: 27 features (differentials, rankings, home court)
- Moneyline: 34 features (all stats, win rates, assist ratios)
"""

import numpy as np
import pandas as pd
from typing import List


class NCAABFeatureEngineer:
    """Feature engineering for NCAAB prediction models"""

    # Conference strength tiers (for encoding)
    POWER_CONFERENCES = ['ACC', 'B12', 'B10', 'SEC', 'BE', 'P12']

    @staticmethod
    def get_totals_features(row: pd.Series) -> np.ndarray:
        """
        Extract 25 features for totals prediction

        Features:
        - Combined tempo metrics (4)
        - Offensive efficiency (4)
        - Defensive efficiency (4)
        - Efficiency margins (3)
        - Pace differentials (2)
        - Conference strength (4)
        - Team quality indicators (4)
        """
        features = np.zeros(25)

        # Tempo features [0-3]
        features[0] = row.get('home_adj_tempo', 68.0)
        features[1] = row.get('away_adj_tempo', 68.0)
        features[2] = np.sqrt(features[0] * features[1])  # Geometric mean
        features[3] = abs(features[0] - features[1])  # Tempo differential

        # Offensive efficiency [4-7]
        features[4] = row.get('home_adj_off_eff', 105.0)
        features[5] = row.get('away_adj_off_eff', 105.0)
        features[6] = (features[4] + features[5]) / 2  # Average offense
        features[7] = features[4] - features[5]  # Offensive differential

        # Defensive efficiency [8-11]
        features[8] = row.get('home_adj_def_eff', 100.0)
        features[9] = row.get('away_adj_def_eff', 100.0)
        features[10] = (features[8] + features[9]) / 2  # Average defense
        features[11] = features[8] - features[9]  # Defensive differential (lower is better)

        # Efficiency margins [12-14]
        features[12] = row.get('home_adj_em', 0.0)
        features[13] = row.get('away_adj_em', 0.0)
        features[14] = features[12] - features[13]  # EM differential

        # Pace indicators [15-16]
        features[15] = 1 if features[2] > 70 else 0  # Fast-paced game
        features[16] = 1 if features[2] < 65 else 0  # Slow-paced game

        # Conference strength [17-20]
        home_conf = row.get('home_conference', 'Unknown')
        away_conf = row.get('away_conference', 'Unknown')
        features[17] = 1 if home_conf in NCAABFeatureEngineer.POWER_CONFERENCES else 0
        features[18] = 1 if away_conf in NCAABFeatureEngineer.POWER_CONFERENCES else 0
        features[19] = 1 if home_conf == away_conf else 0  # Conference game
        features[20] = features[17] + features[18]  # Total power conference teams

        # Team quality [21-24]
        home_rank = row.get('home_rank', 150)
        away_rank = row.get('away_rank', 150)
        features[21] = 1 / (home_rank + 1)  # Inverse rank (higher is better)
        features[22] = 1 / (away_rank + 1)
        features[23] = abs(home_rank - away_rank)  # Rank differential
        features[24] = 1 if min(home_rank, away_rank) <= 25 else 0  # Top 25 team present

        return features.reshape(1, -1)

    @staticmethod
    def get_spreads_features(row: pd.Series) -> np.ndarray:
        """
        Extract 27 features for spreads prediction

        Additional features beyond totals:
        - Home court advantage indicators
        - Ranking differentials
        - Net efficiency ratings
        """
        features = np.zeros(27)

        # Start with totals features (first 25)
        totals_features = NCAABFeatureEngineer.get_totals_features(row).flatten()
        features[:25] = totals_features

        # Spreads-specific features [25-26]
        home_rank = row.get('home_rank', 150)
        away_rank = row.get('away_rank', 150)

        # Net rating advantage (normalized)
        home_net = row.get('home_adj_off_eff', 105.0) - row.get('home_adj_def_eff', 100.0)
        away_net = row.get('away_adj_off_eff', 105.0) - row.get('away_adj_def_eff', 100.0)
        features[25] = home_net - away_net

        # Ranking advantage (positive = home favored)
        features[26] = away_rank - home_rank

        return features.reshape(1, -1)

    @staticmethod
    def get_moneyline_features(row: pd.Series) -> np.ndarray:
        """
        Extract 34 features for moneyline prediction

        Additional features beyond spreads:
        - Win probability indicators
        - Conference matchup details
        - Quality win potential
        - Efficiency ratios
        """
        features = np.zeros(34)

        # Start with spreads features (first 27)
        spreads_features = NCAABFeatureEngineer.get_spreads_features(row).flatten()
        features[:27] = spreads_features

        # Moneyline-specific features [27-33]
        home_em = row.get('home_adj_em', 0.0)
        away_em = row.get('away_adj_em', 0.0)

        # Pythagorean win expectancy approximation
        features[27] = 1 / (1 + np.exp(-home_em / 10))  # Sigmoid of EM (home win prob)
        features[28] = 1 / (1 + np.exp(-away_em / 10))  # Away win prob

        # Quality indicators
        home_rank = row.get('home_rank', 150)
        away_rank = row.get('away_rank', 150)
        features[29] = 1 if home_rank <= 50 and away_rank > 100 else 0  # Mismatch (home favored)
        features[30] = 1 if away_rank <= 50 and home_rank > 100 else 0  # Mismatch (away favored)

        # Efficiency ratios
        home_off = row.get('home_adj_off_eff', 105.0)
        away_def = row.get('away_adj_def_eff', 100.0)
        away_off = row.get('away_adj_off_eff', 105.0)
        home_def = row.get('home_adj_def_eff', 100.0)

        features[31] = home_off / max(away_def, 80.0)  # Home offensive advantage
        features[32] = away_off / max(home_def, 80.0)  # Away offensive advantage

        # Elite team indicator
        features[33] = 1 if home_rank <= 10 or away_rank <= 10 else 0

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
            n_features = 25
        elif model_type == 'spreads':
            feature_func = self.get_spreads_features
            n_features = 27
        elif model_type == 'moneyline':
            feature_func = self.get_moneyline_features
            n_features = 34
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
            'home_adj_tempo', 'away_adj_tempo', 'combined_tempo', 'tempo_diff',
            'home_adj_off_eff', 'away_adj_off_eff', 'avg_offense', 'off_diff',
            'home_adj_def_eff', 'away_adj_def_eff', 'avg_defense', 'def_diff',
            'home_adj_em', 'away_adj_em', 'em_diff',
            'is_fast_paced', 'is_slow_paced',
            'home_power_conf', 'away_power_conf', 'same_conference', 'total_power_conf_teams',
            'home_rank_inverse', 'away_rank_inverse', 'rank_diff', 'has_top25_team'
        ]

        spreads_names = totals_names + [
            'net_efficiency_advantage',
            'ranking_advantage'
        ]

        moneyline_names = spreads_names + [
            'home_win_prob_em', 'away_win_prob_em',
            'is_mismatch_home_favored', 'is_mismatch_away_favored',
            'home_offensive_ratio', 'away_offensive_ratio',
            'has_elite_team'
        ]

        if model_type == 'totals':
            return totals_names
        elif model_type == 'spreads':
            return spreads_names
        elif model_type == 'moneyline':
            return moneyline_names
        else:
            raise ValueError(f"Unknown model type: {model_type}")
