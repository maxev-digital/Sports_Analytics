#!/usr/bin/env python3
"""
Barttorvik Scraper Runner - Replacement for KenPom scraper
Uses Barttorvik.com free public API instead of scraping KenPom

WHY THIS REPLACEMENT:
- KenPom changed their website structure (login form + table structure)
- Selenium scraper keeps failing with "No tables found"
- Barttorvik provides same metrics (AdjOE, AdjDE, Tempo) via free API
- More reliable, no login required, no browser automation needed
- Output format matches KenPom for compatibility with existing models

METRICS PROVIDED (KenPom equivalents):
- AdjEM = barthag (Adjusted Efficiency Margin)
- AdjOffEff = adjoe (Adjusted Offensive Efficiency)
- AdjDefEff = adjde (Adjusted Defensive Efficiency)
- AdjTempo = adjt (Adjusted Tempo)
"""

import sys
import os
import logging
from datetime import datetime

# Add scrapers directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapers', 'ncaab'))

from barttorvik_scraper import BartttorvikScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/logs/kenpom_scraper.log'),  # Keep same log file for compatibility
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run Barttorvik scraper"""
    logger.info("=" * 60)
    logger.info(f"Starting Barttorvik scraper run at {datetime.now()}")
    logger.info("=" * 60)
    logger.info("NOTE: Using Barttorvik API instead of KenPom scraper")
    logger.info("Reason: KenPom website structure changed, causing scraper failures")
    logger.info("Barttorvik provides same metrics via free public API")
    logger.info("=" * 60)

    try:
        # Initialize scraper
        scraper = BartttorvikScraper()

        # Run scraper
        logger.info("Fetching Barttorvik ratings...")
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

            # Show top 5
            logger.info("\nTop 5 Teams:")
            top_5 = df.head(5)[['Rank', 'Team', 'AdjEM', 'AdjOffEff', 'AdjDefEff']]
            logger.info(f"\n{top_5.to_string(index=False)}")

            logger.info("=" * 60)
            logger.info("✅ Barttorvik scraper completed successfully")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("❌ Failed to scrape Barttorvik data - empty result")
            return 1

    except Exception as e:
        logger.error(f"❌ Error running Barttorvik scraper: {e}", exc_info=True)
        return 1

    finally:
        logger.info("=" * 60)
        logger.info(f"Barttorvik scraper run finished at {datetime.now()}")
        logger.info("=" * 60)

if __name__ == "__main__":
    sys.exit(main())
