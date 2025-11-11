"""
Influencer Referral System
Manages influencer partnerships, referral codes, and commission tracking
"""
import json
import secrets
import hashlib
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

# Data files
INFLUENCERS_FILE = Path("influencers.json")
REFERRALS_FILE = Path("referrals.json")
INFLUENCER_EARNINGS_FILE = Path("influencer_earnings.json")

# Commission rate
COMMISSION_RATE = 0.20  # 20% recurring commission

# Subscription tier pricing (monthly)
TIER_PRICING = {
    'trial': 0.00,
    'beta': 9.99,
    'starter': 29.99,
    'semipro': 49.99,
    'professional': 99.99,
    'elite': 199.99,
    'elitepro': 299.99
}


def load_influencers() -> Dict:
    """Load influencers from file"""
    if INFLUENCERS_FILE.exists():
        with open(INFLUENCERS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_influencers(influencers: Dict):
    """Save influencers to file"""
    with open(INFLUENCERS_FILE, 'w') as f:
        json.dump(influencers, f, indent=2)


def load_referrals() -> Dict:
    """Load referrals from file"""
    if REFERRALS_FILE.exists():
        with open(REFERRALS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_referrals(referrals: Dict):
    """Save referrals to file"""
    with open(REFERRALS_FILE, 'w') as f:
        json.dump(referrals, f, indent=2)


def load_earnings() -> Dict:
    """Load earnings tracking from file"""
    if INFLUENCER_EARNINGS_FILE.exists():
        with open(INFLUENCER_EARNINGS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_earnings(earnings: Dict):
    """Save earnings tracking to file"""
    with open(INFLUENCER_EARNINGS_FILE, 'w') as f:
        json.dump(earnings, f, indent=2)


def generate_referral_code(influencer_name: str, custom_code: Optional[str] = None) -> str:
    """
    Generate a unique referral code

    Args:
        influencer_name: Name of the influencer
        custom_code: Custom code requested by influencer (optional)

    Returns:
        Unique referral code
    """
    if custom_code:
        # Validate custom code
        custom_code = custom_code.upper().strip()
        if not custom_code.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Custom code must be alphanumeric (hyphens and underscores allowed)")
        if len(custom_code) < 3 or len(custom_code) > 20:
            raise ValueError("Custom code must be 3-20 characters")

        # Check if code already exists
        influencers = load_influencers()
        for inf_data in influencers.values():
            if inf_data['referral_code'].upper() == custom_code:
                raise ValueError("This referral code is already taken")

        return custom_code
    else:
        # Generate code from name
        base_code = ''.join(c.upper() for c in influencer_name if c.isalnum())[:10]

        # Add random suffix to ensure uniqueness
        influencers = load_influencers()
        while True:
            suffix = secrets.token_hex(2).upper()
            code = f"{base_code}_{suffix}"

            # Check if unique
            if not any(inf['referral_code'] == code for inf in influencers.values()):
                return code


def register_influencer(
    username: str,
    email: str,
    password: str,
    full_name: str,
    social_media_handle: str,
    platform: str,
    follower_count: int,
    custom_code: Optional[str] = None,
    payment_email: Optional[str] = None
) -> Dict:
    """
    Register a new influencer

    Args:
        username: Unique username for influencer login
        email: Influencer email
        password: Password for influencer dashboard
        full_name: Influencer's full name
        social_media_handle: Their handle (e.g., @username)
        platform: Primary platform (Twitter, Instagram, YouTube, TikTok, etc.)
        follower_count: Approximate follower count
        custom_code: Optional custom referral code
        payment_email: Email for payment (defaults to main email)

    Returns:
        Dictionary with influencer data
    """
    influencers = load_influencers()

    # Check if username already exists
    if username in influencers:
        raise ValueError("Username already exists")

    # Check if email already exists
    if any(inf['email'] == email for inf in influencers.values()):
        raise ValueError("Email already registered")

    # Generate referral code
    referral_code = generate_referral_code(full_name, custom_code)

    # Hash password
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    # Create influencer record
    influencer_data = {
        'username': username,
        'email': email,
        'password_hash': password_hash,
        'full_name': full_name,
        'social_media_handle': social_media_handle,
        'platform': platform,
        'follower_count': follower_count,
        'referral_code': referral_code,
        'payment_email': payment_email or email,
        'created_at': datetime.now().isoformat(),
        'status': 'active',  # active, paused, suspended
        'total_referrals': 0,
        'total_earnings': 0.0,
        'lifetime_earnings': 0.0
    }

    influencers[username] = influencer_data
    save_influencers(influencers)

    return influencer_data


def verify_influencer_credentials(username: str, password: str) -> bool:
    """Verify influencer login credentials"""
    influencers = load_influencers()

    if username not in influencers:
        return False

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return influencers[username]['password_hash'] == password_hash


def get_influencer_by_code(referral_code: str) -> Optional[Dict]:
    """Get influencer data by referral code"""
    referral_code = referral_code.upper().strip()
    influencers = load_influencers()

    for username, inf_data in influencers.items():
        if inf_data['referral_code'].upper() == referral_code:
            return {**inf_data, 'username': username}

    return None


def get_influencer_by_username(username: str) -> Optional[Dict]:
    """Get influencer data by username"""
    influencers = load_influencers()

    if username in influencers:
        return {**influencers[username], 'username': username}

    return None


def track_referral(username: str, referral_code: str, subscription_tier: str) -> bool:
    """
    Track a new user referral

    Args:
        username: New user who signed up
        referral_code: Referral code used
        subscription_tier: Subscription tier selected

    Returns:
        Boolean indicating success
    """
    # Get influencer
    influencer = get_influencer_by_code(referral_code)
    if not influencer:
        return False

    # Load referrals
    referrals = load_referrals()

    # Create referral record
    referral_record = {
        'referred_username': username,
        'influencer_username': influencer['username'],
        'referral_code': referral_code,
        'subscription_tier': subscription_tier,
        'signup_date': datetime.now().isoformat(),
        'status': 'active',  # active, cancelled, expired
        'discount_applied': True,
        'discount_end_date': None,  # Will be set after first payment
        'monthly_commission': TIER_PRICING.get(subscription_tier, 0) * COMMISSION_RATE
    }

    # Save referral
    if username not in referrals:
        referrals[username] = referral_record
        save_referrals(referrals)

        # Update influencer stats
        influencers = load_influencers()
        influencers[influencer['username']]['total_referrals'] += 1
        save_influencers(influencers)

        return True

    return False


def get_influencer_referrals(influencer_username: str) -> List[Dict]:
    """Get all referrals for an influencer"""
    referrals = load_referrals()

    influencer_referrals = [
        {**ref_data, 'referred_username': username}
        for username, ref_data in referrals.items()
        if ref_data['influencer_username'] == influencer_username
    ]

    return influencer_referrals


def calculate_influencer_earnings(influencer_username: str) -> Dict:
    """
    Calculate total earnings for an influencer

    Returns:
        Dictionary with earnings breakdown
    """
    referrals = get_influencer_referrals(influencer_username)

    total_monthly = 0.0
    active_referrals = 0
    by_tier = {}

    for referral in referrals:
        if referral['status'] == 'active':
            tier = referral['subscription_tier']
            commission = referral['monthly_commission']

            total_monthly += commission
            active_referrals += 1

            if tier not in by_tier:
                by_tier[tier] = {'count': 0, 'commission': 0.0}

            by_tier[tier]['count'] += 1
            by_tier[tier]['commission'] += commission

    return {
        'influencer_username': influencer_username,
        'total_monthly_commission': round(total_monthly, 2),
        'active_referrals': active_referrals,
        'total_referrals': len(referrals),
        'breakdown_by_tier': by_tier,
        'annual_projection': round(total_monthly * 12, 2)
    }


def update_referral_status(username: str, new_status: str, new_tier: Optional[str] = None):
    """Update referral status when subscription changes"""
    referrals = load_referrals()

    if username in referrals:
        referrals[username]['status'] = new_status

        if new_tier:
            referrals[username]['subscription_tier'] = new_tier
            referrals[username]['monthly_commission'] = TIER_PRICING.get(new_tier, 0) * COMMISSION_RATE

        save_referrals(referrals)
        return True

    return False


def get_all_influencers() -> List[Dict]:
    """Get list of all influencers (admin function)"""
    influencers = load_influencers()

    return [
        {
            'username': username,
            **inf_data
        }
        for username, inf_data in influencers.items()
    ]


def update_influencer_status(username: str, status: str) -> bool:
    """Update influencer status (admin function)"""
    influencers = load_influencers()

    if username in influencers:
        influencers[username]['status'] = status
        save_influencers(influencers)
        return True

    return False


def validate_referral_code(code: str) -> Dict:
    """
    Validate a referral code and return discount info

    Returns:
        Dictionary with validation result and discount info
    """
    influencer = get_influencer_by_code(code)

    if not influencer:
        return {
            'valid': False,
            'message': 'Invalid referral code'
        }

    if influencer['status'] != 'active':
        return {
            'valid': False,
            'message': 'This referral code is no longer active'
        }

    return {
        'valid': True,
        'influencer_name': influencer['full_name'],
        'discount_percentage': 50,
        'discount_duration_months': 2,
        'message': f'Valid! You\'ll get 50% off for the first 2 months (referred by {influencer["full_name"]})'
    }
