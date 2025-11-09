"""
NBA Spreads Models Trainer
Trains Linear Regression, Random Forest, and XGBoost for NBA spreads

Target: home_margin (home_score - away_score)
Guide: "Regression with rest, travel, motivation factors"
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import joblib
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NBASpreadsTrainer:
    """Train multiple models for NBA spreads prediction"""

    def __init__(self):
        self.data_path = "backend/data/historical/nba/nba_historical_latest.csv"
        self.model_dir = "backend/ml/models/"
        os.makedirs(self.model_dir, exist_ok=True)

        self.models = {}
        self.training_stats = {}

    def load_data(self):
        """Load NBA historical data"""
        logger.info("="*70)
        logger.info("LOADING NBA HISTORICAL DATA")
        logger.info("="*70)

        df = pd.read_csv(self.data_path)

        # Create target: home margin (positive = home win, negative = away win)
        df['home_margin'] = df['home_score'] - df['away_score']

        logger.info(f"[OK] Loaded {len(df)} games")
        logger.info(f"[OK] Average margin: {df['home_margin'].mean():.1f} points")
        logger.info(f"[OK] Margin range: {df['home_margin'].min():.0f} to {df['home_margin'].max():.0f}")

        return df

    def prepare_features(self, df):
        """Select and prepare features for training"""

        # Features to exclude
        exclude_cols = [
            'home_margin',  # Target variable (derived)
            'actual_total',  # Different target
            'game_id', 'season', 'game_date',  # Metadata
            'home_team', 'away_team',  # Team names
            'home_score', 'away_score'  # Actual scores (would leak target)
        ]

        feature_cols = [col for col in df.columns if col not in exclude_cols]
        feature_cols = [col for col in feature_cols if df[col].dtype in ['int64', 'float64']]

        logger.info(f"\n[FEATURES] Using {len(feature_cols)} features")
        logger.info(f"Key features: win_pct_diff, point_diff_diff, home_momentum")

        X = df[feature_cols].copy()
        y = df['home_margin'].copy()

        # Handle any NaN values
        X = X.fillna(X.mean())

        logger.info(f"\n[OK] Feature matrix: {X.shape}")

        return X, y, feature_cols

    def train_linear_regression(self, X_train, y_train, X_test, y_test):
        """Train Linear Regression model"""
        logger.info("\n" + "="*70)
        logger.info("TRAINING LINEAR REGRESSION MODEL")
        logger.info("="*70)
        logger.info("Guide: 'Primary model for NBA spreads - power ratings approach'")

        model = LinearRegression()
        model.fit(X_train, y_train)

        # Predictions
        y_pred_test = model.predict(X_test)

        # Metrics
        mae_test = mean_absolute_error(y_test, y_pred_test)
        rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
        r2_test = r2_score(y_test, y_pred_test)

        # ATS (Against The Spread) accuracy
        # In spreads betting, we care about predicting the winner ATS
        correct_direction = np.sum((y_test > 0) == (y_pred_test > 0))
        ats_accuracy = (correct_direction / len(y_test)) * 100

        # Within X points accuracy
        errors = np.abs(y_pred_test - y_test)
        within_3 = np.mean(errors <= 3) * 100
        within_7 = np.mean(errors <= 7) * 100

        logger.info(f"\n[RESULTS]")
        logger.info(f"  Test MAE:  {mae_test:.2f} points")
        logger.info(f"  Test RMSE: {rmse_test:.2f} points")
        logger.info(f"  R²: {r2_test:.4f}")
        logger.info(f"  ATS Accuracy: {ats_accuracy:.1f}%")
        logger.info(f"  Within 3 points: {within_3:.1f}%")
        logger.info(f"  Within 7 points: {within_7:.1f}%")

        self.training_stats['linear_regression'] = {
            'mae': mae_test,
            'rmse': rmse_test,
            'r2': r2_test,
            'ats_accuracy': ats_accuracy,
            'within_3_pts': within_3,
            'within_7_pts': within_7,
            'n_samples': len(y_test)
        }

        return model

    def train_random_forest(self, X_train, y_train, X_test, y_test):
        """Train Random Forest model"""
        logger.info("\n" + "="*70)
        logger.info("TRAINING RANDOM FOREST MODEL")
        logger.info("="*70)
        logger.info("Guide: 'Captures matchup-specific factors'")

        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1,
            verbose=1
        )

        model.fit(X_train, y_train)
        y_pred_test = model.predict(X_test)

        # Metrics
        mae_test = mean_absolute_error(y_test, y_pred_test)
        rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
        r2_test = r2_score(y_test, y_pred_test)

        correct_direction = np.sum((y_test > 0) == (y_pred_test > 0))
        ats_accuracy = (correct_direction / len(y_test)) * 100

        errors = np.abs(y_pred_test - y_test)
        within_3 = np.mean(errors <= 3) * 100
        within_7 = np.mean(errors <= 7) * 100

        logger.info(f"\n[RESULTS]")
        logger.info(f"  Test MAE:  {mae_test:.2f} points")
        logger.info(f"  Test RMSE: {rmse_test:.2f} points")
        logger.info(f"  R²: {r2_test:.4f}")
        logger.info(f"  ATS Accuracy: {ats_accuracy:.1f}%")
        logger.info(f"  Within 3 points: {within_3:.1f}%")
        logger.info(f"  Within 7 points: {within_7:.1f}%")

        self.training_stats['random_forest'] = {
            'mae': mae_test,
            'rmse': rmse_test,
            'r2': r2_test,
            'ats_accuracy': ats_accuracy,
            'within_3_pts': within_3,
            'within_7_pts': within_7,
            'n_samples': len(y_test)
        }

        return model

    def train_xgboost(self, X_train, y_train, X_test, y_test):
        """Train XGBoost model"""
        logger.info("\n" + "="*70)
        logger.info("TRAINING XGBOOST MODEL")
        logger.info("="*70)

        model = xgb.XGBRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=10,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )

        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=50
        )

        y_pred_test = model.predict(X_test)

        # Metrics
        mae_test = mean_absolute_error(y_test, y_pred_test)
        rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
        r2_test = r2_score(y_test, y_pred_test)

        correct_direction = np.sum((y_test > 0) == (y_pred_test > 0))
        ats_accuracy = (correct_direction / len(y_test)) * 100

        errors = np.abs(y_pred_test - y_test)
        within_3 = np.mean(errors <= 3) * 100
        within_7 = np.mean(errors <= 7) * 100

        logger.info(f"\n[RESULTS]")
        logger.info(f"  Test MAE:  {mae_test:.2f} points")
        logger.info(f"  Test RMSE: {rmse_test:.2f} points")
        logger.info(f"  R²: {r2_test:.4f}")
        logger.info(f"  ATS Accuracy: {ats_accuracy:.1f}%")
        logger.info(f"  Within 3 points: {within_3:.1f}%")
        logger.info(f"  Within 7 points: {within_7:.1f}%")

        self.training_stats['xgboost'] = {
            'mae': mae_test,
            'rmse': rmse_test,
            'r2': r2_test,
            'ats_accuracy': ats_accuracy,
            'within_3_pts': within_3,
            'within_7_pts': within_7,
            'n_samples': len(y_test)
        }

        return model

    def save_models(self, models, feature_names):
        """Save all trained models"""
        logger.info("\n" + "="*70)
        logger.info("SAVING MODELS")
        logger.info("="*70)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for name, model in models.items():
            filename = f"{self.model_dir}nba_{name}_spreads_{timestamp}.joblib"
            joblib.dump(model, filename)
            file_size = os.path.getsize(filename) / 1024
            logger.info(f"[OK] {name}: {filename} ({file_size:.1f} KB)")

            latest_filename = f"{self.model_dir}nba_{name}_spreads_latest.joblib"
            joblib.dump(model, latest_filename)

        # Save metadata
        metadata = {
            'feature_names': feature_names,
            'training_stats': self.training_stats,
            'timestamp': timestamp,
            'target': 'home_margin'
        }
        metadata_file = f"{self.model_dir}nba_spreads_metadata_{timestamp}.joblib"
        joblib.dump(metadata, metadata_file)

        latest_metadata_file = f"{self.model_dir}nba_spreads_metadata_latest.joblib"
        joblib.dump(metadata, latest_metadata_file)

        logger.info(f"\n[SUCCESS] All models saved")

    def compare_models(self):
        """Compare all model performances"""
        logger.info("\n" + "="*70)
        logger.info("MODEL COMPARISON (Sorted by ATS Accuracy)")
        logger.info("="*70)

        # Sort by ATS accuracy (most important for spreads)
        sorted_models = sorted(self.training_stats.items(), key=lambda x: x[1]['ats_accuracy'], reverse=True)

        for rank, (name, stats) in enumerate(sorted_models, 1):
            logger.info(f"\n#{rank} {name.upper().replace('_', ' ')}")
            logger.info(f"  ATS Accuracy: {stats['ats_accuracy']:.1f}% ⭐")
            logger.info(f"  MAE: {stats['mae']:.2f} points")
            logger.info(f"  Within 3pts: {stats['within_3_pts']:.1f}%")
            logger.info(f"  Within 7pts: {stats['within_7_pts']:.1f}%")

        best_model = sorted_models[0][0]
        best_ats = sorted_models[0][1]['ats_accuracy']
        logger.info(f"\n🏆 BEST MODEL: {best_model.upper().replace('_', ' ')} ({best_ats:.1f}% ATS)")

    def run(self):
        """Complete training pipeline"""
        logger.info("\n" + "="*70)
        logger.info("NBA SPREADS MODELS TRAINER")
        logger.info("Training: Linear Regression, Random Forest, XGBoost")
        logger.info("="*70)

        # Load data
        df = self.load_data()

        # Prepare features
        X, y, feature_cols = self.prepare_features(df)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        logger.info(f"\n[SPLIT] Train: {len(X_train)} games, Test: {len(X_test)} games")

        # Train all models
        models = {}
        models['linear_regression'] = self.train_linear_regression(X_train, y_train, X_test, y_test)
        models['random_forest'] = self.train_random_forest(X_train, y_train, X_test, y_test)
        models['xgboost'] = self.train_xgboost(X_train, y_train, X_test, y_test)

        # Compare models
        self.compare_models()

        # Save models
        self.save_models(models, feature_cols)

        logger.info(f"\n{'='*70}")
        logger.info("[COMPLETE] NBA Spreads models ready!")
        logger.info("="*70)


if __name__ == "__main__":
    trainer = NBASpreadsTrainer()
    trainer.run()
