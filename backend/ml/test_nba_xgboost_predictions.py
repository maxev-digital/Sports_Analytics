"""
Test NBA XGBoost Quantile Models
Validates predictions and identifies regression-to-mean opportunities

This script:
1. Loads the trained quantile models
2. Makes predictions on test games
3. Calculates z-scores
4. Identifies which games would trigger alerts (z >= 2.0)
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import os
from datetime import datetime

class NBAXGBoostTester:
    """Test NBA XGBoost models and identify regression opportunities"""

    def __init__(self):
        self.model_dir = "backend/ml/models/"
        self.data_path = "backend/data/historical/nba/nba_historical_latest.csv"

        # Load models
        self.models = {}
        self._load_models()

    def _load_models(self):
        """Load the three quantile models"""
        print("=" * 70)
        print("LOADING NBA XGBOOST MODELS")
        print("=" * 70)

        for model_type in ['lower', 'mean', 'upper']:
            model_path = f"{self.model_dir}nba_quantile_{model_type}_latest.json"

            if not os.path.exists(model_path):
                print(f"[ERROR] Model not found: {model_path}")
                continue

            model = xgb.Booster()
            model.load_model(model_path)
            self.models[model_type] = model

            file_size = os.path.getsize(model_path) / 1024
            print(f"[OK] Loaded {model_type} model ({file_size:.1f} KB)")

        print()

    def load_test_data(self, n_samples=20):
        """Load recent games for testing"""
        print("=" * 70)
        print("LOADING TEST DATA")
        print("=" * 70)

        df = pd.read_csv(self.data_path)

        # Prepare features (same as training)
        exclude_cols = [
            'actual_total', 'game_id', 'season', 'game_date',
            'home_team', 'away_team', 'home_score', 'away_score'
        ]

        feature_cols = [col for col in df.columns if col not in exclude_cols]
        feature_cols = [col for col in feature_cols if df[col].dtype in ['int64', 'float64']]

        # Get most recent games
        df = df.sort_values('game_date', ascending=False).head(n_samples)

        X = df[feature_cols].fillna(df[feature_cols].mean())

        print(f"[OK] Loaded {len(df)} recent games")
        print(f"[OK] Date range: {df['game_date'].min()} to {df['game_date'].max()}")
        print()

        return df, X, feature_cols

    def make_predictions(self, X):
        """Make predictions with all three models"""
        dmatrix = xgb.DMatrix(X)

        predictions = {}
        for model_type, model in self.models.items():
            predictions[model_type] = model.predict(dmatrix)

        return predictions

    def calculate_metrics(self, df, predictions):
        """Calculate z-scores and identify alerts"""
        print("=" * 70)
        print("PREDICTION ANALYSIS")
        print("=" * 70)

        results = []

        for idx, (_, row) in enumerate(df.iterrows()):
            # Get predictions
            lower = predictions['lower'][idx]
            mean = predictions['mean'][idx]
            upper = predictions['upper'][idx]

            # Calculate implied standard deviation
            # 80% interval (10th to 90th percentile) = 2.56 standard deviations
            interval_width = upper - lower
            std_dev = interval_width / 2.56

            # Actual total
            actual = row['actual_total']

            # Calculate z-score
            z_score = (actual - mean) / std_dev if std_dev > 0 else 0

            # Determine if this would be an alert
            is_alert = abs(z_score) >= 2.0

            result = {
                'game_date': row['game_date'],
                'matchup': f"{row['away_team']} @ {row['home_team']}",
                'actual_total': actual,
                'predicted_mean': mean,
                'predicted_lower': lower,
                'predicted_upper': upper,
                'std_dev': std_dev,
                'z_score': z_score,
                'is_alert': is_alert,
                'alert_type': 'OVER' if z_score >= 2.0 else ('UNDER' if z_score <= -2.0 else 'NONE')
            }

            results.append(result)

        return pd.DataFrame(results)

    def display_results(self, results_df):
        """Display prediction results"""

        # Overall accuracy
        mae = np.mean(np.abs(results_df['actual_total'] - results_df['predicted_mean']))

        print(f"[ACCURACY] Mean Absolute Error: {mae:.2f} points")
        print(f"[ACCURACY] Average Std Dev: {results_df['std_dev'].mean():.2f} points")
        print()

        # Alert statistics
        alerts = results_df[results_df['is_alert']]
        print(f"[ALERTS] Found {len(alerts)}/{len(results_df)} games that would trigger alerts ({len(alerts)/len(results_df)*100:.1f}%)")
        print()

        if len(alerts) > 0:
            print("=" * 70)
            print("REGRESSION-TO-MEAN ALERT OPPORTUNITIES")
            print("=" * 70)
            print()

            for _, alert in alerts.iterrows():
                print(f"Date: {alert['game_date']}")
                print(f"Game: {alert['matchup']}")
                print(f"Actual Total: {alert['actual_total']:.0f} points")
                print(f"Predicted: {alert['predicted_mean']:.1f} points")
                print(f"80% Range: {alert['predicted_lower']:.1f} - {alert['predicted_upper']:.1f}")
                print(f"Z-Score: {alert['z_score']:.2f} SD")
                print(f"Alert Type: {alert['alert_type']}")
                print(f"Deviation: {alert['actual_total'] - alert['predicted_mean']:.1f} points")
                print("-" * 70)

            print()

        # Display all predictions
        print("=" * 70)
        print("ALL PREDICTIONS")
        print("=" * 70)
        print()

        for _, row in results_df.iterrows():
            alert_marker = " [ALERT]" if row['is_alert'] else ""
            print(f"{row['game_date']} | {row['matchup']}")
            print(f"  Actual: {row['actual_total']:.0f} | Predicted: {row['predicted_mean']:.1f} | "
                  f"Error: {row['actual_total'] - row['predicted_mean']:+.1f} | "
                  f"Z-Score: {row['z_score']:+.2f}{alert_marker}")
            print()

    def run(self):
        """Run complete test suite"""
        print("\n" + "=" * 70)
        print("NBA XGBOOST MODEL VALIDATION")
        print("=" * 70)
        print()

        # Load test data
        df, X, feature_cols = self.load_test_data(n_samples=30)

        # Make predictions
        predictions = self.make_predictions(X)

        # Calculate metrics
        results_df = self.calculate_metrics(df, predictions)

        # Display results
        self.display_results(results_df)

        # Save results
        output_file = "backend/ml/test_predictions_output.csv"
        results_df.to_csv(output_file, index=False)
        print(f"[SAVED] Results saved to: {output_file}")
        print()

        print("=" * 70)
        print("[COMPLETE] Model validation finished!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Review alert opportunities above")
        print("2. Integrate models into live betting system")
        print("3. Set up real-time z-score monitoring")
        print()


if __name__ == "__main__":
    tester = NBAXGBoostTester()
    tester.run()
