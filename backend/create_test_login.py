"""Create a test user account for local development"""
import hashlib
import json
from pathlib import Path

# Test credentials
USERNAME = "testlocal"
PASSWORD = "test123"
EMAIL = "test@local.com"

# Hash the password
password_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()

# Load existing users
users_file = Path("users.json")
if users_file.exists():
    with open(users_file, 'r') as f:
        users = json.load(f)
else:
    users = {}

# Add test user
users[USERNAME] = {
    "password_hash": password_hash,
    "created_at": "2025-11-11T00:00:00",
    "role": "admin",
    "email": EMAIL,
    "full_name": "Test User Local"
}

# Save users
with open(users_file, 'w') as f:
    json.dump(users, f, indent=2)

print(f"Created test user:")
print(f"   Username: {USERNAME}")
print(f"   Password: {PASSWORD}")
print(f"   Hash: {password_hash}")
