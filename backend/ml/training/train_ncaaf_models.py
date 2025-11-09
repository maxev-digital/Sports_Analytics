"""
NCAAF Model Training Script

Trains all 12 NCAAF models (Random Forest, XGBoost, LightGBM, Linear/Logistic Regression)
for Totals, Spreads, and Moneyline predictions.

Usage:
    python -m backend.ml.training.train_ncaaf_models --seasons 2023 2024

Output:
    - Trained .joblib model files in backend/ml/models/
    - Metadata files with performance stats
"""

import argparse
import joblib
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, log_loss

try:
    import xgboost as xgb
except ImportError:
    xgb = None

try:
    import lightgbm as lgb
except ImportError:
    lgb = None

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from ml.data_loaders.ncaaf_data_loader import load_ncaaf_training_data
from ml.feature_engineering.ncaaf_features import NCAAFFeatureEngineer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NCAAFModelTrainer:
    """Train all NCAAF prediction models"""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent.parent / "models"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.feature_engineer = NCAAFFeatureEngineer()

    def train_totals_models(self, df: pd.DataFrame) -> Dict:
        """Train all totals prediction models"""
        logger.info("=" * 60)
        logger.info("Training NCAAF TOTALS models")
        logger.info("=" * 60)

        # Prepare features and target
        X = self.feature_engineer.create_feature_matrix(df, 'totals')
        y = df['total'].values
        feature_names = self.feature_engineer.get_feature_names('totals')

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        models = {}
        metadata = {
            'feature_names': feature_names,
            'training_date': datetime.now().isoformat(),
            'n_train_samples': len(X_train),
            'n_test_samples': len(X_test),
            'training_stats': {}
        }

        # 1. Random Forest
        logger.info("Training Random Forest Totals...")
        rf_model = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
        rf_model.fit(X_train, y_train)
        rf_pred = rf_model.predict(X_test)
        metadata['training_stats']['random_forest'] = self._calculate_regression_metrics(
            y_test, rf_pred, len(X_train)
        )
        models['random_forest'] = rf_model

        # 2. XGBoost
        if xgb:
            logger.info("Training XGBoost Totals...")
            xgb_model = xgb.XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
            xgb_model.fit(X_train, y_train)
            xgb_pred = xgb_model.predict(X_test)
            metadata['training_stats']['xgboost'] = self._calculate_regression_metrics(
                y_test, xgb_pred, len(X_train)
            )
            models['xgboost'] = xgb_model

        # 3. LightGBM
        if lgb:
            logger.info("Training LightGBM Totals...")
            lgb_model = lgb.LGBMRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1)
            lgb_model.fit(X_train, y_train)
            lgb_pred = lgb_model.predict(X_test)
            metadata['training_stats']['lightgbm'] = self._calculate_regression_metrics(
                y_test, lgb_pred, len(X_train)
            )
            models['lightgbm'] = lgb_model

        # 4. Linear Regression
        logger.info("Training Linear Regression Totals...")
        lr_model = LinearRegression()
        lr_model.fit(X_train, y_train)
        lr_pred = lr_model.predict(X_test)
        metadata['training_stats']['linear_regression'] = self._calculate_regression_metrics(
            y_test, lr_pred, len(X_train)
        )
        models['linear_regression'] = lr_model

        # Save models
        for model_name, model in models.items():
            joblib.dump(model, self.output_dir / f"ncaaf_{model_name}_totals_latest.joblib")
            logger.info(f"  [OK] Saved {model_name} totals model")

        # Save metadata
        joblib.dump(metadata, self.output_dir / "ncaaf_totals_metadata_latest.joblib")
        logger.info("  [OK] Saved totals metadata")

        return metadata

    def train_spreads_models(self, df: pd.DataFrame) -> Dict:
        """Train all spreads prediction models"""
        logger.info("=" * 60)
        logger.info("Training NCAAF SPREADS models")
        logger.info("=" * 60)

        X = self.feature_engineer.create_feature_matrix(df, 'spreads')
        y = df['home_margin'].values
        feature_names = self.feature_engineer.get_feature_names('spreads')

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        models = {}
        metadata = {
            'feature_names': feature_names,
            'training_date': datetime.now().isoformat(),
            'n_train_samples': len(X_train),
            'n_test_samples': len(X_test),
            'training_stats': {}
        }

        # Train all models
        rf_model = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
        rf_model.fit(X_train, y_train)
        models['random_forest'] = rf_model
        metadata['training_stats']['random_forest'] = self._calculate_regression_metrics(
            y_test, rf_model.predict(X_test), len(X_train)
        )

        if xgb:
            xgb_model = xgb.XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
            xgb_model.fit(X_train, y_train)
            models['xgboost'] = xgb_model
            metadata['training_stats']['xgboost'] = self._calculate_regression_metrics(
                y_test, xgb_model.predict(X_test), len(X_train)
            )

        if lgb:
            lgb_model = lgb.LGBMRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1)
            lgb_model.fit(X_train, y_train)
            models['lightgbm'] = lgb_model
            metadata['training_stats']['lightgbm'] = self._calculate_regression_metrics(
                y_test, lgb_model.predict(X_test), len(X_train)
            )

        lr_model = LinearRegression()
        lr_model.fit(X_train, y_train)
        models['linear_regression'] = lr_model
        metadata['training_stats']['linear_regression'] = self._calculate_regression_metrics(
            y_test, lr_model.predict(X_test), len(X_train)
        )

        # Save
        for model_name, model in models.items():
            joblib.dump(model, self.output_dir / f"ncaaf_{model_name}_spreads_latest.joblib")
            logger.info(f"  [OK] Saved {model_name} spreads model")

        joblib.dump(metadata, self.output_dir / "ncaaf_spreads_metadata_latest.joblib")
        logger.info("  [OK] Saved spreads metadata")

        return metadata

    def train_moneyline_models(self, df: pd.DataFrame) -> Dict:
        """Train all moneyline prediction models"""
        logger.info("=" * 60)
        logger.info("Training NCAAF MONEYLINE models")
        logger.info("=" * 60)

        X = self.feature_engineer.create_feature_matrix(df, 'moneyline')
        y = df['home_win'].values
        feature_names = self.feature_engineer.get_feature_names('moneyline')

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        models = {}
        metadata = {
            'feature_names': feature_names,
            'training_date': datetime.now().isoformat(),
            'n_train_samples': len(X_train),
            'n_test_samples': len(X_test),
            'training_stats': {}
        }

        # Train classifiers
        rf_model = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
        rf_model.fit(X_train, y_train)
        models['random_forest'] = rf_model
        metadata['training_stats']['random_forest'] = self._calculate_classification_metrics(
            y_test, rf_model.predict(X_test), rf_model.predict_proba(X_test), len(X_train)
        )

        if xgb:
            xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
            xgb_model.fit(X_train, y_train)
            models['xgboost'] = xgb_model
            metadata['training_stats']['xgboost'] = self._calculate_classification_metrics(
                y_test, xgb_model.predict(X_test), xgb_model.predict_proba(X_test), len(X_train)
            )

        if lgb:
            lgb_model = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1)
            lgb_model.fit(X_train, y_train)
            models['lightgbm'] = lgb_model
            metadata['training_stats']['lightgbm'] = self._calculate_classification_metrics(
                y_test, lgb_model.predict(X_test), lgb_model.predict_proba(X_test), len(X_train)
            )

        log_model = LogisticRegression(max_iter=1000, random_state=42)
        log_model.fit(X_train, y_train)
        models['logistic_regression'] = log_model
        metadata['training_stats']['logistic_regression'] = self._calculate_classification_metrics(
            y_test, log_model.predict(X_test), log_model.predict_proba(X_test), len(X_train)
        )

        # Save
        for model_name, model in models.items():
            joblib.dump(model, self.output_dir / f"ncaaf_{model_name}_moneyline_latest.joblib")
            logger.info(f"  [OK] Saved {model_name} moneyline model")

        joblib.dump(metadata, self.output_dir / "ncaaf_moneyline_metadata_latest.joblib")
        logger.info("  [OK] Saved moneyline metadata")

        return metadata

    def _calculate_regression_metrics(self, y_true, y_pred, n_samples) -> Dict:
        """Calculate regression model metrics"""
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)

        # College football-specific metrics (larger point differences)
        errors = np.abs(y_true - y_pred)
        within_7_pts = np.mean(errors <= 7.0)  # Touchdown
        within_14_pts = np.mean(errors <= 14.0)  # Two touchdowns
        within_21_pts = np.mean(errors <= 21.0)  # Three touchdowns

        logger.info(f"    MAE: {mae:.3f} | RMSE: {rmse:.3f} | R²: {r2:.3f}")

        return {
            'mae': float(mae),
            'rmse': float(rmse),
            'r2': float(r2),
            'within_7_pts': float(within_7_pts),
            'within_14_pts': float(within_14_pts),
            'within_21_pts': float(within_21_pts),
            'n_samples': int(n_samples)
        }

    def _calculate_classification_metrics(self, y_true, y_pred, y_proba, n_samples) -> Dict:
        """Calculate classification model metrics"""
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_true, y_proba[:, 1])
        logloss = log_loss(y_true, y_proba)

        logger.info(f"    Accuracy: {accuracy:.3f} | ROC-AUC: {roc_auc:.3f} | Log Loss: {logloss:.3f}")

        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'roc_auc': float(roc_auc),
            'log_loss': float(logloss),
            'n_samples': int(n_samples)
        }


def main():
    parser = argparse.ArgumentParser(description='Train NCAAF prediction models')
    parser.add_argument('--seasons', nargs='+', default=None,
                       help='Seasons to train on (e.g., 2023 2024)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output directory for models')

    args = parser.parse_args()

    # Load training data
    logger.info("Loading NCAAF training data...")
    df = load_ncaaf_training_data(seasons=args.seasons)

    if df.empty:
        logger.error("No training data available. Please check data sources.")
        return

    logger.info(f"Loaded {len(df)} games for training")

    # Train models
    trainer = NCAAFModelTrainer(output_dir=Path(args.output) if args.output else None)

    totals_meta = trainer.train_totals_models(df)
    spreads_meta = trainer.train_spreads_models(df)
    moneyline_meta = trainer.train_moneyline_models(df)

    logger.info("=" * 60)
    logger.info("NCAAF MODEL TRAINING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Models saved to: {trainer.output_dir}")
    logger.info("Total models trained: 12 (4 totals + 4 spreads + 4 moneyline)")


if __name__ == "__main__":
    main()
