"""
NBA Moneyline Models Trainer
Trains Logistic Regression and Random Forest Classifier for NBA moneylines

Target: home_win (1 if home wins, 0 if away wins)
Guide: "Regression-based power ratings"
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, log_loss
import joblib
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NBAMoneylineTrainer:
    """Train classification models for NBA moneyline (straight-up winner) prediction"""

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

        # Create target: home_win (1 = home wins, 0 = away wins)
        df['home_win'] = (df['home_score'] > df['away_score']).astype(int)

        logger.info(f"[OK] Loaded {len(df)} games")
        logger.info(f"[OK] Home win rate: {df['home_win'].mean()*100:.1f}%")
        logger.info(f"[OK] Home wins: {df['home_win'].sum()}")
        logger.info(f"[OK] Away wins: {(1-df['home_win']).sum()}")

        return df

    def prepare_features(self, df):
        """Select and prepare features for training"""

        # Features to exclude
        exclude_cols = [
            'home_win',  # Target variable (derived)
            'home_margin',  # Would leak target
            'actual_total',  # Different target
            'game_id', 'season', 'game_date',  # Metadata
            'home_team', 'away_team',  # Team names
            'home_score', 'away_score'  # Actual scores (would leak target)
        ]

        feature_cols = [col for col in df.columns if col not in exclude_cols]
        feature_cols = [col for col in feature_cols if df[col].dtype in ['int64', 'float64']]

        logger.info(f"\n[FEATURES] Using {len(feature_cols)} features")
        logger.info(f"Key features: win_pct_diff, point_diff_diff, momentum")

        X = df[feature_cols].copy()
        y = df['home_win'].copy()

        # Handle any NaN values
        X = X.fillna(X.mean())

        logger.info(f"\n[OK] Feature matrix: {X.shape}")
        logger.info(f"[OK] Class balance: {y.value_counts().to_dict()}")

        return X, y, feature_cols

    def train_logistic_regression(self, X_train, y_train, X_test, y_test):
        """Train Logistic Regression model"""
        logger.info("\n" + "="*70)
        logger.info("TRAINING LOGISTIC REGRESSION MODEL")
        logger.info("="*70)
        logger.info("Guide: 'Outputs clean probabilities, handles classification well'")

        model = LogisticRegression(
            max_iter=1000,
            random_state=42,
            solver='lbfgs'
        )

        model.fit(X_train, y_train)

        # Predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]  # Probability of home win

        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        logloss = log_loss(y_test, y_pred_proba)

        # Probability calibration check
        # Group predictions by probability bins and check actual win rate
        bins = [0, 0.4, 0.5, 0.6, 1.0]
        bin_labels = ['<40%', '40-50%', '50-60%', '>60%']

        logger.info(f"\n[RESULTS]")
        logger.info(f"  Accuracy: {accuracy*100:.2f}%")
        logger.info(f"  ROC-AUC: {roc_auc:.4f}")
        logger.info(f"  Log Loss: {logloss:.4f}")

        logger.info(f"\n[PROBABILITY CALIBRATION]")
        for i in range(len(bins)-1):
            mask = (y_pred_proba >= bins[i]) & (y_pred_proba < bins[i+1])
            if mask.sum() > 0:
                actual_rate = y_test[mask].mean()
                avg_pred_prob = y_pred_proba[mask].mean()
                logger.info(f"  {bin_labels[i]}: Predicted {avg_pred_prob*100:.1f}% | Actual {actual_rate*100:.1f}% | N={mask.sum()}")

        self.training_stats['logistic_regression'] = {
            'accuracy': accuracy,
            'roc_auc': roc_auc,
            'log_loss': logloss,
            'n_samples': len(y_test)
        }

        return model

    def train_random_forest_classifier(self, X_train, y_train, X_test, y_test):
        """Train Random Forest Classifier model"""
        logger.info("\n" + "="*70)
        logger.info("TRAINING RANDOM FOREST CLASSIFIER MODEL")
        logger.info("="*70)
        logger.info("Guide: 'Captures complex winning factors'")

        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1,
            verbose=1
        )

        model.fit(X_train, y_train)

        # Predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]

        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        logloss = log_loss(y_test, y_pred_proba)

        logger.info(f"\n[RESULTS]")
        logger.info(f"  Accuracy: {accuracy*100:.2f}%")
        logger.info(f"  ROC-AUC: {roc_auc:.4f}")
        logger.info(f"  Log Loss: {logloss:.4f}")

        # Probability calibration
        bins = [0, 0.4, 0.5, 0.6, 1.0]
        bin_labels = ['<40%', '40-50%', '50-60%', '>60%']

        logger.info(f"\n[PROBABILITY CALIBRATION]")
        for i in range(len(bins)-1):
            mask = (y_pred_proba >= bins[i]) & (y_pred_proba < bins[i+1])
            if mask.sum() > 0:
                actual_rate = y_test[mask].mean()
                avg_pred_prob = y_pred_proba[mask].mean()
                logger.info(f"  {bin_labels[i]}: Predicted {avg_pred_prob*100:.1f}% | Actual {actual_rate*100:.1f}% | N={mask.sum()}")

        self.training_stats['random_forest_classifier'] = {
            'accuracy': accuracy,
            'roc_auc': roc_auc,
            'log_loss': logloss,
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
            filename = f"{self.model_dir}nba_{name}_moneyline_{timestamp}.joblib"
            joblib.dump(model, filename)
            file_size = os.path.getsize(filename) / 1024
            logger.info(f"[OK] {name}: {filename} ({file_size:.1f} KB)")

            latest_filename = f"{self.model_dir}nba_{name}_moneyline_latest.joblib"
            joblib.dump(model, latest_filename)

        # Save metadata
        metadata = {
            'feature_names': feature_names,
            'training_stats': self.training_stats,
            'timestamp': timestamp,
            'target': 'home_win'
        }
        metadata_file = f"{self.model_dir}nba_moneyline_metadata_{timestamp}.joblib"
        joblib.dump(metadata, metadata_file)

        latest_metadata_file = f"{self.model_dir}nba_moneyline_metadata_latest.joblib"
        joblib.dump(metadata, latest_metadata_file)

        logger.info(f"\n[SUCCESS] All models saved")

    def compare_models(self):
        """Compare all model performances"""
        logger.info("\n" + "="*70)
        logger.info("MODEL COMPARISON")
        logger.info("="*70)

        # Sort by accuracy
        sorted_models = sorted(self.training_stats.items(), key=lambda x: x[1]['accuracy'], reverse=True)

        for rank, (name, stats) in enumerate(sorted_models, 1):
            logger.info(f"\n#{rank} {name.upper().replace('_', ' ')}")
            logger.info(f"  Accuracy: {stats['accuracy']*100:.2f}%")
            logger.info(f"  ROC-AUC: {stats['roc_auc']:.4f}")
            logger.info(f"  Log Loss: {stats['log_loss']:.4f} (lower is better)")

        best_model = sorted_models[0][0]
        best_acc = sorted_models[0][1]['accuracy']
        logger.info(f"\n🏆 BEST MODEL: {best_model.upper().replace('_', ' ')} ({best_acc*100:.2f}% accuracy)")

    def run(self):
        """Complete training pipeline"""
        logger.info("\n" + "="*70)
        logger.info("NBA MONEYLINE MODELS TRAINER")
        logger.info("Training: Logistic Regression, Random Forest Classifier")
        logger.info("="*70)

        # Load data
        df = self.load_data()

        # Prepare features
        X, y, feature_cols = self.prepare_features(df)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        logger.info(f"\n[SPLIT] Train: {len(X_train)} games, Test: {len(X_test)} games")
        logger.info(f"[SPLIT] Train class balance: {y_train.value_counts().to_dict()}")

        # Train all models
        models = {}
        models['logistic_regression'] = self.train_logistic_regression(X_train, y_train, X_test, y_test)
        models['random_forest_classifier'] = self.train_random_forest_classifier(X_train, y_train, X_test, y_test)

        # Compare models
        self.compare_models()

        # Save models
        self.save_models(models, feature_cols)

        logger.info(f"\n{'='*70}")
        logger.info("[COMPLETE] NBA Moneyline models ready!")
        logger.info("="*70)


if __name__ == "__main__":
    trainer = NBAMoneylineTrainer()
    trainer.run()
