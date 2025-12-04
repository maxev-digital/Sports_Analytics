"""
NBA ENHANCED Model Training - 78 Features + 7 Model Types
Extends base training with PyTorch, TFT, CatBoost

Usage:
    python -m backend.ml.training.train_nba_enhanced --seasons 2023 2024 2025
"""

import argparse
import joblib
import logging
import numpy as np
import pandas as pd
import torch
from pathlib import Path
from datetime import datetime
from typing import Dict
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

try:
    import xgboost as xgb
except ImportError:
    xgb = None

try:
    import lightgbm as lgb
except ImportError:
    lgb = None

try:
    import catboost as cb
except ImportError:
    cb = None

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from ml.data_loaders.nba_data_loader import load_nba_training_data
from ml.feature_engineering.nba_features import NBAFeatureEngineer
from ml.enhanced_features.enhanced_nba_features import EnhancedNBAFeatures, add_enhanced_features
from ml.pytorch_models.tabular_net import TabularNet, TabularNetTrainer
from ml.pytorch_models.ensemble_weighter import EnsembleWeighter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Configuration flag
USE_ENHANCED_78_FEATURE_PIPELINE = True
USE_NEURAL_ENSEMBLE = True


class NBAEnhancedModelTrainer:
    """Train all 7 NBA model types with 78 features"""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(__file__).parent.parent / "models"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.feature_engineer = NBAFeatureEngineer()
        self.enhanced_features = EnhancedNBAFeatures()
        self.scaler = StandardScaler()

    def create_enhanced_feature_matrix(self, df: pd.DataFrame, bet_type: str) -> np.ndarray:
        """Create 78-feature matrix by combining base + enhanced features"""
        if USE_ENHANCED_78_FEATURE_PIPELINE:
            # Add enhanced columns to dataframe
            df = add_enhanced_features(df)

            # Get base features (42)
            base_X = self.feature_engineer.create_feature_matrix(df, bet_type)

            # Get enhanced features (36)
            enhanced_X = np.array([
                self.enhanced_features.get_enhanced_features(row)
                for _, row in df.iterrows()
            ])

            # Combine to 78 features
            X = np.hstack([base_X, enhanced_X])
            logger.info(f"Created enhanced feature matrix: {X.shape} features")
            return X
        else:
            return self.feature_engineer.create_feature_matrix(df, bet_type)

    def train_all_models(self, df: pd.DataFrame, bet_type: str = 'totals') -> Dict:
        """Train all 7 model types"""
        logger.info("=" * 70)
        logger.info(f"ENHANCED NBA TRAINING - {bet_type.upper()} - 78 Features + 7 Models")
        logger.info("=" * 70)

        # Prepare features
        X = self.create_enhanced_feature_matrix(df, bet_type)

        if bet_type == 'totals':
            y = df['total'].values
        elif bet_type == 'spreads':
            y = df['home_margin'].values
        elif bet_type == 'moneyline':
            y = (df['home_margin'] > 0).astype(int).values

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )

        models = {}
        predictions = {}
        metadata = {
            'n_features': X.shape[1],
            'feature_pipeline': '78_enhanced' if USE_ENHANCED_78_FEATURE_PIPELINE else '42_base',
            'training_date': datetime.now().isoformat(),
            'n_train_samples': len(X_train),
            'n_test_samples': len(X_test),
            'model_stats': {}
        }

        is_classifier = bet_type == 'moneyline'

        # 1. Random Forest
        logger.info("Training Random Forest...")
        if is_classifier:
            rf = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
        else:
            rf = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        predictions['random_forest'] = rf.predict(X_test)
        models['random_forest'] = rf
        metadata['model_stats']['random_forest'] = self._calc_metrics(y_test, predictions['random_forest'], is_classifier)

        # 2. XGBoost
        if xgb:
            logger.info("Training XGBoost...")
            if is_classifier:
                xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
            else:
                xgb_model = xgb.XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
            xgb_model.fit(X_train, y_train)
            predictions['xgboost'] = xgb_model.predict(X_test)
            models['xgboost'] = xgb_model
            metadata['model_stats']['xgboost'] = self._calc_metrics(y_test, predictions['xgboost'], is_classifier)

        # 3. LightGBM
        if lgb:
            logger.info("Training LightGBM...")
            if is_classifier:
                lgb_model = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1)
            else:
                lgb_model = lgb.LGBMRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1)
            lgb_model.fit(X_train, y_train)
            predictions['lightgbm'] = lgb_model.predict(X_test)
            models['lightgbm'] = lgb_model
            metadata['model_stats']['lightgbm'] = self._calc_metrics(y_test, predictions['lightgbm'], is_classifier)

        # 4. Linear/Logistic Regression
        logger.info("Training Linear Regression...")
        if is_classifier:
            lr = LogisticRegression(max_iter=1000, random_state=42)
        else:
            lr = LinearRegression()
        lr.fit(X_train, y_train)
        predictions['linear'] = lr.predict(X_test)
        models['linear'] = lr
        metadata['model_stats']['linear'] = self._calc_metrics(y_test, predictions['linear'], is_classifier)

        # 5. CatBoost
        if cb:
            logger.info("Training CatBoost...")
            if is_classifier:
                cb_model = cb.CatBoostClassifier(iterations=100, depth=6, learning_rate=0.1, random_state=42, verbose=0)
            else:
                cb_model = cb.CatBoostRegressor(iterations=100, depth=6, learning_rate=0.1, random_state=42, verbose=0)
            cb_model.fit(X_train, y_train)
            predictions['catboost'] = cb_model.predict(X_test)
            models['catboost'] = cb_model
            metadata['model_stats']['catboost'] = self._calc_metrics(y_test, predictions['catboost'], is_classifier)

        # 6. PyTorch TabularNet
        logger.info("Training PyTorch TabularNet...")
        pytorch_trainer = TabularNetTrainer(input_dim=X.shape[1])
        pytorch_model = pytorch_trainer.train(X_train, y_train, epochs=50)
        predictions['pytorch'] = pytorch_trainer.predict(X_test)
        models['pytorch'] = pytorch_model
        metadata['model_stats']['pytorch'] = self._calc_metrics(y_test, predictions['pytorch'], is_classifier)

        # 7. Neural Ensemble (learns optimal weights)
        if USE_NEURAL_ENSEMBLE and len(predictions) >= 4:
            logger.info("Training Neural Ensemble Weighter...")
            # Stack all predictions
            base_preds = np.column_stack([predictions[k] for k in sorted(predictions.keys())])

            ensemble = EnsembleWeighter(n_models=len(predictions))
            ensemble_preds = self._train_ensemble(ensemble, base_preds, y_test, epochs=100)
            predictions['neural_ensemble'] = ensemble_preds
            models['ensemble_weighter'] = ensemble
            metadata['model_stats']['neural_ensemble'] = self._calc_metrics(y_test, ensemble_preds, is_classifier)

            # Log learned weights
