"""
CatBoost wrapper for categorical features
Handles team names, referee crews, etc.
"""
from catboost import CatBoostRegressor, CatBoostClassifier
import numpy as np
import joblib

class SportsCatBoost:
    def __init__(self, task='regression', cat_features=None):
        self.task = task
        self.cat_features = cat_features or []

        if task == 'regression':
            self.model = CatBoostRegressor(
                iterations=500,
                learning_rate=0.05,
                depth=6,
                cat_features=self.cat_features,
                verbose=False,
                random_seed=42
            )
        else:
            self.model = CatBoostClassifier(
                iterations=500,
                learning_rate=0.05,
                depth=6,
                cat_features=self.cat_features,
                verbose=False,
                random_seed=42
            )

    def train(self, X_train, y_train, X_val=None, y_val=None):
        """Train CatBoost model"""
        if X_val is not None and y_val is not None:
            self.model.fit(
                X_train, y_train,
                eval_set=(X_val, y_val),
                early_stopping_rounds=50,
                verbose=False
            )
        else:
            self.model.fit(X_train, y_train, verbose=False)

        return self.model

    def predict(self, X):
        """Make predictions"""
        return self.model.predict(X)

    def save(self, path):
        """Save model"""
        self.model.save_model(path)

    def load(self, path):
        """Load model"""
        if self.task == 'regression':
            self.model = CatBoostRegressor()
        else:
            self.model = CatBoostClassifier()
        self.model.load_model(path)
        return self.model
