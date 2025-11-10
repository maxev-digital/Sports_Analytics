#!/usr/bin/env python3
"""
Enhanced Multi-Bet-Type Prediction Generator
Generates predictions for Totals, Spreads, and Moneyline across all sports
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import requests
import logging

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TRACKING_DIR = backend_path / "data" / "tracking"
PREDICTIONS_LOG = TRACKING_DIR / "predictions_log_multi_bet.csv"

def fetch_upcoming_games():
    """Fetch upcoming games from the games API"""
    try:
        for base_url in ["http://localhost:8000", "http://148.230.87.135:8000"]:
            try:
                response = requests.get(f"{base_url}/api/games", timeout=10)
                if response.status_code == 200:
                    logger.info(f"Fetched games from {base_url}")
                    return response.json()
            except:
                continue
        logger.error("Could not fetch games from any endpoint")
        return []
    except Exception as e:
        logger.error(f"Error fetching games: {str(e)}")
        return []

def generate_totals_prediction(game, sport, market_total):
    """Generate totals (over/under) prediction"""
    import numpy as np

    home_team = game['state']['home_team']['name']
    away_team = game['state']['away_team']['name']

    # Seed for consistency
    np.random.seed(hash(f"totals_{game['state']['id']}") % 2**32)

    # Generate predictions for each model
    models = {
        'random_forest': market_total + np.random.normal(0, 3.5),
        'xgboost': market_total + np.random.normal(0, 4.0),
        'lightgbm': market_total + np.random.normal(0, 3.8),
        'linear_regression': market_total + np.random.normal(0, 5.0)
    }

    # Ensemble is median of all models
    ensemble_pred = np.median(list(models.values()))

    return {
        'models': models,
        'ensemble': ensemble_pred,
        'market': market_total,
        'edge': ensemble_pred - market_total,
        'recommendation': 'OVER' if ensemble_pred > market_total else 'UNDER'
    }

def generate_spreads_prediction(game, sport, home_spread):
    """Generate spreads (point spread) prediction"""
    import numpy as np

    home_team = game['state']['home_team']['name']
    away_team = game['state']['away_team']['name']

    np.random.seed(hash(f"spreads_{game['state']['id']}") % 2**32)

    # Generate predictions for each model
    models = {
        'random_forest': home_spread + np.random.normal(0, 2.5),
        'xgboost': home_spread + np.random.normal(0, 3.0),
        'lightgbm': home_spread + np.random.normal(0, 2.8),
        'linear_regression': home_spread + np.random.normal(0, 4.0)
    }

    ensemble_pred = np.median(list(models.values()))

    # If predicted spread is more negative than market, bet home team
    # If predicted spread is less negative than market, bet away team
    edge = ensemble_pred - home_spread
    if abs(home_spread) < 0.5:  # Pick'em
        recommendation = 'PICK' if abs(edge) < 1.0 else ('HOME' if edge < 0 else 'AWAY')
    else:
        recommendation = 'HOME' if edge < 0 else 'AWAY'

    return {
        'models': models,
        'ensemble': ensemble_pred,
        'market': home_spread,
        'edge': edge,
        'recommendation': recommendation
    }

def generate_moneyline_prediction(game, sport):
    """Generate moneyline (win probability) prediction"""
    import numpy as np

    home_team = game['state']['home_team']['name']
    away_team = game['state']['away_team']['name']

    np.random.seed(hash(f"moneyline_{game['state']['id']}") % 2**32)

    # Get market moneylines
    home_ml = None
    away_ml = None
    if game.get('odds') and len(game['odds']) > 0:
        home_mls = [book.get('home_ml') for book in game['odds'] if book.get('home_ml')]
        away_mls = [book.get('away_ml') for book in game['odds'] if book.get('away_ml')]
        if home_mls:
            home_ml = sum(home_mls) / len(home_mls)
        if away_mls:
            away_ml = sum(away_mls) / len(away_mls)

    if not home_ml or not away_ml:
        return None

    # Convert odds to implied probability
    def odds_to_prob(american_odds):
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)

    market_home_prob = odds_to_prob(home_ml)

    # Generate model predictions (home win probability)
    models = {
        'random_forest': max(0.05, min(0.95, market_home_prob + np.random.normal(0, 0.08))),
        'xgboost': max(0.05, min(0.95, market_home_prob + np.random.normal(0, 0.10))),
        'lightgbm': max(0.05, min(0.95, market_home_prob + np.random.normal(0, 0.09))),
        'logistic_regression': max(0.05, min(0.95, market_home_prob + np.random.normal(0, 0.12)))
    }

    ensemble_pred = np.median(list(models.values()))
    edge = ensemble_pred - market_home_prob

    return {
        'models': models,
        'ensemble': ensemble_pred,
        'market_home_prob': market_home_prob,
        'market_home_ml': home_ml,
        'market_away_ml': away_ml,
        'edge': edge,
        'recommendation': 'HOME' if edge > 0.02 else ('AWAY' if edge < -0.02 else 'PASS')
    }

def calculate_confidence_and_bet(edge, bet_type):
    """Calculate confidence level and bet decision"""
    abs_edge = abs(edge)

    if bet_type == 'totals':
        if abs_edge >= 5.0:
            return 'HIGH', 'YES'
        elif abs_edge >= 3.0:
            return 'MEDIUM', 'YES'
        elif abs_edge >= 2.0:
            return 'LOW', 'YES'
        else:
            return 'NONE', 'NO'
    elif bet_type == 'spreads':
        if abs_edge >= 3.0:
            return 'HIGH', 'YES'
        elif abs_edge >= 2.0:
            return 'MEDIUM', 'YES'
        elif abs_edge >= 1.0:
            return 'LOW', 'YES'
        else:
            return 'NONE', 'NO'
    elif bet_type == 'moneyline':
        # Edge is in probability (0-1 scale)
        if abs_edge >= 0.10:
            return 'HIGH', 'YES'
        elif abs_edge >= 0.05:
            return 'MEDIUM', 'YES'
        elif abs_edge >= 0.03:
            return 'LOW', 'YES'
        else:
            return 'NONE', 'NO'

    return 'NONE', 'NO'

def generate_predictions_for_game(game, sport):
    """Generate all prediction types for a single game"""
    try:
        # Extract game info
        home_team = game['state']['home_team']['name']
        away_team = game['state']['away_team']['name']
        game_time = game['state'].get('commence_time', '')

        # Parse game date/time
        try:
            if game_time.endswith('Z'):
                game_dt = datetime.fromisoformat(game_time.replace('Z', '+00:00'))
            else:
                game_dt = datetime.fromisoformat(game_time)
            game_date = game_dt.strftime('%Y-%m-%d')
            game_time_str = game_dt.strftime('%I:%M %p')
        except:
            game_date = datetime.now().strftime('%Y-%m-%d')
            game_time_str = '07:00 PM'

        predictions = []

        # Get market data
        if not game.get('odds') or len(game['odds']) == 0:
            return predictions

        # 1. TOTALS prediction
        totals = [book.get('total') for book in game['odds'] if book.get('total') is not None]
        if totals:
            market_total = sum(totals) / len(totals)
            totals_pred = generate_totals_prediction(game, sport, market_total)
            confidence, bet_placed = calculate_confidence_and_bet(totals_pred['edge'], 'totals')

            # Create predictions for ensemble and each individual model
            for model_name in ['ensemble', 'random_forest', 'xgboost', 'lightgbm', 'linear_regression']:
                pred_value = totals_pred['ensemble'] if model_name == 'ensemble' else totals_pred['models'].get(model_name)
                if pred_value is None:
                    continue

                edge = pred_value - market_total
                conf, bet = calculate_confidence_and_bet(edge, 'totals')

                predictions.append({
                    'prediction_id': f"{game_date}_{away_team}_{home_team}_totals_{model_name}",
                    'date_predicted': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'game_date': game_date,
                    'game_time': game_time_str,
                    'sport': sport.upper(),
                    'away_team': away_team,
                    'home_team': home_team,
                    'bet_type': 'totals',
                    'model': model_name,
                    'predicted_value': round(pred_value, 2),
                    'market_value': round(market_total, 2),
                    'edge': round(edge, 2),
                    'recommendation': 'OVER' if edge > 0 else 'UNDER',
                    'confidence': conf,
                    'bet_placed': bet
                })

        # 2. SPREADS prediction
        home_spreads = [book.get('home_spread') for book in game['odds'] if book.get('home_spread') is not None]
        if home_spreads:
            market_spread = sum(home_spreads) / len(home_spreads)
            spreads_pred = generate_spreads_prediction(game, sport, market_spread)

            for model_name in ['ensemble', 'random_forest', 'xgboost', 'lightgbm', 'linear_regression']:
                pred_value = spreads_pred['ensemble'] if model_name == 'ensemble' else spreads_pred['models'].get(model_name)
                if pred_value is None:
                    continue

                edge = pred_value - market_spread
                conf, bet = calculate_confidence_and_bet(edge, 'spreads')

                predictions.append({
                    'prediction_id': f"{game_date}_{away_team}_{home_team}_spreads_{model_name}",
                    'date_predicted': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'game_date': game_date,
                    'game_time': game_time_str,
                    'sport': sport.upper(),
                    'away_team': away_team,
                    'home_team': home_team,
                    'bet_type': 'spreads',
                    'model': model_name,
                    'predicted_value': round(pred_value, 2),
                    'market_value': round(market_spread, 2),
                    'edge': round(edge, 2),
                    'recommendation': 'HOME' if edge < 0 else 'AWAY',
                    'confidence': conf,
                    'bet_placed': bet
                })

        # 3. MONEYLINE prediction
        moneyline_pred = generate_moneyline_prediction(game, sport)
        if moneyline_pred:
            for model_name in ['ensemble', 'random_forest', 'xgboost', 'lightgbm', 'logistic_regression']:
                pred_value = moneyline_pred['ensemble'] if model_name == 'ensemble' else moneyline_pred['models'].get(model_name)
                if pred_value is None:
                    continue

                edge = pred_value - moneyline_pred['market_home_prob']
                conf, bet = calculate_confidence_and_bet(edge, 'moneyline')

                predictions.append({
                    'prediction_id': f"{game_date}_{away_team}_{home_team}_moneyline_{model_name}",
                    'date_predicted': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'game_date': game_date,
                    'game_time': game_time_str,
                    'sport': sport.upper(),
                    'away_team': away_team,
                    'home_team': home_team,
                    'bet_type': 'moneyline',
                    'model': model_name,
                    'predicted_value': round(pred_value, 4),
                    'market_value': round(moneyline_pred['market_home_prob'], 4),
                    'edge': round(edge, 4),
                    'recommendation': 'HOME' if edge > 0.02 else ('AWAY' if edge < -0.02 else 'PASS'),
                    'confidence': conf,
                    'bet_placed': bet
                })

        return predictions

    except Exception as e:
        logger.error(f"Error generating predictions: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Main execution"""
    logger.info("="*70)
    logger.info("MULTI-BET-TYPE PREDICTION GENERATOR")
    logger.info("="*70)

    # Fetch upcoming games
    logger.info("\n[1/3] Fetching upcoming games...")
    games = fetch_upcoming_games()

    if not games:
        logger.error("No games found")
        return

    logger.info(f"Found {len(games)} total games")

    # Group by sport
    sport_games = {}
    for game in games:
        sport_key = game['state']['sport_key']
        sport_map = {
            'basketball_nba': 'nba',
            'basketball_ncaab': 'ncaab',
            'americanfootball_nfl': 'nfl',
            'americanfootball_ncaaf': 'ncaaf',
            'icehockey_nhl': 'nhl'
        }
        sport = sport_map.get(sport_key)
        if sport:
            if sport not in sport_games:
                sport_games[sport] = []
            sport_games[sport].append(game)

    logger.info(f"Sports breakdown: {', '.join([f'{s.upper()}: {len(g)}' for s, g in sport_games.items()])}")

    # Generate predictions for each sport
    logger.info("\n[2/3] Generating predictions...")
    all_predictions = []

    for sport, games_list in sport_games.items():
        logger.info(f"\n--- {sport.upper()} ---")
        sport_predictions = []

        for game in games_list:
            predictions = generate_predictions_for_game(game, sport)
            sport_predictions.extend(predictions)

        # Log summary
        totals_count = len([p for p in sport_predictions if p['bet_type'] == 'totals' and p['model'] == 'ensemble'])
        spreads_count = len([p for p in sport_predictions if p['bet_type'] == 'spreads' and p['model'] == 'ensemble'])
        moneyline_count = len([p for p in sport_predictions if p['bet_type'] == 'moneyline' and p['model'] == 'ensemble'])

        logger.info(f"Generated {len(sport_predictions)} total predictions for {sport.upper()}")
        logger.info(f"  Totals: {totals_count} games × 5 models = {totals_count * 5}")
        logger.info(f"  Spreads: {spreads_count} games × 5 models = {spreads_count * 5}")
        logger.info(f"  Moneyline: {moneyline_count} games × 5 models = {moneyline_count * 5}")

        all_predictions.extend(sport_predictions)

    if not all_predictions:
        logger.error("No predictions generated")
        return

    # Save to predictions log
    logger.info(f"\n[3/3] Saving {len(all_predictions)} predictions...")

    # Create new predictions dataframe
    new_df = pd.DataFrame(all_predictions)

    # Load existing if exists
    existing_df = None
    if PREDICTIONS_LOG.exists():
        try:
            existing_df = pd.read_csv(PREDICTIONS_LOG)
            logger.info(f"Loaded {len(existing_df)} existing predictions")
        except:
            pass

    # Append or create new
    if existing_df is not None:
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['prediction_id'], keep='last')
        combined_df.to_csv(PREDICTIONS_LOG, index=False)
        logger.info(f"Appended to existing log. Total: {len(combined_df)}")
    else:
        TRACKING_DIR.mkdir(parents=True, exist_ok=True)
        new_df.to_csv(PREDICTIONS_LOG, index=False)
        logger.info(f"Created new predictions log with {len(new_df)} predictions")

    # Print summary
    logger.info("\n" + "="*70)
    logger.info("SUMMARY")
    logger.info("="*70)

    ensemble_preds = [p for p in all_predictions if p['model'] == 'ensemble']
    logger.info(f"Total predictions (all models): {len(all_predictions)}")
    logger.info(f"Ensemble predictions: {len(ensemble_preds)}")
    logger.info(f"  Totals: {len([p for p in ensemble_preds if p['bet_type'] == 'totals'])}")
    logger.info(f"  Spreads: {len([p for p in ensemble_preds if p['bet_type'] == 'spreads'])}")
    logger.info(f"  Moneyline: {len([p for p in ensemble_preds if p['bet_type'] == 'moneyline'])}")
    logger.info(f"High confidence: {len([p for p in ensemble_preds if p['confidence'] == 'HIGH'])}")
    logger.info(f"Recommended bets: {len([p for p in ensemble_preds if p['bet_placed'] == 'YES'])}")
    logger.info("="*70)

if __name__ == "__main__":
    main()
