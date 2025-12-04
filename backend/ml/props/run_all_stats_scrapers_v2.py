"""
UNIFIED STATS SCRAPER RUNNER - Version 2
Runs all sports stats scrapers sequentially with improved error handling
Uses MoneyPuck for NHL and BallDontLie for NBA
"""

import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "predictions.db"


def run_scraper(script_name: str, description: str, db_path: str, extra_args: list = None) -> dict:
    """Run a single scraper script and return results"""
    logger.info(f"\n[RUNNING] {description}...")

    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        logger.error(f"[ERROR] Script not found: {script_path}")
        return {"success": False, "error": "Script not found"}

    try:
        cmd = [sys.executable, str(script_path), "--db", str(db_path)]
        if extra_args:
            cmd.extend(extra_args)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        if result.returncode == 0:
            logger.info(f"[SUCCESS] {description} complete")
            logger.info(result.stdout)
            return {"success": True, "output": result.stdout}
        else:
            logger.error(f"[ERROR] {description} failed")
            logger.error(result.stderr)
            return {"success": False, "error": result.stderr}

    except subprocess.TimeoutExpired:
        logger.error(f"[TIMEOUT] {description} timed out after 10 minutes")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        logger.error(f"[ERROR] {description} exception: {e}")
        return {"success": False, "error": str(e)}


def main(db_path: str = None):
    """Run all stats scrapers"""
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    logger.info("=" * 60)
    logger.info("UNIFIED STATS SCRAPER RUNNER - VERSION 2")
    logger.info("=" * 60)
    logger.info(f"Database: {db_path}")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    results = {}

    # 1. NBA Stats (BallDontLie)
    results["nba"] = run_scraper(
        script_name="stats_scraper_nba_balldontlie.py",
        description="NBA Stats (BallDontLie API)",
        db_path=db_path
    )

    # 2. NHL Stats (MoneyPuck)
    results["nhl"] = run_scraper(
        script_name="stats_scraper_nhl_moneypuck.py",
        description="NHL Stats (MoneyPuck API)",
        db_path=db_path,
        extra_args=["--season", "2024"]
    )

    # 3. NFL Stats (ESPN) - Optional, may skip if not working
    # results["nfl"] = run_scraper(
    #     script_name="stats_scraper_nfl.py",
    #     description="NFL Stats (ESPN API)",
    #     db_path=db_path
    # )

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SCRAPER RESULTS SUMMARY")
    logger.info("=" * 60)

    total_success = 0
    total_failed = 0

    for sport, result in results.items():
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        logger.info(f"{sport.upper()}: {status}")
        if result["success"]:
            total_success += 1
        else:
            total_failed += 1
            logger.error(f"  Error: {result.get('error', 'Unknown')}")

    logger.info("=" * 60)
    logger.info(f"Total Successful: {total_success}")
    logger.info(f"Total Failed: {total_failed}")
    logger.info(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # Return exit code (0 if all successful, 1 if any failed)
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run all stats scrapers")
    parser.add_argument("--db", help="Path to predictions database")
    args = parser.parse_args()

    exit_code = main(args.db)
    sys.exit(exit_code)
