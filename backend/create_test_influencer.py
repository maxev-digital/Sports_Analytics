"""
Create test influencer account with sample referrals
"""
import json
import hashlib
from datetime import datetime, timedelta
import random

# Test influencer credentials
INFLUENCER_USERNAME = "testinfluencer"
INFLUENCER_PASSWORD = "test123"
INFLUENCER_EMAIL = "test@influencer.com"
INFLUENCER_CODE = "TEST50"

# File paths
INFLUENCERS_FILE = "influencers.json"
REFERRALS_FILE = "referrals.json"

# Tier pricing
TIER_PRICING = {
    'beta': 9.99,
    'starter': 29.99,
    'semipro': 49.99,
    'professional': 99.99,
    'elite': 199.99,
    'elitepro': 299.99
}

COMMISSION_RATE = 0.20  # 20%

def hash_password(password: str) -> str:
    """Hash password with SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_test_influencer():
    """Create test influencer account"""
    # Load existing influencers
    try:
        with open(INFLUENCERS_FILE, 'r') as f:
            influencers = json.load(f)
    except FileNotFoundError:
        influencers = {}

    # Create test influencer
    influencers[INFLUENCER_USERNAME] = {
        "username": INFLUENCER_USERNAME,
        "email": INFLUENCER_EMAIL,
        "password_hash": hash_password(INFLUENCER_PASSWORD),
        "full_name": "Test Influencer",
        "social_media_handle": "@testinfluencer",
        "platform": "Twitter",
        "follower_count": 50000,
        "referral_code": INFLUENCER_CODE,
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "total_referrals": 20,
        "payment_email": "payment@influencer.com"
    }

    # Save influencers
    with open(INFLUENCERS_FILE, 'w') as f:
        json.dump(influencers, f, indent=2)

    print(f"[OK] Created test influencer: {INFLUENCER_USERNAME}")
    print(f"  Password: {INFLUENCER_PASSWORD}")
    print(f"  Referral Code: {INFLUENCER_CODE}")

def create_sample_referrals():
    """Create 20 sample referrals with various tiers"""
    # Load existing referrals
    try:
        with open(REFERRALS_FILE, 'r') as f:
            referrals = json.load(f)
    except FileNotFoundError:
        referrals = {}

    # Sample user names
    first_names = ["John", "Jane", "Mike", "Sarah", "David", "Emma", "Chris", "Lisa",
                   "Ryan", "Amy", "Tom", "Kate", "Dan", "Nicole", "Brian", "Rachel",
                   "Steve", "Maria", "Kevin", "Jessica"]

    # Tier distribution (realistic mix)
    tiers = [
        'beta', 'beta', 'beta',  # 3 beta users
        'starter', 'starter', 'starter', 'starter',  # 4 starter users
        'semipro', 'semipro', 'semipro',  # 3 semi-pro users
        'professional', 'professional', 'professional', 'professional', 'professional',  # 5 professional users
        'elite', 'elite', 'elite',  # 3 elite users
        'elitepro', 'elitepro'  # 2 elite pro users
    ]

    # Create referrals
    base_date = datetime.now() - timedelta(days=90)  # Started 90 days ago

    for i in range(20):
        username = f"{first_names[i].lower()}_user{i+1}"

        # Random signup date within last 90 days
        days_ago = random.randint(0, 90)
        signup_date = base_date + timedelta(days=days_ago)

        # 90% active, 10% cancelled
        status = "active" if random.random() < 0.9 else "cancelled"

        tier = tiers[i]
        monthly_price = TIER_PRICING[tier]
        monthly_commission = monthly_price * COMMISSION_RATE

        referrals[username] = {
            "referred_username": username,
            "referral_code": INFLUENCER_CODE,
            "influencer_username": INFLUENCER_USERNAME,
            "signup_date": signup_date.isoformat(),
            "subscription_tier": tier,
            "status": status,
            "monthly_commission": round(monthly_commission, 2),
            "discount_applied": True,
            "discount_end_date": (signup_date + timedelta(days=60)).isoformat()
        }

    # Save referrals
    with open(REFERRALS_FILE, 'w') as f:
        json.dump(referrals, f, indent=2)

    print(f"\n[OK] Created 20 sample referrals")

    # Calculate and display summary
    active_count = sum(1 for r in referrals.values() if r['status'] == 'active' and r['influencer_username'] == INFLUENCER_USERNAME)
    total_commission = sum(r['monthly_commission'] for r in referrals.values() if r['status'] == 'active' and r['influencer_username'] == INFLUENCER_USERNAME)

    # Count by tier
    tier_breakdown = {}
    for r in referrals.values():
        if r['influencer_username'] == INFLUENCER_USERNAME and r['status'] == 'active':
            tier = r['subscription_tier']
            if tier not in tier_breakdown:
                tier_breakdown[tier] = {'count': 0, 'commission': 0}
            tier_breakdown[tier]['count'] += 1
            tier_breakdown[tier]['commission'] += r['monthly_commission']

    print(f"\n[SUMMARY]")
    print(f"  Total Referrals: 20")
    print(f"  Active Referrals: {active_count}")
    print(f"  Monthly Earnings: ${total_commission:.2f}")
    print(f"  Annual Projection: ${total_commission * 12:.2f}")
    print(f"\n  Breakdown by Tier:")
    for tier, data in sorted(tier_breakdown.items()):
        print(f"    {tier.title()}: {data['count']} users = ${data['commission']:.2f}/mo")

if __name__ == "__main__":
    print("Creating test influencer account with sample data...\n")
    create_test_influencer()
    create_sample_referrals()
    print("\n[SUCCESS] Test data created successfully!")
    print("\nLogin at: http://localhost:5173/#/influencer-login")
    print(f"Username: {INFLUENCER_USERNAME}")
    print(f"Password: {INFLUENCER_PASSWORD}")
