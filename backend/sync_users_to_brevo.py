"""
Manual Brevo User Sync Script
Syncs users from users.json to Brevo CRM
"""

import json
from datetime import datetime
from brevo_crm import sync_signup_to_brevo, send_welcome_email
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_users():
    """Load users from users.json"""
    with open('users.json', 'r') as f:
        return json.load(f)


def sync_all_users_to_brevo():
    """Sync all users to Brevo CRM"""
    users = load_users()

    synced = 0
    failed = 0
    skipped = 0

    for username, user_data in users.items():
        # Skip default/admin accounts
        if username in ['admin', 'user1', 'user2', 'user3', 'user4']:
            logger.info(f"Skipping default account: {username}")
            skipped += 1
            continue

        email = user_data.get('email')
        full_name = user_data.get('full_name', username)
        trial_start = user_data.get('trial_start', user_data.get('created_at'))
        trial_days = user_data.get('trial_days', 7)

        if not email:
            logger.warning(f"No email for user {username}, skipping")
            skipped += 1
            continue

        logger.info(f"Syncing user: {username} ({email})")

        try:
            # Sync to Brevo
            success = sync_signup_to_brevo(
                email=email,
                full_name=full_name,
                username=username,
                trial_start=trial_start,
                trial_days=trial_days
            )

            if success:
                logger.info(f"✅ Successfully synced {username} to Brevo")
                synced += 1
            else:
                logger.error(f"❌ Failed to sync {username} to Brevo")
                failed += 1

        except Exception as e:
            logger.error(f"❌ Error syncing {username}: {e}")
            failed += 1

    # Print summary
    print("\n" + "="*60)
    print("BREVO SYNC SUMMARY")
    print("="*60)
    print(f"✅ Synced:  {synced}")
    print(f"❌ Failed:  {failed}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"📊 Total:   {synced + failed + skipped}")
    print("="*60)


def sync_users_from_date(date_str):
    """Sync only users who signed up on or after a specific date"""
    users = load_users()
    target_date = datetime.fromisoformat(date_str)

    synced = 0
    failed = 0
    skipped = 0

    for username, user_data in users.items():
        # Skip default/admin accounts
        if username in ['admin', 'user1', 'user2', 'user3', 'user4']:
            skipped += 1
            continue

        created_at = user_data.get('created_at')
        if not created_at:
            logger.warning(f"No created_at for user {username}, skipping")
            skipped += 1
            continue

        # Parse date
        try:
            user_date = datetime.fromisoformat(created_at)
        except:
            logger.warning(f"Invalid date format for {username}, skipping")
            skipped += 1
            continue

        # Check if user signed up on or after target date
        if user_date < target_date:
            logger.info(f"User {username} signed up before {date_str}, skipping")
            skipped += 1
            continue

        email = user_data.get('email')
        full_name = user_data.get('full_name', username)
        trial_start = user_data.get('trial_start', created_at)
        trial_days = user_data.get('trial_days', 7)

        if not email:
            logger.warning(f"No email for user {username}, skipping")
            skipped += 1
            continue

        logger.info(f"Syncing user: {username} ({email}) - signed up {user_date.strftime('%Y-%m-%d %H:%M')}")

        try:
            # Sync to Brevo
            success = sync_signup_to_brevo(
                email=email,
                full_name=full_name,
                username=username,
                trial_start=trial_start,
                trial_days=trial_days
            )

            if success:
                logger.info(f"✅ Successfully synced {username} to Brevo")
                synced += 1
            else:
                logger.error(f"❌ Failed to sync {username} to Brevo")
                failed += 1

        except Exception as e:
            logger.error(f"❌ Error syncing {username}: {e}")
            failed += 1

    # Print summary
    print("\n" + "="*60)
    print(f"BREVO SYNC SUMMARY (from {date_str})")
    print("="*60)
    print(f"✅ Synced:  {synced}")
    print(f"❌ Failed:  {failed}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"📊 Total:   {synced + failed + skipped}")
    print("="*60)


if __name__ == "__main__":
    import sys

    print("="*60)
    print("BREVO USER SYNC TOOL")
    print("="*60)
    print()

    if len(sys.argv) > 1:
        # Sync users from specific date
        date_str = sys.argv[1]
        print(f"Syncing users from: {date_str}")
        print()
        sync_users_from_date(date_str)
    else:
        # Sync all users
        print("Syncing ALL users (except defaults)")
        print()
        response = input("Are you sure? This will sync all users to Brevo. (yes/no): ")
        if response.lower() == 'yes':
            sync_all_users_to_brevo()
        else:
            print("Cancelled.")
