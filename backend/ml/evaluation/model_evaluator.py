"""
NBA Props Model Evaluation & Backtesting
Evaluates model performance and calculates ROI

Usage:
    python backend/ml/evaluation/model_evaluator.py --prop-type points
    python backend/ml/evaluation/model_evaluator.py --prop-type all --backtest
"""

import sys
import sqlite3
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple
import argparse

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml.feature_engineering.nba_props_features import NBAPropsFeatureEngineer


class ModelEvaluator:
    """
    Evaluates trained models and calculates betting performance
    """

    def __init__(self, db_path: str = "data/player_props.db"):
        self.db_path = db_path
        self.feature_engineer = NBAPropsFeatureEngineer(db_path)
        self.models_dir = Path("ml/models/trained/nba_props")

    def backtest_model(
        self,
        prop_type: str,
        model_name: str = 'xgboost',
        confidence_threshold: float = 10.0,
        test_size: int = 200
    ) -> Dict:
        """
        Backtest model on holdout test set

        Args:
            prop_type: Type of prop
            model_name: Model to test
            confidence_threshold: Minimum confidence to bet (0-100)
            test_size: Number of recent props to test on

        Returns:
            Performance metrics dict
        """
        print(f"\n{'='*70}")
        print(f"BACKTESTING {model_name.upper()} - {prop_type.upper()}")
        print(f"{'='*70}\n")

        # Load model
        model_path = self.models_dir / f"{prop_type}_{model_name}_latest.pkl"

        if not model_path.exists():
            raise ValueError(f"Model not found: {model_path}")

        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        model = model_data['model']
        feature_names = model_data['feature_names']

        print(f"[1/4] Loaded {model_name} model")
        print(f"  Test Accuracy: {model_data.get('test_accuracy', 0)*100:.2f}%")
        print(f"  Test AUC: {model_data.get('test_auc', 0):.4f}")

        # Get test data
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
            LIMIT ?
        """

        df = pd.read_sql_query(query, conn, params=(prop_type, test_size))
        conn.close()

        print(f"\n[2/4] Loaded {len(df)} test props")

        if len(df) < 10:
            raise ValueError(f"Insufficient test data: {len(df)} samples")

        # Extract features and predict
        print(f"[3/4] Generating predictions...")
        predictions = []

        for idx, row in df.iterrows():
            if (idx + 1) % 50 == 0:
                print(f"  Progress: {idx + 1}/{len(df)}")

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

                # Convert to DataFrame
                X = pd.DataFrame([features])[feature_names].fillna(0)

                # Predict
                prob = model.predict_proba(X)[0][1]  # Prob of OVER
                pred = 1 if prob >= 0.5 else 0

                # Confidence (distance from 50/50)
                confidence = abs(prob - 0.5) * 200

                predictions.append({
                    'date': row['date'],
                    'player_name': row['player_name'],
                    'market_line': row['market_line'],
                    'actual_value': row['actual_value'],
                    'actual_hit': row['hit'],
                    'predicted_prob': prob,
                    'predicted_hit': pred,
                    'confidence': confidence,
                    'correct': (pred == row['hit'])
                })

            except Exception as e:
                print(f"  [WARN] Failed for {row['player_name']}: {e}")

        results_df = pd.DataFrame(predictions)

        # Calculate metrics
        print(f"\n[4/4] Calculating performance metrics...")

        metrics = self._calculate_metrics(results_df, confidence_threshold)

        # Display results
        self._display_results(prop_type, model_name, metrics, confidence_threshold)

        return metrics

    def _calculate_metrics(
        self,
        results_df: pd.DataFrame,
        confidence_threshold: float
    ) -> Dict:
        """
        Calculate performance metrics
        """
        # Overall accuracy
        overall_accuracy = results_df['correct'].mean()

        # Filter by confidence
        confident = results_df[results_df['confidence'] >= confidence_threshold]

        if len(confident) > 0:
            confident_accuracy = confident['correct'].mean()
            confident_count = len(confident)
        else:
            confident_accuracy = 0
            confident_count = 0

        # Betting simulation (at -110 odds)
        # Win = +0.91 units, Loss = -1.0 units
        confident['roi'] = confident.apply(
            lambda row: 0.91 if row['correct'] else -1.0,
            axis=1
        )

        total_roi = confident['roi'].sum() if len(confident) > 0 else 0
        roi_percent = (total_roi / len(confident) * 100) if len(confident) > 0 else 0

        # Win streak / loss streak
        streaks = []
        current_streak = 0
        for correct in confident['correct']:
            if correct:
                current_streak = current_streak + 1 if current_streak > 0 else 1
            else:
                current_streak = current_streak - 1 if current_streak < 0 else -1
            streaks.append(current_streak)

        max_win_streak = max([s for s in streaks if s > 0], default=0)
        max_loss_streak = abs(min([s for s in streaks if s < 0], default=0))

        # Confidence bins
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        results_df['confidence_bin'] = pd.cut(results_df['confidence'], bins=bins)

        confidence_breakdown = results_df.groupby('confidence_bin')['correct'].agg(['count', 'mean'])

        return {
            'total_predictions': len(results_df),
            'overall_accuracy': overall_accuracy,
            'confident_predictions': confident_count,
            'confident_accuracy': confident_accuracy,
            'total_roi': total_roi,
            'roi_percent': roi_percent,
            'max_win_streak': max_win_streak,
            'max_loss_streak': max_loss_streak,
            'confidence_breakdown': confidence_breakdown,
            'results_df': results_df
        }

    def _display_results(
        self,
        prop_type: str,
        model_name: str,
        metrics: Dict,
        confidence_threshold: float
    ):
        """
        Display evaluation results
        """
        print(f"\n{'='*70}")
        print(f"BACKTEST RESULTS - {prop_type.upper()} ({model_name})")
        print(f"{'='*70}\n")

        print(f"Overall Performance:")
        print(f"  Total Predictions: {metrics['total_predictions']}")
        print(f"  Accuracy: {metrics['overall_accuracy']*100:.2f}%")
        print()

        print(f"Confident Bets (≥{confidence_threshold}% confidence):")
        print(f"  Count: {metrics['confident_predictions']}")
        print(f"  Accuracy: {metrics['confident_accuracy']*100:.2f}%")
        print(f"  Total ROI: {metrics['total_roi']:+.2f} units")
        print(f"  ROI %: {metrics['roi_percent']:+.2f}%")
        print(f"  Max Win Streak: {metrics['max_win_streak']}")
        print(f"  Max Loss Streak: {metrics['max_loss_streak']}")
        print()

        # Breakeven analysis
        breakeven = 0.524  # 52.4% needed at -110 odds
        if metrics['confident_accuracy'] > breakeven:
            edge = (metrics['confident_accuracy'] - breakeven) * 100
            print(f"[PROFITABLE] Beating breakeven by {edge:.2f}%")
        elif metrics['confident_accuracy'] > 0.5:
            print(f"[CLOSE] Above 50% but below breakeven (52.4%)")
        else:
            print(f"[UNPROFITABLE] Below 50%")

        print()
        print(f"Confidence Breakdown:")
        print(f"{'Confidence':<15} {'Count':<10} {'Accuracy':<12}")
        print("-" * 37)

        for bin_range, row in metrics['confidence_breakdown'].iterrows():
            if row['count'] > 0:
                acc = row['mean'] * 100
                print(f"{str(bin_range):<15} {int(row['count']):<10} {acc:<12.1f}%")

        print(f"\n{'='*70}\n")

    def compare_all_models(self, prop_type: str) -> pd.DataFrame:
        """
        Compare performance of all models for a prop type
        """
        print(f"\n{'='*70}")
        print(f"COMPARING ALL MODELS - {prop_type.upper()}")
        print(f"{'='*70}\n")

        results = []

        for model_name in ['xgboost', 'lightgbm', 'random_forest', 'logistic']:
            model_path = self.models_dir / f"{prop_type}_{model_name}_latest.pkl"

            if model_path.exists():
                try:
                    metrics = self.backtest_model(
                        prop_type=prop_type,
                        model_name=model_name,
                        confidence_threshold=20.0,
                        test_size=200
                    )

                    results.append({
                        'model': model_name,
                        'accuracy': metrics['overall_accuracy'],
                        'confident_accuracy': metrics['confident_accuracy'],
                        'confident_count': metrics['confident_predictions'],
                        'roi_percent': metrics['roi_percent'],
                        'total_roi': metrics['total_roi']
                    })

                except Exception as e:
                    print(f"[ERROR] Failed to test {model_name}: {e}")

        comparison_df = pd.DataFrame(results)

        if len(comparison_df) > 0:
            comparison_df = comparison_df.sort_values('confident_accuracy', ascending=False)

            print(f"\n{'='*70}")
            print(f"MODEL COMPARISON - {prop_type.upper()}")
            print(f"{'='*70}\n")
            print(comparison_df.to_string(index=False))
            print(f"\n{'='*70}\n")

        return comparison_df


def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(description='Evaluate NBA props models')
    parser.add_argument('--prop-type', type=str, required=True,
                       choices=['points', 'rebounds', 'assists', 'threes',
                               'blocks', 'steals', 'PRA', 'all'],
                       help='Prop type to evaluate')
    parser.add_argument('--model', type=str, default='xgboost',
                       choices=['xgboost', 'lightgbm', 'random_forest', 'logistic'],
                       help='Model to evaluate (default: xgboost)')
    parser.add_argument('--confidence', type=float, default=20.0,
                       help='Confidence threshold for betting (default: 20)')
    parser.add_argument('--test-size', type=int, default=200,
                       help='Number of props to test (default: 200)')
    parser.add_argument('--compare', action='store_true',
                       help='Compare all models')

    args = parser.parse_args()

    evaluator = ModelEvaluator()

    if args.prop_type == 'all':
        prop_types = ['points', 'rebounds', 'assists', 'threes', 'blocks', 'steals', 'PRA']
    else:
        prop_types = [args.prop_type]

    for prop_type in prop_types:
        try:
            if args.compare:
                evaluator.compare_all_models(prop_type)
            else:
                evaluator.backtest_model(
                    prop_type=prop_type,
                    model_name=args.model,
                    confidence_threshold=args.confidence,
                    test_size=args.test_size
                )

        except Exception as e:
            print(f"\n[ERROR] Failed to evaluate {prop_type}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
