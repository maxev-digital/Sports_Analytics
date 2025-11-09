#!/usr/bin/env python3
"""Quick verification of Colter account"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from subscription_db import SubscriptionDB
import auth

# Check users.json
users = auth.load_users()
if 'Colter' in users:
    print("[OK] User 'Colter' found in users.json")
    print(f"   Email: {users['Colter'].get('email', 'N/A')}")
    print(f"   Role: {users['Colter'].get('role', 'N/A')}")
else:
    print("[ERROR] User 'Colter' NOT found in users.json")

# Check subscription
tier = SubscriptionDB.get_subscription_tier('Colter')
if tier:
    print(f"[OK] Subscription tier: {tier.upper()}")
else:
    print("[ERROR] No subscription found")

print("\n" + "="*50)
print("COLTER ACCOUNT CREDENTIALS")
print("="*50)
print("Username: Colter")
print("Password: Colter1")
print(f"Tier: {tier.upper() if tier else 'NONE'}")
print("="*50)
