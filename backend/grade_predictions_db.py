"""
Database-Based Grading Script
Grades predictions by fetching scores from ESPN API and updating predictions.db
Handles all sports: NBA, NCAAB, NFL, NCAAF, NHL

Usage:
    python grade_predictions_db.py --days 7 --dry-run
    python grade_predictions_db.py --sport NBA --days 3
    python grade_predictions_db.py --all  # Grade everything ungraded
"""

import sqlite3
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import time
from typing import Dict, List, Optional, Tuple
import json

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
PREDICTIONS_DB = Path("/root/sporttrader/backend/ml/predictions.db")

# ESPN API sport mappings
ESPN_SPORTS = {
    'NBA': 'basketball/nba',
    'NCAAB': 'basketball/mens-college-basketball',
    'NFL': 'football/nfl',
    'NCAAF': 'football/college-football',
    'NHL': 'hockey/nhl'
}


def normalize_team_name(team: str) -> str:
    """Normalize team name for matching"""
    # Remove common suffixes and prefixes
    team = team.lower().strip()
    team = team.replace('state', 'st')
    team = team.replace('university', '')
    team = team.replace('college', '')
    return team.strip()


def fetch_scores_from_espn(sport: str, date: str) -> List[Dict]:
    """
    Fetch completed game scores from ESPN API for a specific date

    Args:
        sport: Sport key (NBA, NCAAB, NFL, NCAAF, NHL)
        date: Date string in YYYY-MM-DD format

    Returns:
        List of game dictionaries with scores
    """
    if sport not in ESPN_SPORTS:
        logger.warning(f"Unknown sport: {sport}")
        return []

    # Format date as YYYYMMDD for ESPN
    espn_date = date.replace('-', '')
    espn_sport_path = ESPN_SPORTS[sport]

    url = f"https://site.api.espn.com/apis/site/v2/sports/{espn_sport_path}/scoreboard"
    params = {'dates': espn_date}

    try:
        logger.info(f"Fetching {sport} scores for {date}...")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()
        events = data.get('events', [])

        games = []
        for event in events:
            # Only process completed games
            if event.get('status', {}).get('type', {}).get('completed') != True:
                continue

            competitions = event.get('competitions', [])
            if not competitions:
                continue

            competition = competitions[0]
            competitors = competition.get('competitors', [])

            if len(competitors) != 2:
                continue

            # Extract teams and scores
            home_team = next((c for c in competitors if c.get('homeAway') == 'home'), None)
            away_team = next((c for c in competitors if c.get('homeAway') == 'away'), None)

            if not home_team or not away_team:
                continue

            game = {
                'home_team': home_team.get('team', {}).get('displayName', ''),
                'away_team': away_team.get('team', {}).get('displayName', ''),
                'home_score': int(home_team.get('score', 0)),
                'away_score': int(away_team.get('score', 0)),
                'date': date,
                'sport': sport,
                'completed': True
            }

            games.append(game)

        logger.info(f"✓ Found {len(games)} completed {sport} games on {date}")
        return games

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {sport} scores for {date}: {e}")
        return []


def match_prediction_to_score(prediction: Dict, scores: List[Dict]) -> Optional[Dict]:
    """
    Match a prediction to its actual game score

    Args:
        prediction: Prediction dictionary from database
        scores: List of score dictionaries from ESPN

    Returns:
        Matching score dict or None
    """
    pred_away = normalize_team_name(prediction['away_team'])
    pred_home = normalize_team_name(prediction['home_team'])

    for score in scores:
        score_away = normalize_team_name(score['away_team'])
        score_home = normalize_team_name(score['home_team'])

        # Check if team names match (allow partial matches)
        away_match = (pred_away in score_away or score_away in pred_away)
        home_match = (pred_home in score_home or score_home in pred_home)

        if away_match and home_match:
            return score

    return None


