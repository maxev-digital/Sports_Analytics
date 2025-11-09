#!/usr/bin/env python3
"""
KenPom Scraper Runner - Automated daily scraper for NCAAB stats
Runs daily to fetch latest KenPom ratings for NCAA Basketball
"""

import sys
import os
import logging
from datetime import datetime

# Add scrapers directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapers', 'ncaab'))

from ken_pom_scraper_selenium_fixed import KenPomSeleniumScraper

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

# KenPom credentials
KENPOM_EMAIL = 'gte.apw@gmail.com'
KENPOM_PASSWORD = 'Thewrench1!'

def main():
    """Run KenPom scraper"""
    logger.info("=" * 60)
    logger.info(f"Starting KenPom scraper run at {datetime.now()}")
    logger.info("=" * 60)

    try:
        # Initialize scraper with credentials
        scraper = KenPomSeleniumScraper(
            email=KENPOM_EMAIL,
            password=KENPOM_PASSWORD,
            headless=True  # Run in headless mode on server
        )

        # Run scraper
        logger.info("Fetching KenPom ratings...")
        df = scraper.run()

        if df is not None and len(df) > 0:
            logger.info(f"✅ SUCCESS! Scraped {len(df)} teams")
            logger.info(f"Features: {len(df.columns)}")
            logger.info(f"Columns: {list(df.columns)}")

            # Show summary stats
            if 'AdjTempo' in df.columns:
                logger.info(f"Tempo range: {df['AdjTempo'].min():.1f} - {df['AdjTempo'].max():.1f}")
            if 'AdjOffEff' in df.columns:
                logger.info(f"OffEff range: {df['AdjOffEff'].min():.1f} - {df['AdjOffEff'].max():.1f}")
            if 'AdjDefEff' in df.columns:
                logger.info(f"DefEff range: {df['AdjDefEff'].min():.1f} - {df['AdjDefEff'].max():.1f}")

            logger.info("✅ KenPom scraper completed successfully")
            return 0
        else:
            logger.error("❌ Failed to scrape KenPom data - empty result")
            return 1

    except Exception as e:
        logger.error(f"❌ Error running KenPom scraper: {e}", exc_info=True)
        return 1

    finally:
        logger.info("=" * 60)
        logger.info(f"KenPom scraper run finished at {datetime.now()}")
        logger.info("=" * 60)

if __name__ == "__main__":
    sys.exit(main())
