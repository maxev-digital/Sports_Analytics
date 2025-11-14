#!/usr/bin/env python3
"""
Create the first real partner account for MAX-EV Sports
This is separate from the test account.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from influencer_system import create_influencer

def create_real_partner():
    """
    Create first real partner account.

    Use this template and replace with actual partner info.
    """

    print("=" * 60)
    print("CREATE FIRST REAL PARTNER")
    print("=" * 60)
    print()

    # Template - REPLACE WITH REAL INFO
    partner_info = {
        "username": "realpartner",  # Change this!
        "password": "SecurePassword123!",  # Change this!
        "email": "partner@email.com",  # Change this!
        "full_name": "Real Partner Name",  # Change this!
        "platform": "twitter",  # twitter, instagram, youtube, tiktok
        "platform_handle": "@partnername",  # Change this!
        "follower_count": 50000,  # Change this!
        "referral_code": "PARTNER10",  # Change this! (uppercase, no spaces)
        "payment_email": "paypal@email.com",  # For commission payouts
    }

    print("Partner Info:")
    for key, value in partner_info.items():
        if key != "password":
            print(f"  {key}: {value}")
    print()

    # Confirm before creating
    confirm = input("Create this partner? (yes/no): ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        return

    try:
        # Create partner
        result = create_influencer(
            username=partner_info["username"],
            password=partner_info["password"],
            email=partner_info["email"],
            full_name=partner_info["full_name"],
            platform=partner_info["platform"],
            platform_handle=partner_info["platform_handle"],
            follower_count=partner_info["follower_count"],
            referral_code=partner_info["referral_code"],
            payment_email=partner_info["payment_email"],
        )

        print()
        print("=" * 60)
        print("✅ PARTNER CREATED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print(f"Username: {partner_info['username']}")
        print(f"Password: {partner_info['password']}")
        print(f"Referral Code: {partner_info['referral_code']}")
        print()
        print("NEXT STEPS:")
        print("1. Test login at: https://max-ev-sports.com/#/influencer-login")
        print(f"2. Share referral code: {partner_info['referral_code']}")
        print("3. Test user signup with code")
        print("4. Verify referral appears in partner dashboard")
        print()
        print("Partner Portal: https://max-ev-sports.com/#/influencer-dashboard")
        print("=" * 60)

    except Exception as e:
        print()
        print("❌ ERROR creating partner:")
        print(f"  {str(e)}")
        print()
        print("Check if username or referral code already exists.")


def list_existing_partners():
    """Show existing partners"""

    try:
        with open(Path(__file__).parent / "influencers.json", "r") as f:
            influencers = json.load(f)

        print()
        print("=" * 60)
        print("EXISTING PARTNERS")
        print("=" * 60)
        print()

        if not influencers:
            print("No partners yet.")
            return

        for username, data in influencers.items():
            status = data.get("status", "unknown")
            code = data.get("referral_code", "N/A")
            platform = data.get("platform", "N/A")
            followers = data.get("follower_count", 0)

            print(f"Username: {username}")
            print(f"  Code: {code}")
            print(f"  Platform: {platform} ({followers:,} followers)")
            print(f"  Status: {status}")
            print()

        print("=" * 60)

    except FileNotFoundError:
        print("No partners file found.")
    except Exception as e:
        print(f"Error reading partners: {e}")


if __name__ == "__main__":
    print()
    print("MAX-EV SPORTS - Partner Account Creator")
    print()

    # Show existing partners first
    list_existing_partners()

    print()
    choice = input("Create new partner? (yes/no): ")

    if choice.lower() == "yes":
        print()
        print("IMPORTANT: Edit create_first_real_partner.py")
        print("Update the partner_info dictionary with real info.")
        print()
        create_real_partner()
    else:
        print("Cancelled.")
