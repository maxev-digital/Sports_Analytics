#!/usr/bin/env python3
"""
Update Elite Account Expiration Dates to 12/9/2026
Updates: Mom, MikeS, GregS, Schuess, MickK
"""

import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from subscription_db import SubscriptionDB, init_subscription_tables


def update_expiration_date(username: str, new_end_date: str):
    """Update subscription expiration date"""

    print(f"\nUpdating {username}...")

    # Parse the new end date
    new_date = datetime.strptime(new_end_date, "%Y-%m-%d")

    # Get current subscription
    subscription = SubscriptionDB.get_subscription(username)

    if not subscription:
        print(f"  [ERROR] No subscription found for {username}")
        return False

    # Get stripe_subscription_id from the subscription
    stripe_sub_id = subscription.get('stripe_subscription_id')
    if not stripe_sub_id:
        print(f"  [ERROR] No stripe_subscription_id found for {username}")
        return False

    # Update the subscription end date
    success = SubscriptionDB.update_subscription(
        stripe_subscription_id=stripe_sub_id,
        current_period_end=new_date
    )

    if success:
        # Verify the update
        tier = SubscriptionDB.get_subscription_tier(username)
        print(f"  [OK] {username} - Tier: {tier.upper()}, New expiration: {new_end_date}")
        return True
    else:
        print(f"  [ERROR] Failed to update {username}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("UPDATING ELITE ACCOUNT EXPIRATION DATES")
    print("New expiration date: 2026-12-09")
    print("="*60)

    # Initialize database
    init_subscription_tables()

    # New expiration date (12/9/2026)
    new_expiration = "2026-12-09"

    # List of accounts to update
    accounts = ["Mom", "MikeS", "GregS", "Schuess", "MickK"]

    results = []
    for account in accounts:
        success = update_expiration_date(account, new_expiration)
        results.append((account, success))

    # Summary
    print("\n" + "="*60)
    print("UPDATE SUMMARY")
    print("="*60)

    successful = [acc for acc, success in results if success]
    failed = [acc for acc, success in results if not success]

    if successful:
        print(f"\n[OK] Successfully updated {len(successful)} account(s):")
        for acc in successful:
            print(f"  - {acc}")

    if failed:
        print(f"\n[ERROR] Failed to update {len(failed)} account(s):")
        for acc in failed:
            print(f"  - {acc}")

    print("\n" + "="*60 + "\n")

    if failed:
        sys.exit(1)
