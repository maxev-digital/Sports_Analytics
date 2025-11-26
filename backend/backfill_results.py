"""
Results Backfill Script
Fetches final scores for completed games and matches them to predictions
Calculates WIN/LOSS/PUSH and profit/loss for model performance tracking

Usage:
    python backfill_results.py --sport nba --days 30
    python backfill_results.py --all
"""

import pandas as pd
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import time
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path(__file__).parent / "data" / "tracking"
PREDICTIONS_LOG = DATA_DIR / "predictions_log_multi_bet.csv"
RESULTS_LOG = DATA_DIR / "results_log.csv"

# The Odds API config
import os
from dotenv import load_dotenv
load_dotenv()
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "b569397089cab564f5fa1dd218288aec")
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# Sport mappings
SPORT_KEYS = {
    'basketball_nba': 'NBA',
    'basketball_ncaab': 'NCAAB',
    'icehockey_nhl': 'NHL',
    'americanfootball_nfl': 'NFL',
    'americanfootball_ncaaf': 'NCAAF'
}


def fetch_scores_from_odds_api(sport_key: str, days_ago: int = 30) -> List[Dict]:
    """
    Fetch completed game scores from The Odds API

    Args:
        sport_key: The sport key (e.g., 'basketball_nba')
        days_ago: How many days back to fetch scores

    Returns:
        List of game score dictionaries
    """
    url = f"{ODDS_API_BASE}/sports/{sport_key}/scores"

    params = {
        'apiKey': ODDS_API_KEY,
        'daysFrom': days_ago,
        'dateFormat': 'iso'
    }

    try:
        logger.info(f"Fetching scores for {sport_key} from last {days_ago} days...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        logger.info(f"✓ Fetched {len(data)} completed games for {sport_key}")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching scores for {sport_key}: {e}")
        return []


def normalize_team_name(team: str) -> str:
    """
    Normalize team names to match between predictions and API results

    Common variations:
    - "Los Angeles Lakers" vs "LA Lakers"
    - "Golden State Warriors" vs "GSW"
    """
    # Just lowercase - both sources use full team names
    return team.lower().strip()


def match_prediction_to_score(prediction: pd.Series, scores: List[Dict]) -> Optional[Dict]:
    """
    Match a prediction to its actual game score

    Args:
        prediction: Row from predictions_log DataFrame
        scores: List of score dictionaries from API

    Returns:
        Matching score dict or None
    """
    pred_away = normalize_team_name(prediction['away_team'])
    pred_home = normalize_team_name(prediction['home_team'])
    pred_date = pd.to_datetime(prediction['game_date']).date()

    for score in scores:
        if not score.get('completed'):
            continue

        score_away = normalize_team_name(score.get('away_team', ''))
        score_home = normalize_team_name(score.get('home_team', ''))
        score_date = datetime.fromisoformat(score['commence_time'].replace('Z', '+00:00')).date()

        # Match by teams and date
        if (pred_away in score_away or score_away in pred_away) and \
           (pred_home in score_home or score_home in pred_home) and \
           abs((pred_date - score_date).days) <= 1:  # Allow 1 day difference for timezone issues
            return score

    return None


