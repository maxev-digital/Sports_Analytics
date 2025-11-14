"""
Generate realistic fake referral data for testinfluencer
Creates ~80 new referrals with varied subscription tiers
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Realistic names database
FIRST_NAMES = [
    "Michael", "Jennifer", "William", "Linda", "Robert", "Patricia", "James", "Mary",
    "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah",
    "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Betty", "Matthew", "Helen",
    "Anthony", "Sandra", "Mark", "Donna", "Donald", "Carol", "Steven", "Ruth",
    "Paul", "Sharon", "Andrew", "Michelle", "Joshua", "Laura", "Kenneth", "Deborah",
    "Kevin", "Kimberly", "Brian", "Emily", "George", "Margaret", "Timothy", "Melissa",
    "Ronald", "Rebecca", "Edward", "Dorothy", "Jason", "Amanda", "Jeffrey", "Stephanie",
    "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy", "Nicholas", "Angela",
    "Eric", "Shirley", "Jonathan", "Anna", "Stephen", "Brenda", "Larry", "Pamela",
    "Justin", "Nicole", "Scott", "Katherine", "Brandon", "Samantha", "Benjamin", "Christine",
    "Samuel", "Debra", "Gregory", "Rachel", "Raymond", "Carolyn", "Frank", "Janet"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza"
]

# Subscription tiers and their commissions (25% of price)
TIERS = {
    "beta": {"commission": 2.0, "weight": 0.10},      # 10% - $8/mo tier
    "starter": {"commission": 7.25, "weight": 0.30},   # 30% - $29/mo
    "semipro": {"commission": 19.75, "weight": 0.25},  # 25% - $79/mo
    "professional": {"commission": 37.25, "weight": 0.20},  # 20% - $149/mo
    "elite": {"commission": 74.75, "weight": 0.10},    # 10% - $299/mo
    "elitepro": {"commission": 199.75, "weight": 0.05}  # 5% - $799/mo
}

REFERRALS_FILE = Path("referrals.json")

def generate_username(first_name, last_name, index):
    """Generate a realistic username"""
    options = [
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}",
        f"{first_name[0].lower()}{last_name.lower()}",
        f"{first_name.lower()}_{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}{random.randint(10, 99)}",
    ]
    return random.choice(options)

def generate_signup_date():
    """Generate a signup date in the last 120 days"""
    days_ago = random.randint(1, 120)
    return (datetime.now() - timedelta(days=days_ago)).isoformat()

def choose_tier():
    """Choose a subscription tier based on weighted probabilities"""
    tiers = list(TIERS.keys())
    weights = [TIERS[tier]["weight"] for tier in tiers]
    return random.choices(tiers, weights=weights)[0]

def load_existing_referrals():
    """Load existing referrals"""
    if REFERRALS_FILE.exists():
        with open(REFERRALS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_referrals(referrals):
    """Save referrals to file"""
    with open(REFERRALS_FILE, 'w') as f:
        json.dump(referrals, f, indent=2)

def generate_referrals(num_new=80):
    """Generate new referral data"""
    referrals = load_existing_referrals()

    existing_count = len(referrals)
    print(f"Existing referrals: {existing_count}")

    # Generate unique names
    used_names = set()
    new_referrals = []

    while len(new_referrals) < num_new:
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"

        # Ensure unique name
        if full_name in used_names:
            continue

        used_names.add(full_name)
        username = generate_username(first_name, last_name, len(new_referrals) + existing_count)

        # Avoid duplicate usernames
        if username in referrals:
            username = f"{username}{random.randint(100, 999)}"

        tier = choose_tier()
        signup_date = generate_signup_date()
        signup_dt = datetime.fromisoformat(signup_date)
        discount_end = signup_dt + timedelta(days=60)  # 2 months

        # 95% active, 5% cancelled
        status = "active" if random.random() < 0.95 else "cancelled"

        referral = {
            "referred_username": username,
            "referral_code": "TEST50",
            "influencer_username": "testinfluencer",
            "signup_date": signup_date,
            "subscription_tier": tier,
            "status": status,
            "monthly_commission": TIERS[tier]["commission"],
            "discount_applied": True,
            "discount_end_date": discount_end.isoformat(),
            "full_name": full_name  # Add full name for display
        }

        referrals[username] = referral
        new_referrals.append(referral)

    # Save updated referrals
    save_referrals(referrals)

    # Calculate stats
    total_referrals = len(referrals)
    active_referrals = sum(1 for r in referrals.values() if r["status"] == "active")
    total_commission = sum(r["monthly_commission"] for r in referrals.values() if r["status"] == "active")

    # Tier breakdown
    tier_breakdown = {}
    for tier in TIERS.keys():
        count = sum(1 for r in referrals.values() if r["subscription_tier"] == tier and r["status"] == "active")
        commission = count * TIERS[tier]["commission"]
        tier_breakdown[tier] = {"count": count, "commission": commission}

    print(f"\n{'='*60}")
    print(f"REFERRAL DATA GENERATED SUCCESSFULLY")
    print(f"{'='*60}")
    print(f"Total Referrals: {total_referrals}")
    print(f"Active Referrals: {active_referrals}")
    print(f"Cancelled: {total_referrals - active_referrals}")
    print(f"\nMonthly Commission: ${total_commission:.2f}")
    print(f"Annual Projection: ${total_commission * 12:.2f}")
    print(f"\n{'Tier':<15} {'Count':<8} {'Commission':<12}")
    print(f"{'-'*35}")
    for tier, data in tier_breakdown.items():
        print(f"{tier.capitalize():<15} {data['count']:<8} ${data['commission']:<11.2f}")
    print(f"{'='*60}")
    print(f"\nUpdated referrals.json with {num_new} new referrals")
    print(f"File location: {REFERRALS_FILE.absolute()}")

if __name__ == "__main__":
    generate_referrals(num_new=80)
