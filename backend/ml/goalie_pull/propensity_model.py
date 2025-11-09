"""
Pull Propensity Model - Predicts WHEN a goalie pull will happen

Uses XGBoost to predict P(pull in next 15 seconds) based on:
- Game state (time, score, strength)
- Coach tendencies
- Situational factors
- Momentum

This is Layer A of the timing alpha system.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pickle
import json

try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import roc_auc_score, classification_report, roc_curve
    from sklearn.calibration import calibration_curve
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    print("[WARNING] XGBoost or sklearn not installed. Install with: pip install xgboost scikit-learn")

from database_schema import GoaliePullDB


class PullPropensityModel:
    """Predicts probability of goalie pull in next N seconds"""

    def __init__(self):
        self.db = GoaliePullDB()
        self.model = None
        self.feature_names = None
        self.coach_profiles = {}
        self.model_path = Path(__file__).parent / "propensity_model.pkl"
        self.config_path = Path(__file__).parent / "feature_config.json"

    def load_coach_profiles(self):
        """Load all coach profiles into memory for fast lookup"""
        profiles = self.db.get_all_coach_profiles()

        for profile in profiles:
            self.coach_profiles[profile['coach_id']] = {
                'aggressive_rating': profile['aggressive_rating'] or 5,
                'median_pull_time_down_1': profile['median_pull_time_down_1_seconds'] or 100,
                'median_pull_time_down_2': profile['median_pull_time_down_2_seconds'] or 130,
                'pull_variability': (profile.get('p75_pull_time_down_1_seconds') or 120) -
                                  (profile.get('p25_pull_time_down_1_seconds') or 80),
                'pulls_before_2min': profile['pulls_before_2min'] or 0,
                'pulls_total': profile['pulls_down_1'] + profile['pulls_down_2'] + profile['pulls_down_3_plus']
            }

        print(f"[OK] Loaded {len(self.coach_profiles)} coach profiles")

    def create_features(self, game_state: Dict) -> Dict:
        """
        Create features from game state

        Args:
            game_state: Dict with:
                - time_remaining_seconds: int
                - score_differential: int (-3 to +3)
                - period: int (3 or 4=OT)
                - strength_state: str ('5v5', '5v4', etc.)
                - zone: str ('DZ', 'NZ', 'OZ', None)
                - possession: str ('home', 'away', 'neutral')
                - coach_id: str
                - playoff_game: bool
                - home_game: bool (for pulling team)
                - timeout_available: bool

        Returns:
            Dict of features
        """
        features = {}

        # Time features
        time_remaining = game_state['time_remaining_seconds']
        features['time_remaining'] = time_remaining
        features['time_remaining_binned'] = self._bin_time(time_remaining)

        # Score features
        score_diff = game_state['score_differential']
        features['score_diff'] = score_diff
        features['score_diff_squared'] = score_diff ** 2

        # Interaction: score × time
        features['score_time_interaction'] = score_diff * (300 - time_remaining) / 100

        # Period features
        features['period'] = game_state.get('period', 3)
        features['is_overtime'] = 1 if features['period'] >= 4 else 0

        # Strength state
        strength = game_state.get('strength_state') or '5v5'
        features['is_5v5'] = 1 if strength == '5v5' else 0
        features['is_shorthanded'] = 1 if ('4v5' in strength or '3v5' in strength) else 0
        features['is_powerplay'] = 1 if ('5v4' in strength or '5v3' in strength) else 0

        # Zone features
        zone = game_state.get('zone')
        features['zone_offensive'] = 1 if zone == 'OZ' else 0
        features['zone_defensive'] = 1 if zone == 'DZ' else 0

        # Possession
        possession = game_state.get('possession')
        features['has_possession'] = 1 if possession in ['home', 'away'] else 0

        # Coach features
        coach_id = game_state.get('coach_id')
        if coach_id and coach_id in self.coach_profiles:
            coach = self.coach_profiles[coach_id]
            features['coach_aggressive_rating'] = coach['aggressive_rating']
            features['coach_median_pull_time'] = coach['median_pull_time_down_1'] if score_diff == -1 else coach['median_pull_time_down_2']
            features['coach_pull_variability'] = coach['pull_variability']
            features['coach_pulls_before_2min_rate'] = coach['pulls_before_2min'] / max(coach['pulls_total'], 1)
        else:
            # Default values for unknown coaches
            features['coach_aggressive_rating'] = 5
            features['coach_median_pull_time'] = 100 if score_diff == -1 else 130
            features['coach_pull_variability'] = 40
            features['coach_pulls_before_2min_rate'] = 0.3

        # Situational
        features['playoff_game'] = 1 if game_state.get('playoff_game', False) else 0
        features['home_game'] = 1 if game_state.get('home_game', False) else 0
        features['timeout_available'] = 1 if game_state.get('timeout_available', True) else 0

        # Momentum (if available)
        features['xg_for_last_5min'] = game_state.get('xg_for_last_5min', 0.5)
        features['xg_against_last_5min'] = game_state.get('xg_against_last_5min', 0.5)
        features['recent_goal'] = 1 if game_state.get('recent_goal', False) else 0

        return features

    def _bin_time(self, seconds: int) -> int:
        """Bin time remaining into categories"""
        if seconds <= 60:
            return 0  # 0-60s
        elif seconds <= 90:
            return 1  # 60-90s
        elif seconds <= 120:
            return 2  # 90-120s (1:30-2:00)
        elif seconds <= 180:
            return 3  # 120-180s (2:00-3:00)
        else:
            return 4  # 180+ s

    def prepare_training_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data from historical pulls

        For each pull, create:
        - Positive examples: state at t-15s, t-30s before pull
        - Negative examples: state at t-60s, t-90s before pull (no pull in next 15s)

        Returns:
            X (features), y (labels)
        """
        pulls = self.db.get_historical_pulls()

        if not pulls:
            raise ValueError("No historical pulls found. Run data collection first.")

        print(f"[OK] Loaded {len(pulls)} historical pulls")

        # Load coach profiles
        self.load_coach_profiles()

        training_examples = []

        for pull in pulls:
            pull_time = pull['pull_time_seconds']
            coach_id = pull['coach_id']
            score_diff = pull['score_differential']

            # Create snapshots at different time offsets
            # Positive examples (pull happened within 15s)
            for offset in [15, 30]:
                time_at_snapshot = pull_time + offset

                if time_at_snapshot <= 300:  # Only last 5 minutes
                    game_state = {
                        'time_remaining_seconds': time_at_snapshot,
                        'score_differential': score_diff,
                        'period': pull['pull_period'],
                        'strength_state': pull.get('strength_state', '5v5'),
                        'zone': pull.get('zone'),
                        'possession': pull.get('possession'),
                        'coach_id': coach_id,
                        'playoff_game': pull.get('playoff_game', False),
                        'home_game': pull['pulling_team'] == pull['home_team'],
                        'timeout_available': pull.get('timeout_available', True)
                    }

                    features = self.create_features(game_state)
                    features['pull_in_next_15s'] = 1 if offset <= 15 else 0
                    training_examples.append(features)

            # Negative examples (no pull in next 15s)
            for offset in [60, 90]:
                time_at_snapshot = pull_time + offset

                if time_at_snapshot <= 300:
                    game_state = {
                        'time_remaining_seconds': time_at_snapshot,
                        'score_differential': score_diff,
                        'period': pull['pull_period'],
                        'strength_state': pull.get('strength_state', '5v5'),
                        'zone': pull.get('zone'),
                        'possession': pull.get('possession'),
                        'coach_id': coach_id,
                        'playoff_game': pull.get('playoff_game', False),
                        'home_game': pull['pulling_team'] == pull['home_team'],
                        'timeout_available': pull.get('timeout_available', True)
                    }

                    features = self.create_features(game_state)
                    features['pull_in_next_15s'] = 0
                    training_examples.append(features)

        df = pd.DataFrame(training_examples)
        print(f"[OK] Created {len(df)} training examples")
        print(f"     Positive (pull in 15s): {df['pull_in_next_15s'].sum()}")
        print(f"     Negative (no pull): {(~df['pull_in_next_15s'].astype(bool)).sum()}")

        # Separate features and target
        y = df['pull_in_next_15s']
        X = df.drop('pull_in_next_15s', axis=1)

        self.feature_names = list(X.columns)

        return X, y

    def train(self, X: pd.DataFrame, y: pd.Series):
        """Train XGBoost model"""
        if not HAS_ML_LIBS:
            raise ImportError("XGBoost and scikit-learn required. Install with: pip install xgboost scikit-learn")

        print("\n[TRAINING] Pull Propensity Model")
        print("=" * 80)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"Training set: {len(X_train)} examples")
        print(f"Test set: {len(X_test)} examples")

        # Train XGBoost
        self.model = xgb.XGBClassifier(
            max_depth=6,
            learning_rate=0.05,
            n_estimators=500,
            objective='binary:logistic',
            eval_metric='auc',
            random_state=42,
            early_stopping_rounds=50
        )

        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )

        # Evaluate
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        y_pred = self.model.predict(X_test)

        auc = roc_auc_score(y_test, y_pred_proba)

        print(f"\n[RESULTS]")
        print(f"AUC: {auc:.3f}")
        print(f"\nClassification Report:")
        print(classification_report(y_test, y_pred))

        # Feature importance
        importance = self.model.feature_importances_
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)

        print(f"\nTop 10 Features:")
        print(feature_importance.head(10).to_string(index=False))

        print("\n" + "=" * 80)
        print(f"[OK] Model training complete!")

        return auc

    def save_model(self):
        """Save trained model and configuration"""
        if self.model is None:
            raise ValueError("No model to save. Train first.")

        # Save model
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)

        # Save configuration
        config = {
            'feature_names': self.feature_names,
            'model_type': 'XGBClassifier',
            'training_date': pd.Timestamp.now().isoformat()
        }

        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"[OK] Model saved to {self.model_path}")
        print(f"[OK] Config saved to {self.config_path}")

    def load_model(self):
        """Load trained model and configuration"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}. Train first.")

        with open(self.model_path, 'rb') as f:
            self.model = pickle.load(f)

        with open(self.config_path, 'r') as f:
            config = json.load(f)
            self.feature_names = config['feature_names']

        # Load coach profiles
        self.load_coach_profiles()

        print(f"[OK] Model loaded from {self.model_path}")

    def predict(self, game_state: Dict) -> float:
        """
        Predict probability of pull in next 15 seconds

        Args:
            game_state: Dict with game state features

        Returns:
            Probability (0.0 to 1.0)
        """
        if self.model is None:
            raise ValueError("No model loaded. Load or train first.")

        # Create features
        features = self.create_features(game_state)

        # Convert to DataFrame with correct column order
        X = pd.DataFrame([features])[self.feature_names]

        # Predict
        prob = self.model.predict_proba(X)[0, 1]

        return prob


if __name__ == "__main__":
    print("=" * 80)
    print("PULL PROPENSITY MODEL TRAINING")
    print("=" * 80)

    model = PullPropensityModel()

    # Prepare data
    X, y = model.prepare_training_data()

    # Train
    auc = model.train(X, y)

    # Save
    model.save_model()

    print(f"\n[OK] Training complete! AUC: {auc:.3f}")
