"""Create a dedicated admin account for monitoring feedback and managing the platform"""
import json
import hashlib
from datetime import datetime
from pathlib import Path

# Admin credentials
ADMIN_USERNAME = "MaxEVAdmin"
ADMIN_PASSWORD = "MaxEV2025!Admin"  # Secure password
ADMIN_EMAIL = "admin@max-ev-sports.com"

def create_admin():
    users_file = Path("users.json")

    # Load existing users
    if users_file.exists():
        with open(users_file, 'r') as f:
            users = json.load(f)
    else:
        users = {}

    # Create password hash
    password_hash = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()

    # Add admin account
    users[ADMIN_USERNAME] = {
        "password_hash": password_hash,
        "created_at": datetime.now().isoformat(),
        "role": "admin",
        "email": ADMIN_EMAIL,
        "full_name": "Max EV Admin"
    }

    # Save updated users
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)

    print("Admin account created successfully!")
    print(f"\nUsername: {ADMIN_USERNAME}")
    print(f"Password: {ADMIN_PASSWORD}")
    print(f"Role: admin")
    print(f"Email: {ADMIN_EMAIL}")
    print(f"\nYou can now log in at: https://max-ev-sports.com")
    print("Access feedback at: https://max-ev-sports.com/admin-dashboard")

if __name__ == "__main__":
    create_admin()