#             weights = torch.softmax(ensemble.weights, dim=0).detach().numpy()
#             logger.info(f"Learned ensemble weights: {dict(zip(sorted(predictions.keys())[:-1], weights.round(3)))}")

        # Save all models
        for name, model in models.items():
            if name == 'pytorch':
                torch.save(model.state_dict(), self.output_dir / f"nba_pytorch_{bet_type}_latest.pt")
            elif name == 'ensemble_weighter':
                torch.save(model.state_dict(), self.output_dir / f"nba_ensemble_{bet_type}_latest.pt")
            else:
                joblib.dump(model, self.output_dir / f"nba_{name}_{bet_type}_enhanced.joblib")

        # Save scaler
        joblib.dump(self.scaler, self.output_dir / f"nba_scaler_{bet_type}_enhanced.joblib")

        # Save metadata
        joblib.dump(metadata, self.output_dir / f"nba_{bet_type}_enhanced_metadata.joblib")

        logger.info(f"\n{'='*70}")
        logger.info("MODEL PERFORMANCE SUMMARY:")
        for model_name, stats in metadata['model_stats'].items():
            if is_classifier:
                logger.info(f"  {model_name}: Accuracy={stats.get('accuracy', 0):.3f}")
            else:
                logger.info(f"  {model_name}: MAE={stats.get('mae', 0):.3f}")
        logger.info(f"{'='*70}")

        return metadata

    def _train_ensemble(self, ensemble, base_preds, y_true, epochs=100) -> np.ndarray:
        """Train the neural ensemble weighter"""
        optimizer = torch.optim.Adam(ensemble.parameters(), lr=0.01)
        X_tensor = torch.FloatTensor(base_preds)
        # Create dummy model accuracies (uniform for all models)
        n_models = base_preds.shape[1]
        model_accs = torch.ones_like(X_tensor) / n_models
        y_tensor = torch.FloatTensor(y_true)

        for epoch in range(epochs):
            optimizer.zero_grad()
            preds, _ = ensemble(X_tensor, model_accs)
            loss = torch.nn.functional.mse_loss(preds, y_tensor)
            loss.backward()
            optimizer.step()

        with torch.no_grad():
            final_preds, _ = ensemble(X_tensor, model_accs)
            return final_preds.numpy()

    def _calc_metrics(self, y_true, y_pred, is_classifier=False) -> Dict:
        """Calculate model performance metrics"""
        if is_classifier:
            y_pred_binary = (y_pred > 0.5).astype(int) if y_pred.dtype == float else y_pred
            return {
                'accuracy': float((y_pred_binary == y_true).mean()),
                'n_samples': len(y_true)
            }
        else:
            return {
                'mae': float(mean_absolute_error(y_true, y_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
                'r2': float(r2_score(y_true, y_pred)),
                'n_samples': len(y_true)
            }


def main():
    parser = argparse.ArgumentParser(description='Train NBA Enhanced Models')
    parser.add_argument('--seasons', nargs='+', type=str, default=['2022-23', '2023-24', '2024-25'])
    parser.add_argument('--bet-types', nargs='+', default=['totals', 'spreads', 'moneyline'])
    args = parser.parse_args()

    trainer = NBAEnhancedModelTrainer()

    logger.info(f"Loading training data for seasons: {args.seasons}")
    df = load_nba_training_data(seasons=args.seasons)
    logger.info(f"Loaded {len(df)} training samples")

    for bet_type in args.bet_types:
        trainer.train_all_models(df, bet_type=bet_type)

    logger.info("\n" + "=" * 70)
    logger.info("ENHANCED TRAINING COMPLETE - 78 Features + 7 Model Types")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
