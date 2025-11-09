"""
Master script to run all historical data scrapers in parallel
"""

import subprocess
import sys
import time
from datetime import datetime

def run_scraper(script_name, sport_name):
    """Run a scraper script in subprocess"""
    print(f"\n>>> Starting {sport_name} scraper...")
    print(f"   Script: {script_name}")

    process = subprocess.Popen(
        [sys.executable, script_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    return process

def main():
    print("="*60)
    print("HISTORICAL DATA COLLECTION - ALL SPORTS")
    print("="*60)
    print(f"Started: {datetime.now()}")
    print("\nRunning 4 scrapers in parallel...")
    print("This will take 15-45 minutes depending on network speed.")
    print("="*60)

    # Start all scrapers in parallel
    scrapers = {
        'NBA': run_scraper('backend/scrapers/historical/nba_historical_scraper.py', 'NBA'),
        'NFL': run_scraper('backend/scrapers/historical/nfl_historical_scraper.py', 'NFL'),
        'MLB': run_scraper('backend/scrapers/historical/mlb_historical_scraper.py', 'MLB'),
        'NCAAF': run_scraper('backend/scrapers/historical/ncaaf_historical_scraper.py', 'NCAAF'),
    }

    print("\n[INFO] All scrapers started!")
    print("\nWaiting for completion...")

    # Monitor progress
    completed = {}
    while len(completed) < 4:
        for sport, process in scrapers.items():
            if sport not in completed:
                # Check if process finished
                retcode = process.poll()
                if retcode is not None:
                    completed[sport] = retcode
                    if retcode == 0:
                        print(f"\n[OK] {sport} scraper completed successfully!")
                    else:
                        print(f"\n[ERROR] {sport} scraper FAILED with code {retcode}")

        time.sleep(5)  # Check every 5 seconds

    print("\n" + "="*60)
    print("ALL SCRAPERS COMPLETE!")
    print("="*60)
    print(f"Finished: {datetime.now()}")

    # Summary
    print("\nResults:")
    for sport, code in completed.items():
        status = "SUCCESS" if code == 0 else f"FAILED ({code})"
        print(f"  {sport}: {status}")

    print("\nData saved to:")
    print("  backend/data/historical/nba/nba_historical_latest.csv")
    print("  backend/data/historical/nfl/nfl_historical_latest.csv")
    print("  backend/data/historical/mlb/mlb_historical_latest.csv")
    print("  backend/data/historical/ncaaf/ncaaf_historical_latest.csv")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
