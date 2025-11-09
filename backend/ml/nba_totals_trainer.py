"""
NBA Totals Models Trainer
Trains Random Forest, LightGBM, and Linear Regression for NBA game totals

Uses 3,690 games from 2022-2025 with 49 features
Target: actual_total (combined points)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import lightgbm as lgb
import joblib
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NBATotalsTrainer:
    """Train multiple models for NBA totals prediction"""

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
        logger.info(f"[OK] Loaded {len(df)} games")
        logger.info(f"[OK] Features: {len(df.columns)}")
        logger.info(f"[OK] Date range: {df['game_date'].min()} to {df['game_date'].max()}")
        logger.info(f"[OK] Average total: {df['actual_total'].mean():.1f} points")

        return df

    def prepare_features(self, df):
        """Select and prepare features for training"""

        # Features to exclude
        exclude_cols = [
            'actual_total',  # Target variable
            'game_id', 'season', 'game_date',  # Metadata
            'home_team', 'away_team',  # Team names
            'home_score', 'away_score'  # Actual scores (would leak target)
        ]

        feature_cols = [col for col in df.columns if col not in exclude_cols]
        feature_cols = [col for col in feature_cols if df[col].dtype in ['int64', 'float64']]

        logger.info(f"\n[FEATURES] Using {len(feature_cols)} features:")
        for col in sorted(feature_cols)[:10]:
            logger.info(f"  - {col}")
        logger.info(f"  ... and {len(feature_cols) - 10} more")

        X = df[feature_cols].copy()
        y = df['actual_total'].copy()

        # Handle any NaN values
        X = X.fillna(X.mean())

        logger.info(f"\n[OK] Feature matrix: {X.shape}")
        logger.info(f"[OK] Target range: {y.min():.0f} - {y.max():.0f} points")

        return X, y, feature_cols

    def train_random_forest(self, X_train, y_train, X_test, y_test):
        """Train Random Forest model"""
        logger.info("\n" + "="*70)
        logger.info("TRAINING RANDOM FOREST MODEL")
        logger.info("="*70)
        logger.info("Guide: 'Best for NBA totals' - handles non-linear pace × efficiency")

        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1,
            verbose=1
        )

        model.fit(X_train, y_train)

        # Predictions
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Metrics
        mae_train = mean_absolute_error(y_train, y_pred_train)
        mae_test = mean_absolute_error(y_test, y_pred_test)
        rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
        r2_test = r2_score(y_test, y_pred_test)

        # Within X points accuracy
        errors = np.abs(y_pred_test - y_test)
        within_5 = np.mean(errors <= 5) * 100
        within_10 = np.mean(errors <= 10) * 100

        logger.info(f"\n[RESULTS]")
        logger.info(f"  Train MAE: {mae_train:.2f} points")
        logger.info(f"  Test MAE:  {mae_test:.2f} points")
        logger.info(f"  Test RMSE: {rmse_test:.2f} points")
        logger.info(f"  R²: {r2_test:.4f}")
        logger.info(f"  Within 5 points: {within_5:.1f}%")
        logger.info(f"  Within 10 points: {within_10:.1f}%")

        self.training_stats['random_forest'] = {
            'mae': mae_test,
            'rmse': rmse_test,
            'r2': r2_test,
            'within_5_pts': within_5,
            'within_10_pts': within_10,
            'n_samples': len(y_test)
        }

        return model

    def train_lightgbm(self, X_train, y_train, X_test, y_test):
        """Train LightGBM model"""
        logger.info("\n" + "="*70)
        logger.info("TRAINING LIGHTGBM MODEL")
        logger.info("="*70)
        logger.info("Guide: 'Faster and often better accuracy than XGBoost'")

        model = lgb.LGBMRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=10,
            num_leaves=31,
            min_child_samples=20,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )

        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            eval_metric='mae',
            callbacks=[lgb.early_stopping(stopping_rounds=20), lgb.log_evaluation(period=50)]
        )

        # Predictions
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Metrics
        mae_train = mean_absolute_error(y_train, y_pred_train)
        mae_test = mean_absolute_error(y_test, y_pred_test)
        rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
        r2_test = r2_score(y_test, y_pred_test)

        errors = np.abs(y_pred_test - y_test)
        within_5 = np.mean(errors <= 5) * 100
        within_10 = np.mean(errors <= 10) * 100

        logger.info(f"\n[RESULTS]")
        logger.info(f"  Train MAE: {mae_train:.2f} points")
        logger.info(f"  Test MAE:  {mae_test:.2f} points")
        logger.info(f"  Test RMSE: {rmse_test:.2f} points")
        logger.info(f"  R²: {r2_test:.4f}")
        logger.info(f"  Within 5 points: {within_5:.1f}%")
        logger.info(f"  Within 10 points: {within_10:.1f}%")

        self.training_stats['lightgbm'] = {
            'mae': mae_test,
            'rmse': rmse_test,
            'r2': r2_test,
            'within_5_pts': within_5,
            'within_10_pts': within_10,
            'n_samples': len(y_test)
        }

        return model

    def train_linear_regression(self, X_train, y_train, X_test, y_test):
        """Train Linear Regression model"""
        logger.info("\n" + "="*70)
        logger.info("TRAINING LINEAR REGRESSION MODEL")
        logger.info("="*70)
        logger.info("Guide: 'Fast backup for live betting, interpretable'")

        model = LinearRegression()
        model.fit(X_train, y_train)

        # Predictions
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Metrics
        mae_train = mean_absolute_error(y_train, y_pred_train)
        mae_test = mean_absolute_error(y_test, y_pred_test)
        rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
        r2_test = r2_score(y_test, y_pred_test)

        errors = np.abs(y_pred_test - y_test)
        within_5 = np.mean(errors <= 5) * 100
        within_10 = np.mean(errors <= 10) * 100

        logger.info(f"\n[RESULTS]")
        logger.info(f"  Train MAE: {mae_train:.2f} points")
        logger.info(f"  Test MAE:  {mae_test:.2f} points")
        logger.info(f"  Test RMSE: {rmse_test:.2f} points")
        logger.info(f"  R²: {r2_test:.4f}")
        logger.info(f"  Within 5 points: {within_5:.1f}%")
        logger.info(f"  Within 10 points: {within_10:.1f}%")

        self.training_stats['linear_regression'] = {
            'mae': mae_test,
            'rmse': rmse_test,
            'r2': r2_test,
            'within_5_pts': within_5,
            'within_10_pts': within_10,
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
            # Save with timestamp
            filename = f"{self.model_dir}nba_{name}_totals_{timestamp}.joblib"
            joblib.dump(model, filename)
            file_size = os.path.getsize(filename) / 1024  # KB
            logger.info(f"[OK] {name}: {filename} ({file_size:.1f} KB)")

            # Also save as latest
            latest_filename = f"{self.model_dir}nba_{name}_totals_latest.joblib"
            joblib.dump(model, latest_filename)

        # Save metadata
        metadata = {
            'feature_names': feature_names,
            'training_stats': self.training_stats,
            'timestamp': timestamp
        }
        metadata_file = f"{self.model_dir}nba_totals_metadata_{timestamp}.joblib"
        joblib.dump(metadata, metadata_file)

        latest_metadata_file = f"{self.model_dir}nba_totals_metadata_latest.joblib"
        joblib.dump(metadata, latest_metadata_file)

        logger.info(f"[OK] Metadata: {metadata_file}")
        logger.info(f"\n[SUCCESS] All models saved to {self.model_dir}")

    def compare_models(self):
        """Compare all model performances"""
        logger.info("\n" + "="*70)
        logger.info("MODEL COMPARISON")
        logger.info("="*70)

        # Sort by MAE
        sorted_models = sorted(self.training_stats.items(), key=lambda x: x[1]['mae'])

        for rank, (name, stats) in enumerate(sorted_models, 1):
            logger.info(f"\n#{rank} {name.upper().replace('_', ' ')}")
            logger.info(f"  MAE: {stats['mae']:.2f} points")
            logger.info(f"  RMSE: {stats['rmse']:.2f} points")
            logger.info(f"  R²: {stats['r2']:.4f}")
            logger.info(f"  Within 5pts: {stats['within_5_pts']:.1f}%")
            logger.info(f"  Within 10pts: {stats['within_10_pts']:.1f}%")

        best_model = sorted_models[0][0]
        logger.info(f"\n🏆 BEST MODEL: {best_model.upper().replace('_', ' ')}")

    def run(self):
        """Complete training pipeline"""
        logger.info("\n" + "="*70)
        logger.info("NBA TOTALS MODELS TRAINER")
        logger.info("Training: Random Forest, LightGBM, Linear Regression")
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
        models['random_forest'] = self.train_random_forest(X_train, y_train, X_test, y_test)
        models['lightgbm'] = self.train_lightgbm(X_train, y_train, X_test, y_test)
        models['linear_regression'] = self.train_linear_regression(X_train, y_train, X_test, y_test)

        # Compare models
        self.compare_models()

        # Save models
        self.save_models(models, feature_cols)

        logger.info(f"\n{'='*70}")
        logger.info("[COMPLETE] NBA Totals models ready for Edge Lab!")
        logger.info("="*70)
        logger.info("\nNext steps:")
        logger.info("1. Create API wrappers in backend/models/nba/")
        logger.info("2. Add to routes/models.py")
        logger.info("3. Test in Edge Lab\n")


if __name__ == "__main__":
    trainer = NBATotalsTrainer()
    trainer.run()