def calculate_result(prediction: Dict, score: Dict) -> Dict:
    """
    Calculate WIN/LOSS/PUSH and profit/loss for a prediction

    Args:
        prediction: Prediction dictionary from database
        score: Score dictionary from ESPN

    Returns:
        Result dictionary with outcome and profit/loss
    """
    away_score = score['away_score']
    home_score = score['home_score']
    actual_total = away_score + home_score
    actual_spread = home_score - away_score  # Positive means home won

    bet_type = prediction['bet_type'].lower()
    recommendation = prediction['recommendation'].upper()
    market_value = float(prediction['market_value'])

    # Determine outcome based on bet type
    result = 'UNKNOWN'

    if bet_type == 'totals':
        if recommendation == 'OVER':
            if actual_total > market_value:
                result = 'WIN'
            elif actual_total < market_value:
                result = 'LOSS'
            else:
                result = 'PUSH'
        elif recommendation == 'UNDER':
            if actual_total < market_value:
                result = 'WIN'
            elif actual_total > market_value:
                result = 'LOSS'
            else:
                result = 'PUSH'

    elif bet_type == 'spreads':
        # market_value is the spread (negative = home favored)
        if recommendation == 'HOME':
            # Home team must win by MORE than the spread
            if actual_spread > abs(market_value):
                result = 'WIN'
            elif actual_spread < abs(market_value):
                result = 'LOSS'
            else:
                result = 'PUSH'
        elif recommendation == 'AWAY':
            # Away team must lose by LESS than the spread (or win)
            if actual_spread < abs(market_value):
                result = 'WIN'
            elif actual_spread > abs(market_value):
                result = 'LOSS'
            else:
                result = 'PUSH'

    elif bet_type == 'moneyline':
        if recommendation == 'HOME':
            result = 'WIN' if home_score > away_score else 'LOSS'
        elif recommendation == 'AWAY':
            result = 'WIN' if away_score > home_score else 'LOSS'

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
        'away_score': away_score,
        'home_score': home_score,
        'actual_total': actual_total if bet_type == 'totals' else None
    }


