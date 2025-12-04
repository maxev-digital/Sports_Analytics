#!/usr/bin/env python3
"""
Enhanced ML Predictions - All 7 Models + Neural Ensemble
Generates daily predictions using complete enhanced architecture

7 Models per Sport:
1. XGBoost
2. LightGBM
3. Random Forest
4. Linear Regression
5. PyTorch TabularNet
6. CatBoost
7. Neural Ensemble (combines all 6)

Usage:
    python3 run_enhanced_predictions_all_sports.py
"""

import sys
import os
import sqlite3
import numpy as np
import pandas as pd
import joblib
import torch
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add backend to path
sys.path.append('/root/sporttrader/backend')

from ml.pytorch_models.tabular_net import TabularNetTrainer
from ml.pytorch_models.catboost_model import SportsCatBoost
from ml.pytorch_models.ensemble_weighter import EnsembleWeighterTrainer
from ml.feature_engineering.nba_features import NBAFeatureEngineer
from ml.feature_engineering.ncaab_features import NCAABFeatureEngineer
from ml.feature_engineering.nhl_features import NHLFeatureEngineer
from ml.feature_engineering.nfl_features import NFLFeatureEngineer
from ml.feature_engineering.ncaaf_features import NCAAFFeatureEngineer

# Configuration
SPORTS_CONFIG = {
    'nba': {
        'engineer': NBAFeatureEngineer,
        'total_range': (180, 270),
        'enabled': True
    },
    'ncaab': {
        'engineer': NCAABFeatureEngineer,
        'total_range': (110, 180),
        'enabled': True
    },
    'nhl': {
        'engineer': NHLFeatureEngineer,
        'total_range': (4, 9),
        'enabled': True
    },
    'nfl': {
        'engineer': NFLFeatureEngineer,
        'total_range': (35, 65),
        'enabled': True
    },
    'ncaaf': {
        'engineer': NCAAFFeatureEngineer,
        'total_range': (35, 80),
        'enabled': True
    }
}

MODELS_DIR = Path('/root/sporttrader/backend/ml/models')
DB_PATH = Path('/root/sporttrader/backend/ml/predictions.db')
GAMES_API = 'http://localhost:8000/api/games'


