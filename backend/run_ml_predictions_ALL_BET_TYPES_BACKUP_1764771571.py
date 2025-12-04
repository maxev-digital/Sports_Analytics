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
from ml.feature_engineering.ncaab_features import NCAABFeatureEngineer
from ml.feature_engineering.nhl_features import NHLFeatureEngineer
from ml.feature_engineering.nfl_features import NFLFeatureEngineer
from ml.feature_engineering.ncaaf_features import NCAAFFeatureEngineer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PREDICTIONS_DB = backend_path / "ml" / "predictions.db"

# TeamRankings cache file locations
CACHE_FILES = {
    'NBA': backend_path / "data" / "raw" / "nba" / "teamrankings_cache.json",
    'NCAAB': backend_path / "data" / "raw" / "ncaab" / "teamrankings_cache.json",
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
            
            # Handle NCAAB nested structure: {data: {teams: {...}}}
            if sport == 'NCAAB' and 'teams' in teams_data:
                teams_data = teams_data['teams']
            
            logger.info(f"Loaded {len(teams_data)} {sport} teams from cache")
            return teams_data
    except Exception as e:
        logger.error(f"Error loading {sport} cache: {e}")
        return {}

def normalize_team_name(team_name):
    """Normalize team names with abbreviation support"""
    normalized = team_name.lower()
    
    # Remove sport suffixes
    normalized = normalized.replace(' football', '').replace(' basketball', '')
    
    # Abbreviation mapping
    abbrev_map = {
        'saint': 'st', 'st.': 'st',
        'southern': 's', 'south': 's',
        'northern': 'n', 'north': 'n',
        'eastern': 'e', 'east': 'e',
        'western': 'w', 'west': 'w',
        'central': 'c',
        'state': 'st',
        'university': 'u',
        'mount': 'mt',
        'fort': 'ft',
        'college': '',
        'and': '&',
        'texas a&m': 'texas am',  # Special case
    }
    
    for long_form, short_form in abbrev_map.items():
        normalized = normalized.replace(long_form, short_form)
    
    # Remove mascots
    mascots = [
        'bulldogs', 'wildcats', 'tigers', 'bears', 'lions', 'panthers', 'eagles', 'hawks',
        'falcons', 'cardinals', 'blue devils', 'demon deacons', 'tar heels', 'hokies',
        'cavaliers', 'terrapins', 'orange', 'minutemen', 'huskies', 'golden eagles',
        'aggies', 'rebels', 'commodores', 'volunteers', 'gators', 'seminoles', 'hurricanes',
        'wolfpack', 'gamecocks', 'razorbacks', 'sooners', 'longhorns', 'cowboys', 'jayhawks',
        'cyclones', 'mountaineers', 'red raiders', 'horned frogs', 'bruins', 'trojans',
        'sun devils', 'utes', 'cougars', 'ducks', 'beavers', 'golden bears', 'cardinal',
        'spartans', 'wolverines', 'buckeyes', 'nittany lions', 'badgers', 'cornhuskers',
        'fighting irish', 'crimson tide', 'war eagle', 'plainsmen', 'bulldawgs', 'redbirds',
        'pirates', 'raiders', 'knights', 'owls', 'penguins', 'rockets', 'phoenix', 'rams',
        'seawolves', 'retrievers', 'greyhounds', 'privateers', 'chanticleers', 'monarchs'
    ]
    
    for mascot in mascots:
        normalized = normalized.replace(f' {mascot}', '')
    
    # Clean up extra spaces
    normalized = ' '.join(normalized.split())
    
    return normalized.strip()

def find_team_stats(team_name, teams_cache, sport):
    """Find team stats using enhanced fuzzy matching"""
    normalized_input = normalize_team_name(team_name)
    input_words = set(normalized_input.split())
    
    best_match = None
    best_score = 0
    best_cache_team = None
    
    for cache_team, stats in teams_cache.items():
        cache_normalized = normalize_team_name(cache_team)
        cache_words = set(cache_normalized.split())
        
        # Calculate overlap
        overlap = len(input_words & cache_words)
        
        if overlap == 0:
            continue
        
        # Word overlap score (what % of max word count matches)
        max_words = max(len(input_words), len(cache_words))
        word_score = overlap / max_words
        
        # Coverage score (what % of smaller name is covered)
        min_words = min(len(input_words), len(cache_words))
        coverage_score = overlap / min_words
        
        # Combined score (favor coverage to handle abbreviations)
        combined_score = (word_score * 0.4) + (coverage_score * 0.6)
        
        if combined_score > best_score:
            best_score = combined_score
            best_match = stats
            best_cache_team = cache_team
    
    # Lowered threshold to 0.35 for better abbreviation matching
    if best_match and best_score >= 0.35:
        logger.info(f"  Returning stats: {list(best_match.keys())[:5] if isinstance(best_match, dict) else type(best_match)}")
        logger.info(f"✓ Matched '{team_name}' → '{best_cache_team}' (score: {best_score:.2f})")
        return best_match
    else:
        logger.warning(f"✗ No match for '{team_name}' (best: {best_cache_team} @ {best_score:.2f})")
        return None


def load_sport_models(sport, bet_type="totals"):
    """Load models for a specific sport"""
    models_dir = backend_path / "ml" / "models"
    models = {}
    sport_lower = sport.lower()

    for name in ['xgboost', 'lightgbm', 'random_forest', 'linear', 'catboost']:
        model_path = models_dir / f'{sport_lower}_{name}_{bet_type}_enhanced.joblib'
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

        # For NHL, use stats from game object instead of cache
        if sport != 'NHL':
            # Get REAL stats from cache (for NFL and NCAAF)
            home_stats = find_team_stats(home_team, teams_cache, sport)
            away_stats = find_team_stats(away_team, teams_cache, sport)

            if not home_stats or not away_stats:
                logger.warning(f"Missing stats for {away_team} @ {home_team}")
                return None

        # Build feature data using REAL stats from cache
        if sport == 'NBA':
            # NBA uses teamrankings cache now (40 features expected by models)
            # Map cache stats to feature engineer expected format
            game_data = pd.Series({
                # Pace
                'home_pace': home_stats.get('pace', 100.0),
                'away_pace': away_stats.get('pace', 100.0),
                # Ratings (estimate from ppg/allowed)
                'home_off_rating': home_stats.get('pts_per_game', 110.0),
                'away_off_rating': away_stats.get('pts_per_game', 110.0),
                'home_def_rating': away_stats.get('pts_allowed', 110.0),  # Opponent's offense
                'away_def_rating': home_stats.get('pts_allowed', 110.0),
                # Shooting
                'home_fg_pct': home_stats.get('field_goal_pct', 46.0) / 100.0,
                'away_fg_pct': away_stats.get('field_goal_pct', 46.0) / 100.0,
                'home_fg3_pct': home_stats.get('three_point_pct', 36.0) / 100.0,
                'away_fg3_pct': away_stats.get('three_point_pct', 36.0) / 100.0,
                # Advanced (use defaults if missing)
                'home_ts_pct': 0.56,
                'away_ts_pct': 0.56,
                'home_efg_pct': home_stats.get('effective_field_goal_pct', 52.0) / 100.0,
                'away_efg_pct': away_stats.get('effective_field_goal_pct', 52.0) / 100.0,
                'home_tov_pct': 0.13,
                'away_tov_pct': 0.13,
                'home_orb_pct': 0.25,
                'away_orb_pct': 0.25,
                'home_ft_rate': home_stats.get('free_throw_pct', 75.0) / 100.0,
                'away_ft_rate': away_stats.get('free_throw_pct', 75.0) / 100.0,
                # Rebounds
                'home_rebounds': home_stats.get('total_rebounds', 44.0),
                'away_rebounds': away_stats.get('total_rebounds', 44.0),
                # Other
                'home_assists': home_stats.get('assists', 25.0),
                'away_assists': away_stats.get('assists', 25.0),
                'home_turnovers': home_stats.get('turnovers', 14.0),
                'away_turnovers': away_stats.get('turnovers', 14.0),
                'home_steals': home_stats.get('steals', 8.0),
                'away_steals': away_stats.get('steals', 8.0),
                'home_blocks': home_stats.get('blocks', 5.0),
                'away_blocks': away_stats.get('blocks', 5.0),
                # Win/loss (use win_pct if available)
                'home_win_pct': home_stats.get('win_pct', 0.5),
                'away_win_pct': away_stats.get('win_pct', 0.5),
                # Momentum (defaults)
                'home_momentum': 0.0,
                'away_momentum': 0.0,
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
            # For NHL, use NHL-specific stats from games API
            home_nhl_stats = game.get('home_nhl_stats', {})
            away_nhl_stats = game.get('away_nhl_stats', {})

            if not home_nhl_stats or not away_nhl_stats:
                logger.warning(f"Missing NHL stats for {away_team} @ {home_team}")
                return None

            # Map NHL stats to feature engineer expected fields
            game_data = pd.Series({
                # Core offensive stats
                'home_goals_per_game': home_nhl_stats.get('goals_per_game', 3.0),
                'away_goals_per_game': away_nhl_stats.get('goals_per_game', 3.0),
                'home_shots_per_game': home_nhl_stats.get('shots_per_game', 30.0),
                'away_shots_per_game': away_nhl_stats.get('shots_per_game', 30.0),
                'home_shooting_pct': home_nhl_stats.get('shooting_pct', 10.0) / 100.0,  # Convert to decimal
                'away_shooting_pct': away_nhl_stats.get('shooting_pct', 10.0) / 100.0,
                'home_power_play_pct': home_nhl_stats.get('power_play_pct', 20.0) / 100.0,
                'away_power_play_pct': away_nhl_stats.get('power_play_pct', 20.0) / 100.0,

                # Defensive stats
                'home_goals_against_per_game': home_nhl_stats.get('goals_against_per_game', 3.0),
                'away_goals_against_per_game': away_nhl_stats.get('goals_against_per_game', 3.0),
                'home_shots_against_per_game': home_nhl_stats.get('shots_against_per_game', 30.0),
                'away_shots_against_per_game': away_nhl_stats.get('shots_against_per_game', 30.0),
                'home_penalty_kill_pct': home_nhl_stats.get('penalty_kill_pct', 80.0) / 100.0,
                'away_penalty_kill_pct': away_nhl_stats.get('penalty_kill_pct', 80.0) / 100.0,
                'home_save_pct': home_nhl_stats.get('save_pct', 90.0) / 100.0,
                'away_save_pct': away_nhl_stats.get('save_pct', 90.0) / 100.0,

                # Advanced stats
                'home_pdo': home_nhl_stats.get('pdo', 100.0),
                'away_pdo': away_nhl_stats.get('pdo', 100.0),
                'home_faceoff_win_pct': home_nhl_stats.get('faceoff_win_pct', 50.0) / 100.0,
                'away_faceoff_win_pct': away_nhl_stats.get('faceoff_win_pct', 50.0) / 100.0,

                # Goalie stats (same as team save pct if not available)
                'home_goalie_save_pct': home_nhl_stats.get('save_pct', 90.0) / 100.0,
                'away_goalie_save_pct': away_nhl_stats.get('save_pct', 90.0) / 100.0,
                'home_goalie_gaa': home_nhl_stats.get('goals_against_per_game', 3.0),
                'away_goalie_gaa': away_nhl_stats.get('goals_against_per_game', 3.0),

                # Empty net stats (new features)
                'home_en_goals_for_per_game': home_nhl_stats.get('en_goals_for', 0.0) / max(home_nhl_stats.get('games_played', 1), 1),
                'away_en_goals_for_per_game': away_nhl_stats.get('en_goals_for', 0.0) / max(away_nhl_stats.get('games_played', 1), 1),
                'home_en_goals_against_per_game': home_nhl_stats.get('en_goals_against', 0.0) / max(home_nhl_stats.get('games_played', 1), 1),
                'away_en_goals_against_per_game': away_nhl_stats.get('en_goals_against', 0.0) / max(away_nhl_stats.get('games_played', 1), 1),
                'home_en_success_rate': home_nhl_stats.get('en_success_rate', 0.0),
                'away_en_success_rate': away_nhl_stats.get('en_success_rate', 0.0),
            })
        elif sport == 'NCAAB':
            # Use REAL stats from TeamRankings cache - return RAW features (8 features to match training)
            # Training used: home_adj_em, away_adj_em, home_adj_off_eff, away_adj_off_eff, 
            #                home_adj_def_eff, away_adj_def_eff, home_adj_tempo, away_adj_tempo
            features = np.array([
                home_stats.get('adj_em', 0.0),  # home_adj_em
                away_stats.get('adj_em', 0.0),  # away_adj_em
                home_stats.get('offensive_efficiency', 1.05) * 100,  # home_adj_off_eff
                away_stats.get('offensive_efficiency', 1.05) * 100,  # away_adj_off_eff
                home_stats.get('defensive_efficiency', 1.05) * 100,  # home_adj_def_eff
                away_stats.get('defensive_efficiency', 1.05) * 100,  # away_adj_def_eff
                home_stats.get('possessions_per_game', 70.0),        # home_adj_tempo
                away_stats.get('possessions_per_game', 70.0)         # away_adj_tempo
            ])
            logger.info(f"  NCAAB features for {home_team}: {features}")
            return features.reshape(1, -1)  # Return as 2D array for model.predict()
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
            home_team = game_state.get('home_team', {}).get('name', '') or game.get('home_team', '')
            away_team = game_state.get('away_team', {}).get('name', '') or game.get('away_team', '')
            # Convert UTC commence_time to CST date/time
            commence_time_utc = game_state.get('commence_time', '') or game.get('commence_time', '') or game.get('date', '')
            if commence_time_utc:
                from datetime import datetime
                import pytz
                utc_dt = datetime.fromisoformat(commence_time_utc.replace('Z', '+00:00'))
                cst_dt = utc_dt.astimezone(pytz.timezone('America/Chicago'))
                game_date = cst_dt.strftime('%Y-%m-%d')
                game_time = cst_dt.strftime('%H:%M')
            else:
                game_date = ''
                game_time = ''
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
        # Loop through all bet types for this sport
        bet_types = ["totals", "spreads", "moneyline"] if sport != "NCAAB" else ["totals"]
        for bet_type in bet_types:
            models = load_sport_models(sport, bet_type)
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