def calculate_result(prediction: pd.Series, score: Dict) -> Dict:
    """
    Calculate WIN/LOSS/PUSH and profit/loss for a prediction

    Args:
        prediction: Prediction row from DataFrame
        score: Score dictionary from API

    Returns:
        Result dictionary with outcome and profit/loss
    """
    away_score = score['scores'][0]['score'] if score['scores'] else None
    home_score = score['scores'][1]['score'] if len(score['scores']) > 1 else None

    if away_score is None or home_score is None:
        return {
            'result': 'UNKNOWN',
            'profit_loss': 0.0,
            'actual_total': None,
            'actual_spread': None
        }

    away_score = int(away_score)
    home_score = int(home_score)
    actual_total = away_score + home_score
    actual_spread = home_score - away_score  # Positive means home won

    bet_type = prediction['bet_type'].lower()
    recommendation = prediction['recommendation'].upper()

    # Determine outcome based on bet type
    if bet_type == 'totals':
        market_total = float(prediction['market_value'])

        if recommendation == 'OVER':
            if actual_total > market_total:
                result = 'WIN'
            elif actual_total < market_total:
                result = 'LOSS'
            else:
                result = 'PUSH'
        elif recommendation == 'UNDER':
            if actual_total < market_total:
                result = 'WIN'
            elif actual_total > market_total:
                result = 'LOSS'
            else:
                result = 'PUSH'
        else:
            result = 'UNKNOWN'

    elif bet_type == 'spreads':
        market_spread = float(prediction['market_value'])

        if recommendation == 'HOME':
            if actual_spread > abs(market_spread):
                result = 'WIN'
            elif actual_spread < abs(market_spread):
                result = 'LOSS'
            else:
                result = 'PUSH'
        elif recommendation == 'AWAY':
            # AWAY gets the underdog spread
            # If market is -18.5 (HOME favored), AWAY gets +18.5
            # AWAY wins if they lose by LESS than 18.5 (or win outright)
            # actual_spread is positive when HOME wins
            if actual_spread < abs(market_spread):
                result = 'WIN'
            elif actual_spread > abs(market_spread):
                result = 'LOSS'
            else:
                result = 'PUSH'
        else:
            result = 'UNKNOWN'

    elif bet_type == 'moneyline':
        if recommendation == 'HOME':
            result = 'WIN' if home_score > away_score else 'LOSS'
        elif recommendation == 'AWAY':
            result = 'WIN' if away_score > home_score else 'LOSS'
        else:
            result = 'UNKNOWN'
    else:
        result = 'UNKNOWN'

    # Calculate profit/loss (assuming -110 odds, 1 unit bets)
    if result == 'WIN':
        profit_loss = 0.91  # Win 0.91 units at -110
    elif result == 'LOSS':
        profit_loss = -1.0  # Lose 1 unit
    else:
        profit_loss = 0.0  # Push

    return {
        'result': result,
        'profit_loss': profit_loss,
        'actual_total': actual_total if bet_type == 'totals' else None,
        'actual_spread': actual_spread if bet_type == 'spreads' else None,
        'away_score': away_score,
        'home_score': home_score
    }


