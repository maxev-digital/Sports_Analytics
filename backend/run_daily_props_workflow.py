"""
Daily NBA Props ML Workflow
Runs complete daily workflow for props predictions

Schedule:
- 8:00 AM CST: Scrape props lines
- 2:00 AM CST: Grade previous day's props
- 9:00 AM CST: Generate predictions
- Weekly: Retrain models (Mondays 4:00 AM)

Usage:
    python backend/run_daily_props_workflow.py --task morning
    python backend/run_daily_props_workflow.py --task night
    python backend/run_daily_props_workflow.py --task predictions
    python backend/run_daily_props_workflow.py --task retrain
"""

import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.props.daily_props_scraper import DailyPropsLineScraper
from scrapers.props.results_tracker import PropsResultsTracker
# Prediction and training imports will be added when models are ready


class DailyPropsWorkflow:
    """
    Orchestrates daily props ML workflow
    """

    def __init__(self):
        self.scraper = DailyPropsLineScraper()
        self.tracker = PropsResultsTracker()

    async def morning_workflow(self):
        """
        Morning workflow: Scrape today's props lines
        Run at 8:00 AM CST
        """
        print(f"\n{'='*70}")
        print(f"MORNING WORKFLOW - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        # 1. Scrape today's NBA props
        print("[1/3] Scraping NBA props lines...")
        try:
            result = await self.scraper.scrape_nba_props()
            print(f"  [OK] Scraped {result['props_stored']} props")
        except Exception as e:
            print(f"  [ERROR] Failed to scrape props: {e}")
            return

        # 2. Backup data
        print("\n[2/3] Backing up data...")
        try:
            import subprocess
            subprocess.run(['python', 'backup_props_data.py'], check=True)
            print(f"  [OK] Backup complete")
        except Exception as e:
            print(f"  [ERROR] Backup failed: {e}")

        # 3. Ready for predictions
        print(f"\n[3/3] Ready for predictions workflow")
        print(f"  Run: python backend/run_daily_props_workflow.py --task predictions")

        print(f"\n{'='*70}")
        print(f"[SUCCESS] Morning workflow complete!")
        print(f"{'='*70}\n")

    def night_workflow(self):
        """
        Night workflow: Grade previous day's props
        Run at 2:00 AM CST
        """
        print(f"\n{'='*70}")
        print(f"NIGHT WORKFLOW - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        # 1. Grade yesterday's props
        print("[1/2] Grading previous day's props...")
        yesterday = date.today() - timedelta(days=1)

        try:
            result = self.tracker.grade_previous_day_props(yesterday)
            print(f"  [OK] Graded {result['graded']} props")
            print(f"  [SKIP] {result['skipped']} (no game data)")
            print(f"  [ERROR] {result['errors']} errors")
        except Exception as e:
            print(f"  [ERROR] Failed to grade props: {e}")
            return

        # 2. Backup data
        print("\n[2/2] Backing up data...")
        try:
            import subprocess
            subprocess.run(['python', 'backup_props_data.py'], check=True)
            print(f"  [OK] Backup complete")
        except Exception as e:
            print(f"  [ERROR] Backup failed: {e}")

        print(f"\n{'='*70}")
        print(f"[SUCCESS] Night workflow complete!")
        print(f"{'='*70}\n")

    def predictions_workflow(self):
        """
        Predictions workflow: Generate ML predictions
        Run at 9:00 AM CST (after morning scrape)
        """
        print(f"\n{'='*70}")
        print(f"PREDICTIONS WORKFLOW - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        print("[INFO] Predictions workflow")
        print("  Once models are trained, this will:")
        print("  1. Load trained models")
        print("  2. Generate predictions for today's props")
        print("  3. Calculate edge and confidence")
        print("  4. Export top picks")
        print()
        print("  Run manually:")
        print("  python backend/ml/predictions/daily_props_predictor.py")

        print(f"\n{'='*70}\n")

    def retrain_workflow(self):
        """
        Retraining workflow: Retrain models weekly
        Run Mondays at 4:00 AM CST
        """
        print(f"\n{'='*70}")
        print(f"RETRAINING WORKFLOW - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        print("[INFO] Model retraining workflow")
        print("  Run:")
        print("  python backend/ml/models/nba_props_trainer.py --prop-type all")
        print()
        print("  This will:")
        print("  1. Load all graded props from database")
        print("  2. Extract features")
        print("  3. Train XGBoost, LightGBM, Random Forest")
        print("  4. Evaluate and save models")
        print("  5. Update predictions with new models")

        print(f"\n{'='*70}\n")


async def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(description='Run daily props ML workflow')
    parser.add_argument('--task', type=str, required=True,
                       choices=['morning', 'night', 'predictions', 'retrain', 'test'],
                       help='Workflow to run')

    args = parser.parse_args()

    workflow = DailyPropsWorkflow()

    if args.task == 'morning':
        await workflow.morning_workflow()

    elif args.task == 'night':
        workflow.night_workflow()

    elif args.task == 'predictions':
        workflow.predictions_workflow()

    elif args.task == 'retrain':
        workflow.retrain_workflow()

    elif args.task == 'test':
        print("\n[TEST] Running quick test of all workflows...")
        await workflow.morning_workflow()
        workflow.night_workflow()
        workflow.predictions_workflow()


if __name__ == "__main__":
    asyncio.run(main())
