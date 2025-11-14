"""
Prediction Runner with Automatic Logging
FIXED: 2025-11-13 - Absolute paths, all 5 sports support

Runs ML prediction workflows and automatically logs results
for the autonomous learning system.

Updated schedule (runs by 5 AM CST for user):
    0 8 * * * (2 AM CST) - NBA predictions
    15 8 * * * (2:15 AM CST) - NCAAB predictions
    30 8 * * * (2:30 AM CST) - NHL predictions
    45 8 * * * (2:45 AM CST) - NFL predictions
    0 9 * * * (3 AM CST) - NCAAF predictions
"""

import sys
import os
import logging
import pandas as pd
import subprocess
from datetime import datetime
from pathlib import Path
import argparse

# FIXED: Use absolute paths
BASE_DIR = Path("/root/sporttrader/backend")
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging with absolute path
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'prediction_runner_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_ml_predictions(sport: str):
    """Run ML predictions for any sport using generate_all_sport_predictions.py"""
    logger.info("="*80)
    logger.info(f"RUNNING {sport.upper()} ML PREDICTIONS")
    logger.info("="*80)

    try:
        # FIXED: Use absolute path to script
        script_path = BASE_DIR / "generate_all_sport_predictions.py"

        if not script_path.exists():
            logger.error(f"Prediction script not found: {script_path}")
            return None

        # Run the ML prediction script with sport argument
        result = subprocess.run(
            [sys.executable, str(script_path), "--sport", sport],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(BASE_DIR)  # Set working directory
        )

        if result.stdout:
            logger.info(result.stdout)

        if result.returncode != 0:
            logger.error(f"{sport.upper()} predictions failed: {result.stderr}")
            return None

        # FIXED: Use absolute path to predictions file
        predictions_file = BASE_DIR / f"data/predictions/{sport}_ml_predictions_latest.csv"

        if not predictions_file.exists():
            logger.warning(f"Predictions file not found at {predictions_file}")
            # Try alternate location
            predictions_file = BASE_DIR / f"data/predictions/{sport}_predictions_latest.csv"

        if not predictions_file.exists():
            logger.error(f"{sport.upper()} predictions file not found")
            return None

        logger.info(f"✓ {sport.upper()} predictions generated: {predictions_file}")
        return predictions_file

    except subprocess.TimeoutExpired:
        logger.error(f"{sport.upper()} prediction script timed out after 5 minutes")
        return None
    except Exception as e:
        logger.error(f"Error running {sport.upper()} predictions: {e}", exc_info=True)
        return None


def log_predictions_to_tracking(predictions_file: Path, sport: str):
    """Log predictions to tracking file for autonomous learning"""
    logger.info("="*80)
    logger.info("LOGGING PREDICTIONS FOR AUTONOMOUS LEARNING")
    logger.info("="*80)

    try:
        # Load predictions
        predictions = pd.read_csv(predictions_file)
        logger.info(f"Loaded {len(predictions)} predictions from {predictions_file.name}")

        # FIXED: Use absolute path for tracking directory
        tracking_dir = BASE_DIR / "data/tracking"
        tracking_dir.mkdir(parents=True, exist_ok=True)
        tracking_file = tracking_dir / "predictions_log.csv"

        # Initialize tracking file if it doesn't exist
        if not tracking_file.exists():
            tracking_df = pd.DataFrame(columns=[
                'prediction_id', 'date_predicted', 'game_date', 'game_time', 'sport',
                'away_team', 'home_team', 'bet_type', 'predicted_value', 'market_value',
                'edge', 'recommendation', 'confidence', 'bet_placed'
            ])
            tracking_df.to_csv(tracking_file, index=False)
            logger.info(f"Created tracking file: {tracking_file}")

        # Load existing tracking data
        existing = pd.read_csv(tracking_file)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        new_entries = []

        for _, pred in predictions.iterrows():
            # Extract game date (handle different formats)
            game_date = pred.get('game_date', pred.get('date', ''))
            if pd.isna(game_date):
                game_date = datetime.now().strftime('%Y-%m-%d')

            # Create unique prediction ID
            away = str(pred.get('away_team', pred.get('away', ''))).replace(' ', '_')
            home = str(pred.get('home_team', pred.get('home', ''))).replace(' ', '_')
            bet_type = str(pred.get('bet_type', pred.get('market', 'TOTALS'))).upper()

            pred_id = f"{sport.upper()}_{game_date.replace('-', '')}_{away}_{home}_{bet_type}"

            # Skip if already logged
            if pred_id in existing['prediction_id'].values:
                continue

            # Map prediction fields to tracking format (handle different column names)
            entry = {
                'prediction_id': pred_id,
                'date_predicted': timestamp,
                'game_date': game_date,
                'game_time': pred.get('game_time', pred.get('time', '')),
                'sport': sport.upper(),
                'away_team': pred.get('away_team', pred.get('away', '')),
                'home_team': pred.get('home_team', pred.get('home', '')),
                'bet_type': bet_type,
                'predicted_value': pred.get('predicted_total', pred.get('predicted_value', pred.get('prediction', 0.0))),
                'market_value': pred.get('market_total', pred.get('market_value', pred.get('market', 0.0))),
                'edge': pred.get('edge', 0.0),
                'recommendation': pred.get('recommendation', pred.get('pick', 'PASS')),
                'confidence': pred.get('confidence', 'NONE'),
                'bet_placed': 'YES' if str(pred.get('bet', pred.get('bet_placed', 'NO'))).upper() == 'YES' else 'NO'
            }

            new_entries.append(entry)

        if new_entries:
            # Append new predictions
            new_df = pd.DataFrame(new_entries)
            combined = pd.concat([existing, new_df], ignore_index=True)
            combined.to_csv(tracking_file, index=False)

            logger.info(f"✓ Logged {len(new_entries)} new predictions")
            logger.info(f"✓ Total tracked: {len(combined)}")

            # Show sample
            logger.info(f"\nSample {sport.upper()} predictions logged:")
            for entry in new_entries[:3]:
                logger.info(f"  {entry['away_team']} @ {entry['home_team']} ({entry['bet_type']})")
                logger.info(f"    Predicted: {entry['predicted_value']:.1f} | Market: {entry['market_value']:.1f}")
                logger.info(f"    Edge: {entry['edge']:+.1f} | Rec: {entry['recommendation']} | Conf: {entry['confidence']}")

        else:
            logger.info(f"All {sport.upper()} predictions already logged")

        return True

    except Exception as e:
        logger.error(f"Error logging predictions: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description='Run predictions and log for autonomous learning')
    parser.add_argument('--sport', required=True, choices=['nba', 'ncaab', 'nhl', 'nfl', 'ncaaf'],
                       help='Sport to generate predictions for')

    args = parser.parse_args()

    logger.info(f"\n{'='*80}")
    logger.info(f"AUTOMATED PREDICTION RUNNER - {args.sport.upper()}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Base Directory: {BASE_DIR}")
    logger.info(f"{'='*80}\n")

    # Run ML predictions for the sport
    predictions_file = run_ml_predictions(args.sport)

    if not predictions_file:
        logger.error(f"Failed to generate {args.sport.upper()} predictions")
        sys.exit(1)

    # Log to tracking system
    success = log_predictions_to_tracking(predictions_file, args.sport)

    if success:
        logger.info(f"\n✅ COMPLETE: {args.sport.upper()} predictions generated and logged for autonomous learning")
        sys.exit(0)
    else:
        logger.error(f"\n❌ FAILED: Could not log {args.sport.upper()} predictions")
        sys.exit(1)


if __name__ == "__main__":
    main()
