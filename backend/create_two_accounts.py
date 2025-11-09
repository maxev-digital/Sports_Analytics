#!/usr/bin/env python3
"""
Create two user accounts: MissyBee and TomG
Quick script to create specific user accounts
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from subscription_db import SubscriptionDB, init_subscription_tables
import auth


def create_account(username: str, password: str, email: str, full_name: str):
    """Create a single Elite account"""

    print(f"\nCreating account for {username}...")

    # Initialize database tables
    init_subscription_tables()

    # Step 1: Create user in users.json
    users = auth.load_users()

    if username in users:
        print(f"   WARNING: User '{username}' already exists! Skipping...")
        return False

    users[username] = {
        "password_hash": auth.hash_password(password),
        "role": "user",
        "created_at": datetime.now().isoformat(),
        "full_name": full_name,
        "email": email,
        "trial_start": datetime.now().isoformat(),
        "trial_days": 0
    }
    auth.save_users(users)
    print(f"   [OK] User account created: {username}")

    # Step 2: Create user in subscription database
    SubscriptionDB.create_or_update_user(
        user_id=username,
        email=email,
        name=full_name,
        stripe_customer_id=f"test_cus_{username}"
    )
    print(f"   [OK] Database entry created")

    # Step 3: Create Elite subscription (1 year)
    period_start = datetime.now()
    period_end = period_start + timedelta(days=365)

    subscription_id = SubscriptionDB.create_subscription(
        user_id=username,
        stripe_subscription_id=f"test_sub_{username}_{int(datetime.now().timestamp())}",
        stripe_customer_id=f"test_cus_{username}",
        tier="elite",
        status="active",
        current_period_start=period_start,
        current_period_end=period_end,
        trial_end=None
    )

    if subscription_id:
        print(f"   [OK] Elite subscription created (expires: {period_end.strftime('%Y-%m-%d')})")
    else:
        print(f"   [ERROR] Failed to create subscription")
        return False

    # Verify subscription
    tier = SubscriptionDB.get_subscription_tier(username)
    if tier == "elite":
        print(f"   [OK] Verified: ELITE tier")
    else:
        print(f"   [ERROR] Verification failed: Got tier '{tier}'")
        return False

    return True


def main():
    """Create both accounts"""

    print("=" * 60)
    print("  Creating User Accounts: MissyBee and TomG")
    print("=" * 60)

    # Account 1: MissyBee
    success1 = create_account(
        username="MissyBee",
        password="Nash6274",
        email="missybee@max-ev-sports.com",
        full_name="Missy Bee"
    )

    # Account 2: TomG
    success2 = create_account(
        username="TomG",
        password="Nash6274",
        email="tomg@max-ev-sports.com",
        full_name="Tom G"
    )

    # Summary
    print("\n" + "=" * 60)
    print("  ACCOUNT CREATION SUMMARY")
    print("=" * 60)

    if success1:
        print("\n[SUCCESS] MissyBee account created")
        print("  Username: MissyBee")
        print("  Password: Nash6274")
        print("  Email:    missybee@max-ev-sports.com")
        print("  Tier:     ELITE (1 year)")

    if success2:
        print("\n[SUCCESS] TomG account created")
        print("  Username: TomG")
        print("  Password: Nash6274")
        print("  Email:    tomg@max-ev-sports.com")
        print("  Tier:     ELITE (1 year)")

    if success1 and success2:
        print("\n" + "=" * 60)
        print("  Both accounts created successfully!")
        print("  Users can login at: https://max-ev-sports.com/login")
        print("=" * 60 + "\n")
    else:
        print("\n[WARNING] Some accounts failed to create. Check messages above.\n")


if __name__ == "__main__":
    main()