def grade_predictions(sport: Optional[str] = None, days: int = 7, dry_run: bool = False, grade_all: bool = False):
    """
    Main function to grade ungraded predictions from database

    Args:
        sport: Filter by sport (NBA, NCAAB, etc.) or None for all
        days: Number of days back to process
        dry_run: If True, don't write to database
        grade_all: If True, grade all ungraded predictions regardless of date
    """
    logger.info("="*80)
    logger.info("DATABASE-BASED GRADING SCRIPT")
    logger.info("="*80)

    # Connect to database
    conn = sqlite3.connect(PREDICTIONS_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build query to get ungraded predictions
    if grade_all:
        where_clause = "WHERE p.prediction_id NOT IN (SELECT prediction_id FROM results) AND p.game_date < strftime('%Y-%m-%d', datetime('now', '-6 hours')) AND p.predicted_value IS NOT NULL AND p.market_value IS NOT NULL"
        if sport:
            where_clause += f" AND p.sport = '{sport}'"
    else:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        where_clause = f"WHERE p.prediction_id NOT IN (SELECT prediction_id FROM results) AND p.game_date >= '{cutoff_date}' AND p.game_date < strftime('%Y-%m-%d', datetime('now', '-6 hours')) AND p.predicted_value IS NOT NULL AND p.market_value IS NOT NULL"
        if sport:
            where_clause += f" AND p.sport = '{sport}'"

    query = f"""
        SELECT p.* FROM predictions p
        {where_clause}
        ORDER BY p.game_date ASC
    """

    cursor.execute(query)
    predictions = cursor.fetchall()

    logger.info(f"Found {len(predictions)} ungraded predictions to process")

    if len(predictions) == 0:
        logger.info("No predictions to grade. Exiting.")
        conn.close()
        return

    # Group predictions by sport and date
    predictions_by_sport_date = {}
    for pred in predictions:
        key = (pred['sport'], pred['game_date'])
        if key not in predictions_by_sport_date:
            predictions_by_sport_date[key] = []
        predictions_by_sport_date[key].append(dict(pred))

    logger.info(f"Processing {len(predictions_by_sport_date)} unique sport/date combinations")

    # Process each sport/date combination
    results_to_insert = []
    matched = 0
    unmatched = 0

    for (sport_key, game_date), preds in predictions_by_sport_date.items():
        logger.info(f"\nProcessing {sport_key} on {game_date} ({len(preds)} predictions)...")

        # Fetch scores for this sport and date
        scores = fetch_scores_from_espn(sport_key, game_date)

        if not scores:
            logger.warning(f"No scores found for {sport_key} on {game_date}")
            unmatched += len(preds)
            continue

        # Match each prediction to a score
        for pred in preds:
            score = match_prediction_to_score(pred, scores)

            if score:
                matched += 1
                logger.debug(f"✓ MATCHED: {pred['away_team']} @ {pred['home_team']}")
                outcome = calculate_result(pred, score)

                result_row = {
                    'prediction_id': pred['prediction_id'],
                    'sport': pred['sport'],
                    'bet_type': pred['bet_type'],
                    'game_date': pred['game_date'],
                    'away_team': pred['away_team'],
                    'home_team': pred['home_team'],
                    'away_score': outcome['away_score'],
                    'home_score': outcome['home_score'],
                    'actual_total': outcome['actual_total'],
                    'predicted_value': pred['predicted_value'],
                    'market_value': pred['market_value'],
                    'recommendation': pred['recommendation'],
                    'confidence': pred['confidence'],
                    'result': outcome['result'],
                    'profit_loss': outcome['profit_loss'],
                    'model': pred['model']
                }

                results_to_insert.append(result_row)

                if matched % 50 == 0:
                    logger.info(f"Progress: {matched} matched, {unmatched} unmatched")
            else:
                unmatched += 1
                logger.debug(f"✗ NO MATCH: {pred['away_team']} @ {pred['home_team']}")
                if unmatched <= 3:  # Show first 3 unmatched in detail
                    logger.debug(f"  Normalized: {normalize_team_name(pred['away_team'])} @ {normalize_team_name(pred['home_team'])}")
                    logger.debug(f"  Available scores: {[(s['away_team'], s['home_team']) for s in scores[:3]]}")

        time.sleep(0.5)  # Rate limit

    logger.info("")
    logger.info("="*80)
    logger.info("GRADING COMPLETE")
    logger.info("="*80)
    logger.info(f"Matched: {matched}")
    logger.info(f"Unmatched: {unmatched}")
    logger.info(f"Total predictions processed: {len(predictions)}")

    if results_to_insert:
        # Calculate summary stats
        wins = sum(1 for r in results_to_insert if r['result'] == 'WIN')
        losses = sum(1 for r in results_to_insert if r['result'] == 'LOSS')
        pushes = sum(1 for r in results_to_insert if r['result'] == 'PUSH')
        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0
        total_profit = sum(r['profit_loss'] for r in results_to_insert)
        roi = (total_profit / len(results_to_insert)) * 100 if len(results_to_insert) > 0 else 0

        logger.info("")
        logger.info("PERFORMANCE SUMMARY:")
        logger.info(f"  Wins: {wins}")
        logger.info(f"  Losses: {losses}")
        logger.info(f"  Pushes: {pushes}")
        logger.info(f"  Win Rate: {win_rate:.1%}")
        logger.info(f"  Total Profit/Loss: {total_profit:+.2f} units")
        logger.info(f"  ROI: {roi:+.2f}%")

        if not dry_run:
            # Insert results into database
            insert_query = """
                INSERT INTO results (
                    prediction_id, sport, bet_type, game_date, away_team, home_team,
                    away_score, home_score, actual_total, predicted_value, market_value,
                    recommendation, confidence, result, profit_loss, model
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            for result in results_to_insert:
                cursor.execute(insert_query, (
                    result['prediction_id'],
                    result['sport'],
                    result['bet_type'],
                    result['game_date'],
                    result['away_team'],
                    result['home_team'],
                    result['away_score'],
                    result['home_score'],
                    result['actual_total'],
                    result['predicted_value'],
                    result['market_value'],
                    result['recommendation'],
                    result['confidence'],
                    result['result'],
                    result['profit_loss'],
                    result['model']
                ))

            conn.commit()
            logger.info(f"✓ Saved {len(results_to_insert)} results to database")
        else:
            logger.info("[DRY RUN] Results not saved to database")
    else:
        logger.info("No new results to save")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grade predictions from database using ESPN scores")
    parser.add_argument('--sport', type=str, help='Filter by sport (NBA, NCAAB, NHL, NFL, NCAAF)')
    parser.add_argument('--days', type=int, default=7, help='Number of days back to process (default: 7)')
    parser.add_argument('--all', action='store_true', help='Grade all ungraded predictions regardless of date')
    parser.add_argument('--dry-run', action='store_true', help='Run without saving to database')

    args = parser.parse_args()

    grade_predictions(
        sport=args.sport,
        days=args.days,
        dry_run=args.dry_run,
        grade_all=args.all
    )