def backfill_results(sport: Optional[str] = None, days: int = 30, dry_run: bool = False):
    """
    Main function to backfill results for predictions

    Args:
        sport: Filter by sport (nba, ncaab, etc.) or None for all
        days: Number of days back to process
        dry_run: If True, don't write to results_log.csv
    """
    logger.info("="*80)
    logger.info("RESULTS BACKFILL SCRIPT")
    logger.info("="*80)

    # Load predictions
    if not PREDICTIONS_LOG.exists():
        logger.error(f"Predictions log not found: {PREDICTIONS_LOG}")
        return

    predictions_df = pd.read_csv(PREDICTIONS_LOG)
    logger.info(f"Loaded {len(predictions_df)} predictions from log")

    # Filter by sport if specified
    if sport:
        sport_filter = sport.lower()
        predictions_df = predictions_df[predictions_df['sport'].str.lower().str.contains(sport_filter)]
        logger.info(f"Filtered to {len(predictions_df)} predictions for sport: {sport}")

    # Filter by date
    cutoff_date = datetime.now() - timedelta(days=days)
    predictions_df['game_date_dt'] = pd.to_datetime(predictions_df['game_date'], format='mixed', errors='coerce')
    predictions_df = predictions_df[predictions_df['game_date_dt'] >= cutoff_date]
    logger.info(f"Filtered to {len(predictions_df)} predictions from last {days} days")

    # Load existing results to avoid duplicates
    existing_results = set()
    if RESULTS_LOG.exists():
        results_df = pd.read_csv(RESULTS_LOG)
        existing_results = set(results_df['prediction_id'].values)
        logger.info(f"Found {len(existing_results)} existing results")

    # Group predictions by sport to minimize API calls
    sports_to_fetch = predictions_df['sport'].unique()
    logger.info(f"Sports to process: {sports_to_fetch}")

    all_scores = {}
    for sport_name in sports_to_fetch:
        # Map internal sport name to API sport key
        sport_key = None
        for api_key, internal_name in SPORT_KEYS.items():
            if internal_name.lower() in sport_name.lower():
                sport_key = api_key
                break

        if not sport_key:
            logger.warning(f"Could not map sport name '{sport_name}' to API key")
            continue

        scores = fetch_scores_from_odds_api(sport_key, days_ago=days)
        all_scores[sport_name] = scores
        time.sleep(1)  # Rate limit

    # Process each prediction
    results = []
    matched = 0
    unmatched = 0

    for idx, prediction in predictions_df.iterrows():
        prediction_id = prediction['prediction_id']

        # Skip if already processed
        if prediction_id in existing_results:
            continue

        # Get scores for this sport
        sport_name = prediction['sport']
        scores = all_scores.get(sport_name, [])

        if not scores:
            continue

        # Match to score
        score = match_prediction_to_score(prediction, scores)

        if score:
            matched += 1
            outcome = calculate_result(prediction, score)

            result_row = {
                'prediction_id': prediction_id,
                'game_date': prediction['game_date'],
                'away_team': prediction['away_team'],
                'home_team': prediction['home_team'],
                'away_score': outcome['away_score'],
                'home_score': outcome['home_score'],
                'actual_total': outcome['actual_total'],
                'market_total': prediction.get('market_value') or prediction.get('market_total'),
                'predicted_total': prediction.get('predicted_value') or prediction.get('predicted_total'),
                'recommendation': prediction['recommendation'],
                'confidence': prediction['confidence'],
                'result': outcome['result'],
                'edge_accuracy': prediction.get('edge', 0),
                'profit_loss': outcome['profit_loss']
            }

            results.append(result_row)

            if matched % 50 == 0:
                logger.info(f"Progress: {matched} matched, {unmatched} unmatched")
        else:
            unmatched += 1

    logger.info("")
    logger.info("="*80)
    logger.info("BACKFILL COMPLETE")
    logger.info("="*80)
    logger.info(f"Matched: {matched}")
    logger.info(f"Unmatched: {unmatched}")
    logger.info(f"Total predictions processed: {len(predictions_df)}")

    if results:
        # Calculate summary stats
        results_df_new = pd.DataFrame(results)
        wins = len(results_df_new[results_df_new['result'] == 'WIN'])
        losses = len(results_df_new[results_df_new['result'] == 'LOSS'])
        pushes = len(results_df_new[results_df_new['result'] == 'PUSH'])
        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0
        total_profit = results_df_new['profit_loss'].sum()
        roi = (total_profit / len(results_df_new)) * 100 if len(results_df_new) > 0 else 0

        logger.info("")
        logger.info("PERFORMANCE SUMMARY:")
        logger.info(f"  Wins: {wins}")
        logger.info(f"  Losses: {losses}")
        logger.info(f"  Pushes: {pushes}")
        logger.info(f"  Win Rate: {win_rate:.1%}")
        logger.info(f"  Total Profit/Loss: {total_profit:+.2f} units")
        logger.info(f"  ROI: {roi:+.2f}%")

        if not dry_run:
            # Append to results log
            if RESULTS_LOG.exists():
                results_df_existing = pd.read_csv(RESULTS_LOG)
                results_df_combined = pd.concat([results_df_existing, results_df_new], ignore_index=True)
            else:
                results_df_combined = results_df_new

            results_df_combined.to_csv(RESULTS_LOG, index=False)
            logger.info(f"✓ Saved {len(results)} new results to {RESULTS_LOG}")
        else:
            logger.info("[DRY RUN] Results not saved")
    else:
        logger.info("No new results to save")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill game results for predictions")
    parser.add_argument('--sport', type=str, help='Filter by sport (nba, ncaab, nhl, nfl, ncaaf)')
    parser.add_argument('--days', type=int, default=30, help='Number of days back to process (default: 30)')
    parser.add_argument('--all', action='store_true', help='Process all sports')
    parser.add_argument('--dry-run', action='store_true', help='Run without saving results')

    args = parser.parse_args()

    backfill_results(
        sport=args.sport if not args.all else None,
        days=args.days,
        dry_run=args.dry_run
    )
