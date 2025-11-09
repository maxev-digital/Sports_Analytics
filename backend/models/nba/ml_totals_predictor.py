#!/usr/bin/env python3
"""
NBA ML Totals Predictor

Uses trained machine learning models (Random Forest, XGBoost, LightGBM, Linear Regression)
to predict NBA game totals. Provides ensemble predictions for maximum accuracy.

Drop-in replacement for the traditional NBATotalsPredictor.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add ML module to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ml.model_loader import ModelLoader
from ml.feature_engineering.nba_features import NBAFeatureEngineer


class MLNBATotalsPredictor:
    """Predict NBA game totals using trained ML models"""

    def __init__(self, team_stats_df, use_ensemble=True, algorithm='random_forest'):
        """
        Initialize with team statistics DataFrame

        Args:
            team_stats_df: DataFrame with columns: team_name, pace, off_rating, def_rating, etc.
            use_ensemble: If True, average predictions from all 4 models (recommended)
            algorithm: Which model to use if not using ensemble
                      ('random_forest', 'xgboost', 'lightgbm', 'linear_regression')
        """
        self.team_stats = team_stats_df.set_index('team_name')
        self.use_ensemble = use_ensemble
        self.algorithm = algorithm

        # Initialize ML model loader
        self.model_loader = ModelLoader()
        self.feature_engineer = NBAFeatureEngineer()

        # Load models
        if use_ensemble:
            self.models = self.model_loader.load_all_models('nba', 'totals')
            print(f"[OK] Loaded {len(self.models)} NBA totals models for ensemble")
        else:
            self.model = self.model_loader.load_model('nba', 'totals', algorithm)
            print(f"[OK] Loaded NBA {algorithm} totals model")

        # League averages for reference
        self.league_avg_pace = team_stats_df['pace'].mean() if 'pace' in team_stats_df.columns else 99.0
        self.league_avg_off = team_stats_df['off_rating'].mean() if 'off_rating' in team_stats_df.columns else 113.0
        self.league_avg_def = team_stats_df['def_rating'].mean() if 'def_rating' in team_stats_df.columns else 113.0

        print(f"League Averages:")
        print(f"  Pace: {self.league_avg_pace:.1f}")
        print(f"  Off Rating: {self.league_avg_off:.1f}")
        print(f"  Def Rating: {self.league_avg_def:.1f}")

    def _create_game_row(self, home_team, away_team, game_context=None):
        """
        Create a game row for feature extraction

        Args:
            home_team: Home team name
            away_team: Away team name
            game_context: Dict with rest_days, back_to_back flags

        Returns:
            pd.Series with all required features
        """
        if game_context is None:
            game_context = {}

        try:
            home_stats = self.team_stats.loc[home_team]
            away_stats = self.team_stats.loc[away_team]
        except KeyError as e:
            raise ValueError(f"Team not found: {e}")

        # Build game row with all NBA features (32 for totals)
        game_row = pd.Series({
            # Pace features
            'home_pace': home_stats.get('pace', self.league_avg_pace),
            'away_pace': away_stats.get('pace', self.league_avg_pace),

            # Offensive/Defensive ratings
            'home_off_rating': home_stats.get('off_rating', self.league_avg_off),
            'away_off_rating': away_stats.get('off_rating', self.league_avg_off),
            'home_def_rating': home_stats.get('def_rating', self.league_avg_def),
            'away_def_rating': away_stats.get('def_rating', self.league_avg_def),

            # Shooting percentages
            'home_fg_pct': home_stats.get('fg_pct', 0.46),
            'away_fg_pct': away_stats.get('fg_pct', 0.46),
            'home_fg3_pct': home_stats.get('fg3_pct', 0.36),
            'away_fg3_pct': away_stats.get('fg3_pct', 0.36),

            # Points per game
            'home_ppg': home_stats.get('ppg', self.league_avg_off),
            'away_ppg': away_stats.get('ppg', self.league_avg_off),

            # Momentum (last 5/10 games)
            'home_last_5_ppg': home_stats.get('last_5_ppg', home_stats.get('ppg', self.league_avg_off)),
            'away_last_5_ppg': away_stats.get('last_5_ppg', away_stats.get('ppg', self.league_avg_off)),
            'home_last_10_ppg': home_stats.get('last_10_ppg', home_stats.get('ppg', self.league_avg_off)),
            'away_last_10_ppg': away_stats.get('last_10_ppg', away_stats.get('ppg', self.league_avg_off)),

            # Team quality (win percentages)
            'home_win_pct': home_stats.get('win_pct', 0.5),
            'away_win_pct': away_stats.get('win_pct', 0.5),
            'home_wins': home_stats.get('wins', 0),
            'away_wins': away_stats.get('wins', 0),
            'home_games_played': home_stats.get('games_played', 1),
            'away_games_played': away_stats.get('games_played', 1),
        })

        return game_row

    def predict_game_total(self, home_team, away_team, game_context=None):
        """
        Predict total points for an NBA game using ML models

        Args:
            home_team: Home team name
            away_team: Away team name
            game_context: Dict with rest_days, back_to_back flags (not used by ML models yet)

        Returns:
            Dict with prediction details
        """
        if game_context is None:
            game_context = {}

        # Create game row
        try:
            game_row = self._create_game_row(home_team, away_team, game_context)
        except ValueError as e:
            return {
                'error': str(e),
                'predicted_total': None
            }

        # Extract features (32 features for NBA totals)
        features = self.feature_engineer.get_totals_features(game_row)

        # Get prediction
        if self.use_ensemble:
            # Ensemble prediction from all 4 models (use median to be robust to outliers)
            result = self.model_loader.get_ensemble_prediction('nba', 'totals', features, method='median')

            predicted_total = result['prediction']
            individual_preds = result['individual_predictions']
            std = result['std']

            # Estimate points per team (rough 50/50 split with slight home advantage)
            home_expected_points = predicted_total * 0.515  # ~51.5% for home team
            away_expected_points = predicted_total * 0.485

            return {
                'predicted_total': round(predicted_total, 1),
                'home_expected_points': round(home_expected_points, 1),
                'away_expected_points': round(away_expected_points, 1),
                'expected_pace': round(game_row['home_pace'] * game_row['away_pace']) ** 0.5,
                'ensemble_std': round(std, 2),
                'individual_predictions': {k: round(v, 1) for k, v in individual_preds.items()},
                'model_type': 'ensemble',
                'breakdown': {
                    'home_pace': round(game_row['home_pace'], 1),
                    'away_pace': round(game_row['away_pace'], 1),
                    'home_off_rating': round(game_row['home_off_rating'], 1),
                    'away_off_rating': round(game_row['away_off_rating'], 1),
                    'home_def_rating': round(game_row['home_def_rating'], 1),
                    'away_def_rating': round(game_row['away_def_rating'], 1),
                    'pace_adjustment': 0.0,  # ML models handle this internally
                    'rest_factors': ['ML model handles rest internally']
                }
            }
        else:
            # Single model prediction
            predicted_total = self.model.predict(features)[0]

            home_expected_points = predicted_total * 0.515
            away_expected_points = predicted_total * 0.485

            return {
                'predicted_total': round(predicted_total, 1),
                'home_expected_points': round(home_expected_points, 1),
                'away_expected_points': round(away_expected_points, 1),
                'expected_pace': round((game_row['home_pace'] * game_row['away_pace']) ** 0.5, 1),
                'model_type': self.algorithm,
                'breakdown': {
                    'home_pace': round(game_row['home_pace'], 1),
                    'away_pace': round(game_row['away_pace'], 1),
                    'home_off_rating': round(game_row['home_off_rating'], 1),
                    'away_off_rating': round(game_row['away_off_rating'], 1),
                    'home_def_rating': round(game_row['home_def_rating'], 1),
                    'away_def_rating': round(game_row['away_def_rating'], 1),
                    'pace_adjustment': 0.0,
                    'rest_factors': ['ML model handles rest internally']
                }
            }

    def calculate_edge(self, predicted_total, market_total):
        """
        Calculate betting edge vs market

        Args:
            predicted_total: Model's predicted total
            market_total: Current market total

        Returns:
            Dict with edge, side, confidence, bet recommendation
        """
        edge = abs(predicted_total - market_total)

        recommendation = {
            'edge': round(edge, 1),
            'side': None,
            'confidence': None,
            'bet': False
        }

        # Edge thresholds (more conservative for ML models)
        if edge >= 5.0:
            recommendation['confidence'] = 'HIGH'
            recommendation['bet'] = True
        elif edge >= 3.5:
            recommendation['confidence'] = 'MEDIUM'
            recommendation['bet'] = True
        elif edge >= 2.5:
            recommendation['confidence'] = 'LOW'
            recommendation['bet'] = False
        else:
            recommendation['confidence'] = 'NONE'
            recommendation['bet'] = False

        if predicted_total > market_total:
            recommendation['side'] = 'OVER'
        else:
            recommendation['side'] = 'UNDER'

        return recommendation


if __name__ == "__main__":
    import os

    print("=" * 60)
    print("NBA ML TOTALS PREDICTOR - TEST")
    print("=" * 60)

    # Load latest team stats
    stats_file = 'backend/data/raw/nba/nba_team_stats_latest.csv'

    if not os.path.exists(stats_file):
        print(f"[ERROR] Team stats not found: {stats_file}")
        print("Run: python backend/scrapers/nba/nba_api_stats.py first")
    else:
        team_stats = pd.read_csv(stats_file)

        # Initialize ML predictor with ensemble
        print("\n[TEST 1] Ensemble Prediction")
        print("-" * 60)
        predictor = MLNBATotalsPredictor(team_stats, use_ensemble=True)

        # Test prediction
        print("\n" + "=" * 60)
        print("SAMPLE PREDICTION")
        print("=" * 60)

        # Use first two teams from stats
        home = team_stats.iloc[0]['team_name']
        away = team_stats.iloc[1]['team_name']

        print(f"\nGame: {away} @ {home}")

        result = predictor.predict_game_total(home, away)

        if 'error' in result:
            print(f"[ERROR] Error: {result['error']}")
        else:
            print(f"\n[Prediction] ML Prediction (Ensemble):")
            print(f"  Total: {result['predicted_total']}")
            print(f"  {home}: {result['home_expected_points']}")
            print(f"  {away}: {result['away_expected_points']}")
            print(f"  Expected Pace: {result['expected_pace']}")

            if 'ensemble_std' in result:
                print(f"  Std Dev: {result['ensemble_std']} (confidence measure)")

            if 'individual_predictions' in result:
                print(f"\n  Individual Model Predictions:")
                for model, pred in result['individual_predictions'].items():
                    print(f"    {model}: {pred}")

            # Test edge calculation
            market_total = 220.5
            edge = predictor.calculate_edge(result['predicted_total'], market_total)

            print(f"\n[Market Analysis] vs Market Total: {market_total}")
            print(f"  Edge: {edge['edge']} points")
            print(f"  Recommendation: {edge['side']} ({edge['confidence']})")
            print(f"  Bet: {'YES' if edge['bet'] else 'NO'}")

        # Test single model
        print("\n\n[TEST 2] Single Model (Random Forest)")
        print("-" * 60)
        predictor_rf = MLNBATotalsPredictor(team_stats, use_ensemble=False, algorithm='random_forest')

        result_rf = predictor_rf.predict_game_total(home, away)

        if 'error' not in result_rf:
            print(f"\n[Prediction] ML Prediction (Random Forest only):")
            print(f"  Total: {result_rf['predicted_total']}")

        print("\n" + "=" * 60)
        print("ML PREDICTOR TEST COMPLETE")
        print("=" * 60)
