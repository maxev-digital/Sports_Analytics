#!/usr/bin/env python3
"""
Remove Sheets and TenTon accounts
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from subscription_db import SubscriptionDB, init_subscription_tables, get_db_connection
import auth


def remove_account(username: str):
    """Remove account from users.json and subscription database"""

    print(f"\nRemoving account: {username}")

    # Step 1: Remove from users.json
    print(f"1. Removing from users.json...")
    users = auth.load_users()

    if username in users:
        del users[username]
        auth.save_users(users)
        print(f"   [OK] Removed {username} from users.json")
    else:
        print(f"   [WARNING] {username} not found in users.json")

    # Step 2: Delete subscription from database
    print(f"2. Removing subscription from database...")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Delete subscription
            cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (username,))
            deleted_subs = cursor.rowcount

            # Delete user entry
            cursor.execute('DELETE FROM users WHERE id = ?', (username,))
            deleted_users = cursor.rowcount

            print(f"   [OK] Deleted {deleted_subs} subscription(s) and {deleted_users} user(s) from database")

    except Exception as e:
        print(f"   [ERROR] Failed to remove from database: {e}")
        return False

    print(f"   [OK] {username} account fully removed\n")
    return True


if __name__ == "__main__":
    print("="*60)
    print("REMOVING SHEETS AND TENTON ACCOUNTS")
    print("="*60)

    # Initialize database
    init_subscription_tables()

    # Remove accounts
    success1 = remove_account("Sheets")
    success2 = remove_account("TenTon")

    print("="*60)
    if success1 and success2:
        print("BOTH ACCOUNTS REMOVED SUCCESSFULLY")
    else:
        print("SOME ACCOUNTS FAILED TO REMOVE - CHECK ERRORS ABOVE")
    print("="*60 + "\n")
