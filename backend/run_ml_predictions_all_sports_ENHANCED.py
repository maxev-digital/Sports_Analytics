#!/usr/bin/env python3
"""
Multi-Sport ML Prediction Generator - ALL 5 SPORTS
Uses REAL team stats from TeamRankings scrapers (cached data)
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
import json
import logging
from datetime import datetime, timezone
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

from ml.feature_engineering.nba_features import NBAFeatureEngineer

# Enhanced model imports
from ml.pytorch_models.tabular_net import TabularNetTrainer
from ml.pytorch_models.catboost_model import SportsCatBoost
from ml.pytorch_models.ensemble_weighter import EnsembleWeighterTrainer
import torch
from ml.feature_engineering.ncaab_features import NCAABFeatureEngineer
from ml.feature_engineering.nhl_features import NHLFeatureEngineer
from ml.feature_engineering.nfl_features import NFLFeatureEngineer
from ml.feature_engineering.ncaaf_features import NCAAFFeatureEngineer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PREDICTIONS_DB = backend_path / "ml" / "predictions.db"

# TeamRankings cache file locations
CACHE_FILES = {
    'NFL': backend_path / "data" / "raw" / "nfl" / "teamrankings_cache.json",
    'NCAAF': backend_path / "data" / "raw" / "ncaaf" / "teamrankings_cache.json",
    'NHL': None,  # Will use different source
}

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

def load_teamrankings_cache(sport):
    """Load REAL team stats from TeamRankings cache files"""
    cache_file = CACHE_FILES.get(sport)
    if not cache_file or not cache_file.exists():
        logger.warning(f"No cache file for {sport}")
        return {}

    try:
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
            teams_data = cache_data.get('data', {})
            logger.info(f"Loaded {len(teams_data)} {sport} teams from cache")
            return teams_data
    except Exception as e:
        logger.error(f"Error loading {sport} cache: {e}")
        return {}

def normalize_team_name(team_name):
    """Normalize team names for matching"""
    # Remove common suffixes and normalize
    normalized = team_name.lower()
    normalized = normalized.replace(' football', '').replace(' basketball', '')
    return normalized.strip()

def find_team_stats(team_name, teams_cache, sport):
    """Find team stats in cache with fuzzy matching"""
    if not teams_cache:
        return None

    # Try exact match first
    if team_name in teams_cache:
        return teams_cache[team_name]

    # Try normalized matching
    normalized_input = normalize_team_name(team_name)
    for cache_team, stats in teams_cache.items():
        cache_normalized = normalize_team_name(cache_team)
        if normalized_input in cache_normalized or cache_normalized in normalized_input:
            logger.info(f"Matched '{team_name}' to '{cache_team}'")
            return stats

    logger.warning(f"No stats found for {team_name} in {sport} cache")
    return None

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

def extract_features_with_real_stats(game, sport, feature_engineer_class, teams_cache):
    """Extract features using REAL team stats from cache"""
    try:
        home_team = game.get('home_team')
        away_team = game.get('away_team')

        if not home_team or not away_team:
            return None

        # Get REAL stats from cache
        home_stats = find_team_stats(home_team, teams_cache, sport)
        away_stats = find_team_stats(away_team, teams_cache, sport)

        if not home_stats or not away_stats:
            logger.warning(f"Missing stats for {away_team} @ {home_team}")
            return None

        # Build feature data using REAL stats from cache
        if sport == 'NBA':
            # NBA uses games API stats (already working)
            game_stats = game.get('home_team_stats', {})
            if not game_stats:
                return None
            game_data = pd.Series({
                'home_pace': game_stats.get('pace', 100.0),
                'away_pace': game.get('away_team_stats', {}).get('pace', 100.0),
                'home_off_rating': game_stats.get('off_rating', 110.0),
                'away_off_rating': game.get('away_team_stats', {}).get('off_rating', 110.0),
                'home_def_rating': game_stats.get('def_rating', 110.0),
                'away_def_rating': game.get('away_team_stats', {}).get('def_rating', 110.0),
                'home_ts_pct': game_stats.get('ts_pct', 0.56),
                'away_ts_pct': game.get('away_team_stats', {}).get('ts_pct', 0.56),
                'home_efg_pct': game_stats.get('efg_pct', 0.52),
                'away_efg_pct': game.get('away_team_stats', {}).get('efg_pct', 0.52),
                'home_tov_pct': game_stats.get('tov_pct', 0.13),
                'away_tov_pct': game.get('away_team_stats', {}).get('tov_pct', 0.13),
                'home_orb_pct': game_stats.get('orb_pct', 0.25),
                'away_orb_pct': game.get('away_team_stats', {}).get('orb_pct', 0.25),
                'home_ft_rate': game_stats.get('ft_rate', 0.25),
                'away_ft_rate': game.get('away_team_stats', {}).get('ft_rate', 0.25)
            })
        elif sport == 'NFL':
            # Use REAL stats from TeamRankings cache - map to NFLFeatureEngineer expected fields
            game_data = pd.Series({
                # Offensive production (what NFLFeatureEngineer expects)
                'home_ppg': home_stats.get('pts_per_game', 22.0),
                'away_ppg': away_stats.get('pts_per_game', 22.0),
                'home_yards_per_play': home_stats.get('yards_per_play', 5.5),
                'away_yards_per_play': away_stats.get('yards_per_play', 5.5),
                'home_third_down_pct': home_stats.get('third_down_conversion_pct', 40.0),
                'away_third_down_pct': away_stats.get('third_down_conversion_pct', 40.0),

                # Defensive efficiency
                'home_points_allowed_per_game': home_stats.get('pts_allowed', 22.0),
                'away_points_allowed_per_game': away_stats.get('pts_allowed', 22.0),
                'home_yards_per_play_allowed': home_stats.get('opponent_yards_per_play', 5.5),
                'away_yards_per_play_allowed': away_stats.get('opponent_yards_per_play', 5.5),
                'home_third_down_pct_defense': home_stats.get('opponent_third_down_conversion_pct', 40.0),
                'away_third_down_pct_defense': away_stats.get('opponent_third_down_conversion_pct', 40.0),

                # Turnovers
                'home_turnover_margin': home_stats.get('turnover_diff', 0.0),
                'away_turnover_margin': away_stats.get('turnover_diff', 0.0),

                # Game situation (defaults)
                'is_division_game': 0,
                'is_primetime': 0,
                'temperature': 70.0,
                'wind_speed': 5.0
            })
        elif sport == 'NCAAF':
            # Use REAL stats from TeamRankings cache - map to NCAAFFeatureEngineer expected fields
            game_data = pd.Series({
                # Offensive production (what NCAAFFeatureEngineer expects)
                'home_ppg': home_stats.get('pts_per_game', 28.0),
                'away_ppg': away_stats.get('pts_per_game', 28.0),
                'home_yards_per_play': home_stats.get('yards_per_play', 5.8),
                'away_yards_per_play': away_stats.get('yards_per_play', 5.8),
                'home_third_down_pct': home_stats.get('third_down_conversion_pct', 40.0),
                'away_third_down_pct': away_stats.get('third_down_conversion_pct', 40.0),

                # Defensive efficiency
                'home_points_allowed_per_game': home_stats.get('pts_allowed', 28.0),
                'away_points_allowed_per_game': away_stats.get('pts_allowed', 28.0),
                'home_yards_per_play_allowed': home_stats.get('opponent_yards_per_play', 5.8),
                'away_yards_per_play_allowed': away_stats.get('opponent_yards_per_play', 5.8),
                'home_third_down_pct_defense': home_stats.get('opponent_third_down_conversion_pct', 40.0),
                'away_third_down_pct_defense': away_stats.get('opponent_third_down_conversion_pct', 40.0),

                # Turnovers
                'home_turnover_margin': home_stats.get('turnover_diff', 0.0),
                'away_turnover_margin': away_stats.get('turnover_diff', 0.0),

                # Conference strength (defaults)
                'home_conference': 'Other',
                'away_conference': 'Other',

                # Game situation and tempo
                'is_rivalry': 0,
                'is_bowl_game': 0,
                'home_plays_per_game': 70.0,
                'away_plays_per_game': 70.0
            })
        elif sport == 'NHL':
            # For NHL, use games API stats (if available) or defaults
            game_stats = game.get('home_team_stats', {})
            if not game_stats:
                return None
            game_data = pd.Series({
                'home_gf_per_game': game_stats.get('gf_per_game', 3.0),
                'away_gf_per_game': game.get('away_team_stats', {}).get('gf_per_game', 3.0),
                'home_ga_per_game': game_stats.get('ga_per_game', 3.0),
                'away_ga_per_game': game.get('away_team_stats', {}).get('ga_per_game', 3.0),
                'home_pp_pct': game_stats.get('pp_pct', 0.20),
                'away_pp_pct': game.get('away_team_stats', {}).get('pp_pct', 0.20),
                'home_pk_pct': game_stats.get('pk_pct', 0.80),
                'away_pk_pct': game.get('away_team_stats', {}).get('pk_pct', 0.80),
                'home_shots_per_game': game_stats.get('shots_per_game', 30.0),
                'away_shots_per_game': game.get('away_team_stats', {}).get('shots_per_game', 30.0)
            })
        elif sport == 'NCAAB':
            # Use games API stats (if available) or defaults
            game_stats = game.get('home_team_stats', {})
            if not game_stats:
                return None
            game_data = pd.Series({
                'home_adj_tempo': game_stats.get('adj_tempo', 70.0),
                'away_adj_tempo': game.get('away_team_stats', {}).get('adj_tempo', 70.0),
                'home_adj_off': game_stats.get('adj_off', 105.0),
                'away_adj_off': game.get('away_team_stats', {}).get('adj_off', 105.0),
                'home_adj_def': game_stats.get('adj_def', 105.0),
                'away_adj_def': game.get('away_team_stats', {}).get('adj_def', 105.0),
                'home_efg_pct': game_stats.get('efg_pct', 0.50),
                'away_efg_pct': game.get('away_team_stats', {}).get('efg_pct', 0.50),
                'home_tov_pct': game_stats.get('tov_pct', 0.18),
                'away_tov_pct': game.get('away_team_stats', {}).get('tov_pct', 0.18)
            })
        else:
            return None

        # Extract features using sport-specific engineer
        features = feature_engineer_class.get_totals_features(game_data)
        return features

    except Exception as e:
        logger.error(f"Feature extraction error for {sport}: {e}")
        return None

def predict_for_sport(sport, games, models, config, teams_cache):
    """Generate predictions for a specific sport using REAL stats"""
    predictions = []
    feature_engineer = config['feature_engineer']
    min_val, max_val = config['valid_range']

    sport_games = [g for g in games if g.get('sport', '').upper() == sport.upper()]
    logger.info(f"\n{sport}: Processing {len(sport_games)} games")

    for game in sport_games:
        try:
            # Extract features using REAL stats from cache
            features = extract_features_with_real_stats(game, sport, feature_engineer, teams_cache)
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

            # Get market value from game
            game_state = game.get('state', {})
            market_value = game_state.get('total', config['default_total'])
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

            home_team = game_state.get('home_team', {}).get('name', '')
            away_team = game_state.get('away_team', {}).get('name', '')
            game_date = game_state.get('commence_time', '')[:10] if game_state.get('commence_time') else ''
            game_time = game_state.get('commence_time', '')[11:16] if game_state.get('commence_time') else ''

            pred_id = f"{sport.lower()}_totals_{game_date}_{home_team.replace(' ', '_')}"

            predictions.append({
                'id': pred_id,
                'sport': sport.upper(),
                'bet_type': 'totals',
                'game_date': game_date,
                'game_time': game_time,
                'away_team': away_team,
                'home_team': home_team,
                'predicted_value': round(ensemble, 2),
                'market_value': round(market_value, 2),
                'edge': round(edge, 2),
                'recommendation': recommendation,
                'confidence': confidence,
                'model': 'ensemble'
            })

            logger.info(f"  ✓ {away_team} @ {home_team}: {ensemble:.1f} (edge: {edge:+.1f}%)")

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
    logger.info("MULTI-SPORT ML PREDICTION GENERATOR (Using REAL Team Stats)")
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

        # Load REAL team stats from cache
        teams_cache = load_teamrankings_cache(sport)

        # Generate predictions
        sport_predictions = predict_for_sport(sport, games, models, config, teams_cache)
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
        import traceback
        traceback.print_exc()
        sys.exit(1)
