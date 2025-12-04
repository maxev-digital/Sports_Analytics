#!/usr/bin/env python3
"""
Multi-Sport ML Prediction Generator - ALL 5 SPORTS
Generates predictions using ACTUAL trained ML models for:
- NBA, NCAAB, NHL, NFL, NCAAF
"""
import sys
import os
from pathlib import Path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

import joblib
import sqlite3
import pandas as pd
import numpy as np
import requests
import logging
from datetime import datetime, timezone
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

from ml.feature_engineering.nba_features import NBAFeatureEngineer
from ml.feature_engineering.ncaab_features import NCAABFeatureEngineer
from ml.feature_engineering.nhl_features import NHLFeatureEngineer
from ml.feature_engineering.nfl_features import NFLFeatureEngineer
from ml.feature_engineering.ncaaf_features import NCAAFFeatureEngineer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PREDICTIONS_DB = backend_path / "ml" / "predictions.db"

# Sport-specific configuration
SPORT_CONFIG = {
    'NBA': {
        'feature_engineer': NBAFeatureEngineer,
        'valid_range': (110, 270),
        'default_total': 220
    },
    'NCAAB': {
        'feature_engineer': NCAABFeatureEngineer,
        'valid_range': (100, 200),
        'default_total': 145
    },
    'NHL': {
        'feature_engineer': NHLFeatureEngineer,
        'valid_range': (4, 10),
        'default_total': 6.5
    },
    'NFL': {
        'feature_engineer': NFLFeatureEngineer,
        'valid_range': (30, 70),
        'default_total': 45
    },
    'NCAAF': {
        'feature_engineer': NCAAFFeatureEngineer,
        'valid_range': (35, 85),
        'default_total': 55
    }
}

def load_sport_models(sport):
    """Load models for a specific sport"""
    models_dir = backend_path / "ml" / "models"
    models = {}
    sport_lower = sport.lower()

    for name in ['xgboost', 'lightgbm', 'random_forest']:
        model_path = models_dir / f'{sport_lower}_{name}_totals_latest.joblib'
        if model_path.exists():
            models[name] = joblib.load(model_path)
            logger.info(f"  ✓ Loaded {sport} {name} model")

    return models

def fetch_games():
    """Fetch today's games from games API"""
    for url in ["http://localhost:8000/api/games", "http://148.230.87.135:8000/api/games"]:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            continue
    return []

