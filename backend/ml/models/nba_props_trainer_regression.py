"""
NBA Props Model Trainer - REGRESSION MODE
Trains ML models to predict ACTUAL STAT VALUES (not probabilities)

This is the correct approach:
- Predicts actual values: 25.3 points, 8.7 rebounds, 5.1 assists
- Compares to market lines to generate OVER/UNDER recommendations
- Uses regression models instead of classification

Usage:
    python backend/ml/models/nba_props_trainer_regression.py --prop-type points
    python backend/ml/models/nba_props_trainer_regression.py --prop-type all
"""

import sys
import sqlite3
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import argparse

# ML libraries
try:
    import xgboost as xgb
    from lightgbm import LGBMRegressor
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    print("[WARN] ML libraries not installed. Run: pip install xgboost lightgbm scikit-learn")

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class RegressionNBAPropsTrainer:
    """
    NBA Props Model Trainer - REGRESSION MODE
    Predicts actual stat values instead of binary outcomes
    """

    def __init__(self, db_path: str = "D:/backend/data/player_props.db"):
        self.db_path = db_path
        self.models_dir = Path("D:/backend/ml/trained_models")
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def prepare_training_data(self, prop_type: str, min_samples: int = 100) -> Tuple:
        """
        Load data from database and prepare for training
        Target: actual_value (regression)
        """
        print(f"\n{'='*70}")
        print(f"PREPARING TRAINING DATA - {prop_type.upper()} (REGRESSION)")
        print(f"{'='*70}\n")

        conn = sqlite3.connect(self.db_path)

        # Load graded props with ACTUAL VALUES
        query = """
            SELECT
                r.prop_type,
                r.market_line,
                r.actual_value,
                r.hit,
                l.home_away,
                l.date
            FROM player_props_results r
            JOIN player_props_lines l
                ON r.date = l.date
                AND r.player_id = l.player_id
                AND r.prop_type = l.prop_type
            WHERE r.prop_type = ?
              AND r.actual_value IS NOT NULL
        """

        df = pd.read_sql_query(query, conn, params=(prop_type,))
        conn.close()

        print(f"[1/4] Loaded {len(df)} {prop_type} props from database")

        if len(df) < min_samples:
            raise ValueError(f"Insufficient data: {len(df)} samples (need {min_samples})")

        # Display stats about actual values
        print(f"[2/4] Actual value statistics:")
        print(f"  Mean: {df['actual_value'].mean():.2f}")
        print(f"  Median: {df['actual_value'].median():.2f}")
        print(f"  Std: {df['actual_value'].std():.2f}")
        print(f"  Min: {df['actual_value'].min():.2f}")
        print(f"  Max: {df['actual_value'].max():.2f}")

        # Extract features
        print(f"[3/4] Extracting features from database...")

        features_list = []
        for idx, row in df.iterrows():
            features = {
                # Market features
                'market_line': row['market_line'],
                'line_normalized': row['market_line'] / 100.0,

                # Context features
                'is_home': 1.0 if row['home_away'] == 'HOME' else 0.0,
                'is_away': 1.0 if row['home_away'] == 'AWAY' else 0.0,

                # Derived features
                'line_squared': (row['market_line'] / 100.0) ** 2,
                'line_log': np.log1p(row['market_line']),

                # Target: ACTUAL VALUE (not hit!)
                'actual_value': row['actual_value']
            }
            features_list.append(features)

        features_df = pd.DataFrame(features_list)

        # Separate features and target
        feature_cols = [c for c in features_df.columns if c != 'actual_value']
        X = features_df[feature_cols].fillna(0)
        y = features_df['actual_value'].values  # REGRESSION TARGET

        print(f"[4/4] Features extracted: {len(feature_cols)} features")
        print(f"  Feature names: {', '.join(feature_cols)}")

        # Train/test split (80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        print(f"  Training samples: {len(X_train)}")
        print(f"  Test samples: {len(X_test)}")
        print(f"  Target mean (train): {y_train.mean():.2f}")
        print(f"  Target mean (test): {y_test.mean():.2f}")

        return X_train, X_test, y_train, y_test, feature_cols

    def train_xgboost(self, X_train, y_train, X_test, y_test) -> Dict:
        """Train XGBoost REGRESSOR"""
        print(f"\n[Training XGBoost Regressor]")

        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            random_state=42,
            eval_metric='rmse'
        )

        model.fit(X_train, y_train, verbose=False)

        # Evaluate
        y_pred = model.predict(X_test)

        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        print(f"  RMSE: {rmse:.3f}")
        print(f"  MAE: {mae:.3f}")
        print(f"  R²: {r2:.4f}")

        # Calculate accuracy for OVER/UNDER recommendations
        over_correct = np.sum((y_test > X_test['market_line'].values) == (y_pred > X_test['market_line'].values))
        over_under_accuracy = over_correct / len(y_test) * 100
        print(f"  OVER/UNDER Accuracy: {over_under_accuracy:.1f}%")

        return {
            'model': model,
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'over_under_accuracy': over_under_accuracy,
            'test_accuracy': over_under_accuracy  # For compatibility
        }

    def train_lightgbm(self, X_train, y_train, X_test, y_test) -> Dict:
        """Train LightGBM REGRESSOR"""
        print(f"\n[Training LightGBM Regressor]")

        model = LGBMRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            random_state=42,
            verbose=-1
        )

        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)

        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        print(f"  RMSE: {rmse:.3f}")
        print(f"  MAE: {mae:.3f}")
        print(f"  R²: {r2:.4f}")

        # Calculate accuracy for OVER/UNDER recommendations
        over_correct = np.sum((y_test > X_test['market_line'].values) == (y_pred > X_test['market_line'].values))
        over_under_accuracy = over_correct / len(y_test) * 100
        print(f"  OVER/UNDER Accuracy: {over_under_accuracy:.1f}%")

        return {
            'model': model,
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'over_under_accuracy': over_under_accuracy,
            'test_accuracy': over_under_accuracy
        }

    def train_random_forest(self, X_train, y_train, X_test, y_test) -> Dict:
        """Train Random Forest REGRESSOR"""
        print(f"\n[Training Random Forest Regressor]")

        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)

        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        print(f"  RMSE: {rmse:.3f}")
        print(f"  MAE: {mae:.3f}")
        print(f"  R²: {r2:.4f}")

        # Calculate accuracy for OVER/UNDER recommendations
        over_correct = np.sum((y_test > X_test['market_line'].values) == (y_pred > X_test['market_line'].values))
        over_under_accuracy = over_correct / len(y_test) * 100
        print(f"  OVER/UNDER Accuracy: {over_under_accuracy:.1f}%")

        return {
            'model': model,
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'over_under_accuracy': over_under_accuracy,
            'test_accuracy': over_under_accuracy
        }

    def train_linear(self, X_train, y_train, X_test, y_test) -> Dict:
        """Train Linear REGRESSION"""
        print(f"\n[Training Linear Regression]")

        model = LinearRegression()

        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)

        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        print(f"  RMSE: {rmse:.3f}")
        print(f"  MAE: {mae:.3f}")
        print(f"  R²: {r2:.4f}")

        # Calculate accuracy for OVER/UNDER recommendations
        over_correct = np.sum((y_test > X_test['market_line'].values) == (y_pred > X_test['market_line'].values))
        over_under_accuracy = over_correct / len(y_test) * 100
        print(f"  OVER/UNDER Accuracy: {over_under_accuracy:.1f}%")

        return {
            'model': model,
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'over_under_accuracy': over_under_accuracy,
            'test_accuracy': over_under_accuracy
        }

    def train_all_models(self, prop_type: str, min_samples: int = 100) -> Dict:
        """
        Train all model types for a given prop type
        """
        print(f"\n{'='*70}")
        print(f"TRAINING ALL REGRESSION MODELS FOR {prop_type.upper()}")
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
        results['linear'] = self.train_linear(X_train, y_train, X_test, y_test)

        # Create ensemble (average predictions)
        print(f"\n[Creating Ensemble]")
        ensemble_pred = np.mean([
            results['xgboost']['model'].predict(X_test),
            results['lightgbm']['model'].predict(X_test),
            results['random_forest']['model'].predict(X_test),
            results['linear']['model'].predict(X_test)
        ], axis=0)

        ensemble_rmse = np.sqrt(mean_squared_error(y_test, ensemble_pred))
        ensemble_mae = mean_absolute_error(y_test, ensemble_pred)
        ensemble_r2 = r2_score(y_test, ensemble_pred)

        # Ensemble OVER/UNDER accuracy
        over_correct = np.sum((y_test > X_test['market_line'].values) == (ensemble_pred > X_test['market_line'].values))
        ensemble_over_under_accuracy = over_correct / len(y_test) * 100

        print(f"  RMSE: {ensemble_rmse:.3f}")
        print(f"  MAE: {ensemble_mae:.3f}")
        print(f"  R²: {ensemble_r2:.4f}")
        print(f"  OVER/UNDER Accuracy: {ensemble_over_under_accuracy:.1f}%")

        results['ensemble'] = {
            'rmse': ensemble_rmse,
            'mae': ensemble_mae,
            'r2': ensemble_r2,
            'over_under_accuracy': ensemble_over_under_accuracy,
            'test_accuracy': ensemble_over_under_accuracy
        }

        # Save models
        print(f"\n{'='*70}")
        print("SAVING MODELS")
        print(f"{'='*70}\n")

        for model_type, model_data in results.items():
            if model_type == 'ensemble':
                continue  # Skip ensemble (it's just an average)

            model_path = self.models_dir / f"{prop_type}_{model_type}_model.joblib"

            # Save model with metadata
            save_data = {
                'model': model_data['model'],
                'model_type': model_type,
                'prop_type': prop_type,
                'feature_names': list(feature_names),
                'trained_date': datetime.now().isoformat(),
                'test_accuracy': model_data['test_accuracy'],
                'rmse': model_data['rmse'],
                'mae': model_data['mae'],
                'r2': model_data['r2'],
                'over_under_accuracy': model_data['over_under_accuracy'],
                'is_regression': True  # Important flag!
            }

            joblib.dump(save_data, model_path)
            print(f"[OK] Saved {model_type} model to {model_path}")

        print(f"\n{'='*70}")
        print("TRAINING COMPLETE")
        print(f"{'='*70}\n")

        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Train NBA Props Regression Models')
    parser.add_argument('--prop-type', type=str, default='all',
                       help='Prop type to train (or "all")')
    parser.add_argument('--min-samples', type=int, default=100,
                       help='Minimum samples required')
    parser.add_argument('--db-path', type=str, default='D:/backend/data/player_props.db',
                       help='Path to database')

    args = parser.parse_args()

    if not HAS_ML_LIBS:
        print("[ERROR] ML libraries not installed")
        print("Run: pip install xgboost lightgbm scikit-learn")
        sys.exit(1)

    trainer = RegressionNBAPropsTrainer(db_path=args.db_path)

    prop_types = ['points', 'rebounds', 'assists', 'threes', 'blocks', 'steals', 'PRA']

    if args.prop_type == 'all':
        print(f"\n{'='*70}")
        print("TRAINING ALL PROP TYPES")
        print(f"{'='*70}\n")

        for prop_type in prop_types:
            try:
                trainer.train_all_models(prop_type, min_samples=args.min_samples)
            except Exception as e:
                print(f"\n[ERROR] Failed to train {prop_type}: {str(e)}\n")
                continue

        print(f"\n{'='*70}")
        print("ALL MODELS TRAINED SUCCESSFULLY")
        print(f"{'='*70}\n")

    else:
        trainer.train_all_models(args.prop_type, min_samples=args.min_samples)


if __name__ == "__main__":
    main()
