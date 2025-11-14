#!/usr/bin/env python3
"""
Create a quick test account for immediate login
"""
import sys
import json
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import auth

# Create test account
username = "testuser"
password = "test123"
email = "test@max-ev-sports.com"

users = auth.load_users()

users[username] = {
    "password_hash": auth.hash_password(password),
    "role": "user",
    "created_at": datetime.now().isoformat(),
    "full_name": "Test User",
    "email": email,
    "trial_start": datetime.now().isoformat(),
    "trial_days": 7
}

auth.save_users(users)

print(f"\n{'='*60}")
print(f"TEST ACCOUNT CREATED SUCCESSFULLY")
print(f"{'='*60}\n")
print(f"Username: {username}")
print(f"Password: {password}")
print(f"Login at: http://localhost:5174/login")
print(f"\n{'='*60}\n")
