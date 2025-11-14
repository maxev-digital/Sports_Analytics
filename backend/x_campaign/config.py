"""
Configuration for X Campaign
Loads API credentials and campaign settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# X API Credentials (will be added after Elevated Access approval)
X_API_KEY = os.getenv("X_API_KEY", "")
X_API_SECRET = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET", "")
X_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

# Google Sheets
GOOGLE_SHEET_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEETS_SHEET_ID", "")

# Campaign Settings
DAILY_DM_LIMIT = 50
DM_DELAY_SECONDS = 120  # 2 minutes between DMs
POLL_INTERVAL_MINUTES = 60  # Check for replies every hour
BETA_KEYWORD = "BETA"  # Keyword to trigger auto-response

# Referral Code Settings
COMMISSION_RATE = 0.25  # 25% recurring commission
BETA_DISCOUNT = 0.50  # 50% off for beta partners

# Database
DB_PATH = Path(__file__).parent / 'referrals.db'

# DM Template
DM_TEMPLATE = """Hey {handle}!

I'm with Max EV Sports - we just launched a sports betting analytics platform with ML-powered predictions, arbitrage detection, and live in-game alerts.

We're inviting {follower_count}+ influencers to our beta partner program:
- Free Elite access ($199/mo value)
- 25% recurring commission on referrals
- Custom dashboard + referral tracking
- Early access to new features

Interested? Reply "BETA" and I'll send your partner code + portal link.

Check us out: https://max-ev-sports.com

{why_target}

- Max EV Sports Team"""

# Auto-reply template
AUTO_REPLY_TEMPLATE = """Welcome to the Max EV Sports partner program!

Your Details:
- Referral Code: {code}
- Commission: 25% recurring
- Partner Portal: https://max-ev-sports.com/partners

Your Portal:
https://beta.maxevsports.com/ref/{code}

Share this link with your audience. When they sign up:
1. They get 50% off (beta discount)
2. You earn 25% recurring commission
3. Track everything in your dashboard

Questions? DM anytime or email partnerships@max-ev-sports.com

Let's make some money together!"""

def check_credentials():
    """Verify all required credentials are present"""
    missing = []

    if not X_API_KEY:
        missing.append("X_API_KEY")
    if not X_API_SECRET:
        missing.append("X_API_SECRET")
    if not X_ACCESS_TOKEN:
        missing.append("X_ACCESS_TOKEN")
    if not X_ACCESS_SECRET:
        missing.append("X_ACCESS_SECRET")
    if not GOOGLE_SHEET_CREDENTIALS:
        missing.append("GOOGLE_SHEET_CREDENTIALS")

    if missing:
        print(f"[WARN] Missing credentials: {', '.join(missing)}")
        print("Add these to backend/.env before launching campaign")
        return False

    print("[OK] All credentials loaded successfully")
    return True

if __name__ == "__main__":
    print("X Campaign Configuration")
    print("=" * 50)
    print(f"Daily DM Limit: {DAILY_DM_LIMIT}")
    print(f"DM Delay: {DM_DELAY_SECONDS}s")
    print(f"Poll Interval: {POLL_INTERVAL_MINUTES} min")
    print(f"Commission Rate: {COMMISSION_RATE * 100}%")
    print(f"Beta Discount: {BETA_DISCOUNT * 100}%")
    print()
    check_credentials()
