"""
NBA Player Props - ML Model Training Pipeline
Trains XGBoost, LightGBM, Random Forest, and Ensemble models

Usage:
    python backend/ml/models/nba_props_trainer.py --prop-type points
    python backend/ml/models/nba_props_trainer.py --prop-type all
"""

import sys
import sqlite3
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
import argparse

# ML imports
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
import lightgbm as lgb

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml.feature_engineering.nba_props_features import NBAPropsFeatureEngineer


class NBAPropsModelTrainer:
    """
    Trains ML models to predict NBA player props outcomes
    """

    def __init__(self, db_path: str = "data/player_props.db"):
        self.db_path = db_path
        self.feature_engineer = NBAPropsFeatureEngineer(db_path)
        self.models = {}
        self.feature_names = []
        self.models_dir = Path("ml/models/trained/nba_props")
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def prepare_training_data(
        self,
        prop_type: str,
        min_samples: int = 100,
        test_size: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Prepare training data from database

        Args:
            prop_type: Type of prop ('points', 'rebounds', 'assists', etc.)
            min_samples: Minimum samples required for training
            test_size: Fraction of data for testing

        Returns:
            X_train, X_test, y_train, y_test
        """
        print(f"\n{'='*70}")
        print(f"PREPARING TRAINING DATA - {prop_type.upper()}")
        print(f"{'='*70}\n")

        # Get all graded props from database
        conn = sqlite3.connect(self.db_path)

        query = """
            SELECT
                r.date,
                r.player_id,
                r.player_name,
                r.team,
                r.opponent,
                r.prop_type,
                r.market_line,
                r.actual_value,
                r.hit,
                l.home_away
            FROM player_props_results r
            JOIN player_props_lines l
                ON r.date = l.date
                AND r.player_id = l.player_id
                AND r.prop_type = l.prop_type
            WHERE r.prop_type = ?
            ORDER BY r.date DESC
        """

        df = pd.read_sql_query(query, conn, params=(prop_type,))
        conn.close()

        print(f"[1/5] Loaded {len(df)} {prop_type} props from database")

        if len(df) < min_samples:
            raise ValueError(
                f"Insufficient data: {len(df)} samples (need {min_samples})"
            )

        # Extract features for each prop
        print(f"[2/5] Extracting features...")
        all_features = []

        for idx, row in df.iterrows():
            if (idx + 1) % 500 == 0:
                print(f"  Progress: {idx + 1}/{len(df)} ({(idx+1)/len(df)*100:.1f}%)")

            try:
                features = self.feature_engineer.extract_features_for_prop(
                    player_name=row['player_name'],
                    team=row['team'],
                    opponent=row['opponent'],
                    prop_type=row['prop_type'],
                    market_line=row['market_line'],
                    game_date=pd.to_datetime(row['date']).date(),
                    home_away=row['home_away']
                )

                # Add target variable
                features['target'] = int(row['hit'])
                all_features.append(features)

            except Exception as e:
                print(f"  [WARN] Failed to extract features for row {idx}: {e}")

        features_df = pd.DataFrame(all_features)
        print(f"  [OK] Extracted features for {len(features_df)} props")

        # Remove non-numeric and metadata columns
        exclude_cols = ['player_name', 'team', 'opponent', 'prop_type',
                       'market_line', 'game_date', 'game_id', 'target']

        feature_cols = [col for col in features_df.columns if col not in exclude_cols]

        # Handle missing values
        features_df[feature_cols] = features_df[feature_cols].fillna(0)

        X = features_df[feature_cols]
        y = features_df['target']

        self.feature_names = feature_cols

        print(f"\n[3/5] Dataset summary:")
        print(f"  Total samples: {len(X)}")
        print(f"  Features: {len(feature_cols)}")
        print(f"  Hit rate: {y.mean()*100:.1f}%")
        print(f"  Feature names: {feature_cols[:10]}... (showing first 10)")

        # Train/test split
        print(f"\n[4/5] Splitting data (test_size={test_size})...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        print(f"  Training set: {len(X_train)} samples ({y_train.mean()*100:.1f}% hit rate)")
        print(f"  Test set: {len(X_test)} samples ({y_test.mean()*100:.1f}% hit rate)")

        print(f"\n[5/5] Data preparation complete!\n")

        return X_train, X_test, y_train, y_test

    def train_xgboost(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """
        Train XGBoost model
        """
        print(f"\n{'='*70}")
        print("TRAINING XGBOOST MODEL")
        print(f"{'='*70}\n")

        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'max_depth': 6,
            'learning_rate': 0.05,
            'n_estimators': 200,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }

        model = xgb.XGBClassifier(**params)

        print(f"[1/2] Training XGBoost...")
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

        # Evaluate
        train_pred = model.predict(X_train)
        train_prob = model.predict_proba(X_train)[:, 1]
        test_pred = model.predict(X_test)
        test_prob = model.predict_proba(X_test)[:, 1]

        results = {
            'model': model,
            'train_accuracy': accuracy_score(y_train, train_pred),
            'test_accuracy': accuracy_score(y_test, test_pred),
            'train_auc': roc_auc_score(y_train, train_prob),
            'test_auc': roc_auc_score(y_test, test_prob),
            'train_logloss': log_loss(y_train, train_prob),
            'test_logloss': log_loss(y_test, test_prob)
        }

        print(f"[2/2] XGBoost Results:")
        print(f"  Train Accuracy: {results['train_accuracy']*100:.2f}%")
        print(f"  Test Accuracy:  {results['test_accuracy']*100:.2f}%")
        print(f"  Test AUC:       {results['test_auc']:.4f}")
        print(f"  Test LogLoss:   {results['test_logloss']:.4f}")

        return results

    def train_lightgbm(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """
        Train LightGBM model
        """
        print(f"\n{'='*70}")
        print("TRAINING LIGHTGBM MODEL")
        print(f"{'='*70}\n")

        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'max_depth': 6,
            'learning_rate': 0.05,
            'n_estimators': 200,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'verbose': -1
        }

        model = lgb.LGBMClassifier(**params)

        print(f"[1/2] Training LightGBM...")
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)])

        # Evaluate
        train_pred = model.predict(X_train)
        train_prob = model.predict_proba(X_train)[:, 1]
        test_pred = model.predict(X_test)
        test_prob = model.predict_proba(X_test)[:, 1]

        results = {
            'model': model,
            'train_accuracy': accuracy_score(y_train, train_pred),
            'test_accuracy': accuracy_score(y_test, test_pred),
            'train_auc': roc_auc_score(y_train, train_prob),
            'test_auc': roc_auc_score(y_test, test_prob),
            'train_logloss': log_loss(y_train, train_prob),
            'test_logloss': log_loss(y_test, test_prob)
        }

        print(f"[2/2] LightGBM Results:")
        print(f"  Train Accuracy: {results['train_accuracy']*100:.2f}%")
        print(f"  Test Accuracy:  {results['test_accuracy']*100:.2f}%")
        print(f"  Test AUC:       {results['test_auc']:.4f}")
        print(f"  Test LogLoss:   {results['test_logloss']:.4f}")

        return results

    def train_random_forest(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """
        Train Random Forest model
        """
        print(f"\n{'='*70}")
        print("TRAINING RANDOM FOREST MODEL")
        print(f"{'='*70}\n")

        params = {
            'n_estimators': 200,
            'max_depth': 10,
            'min_samples_split': 10,
            'min_samples_leaf': 5,
            'random_state': 42,
            'n_jobs': -1
        }

        model = RandomForestClassifier(**params)

        print(f"[1/2] Training Random Forest...")
        model.fit(X_train, y_train)

        # Evaluate
        train_pred = model.predict(X_train)
        train_prob = model.predict_proba(X_train)[:, 1]
        test_pred = model.predict(X_test)
        test_prob = model.predict_proba(X_test)[:, 1]

        results = {
            'model': model,
            'train_accuracy': accuracy_score(y_train, train_pred),
            'test_accuracy': accuracy_score(y_test, test_pred),
            'train_auc': roc_auc_score(y_train, train_prob),
            'test_auc': roc_auc_score(y_test, test_prob),
            'train_logloss': log_loss(y_train, train_prob),
            'test_logloss': log_loss(y_test, test_prob)
        }

        print(f"[2/2] Random Forest Results:")
        print(f"  Train Accuracy: {results['train_accuracy']*100:.2f}%")
        print(f"  Test Accuracy:  {results['test_accuracy']*100:.2f}%")
        print(f"  Test AUC:       {results['test_auc']:.4f}")
        print(f"  Test LogLoss:   {results['test_logloss']:.4f}")

        return results

    def train_logistic_regression(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """
        Train Logistic Regression (baseline model)
        """
        print(f"\n{'='*70}")
        print("TRAINING LOGISTIC REGRESSION (BASELINE)")
        print(f"{'='*70}\n")

        model = LogisticRegression(max_iter=1000, random_state=42)

        print(f"[1/2] Training Logistic Regression...")
        model.fit(X_train, y_train)

        # Evaluate
        train_pred = model.predict(X_train)
        train_prob = model.predict_proba(X_train)[:, 1]
        test_pred = model.predict(X_test)
        test_prob = model.predict_proba(X_test)[:, 1]

        results = {
            'model': model,
            'train_accuracy': accuracy_score(y_train, train_pred),
            'test_accuracy': accuracy_score(y_test, test_pred),
            'train_auc': roc_auc_score(y_train, train_prob),
            'test_auc': roc_auc_score(y_test, test_prob),
            'train_logloss': log_loss(y_train, train_prob),
            'test_logloss': log_loss(y_test, test_prob)
        }

        print(f"[2/2] Logistic Regression Results:")
        print(f"  Train Accuracy: {results['train_accuracy']*100:.2f}%")
        print(f"  Test Accuracy:  {results['test_accuracy']*100:.2f}%")
        print(f"  Test AUC:       {results['test_auc']:.4f}")
        print(f"  Test LogLoss:   {results['test_logloss']:.4f}")

        return results

    def train_ensemble(
        self,
        xgb_results: Dict,
        lgb_results: Dict,
        rf_results: Dict,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """
        Create ensemble model (average of all models)
        """
        print(f"\n{'='*70}")
        print("CREATING ENSEMBLE MODEL")
        print(f"{'='*70}\n")

        # Get predictions from all models
        xgb_prob = xgb_results['model'].predict_proba(X_test)[:, 1]
        lgb_prob = lgb_results['model'].predict_proba(X_test)[:, 1]
        rf_prob = rf_results['model'].predict_proba(X_test)[:, 1]

        # Average probabilities
        ensemble_prob = (xgb_prob + lgb_prob + rf_prob) / 3
        ensemble_pred = (ensemble_prob >= 0.5).astype(int)

        results = {
            'test_accuracy': accuracy_score(y_test, ensemble_pred),
            'test_auc': roc_auc_score(y_test, ensemble_prob),
            'test_logloss': log_loss(y_test, ensemble_prob)
        }

        print(f"Ensemble Results:")
        print(f"  Test Accuracy: {results['test_accuracy']*100:.2f}%")
        print(f"  Test AUC:      {results['test_auc']:.4f}")
        print(f"  Test LogLoss:  {results['test_logloss']:.4f}")

        return results

    def save_models(self, prop_type: str, models: Dict):
        """
        Save trained models to disk
        """
        print(f"\n{'='*70}")
        print("SAVING MODELS")
        print(f"{'='*70}\n")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for model_name, results in models.items():
            if 'model' not in results:
                continue

            filename = f"{prop_type}_{model_name}_{timestamp}.pkl"
            filepath = self.models_dir / filename

            model_data = {
                'model': results['model'],
                'feature_names': self.feature_names,
                'prop_type': prop_type,
                'trained_date': datetime.now().isoformat(),
                'test_accuracy': results.get('test_accuracy'),
                'test_auc': results.get('test_auc')
            }

            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)

            print(f"  [OK] Saved {model_name}: {filepath}")

        # Save latest symlinks
        for model_name in models.keys():
            if 'model' not in models[model_name]:
                continue
            latest_path = self.models_dir / f"{prop_type}_{model_name}_latest.pkl"
            if latest_path.exists():
                latest_path.unlink()
            # Create copy instead of symlink (Windows compatible)
            import shutil
            shutil.copy(
                self.models_dir / f"{prop_type}_{model_name}_{timestamp}.pkl",
                latest_path
            )

        print(f"\n[SUCCESS] All models saved to {self.models_dir}")

    def train_all_models(self, prop_type: str):
        """
        Train all models for a prop type
        """
        print(f"\n{'='*70}")
        print(f"TRAINING ALL MODELS FOR {prop_type.upper()}")
        print(f"{'='*70}\n")

        # Prepare data
        X_train, X_test, y_train, y_test = self.prepare_training_data(prop_type)

        # Train models
        results = {}
        results['xgboost'] = self.train_xgboost(X_train, y_train, X_test, y_test)
        results['lightgbm'] = self.train_lightgbm(X_train, y_train, X_test, y_test)
        results['random_forest'] = self.train_random_forest(X_train, y_train, X_test, y_test)
        results['logistic'] = self.train_logistic_regression(X_train, y_train, X_test, y_test)
        results['ensemble'] = self.train_ensemble(
            results['xgboost'],
            results['lightgbm'],
            results['random_forest'],
            X_test,
            y_test
        )

        # Summary
        print(f"\n{'='*70}")
        print(f"MODEL COMPARISON - {prop_type.upper()}")
        print(f"{'='*70}\n")
        print(f"{'Model':<20} {'Test Acc':<12} {'Test AUC':<12} {'LogLoss':<12}")
        print(f"{'-'*56}")

        for model_name, result in results.items():
            acc = result.get('test_accuracy', 0) * 100
            auc = result.get('test_auc', 0)
            loss = result.get('test_logloss', 0)
            print(f"{model_name:<20} {acc:<12.2f} {auc:<12.4f} {loss:<12.4f}")

        # Save models
        self.save_models(prop_type, results)

        return results


def main():
    """
    Main training entry point
    """
    parser = argparse.ArgumentParser(description='Train NBA props ML models')
    parser.add_argument('--prop-type', type=str, required=True,
                       choices=['points', 'rebounds', 'assists', 'threes',
                               'blocks', 'steals', 'PRA', 'all'],
                       help='Prop type to train')
    parser.add_argument('--min-samples', type=int, default=100,
                       help='Minimum samples required (default: 100)')

    args = parser.parse_args()

    trainer = NBAPropsModelTrainer()

    if args.prop_type == 'all':
        prop_types = ['points', 'rebounds', 'assists', 'threes', 'blocks', 'steals', 'PRA']
    else:
        prop_types = [args.prop_type]

    for prop_type in prop_types:
        try:
            print(f"\n\n{'#'*70}")
            print(f"# TRAINING {prop_type.upper()} MODELS")
            print(f"{'#'*70}\n")

            trainer.train_all_models(prop_type)

        except Exception as e:
            print(f"\n[ERROR] Failed to train {prop_type} models: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n\n{'='*70}")
    print("[SUCCESS] MODEL TRAINING COMPLETE!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
