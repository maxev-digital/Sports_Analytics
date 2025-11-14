"""
Reply Listener
Monitors DMs for "BETA" keyword and auto-responds with partner code
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Handle both direct execution and module import
try:
    from .x_client import get_client
    from .generate_codes import create_partner_code
    from .db_setup import DB_PATH, mark_reply_received, mark_onboarded
    from .config import BETA_KEYWORD, AUTO_REPLY_TEMPLATE
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from x_campaign.x_client import get_client
    from x_campaign.generate_codes import create_partner_code
    from x_campaign.db_setup import DB_PATH, mark_reply_received, mark_onboarded
    from x_campaign.config import BETA_KEYWORD, AUTO_REPLY_TEMPLATE

def check_for_replies():
    """
    Check recent DMs for "BETA" keyword replies
    Auto-respond with referral code and onboard partner

    Returns:
        dict: {new_replies: int, onboarded: int}
    """
    print(f"\n{'='*60}")
    print("Checking for new replies...")
    print(f"{'='*60}\n")

    client = get_client()

    # Get recent DMs
    recent_dms = client.get_dms(max_results=50)

    if not recent_dms:
        print("No DMs found")
        return {'new_replies': 0, 'onboarded': 0}

    print(f"Found {len(recent_dms)} recent DMs")

    # Get partners who have been DMed but not replied
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT id, handle, dm_id
    FROM partners
    WHERE dm_sent = 1 AND replied = 0
    ''')

    pending_partners = {row[2]: (row[0], row[1]) for row in cursor.fetchall()}
    conn.close()

    print(f"Checking {len(pending_partners)} partners awaiting replies")

    stats = {
        'new_replies': 0,
        'onboarded': 0
    }

    # Check each DM
    for dm in recent_dms:
        dm_text = dm['text'].upper()
        sender_id = dm['sender_id']

        # Check if this is a reply from a pending partner
        matching_partner = None
        for dm_id, (partner_id, handle) in pending_partners.items():
            # Note: This is simplified - in production, you'd match by sender_id
            # For now, checking if DM contains the beta keyword
            if BETA_KEYWORD in dm_text:
                matching_partner = (partner_id, handle)
                break

        if not matching_partner:
            continue

        partner_id, handle = matching_partner

        print(f"\n✅ Found reply from @{handle}")
        print(f"   Message: {dm['text'][:50]}...")

        # Mark reply received
        mark_reply_received(partner_id, dm['text'])
        stats['new_replies'] += 1

        # Generate referral code
        code = create_partner_code(handle)
        print(f"   Generated code: {code}")

        # Send auto-reply with code
        reply_message = AUTO_REPLY_TEMPLATE.format(code=code)

        result = client.send_dm(handle, reply_message)

        if result['success']:
            print(f"   ✅ Sent partner portal info to @{handle}")

            # Mark as onboarded
            mark_onboarded(partner_id, code)
            stats['onboarded'] += 1

            # TODO: Create account in main system
            # TODO: Update Google Sheets

        else:
            print(f"   ❌ Failed to send auto-reply: {result.get('error')}")

    print(f"\n{'='*60}")
    print(f"Reply Check Complete")
    print(f"{'='*60}")
    print(f"New Replies: {stats['new_replies']}")
    print(f"Onboarded: {stats['onboarded']}")
    print(f"{'='*60}\n")

    return stats

def monitor_replies(interval_minutes=60):
    """
    Continuously monitor for replies at specified interval

    Args:
        interval_minutes: How often to check (default 60 min)
    """
    import time

    print(f"Starting reply monitor - checking every {interval_minutes} minutes")
    print("Press Ctrl+C to stop")
    print()

    try:
        while True:
            check_for_replies()
            print(f"\nWaiting {interval_minutes} minutes until next check...")
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        print("\n\nMonitor stopped")

if __name__ == "__main__":
    import sys

    if '--monitor' in sys.argv:
        # Continuous monitoring mode
        interval = 60
        if '--interval' in sys.argv:
            idx = sys.argv.index('--interval')
            if idx + 1 < len(sys.argv):
                interval = int(sys.argv[idx + 1])

        monitor_replies(interval_minutes=interval)
    else:
        # One-time check
        check_for_replies()
