"""
UNIFIED STATS SCRAPER RUNNER
Executes all sports stats scrapers and reports results
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_all_scrapers(db_path: str = None):
    """Run all stats scrapers sequentially"""

    if db_path is None:
        db_path = Path(__file__).parent.parent / "predictions.db"

    logger.info("="*60)
    logger.info("STARTING ALL STATS SCRAPERS")
    logger.info("="*60)
    start_time = datetime.now()

    results = {}

    # NBA Scraper (BallDontLie API)
    try:
        logger.info("\n[1/3] Running NBA Stats Scraper (BallDontLie API)...")
        from stats_scraper_nba import NBAStatsScraperBallDontLie
        nba_scraper = NBAStatsScraperBallDontLie(db_path)
        results["nba"] = nba_scraper.scrape_all_nba_stats()
        logger.info("[SUCCESS] NBA scraper complete")
    except Exception as e:
        logger.error(f"[ERROR] NBA scraper failed: {e}")
        results["nba"] = {"error": str(e)}

    # NHL Scraper
    try:
        logger.info("\n[2/3] Running NHL Stats Scraper...")
        from stats_scraper_nhl import NHLStatsScraper
        nhl_scraper = NHLStatsScraper(db_path)
        results["nhl"] = nhl_scraper.scrape_all_nhl_stats()
        logger.info("[SUCCESS] NHL scraper complete")
    except Exception as e:
        logger.error(f"[ERROR] NHL scraper failed: {e}")
        results["nhl"] = {"error": str(e)}

    # NFL Scraper
    try:
        logger.info("\n[3/3] Running NFL Stats Scraper...")
        from stats_scraper_nfl import NFLStatsScraper
        nfl_scraper = NFLStatsScraper(db_path)
        results["nfl"] = nfl_scraper.scrape_all_nfl_stats()
        logger.info("[SUCCESS] NFL scraper complete")
    except Exception as e:
        logger.error(f"[ERROR] NFL scraper failed: {e}")
        results["nfl"] = {"error": str(e)}

    # Summary
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    logger.info("\n" + "="*60)
    logger.info("ALL STATS SCRAPERS COMPLETE")
    logger.info("="*60)

    # NBA Results
    if "error" not in results.get("nba", {}):
        nba = results["nba"]
        logger.info(f"\nNBA Results:")
        logger.info(f"  Players updated: {nba.get('players_updated', 0)}")
        logger.info(f"  Players failed: {nba.get('players_failed', 0)}")
        logger.info(f"  Teams updated: {nba.get('teams_updated', 0)}")
        logger.info(f"  Time: {nba.get('elapsed_seconds', 0):.1f}s")
    else:
        logger.error(f"\nNBA Results: FAILED - {results['nba'].get('error')}")

    # NHL Results
    if "error" not in results.get("nhl", {}):
        nhl = results["nhl"]
        logger.info(f"\nNHL Results:")
        logger.info(f"  Skaters updated: {nhl.get('skaters_updated', 0)}")
        logger.info(f"  Goalies updated: {nhl.get('goalies_updated', 0)}")
        logger.info(f"  Players failed: {nhl.get('players_failed', 0)}")
        logger.info(f"  Teams updated: {nhl.get('teams_updated', 0)}")
        logger.info(f"  Time: {nhl.get('elapsed_seconds', 0):.1f}s")
    else:
        logger.error(f"\nNHL Results: FAILED - {results['nhl'].get('error')}")

    # NFL Results
    if "error" not in results.get("nfl", {}):
        nfl = results["nfl"]
        logger.info(f"\nNFL Results:")
        logger.info(f"  QBs updated: {nfl.get('qbs_updated', 0)}")
        logger.info(f"  RBs updated: {nfl.get('rbs_updated', 0)}")
        logger.info(f"  WR/TE updated: {nfl.get('receivers_updated', 0)}")
        logger.info(f"  Players failed: {nfl.get('players_failed', 0)}")
        logger.info(f"  Teams updated: {nfl.get('teams_updated', 0)}")
        logger.info(f"  Time: {nfl.get('elapsed_seconds', 0):.1f}s")
    else:
        logger.error(f"\nNFL Results: FAILED - {results['nfl'].get('error')}")

    logger.info(f"\nTotal time: {elapsed:.1f}s")
    logger.info("="*60)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run all stats scrapers")
    parser.add_argument("--db", help="Path to predictions database")
    args = parser.parse_args()

    results = run_all_scrapers(args.db)

    # Exit with error code if any scraper failed
    failed = any("error" in r for r in results.values())
    sys.exit(1 if failed else 0)