class EnhancedMLPredictor:
    """Loads all 7 models and generates ensemble predictions"""

    def __init__(self, sport: str):
        self.sport = sport.lower()
        self.config = SPORTS_CONFIG[self.sport]
        self.models = {}
        self.feature_engineer = self.config['engineer']()
        self.total_range = self.config['total_range']

    def load_all_models(self, bet_type: str = 'totals') -> bool:
        """Load all 7 model types for this sport"""
        print(f"  Loading {self.sport.upper()} {bet_type} models...")

        model_files = {
            'xgboost': f'{self.sport}_xgboost_{bet_type}_latest.joblib',
            'lightgbm': f'{self.sport}_lightgbm_{bet_type}_latest.joblib',
            'random_forest': f'{self.sport}_random_forest_{bet_type}_latest.joblib',
            'linear': f'{self.sport}_linear_regression_{bet_type}_latest.joblib',
            'pytorch_tabular': f'{self.sport}_pytorch_tabular_{bet_type}_latest.pt',
            'catboost': f'{self.sport}_catboost_{bet_type}_latest.cbm',
            'neural_ensemble': f'{self.sport}_neural_ensemble_{bet_type}_latest.pt'
        }

        loaded_count = 0

        for model_name, filename in model_files.items():
            try:
                filepath = MODELS_DIR / filename

                if not filepath.exists():
                    print(f"    ⚠️  {model_name}: not found")
                    continue

                if model_name == 'pytorch_tabular':
                    trainer = TabularNetTrainer()
                    trainer.load(filepath)
                    self.models[model_name] = trainer

                elif model_name == 'catboost':
                    cb = SportsCatBoost(task='regression')
                    cb.load(str(filepath))
                    self.models[model_name] = cb

                elif model_name == 'neural_ensemble':
                    # Don't count ensemble in loaded models (it uses the others)
                    ensemble = EnsembleWeighterTrainer(n_models=6)
                    ensemble.load(filepath)
                    self.models[model_name] = ensemble

                else:
                    # Standard joblib models
                    self.models[model_name] = joblib.load(filepath)

                loaded_count += 1
                print(f"    ✓ {model_name}")

            except Exception as e:
                print(f"    ✗ {model_name}: {str(e)}")

        print(f"  Total: {loaded_count}/7 models loaded")
        return loaded_count >= 4  # Need at least 4 base models

    def predict_with_ensemble(self, features: np.ndarray) -> Tuple[float, Dict[str, float]]:
        """
        Generate predictions from all models and combine with neural ensemble

        Returns:
            (final_prediction, individual_predictions_dict)
        """
        if len(features.shape) == 1:
            features = features.reshape(1, -1)

        individual_preds = {}

        # Get predictions from 6 base models
        base_models = ['xgboost', 'lightgbm', 'random_forest', 'linear', 'pytorch_tabular', 'catboost']

        for model_name in base_models:
            if model_name not in self.models:
                continue

            try:
                model = self.models[model_name]

                if model_name == 'pytorch_tabular':
                    pred = model.predict(features)[0]
                elif model_name == 'catboost':
                    pred = model.predict(features)[0]
                else:
                    pred = model.predict(features)[0]

                # Constrain to valid range
                pred = np.clip(pred, self.total_range[0], self.total_range[1])
                individual_preds[model_name] = float(pred)

            except Exception as e:
                print(f"      Error with {model_name}: {e}")

        if not individual_preds:
            return None, {}

        # Use neural ensemble if available
        if 'neural_ensemble' in self.models and len(individual_preds) >= 3:
            try:
                # Prepare inputs for neural ensemble
                preds_array = np.array(list(individual_preds.values())).reshape(1, -1)
                # Use default accuracies (0.55) if no recent history
                accuracies = np.ones((1, len(individual_preds))) * 0.55

                ensemble_model = self.models['neural_ensemble']
                final_pred, weights = ensemble_model.predict(preds_array, accuracies)
                final_pred = float(final_pred[0])

                # Log which models got highest weights
                weights_dict = dict(zip(individual_preds.keys(), weights[0]))
                top_model = max(weights_dict.items(), key=lambda x: x[1])
                print(f"      Neural Ensemble: {final_pred:.1f} (top weight: {top_model[0]} {top_model[1]:.2%})")

            except Exception as e:
                print(f"      Neural Ensemble failed, using median: {e}")
                final_pred = float(np.median(list(individual_preds.values())))
        else:
            # Fallback to median
            final_pred = float(np.median(list(individual_preds.values())))
            print(f"      Median Ensemble: {final_pred:.1f}")

        # Final constraint
        final_pred = np.clip(final_pred, self.total_range[0], self.total_range[1])

        return final_pred, individual_preds


def fetch_todays_games() -> Dict[str, List[dict]]:
    """Fetch today's games from the games API"""
    print("\nFetching today's games from API...")

    try:
        response = requests.get(GAMES_API, timeout=10)
        response.raise_for_status()
        games = response.json()

        # Group by sport
        games_by_sport = {}
        for game in games:
            sport = game.get('sport', '').lower()
            if sport not in games_by_sport:
                games_by_sport[sport] = []
            games_by_sport[sport].append(game)

        # Print summary
        for sport, sport_games in games_by_sport.items():
            print(f"  {sport.upper()}: {len(sport_games)} games")

        return games_by_sport

    except Exception as e:
        print(f"  ERROR fetching games: {e}")
        return {}


