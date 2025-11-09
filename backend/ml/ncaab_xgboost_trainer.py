"""
NCAAB XGBoost Training Pipeline
Train XGBoost model to predict game totals using KenPom features
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NCAABXGBoostTrainer:
    """Train XGBoost model for NCAAB totals prediction"""

    def __init__(self):
        self.model = None
        self.feature_names = []
        self.training_stats = {}

    def load_data(self):
        """Load historical game data and KenPom stats"""
        logger.info("Loading historical game data...")

        # Load game results
        games_file = "backend/data/historical/game_results_2024_season_20251010_125603.csv"
        games_df = pd.read_csv(games_file)
        logger.info(f"Loaded {len(games_df)} games from 2023-24 season")

        # Load KenPom stats (end-of-season 2023-24)
        kenpom_file = "backend/data/historical/kenpom_2024_season_20251010_114442.csv"
        kenpom_df = pd.read_csv(kenpom_file)
        logger.info(f"Loaded KenPom stats for {len(kenpom_df)} teams")

        return games_df, kenpom_df

    def engineer_features(self, games_df, kenpom_df):
        """
        Engineer features for XGBoost training

        Features created:
        - Team efficiency metrics (offense, defense, tempo)
        - Matchup differentials
        - Products and ratios
        - Tempo-adjusted expectations
        """
        logger.info("Engineering features...")

        # Create lookup dict for KenPom stats
        kenpom_dict = {}
        for _, row in kenpom_df.iterrows():
            team_name = row['Team'].strip()
            kenpom_dict[team_name] = {
                'AdjEM': row['AdjEM'],
                'AdjOffEff': row['AdjOffEff'],
                'AdjDefEff': row['AdjDefEff'],
                'AdjTempo': row['AdjTempo'],
                'Rank': row['Rank']
            }

        # Build feature matrix
        features_list = []
        targets = []

        for idx, game in games_df.iterrows():
            home_team = game['Home_Team'].strip()
            away_team = game['Away_Team'].strip()
            actual_total = game['Actual_Total']

            # Get KenPom stats (with fuzzy matching)
            home_stats = self._find_team_stats(home_team, kenpom_dict)
            away_stats = self._find_team_stats(away_team, kenpom_dict)

            if home_stats is None or away_stats is None:
                # Skip game if we can't find team stats
                continue

            # Calculate features
            features = self._calculate_game_features(home_stats, away_stats)

            features_list.append(features)
            targets.append(actual_total)

        X = pd.DataFrame(features_list)
        y = pd.Series(targets)

        self.feature_names = list(X.columns)

        logger.info(f"Engineered {len(X)} games with {len(X.columns)} features")
        logger.info(f"Features: {self.feature_names}")

        return X, y

    def _find_team_stats(self, team_name, kenpom_dict):
        """Find team in KenPom dict with fuzzy matching"""
        # Try exact match first
        if team_name in kenpom_dict:
            return kenpom_dict[team_name]

        # Try case-insensitive match
        team_lower = team_name.lower()
        for kp_team, stats in kenpom_dict.items():
            if kp_team.lower() == team_lower:
                return stats

        # Try partial match (for teams like "UConn" vs "Connecticut")
        for kp_team, stats in kenpom_dict.items():
            if team_lower in kp_team.lower() or kp_team.lower() in team_lower:
                return stats

        # Common aliases
        aliases = {
            'UConn': 'Connecticut',
            'Miami (FL)': 'Miami FL',
            'Miami': 'Miami FL',
            'Ole Miss': 'Mississippi',
            'USC': 'Southern California',
        }

        if team_name in aliases:
            alt_name = aliases[team_name]
            return self._find_team_stats(alt_name, kenpom_dict)

        logger.warning(f"Could not find KenPom stats for: {team_name}")
        return None

    def _calculate_game_features(self, home_stats, away_stats):
        """Calculate all features for a single game"""

        # Basic stats
        features = {
            # Home team stats
            'home_adj_em': home_stats['AdjEM'],
            'home_off_eff': home_stats['AdjOffEff'],
            'home_def_eff': home_stats['AdjDefEff'],
            'home_tempo': home_stats['AdjTempo'],
            'home_rank': home_stats['Rank'],

            # Away team stats
            'away_adj_em': away_stats['AdjEM'],
            'away_off_eff': away_stats['AdjOffEff'],
            'away_def_eff': away_stats['AdjDefEff'],
            'away_tempo': away_stats['AdjTempo'],
            'away_rank': away_stats['Rank'],
        }

        # Differentials
        features['em_diff'] = home_stats['AdjEM'] - away_stats['AdjEM']
        features['tempo_diff'] = home_stats['AdjTempo'] - away_stats['AdjTempo']
        features['rank_diff'] = away_stats['Rank'] - home_stats['Rank']  # Lower rank = better

        # Averages (expected pace)
        features['avg_tempo'] = (home_stats['AdjTempo'] + away_stats['AdjTempo']) / 2
        features['geometric_tempo'] = np.sqrt(home_stats['AdjTempo'] * away_stats['AdjTempo'])

        # Offensive/Defensive matchups
        features['home_off_vs_away_def'] = home_stats['AdjOffEff'] - away_stats['AdjDefEff']
        features['away_off_vs_home_def'] = away_stats['AdjOffEff'] - home_stats['AdjDefEff']
        features['total_off_eff'] = home_stats['AdjOffEff'] + away_stats['AdjOffEff']
        features['total_def_eff'] = home_stats['AdjDefEff'] + away_stats['AdjDefEff']
        features['avg_off_eff'] = (home_stats['AdjOffEff'] + away_stats['AdjOffEff']) / 2
        features['avg_def_eff'] = (home_stats['AdjDefEff'] + away_stats['AdjDefEff']) / 2

        # Products (interaction effects)
        features['tempo_x_off_eff'] = features['avg_tempo'] * features['avg_off_eff']
        features['tempo_x_def_eff'] = features['avg_tempo'] * features['avg_def_eff']

        # Efficiency margin (how much better offense is than defense)
        features['home_eff_margin'] = home_stats['AdjOffEff'] - home_stats['AdjDefEff']
        features['away_eff_margin'] = away_stats['AdjOffEff'] - away_stats['AdjDefEff']
        features['total_eff_margin'] = features['home_eff_margin'] + features['away_eff_margin']

        # Expected points (basic formula)
        # Points = (Efficiency / 100) * Tempo
        features['expected_home_pts'] = (home_stats['AdjOffEff'] / 100) * features['geometric_tempo']
        features['expected_away_pts'] = (away_stats['AdjOffEff'] / 100) * features['geometric_tempo']
        features['expected_total_basic'] = features['expected_home_pts'] + features['expected_away_pts']

        # Defensive adjustment
        features['expected_home_pts_adj'] = ((home_stats['AdjOffEff'] - (away_stats['AdjDefEff'] - 100)) / 100) * features['geometric_tempo']
        features['expected_away_pts_adj'] = ((away_stats['AdjOffEff'] - (home_stats['AdjDefEff'] - 100)) / 100) * features['geometric_tempo']
        features['expected_total_adj'] = features['expected_home_pts_adj'] + features['expected_away_pts_adj']

        # Tempo extremes (binary flags)
        features['fast_pace_game'] = 1 if features['avg_tempo'] > 70 else 0
        features['slow_pace_game'] = 1 if features['avg_tempo'] < 65 else 0

        # Efficiency extremes
        features['high_scoring_offense'] = 1 if features['avg_off_eff'] > 115 else 0
        features['elite_defense'] = 1 if features['avg_def_eff'] < 95 else 0

        # Mismatches
        features['tempo_mismatch'] = 1 if abs(features['tempo_diff']) > 5 else 0
        features['rank_mismatch'] = 1 if abs(features['rank_diff']) > 50 else 0

        return features

    def train_model(self, X_train, y_train, X_val, y_val):
        """Train XGBoost model"""
        logger.info("Training XGBoost model...")

        # XGBoost parameters optimized for regression
        params = {
            'objective': 'reg:squarederror',
            'max_depth': 6,
            'learning_rate': 0.05,
            'n_estimators': 200,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 3,
            'gamma': 0.1,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'random_state': 42
        }

        # Create DMatrix for XGBoost
        dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=self.feature_names)
        dval = xgb.DMatrix(X_val, label=y_val, feature_names=self.feature_names)

        # Train with early stopping
        evals = [(dtrain, 'train'), (dval, 'val')]

        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=200,
            evals=evals,
            early_stopping_rounds=20,
            verbose_eval=False
        )

        logger.info(f"Training complete. Best iteration: {self.model.best_iteration}")

        return self.model

    def evaluate_model(self, X_test, y_test):
        """Evaluate model performance"""
        logger.info("Evaluating model...")

        dtest = xgb.DMatrix(X_test, feature_names=self.feature_names)
        predictions = self.model.predict(dtest)

        # Calculate metrics
        mae = mean_absolute_error(y_test, predictions)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        r2 = r2_score(y_test, predictions)

        # Within X points accuracy
        errors = np.abs(predictions - y_test)
        within_3 = np.mean(errors <= 3) * 100
        within_5 = np.mean(errors <= 5) * 100
        within_10 = np.mean(errors <= 10) * 100

        self.training_stats = {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'within_3_pts': within_3,
            'within_5_pts': within_5,
            'within_10_pts': within_10,
            'n_samples': len(y_test)
        }

        logger.info("=" * 60)
        logger.info("MODEL EVALUATION RESULTS")
        logger.info("=" * 60)
        logger.info(f"Test samples: {len(y_test)}")
        logger.info(f"MAE: {mae:.2f} points")
        logger.info(f"RMSE: {rmse:.2f} points")
        logger.info(f"R²: {r2:.4f}")
        logger.info(f"Within 3 points: {within_3:.1f}%")
        logger.info(f"Within 5 points: {within_5:.1f}%")
        logger.info(f"Within 10 points: {within_10:.1f}%")
        logger.info("=" * 60)

        return predictions

    def get_feature_importance(self):
        """Get and display feature importance"""
        importance = self.model.get_score(importance_type='gain')

        # Sort by importance
        importance_df = pd.DataFrame([
            {'feature': k, 'importance': v}
            for k, v in importance.items()
        ]).sort_values('importance', ascending=False)

        logger.info("\nTOP 20 FEATURE IMPORTANCE:")
        logger.info("=" * 60)
        for idx, row in importance_df.head(20).iterrows():
            logger.info(f"{row['feature']:.<50} {row['importance']:>8.1f}")

        return importance_df

    def save_model(self, output_dir="backend/ml/models"):
        """Save trained model and metadata"""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = f"{output_dir}/ncaab_xgboost_{timestamp}.json"
        metadata_path = f"{output_dir}/ncaab_xgboost_{timestamp}_metadata.pkl"

        # Save XGBoost model
        self.model.save_model(model_path)
        logger.info(f"Model saved: {model_path}")

        # Save metadata
        metadata = {
            'feature_names': self.feature_names,
            'training_stats': self.training_stats,
            'timestamp': timestamp
        }
        joblib.dump(metadata, metadata_path)
        logger.info(f"Metadata saved: {metadata_path}")

        # Also save as "latest"
        latest_model_path = f"{output_dir}/ncaab_xgboost_latest.json"
        latest_metadata_path = f"{output_dir}/ncaab_xgboost_latest_metadata.pkl"
        self.model.save_model(latest_model_path)
        joblib.dump(metadata, latest_metadata_path)
        logger.info(f"Latest model saved: {latest_model_path}")

        return model_path, metadata_path

    def run_full_pipeline(self):
        """Run complete training pipeline"""
        logger.info("=" * 60)
        logger.info("NCAAB XGBOOST TRAINING PIPELINE")
        logger.info("=" * 60)

        # 1. Load data
        games_df, kenpom_df = self.load_data()

        # 2. Engineer features
        X, y = self.engineer_features(games_df, kenpom_df)

        logger.info(f"\nDataset: {len(X)} games")
        logger.info(f"Features: {len(X.columns)}")
        logger.info(f"Target range: {y.min():.1f} - {y.max():.1f} points")
        logger.info(f"Target mean: {y.mean():.1f} points")

        # 3. Split data: 70% train, 15% validation, 15% test
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=0.15, random_state=42
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.176, random_state=42  # 0.176 * 0.85 ≈ 0.15
        )

        logger.info(f"\nTrain set: {len(X_train)} games ({len(X_train)/len(X)*100:.1f}%)")
        logger.info(f"Validation set: {len(X_val)} games ({len(X_val)/len(X)*100:.1f}%)")
        logger.info(f"Test set: {len(X_test)} games ({len(X_test)/len(X)*100:.1f}%)")

        # 4. Train model
        self.train_model(X_train, y_train, X_val, y_val)

        # 5. Evaluate on test set
        predictions = self.evaluate_model(X_test, y_test)

        # 6. Feature importance
        importance_df = self.get_feature_importance()

        # 7. Save model
        model_path, metadata_path = self.save_model()

        logger.info("\n" + "=" * 60)
        logger.info("TRAINING COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"Model: {model_path}")
        logger.info(f"MAE: {self.training_stats['mae']:.2f} points")
        logger.info(f"Within 5 points: {self.training_stats['within_5_pts']:.1f}%")
        logger.info("=" * 60)

        return self.model, self.training_stats, importance_df


if __name__ == "__main__":
    trainer = NCAABXGBoostTrainer()
    model, stats, importance = trainer.run_full_pipeline()
