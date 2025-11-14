"""
X Campaign Orchestrator
Master scheduler for automated DM campaign
- Sends 50 DMs daily at 9am CST
- Checks for replies hourly
- Generates daily reports
"""
import schedule
import time
import sys
from datetime import datetime
from pathlib import Path

# Handle both direct execution and module import
try:
    from .send_dm import send_batch
    from .listener import check_for_replies
    from .db_setup import get_campaign_stats, print_stats
    from .config import DAILY_DM_LIMIT, POLL_INTERVAL_MINUTES, check_credentials
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from x_campaign.send_dm import send_batch
    from x_campaign.listener import check_for_replies
    from x_campaign.db_setup import get_campaign_stats, print_stats
    from x_campaign.config import DAILY_DM_LIMIT, POLL_INTERVAL_MINUTES, check_credentials

def daily_dm_send():
    """Send daily batch of DMs (runs at 9am CST)"""
    print(f"\n{'='*70}")
    print(f"SCHEDULED TASK: Daily DM Send - {datetime.now()}")
    print(f"{'='*70}\n")

    send_batch(batch_size=DAILY_DM_LIMIT, dry_run=False)

def hourly_reply_check():
    """Check for replies (runs every hour)"""
    print(f"\n{'='*70}")
    print(f"SCHEDULED TASK: Reply Check - {datetime.now()}")
    print(f"{'='*70}\n")

    check_for_replies()

def nightly_report():
    """Generate daily performance report (runs at 11pm CST)"""
    print(f"\n{'='*70}")
    print(f"DAILY REPORT - {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'='*70}\n")

    print_stats()

    # TODO: Send report via email or Slack

def run_scheduler(test_mode=False):
    """
    Run the campaign scheduler

    Args:
        test_mode: If True, run tasks immediately for testing
    """
    print("\n" + "="*70)
    print("X CAMPAIGN SCHEDULER")
    print("="*70)

    # Check credentials first
    if not check_credentials():
        print("\n[WARN] Cannot start - missing credentials")
        print("See X_CAMPAIGN_ACTION_PLAN.md for setup instructions")
        return

    if test_mode:
        print("TEST MODE - Running all tasks once immediately")
        print()

        print("1. Running DM send (DRY RUN)...")
        send_batch(batch_size=5, dry_run=True)

        print("\n2. Checking for replies...")
        check_for_replies()

        print("\n3. Generating report...")
        print_stats()

        print("\n[OK] Test mode complete")
        return

    # Production schedule
    print("\nScheduling tasks:")
    print(f"  • Daily DM Send: 9:00 AM CST ({DAILY_DM_LIMIT} DMs)")
    print(f"  • Reply Check: Every {POLL_INTERVAL_MINUTES} minutes")
    print(f"  • Daily Report: 11:00 PM CST")
    print()
    print("Press Ctrl+C to stop")
    print("="*70 + "\n")

    # Schedule tasks
    schedule.every().day.at("09:00").do(daily_dm_send)  # 9am CST
    schedule.every(POLL_INTERVAL_MINUTES).minutes.do(hourly_reply_check)
    schedule.every().day.at("23:00").do(nightly_report)  # 11pm CST

    # Initial stats
    print("Current Campaign Status:")
    print_stats()
    print()

    # Run scheduler loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nScheduler stopped")

if __name__ == "__main__":
    import sys

    # Parse arguments
    test_mode = '--test' in sys.argv

    if test_mode:
        print("Running in TEST MODE")
        print("All DM sends will be DRY RUN")
        print()

    run_scheduler(test_mode=test_mode)