def save_prediction_to_db(prediction: dict):
    """Save prediction to predictions.db"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO predictions (
            prediction_id, sport, bet_type, game_date, game_time,
            away_team, home_team, predicted_value, market_value, edge,
            recommendation, confidence, model, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        prediction['prediction_id'],
        prediction['sport'],
        prediction['bet_type'],
        prediction['game_date'],
        prediction.get('game_time', ''),
        prediction['away_team'],
        prediction['home_team'],
        prediction['predicted_value'],
        prediction['market_value'],
        prediction['edge'],
        prediction['recommendation'],
        prediction['confidence'],
        prediction['model'],
        prediction['created_at']
    ))

    conn.commit()
    conn.close()


def generate_predictions_for_sport(sport: str, games: List[dict]) -> int:
    """Generate predictions for all games in a sport"""
    print(f"\n{'='*60}")
    print(f"Processing {sport.upper()}")
    print(f"{'='*60}")

    if not games:
        print("  No games today")
        return 0

    # Initialize predictor
    predictor = EnhancedMLPredictor(sport)

    # Load models
    if not predictor.load_all_models(bet_type='totals'):
        print(f"  ERROR: Not enough models loaded for {sport}")
        return 0

    predictions_count = 0

    for game in games:
        try:
            print(f"\n  {game.get('away_team', 'Unknown')} @ {game.get('home_team', 'Unknown')}")

            # Extract features
            features = predictor.feature_engineer.get_totals_features(game)

            if features is None or len(features) == 0:
                print("    ⚠️  Could not extract features")
                continue

            # Get prediction from all 7 models
            final_pred, individual_preds = predictor.predict_with_ensemble(features)

            if final_pred is None:
                print("    ⚠️  Prediction failed")
                continue

            # Calculate edge
            market_total = game.get('total', 0)
            if market_total == 0:
                print("    ⚠️  No market total available")
                continue

            edge = ((final_pred - market_total) / market_total) * 100

            # Determine recommendation
            if edge > 2.5:
                recommendation = 'OVER'
                confidence = 'HIGH' if edge > 5 else 'MEDIUM'
            elif edge < -2.5:
                recommendation = 'UNDER'
                confidence = 'HIGH' if edge < -5 else 'MEDIUM'
            else:
                recommendation = 'NO BET'
                confidence = 'LOW'

            print(f"    Market: {market_total:.1f} | Prediction: {final_pred:.1f} | Edge: {edge:+.1f}%")
            print(f"    Recommendation: {recommendation} ({confidence})")

            # Save to database
            prediction = {
                'prediction_id': f"{sport}_totals_{game.get('game_date', '')}_{game.get('home_team', '').replace(' ', '_')}",
                'sport': sport.upper(),
                'bet_type': 'totals',
                'game_date': game.get('game_date', ''),
                'game_time': game.get('game_time', ''),
                'away_team': game.get('away_team', ''),
                'home_team': game.get('home_team', ''),
                'predicted_value': final_pred,
                'market_value': market_total,
                'edge': edge,
                'recommendation': recommendation,
                'confidence': confidence,
                'model': 'enhanced_ensemble_7_models',
                'created_at': datetime.now(timezone.utc).isoformat()
            }

            save_prediction_to_db(prediction)
            predictions_count += 1
            print("    ✓ Saved to database")

        except Exception as e:
            print(f"    ✗ Error: {e}")
            import traceback
            traceback.print_exc()

    return predictions_count


def main():
    """Main prediction workflow"""
    print("="*60)
    print("ENHANCED ML PREDICTIONS - 7 Model Architecture")
    print("="*60)
    print(f"Started: {datetime.now()}")
    print(f"Database: {DB_PATH}")
    print("="*60)

    # Fetch games
    games_by_sport = fetch_todays_games()

    if not games_by_sport:
        print("\nNo games found for today")
        return

    # Generate predictions for each sport
    total_predictions = 0

    for sport, sport_config in SPORTS_CONFIG.items():
        if not sport_config['enabled']:
            print(f"\n{sport.upper()}: DISABLED")
            continue

        games = games_by_sport.get(sport, [])
        count = generate_predictions_for_sport(sport, games)
        total_predictions += count

    # Summary
    print(f"\n{'='*60}")
    print(f"COMPLETED")
    print(f"{'='*60}")
    print(f"Total predictions generated: {total_predictions}")
    print(f"Finished: {datetime.now()}")
    print("="*60)


if __name__ == '__main__':
    main()
