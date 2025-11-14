"""
Master Data Enrichment Script

Runs complete data enrichment pipeline:
1. Aggregate player stats from box scores (NO API)
2. Enrich with NBA Stats API (minutes, shooting %, trends)
3. Fetch injury data and identify cascade opportunities

This gives you EVERYTHING needed for advanced props betting:
- Season averages for all players
- Minutes per game for usage analysis
- Shooting percentages for hot/cold streak detection
- Recent game trends (last 10 games)
- Injury tracking and cascade bet opportunities
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_script(script_name: str, description: str):
    """
    Run a Python script and handle errors
    """
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"{'='*70}\n")

    script_path = Path(__file__).parent / script_name

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False,
            text=True
        )

        print(f"\n[OK] {description} - COMPLETE\n")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] {description} - FAILED")
        print(f"Error: {e}\n")
        return False


def main():
    """
    Run all enrichment scripts in sequence
    """
    start_time = datetime.now()

    print(f"\n{'='*70}")
    print("MASTER DATA ENRICHMENT PIPELINE")
    print(f"{'='*70}")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {}

    # Step 1: Aggregate player stats from existing box scores
    print("\n[STEP 1/3] Aggregate Player Stats from Box Scores")
    results['aggregate'] = run_script(
        'aggregate_player_stats_from_results.py',
        'Calculating season averages from 15,530 box scores'
    )

    # Step 2: Enrich with NBA Stats API
    print("\n[STEP 2/3] Enrich with NBA Stats API")
    results['nba_api'] = run_script(
        'enrich_player_stats_nba_api.py',
        'Adding minutes, shooting %, and recent trends'
    )

    # Step 3: Fetch injury data
    print("\n[STEP 3/3] Fetch Injury Data and Cascade Opportunities")
    results['injuries'] = run_script(
        'fetch_injury_data.py',
        'Tracking injuries and identifying cascade bets'
    )

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{'='*70}")
    print("ENRICHMENT PIPELINE COMPLETE")
    print(f"{'='*70}")
    print(f"Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {duration/60:.1f} minutes\n")

    print("Results:")
    print(f"  Step 1 (Aggregate):  {'✓ PASS' if results['aggregate'] else '✗ FAIL'}")
    print(f"  Step 2 (NBA API):    {'✓ PASS' if results['nba_api'] else '✗ FAIL'}")
    print(f"  Step 3 (Injuries):   {'✓ PASS' if results['injuries'] else '✗ FAIL'}")

    success_count = sum(1 for r in results.values() if r)
    print(f"\nOverall: {success_count}/3 steps completed successfully")

    if success_count == 3:
        print(f"\n{'='*70}")
        print("YOUR DATA IS NOW READY FOR ADVANCED BETTING!")
        print(f"{'='*70}")
        print("\nYou now have:")
        print("  ✓ 381 players with season averages")
        print("  ✓ Minutes per game for all players")
        print("  ✓ Shooting percentages (FG%, 3P%, FT%)")
        print("  ✓ Last 10 game trends")
        print("  ✓ Injury tracking system")
        print("  ✓ Cascade betting opportunities")
        print("\nNext steps:")
        print("  1. Retrain models with enriched features")
        print("  2. Run daily predictions with injury adjustments")
        print("  3. Monitor cascade opportunities for value bets")
        print(f"{'='*70}\n")
    else:
        print(f"\n[WARN] Some enrichment steps failed. Check logs above.")

    print(f"Database: D:/backend/data/player_props.db")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
