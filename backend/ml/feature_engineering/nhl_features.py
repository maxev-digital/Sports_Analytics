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
        """Extract features for totals prediction (24 features)"""
        features = np.array([
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

            # Goalie stats (placeholders if not available)
            row.get('home_goalie_save_pct', row['home_save_pct']),
            row.get('away_goalie_save_pct', row['away_save_pct']),
            row.get('home_goalie_gaa', row['home_goals_against_per_game']),
            row.get('away_goalie_gaa', row['away_goals_against_per_game'])
        ])
        return features

    @staticmethod
    def get_spreads_features(row: pd.Series) -> np.ndarray:
        """Extract features for spreads prediction (29 features)"""
        features = np.array([
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
            row['home_win_pct'],
            row['away_win_pct'],

            # Goalie stats
            row.get('home_goalie_save_pct', row['home_save_pct']),
            row.get('away_goalie_save_pct', row['away_save_pct']),
            row.get('home_goalie_gaa', row['home_goals_against_per_game']),
            row.get('away_goalie_gaa', row['away_goals_against_per_game']),

            # Home ice advantage
            1.0
        ])
        return features

    @staticmethod
    def get_moneyline_features(row: pd.Series) -> np.ndarray:
        """Extract features for moneyline prediction (34 features)"""
        features = np.array([
            # Team strength differential
            row['home_goals_per_game'] - row['away_goals_per_game'],
            row['home_goals_against_per_game'] - row['away_goals_against_per_game'],
            row['home_win_pct'] - row['away_win_pct'],

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
            row['home_win_pct'],
            row['away_win_pct'],
            row.get('home_points', row['home_win_pct'] * 82) / 82,
            row.get('away_points', row['away_win_pct'] * 82) / 82,

            # Goalie stats
            row.get('home_goalie_save_pct', row['home_save_pct']),
            row.get('away_goalie_save_pct', row['away_save_pct']),
            row.get('home_goalie_gaa', row['home_goals_against_per_game']),
            row.get('away_goalie_gaa', row['away_goals_against_per_game']),
            row.get('home_goalie_win_pct', row['home_win_pct']),
            row.get('away_goalie_win_pct', row['away_win_pct']),

            # Home ice advantage
            1.0
        ])
        return features

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
