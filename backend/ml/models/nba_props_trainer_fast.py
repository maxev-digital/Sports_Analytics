"""
NBA Props Model Trainer - FAST MODE
Trains ML models using only database features (no API calls)

This is 10-100x faster than full trainer for quick iterations.
Use this for initial training, then enhance with full features later.

Usage:
    python backend/ml/models/nba_props_trainer_fast.py --prop-type points
    python backend/ml/models/nba_props_trainer_fast.py --prop-type all
"""

import sys
import sqlite3
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import argparse

# ML libraries
try:
    import xgboost as xgb
    from lightgbm import LGBMClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    print("[WARN] ML libraries not installed. Run: pip install xgboost lightgbm scikit-learn")

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class FastNBAPropsTrainer:
    """
    Fast NBA Props Model Trainer - Uses only database features
    """

    def __init__(self, db_path: str = "data/player_props.db"):
        self.db_path = db_path
        self.models_dir = Path("ml/models/trained/nba_props")
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def prepare_training_data(self, prop_type: str, min_samples: int = 100) -> Tuple:
        """
        Load data from database and prepare for training
        Uses ONLY database columns - no API calls!
        """
        print(f"\n{'='*70}")
        print(f"PREPARING TRAINING DATA - {prop_type.upper()}")
        print(f"{'='*70}\n")

        conn = sqlite3.connect(self.db_path)

        # Load graded props with results
        query = """
            SELECT
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
        """

        df = pd.read_sql_query(query, conn, params=(prop_type,))
        conn.close()

        print(f"[1/4] Loaded {len(df)} {prop_type} props from database")

        if len(df) < min_samples:
            raise ValueError(f"Insufficient data: {len(df)} samples (need {min_samples})")

        # Extract simple features from database
        print(f"[2/4] Extracting features from database...")

        features_list = []
        for idx, row in df.iterrows():
            features = {
                # Market features
                'market_line': row['market_line'],
                'line_normalized': row['market_line'] / 100.0,  # Normalize

                # Context features
                'is_home': 1.0 if row['home_away'] == 'HOME' else 0.0,
                'is_away': 1.0 if row['home_away'] == 'AWAY' else 0.0,

                # Simple derived features
                'line_squared': (row['market_line'] / 100.0) ** 2,
                'line_log': np.log1p(row['market_line']),

                # Target
                'hit': row['hit']
            }
            features_list.append(features)

        features_df = pd.DataFrame(features_list)

        # Separate features and target
        feature_cols = [c for c in features_df.columns if c != 'hit']
        X = features_df[feature_cols].fillna(0)
        y = features_df['hit'].values

        print(f"[3/4] Features extracted: {len(feature_cols)} features")
        print(f"  Feature names: {', '.join(feature_cols)}")

        # Train/test split (80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"[4/4] Data split complete")
        print(f"  Training samples: {len(X_train)}")
        print(f"  Test samples: {len(X_test)}")
        print(f"  Positive rate (train): {y_train.mean()*100:.1f}%")
        print(f"  Positive rate (test): {y_test.mean()*100:.1f}%")

        return X_train, X_test, y_train, y_test, feature_cols

    def train_xgboost(self, X_train, y_train, X_test, y_test) -> Dict:
        """Train XGBoost model"""
        print(f"\n[Training XGBoost]")

        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss'
        )

        model.fit(X_train, y_train, verbose=False)

        # Evaluate
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)
        logloss = log_loss(y_test, y_pred_proba)

        print(f"  Accuracy: {accuracy*100:.2f}%")
        print(f"  AUC: {auc:.4f}")
        print(f"  LogLoss: {logloss:.4f}")

        return {
            'model': model,
            'accuracy': accuracy,
            'auc': auc,
            'logloss': logloss
        }

    def train_lightgbm(self, X_train, y_train, X_test, y_test) -> Dict:
        """Train LightGBM model"""
        print(f"\n[Training LightGBM]")

        model = LGBMClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            verbose=-1
        )

        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)
        logloss = log_loss(y_test, y_pred_proba)

        print(f"  Accuracy: {accuracy*100:.2f}%")
        print(f"  AUC: {auc:.4f}")
        print(f"  LogLoss: {logloss:.4f}")

        return {
            'model': model,
            'accuracy': accuracy,
            'auc': auc,
            'logloss': logloss
        }

    def train_random_forest(self, X_train, y_train, X_test, y_test) -> Dict:
        """Train Random Forest model"""
        print(f"\n[Training Random Forest]")

        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)
        logloss = log_loss(y_test, y_pred_proba)

        print(f"  Accuracy: {accuracy*100:.2f}%")
        print(f"  AUC: {auc:.4f}")
        print(f"  LogLoss: {logloss:.4f}")

        return {
            'model': model,
            'accuracy': accuracy,
            'auc': auc,
            'logloss': logloss
        }

    def train_logistic_regression(self, X_train, y_train, X_test, y_test) -> Dict:
        """Train Logistic Regression model"""
        print(f"\n[Training Logistic Regression]")

        model = LogisticRegression(
            random_state=42,
            max_iter=1000
        )

        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)
        logloss = log_loss(y_test, y_pred_proba)

        print(f"  Accuracy: {accuracy*100:.2f}%")
        print(f"  AUC: {auc:.4f}")
        print(f"  LogLoss: {logloss:.4f}")

        return {
            'model': model,
            'accuracy': accuracy,
            'auc': auc,
            'logloss': logloss
        }

    def train_all_models(self, prop_type: str, min_samples: int = 100) -> Dict:
        """
        Train all model types for a given prop type
        """
        print(f"\n{'='*70}")
        print(f"TRAINING ALL MODELS FOR {prop_type.upper()}")
        print(f"{'='*70}")

        # Prepare data
        X_train, X_test, y_train, y_test, feature_names = self.prepare_training_data(
            prop_type, min_samples
        )

        results = {}

        # Train each model type
        print(f"\n{'='*70}")
        print("TRAINING MODELS")
        print(f"{'='*70}")

        results['xgboost'] = self.train_xgboost(X_train, y_train, X_test, y_test)
        results['lightgbm'] = self.train_lightgbm(X_train, y_train, X_test, y_test)
        results['random_forest'] = self.train_random_forest(X_train, y_train, X_test, y_test)
        results['logistic'] = self.train_logistic_regression(X_train, y_train, X_test, y_test)

        # Create ensemble (average predictions)
        print(f"\n[Creating Ensemble]")
        ensemble_probs = np.mean([
            results['xgboost']['model'].predict_proba(X_test)[:, 1],
            results['lightgbm']['model'].predict_proba(X_test)[:, 1],
            results['random_forest']['model'].predict_proba(X_test)[:, 1],
            results['logistic']['model'].predict_proba(X_test)[:, 1]
        ], axis=0)

        ensemble_pred = (ensemble_probs >= 0.5).astype(int)
        ensemble_accuracy = accuracy_score(y_test, ensemble_pred)
        ensemble_auc = roc_auc_score(y_test, ensemble_probs)
        ensemble_logloss = log_loss(y_test, ensemble_probs)

        print(f"  Accuracy: {ensemble_accuracy*100:.2f}%")
        print(f"  AUC: {ensemble_auc:.4f}")
        print(f"  LogLoss: {ensemble_logloss:.4f}")

        results['ensemble'] = {
            'model': None,  # Ensemble doesn't have single model
            'accuracy': ensemble_accuracy,
            'auc': ensemble_auc,
            'logloss': ensemble_logloss
        }

        # Save models
        self.save_models(prop_type, results, feature_names)

        # Print summary
        self.print_summary(prop_type, results)

        return results

    def save_models(self, prop_type: str, results: Dict, feature_names: List[str]):
        """Save trained models to disk"""
        print(f"\n{'='*70}")
        print("SAVING MODELS")
        print(f"{'='*70}\n")

        for model_name, model_data in results.items():
            if model_name == 'ensemble':
                continue  # Skip ensemble (uses other models)

            model_path = self.models_dir / f"{prop_type}_{model_name}_latest.pkl"

            model_save_data = {
                'model': model_data['model'],
                'feature_names': feature_names,
                'test_accuracy': model_data['accuracy'],
                'test_auc': model_data['auc'],
                'test_logloss': model_data['logloss'],
                'trained_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'prop_type': prop_type,
                'model_type': model_name,
                'fast_mode': True  # Flag to indicate this was trained in fast mode
            }

            with open(model_path, 'wb') as f:
                pickle.dump(model_save_data, f)

            print(f"  [OK] Saved {model_name} to {model_path}")

        print(f"\n[SUCCESS] All models saved!\n")

    def print_summary(self, prop_type: str, results: Dict):
        """Print training summary"""
        print(f"\n{'='*70}")
        print(f"TRAINING SUMMARY - {prop_type.upper()}")
        print(f"{'='*70}\n")

        print(f"{'Model':<20} {'Accuracy':<12} {'AUC':<12} {'LogLoss':<12}")
        print("-" * 56)

        for model_name, model_data in results.items():
            acc = model_data['accuracy'] * 100
            auc = model_data['auc']
            ll = model_data['logloss']
            print(f"{model_name:<20} {acc:<12.2f}% {auc:<12.4f} {ll:<12.4f}")

        print(f"\n{'='*70}")

        # Highlight best model
        best_model = max(results.items(), key=lambda x: x[1]['accuracy'])
        print(f"[BEST] {best_model[0].upper()} - {best_model[1]['accuracy']*100:.2f}% accuracy")

        # Check if profitable
        breakeven = 52.4
        best_acc = best_model[1]['accuracy'] * 100

        if best_acc > breakeven:
            edge = best_acc - breakeven
            print(f"[PROFITABLE] Beating breakeven by {edge:.2f}%")
        elif best_acc > 50:
            print(f"[CLOSE] Above 50% but below breakeven (52.4%)")
        else:
            print(f"[UNPROFITABLE] Below 50%")

        print(f"{'='*70}\n")


def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(description='Fast NBA Props Model Trainer')
    parser.add_argument('--prop-type', type=str, required=True,
                       choices=['points', 'rebounds', 'assists', 'threes',
                               'blocks', 'steals', 'PRA', 'all'],
                       help='Prop type to train')
    parser.add_argument('--min-samples', type=int, default=100,
                       help='Minimum samples required (default: 100)')

    args = parser.parse_args()

    if not HAS_ML_LIBS:
        print("\n[ERROR] ML libraries not installed!")
        print("Run: pip install xgboost lightgbm scikit-learn\n")
        return

    trainer = FastNBAPropsTrainer()

    if args.prop_type == 'all':
        prop_types = ['points', 'rebounds', 'assists', 'threes', 'blocks', 'steals', 'PRA']
    else:
        prop_types = [args.prop_type]

    # Train each prop type
    for prop_type in prop_types:
        try:
            print(f"\n{'#'*70}")
            print(f"# TRAINING {prop_type.upper()} MODELS")
            print(f"{'#'*70}\n")

            trainer.train_all_models(prop_type, args.min_samples)

        except Exception as e:
            print(f"\n[ERROR] Failed to train {prop_type}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*70}")
    print("[COMPLETE] All training finished!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
