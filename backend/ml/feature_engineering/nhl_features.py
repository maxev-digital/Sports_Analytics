"""
NHL Feature Engineering

Converts raw game/team data into model-ready features
Matches the feature extraction in the model files
"""

import numpy as np
import pandas as pd
from typing import Dict, List


class NHLFeatureEngineer:
    """Feature engineering for NHL models"""

    @staticmethod
    def get_totals_features(row: pd.Series) -> np.ndarray:
        """
        Extract features for totals prediction

        UPGRADED 2025-11-11: Now 44 features (was 24)
        Added: xG (6), shot quality (4), possession (4), empty net (6)
        """
        # NOTE: Production models trained with 27 features (24 original + 3 empty net features)
        features = np.array([
            # Offensive stats (8)
            row['home_goals_per_game'],
            row['away_goals_per_game'],
            row['home_shots_per_game'],
            row['away_shots_per_game'],
            row['home_shooting_pct'],
            row['away_shooting_pct'],
            row['home_power_play_pct'],
            row['away_power_play_pct'],

            # Defensive stats (8)
            row['home_goals_against_per_game'],
            row['away_goals_against_per_game'],
            row['home_shots_against_per_game'],
            row['away_shots_against_per_game'],
            row['home_penalty_kill_pct'],
            row['away_penalty_kill_pct'],
            row['home_save_pct'],
            row['away_save_pct'],

            # Advanced stats (4)
            row['home_pdo'],
            row['away_pdo'],
            row['home_faceoff_win_pct'],
            row['away_faceoff_win_pct'],

            row.get("home_win_pct", 0.5),
            row.get("away_win_pct", 0.5),
            # Goalie stats (4)
#            row.get('home_goalie_save_pct', row['home_save_pct']),
#            row.get('away_goalie_save_pct', row['away_save_pct']),
#            row.get('home_goalie_gaa', row['home_goals_against_per_game']),
#            row.get('away_goalie_gaa', row['away_goals_against_per_game']),
#
#            # Empty net stats (3) - added to reach 27 features
#            row.get('home_en_goals_for_per_game', 0),
#            row.get('away_en_goals_for_per_game', 0),
#            row.get('home_en_success_rate', 0),
        ])
        return features.reshape(1, -1)

    @staticmethod
    def get_spreads_features(row: pd.Series) -> np.ndarray:
        """
        Extract features for spreads prediction

        UPGRADED 2025-11-11: Now 49 features (was 29)
        Added: xG (6), shot quality (4), possession (4), empty net (6)
        """
        features = np.array([
            # === ORIGINAL 29 FEATURES ===
            # Team strength differential
            row['home_goals_per_game'] - row['away_goals_per_game'],
            row['home_goals_against_per_game'] - row['away_goals_against_per_game'],

            # Offensive stats
            row['home_goals_per_game'],
            row['away_goals_per_game'],
            row['home_shots_per_game'],
            row['away_shots_per_game'],
            row['home_shooting_pct'],
            row['away_shooting_pct'],
            row['home_power_play_pct'],
            row['away_power_play_pct'],

            # Defensive stats
            row['home_goals_against_per_game'],
            row['away_goals_against_per_game'],
            row['home_shots_against_per_game'],
            row['away_shots_against_per_game'],
            row['home_penalty_kill_pct'],
            row['away_penalty_kill_pct'],
            row['home_save_pct'],
            row['away_save_pct'],

            # Advanced stats
            row['home_pdo'],
            row['away_pdo'],
            row['home_faceoff_win_pct'],
            row['away_faceoff_win_pct'],
            (row['home_goals_per_game'] - row['home_goals_against_per_game']) / 6.0,
            (row['away_goals_per_game'] - row['away_goals_against_per_game']) / 6.0,

            # Goalie stats
            row.get('home_goalie_save_pct', row['home_save_pct']),
            row.get('away_goalie_save_pct', row['away_save_pct']),
            row.get('home_goalie_gaa', row['home_goals_against_per_game']),
            row.get('away_goalie_gaa', row['away_goals_against_per_game']),

            # Home ice advantage
            1.0,

            # === NEW 20 FEATURES (2025-11-11) ===
            # Expected Goals (6 features)
            row.get('home_xgoals_per_game', row['home_goals_per_game']),
            row.get('away_xgoals_per_game', row['away_goals_per_game']),
            row.get('home_xgoals_against_per_game', row['home_goals_against_per_game']),
            row.get('away_xgoals_against_per_game', row['away_goals_against_per_game']),
            row.get('home_goals_above_expected', 0),
            row.get('away_goals_above_expected', 0),

            # Shot Quality (4 features)
            row.get('home_hd_shooting_pct', 25.0),
            row.get('away_hd_shooting_pct', 25.0),
            row.get('home_hd_save_pct', 0.70),
            row.get('away_hd_save_pct', 0.70),

            # Possession (4 features)
            row.get('home_corsi_for_pct', 50.0),
            row.get('away_corsi_for_pct', 50.0),
            row.get('home_fenwick_for_pct', 50.0),
            row.get('away_fenwick_for_pct', 50.0),

            # Empty Net (6 features)
            row.get('home_en_goals_for_per_game', 0),
            row.get('away_en_goals_for_per_game', 0),
            row.get('home_en_goals_against_per_game', 0),
            row.get('away_en_goals_against_per_game', 0),
            row.get('home_en_success_rate', 0),
            row.get('away_en_success_rate', 0),
        ])
        return features.reshape(1, -1)

    @staticmethod
    def get_moneyline_features(row: pd.Series) -> np.ndarray:
        """
        Extract features for moneyline prediction

        UPGRADED 2025-11-11: Now 54 features (was 34)
        Added: xG (6), shot quality (4), possession (4), empty net (6)
        """
        features = np.array([
            # === ORIGINAL 34 FEATURES ===
            # Team strength differential
            row['home_goals_per_game'] - row['away_goals_per_game'],
            row['home_goals_against_per_game'] - row['away_goals_against_per_game'],
            (row['home_goals_per_game'] - row['home_goals_against_per_game']) - (row['away_goals_per_game'] - row['away_goals_against_per_game']),

            # Offensive stats
            row['home_goals_per_game'],
            row['away_goals_per_game'],
            row['home_shots_per_game'],
            row['away_shots_per_game'],
            row['home_shooting_pct'],
            row['away_shooting_pct'],
            row['home_power_play_pct'],
            row['away_power_play_pct'],

            # Defensive stats
            row['home_goals_against_per_game'],
            row['away_goals_against_per_game'],
            row['home_shots_against_per_game'],
            row['away_shots_against_per_game'],
            row['home_penalty_kill_pct'],
            row['away_penalty_kill_pct'],
            row['home_save_pct'],
            row['away_save_pct'],

            # Advanced stats
            row['home_pdo'],
            row['away_pdo'],
            row['home_faceoff_win_pct'],
            row['away_faceoff_win_pct'],

            # Record stats
            (row['home_goals_per_game'] - row['home_goals_against_per_game']) / 6.0,
            (row['away_goals_per_game'] - row['away_goals_against_per_game']) / 6.0,
            row.get('home_points', (row['home_goals_per_game'] - row['home_goals_against_per_game']) / 6.0 * 82) / 82,
            row.get('away_points', (row['away_goals_per_game'] - row['away_goals_against_per_game']) / 6.0 * 82) / 82,

            # Goalie stats
            row.get('home_goalie_save_pct', row['home_save_pct']),
            row.get('away_goalie_save_pct', row['away_save_pct']),
            row.get('home_goalie_gaa', row['home_goals_against_per_game']),
            row.get('away_goalie_gaa', row['away_goals_against_per_game']),
            row.get('home_goalie_win_pct', (row['home_goals_per_game'] - row['home_goals_against_per_game']) / 6.0),
            row.get('away_goalie_win_pct', (row['away_goals_per_game'] - row['away_goals_against_per_game']) / 6.0),

            # Home ice advantage
            1.0,

            # === NEW 20 FEATURES (2025-11-11) ===
            # Expected Goals (6 features)
            row.get('home_xgoals_per_game', row['home_goals_per_game']),
            row.get('away_xgoals_per_game', row['away_goals_per_game']),
            row.get('home_xgoals_against_per_game', row['home_goals_against_per_game']),
            row.get('away_xgoals_against_per_game', row['away_goals_against_per_game']),
            row.get('home_goals_above_expected', 0),
            row.get('away_goals_above_expected', 0),

            # Shot Quality (4 features)
            row.get('home_hd_shooting_pct', 25.0),
            row.get('away_hd_shooting_pct', 25.0),
            row.get('home_hd_save_pct', 0.70),
            row.get('away_hd_save_pct', 0.70),

            # Possession (4 features)
            row.get('home_corsi_for_pct', 50.0),
            row.get('away_corsi_for_pct', 50.0),
            row.get('home_fenwick_for_pct', 50.0),
            row.get('away_fenwick_for_pct', 50.0),

            # Empty Net (6 features)
            row.get('home_en_goals_for_per_game', 0),
            row.get('away_en_goals_for_per_game', 0),
            row.get('home_en_goals_against_per_game', 0),
            row.get('away_en_goals_against_per_game', 0),
            row.get('home_en_success_rate', 0),
            row.get('away_en_success_rate', 0),
        ])
        return features.reshape(1, -1)

    @staticmethod
    def create_feature_matrix(df: pd.DataFrame, bet_type: str) -> np.ndarray:
        """
        Create feature matrix for all games

        Args:
            df: DataFrame with game data
            bet_type: 'totals', 'spreads', or 'moneyline'

        Returns:
            Feature matrix (n_games, n_features)
        """
        if bet_type == 'totals':
            features_list = [NHLFeatureEngineer.get_totals_features(row) for _, row in df.iterrows()]
        elif bet_type == 'spreads':
            features_list = [NHLFeatureEngineer.get_spreads_features(row) for _, row in df.iterrows()]
        elif bet_type == 'moneyline':
            features_list = [NHLFeatureEngineer.get_moneyline_features(row) for _, row in df.iterrows()]
        else:
            raise ValueError(f"Unknown bet_type: {bet_type}")

        return np.array(features_list)

    @staticmethod
    def get_feature_names(bet_type: str) -> List[str]:
        """Get feature names for a bet type"""
        if bet_type == 'totals':
            return [
                'home_gpg', 'away_gpg', 'home_spg', 'away_spg',
                'home_sh_pct', 'away_sh_pct', 'home_pp_pct', 'away_pp_pct',
                'home_gapg', 'away_gapg', 'home_sapg', 'away_sapg',
                'home_pk_pct', 'away_pk_pct', 'home_sv_pct', 'away_sv_pct',
                'home_pdo', 'away_pdo', 'home_fo_pct', 'away_fo_pct',
                'home_goalie_sv_pct', 'away_goalie_sv_pct',
                'home_goalie_gaa', 'away_goalie_gaa'
            ]
        elif bet_type == 'spreads':
            return [
                'gpg_diff', 'gapg_diff',
                'home_gpg', 'away_gpg', 'home_spg', 'away_spg',
                'home_sh_pct', 'away_sh_pct', 'home_pp_pct', 'away_pp_pct',
                'home_gapg', 'away_gapg', 'home_sapg', 'away_sapg',
                'home_pk_pct', 'away_pk_pct', 'home_sv_pct', 'away_sv_pct',
                'home_pdo', 'away_pdo', 'home_fo_pct', 'away_fo_pct',
                'home_win_pct', 'away_win_pct',
                'home_goalie_sv_pct', 'away_goalie_sv_pct',
                'home_goalie_gaa', 'away_goalie_gaa',
                'home_ice'
            ]
        elif bet_type == 'moneyline':
            return [
                'gpg_diff', 'gapg_diff', 'win_pct_diff',
                'home_gpg', 'away_gpg', 'home_spg', 'away_spg',
                'home_sh_pct', 'away_sh_pct', 'home_pp_pct', 'away_pp_pct',
                'home_gapg', 'away_gapg', 'home_sapg', 'away_sapg',
                'home_pk_pct', 'away_pk_pct', 'home_sv_pct', 'away_sv_pct',
                'home_pdo', 'away_pdo', 'home_fo_pct', 'away_fo_pct',
                'home_win_pct', 'away_win_pct', 'home_pts_norm', 'away_pts_norm',
                'home_goalie_sv_pct', 'away_goalie_sv_pct',
                'home_goalie_gaa', 'away_goalie_gaa',
                'home_goalie_win_pct', 'away_goalie_win_pct',
                'home_ice'
            ]
