#!/usr/bin/env python3
"""
Daily NBA Player Props Workflow
Scrapes props, generates ML predictions, grades yesterday's results

Schedule: Daily at 9:00 AM CST (after games finish, before new props)
"""
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def grade_yesterday_props():
    """Grade props from yesterday using actual stats"""
    from scrapers.props.balldontlie_nba_props import BalldontlieNBAPropsClient

    logger.info("="*70)
    logger.info("GRADING YESTERDAY'S PROPS")
    logger.info("="*70)

    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    db_path = Path(__file__).parent / "data" / "player_props.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Get yesterday's predictions
    cursor.execute("""
        SELECT
            id,
            player_id,
            player_name,
            prop_type,
            market_line,
            predicted_value,
            recommendation
        FROM player_props_predictions
        WHERE game_date = ?
          AND result IS NULL
    """, (yesterday,))

    predictions = cursor.fetchall()
    logger.info(f"Found {len(predictions)} predictions to grade")

    if not predictions:
        logger.info("No predictions to grade")
        conn.close()
        return

    # Fetch actual stats
    props_client = BalldontlieNBAPropsClient()

    graded_count = 0
    for pred_id, player_id, player_name, prop_type, market_line, predicted_value, recommendation in predictions:
        try:
            # Get actual stats for player
            stats = props_client.get_player_stats(player_id, yesterday)

            if not stats:
                logger.warning(f"No stats found for {player_name} on {yesterday}")
                continue

            # Map prop type to stat key
            stat_map = {
                'points': 'pts',
                'rebounds': 'reb',
                'assists': 'ast',
                'threes': 'fg3m',
                'blocks': 'blk',
                'steals': 'stl',
                'PRA': 'pts_reb_ast'
            }

            stat_key = stat_map.get(prop_type)
            if not stat_key:
                logger.warning(f"Unknown prop type: {prop_type}")
                continue

            if prop_type == 'PRA':
                actual_value = stats.get('pts', 0) + stats.get('reb', 0) + stats.get('ast', 0)
            else:
                actual_value = stats.get(stat_key, 0)

            # Determine result
            if recommendation == 'OVER':
                result = 'WIN' if actual_value > market_line else ('PUSH' if actual_value == market_line else 'LOSS')
            elif recommendation == 'UNDER':
                result = 'WIN' if actual_value < market_line else ('PUSH' if actual_value == market_line else 'LOSS')
            else:
                result = 'PASS'

            # Update prediction with result
            cursor.execute("""
                UPDATE player_props_predictions
                SET actual_value = ?,
                    result = ?
                WHERE id = ?
            """, (actual_value, result, pred_id))

            graded_count += 1
            logger.info(f"✓ {player_name} {prop_type}: {result} (actual: {actual_value}, line: {market_line})")

        except Exception as e:
            logger.error(f"Error grading {player_name}: {str(e)}")
            continue

    conn.commit()
    conn.close()

    logger.info(f"✓ Graded {graded_count} predictions")


def scrape_todays_props():
    """Scrape props lines for today's games"""
    from scrapers.props.odds_api_props import OddsAPIPropsClient

    logger.info("="*70)
    logger.info("SCRAPING TODAY'S PROPS")
    logger.info("="*70)

    client = OddsAPIPropsClient()
    today = datetime.now().strftime('%Y-%m-%d')

    props = client.get_nba_props(date=today)

    if not props:
        logger.warning("No props found for today")
        return 0

    # Save to database
    db_path = Path(__file__).parent / "data" / "player_props.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    saved_count = 0
    for prop in props:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO player_props_lines
                (date, player_id, player_name, team, opponent, prop_type, market_line, over_odds, under_odds, bookmaker)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prop['date'],
                prop['player_id'],
                prop['player_name'],
                prop['team'],
                prop['opponent'],
                prop['prop_type'],
                prop['market_line'],
                prop['over_odds'],
                prop['under_odds'],
                prop['bookmaker']
            ))
            saved_count += 1
        except Exception as e:
            logger.error(f"Error saving prop: {str(e)}")
            continue

    conn.commit()
    conn.close()

    logger.info(f"✓ Saved {saved_count} props to database")
    return saved_count


def generate_predictions():
    """Generate ML predictions for today's props"""
    from ml.predictions.daily_props_predictor_fast import EnhancedPropsPredictor

    logger.info("="*70)
    logger.info("GENERATING ML PREDICTIONS")
    logger.info("="*70)

    predictor = EnhancedPropsPredictor()
    predictor.load_models()
    predictor.load_team_stats()

    today = datetime.now().strftime('%Y-%m-%d')

    # Get today's props from database
    db_path = Path(__file__).parent / "data" / "player_props.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT
            player_id,
            player_name,
            team,
            opponent,
            prop_type,
            market_line
        FROM player_props_lines
        WHERE date = ?
    """, (today,))

    props_to_predict = cursor.fetchall()
    logger.info(f"Found {len(props_to_predict)} props to predict")

    predictions_saved = 0
    for prop in props_to_predict:
        try:
            prediction = predictor.predict_prop(
                player_id=prop['player_id'],
                player_name=prop['player_name'],
                team=prop['team'],
                opponent=prop['opponent'],
                prop_type=prop['prop_type'],
                market_line=prop['market_line'],
                home_away='HOME'  # Will be determined from game data
            )

            if not prediction:
                continue

            # Calculate edge and recommendation
            predicted_value = prediction['predicted_value']
            edge = predicted_value - prop['market_line']
            edge_pct = (edge / prop['market_line']) * 100 if prop['market_line'] > 0 else 0

            if abs(edge_pct) >= 5.0:
                recommendation = 'OVER' if edge > 0 else 'UNDER'
            else:
                recommendation = 'PASS'

            # Save prediction
            cursor.execute("""
                INSERT INTO player_props_predictions
                (prediction_date, game_date, player_id, player_name, team, opponent,
                 prop_type, market_line, predicted_value, confidence, model_type, edge_pct, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime('%Y-%m-%d'),
                today,
                prop['player_id'],
                prop['player_name'],
                prop['team'],
                prop['opponent'],
                prop['prop_type'],
                prop['market_line'],
                predicted_value,
                prediction.get('confidence', 0.5),
                'ensemble',
                edge_pct,
                recommendation
            ))

            predictions_saved += 1

        except Exception as e:
            logger.error(f"Error predicting {prop['player_name']} {prop['prop_type']}: {str(e)}")
            continue

    conn.commit()
    conn.close()

    logger.info(f"✓ Saved {predictions_saved} predictions")
    return predictions_saved


def main():
    logger.info("\n" + "="*70)
    logger.info("NBA PROPS DAILY WORKFLOW")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("="*70 + "\n")

    try:
        # Step 1: Grade yesterday's props
        grade_yesterday_props()

        # Step 2: Scrape today's props
        props_count = scrape_todays_props()

        # Step 3: Generate predictions
        if props_count > 0:
            generate_predictions()

        logger.info("\n" + "="*70)
        logger.info("WORKFLOW COMPLETE ✓")
        logger.info("="*70 + "\n")

    except Exception as e:
        logger.error(f"Workflow failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
