#!/usr/bin/env python3
"""
Create a test Elite account for beta testing
Usage: python create_test_elite_account.py
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from subscription_db import SubscriptionDB, init_subscription_tables
import auth


def create_elite_test_account(
    username: str,
    email: str,
    full_name: str,
    password: str = "TestPassword123!"
):
    """
    Create a test Elite account

    Args:
        username: Username for login
        email: User's email address
        full_name: User's full name
        password: Password (default: TestPassword123!)
    """

    print(f"\n{'='*60}")
    print(f"Creating Elite Test Account")
    print(f"{'='*60}\n")

    # Initialize database tables
    init_subscription_tables()

    # Step 1: Create user in users.json
    print(f"1. Creating user account...")
    users = auth.load_users()

    if username in users:
        print(f"   WARNING: User '{username}' already exists!")
        response = input("   Do you want to upgrade existing user to Elite? (yes/no): ")
        if response.lower() != 'yes':
            print("   Aborted.")
            return False
    else:
        users[username] = {
            "password_hash": auth.hash_password(password),
            "role": "user",
            "created_at": datetime.now().isoformat(),
            "full_name": full_name,
            "email": email,
            "trial_start": datetime.now().isoformat(),
            "trial_days": 0  # No trial needed for test account
        }
        auth.save_users(users)
        print(f"   [OK] User account created: {username}")

    # Step 2: Create user in subscription database
    print(f"2. Creating subscription database entry...")
    SubscriptionDB.create_or_update_user(
        user_id=username,
        email=email,
        name=full_name,
        stripe_customer_id=f"test_cus_{username}"
    )
    print(f"   [OK] Database entry created")

    # Step 3: Create Elite subscription
    print(f"3. Creating Elite subscription...")

    # Calculate subscription period (1 year for testing)
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
    print(f"ELITE TEST ACCOUNT CREATED SUCCESSFULLY")
    print(f"{'='*60}\n")
    print(f"Email:        {email}")
    print(f"Username:     {username}")
    print(f"Password:     {password}")
    print(f"Tier:         ELITE")
    print(f"Valid Until:  {period_end.strftime('%Y-%m-%d')}")
    print(f"\n{'='*60}\n")

    return True


def main():
    """Main function - Interactive account creation"""

    print("\n" + "="*60)
    print("  MAX EV SPORTS - Elite Test Account Creator")
    print("="*60 + "\n")

    # Get account details
    print("Enter test account details:")
    print("-" * 40)

    username = input("Username (e.g., 'simspeed'): ").strip()
    if not username:
        print("ERROR: Username is required")
        return

    email = input("Email (e.g., 'simspeed@gmail.com'): ").strip()
    if not email:
        print("ERROR: Email is required")
        return

    full_name = input("Full Name (e.g., 'Sim Speed'): ").strip()
    if not full_name:
        print("ERROR: Full name is required")
        return

    password = input("Password (or press Enter for default 'TestPassword123!'): ").strip()
    if not password:
        password = "TestPassword123!"

    # Confirm
    print(f"\n" + "-"*40)
    print("Review account details:")
    print(f"  Username:  {username}")
    print(f"  Email:     {email}")
    print(f"  Name:      {full_name}")
    print(f"  Password:  {password}")
    print(f"  Tier:      ELITE (1 year access)")
    print("-"*40)

    confirm = input("\nCreate this account? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Account creation cancelled")
        return

    # Create the account
    success = create_elite_test_account(
        username=username,
        email=email,
        full_name=full_name,
        password=password
    )

    if success:
        print("SUCCESS! You can now share these credentials with your beta tester!")
        print("   They can login at: https://max-ev-sports.com/login")
        print("   Or in the desktop app.\n")
    else:
        print("FAILED to create account. Check the error messages above.\n")


if __name__ == "__main__":
    main()
