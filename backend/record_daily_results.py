"""
Automatic Daily Result Recorder
Runs daily at 1am to backfill previous day's game results

This script automatically fetches final scores and records outcomes for
predictions made in the last 3 days, ensuring continuous performance tracking
without manual intervention.

Designed to be run via cron:
    0 1 * * * cd /root/sporttrader/backend && source venv/bin/activate && python3 record_daily_results.py >> logs/results_recorder.log 2>&1
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'results_recorder_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main function to record daily results"""
    logger.info("="*80)
    logger.info("AUTOMATIC DAILY RESULT RECORDER")
    logger.info(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)

    try:
        # Import backfill script
        from backfill_results import backfill_results

        # Run backfill for last 3 days (covers yesterday + buffer for timezone issues)
        logger.info("Running backfill for last 3 days...")
        backfill_results(
            sport=None,  # All sports
            days=3,      # Last 3 days (API limit)
            dry_run=False
        )

        logger.info("")
        logger.info("="*80)
        logger.info("DAILY RESULT RECORDING COMPLETE")
        logger.info(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80)
        logger.info("")

    except Exception as e:
        logger.error(f"Error during daily result recording: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
