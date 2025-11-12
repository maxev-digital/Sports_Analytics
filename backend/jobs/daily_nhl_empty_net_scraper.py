"""
Daily NHL Empty Net Stats Scraper Job
Runs daily in the morning to fetch latest empty net statistics from MoreHockeyStats.com

Schedule: Daily at 9am CST (before daily predictions run)
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.nhl.morehockeystats_en_scraper import MoreHockeyStatsENScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run daily empty net scraper"""
    logger.info("=" * 70)
    logger.info("DAILY NHL EMPTY NET STATS SCRAPER")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    try:
        # Initialize scraper
        scraper = MoreHockeyStatsENScraper()

        # Scrape latest data
        logger.info("Scraping empty net stats from MoreHockeyStats.com...")
        df = scraper.scrape_empty_net_stats()

        if df.empty:
            logger.error("❌ Failed to scrape empty net data")
            sys.exit(1)

        logger.info(f"✅ Successfully scraped data for {len(df)} teams")

        # Save with timestamp
        logger.info("Saving timestamped version...")
        scraper.save_to_csv(df)

        # Save as latest (this is what the API will load)
        logger.info("Saving as latest version...")
        latest_path = scraper.save_to_latest(df)

        # Display summary
        logger.info("\n" + "=" * 70)
        logger.info("SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Teams scraped: {len(df)}")
        logger.info(f"Total EN goals scored: {df['en_goals_for'].sum():.0f}")
        logger.info(f"Total EN goals allowed: {df['en_goals_against'].sum():.0f}")
        logger.info(f"Avg per team: {df['en_goals_for'].mean():.2f} for / {df['en_goals_against'].mean():.2f} against")
        logger.info(f"\nData saved to: {latest_path}")

        # Top/Bottom 3
        logger.info("\n📊 Top 3 Teams (EN Differential):")
        top3 = df.nlargest(3, 'en_differential')[['Team', 'en_differential']]
        for _, row in top3.iterrows():
            logger.info(f"  • {row['Team']}: {row['en_differential']:+.0f}")

        logger.info("\n📉 Bottom 3 Teams (EN Differential):")
        bottom3 = df.nsmallest(3, 'en_differential')[['Team', 'en_differential']]
        for _, row in bottom3.iterrows():
            logger.info(f"  • {row['Team']}: {row['en_differential']:+.0f}")

        logger.info("\n" + "=" * 70)
        logger.info("✅ DAILY SCRAPE COMPLETE")
        logger.info(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"❌ Error in daily scraper: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
