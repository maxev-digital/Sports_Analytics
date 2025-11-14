#!/usr/bin/env python3
"""
Automated Daily Grading Script
Grades all predictions from yesterday using completed game results

Schedule: 1:00 AM CST daily (7:00 AM UTC)
This runs AFTER games finish but BEFORE next day's predictions
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backfill_results import backfill_results
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("="*80)
    logger.info("AUTOMATED DAILY GRADING")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("="*80)

    # Grade last 3 days (Odds API free tier limit)
    # This ensures we catch any late-finishing games
    logger.info("\nGrading predictions from last 3 days...")

    try:
        backfill_results(
            sport=None,  # All sports
            days=3,      # Last 3 days
            dry_run=False  # Save results
        )

        logger.info("\n✅ DAILY GRADING COMPLETE")
        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ GRADING FAILED: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