def extract_features(game, sport, feature_engineer_class):
    """Extract features for a game using sport-specific feature engineer"""
    try:
        home_stats = game.get('home_team_stats', {})
        away_stats = game.get('away_team_stats', {})

        # Common feature extraction pattern
        if sport == 'NBA':
            game_data = pd.Series({
                'home_pace': home_stats.get('pace', 100.0),
                'away_pace': away_stats.get('pace', 100.0),
                'home_off_rating': home_stats.get('off_rating', 110.0),
                'away_off_rating': away_stats.get('off_rating', 110.0),
                'home_def_rating': home_stats.get('def_rating', 110.0),
                'away_def_rating': away_stats.get('def_rating', 110.0),
                'home_ts_pct': home_stats.get('ts_pct', 0.56),
                'away_ts_pct': away_stats.get('ts_pct', 0.56),
                'home_efg_pct': home_stats.get('efg_pct', 0.52),
                'away_efg_pct': away_stats.get('efg_pct', 0.52),
                'home_tov_pct': home_stats.get('tov_pct', 0.13),
                'away_tov_pct': away_stats.get('tov_pct', 0.13),
                'home_orb_pct': home_stats.get('orb_pct', 0.25),
                'away_orb_pct': away_stats.get('orb_pct', 0.25),
                'home_ft_rate': home_stats.get('ft_rate', 0.25),
                'away_ft_rate': away_stats.get('ft_rate', 0.25)
            })
        elif sport == 'NCAAB':
            game_data = pd.Series({
                'home_adj_tempo': home_stats.get('adj_tempo', 70.0),
                'away_adj_tempo': away_stats.get('adj_tempo', 70.0),
                'home_adj_off': home_stats.get('adj_off', 105.0),
                'away_adj_off': away_stats.get('adj_off', 105.0),
                'home_adj_def': home_stats.get('adj_def', 105.0),
                'away_adj_def': away_stats.get('adj_def', 105.0),
                'home_efg_pct': home_stats.get('efg_pct', 0.50),
                'away_efg_pct': away_stats.get('efg_pct', 0.50),
                'home_tov_pct': home_stats.get('tov_pct', 0.18),
                'away_tov_pct': away_stats.get('tov_pct', 0.18)
            })
        elif sport == 'NHL':
            game_data = pd.Series({
                'home_gf_per_game': home_stats.get('gf_per_game', 3.0),
                'away_gf_per_game': away_stats.get('gf_per_game', 3.0),
                'home_ga_per_game': home_stats.get('ga_per_game', 3.0),
                'away_ga_per_game': away_stats.get('ga_per_game', 3.0),
                'home_pp_pct': home_stats.get('pp_pct', 0.20),
                'away_pp_pct': away_stats.get('pp_pct', 0.20),
                'home_pk_pct': home_stats.get('pk_pct', 0.80),
                'away_pk_pct': away_stats.get('pk_pct', 0.80),
                'home_shots_per_game': home_stats.get('shots_per_game', 30.0),
                'away_shots_per_game': away_stats.get('shots_per_game', 30.0)
            })
        elif sport == 'NFL':
            game_data = pd.Series({
                'home_ppg': home_stats.get('ppg', 22.0),
                'away_ppg': away_stats.get('ppg', 22.0),
                'home_papg': home_stats.get('papg', 22.0),
                'away_papg': away_stats.get('papg', 22.0),
                'home_ypg': home_stats.get('ypg', 350.0),
                'away_ypg': away_stats.get('ypg', 350.0),
                'home_pass_ypg': home_stats.get('pass_ypg', 230.0),
                'away_pass_ypg': away_stats.get('pass_ypg', 230.0),
                'home_rush_ypg': home_stats.get('rush_ypg', 120.0),
                'away_rush_ypg': away_stats.get('rush_ypg', 120.0)
            })
        elif sport == 'NCAAF':
            game_data = pd.Series({
                'home_ppg': home_stats.get('ppg', 28.0),
                'away_ppg': away_stats.get('ppg', 28.0),
                'home_papg': home_stats.get('papg', 28.0),
                'away_papg': away_stats.get('papg', 28.0),
                'home_ypg': home_stats.get('ypg', 400.0),
                'away_ypg': away_stats.get('ypg', 400.0),
                'home_pass_ypg': home_stats.get('pass_ypg', 250.0),
                'away_pass_ypg': away_stats.get('pass_ypg', 250.0),
                'home_rush_ypg': home_stats.get('rush_ypg', 150.0),
                'away_rush_ypg': away_stats.get('rush_ypg', 150.0)
            })
        else:
            return None

        # Extract features using sport-specific engineer
        features = feature_engineer_class.get_totals_features(game_data)
        return features

    except Exception as e:
        logger.error(f"Feature extraction error for {sport}: {e}")
        return None

