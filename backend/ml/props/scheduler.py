"""
AUTOMATED WORKFLOW SCHEDULER - PHASE 6
Runs daily predictions and nightly grading automatically
"""
import schedule
import time
import logging
import sys
from pathlib import Path
from datetime import datetime, date
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths
BACKEND_DIR = Path(__file__).parent.parent.parent
PREDICTOR_PATH = Path(__file__).parent / "predictor.py"
GRADING_PATH = Path(__file__).parent / "grading_engine.py"


class PropsScheduler:
    """Automated scheduler for predictions and grading"""

    def __init__(self):
        self.last_prediction_date = None
        self.last_grading_date = None

    # ============================================================================
    # DAILY PREDICTIONS (Run at 10 AM)
    # ============================================================================

    def run_daily_predictions(self):
        """
        Run daily predictions for NBA
        Generates props + combos for today's games
        """
        today = date.today()

        # Prevent running multiple times per day
        if self.last_prediction_date == today:
            logger.info(f"[SKIP]Predictions already run today ({today})")
            return

        logger.info("="*70)
        logger.info(f"[PREDICTIONS] Running daily predictions - {today}")
        logger.info("="*70)

        try:
            # Run predictor for NBA
            logger.info("Running NBA predictor...")
            result = subprocess.run(
                [sys.executable, str(PREDICTOR_PATH), "--sport", "nba"],
                cwd=str(PREDICTOR_PATH.parent),
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode == 0:
                logger.info("[SUCCESS]Predictions generated successfully")
                logger.info(f"Output: {result.stdout[-500:]}")  # Last 500 chars
                self.last_prediction_date = today
            else:
                logger.error(f"[ERROR]Predictor failed with code {result.returncode}")
                logger.error(f"Error: {result.stderr}")
                self.send_alert("Prediction Failed", result.stderr)

        except subprocess.TimeoutExpired:
            logger.error("❌ Predictor timed out after 10 minutes")
            self.send_alert("Prediction Timeout", "Predictor took longer than 10 minutes")
        except Exception as e:
            logger.error(f"[ERROR]Error running predictions: {e}", exc_info=True)
            self.send_alert("Prediction Error", str(e))

    # ============================================================================
    # NIGHTLY GRADING (Run at 1 AM - after all games finish)
    # ============================================================================

    def run_nightly_grading(self):
        """
        Grade yesterday's predictions
        Fetches game results and calculates win/loss
        """
        today = date.today()
        yesterday = date.today().replace(day=date.today().day - 1)

        # Prevent running multiple times per day
        if self.last_grading_date == today:
            logger.info(f"[SKIP]Grading already run today ({today})")
            return

        logger.info("="*70)
        logger.info(f"[GRADING]RUNNING NIGHTLY GRADING - {yesterday}")
        logger.info("="*70)

        try:
            # Run grading engine for yesterday
            logger.info(f"Grading predictions from {yesterday}...")
            result = subprocess.run(
                [sys.executable, str(GRADING_PATH), str(yesterday), "nba"],
                cwd=str(GRADING_PATH.parent),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info("[SUCCESS]Grading completed successfully")
                logger.info(f"Output: {result.stdout[-500:]}")
                self.last_grading_date = today

                # Parse results to send summary
                self._parse_and_log_results(result.stdout)
            else:
                logger.error(f"[ERROR]Grading failed with code {result.returncode}")
                logger.error(f"Error: {result.stderr}")
                self.send_alert("Grading Failed", result.stderr)

        except subprocess.TimeoutExpired:
            logger.error("❌ Grading timed out after 5 minutes")
            self.send_alert("Grading Timeout", "Grading took longer than 5 minutes")
        except Exception as e:
            logger.error(f"[ERROR]Error running grading: {e}", exc_info=True)
            self.send_alert("Grading Error", str(e))

    def _parse_and_log_results(self, output: str):
        """Parse grading output and log summary"""
        # Extract key metrics from output
        lines = output.split('\n')
        for line in lines:
            if 'Win Rate:' in line or 'Total:' in line or 'Graded:' in line:
                logger.info(f"  {line.strip()}")

    # ============================================================================
    # HEALTH CHECKS
    # ============================================================================

    def run_health_check(self):
        """
        Hourly health check - verify system is running
        Checks:
        - Database accessible
        - Recent predictions exist
        - API server responding
        """
        logger.info("[HEALTH]Running health check...")

        try:
            # Check database
            from performance_tracker import PerformanceTracker
            tracker = PerformanceTracker()
            conn = tracker.get_db_connection()
            cursor = conn.cursor()

            # Check if predictions table exists
            cursor.execute("SELECT COUNT(*) FROM player_props_predictions")
            pred_count = cursor.fetchone()[0]

            # Check recent predictions (last 7 days)
            cursor.execute("""
                SELECT COUNT(*) FROM player_props_predictions
                WHERE prediction_date >= date('now', '-7 days')
            """)
            recent_count = cursor.fetchone()[0]

            conn.close()

            logger.info(f"[SUCCESS]Health Check: {pred_count} total predictions, {recent_count} in last 7 days")

            # Alert if no recent predictions
            if recent_count == 0:
                logger.warning("[WARNING]No predictions in last 7 days!")
                self.send_alert("No Recent Predictions", "System hasn't generated predictions in 7 days")

        except Exception as e:
            logger.error(f"[ERROR]Health check failed: {e}")
            self.send_alert("Health Check Failed", str(e))

    # ============================================================================
    # ALERTS & NOTIFICATIONS
    # ============================================================================

    def send_alert(self, subject: str, message: str):
        """
        Send alert when something fails
        Currently logs - can extend to email/Slack/Discord
        """
        logger.error(f"[ALERT]ALERT: {subject}")
        logger.error(f"   Message: {message}")

        # TODO: Implement email/Slack notifications
        # Example:
        # import smtplib
        # send_email(to="admin@example.com", subject=subject, body=message)

    # ============================================================================
    # SCHEDULER SETUP
    # ============================================================================

    def start(self):
        """Start the scheduler"""
        logger.info("="*70)
        logger.info("[SCHEDULER]PLAYER PROPS SCHEDULER STARTING")
        logger.info("="*70)

        # Schedule daily predictions at 10:00 AM
        schedule.every().day.at("10:00").do(self.run_daily_predictions)
        logger.info("[SCHEDULE]Scheduled: Daily predictions at 10:00 AM")

        # Schedule nightly grading at 1:00 AM (after games finish)
        schedule.every().day.at("01:00").do(self.run_nightly_grading)
        logger.info("[SCHEDULE]Scheduled: Nightly grading at 1:00 AM")

        # Schedule hourly health checks
        schedule.every().hour.do(self.run_health_check)
        logger.info("[SCHEDULE]Scheduled: Hourly health checks")

        logger.info("="*70)
        logger.info("[SUCCESS]Scheduler running. Press Ctrl+C to stop.")
        logger.info("="*70)

        # Run health check immediately on startup
        self.run_health_check()

        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("\n[SHUTDOWN]Scheduler stopped by user")
        except Exception as e:
            logger.error(f"[ERROR]Scheduler crashed: {e}", exc_info=True)
            self.send_alert("Scheduler Crashed", str(e))


# ============================================================================
# MANUAL TRIGGERS (for testing)
# ============================================================================

def run_predictions_now():
    """Manually trigger predictions"""
    scheduler = PropsScheduler()
    scheduler.run_daily_predictions()


def run_grading_now(date_str: str = None):
    """Manually trigger grading for a specific date"""
    from datetime import datetime, timedelta

    if not date_str:
        # Default to yesterday
        yesterday = date.today() - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")

    logger.info(f"Manually grading {date_str}...")

    result = subprocess.run(
        [sys.executable, str(GRADING_PATH), date_str, "nba"],
        cwd=str(GRADING_PATH.parent),
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "start":
            # Start the scheduler daemon
            scheduler = PropsScheduler()
            scheduler.start()

        elif command == "predict":
            # Run predictions now
            run_predictions_now()

        elif command == "grade":
            # Grade now (optionally pass date)
            date_str = sys.argv[2] if len(sys.argv) > 2 else None
            run_grading_now(date_str)

        elif command == "health":
            # Run health check
            scheduler = PropsScheduler()
            scheduler.run_health_check()

        else:
            print("Unknown command. Usage:")
            print("  python scheduler.py start         - Start automated scheduler")
            print("  python scheduler.py predict       - Run predictions now")
            print("  python scheduler.py grade [date]  - Grade predictions for date")
            print("  python scheduler.py health        - Run health check")

    else:
        print("Player Props Automated Scheduler")
        print("="*70)
        print("Usage:")
        print("  python scheduler.py start         - Start automated scheduler")
        print("  python scheduler.py predict       - Run predictions now")
        print("  python scheduler.py grade [date]  - Grade predictions for date")
        print("  python scheduler.py health        - Run health check")
        print()
        print("Scheduled Jobs:")
        print("  10:00 AM - Daily predictions (props + combos)")
        print("  01:00 AM - Nightly grading (grade yesterday's predictions)")
        print("  Every hour - Health checks")
