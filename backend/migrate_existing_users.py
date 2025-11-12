"""
Migration script to add subscriptions for existing users
Gives all existing users without subscriptions a free Elite tier (as early supporters)
"""

import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from auth import load_users
from subscription_db import SubscriptionDB

def migrate_users():
    """Add subscriptions for all existing users without them"""
    users = load_users()

    print(f"Found {len(users)} total users")

    migrated = 0
    skipped = 0

    for username, user_data in users.items():
        # Check if user already has a subscription
        existing_sub = SubscriptionDB.get_subscription(username)

        if existing_sub:
            print(f"✓ {username} already has subscription: {existing_sub['tier']}")
            skipped += 1
            continue

        # Give existing users Elite tier for free (early supporters)
        # Set trial_end 1 year from now
        trial_end = datetime.now() + timedelta(days=365)

        # Create subscription
        sub_id = SubscriptionDB.create_subscription(
            user_id=username,
            stripe_subscription_id=None,
            stripe_customer_id=None,
            tier="elite",  # Elite tier for early supporters
            status="active",
            trial_end=trial_end
        )

        if sub_id:
            print(f"✓ Migrated {username} → Elite tier (1 year free)")
            migrated += 1
        else:
            print(f"✗ Failed to migrate {username}")

    print(f"\n{'='*50}")
    print(f"Migration complete:")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped (already had subscription): {skipped}")
    print(f"  Total: {len(users)}")
    print(f"{'='*50}")

if __name__ == "__main__":
    migrate_users()
