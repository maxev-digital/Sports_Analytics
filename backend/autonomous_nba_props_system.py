"""
AUTONOMOUS NBA PLAYER PROPS SYSTEM
Master automation script - runs complete daily workflow

Schedule this to run via Windows Task Scheduler or cron:
- Daily at 9am CST: Full workflow
- Daily at 11pm CST: Fetch results and grade predictions
- Weekly Sunday 3am CST: Retrain models

No manual intervention required.
"""

import subprocess
import sys
import os
from datetime import datetime, time
from pathlib import Path
import logging

# Setup logging
log_dir = Path("D:/backend/logs/autonomous_system")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f"autonomous_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class AutonomousNBAPropsSystem:
    """
    Complete autonomous workflow for NBA player props predictions
    """

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.data_dir = Path("D:/backend/data")
        self.db_path = self.data_dir / "player_props.db"

    def run_script(self, script_path: str, description: str, timeout: int = 600):
        """
        Run a Python script and log results
        """
        logger.info(f"Starting: {description}")
        logger.info(f"Script: {script_path}")

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.base_dir
            )

            if result.returncode == 0:
                logger.info(f"✓ SUCCESS: {description}")
                if result.stdout:
                    logger.debug(f"Output: {result.stdout[:500]}")
                return True
            else:
                logger.error(f"✗ FAILED: {description}")
                logger.error(f"Error: {result.stderr[:500]}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"✗ TIMEOUT: {description} exceeded {timeout}s")
            return False
        except Exception as e:
            logger.error(f"✗ ERROR: {description} - {str(e)}")
            return False

    def daily_morning_workflow(self):
        """
        Morning workflow (9am CST):
        1. Fetch today's props lines
        2. Update player data (injuries, recent stats)
        3. Generate predictions
        4. Output high-value bets
        """
        logger.info("="*70)
        logger.info("AUTONOMOUS NBA PROPS - MORNING WORKFLOW")
        logger.info("="*70)
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        logger.info(f"Time: {datetime.now().strftime('%H:%M:%S CST')}")
        logger.info("")

        results = {}

        # Step 1: Fetch today's props lines (Odds API)
        results['props_fetch'] = self.run_script(
            self.base_dir / "scrapers/props/daily_props_scraper.py",
            "Fetch Today's Props Lines",
            timeout=300
        )

        # Step 2: Enrich player data (NBA API + Injuries)
        results['data_enrich'] = self.run_script(
            self.base_dir / "scrapers/props/enrich_all_data.py",
            "Update Player Stats & Injuries",
            timeout=600
        )

        # Step 3: Generate predictions
        results['predictions'] = self.run_script(
            self.base_dir / "ml/predictions/daily_props_predictor_fast.py",
            "Generate ML Predictions",
            timeout=180
        )

        # Summary
        success_count = sum(1 for r in results.values() if r)
        logger.info("")
        logger.info("="*70)
        logger.info(f"MORNING WORKFLOW COMPLETE: {success_count}/3 steps successful")
        logger.info("="*70)

        for step, success in results.items():
            status = "✓" if success else "✗"
            logger.info(f"{status} {step}")

        return success_count == 3

    def daily_night_workflow(self):
        """
        Night workflow (11pm CST):
        1. Fetch game results for today
        2. Grade predictions (win/loss/push)
        3. Update performance metrics
        """
        logger.info("="*70)
        logger.info("AUTONOMOUS NBA PROPS - NIGHT WORKFLOW")
        logger.info("="*70)
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        logger.info(f"Time: {datetime.now().strftime('%H:%M:%S CST')}")
        logger.info("")

        results = {}

        # Step 1: Fetch today's results
        results['fetch_results'] = self.run_script(
            self.base_dir / "scrapers/props/fetch_daily_results.py",
            "Fetch Game Results",
            timeout=300
        )

        # Step 2: Grade predictions
        results['grade_predictions'] = self.run_script(
            self.base_dir / "utils/grade_predictions.py",
            "Grade Predictions",
            timeout=120
        )

        # Summary
        success_count = sum(1 for r in results.values() if r)
        logger.info("")
        logger.info("="*70)
        logger.info(f"NIGHT WORKFLOW COMPLETE: {success_count}/2 steps successful")
        logger.info("="*70)

        return success_count == 2

    def weekly_retraining_workflow(self):
        """
        Weekly workflow (Sunday 3am CST):
        1. Aggregate past week's results
        2. Retrain all 28 models
        3. Evaluate new model performance
        4. Deploy if improved
        """
        logger.info("="*70)
        logger.info("AUTONOMOUS NBA PROPS - WEEKLY RETRAINING")
        logger.info("="*70)
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        logger.info(f"Time: {datetime.now().strftime('%H:%M:%S CST')}")
        logger.info("")

        results = {}

        # Step 1: Aggregate weekly data
        results['aggregate_data'] = self.run_script(
            self.base_dir / "scrapers/props/aggregate_player_stats_from_results.py",
            "Aggregate Weekly Results",
            timeout=180
        )

        # Step 2: Retrain all models
        results['retrain_models'] = self.run_script(
            self.base_dir / "ml/models/retrain_all_props_models.py",
            "Retrain All 28 Models",
            timeout=1800  # 30 minutes
        )

        # Step 3: Evaluate performance
        results['evaluate'] = self.run_script(
            self.base_dir / "ml/evaluation/evaluate_model_performance.py",
            "Evaluate Model Performance",
            timeout=300
        )

        # Summary
        success_count = sum(1 for r in results.values() if r)
        logger.info("")
        logger.info("="*70)
        logger.info(f"WEEKLY RETRAINING COMPLETE: {success_count}/3 steps successful")
        logger.info("="*70)

        return success_count == 3


def main():
    """
    Main entry point - determines which workflow to run based on arguments
    """
    import argparse

    parser = argparse.ArgumentParser(description='Autonomous NBA Props System')
    parser.add_argument('workflow', choices=['morning', 'night', 'weekly'],
                       help='Which workflow to run')

    args = parser.parse_args()

    system = AutonomousNBAPropsSystem()

    if args.workflow == 'morning':
        success = system.daily_morning_workflow()
    elif args.workflow == 'night':
        success = system.daily_night_workflow()
    elif args.workflow == 'weekly':
        success = system.weekly_retraining_workflow()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
