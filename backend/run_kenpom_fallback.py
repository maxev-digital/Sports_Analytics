#!/usr/bin/env python3
"""
KenPom Fallback - Uses last successful scrape until scraper fixed
Temporary solution while KenPom/Barttorvik scrapers are broken

This script:
1. Finds the most recent successful KenPom scrape
2. Copies it with today's timestamp
3. Logs the fallback action

WHY THIS IS NEEDED:
- KenPom website structure changed (December 2025)
- Selenium scraper fails with "No tables found"
- Barttorvik API also changed
- NCAAB predictions need KenPom ratings daily
- Last successful scrape: November 28, 2025
- Data doesn't change drastically day-to-day during season

RECOMMENDATION:
- Use this fallback for now
- Monitor for KenPom API or alternative data source
- Re-scrape weekly when scraper fixed
"""

import sys
import os
import logging
import shutil
import glob
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/logs/kenpom_scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def find_latest_kenpom_file():
    """Find the most recent KenPom scrape file"""
    data_dir = 'backend/data/raw/ncaab'
    pattern = os.path.join(data_dir, 'kenpom_ratings_*.csv')

    files = glob.glob(pattern)
    if not files:
        logger.error("❌ No previous KenPom files found!")
        return None

    # Get most recent file
    latest_file = max(files, key=os.path.getmtime)
    file_date = datetime.fromtimestamp(os.path.getmtime(latest_file))

    logger.info(f"Found latest KenPom file: {os.path.basename(latest_file)}")
    logger.info(f"Last modified: {file_date.strftime('%Y-%m-%d %H:%M:%S')}")

    return latest_file

def copy_with_new_timestamp(source_file):
    """Copy the file with today's timestamp"""
    data_dir = 'backend/data/raw/ncaab'

    # Generate new filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    new_filename = f'kenpom_ratings_{timestamp}.csv'
    new_filepath = os.path.join(data_dir, new_filename)

    # Copy file
    shutil.copy2(source_file, new_filepath)
    logger.info(f"✅ Copied to: {os.path.basename(new_filepath)}")

    return new_filepath

def main():
    """Run KenPom fallback"""
    logger.info("=" * 60)
    logger.info(f"Starting KenPom FALLBACK at {datetime.now()}")
    logger.info("=" * 60)
    logger.warning("⚠️  USING FALLBACK MODE - Scraper currently broken")
    logger.info("Reason: KenPom website structure changed")
    logger.info("Action: Copying last successful scrape with new timestamp")
    logger.info("=" * 60)

    try:
        # Find latest file
        latest_file = find_latest_kenpom_file()
        if not latest_file:
            logger.error("❌ Cannot proceed - no previous data found")
            return 1

        # Check how old it is
        file_date = datetime.fromtimestamp(os.path.getmtime(latest_file))
        days_old = (datetime.now() - file_date).days

        if days_old > 14:
            logger.warning(f"⚠️  WARNING: Data is {days_old} days old!")
            logger.warning("Consider finding alternative data source soon")

        # Copy with new timestamp
        new_file = copy_with_new_timestamp(latest_file)

        # Show summary
        logger.info("=" * 60)
        logger.info("FALLBACK SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Source: {os.path.basename(latest_file)}")
        logger.info(f"Age: {days_old} days old")
        logger.info(f"Output: {os.path.basename(new_file)}")
        logger.info("")
        logger.info("✅ KenPom fallback completed successfully")
        logger.info("⚠️  NOTE: This is using old data until scraper is fixed")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"❌ Error in fallback: {e}", exc_info=True)
        return 1

    finally:
        logger.info("=" * 60)
        logger.info(f"KenPom fallback finished at {datetime.now()}")
        logger.info("=" * 60)

if __name__ == "__main__":
    sys.exit(main())
