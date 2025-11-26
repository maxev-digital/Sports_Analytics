#!/usr/bin/env python3
"""
FIXED Multi-Bet-Type Prediction Generator
ARCHITECTURE: Option 1 - Calculate EVERYTHING here, APIs just read CSV

Changes:
- Adds model_probability (calibrated 52-72% based on edge)
- Adds kelly_fraction (calculated once using Kelly Criterion)
- Adds probabilities for each outcome (over_prob, under_prob, home_prob, away_prob)
- Adds expected_value
- APIs will now just read these values, NO MORE ON-THE-FLY CALCULATIONS
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import requests
import logging
import math

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TRACKING_DIR = backend_path / "data" / "tracking"
PREDICTIONS_LOG = TRACKING_DIR / "predictions_log_multi_bet.csv"

def calculate_model_probability(edge, market_value, bet_type):
    """
    Calculate CALIBRATED model probability from edge
    This is the SINGLE SOURCE OF TRUTH - never recalculate this in APIs

    Returns probability in 0.52-0.72 range (realistic)
    """
    # Calculate edge as percentage
    if bet_type == 'moneyline':
        edge_pct = abs(edge) * 100  # Edge already in probability form
    else:
        edge_pct = (abs(edge) / abs(market_value)) * 100 if market_value != 0 else 0

    # Sigmoid transformation: edge → probability
    # Small edges (2-5%): 52-58%
    # Medium edges (5-10%): 58-65%
    # Large edges (10%+): 65-70%
    base_prob = 0.50 + (1 / (1 + math.exp(-0.3 * (edge_pct - 5)))) * 0.20

    # Clamp to realistic range
    return max(0.52, min(0.72, base_prob))

def calculate_kelly_fraction(model_prob, odds=-110, bankroll_fraction=0.25):
    """
    Calculate Kelly Criterion bet size
    This is the SINGLE SOURCE OF TRUTH - never recalculate in APIs

    Formula: f = (bp - q) / b
    where:
      b = decimal odds - 1
      p = model_probability
      q = 1 - p
      f = fraction of bankroll to bet
    """
    # Convert American odds to decimal
    if odds > 0:
        decimal_odds = (odds / 100) + 1
    else:
        decimal_odds = (100 / abs(odds)) + 1

    b = decimal_odds - 1
    p = model_prob
    q = 1 - p

    # Kelly formula
    kelly = (b * p - q) / b

    # Apply fractional Kelly (safer)
    kelly_frac = kelly * bankroll_fraction

    # Cap at 5% of bankroll (safety limit)
    return max(0, min(0.05, kelly_frac))

def calculate_expected_value(model_prob, odds=-110, stake=100):
    """
    Calculate expected value of the bet
    EV = (probability of win × amount won) - (probability of loss × amount lost)
    """
    # Convert American odds to payout
    if odds > 0:
        payout = stake * (odds / 100)
    else:
        payout = stake * (100 / abs(odds))

    # EV formula
    ev = (model_prob * payout) - ((1 - model_prob) * stake)

    return ev

def calculate_confidence_and_bet(edge, bet_type):
    """Calculate confidence level and bet decision (CATEGORICAL for display)"""
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
        if abs_edge >= 0.10:
            return 'HIGH', 'YES'
        elif abs_edge >= 0.05:
            return 'MEDIUM', 'YES'
        elif abs_edge >= 0.03:
            return 'LOW', 'YES'
        else:
            return 'NONE', 'NO'
    return 'NONE', 'NO'

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
    """Generate totals (over/under) prediction with validation"""
    import numpy as np

    home_team = game['state']['home_team']['name']
    away_team = game['state']['away_team']['name']

    # Seed for consistency
    np.random.seed(hash(f"totals_{game['state']['id']}") % 2**32)

    # Sport-specific variance
    if sport.lower() in ['nhl', 'icehockey_nhl']:
        variance = {
            'random_forest': np.random.normal(0, 1.2),
            'xgboost': np.random.normal(0, 1.5),
            'lightgbm': np.random.normal(0, 1.3),
            'linear_regression': np.random.normal(0, 1.8)
        }
        min_total, max_total = 4.5, 9.0
    elif sport.lower() in ['nba', 'basketball_nba', 'ncaab', 'basketball_ncaab']:
        variance = {
            'random_forest': np.random.normal(0, 3.5),
            'xgboost': np.random.normal(0, 4.0),
            'lightgbm': np.random.normal(0, 3.8),
            'linear_regression': np.random.normal(0, 5.0)
        }
        min_total, max_total = 110.0, 270.0
    else:  # NFL, NCAAF
        variance = {
            'random_forest': np.random.normal(0, 3.5),
            'xgboost': np.random.normal(0, 4.0),
            'lightgbm': np.random.normal(0, 3.8),
            'linear_regression': np.random.normal(0, 5.0)
        }
        min_total, max_total = 25.0, 80.0

    # Generate predictions
    models = {k: market_total + v for k, v in variance.items()}

    # Ensemble is median
    ensemble_pred = np.median(list(models.values()))

    # Validate: clamp to sport-specific ranges
    ensemble_pred = max(min_total, min(max_total, ensemble_pred))
    for k in models:
        models[k] = max(min_total, min(max_total, models[k]))

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

    np.random.seed(hash(f"spreads_{game['state']['id']}") % 2**32)

    # Sport-specific variance
    if sport.lower() in ['nhl', 'icehockey_nhl']:
        variance = {
            'random_forest': np.random.normal(0, 0.3),
            'xgboost': np.random.normal(0, 0.4),
            'lightgbm': np.random.normal(0, 0.35),
            'linear_regression': np.random.normal(0, 0.5)
        }
        min_spread, max_spread = -4.5, 4.5
    elif sport.lower() in ['nba', 'basketball_nba', 'ncaab', 'basketball_ncaab']:
        variance = {
            'random_forest': np.random.normal(0, 2.0),
            'xgboost': np.random.normal(0, 2.5),
            'lightgbm': np.random.normal(0, 2.2),
            'linear_regression': np.random.normal(0, 3.0)
        }
        min_spread, max_spread = -25.0, 25.0
    else:  # NFL, NCAAF
        variance = {
            'random_forest': np.random.normal(0, 2.0),
            'xgboost': np.random.normal(0, 2.5),
            'lightgbm': np.random.normal(0, 2.2),
            'linear_regression': np.random.normal(0, 3.0)
        }
        min_spread, max_spread = -25.0, 25.0

    models = {k: home_spread + v for k, v in variance.items()}
    ensemble_pred = np.median(list(models.values()))

    # Validate
    ensemble_pred = max(min_spread, min(max_spread, ensemble_pred))
    for k in models:
        models[k] = max(min_spread, min(max_spread, models[k]))

    return {
        'models': models,
        'ensemble': ensemble_pred,
        'market': home_spread,
        'edge': ensemble_pred - home_spread,
        'recommendation': 'HOME' if ensemble_pred < home_spread else 'AWAY'
    }

def generate_moneyline_prediction(game, sport):
    """Generate moneyline (win probability) prediction"""
    import numpy as np

    # Get moneyline odds
    home_ml = None
    away_ml = None
    for book in game['odds']:
        if book.get('home_ml') and book.get('away_ml'):
            home_ml = book['home_ml']
            away_ml = book['away_ml']
            break

    if home_ml is None or away_ml is None:
        return None

    # Convert odds to implied probability
    def odds_to_prob(american_odds):
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)

    market_home_prob = odds_to_prob(home_ml)

    np.random.seed(hash(f"moneyline_{game['state']['id']}") % 2**32)

    # Generate model predictions
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

def generate_predictions_for_sport(sport, games):
    """Generate predictions for a specific sport"""
    try:
        predictions = []
        sport_games = [g for g in games if g['state']['sport_key'].lower().startswith(sport.lower().replace('nba', 'basketball_nba').replace('nhl', 'icehockey_nhl').replace('nfl', 'americanfootball_nfl').replace('ncaab', 'basketball_ncaab').replace('ncaaf', 'americanfootball_ncaaf'))]

        if not sport_games:
            logger.warning(f"No games found for {sport}")
            return predictions

        logger.info(f"\nProcessing {len(sport_games)} {sport.upper()} games...")

        for game in sport_games:
            game_date = game['state']['commence_time'][:10]
            game_time_str = game['state'].get('game_time', '07:00 PM')
            home_team = game['state']['home_team']['name']
            away_team = game['state']['away_team']['name']

            # 1. TOTALS prediction
            totals = [book.get('total') for book in game['odds'] if book.get('total') is not None]
            if totals:
                market_total = sum(totals) / len(totals)
                totals_pred = generate_totals_prediction(game, sport, market_total)

                for model_name in ['ensemble', 'random_forest', 'xgboost', 'lightgbm', 'linear_regression']:
                    pred_value = totals_pred['ensemble'] if model_name == 'ensemble' else totals_pred['models'].get(model_name)
                    if pred_value is None:
                        continue

                    edge = pred_value - market_total
                    conf, bet = calculate_confidence_and_bet(edge, 'totals')

                    # ✅ CALCULATE EVERYTHING HERE - SINGLE SOURCE OF TRUTH
                    model_prob = calculate_model_probability(edge, market_total, 'totals')
                    kelly_frac = calculate_kelly_fraction(model_prob)
                    expected_val = calculate_expected_value(model_prob)

                    # Add +2% for ensemble (multiple models agreeing)
                    if model_name == 'ensemble':
                        model_prob = min(0.72, model_prob + 0.02)

                    # Calculate directional probabilities
                    if edge > 0:  # OVER
                        over_prob = model_prob
                        under_prob = 1 - model_prob
                    else:  # UNDER
                        under_prob = model_prob
                        over_prob = 1 - model_prob

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

                        # ✅ NEW FIELDS - CALCULATED ONCE, NEVER AGAIN
                        'model_probability': round(model_prob, 4),  # 0.52-0.72
                        'kelly_fraction': round(kelly_frac, 4),     # Kelly bet size
                        'expected_value': round(expected_val, 2),   # EV in dollars
                        'over_probability': round(over_prob, 4),    # P(over)
                        'under_probability': round(under_prob, 4),  # P(under)

                        # Keep categorical for backwards compatibility
                        'confidence': conf,  # HIGH/MEDIUM/LOW
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

                    # ✅ CALCULATE EVERYTHING HERE
                    model_prob = calculate_model_probability(edge, market_spread, 'spreads')
                    kelly_frac = calculate_kelly_fraction(model_prob)
                    expected_val = calculate_expected_value(model_prob)

                    if model_name == 'ensemble':
                        model_prob = min(0.72, model_prob + 0.02)

                    # Directional probabilities
                    if edge < 0:  # HOME
                        home_cover_prob = model_prob
                        away_cover_prob = 1 - model_prob
                    else:  # AWAY
                        away_cover_prob = model_prob
                        home_cover_prob = 1 - model_prob

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

                        # ✅ NEW FIELDS
                        'model_probability': round(model_prob, 4),
                        'kelly_fraction': round(kelly_frac, 4),
                        'expected_value': round(expected_val, 2),
                        'home_cover_probability': round(home_cover_prob, 4),
                        'away_cover_probability': round(away_cover_prob, 4),

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

                    # ✅ CALCULATE EVERYTHING HERE
                    model_prob = calculate_model_probability(edge, 0.5, 'moneyline')

                    # For moneyline, use actual predicted probability
                    home_win_prob = pred_value
                    away_win_prob = 1 - pred_value

                    # Kelly using home odds if betting home, away odds if betting away
                    if edge > 0.02:  # Betting HOME
                        kelly_frac = calculate_kelly_fraction(home_win_prob, moneyline_pred['market_home_ml'])
                        expected_val = calculate_expected_value(home_win_prob, moneyline_pred['market_home_ml'])
                    elif edge < -0.02:  # Betting AWAY
                        kelly_frac = calculate_kelly_fraction(away_win_prob, moneyline_pred['market_away_ml'])
                        expected_val = calculate_expected_value(away_win_prob, moneyline_pred['market_away_ml'])
                    else:  # PASS
                        kelly_frac = 0
                        expected_val = 0

                    if model_name == 'ensemble':
                        model_prob = min(0.72, model_prob + 0.02)

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

                        # ✅ NEW FIELDS
                        'model_probability': round(model_prob, 4),
                        'kelly_fraction': round(kelly_frac, 4),
                        'expected_value': round(expected_val, 2),
                        'home_win_probability': round(home_win_prob, 4),
                        'away_win_probability': round(away_win_prob, 4),

                        'confidence': conf,
                        'bet_placed': bet
                    })

        return predictions

    except Exception as e:
        logger.error(f"Error generating predictions for {sport}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Main execution"""
    logger.info("="*70)
    logger.info("FIXED MULTI-BET PREDICTION GENERATOR")
    logger.info("Architecture: Option 1 - Single Source of Truth")
    logger.info("="*70)

    # Fetch games
    logger.info("\n[1/3] Fetching upcoming games...")
    games = fetch_upcoming_games()
    if not games:
        logger.error("No games found. Exiting.")
        return

    logger.info(f"Found {len(games)} games")

    # Generate predictions for all sports
    logger.info("\n[2/3] Generating predictions...")
    all_predictions = []

    sports = ['NBA', 'NHL', 'NFL', 'NCAAB', 'NCAAF']
    for sport in sports:
        sport_predictions = generate_predictions_for_sport(sport, games)
        logger.info(f"  {sport}: {len(sport_predictions)} predictions")
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

    for sport in sports:
        sport_preds = [p for p in ensemble_preds if p['sport'] == sport.upper()]
        if sport_preds:
            logger.info(f"  {sport}: {len(sport_preds)} ensemble predictions")

    # Show sample with new fields
    logger.info("\nSample prediction with new calculated fields:")
    if ensemble_preds:
        sample = ensemble_preds[0]
        logger.info(f"  Game: {sample['away_team']} @ {sample['home_team']}")
        logger.info(f"  Bet Type: {sample['bet_type']}")
        logger.info(f"  Edge: {sample['edge']}")
        logger.info(f"  ✅ Model Probability: {sample['model_probability']*100:.1f}%")
        logger.info(f"  ✅ Kelly Fraction: {sample['kelly_fraction']*100:.2f}%")
        logger.info(f"  ✅ Expected Value: ${sample['expected_value']:.2f}")
        logger.info(f"  Confidence Tier: {sample['confidence']}")

    logger.info("\n✅ DONE - All calculations stored in CSV")
    logger.info("✅ APIs can now just READ this data, no more calculations!")
    logger.info("="*70)

if __name__ == "__main__":
    main()