def predict_for_sport(sport, games, models, config):
    """Generate predictions for a specific sport"""
    predictions = []
    feature_engineer = config['feature_engineer']
    min_val, max_val = config['valid_range']

    sport_games = [g for g in games if g.get('sport', '').upper() == sport.upper()]
    logger.info(f"\n{sport}: Processing {len(sport_games)} games")

    for game in sport_games:
        try:
            # Extract features
            features = extract_features(game, sport, feature_engineer)
            if features is None:
                continue

            # Get predictions from all models
            preds = {}
            for name, model in models.items():
                pred = model.predict(features)[0]
                preds[name] = pred

            if not preds:
                continue

            # Ensemble: median of all predictions
            ensemble = np.median(list(preds.values()))
            ensemble = max(min_val, min(max_val, ensemble))

            # Get market value
            market_value = game.get('total', config['default_total'])
            edge = ((ensemble - market_value) / market_value) * 100

            # Determine recommendation
            if edge > 2.5:
                recommendation = "OVER"
                confidence = "HIGH" if edge > 5 else "MEDIUM"
            elif edge < -2.5:
                recommendation = "UNDER"
                confidence = "HIGH" if edge < -5 else "MEDIUM"
            else:
                recommendation = "NO BET"
                confidence = "LOW"

            pred_id = f"{sport.lower()}_totals_{game.get('game_date', '')}_{game.get('home_team', '').replace(' ', '_')}"

            predictions.append({
                'id': pred_id,
                'sport': sport.upper(),
                'bet_type': 'totals',
                'game_date': game.get('game_date', ''),
                'game_time': game.get('game_time', ''),
                'away_team': game.get('away_team', ''),
                'home_team': game.get('home_team', ''),
                'predicted_value': round(ensemble, 2),
                'market_value': round(market_value, 2),
                'edge': round(edge, 2),
                'recommendation': recommendation,
                'confidence': confidence,
                'model': 'ensemble'
            })

            logger.info(f"  ✓ {game.get('away_team')} @ {game.get('home_team')}: {ensemble:.1f} (edge: {edge:+.1f}%)")

        except Exception as e:
            logger.error(f"  ✗ Prediction error: {e}")
            continue

    return predictions

def save_to_db(predictions):
    """Save predictions to database"""
    if not predictions:
        logger.warning("No predictions to save")
        return

    conn = sqlite3.connect(str(PREDICTIONS_DB))
    cursor = conn.cursor()

    for pred in predictions:
        cursor.execute('''INSERT OR REPLACE INTO predictions (
            prediction_id, sport, bet_type, game_date, game_time,
            away_team, home_team, predicted_value, market_value, edge,
            recommendation, confidence, model, kelly_pct,
            over_probability, under_probability, expected_value, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
            pred['id'], pred['sport'], pred['bet_type'], pred['game_date'], pred['game_time'],
            pred['away_team'], pred['home_team'], pred['predicted_value'], pred['market_value'],
            pred['edge'], pred['recommendation'], pred['confidence'], pred['model'],
            0.0, 0.5, 0.5, 0.0, datetime.now(timezone.utc).isoformat()
        ))

    conn.commit()
    conn.close()
    logger.info(f"\n✓ Saved {len(predictions)} total predictions to database")

def main():
    logger.info("=" * 80)
    logger.info("MULTI-SPORT ML PREDICTION GENERATOR")
    logger.info("Using ACTUAL trained models for NBA, NCAAB, NHL, NFL, NCAAF")
    logger.info("=" * 80)

    # Fetch all games
    logger.info("\nFetching games from API...")
    games = fetch_games()
    logger.info(f"Found {len(games)} total games")

    all_predictions = []

    # Process each sport
    for sport, config in SPORT_CONFIG.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {sport}")
        logger.info(f"{'='*60}")

        # Load models
        models = load_sport_models(sport)
        if not models:
            logger.warning(f"No models found for {sport}")
            continue

        # Generate predictions
        sport_predictions = predict_for_sport(sport, games, models, config)
        all_predictions.extend(sport_predictions)

    # Save all predictions
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Total predictions generated: {len(all_predictions)}")

    if all_predictions:
        save_to_db(all_predictions)
        logger.info("\n✅ SUCCESS: All predictions saved to predictions.db")
    else:
        logger.warning("\n⚠️  No predictions generated")

    return len(all_predictions)

if __name__ == "__main__":
    try:
        count = main()
        sys.exit(0 if count > 0 else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
