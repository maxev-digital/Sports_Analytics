"""
Daily NBA Props Predictions
Generates ML-powered predictions for today's NBA props

Usage:
    python backend/ml/predictions/daily_props_predictor.py
    python backend/ml/predictions/daily_props_predictor.py --date 2025-11-14
"""

import sys
import sqlite3
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import argparse

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml.feature_engineering.nba_props_features import NBAPropsFeatureEngineer
from player_props_client import PlayerPropsClient


class DailyPropsPredictor:
    """
    Generates daily predictions for NBA props using trained ML models
    """

    def __init__(self, db_path: str = "data/player_props.db"):
        self.db_path = db_path
        self.feature_engineer = NBAPropsFeatureEngineer(db_path)
        self.props_client = PlayerPropsClient()
        self.models_dir = Path("ml/models/trained/nba_props")
        self.models = {}

    def load_models(self, prop_types: List[str] = None):
        """
        Load trained models from disk

        Args:
            prop_types: List of prop types to load (default: all available)
        """
        print(f"\n{'='*70}")
        print("LOADING TRAINED MODELS")
        print(f"{'='*70}\n")

        if prop_types is None:
            # Auto-detect available models
            prop_types = []
            for model_file in self.models_dir.glob("*_xgboost_latest.pkl"):
                prop_type = model_file.stem.replace("_xgboost_latest", "")
                prop_types.append(prop_type)

        for prop_type in prop_types:
            model_types = ['xgboost', 'lightgbm', 'random_forest']

            for model_type in model_types:
                model_path = self.models_dir / f"{prop_type}_{model_type}_latest.pkl"

                if model_path.exists():
                    try:
                        with open(model_path, 'rb') as f:
                            model_data = pickle.load(f)

                        key = f"{prop_type}_{model_type}"
                        self.models[key] = model_data

                        acc = model_data.get('test_accuracy', 0) * 100
                        auc = model_data.get('test_auc', 0)
                        print(f"  [OK] Loaded {key}: {acc:.1f}% acc, {auc:.3f} AUC")

                    except Exception as e:
                        print(f"  [ERROR] Failed to load {key}: {e}")
                else:
                    print(f"  [SKIP] Model not found: {model_path.name}")

        print(f"\n[SUCCESS] Loaded {len(self.models)} models\n")

        if len(self.models) == 0:
            raise ValueError("No trained models found! Run training first.")

    def predict_prop(
        self,
        player_name: str,
        team: str,
        opponent: str,
        prop_type: str,
        market_line: float,
        game_date: date,
        home_away: str = "HOME"
    ) -> Dict:
        """
        Generate prediction for a single prop

        Returns:
            {
                'player_name': str,
                'prop_type': str,
                'market_line': float,
                'predicted_value': float,
                'over_prob': float,
                'under_prob': float,
                'confidence': float,
                'edge': float,
                'recommendation': str,  # 'OVER', 'UNDER', 'PASS'
                'model_votes': dict
            }
        """
        # Extract features
        features = self.feature_engineer.extract_features_for_prop(
            player_name=player_name,
            team=team,
            opponent=opponent,
            prop_type=prop_type,
            market_line=market_line,
            game_date=game_date,
            home_away=home_away
        )

        # Convert features to DataFrame
        feature_names = [k for k in features.keys()
                        if k not in ['player_name', 'team', 'opponent',
                                   'prop_type', 'market_line', 'game_date', 'game_id']]

        X = pd.DataFrame([features])[feature_names].fillna(0)

        # Get predictions from all available models for this prop type
        predictions = []
        model_votes = {}

        for model_name in ['xgboost', 'lightgbm', 'random_forest']:
            key = f"{prop_type}_{model_name}"

            if key in self.models:
                model_data = self.models[key]
                model = model_data['model']

                # Ensure features match training
                trained_features = model_data.get('feature_names', feature_names)

                # Reorder/filter features to match training
                X_aligned = pd.DataFrame(0, index=X.index, columns=trained_features)
                for col in trained_features:
                    if col in X.columns:
                        X_aligned[col] = X[col]

                # Predict
                prob = model.predict_proba(X_aligned)[0][1]  # Probability of OVER
                pred = 1 if prob >= 0.5 else 0

                predictions.append(prob)
                model_votes[model_name] = {
                    'over_prob': prob,
                    'prediction': 'OVER' if pred else 'UNDER'
                }

        if len(predictions) == 0:
            return {
                'error': f'No trained model available for {prop_type}',
                'player_name': player_name,
                'prop_type': prop_type,
                'market_line': market_line
            }

        # Ensemble prediction (average)
        over_prob = np.mean(predictions)
        under_prob = 1 - over_prob

        # Calculate confidence (how far from 50/50?)
        confidence = abs(over_prob - 0.5) * 200  # Scale to 0-100

        # Calculate edge (expected value vs market implied prob)
        # Market implied prob at -110 odds = 52.4%
        market_implied = 0.524
        edge = over_prob - market_implied

        # Recommendation
        if confidence >= 20 and edge >= 0.05:  # High confidence + positive edge
            recommendation = 'OVER' if over_prob > 0.5 else 'UNDER'
        elif confidence >= 10 and edge >= 0.03:  # Medium confidence + edge
            recommendation = 'OVER' if over_prob > 0.5 else 'UNDER'
        else:
            recommendation = 'PASS'

        # Estimate predicted value (using market line as baseline)
        # If over_prob > 0.5, we expect value > line
        predicted_value = market_line * (1 + edge * 2)  # Rough estimate

        return {
            'player_name': player_name,
            'team': team,
            'opponent': opponent,
            'prop_type': prop_type,
            'market_line': market_line,
            'predicted_value': round(predicted_value, 1),
            'over_prob': round(over_prob, 3),
            'under_prob': round(under_prob, 3),
            'confidence': round(confidence, 1),
            'edge': round(edge * 100, 2),  # As percentage
            'recommendation': recommendation,
            'model_votes': model_votes
        }

    def generate_daily_predictions(
        self,
        target_date: date = None,
        min_confidence: float = 0.0
    ) -> pd.DataFrame:
        """
        Generate predictions for all props on a given date

        Args:
            target_date: Date to generate predictions for (default: today)
            min_confidence: Minimum confidence to include (default: 0)

        Returns:
            DataFrame with all predictions
        """
        if target_date is None:
            target_date = date.today()

        print(f"\n{'='*70}")
        print(f"GENERATING PREDICTIONS FOR {target_date}")
        print(f"{'='*70}\n")

        # Get today's props from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT player_name, team, opponent, home_away,
                   prop_type, market_line, game_id
            FROM player_props_lines
            WHERE date = ?
        """, (target_date,))

        props = cursor.fetchall()
        conn.close()

        print(f"[1/2] Found {len(props)} props for {target_date}")

        if len(props) == 0:
            print(f"\n[WARN] No props found for {target_date}")
            print(f"  Have you run the daily scraper?")
            print(f"  python backend/scrapers/props/daily_props_scraper.py")
            return pd.DataFrame()

        # Generate predictions
        print(f"[2/2] Generating predictions...")
        predictions = []

        for i, prop in enumerate(props, 1):
            player_name, team, opponent, home_away, prop_type, market_line, game_id = prop

            if i % 50 == 0:
                print(f"  Progress: {i}/{len(props)} ({i/len(props)*100:.1f}%)")

            try:
                pred = self.predict_prop(
                    player_name=player_name,
                    team=team,
                    opponent=opponent,
                    prop_type=prop_type,
                    market_line=market_line,
                    game_date=target_date,
                    home_away=home_away
                )

                if 'error' not in pred and pred['confidence'] >= min_confidence:
                    pred['game_id'] = game_id
                    predictions.append(pred)

            except Exception as e:
                print(f"  [ERROR] Failed for {player_name} {prop_type}: {e}")

        # Convert to DataFrame
        df = pd.DataFrame(predictions)

        if len(df) > 0:
            # Sort by confidence descending
            df = df.sort_values('confidence', ascending=False)

            # Store predictions in database
            self._save_predictions(df, target_date)

        print(f"\n{'='*70}")
        print(f"[SUCCESS] Generated {len(df)} predictions")
        print(f"{'='*70}\n")

        return df

    def _save_predictions(self, predictions_df: pd.DataFrame, prediction_date: date):
        """
        Save predictions to database
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for _, pred in predictions_df.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO player_props_predictions
                    (prediction_date, game_date, player_id, player_name, team, opponent,
                     prop_type, market_line, predicted_value, confidence, model_type,
                     edge_pct, recommendation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().date(),
                    prediction_date,
                    pred.get('player_name', ''),  # Use name as ID for now
                    pred['player_name'],
                    pred['team'],
                    pred['opponent'],
                    pred['prop_type'],
                    pred['market_line'],
                    pred['predicted_value'],
                    pred['confidence'],
                    'ensemble',
                    pred['edge'],
                    pred['recommendation']
                ))
            except Exception as e:
                print(f"  [ERROR] Failed to save prediction: {e}")

        conn.commit()
        conn.close()

        print(f"  [OK] Saved {len(predictions_df)} predictions to database")

    def display_top_picks(self, predictions_df: pd.DataFrame, n: int = 10):
        """
        Display top N picks
        """
        if len(predictions_df) == 0:
            print("\n[INFO] No predictions to display")
            return

        # Filter to recommendations only
        picks = predictions_df[predictions_df['recommendation'] != 'PASS'].copy()

        if len(picks) == 0:
            print("\n[INFO] No confident picks found (all PASS)")
            return

        print(f"\n{'='*70}")
        print(f"TOP {min(n, len(picks))} PICKS")
        print(f"{'='*70}\n")

        for i, (_, pick) in enumerate(picks.head(n).iterrows(), 1):
            print(f"{i}. {pick['player_name']} - {pick['prop_type'].upper()}")
            print(f"   Line: {pick['market_line']} | Predicted: {pick['predicted_value']}")
            print(f"   Recommendation: {pick['recommendation']}")
            print(f"   Confidence: {pick['confidence']:.1f}% | Edge: {pick['edge']:+.2f}%")
            print(f"   Over: {pick['over_prob']:.1%} | Under: {pick['under_prob']:.1%}")
            print(f"   vs {pick['opponent']}\n")

        print(f"{'='*70}\n")


def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(description='Generate daily NBA props predictions')
    parser.add_argument('--date', type=str, help='Date (YYYY-MM-DD, default: today)')
    parser.add_argument('--min-confidence', type=float, default=0.0,
                       help='Minimum confidence (0-100, default: 0)')
    parser.add_argument('--top-n', type=int, default=10,
                       help='Number of top picks to display (default: 10)')

    args = parser.parse_args()

    # Parse date
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        target_date = date.today()

    # Initialize predictor
    predictor = DailyPropsPredictor()

    # Load models
    predictor.load_models()

    # Generate predictions
    predictions = predictor.generate_daily_predictions(
        target_date=target_date,
        min_confidence=args.min_confidence
    )

    # Display top picks
    predictor.display_top_picks(predictions, n=args.top_n)

    # Export to CSV
    if len(predictions) > 0:
        output_file = f"ml/predictions/nba_props_predictions_{target_date}.csv"
        predictions.to_csv(output_file, index=False)
        print(f"[EXPORT] Predictions saved to {output_file}\n")


if __name__ == "__main__":
    main()
