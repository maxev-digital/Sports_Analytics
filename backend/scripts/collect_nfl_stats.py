"""
NFL Stats Collection Script
Fetches data from TeamRankings and stores in database
Calculates betting trends from odds archive
Run this daily via cron/Task Scheduler
"""
import sys
sys.path.insert(0, 'backend')

from database.nfl_db import NFLDatabase
from scrapers.teamrankings_nfl_scraper import TeamRankingsNFLScraper
from scrapers.nfl_betting_trends_calculator import NFLBettingTrendsCalculator
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/logs/nfl_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def collect_team_stats():
    """Scrape and store NFL team stats from TeamRankings"""
    logger.info("=" * 80)
    logger.info("Starting NFL Team Stats Collection")
    logger.info("=" * 80)

    try:
        # Initialize database and scraper
        db = NFLDatabase()
        scraper = TeamRankingsNFLScraper()

        # Fetch all team stats (with 6-hour cache)
        logger.info("Fetching team stats from TeamRankings...")
        team_stats = scraper.fetch_all_team_stats(force_refresh=True)

        if not team_stats:
            logger.error("No team stats returned from scraper!")
            return False

        logger.info(f"Fetched stats for {len(team_stats)} teams")

        # Store each team's stats in database
        stored_count = 0
        for team_name, stats in team_stats.items():
            try:
                # Use simplified insert method
                db.insert_team_stats_simple(team_name, 2024, stats)
                stored_count += 1
                logger.info(f"Stored {team_name}")

            except Exception as e:
                logger.error(f"Error storing {team_name}: {str(e)}")
                continue

        logger.info("=" * 80)
        logger.info(f"Team Stats Collection Complete! Stored {stored_count}/{len(team_stats)} teams")
        logger.info("=" * 80)

        # Print database stats
        db_stats = db.get_database_stats()
        logger.info(f"\nDatabase now contains:")
        logger.info(f"  - {db_stats['nfl_team_stats']} team stat records")
        logger.info(f"  - Latest scrape: {db_stats['latest_team_stats_scrape']}")

        db.close()
        return True

    except Exception as e:
        logger.error(f"Collection FAILED: {str(e)}", exc_info=True)
        return False


def collect_betting_trends():
    """Calculate and store NFL betting trends from odds archive"""
    logger.info("\n" + "=" * 80)
    logger.info("Starting NFL Betting Trends Collection")
    logger.info("=" * 80)

    try:
        # Initialize database and calculator
        db = NFLDatabase()
        calculator = NFLBettingTrendsCalculator()

        # Calculate trends for last 120 days (covers full season)
        logger.info("Calculating betting trends from odds archive (last 120 days)...")
        all_trends = calculator.calculate_team_trends(lookback_days=120)

        if not all_trends:
            logger.warning("No betting trends calculated (odds archive may be empty)")
            db.close()
            return True  # Not a failure, just no data yet

        logger.info(f"Calculated trends for {len(all_trends)} teams")

        # Store each team's trends in database
        stored_count = 0
        for team_name, trends in all_trends.items():
            try:
                db.insert_betting_trends_from_calculator(team_name, 2024, trends)
                stored_count += 1
                logger.info(f"Stored trends for {team_name} ({trends['games_analyzed']} games)")

            except Exception as e:
                logger.error(f"Error storing trends for {team_name}: {str(e)}")
                continue

        logger.info("=" * 80)
        logger.info(f"Trends Collection Complete! Stored {stored_count}/{len(all_trends)} teams")
        logger.info("=" * 80)

        # Print database stats
        db_stats = db.get_database_stats()
        logger.info(f"\nDatabase now contains:")
        logger.info(f"  - {db_stats['nfl_betting_trends']} betting trends records")
        logger.info(f"  - Latest trends scrape: {db_stats['latest_trends_scrape']}")

        db.close()
        return True

    except Exception as e:
        logger.error(f"Trends collection FAILED: {str(e)}", exc_info=True)
        return False


if __name__ == '__main__':
    # Collect team stats first
    stats_success = collect_team_stats()

    # Then calculate betting trends (only if on VPS with odds_history.db)
    trends_success = collect_betting_trends()

    # Exit with success if both completed
    sys.exit(0 if (stats_success and trends_success) else 1)
