#!/usr/bin/env python3
"""
Master Scraper Runner - Runs all TeamRankings scrapers daily

This script refreshes all sports databases from TeamRankings.com:
- NBA (30 teams)
- NFL (32 teams)
- NCAAF (130+ teams)
- MLB (30 teams)

Run this script daily in the morning CST to keep data fresh.

Usage:
    python run_all_scrapers.py
    python run_all_scrapers.py --force  # Force refresh (bypass cache)
"""

import sys
import logging
from datetime import datetime
import argparse

# Add backend to path if needed
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.teamrankings_nba_scraper import TeamRankingsNBAScraper
from scrapers.teamrankings_nfl_scraper import TeamRankingsNFLScraper
from scrapers.teamrankings_ncaaf_scraper import TeamRankingsNCAAFScraper
from scrapers.teamrankings_mlb_scraper import TeamRankingsMLBScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/logs/scraper_runs.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def run_all_scrapers(force_refresh: bool = False):
    """
    Run all TeamRankings scrapers

    Args:
        force_refresh: Bypass cache and fetch fresh data
    """
    start_time = datetime.now()
    logger.info("="*80)
    logger.info(f"Starting scraper run at {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("="*80)

    results = {}

    # 1. NBA Scraper
    logger.info("\n[1/4] Running NBA scraper...")
    try:
        nba_scraper = TeamRankingsNBAScraper()
        nba_stats = nba_scraper.fetch_all_team_stats(force_refresh=force_refresh)
        results['nba'] = {
            'status': 'success',
            'teams': len(nba_stats),
            'cache_file': nba_scraper.CACHE_FILE
        }
        logger.info(f"✅ NBA: {len(nba_stats)} teams scraped successfully")
    except Exception as e:
        results['nba'] = {'status': 'error', 'error': str(e)}
        logger.error(f"❌ NBA scraper failed: {e}")

    # 2. NFL Scraper
    logger.info("\n[2/4] Running NFL scraper...")
    try:
        nfl_scraper = TeamRankingsNFLScraper()
        nfl_stats = nfl_scraper.fetch_all_team_stats(force_refresh=force_refresh)
        results['nfl'] = {
            'status': 'success',
            'teams': len(nfl_stats),
            'cache_file': nfl_scraper.CACHE_FILE
        }
        logger.info(f"✅ NFL: {len(nfl_stats)} teams scraped successfully")
    except Exception as e:
        results['nfl'] = {'status': 'error', 'error': str(e)}
        logger.error(f"❌ NFL scraper failed: {e}")

    # 3. NCAAF Scraper
    logger.info("\n[3/4] Running NCAAF scraper...")
    try:
        ncaaf_scraper = TeamRankingsNCAAFScraper()
        ncaaf_stats = ncaaf_scraper.fetch_all_team_stats(force_refresh=force_refresh)
        results['ncaaf'] = {
            'status': 'success',
            'teams': len(ncaaf_stats),
            'cache_file': ncaaf_scraper.CACHE_FILE
        }
        logger.info(f"✅ NCAAF: {len(ncaaf_stats)} teams scraped successfully")
    except Exception as e:
        results['ncaaf'] = {'status': 'error', 'error': str(e)}
        logger.error(f"❌ NCAAF scraper failed: {e}")

    # 4. MLB Scraper
    logger.info("\n[4/4] Running MLB scraper...")
    try:
        mlb_scraper = TeamRankingsMLBScraper()
        mlb_stats = mlb_scraper.fetch_all_team_stats(force_refresh=force_refresh)
        results['mlb'] = {
            'status': 'success',
            'teams': len(mlb_stats),
            'cache_file': mlb_scraper.CACHE_FILE
        }
        logger.info(f"✅ MLB: {len(mlb_stats)} teams scraped successfully")
    except Exception as e:
        results['mlb'] = {'status': 'error', 'error': str(e)}
        logger.error(f"❌ MLB scraper failed: {e}")

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info("\n" + "="*80)
    logger.info("SCRAPER RUN SUMMARY")
    logger.info("="*80)

    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    total_teams = sum(r.get('teams', 0) for r in results.values() if r['status'] == 'success')

    for sport, result in results.items():
        if result['status'] == 'success':
            logger.info(f"✅ {sport.upper()}: {result['teams']} teams")
        else:
            logger.info(f"❌ {sport.upper()}: {result['error']}")

    logger.info("-"*80)
    logger.info(f"Total: {success_count}/{len(results)} scrapers succeeded")
    logger.info(f"Teams scraped: {total_teams}")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("="*80)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run all TeamRankings scrapers')
    parser.add_argument('--force', action='store_true', help='Force refresh (bypass cache)')
    args = parser.parse_args()

    try:
        # Create logs directory if it doesn't exist
        os.makedirs('backend/logs', exist_ok=True)

        # Run scrapers
        results = run_all_scrapers(force_refresh=args.force)

        # Exit with error code if any scraper failed
        failed = sum(1 for r in results.values() if r['status'] == 'error')
        sys.exit(1 if failed > 0 else 0)

    except KeyboardInterrupt:
        logger.info("\n⚠️  Scraper run interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        sys.exit(1)
