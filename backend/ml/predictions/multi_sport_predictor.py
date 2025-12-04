"""
Multi-Sport Player Props Predictor
===================================
Unified predictor that supports all major sports

Usage:
    python backend/ml/predictions/multi_sport_predictor.py --sports nba
    python backend/ml/predictions/multi_sport_predictor.py --sports all
    python backend/ml/predictions/multi_sport_predictor.py --sports nba,nfl,nhl
"""

import sys
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional
import argparse
import joblib

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml.feature_engineering.multi_sport_features import get_feature_engineer


class MultiSportPropsPredictor:
    """Unified predictor for all sports"""

    # Confidence thresholds
    CONFIDENCE_THRESHOLDS = {
        'high': 0.60,
        'medium': 0.55,
        'low': 0.50
    }

    # Edge calculation: (predicted - line) / line * 100
    MIN_EDGE_PERCENT = 1.0  # Minimum 1% edge to recommend

    def __init__(self, db_path: str = "data/player_props.db"):
        self.db_path = db_path
        self.models = {}
        self.feature_engineers = {}
        self.models_dir = Path(__file__).parent.parent / "trained_models"

    def get_db(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def load_models_for_sport(self, sport: str):
        """Load all models for a specific sport"""
        if sport in self.models:
            return  # Already loaded

        print(f"\n{'='*70}")
        print(f"LOADING {sport.upper()} MODELS")
        print(f"{'='*70}\n")

        self.models[sport] = {}

        # Look for sport-specific models
        pattern = f"{sport}_*_model.joblib"
        model_files = list(self.models_dir.glob(pattern))

        if not model_files:
            print(f"  [WARN] No models found for {sport}")
            print(f"  Looking for: {self.models_dir / pattern}")
            return

        for model_file in model_files:
            # Extract prop type from filename: {sport}_{prop_type}_model.joblib
            parts = model_file.stem.split('_')
            if len(parts) >= 2:
                prop_type = '_'.join(parts[1:-1])  # Everything between sport and 'model'

                try:
                    model = joblib.load(model_file)
                    self.models[sport][prop_type] = model
                    print(f"  [OK] Loaded {prop_type} model")
                except Exception as e:
                    print(f"  [ERROR] Failed to load {prop_type}: {e}")

        if self.models[sport]:
            print(f"\n  Total models loaded: {len(self.models[sport])}")
        else:
            print(f"\n  [ERROR] No valid models loaded for {sport}")

    def get_feature_engineer(self, sport: str):
        """Get or create feature engineer for sport"""
        if sport not in self.feature_engineers:
            conn = self.get_db()
            self.feature_engineers[sport] = get_feature_engineer(sport, conn)

        return self.feature_engineers[sport]

    def get_todays_props(self, sport: str) -> List[Dict]:
        """Get all player props lines for today for a specific sport"""
        conn = self.get_db()
        cursor = conn.cursor()

        today = date.today()

        query = """
            SELECT
                player_name,
                team,
                opponent,
                home_away,
                prop_type,
                market_line,
                over_odds,
                under_odds,
                bookmaker,
                game_id
            FROM player_props_lines
            WHERE date = ? AND sport = ?
            ORDER BY player_name, prop_type
        """

        cursor.execute(query, (today, sport))
        rows = cursor.fetchall()

        props = []
        for row in rows:
            props.append({
                'player_name': row['player_name'],
                'team': row['team'],
                'opponent': row['opponent'],
                'home_away': row['home_away'],
                'prop_type': row['prop_type'],
                'market_line': row['market_line'],
                'over_odds': row['over_odds'] or -110,
                'under_odds': row['under_odds'] or -110,
                'bookmaker': row['bookmaker'],
                'game_id': row['game_id']
            })

        conn.close()
        return props

    def predict_prop(self, sport: str, prop: Dict) -> Optional[Dict]:
        """Generate prediction for a single prop"""
        prop_type = prop['prop_type']

        # Check if we have a model for this prop type
        if sport not in self.models or prop_type not in self.models[sport]:
            return None

        model = self.models[sport][prop_type]
        feature_engineer = self.get_feature_engineer(sport)

        # Engineer features
        try:
            is_home = prop['home_away'] == 'HOME'
            features = feature_engineer.engineer_features(
                player_name=prop['player_name'],
                team=prop['team'],
                opponent=prop['opponent'],
                prop_type=prop_type,
                market_line=prop['market_line'],
                is_home=is_home
            )

            # Create feature dataframe in correct order
            feature_names = feature_engineer.get_feature_names()
            X = pd.DataFrame([[features[f] for f in feature_names]], columns=feature_names)

            # Get prediction
            predicted_value = model.predict(X)[0]

            # Get confidence (probability) if available
            if hasattr(model, 'predict_proba'):
                # Classification model
                proba = model.predict_proba(X)[0]
                confidence = max(proba)
            else:
                # Regression model - calculate confidence based on prediction distance from line
                distance = abs(predicted_value - prop['market_line'])
                confidence = 1.0 / (1.0 + distance / 5.0)  # Inverse distance scaling

            # Calculate edge
            edge = predicted_value - prop['market_line']
            edge_pct = (edge / prop['market_line'] * 100) if prop['market_line'] > 0 else 0

            # Determine recommendation
            if abs(edge_pct) < self.MIN_EDGE_PERCENT:
                recommendation = 'NO_PLAY'
            elif edge > 0:
                recommendation = 'OVER'
            else:
                recommendation = 'UNDER'

            # Get confidence level
            if confidence >= self.CONFIDENCE_THRESHOLDS['high']:
                confidence_level = 'high'
            elif confidence >= self.CONFIDENCE_THRESHOLDS['medium']:
                confidence_level = 'medium'
            else:
                confidence_level = 'low'

            return {
                'player_name': prop['player_name'],
                'team': prop['team'],
                'opponent': prop['opponent'],
                'home_away': prop['home_away'],
                'prop_type': prop_type,
                'market_line': prop['market_line'],
                'predicted_value': round(predicted_value, 2),
                'edge': round(edge, 2),
                'edge_pct': round(edge_pct, 2),
                'confidence': round(confidence, 3),
                'confidence_level': confidence_level,
                'recommendation': recommendation,
                'over_odds': prop['over_odds'],
                'under_odds': prop['under_odds'],
                'bookmaker': prop['bookmaker'],
                'model_type': type(model).__name__,
                'sport': sport
            }

        except Exception as e:
            print(f"  [ERROR] Failed to predict {prop['player_name']} {prop_type}: {e}")
            return None

    def store_predictions(self, predictions: List[Dict], sport: str):
        """Store predictions in database"""
        conn = self.get_db()
        cursor = conn.cursor()

        today = date.today()
        timestamp = datetime.now().isoformat()

        stored = 0

        for pred in predictions:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO player_props_predictions
                    (prediction_date, player_name, team, opponent, home_away, prop_type,
                     market_line, predicted_value, edge, edge_pct, confidence,
                     confidence_level, recommendation, over_odds, under_odds,
                     bookmaker, model_type, sport, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    today,
                    pred['player_name'],
                    pred['team'],
                    pred['opponent'],
                    pred['home_away'],
                    pred['prop_type'],
                    pred['market_line'],
                    pred['predicted_value'],
                    pred['edge'],
                    pred['edge_pct'],
                    pred['confidence'],
                    pred['confidence_level'],
                    pred['recommendation'],
                    pred['over_odds'],
                    pred['under_odds'],
                    pred['bookmaker'],
                    pred['model_type'],
                    sport,
                    timestamp
                ))
                stored += 1
            except Exception as e:
                print(f"  [ERROR] Failed to store prediction for {pred['player_name']}: {e}")

        conn.commit()
        conn.close()

        return stored

    def run_sport(self, sport: str) -> Dict:
        """Run predictions for a single sport"""
        print(f"\n{'='*70}")
        print(f"RUNNING {sport.upper()} PREDICTIONS")
        print(f"{'='*70}\n")

        # Load models
        self.load_models_for_sport(sport)

        if sport not in self.models or not self.models[sport]:
            print(f"  [SKIP] No models available for {sport}")
            return {'sport': sport, 'predictions': 0, 'stored': 0, 'errors': 0}

        # Get today's props
        props = self.get_todays_props(sport)
        print(f"  Found {len(props)} props to analyze")

        if not props:
            print(f"  [SKIP] No props found for {sport} today")
            return {'sport': sport, 'predictions': 0, 'stored': 0, 'errors': 0}

        # Generate predictions
        predictions = []
        errors = 0

        for prop in props:
            prediction = self.predict_prop(sport, prop)
            if prediction:
                predictions.append(prediction)
            else:
                errors += 1

        print(f"\n  Generated {len(predictions)} predictions")
        print(f"  Errors: {errors}")

        # Store predictions
        if predictions:
            stored = self.store_predictions(predictions, sport)
            print(f"  Stored {stored} predictions")
        else:
            stored = 0

        # Summary stats
        if predictions:
            edges = [p for p in predictions if p['recommendation'] != 'NO_PLAY']
            high_conf = [p for p in predictions if p['confidence_level'] == 'high']

            print(f"\n  Summary:")
            print(f"    Props with edge: {len(edges)}")
            print(f"    High confidence: {len(high_conf)}")
            print(f"    Avg edge: {np.mean([p['edge_pct'] for p in edges]):.2f}%" if edges else "    Avg edge: N/A")

        return {
            'sport': sport,
            'predictions': len(predictions),
            'stored': stored,
            'errors': errors
        }

    def run(self, sports: List[str] = None):
        """Run predictions for multiple sports"""
        if sports is None:
            sports = ['nba']

        if 'all' in sports:
            sports = ['nba', 'nfl', 'nhl', 'ncaab', 'ncaaf']

        print("=" * 70)
        print("MULTI-SPORT PLAYER PROPS PREDICTOR")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Sports: {', '.join(sports)}")
        print(f"Database: {self.db_path}")

        results = []
        for sport in sports:
            result = self.run_sport(sport)
            results.append(result)

        # Overall summary
        print("\n" + "=" * 70)
        print("OVERALL SUMMARY")
        print("=" * 70)

        total_predictions = sum(r['predictions'] for r in results)
        total_stored = sum(r['stored'] for r in results)
        total_errors = sum(r['errors'] for r in results)

        for result in results:
            print(f"  {result['sport'].upper():8} - {result['predictions']} predictions, {result['stored']} stored")

        print(f"\n  Total predictions: {total_predictions}")
        print(f"  Total stored: {total_stored}")
        print(f"  Total errors: {total_errors}")
        print()

        return results


def main():
    parser = argparse.ArgumentParser(description='Generate multi-sport player props predictions')
    parser.add_argument('--sports', type=str, default='nba',
                       help='Sports to predict (comma-separated: nba,nhl,nfl,ncaab,ncaaf or "all")')
    parser.add_argument('--db', type=str, default='data/player_props.db',
                       help='Database path')

    args = parser.parse_args()

    sports = [s.strip().lower() for s in args.sports.split(',')]

    predictor = MultiSportPropsPredictor(db_path=args.db)
    results = predictor.run(sports)

    # Exit with error if no predictions generated
    total_predictions = sum(r['predictions'] for r in results)
    if total_predictions == 0:
        print("\n[ERROR] No predictions generated")
        sys.exit(1)

    print(f"\n[DONE] Generated {total_predictions} predictions across {len(results)} sports")


if __name__ == "__main__":
    main()
