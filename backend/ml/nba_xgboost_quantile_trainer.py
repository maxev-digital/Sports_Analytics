"""
NBA XGBoost Quantile Regression Trainer
Trains models to predict game totals with confidence intervals

Uses NBA historical data: 3,690 games, 57 features
Target: actual_total (combined points)
Output: 3 models (10th percentile, mean, 90th percentile)
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os
from datetime import datetime

class NBAQuantileTrainer:
    """Train XGBoost quantile regression models for NBA totals prediction"""

    def __init__(self):
        self.data_path = "backend/data/historical/nba/nba_historical_latest.csv"
        self.model_dir = "backend/ml/models/"
        os.makedirs(self.model_dir, exist_ok=True)

        # XGBoost parameters optimized for totals prediction
        self.params_base = {
            'objective': 'reg:quantileerror',
            'tree_method': 'hist',
            'max_depth': 6,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 3,
            'gamma': 0.1,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'seed': 42
        }

    def load_data(self):
        """Load NBA historical data"""
        print("="*70)
        print("LOADING NBA HISTORICAL DATA")
        print("="*70)

        df = pd.read_csv(self.data_path)
        print(f"[OK] Loaded {len(df)} games from {self.data_path}")
        print(f"[OK] Features: {len(df.columns)}")
        print(f"[OK] Date range: {df['game_date'].min()} to {df['game_date'].max()}")
        print(f"[OK] Average total: {df['actual_total'].mean():.1f} points")

        return df

    def prepare_features(self, df):
        """Select and prepare features for training"""

        # Features to use (all numeric columns except target and metadata)
        exclude_cols = [
            'actual_total',  # Target variable
            'game_id', 'season', 'game_date',  # Metadata
            'home_team', 'away_team',  # Team names
            'home_score', 'away_score'  # Actual scores (would leak target)
        ]

        feature_cols = [col for col in df.columns if col not in exclude_cols]

        # Remove any non-numeric columns
        feature_cols = [col for col in feature_cols if df[col].dtype in ['int64', 'float64']]

        print(f"\n[FEATURES] Using {len(feature_cols)} features:")
        for col in sorted(feature_cols):
            print(f"  - {col}")

        X = df[feature_cols].copy()
        y = df['actual_total'].copy()

        # Handle any NaN values
        X = X.fillna(X.mean())

        print(f"\n[OK] Feature matrix: {X.shape}")
        print(f"[OK] Target range: {y.min():.0f} - {y.max():.0f} points")

        return X, y, feature_cols

    def train_quantile_models(self, X, y):
        """Train 3 quantile models: lower (10%), mean (50%), upper (90%)"""

        # Split data (80/20 train/test)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        print(f"\n[SPLIT] Train: {len(X_train)} games, Test: {len(X_test)} games")

        # Convert to DMatrix
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dtest = xgb.DMatrix(X_test, label=y_test)

        models = {}
        predictions = {}

        # Train 3 quantile models
        quantiles = {
            'lower': 0.10,  # 10th percentile
            'mean': 0.50,   # Median (close to mean for symmetric distributions)
            'upper': 0.90   # 90th percentile
        }

        for name, quantile in quantiles.items():
            print(f"\n{'='*70}")
            print(f"TRAINING {name.upper()} MODEL (quantile={quantile})")
            print("="*70)

            params = self.params_base.copy()
            params['quantile_alpha'] = quantile

            # Train model
            model = xgb.train(
                params,
                dtrain,
                num_boost_round=500,
                evals=[(dtrain, 'train'), (dtest, 'test')],
                early_stopping_rounds=50,
                verbose_eval=100
            )

            # Make predictions
            y_pred_train = model.predict(dtrain)
            y_pred_test = model.predict(dtest)

            # Calculate metrics
            mae_train = mean_absolute_error(y_train, y_pred_train)
            mae_test = mean_absolute_error(y_test, y_pred_test)
            rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))

            print(f"\n[RESULTS]")
            print(f"  Train MAE: {mae_train:.2f} points")
            print(f"  Test MAE:  {mae_test:.2f} points")
            print(f"  Test RMSE: {rmse_test:.2f} points")

            models[name] = model
            predictions[name] = y_pred_test

        # Analyze prediction intervals
        print(f"\n{'='*70}")
        print("CONFIDENCE INTERVAL ANALYSIS")
        print("="*70)

        interval_widths = predictions['upper'] - predictions['lower']
        print(f"Average 80% interval width: {interval_widths.mean():.2f} points")
        print(f"Interval range: {interval_widths.min():.2f} - {interval_widths.max():.2f} points")

        # Calculate implied standard deviation (80% interval / 2.56)
        implied_std = interval_widths / 2.56
        print(f"Implied std dev: {implied_std.mean():.2f} points")

        return models, X_test, y_test

    def save_models(self, models):
        """Save trained models"""
        print(f"\n{'='*70}")
        print("SAVING MODELS")
        print("="*70)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for name, model in models.items():
            # Save with timestamp
            filename = f"{self.model_dir}nba_quantile_{name}_{timestamp}.json"
            model.save_model(filename)
            file_size = os.path.getsize(filename) / 1024  # KB
            print(f"[OK] {name}: {filename} ({file_size:.1f} KB)")

            # Also save as latest
            latest_filename = f"{self.model_dir}nba_quantile_{name}_latest.json"
            model.save_model(latest_filename)

        print(f"\n[SUCCESS] All models saved to {self.model_dir}")

    def run(self):
        """Complete training pipeline"""
        print("\n" + "="*70)
        print("NBA XGBOOST QUANTILE REGRESSION TRAINER")
        print("="*70)

        # Load data
        df = self.load_data()

        # Prepare features
        X, y, feature_cols = self.prepare_features(df)

        # Train models
        models, X_test, y_test = self.train_quantile_models(X, y)

        # Save models
        self.save_models(models)

        print(f"\n{'='*70}")
        print("[COMPLETE] NBA XGBoost models ready for regression-to-mean strategy!")
        print("="*70)
        print()
        print("Next steps:")
        print("1. Test models with: python backend/ml/test_nba_xgboost_predictions.py")
        print("2. Integrate into live betting strategy")
        print("3. Monitor for regression opportunities")
        print()


if __name__ == "__main__":
    trainer = NBAQuantileTrainer()
    trainer.run()
