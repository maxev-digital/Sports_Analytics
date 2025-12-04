"""
Enhanced Multi-Model Trainer
Trains all 7 model types in one coordinated workflow
"""
import sys
import os
import numpy as np
import joblib
import torch
from pathlib import Path
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

sys.path.append('/root/sporttrader/backend')

from ml.pytorch_models.tabular_net import TabularNetTrainer
from ml.pytorch_models.catboost_model import SportsCatBoost
from ml.pytorch_models.ensemble_weighter import EnsembleWeighterTrainer

class EnhancedMultiModelTrainer:
    def __init__(self, sport, bet_type='totals', models_dir='/root/sporttrader/backend/ml/models'):
        self.sport = sport.lower()
        self.bet_type = bet_type
        self.models_dir = Path(models_dir)
        self.models = {}

    def train_all_models(self, X_train, y_train, X_val=None, y_val=None):
        """Train all 7 model types"""
        print(f"Training all 7 models for {self.sport} {self.bet_type}...")

        if X_val is None:
            X_train, X_val, y_train, y_val = train_test_split(
                X_train, y_train, test_size=0.2, random_state=42
            )

        # 1. XGBoost
        print("[1/7] Training XGBoost...")
        xgb = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42)
        xgb.fit(X_train, y_train)
        self.models['xgboost'] = xgb
        joblib.dump(xgb, self.models_dir / f"{self.sport}_xgboost_{self.bet_type}_latest.joblib")

        # 2. LightGBM
        print("[2/7] Training LightGBM...")
        lgb = LGBMRegressor(n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42, verbose=-1)
        lgb.fit(X_train, y_train)
        self.models['lightgbm'] = lgb
        joblib.dump(lgb, self.models_dir / f"{self.sport}_lightgbm_{self.bet_type}_latest.joblib")

        # 3. Random Forest
        print("[3/7] Training Random Forest...")
        rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
        rf.fit(X_train, y_train)
        self.models['random_forest'] = rf
        joblib.dump(rf, self.models_dir / f"{self.sport}_random_forest_{self.bet_type}_latest.joblib")

        # 4. Linear Regression
        print("[4/7] Training Linear Regression...")
        lin = LinearRegression()
        lin.fit(X_train, y_train)
        self.models['linear'] = lin
        joblib.dump(lin, self.models_dir / f"{self.sport}_linear_regression_{self.bet_type}_latest.joblib")

        # 5. PyTorch TabularNet
        print("[5/7] Training PyTorch TabularNet...")
        try:
            pytorch_trainer = TabularNetTrainer(input_dim=X_train.shape[1], lr=0.001)
            pytorch_trainer.train(X_train, y_train, epochs=50, batch_size=32)
            self.models['pytorch_tabular'] = pytorch_trainer
            pytorch_trainer.save(self.models_dir / f"{self.sport}_pytorch_tabular_{self.bet_type}_latest.pt")
        except Exception as e:
            print(f"  PyTorch training failed: {e}")

        # 6. CatBoost
        print("[6/7] Training CatBoost...")
        try:
            catboost = SportsCatBoost(task='regression')
            catboost.train(X_train, y_train, X_val, y_val)
            self.models['catboost'] = catboost
            catboost.save(str(self.models_dir / f"{self.sport}_catboost_{self.bet_type}_latest.cbm"))
        except Exception as e:
            print(f"  CatBoost training failed: {e}")

        # 7. Neural Ensemble Weighter
        print("[7/7] Training Neural Ensemble Weighter...")
        try:
            if len(self.models) >= 3:
                # Get predictions from all models on validation set
                all_preds = []
                for name, model in self.models.items():
                    if name == 'pytorch_tabular':
                        preds = model.predict(X_val)
                    elif name == 'catboost':
                        preds = model.predict(X_val)
                    else:
                        preds = model.predict(X_val)
                    all_preds.append(preds)

                all_preds = np.array(all_preds).T
                # Default accuracies
                accuracies = np.ones((len(X_val), len(self.models))) * 0.55

                ensemble_trainer = EnsembleWeighterTrainer(n_models=len(self.models))
                ensemble_trainer.train(all_preds, accuracies, y_val, epochs=30)
                self.models['neural_ensemble'] = ensemble_trainer
                ensemble_trainer.save(self.models_dir / f"{self.sport}_neural_ensemble_{self.bet_type}_latest.pt")
        except Exception as e:
            print(f"  Neural Ensemble training failed: {e}")

        print(f"✓ Trained {len(self.models)} models successfully")
        return self.models

