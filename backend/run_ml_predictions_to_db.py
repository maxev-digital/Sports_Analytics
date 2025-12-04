#!/usr/bin/env python3
"""
ML Prediction Generator - Writes ACTUAL ML predictions directly to predictions.db
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PREDICTIONS_DB = backend_path / "ml" / "predictions.db"

def load_nba_models():
    """Load NBA totals models"""
    models_dir = backend_path / "ml" / "models"
    models = {}
    for name in ['xgboost', 'lightgbm', 'random_forest']:
        model_path = models_dir / f'nba_{name}_totals_latest.joblib'
        if model_path.exists():
            models[name] = joblib.load(model_path)
            logger.info(f"Loaded {name} model")
    return models

def fetch_games():
    """Fetch today's games from games API"""
    for url in ["http://localhost:8000/api/games", "http://148.230.87.135:8000/api/games"]:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except:
            continue
    return []

def save_to_db(predictions):
    """Save predictions to database"""
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
    logger.info(f"✓ Saved {len(predictions)} predictions to database")

def main():
    logger.info("=" * 70)
    logger.info("ML PREDICTION GENERATOR - Using ACTUAL trained models")
    logger.info("=" * 70)
    
    # Load models
    models = load_nba_models()
    if not models:
        logger.error("No models loaded!")
        return
    
    # Fetch games
    games = fetch_games()
    nba_games = [g for g in games if g.get('sport') == 'NBA']
    logger.info(f"Found {len(nba_games)} NBA games")
    
    predictions = []
    for game in nba_games:
        try:
            home_stats = game.get('home_team_stats', {})
            away_stats = game.get('away_team_stats', {})
            
            # Create feature row
            game_data = pd.Series({
                'home_pace': home_stats.get('pace', 100.0),
                'away_pace': away_stats.get('pace', 100.0),
                'home_off_rating': home_stats.get('off_rating', 110.0),
                'away_off_rating': away_stats.get('off_rating', 110.0),
                'home_def_rating': home_stats.get('def_rating', 110.0),
                'away_def_rating': away_stats.get('def_rating', 110.0),
                'home_fg_pct': home_stats.get('fg_pct', 0.45),
                'away_fg_pct': away_stats.get('fg_pct', 0.45),
                'home_fg3_pct': home_stats.get('fg3_pct', 0.35),
                'away_fg3_pct': away_stats.get('fg3_pct', 0.35),
                'home_ppg': home_stats.get('pts_per_game', 110.0),
                'away_ppg': away_stats.get('pts_per_game', 110.0),
                'home_win_pct': home_stats.get('win_pct', 0.5),
                'away_win_pct': away_stats.get('win_pct', 0.5),
                'home_wins': home_stats.get('wins', 0),
                'away_wins': away_stats.get('wins', 0),
                'home_games_played': home_stats.get('games_played', 1),
                'away_games_played': away_stats.get('games_played', 1),
            })
            
            # Extract features
            features = NBAFeatureEngineer.get_totals_features(game_data)
            
            # Get predictions
            preds = {}
            for name, model in models.items():
                preds[name] = model.predict(features)[0]
            
            # Ensemble median
            ensemble = np.median(list(preds.values()))
            ensemble = max(110.0, min(270.0, ensemble))  # Clamp to valid NBA range
            
            # Get market total
            market_total = game.get('projection', {}).get('pregame_total', 225.0)
            edge = ensemble - market_total
            
            # Create prediction
            game_date = game['state']['commence_time'][:10]
            game_time = game['state']['commence_time'][11:16]
            
            predictions.append({
                'id': f"nba_totals_{game_date}_{game['state']['home_team']['name'].replace(' ', '_')}",
                'sport': 'NBA',
                'bet_type': 'totals',
                'game_date': game_date,
                'game_time': game_time,
                'away_team': game['state']['away_team']['name'],
                'home_team': game['state']['home_team']['name'],
                'predicted_value': ensemble,
                'market_value': market_total,
                'edge': edge,
                'recommendation': 'OVER' if edge > 2 else 'UNDER' if edge < -2 else 'NO BET',
                'confidence': 'HIGH' if abs(edge) > 5 else 'MEDIUM' if abs(edge) > 3 else 'LOW',
                'model': 'ensemble'
            })
            
            logger.info(f"{game['state']['away_team']['name']} @ {game['state']['home_team']['name']}: {ensemble:.1f} (market: {market_total:.1f}, edge: {edge:+.1f})")
            
        except Exception as e:
            logger.error(f"Error processing game: {e}")
    
    # Save to database
    if predictions:
        save_to_db(predictions)
        logger.info(f"\n✓ Generated {len(predictions)} NBA predictions using ACTUAL ML models")
    else:
        logger.warning("No predictions generated")

if __name__ == "__main__":
    main()
