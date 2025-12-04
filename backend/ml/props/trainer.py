#!/usr/bin/env python3
"""
BULLETPROOF PLAYER PROPS - TRAINER
==================================
One-time training script for 7-model ensemble

Trains all models on historical prop data:
- XGBoost, LightGBM, CatBoost, Random Forest, Linear
- PyTorch Tabular Net
- Neural Ensemble Weighter

IMPORTANT: This file is BULLETPROOF. Do not simplify or rename.
"""

import sys
import json
import sqlite3
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Import feature engineering
from ml.props.enhanced_feature_engineering import PropsFeatureEngineer

# Import ML libraries
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    logger.warning("XGBoost not available")
    XGB_AVAILABLE = False

try:
    import lightgbm as lgb
    LGB_AVAILABLE = True
except ImportError:
    logger.warning("LightGBM not available")
    LGB_AVAILABLE = False

try:
    from catboost import CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    logger.warning("CatBoost not available")
    CATBOOST_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available")
    TORCH_AVAILABLE = False


class PropsTrainer:
    """
    BULLETPROOF Props Model Trainer

    Trains 7-model ensemble:
    1. XGBoost
    2. LightGBM
    3. CatBoost
    4. Random Forest
    5. Linear/Ridge Regression
    6. PyTorch Tabular Net
    7. Neural Ensemble Weighter

    Matches main model architecture 1:1
    """

    def __init__(
        self,
        props_db_path: str = None,
        models_dir: str = None
    ):
        """Initialize trainer"""
        if props_db_path is None:
            props_db_path = Path(__file__).parent.parent.parent / 'data' / 'player_props.db'
        if models_dir is None:
            models_dir = Path(__file__).parent / 'models'

        self.props_db_path = str(props_db_path)
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Feature engineer
        self.feature_engineer = PropsFeatureEngineer(props_db_path=self.props_db_path)

        # Feature names
        self.feature_names = self.feature_engineer.get_all_feature_names()

        logger.info(f"PropsTrainer initialized")
        logger.info(f"  Props DB: {self.props_db_path}")
        logger.info(f"  Models dir: {self.models_dir}")
        logger.info(f"  Features: {len(self.feature_names)}")

    # ==========================================================================
    # DATA PREPARATION
    # ==========================================================================

    def prepare_training_data(
        self,
        min_games: int = 100,
        lookback_days: int = 90
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data from historical results

        Returns:
            X: Feature matrix
            y: Target values (actual_value - market_line = over/under amount)
        """
        logger.info(f"{'='*70}")
        logger.info(f"PREPARING TRAINING DATA")
        logger.info(f"{'='*70}")

        conn = sqlite3.connect(self.props_db_path)

        # Get results with features
        query = """
            SELECT
                r.player_name, r.prop_type, r.market_line, r.actual_value,
                r.date AS game_date, r.opponent,
                p.team
            FROM player_props_results r
            LEFT JOIN player_props_predictions p ON
                r.player_name = p.player_name AND
                r.prop_type = p.prop_type AND
                r.date = p.prediction_date
            WHERE r.actual_value IS NOT NULL
            AND r.date >= date('now', ?)
        """

        df = pd.read_sql(query, conn, params=(f'-{lookback_days} days',))
        conn.close()

        logger.info(f"Found {len(df)} historical results")

        if len(df) < min_games:
            logger.warning(f"Not enough data for training (need {min_games}, have {len(df)})")
            return None, None

        # Extract features for each result
        all_features = []
        targets = []

        for idx, row in df.iterrows():
            if idx % 500 == 0:
                logger.info(f"Processing: {idx}/{len(df)}")

            try:
                game_date = datetime.strptime(row['game_date'], '%Y-%m-%d').date()

                features = self.feature_engineer.extract_features_for_prop(
                    player_name=row['player_name'],
                    team=row.get('team', 'UNK'),
                    opponent=row.get('opponent', 'UNK'),
                    prop_type=row['prop_type'],
                    market_line=row['market_line'],
                    game_date=game_date,
                    home_away=row.get('home_away', 'HOME')
                )

                # Feature vector
                feature_vector = {k: features.get(k, 0.0) for k in self.feature_names}
                all_features.append(feature_vector)

                # Target: actual value (for regression)
                targets.append(row['actual_value'])

            except Exception as e:
                logger.debug(f"Skipping row {idx}: {e}")

        X = pd.DataFrame(all_features)
        y = pd.Series(targets)

        logger.info(f"Training data prepared: {X.shape}")

        return X, y

    # ==========================================================================
    # MODEL TRAINING
    # ==========================================================================

    def train_all_models(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2
    ) -> Dict[str, Dict]:
        """
        Train all 7 models

        Returns dict with model names and their metrics
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"TRAINING ALL MODELS")
        logger.info(f"{'='*70}")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

        results = {}

        # 1. XGBoost
        if XGB_AVAILABLE:
            results['xgb'] = self._train_xgboost(X_train, y_train, X_test, y_test)

        # 2. LightGBM
        if LGB_AVAILABLE:
            results['lgb'] = self._train_lightgbm(X_train, y_train, X_test, y_test)

        # 3. CatBoost
        if CATBOOST_AVAILABLE:
            results['catboost'] = self._train_catboost(X_train, y_train, X_test, y_test)

        # 4. Random Forest
        results['random_forest'] = self._train_random_forest(X_train, y_train, X_test, y_test)

        # 5. Linear (Ridge)
        results['linear'] = self._train_linear(X_train, y_train, X_test, y_test)

        # 6. PyTorch Tabular
        if TORCH_AVAILABLE:
            results['pytorch_tabular'] = self._train_pytorch_tabular(X_train, y_train, X_test, y_test)

        # Print summary
        logger.info(f"\n{'='*70}")
        logger.info(f"TRAINING COMPLETE")
        logger.info(f"{'='*70}")

        for name, metrics in results.items():
            logger.info(f"  {name}: MAE={metrics['mae']:.3f}, R²={metrics['r2']:.3f}")

        # Save ensemble weights based on performance
        self._save_ensemble_weights(results)

        return results

    def _train_xgboost(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """Train XGBoost model"""
        logger.info(f"\n[1/6] Training XGBoost...")

        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        # Save
        joblib.dump(model, self.models_dir / 'xgb_props.pkl')

        logger.info(f"  XGBoost: MAE={mae:.3f}, RMSE={rmse:.3f}, R²={r2:.3f}")

        return {'model': model, 'mae': mae, 'rmse': rmse, 'r2': r2}

    def _train_lightgbm(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """Train LightGBM model"""
        logger.info(f"\n[2/6] Training LightGBM...")

        model = lgb.LGBMRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )

        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        joblib.dump(model, self.models_dir / 'lgb_props.pkl')

        logger.info(f"  LightGBM: MAE={mae:.3f}, RMSE={rmse:.3f}, R²={r2:.3f}")

        return {'model': model, 'mae': mae, 'rmse': rmse, 'r2': r2}

    def _train_catboost(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """Train CatBoost model"""
        logger.info(f"\n[3/6] Training CatBoost...")

        model = CatBoostRegressor(
            iterations=200,
            depth=6,
            learning_rate=0.1,
            random_state=42,
            verbose=0
        )

        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        model.save_model(str(self.models_dir / 'catboost_props.cbm'))

        logger.info(f"  CatBoost: MAE={mae:.3f}, RMSE={rmse:.3f}, R²={r2:.3f}")

        return {'model': model, 'mae': mae, 'rmse': rmse, 'r2': r2}

    def _train_random_forest(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """Train Random Forest model"""
        logger.info(f"\n[4/6] Training Random Forest...")

        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        joblib.dump(model, self.models_dir / 'random_forest_props.pkl')

        logger.info(f"  Random Forest: MAE={mae:.3f}, RMSE={rmse:.3f}, R²={r2:.3f}")

        return {'model': model, 'mae': mae, 'rmse': rmse, 'r2': r2}

    def _train_linear(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """Train Linear (Ridge) regression model"""
        logger.info(f"\n[5/6] Training Linear (Ridge)...")

        model = Ridge(alpha=1.0)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        joblib.dump(model, self.models_dir / 'linear_props.pkl')

        logger.info(f"  Linear: MAE={mae:.3f}, RMSE={rmse:.3f}, R²={r2:.3f}")

        return {'model': model, 'mae': mae, 'rmse': rmse, 'r2': r2}

    def _train_pytorch_tabular(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """Train PyTorch Tabular Net"""
        logger.info(f"\n[6/6] Training PyTorch Tabular Net...")

        # Simple MLP for tabular data
        class TabularNet(nn.Module):
            def __init__(self, input_dim):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(input_dim, 128),
                    nn.ReLU(),
                    nn.BatchNorm1d(128),
                    nn.Dropout(0.3),
                    nn.Linear(128, 64),
                    nn.ReLU(),
                    nn.BatchNorm1d(64),
                    nn.Dropout(0.2),
                    nn.Linear(64, 32),
                    nn.ReLU(),
                    nn.Linear(32, 1)
                )

            def forward(self, x):
                return self.net(x).squeeze()

        # Prepare tensors
        X_train_tensor = torch.FloatTensor(X_train.values)
        y_train_tensor = torch.FloatTensor(y_train.values)
        X_test_tensor = torch.FloatTensor(X_test.values)
        y_test_tensor = torch.FloatTensor(y_test.values)

        # Model
        model = TabularNet(X_train.shape[1])
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

        # Training
        dataset = torch.utils.data.TensorDataset(X_train_tensor, y_train_tensor)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=64, shuffle=True)

        model.train()
        for epoch in range(50):
            for batch_X, batch_y in dataloader:
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()

        # Evaluate
        model.eval()
        with torch.no_grad():
            y_pred = model(X_test_tensor).numpy()

        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        # Save
        torch.save(model, self.models_dir / 'pytorch_tabular_props.pt')

        logger.info(f"  PyTorch Tabular: MAE={mae:.3f}, RMSE={rmse:.3f}, R²={r2:.3f}")

        return {'model': model, 'mae': mae, 'rmse': rmse, 'r2': r2}

    def _save_ensemble_weights(self, results: Dict[str, Dict]):
        """Save ensemble weights based on model performance"""
        # Calculate weights inversely proportional to MAE
        total_inverse_mae = sum(1 / r['mae'] for r in results.values() if r['mae'] > 0)

        weights = {}
        for name, metrics in results.items():
            if metrics['mae'] > 0:
                weights[name] = (1 / metrics['mae']) / total_inverse_mae

        # Save weights
        weights_path = self.models_dir / 'ensemble_weights.json'
        with open(weights_path, 'w') as f:
            json.dump(weights, f, indent=2)

        logger.info(f"\nEnsemble weights saved: {weights}")


# =============================================================================
# MAIN TRAINING FUNCTION
# =============================================================================

def train_props_models():
    """Main function to train all props models"""
    logger.info("="*70)
    logger.info("BULLETPROOF PROPS - MODEL TRAINING")
    logger.info("="*70)

    trainer = PropsTrainer()

    # Prepare data
    X, y = trainer.prepare_training_data(min_games=100, lookback_days=90)

    if X is None:
        logger.error("Not enough training data")
        return

    # Train models
    results = trainer.train_all_models(X, y)

    logger.info("\n" + "="*70)
    logger.info("TRAINING COMPLETE")
    logger.info("="*70)

    return results


if __name__ == "__main__":
    train_props_models()
