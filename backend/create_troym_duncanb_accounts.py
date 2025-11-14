#!/usr/bin/env python3
"""
Create Two Elite Accounts
Account 1: TroyM / Caddyshack
Account 2: DuncanB / Babydolls
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from subscription_db import SubscriptionDB, init_subscription_tables
import auth


def create_elite_account(username: str, password: str, email: str, full_name: str):
    """Create an Elite account with expiration date 12/9/2026"""

    print(f"\n{'='*60}")
    print(f"Creating Elite Account: {username}")
    print(f"{'='*60}\n")

    # Initialize database tables
    init_subscription_tables()

    # Step 1: Create user in users.json
    print(f"1. Creating user account...")
    users = auth.load_users()

    if username in users:
        print(f"   WARNING: User '{username}' already exists!")
        print(f"   Upgrading to Elite subscription...")
    else:
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
    print(f"2. Creating subscription database entry...")
    SubscriptionDB.create_or_update_user(
        user_id=username,
        email=email,
        name=full_name,
        stripe_customer_id=f"elite_cus_{username.lower()}"
    )
    print(f"   [OK] Database entry created")

    # Step 3: Create Elite subscription
    print(f"3. Creating Elite subscription...")

    # Set expiration to 12/9/2026 to match other accounts
    period_start = datetime.now()
    period_end = datetime(2026, 12, 9, 23, 59, 59)

    subscription_id = SubscriptionDB.create_subscription(
        user_id=username,
        stripe_subscription_id=f"elite_sub_{username.lower()}_{int(datetime.now().timestamp())}",
        stripe_customer_id=f"elite_cus_{username.lower()}",
        tier="elite",
        status="active",
        current_period_start=period_start,
        current_period_end=period_end,
        trial_end=None
    )

    if subscription_id:
        print(f"   [OK] Elite subscription created (ID: {subscription_id})")
    else:
        print(f"   [ERROR] Failed to create subscription")
        return False

    # Step 4: Verify subscription
    print(f"4. Verifying subscription...")
    tier = SubscriptionDB.get_subscription_tier(username)
    if tier == "elite":
        print(f"   [OK] Subscription verified: {tier.upper()}")
    else:
        print(f"   [ERROR] Verification failed: Got tier '{tier}' instead of 'elite'")
        return False

    # Success summary
    print(f"\n{'='*60}")
    print(f"ELITE ACCOUNT CREATED SUCCESSFULLY")
    print(f"{'='*60}\n")
    print(f"Username:     {username}")
    print(f"Password:     {password}")
    print(f"Email:        {email}")
    print(f"Tier:         ELITE")
    print(f"Valid Until:  {period_end.strftime('%Y-%m-%d')}")
    print(f"\n{'='*60}\n")

    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CREATING TWO ELITE ACCOUNTS")
    print("="*60)

    # Account 1: TroyM
    success1 = create_elite_account(
        username="TroyM",
        password="Caddyshack",
        email="troym@maxevsports.com",
        full_name="TroyM"
    )

    # Account 2: DuncanB
    success2 = create_elite_account(
        username="DuncanB",
        password="Babydolls",
        email="duncanb@maxevsports.com",
        full_name="DuncanB"
    )

    if success1 and success2:
        print("\n" + "="*60)
        print("BOTH ACCOUNTS CREATED SUCCESSFULLY")
        print("="*60)
        print("\nAccount 1:")
        print("  Username: TroyM")
        print("  Password: Caddyshack")
        print("\nAccount 2:")
        print("  Username: DuncanB")
        print("  Password: Babydolls")
        print("\nLogin URL: https://max-ev-sports.com/login")
        print("="*60 + "\n")
    else:
        print("\nFAILED to create one or more accounts. Check the error messages above.\n")
        sys.exit(1)
