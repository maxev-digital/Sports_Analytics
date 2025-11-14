"""
Referral Code Generator
Creates unique referral codes for partner program
Format: LASTNAME_abc12 (e.g., MOORE_xy3z9)
"""
import random
import string
import json
from pathlib import Path

# Characters for random suffix (5 chars: letters + numbers)
CHARS = string.ascii_lowercase + string.digits

def generate_code(handle):
    """
    Generate referral code from X handle
    Format: LASTNAME_abc12

    Examples:
        @BenMoore_Sports → MOORE_xy3z9
        @SharpBettor → SHARP_a1b2c
        @NBAPicks247 → NBA247_kl4mn
    """
    # Extract base from handle
    clean_handle = handle.replace('@', '').replace('_', '').replace('-', '')

    # Try to extract a reasonable base (6-8 chars)
    if len(clean_handle) >= 8:
        # Take last word or segment
        base = clean_handle[-8:].upper()
    else:
        base = clean_handle.upper()

    # Generate random 5-char suffix
    suffix = ''.join(random.choices(CHARS, k=5))

    return f"{base}_{suffix}"

def generate_unique_code(handle, existing_codes):
    """Generate a code that doesn't conflict with existing codes"""
    max_attempts = 10

    for _ in range(max_attempts):
        code = generate_code(handle)
        if code not in existing_codes:
            return code

    # If still colliding after 10 attempts, add extra random chars
    base = handle.replace('@', '').replace('_', '')[:6].upper()
    suffix = ''.join(random.choices(CHARS, k=8))
    return f"{base}_{suffix}"

def load_existing_codes():
    """Load existing referral codes from referrals.json"""
    referrals_path = Path(__file__).parent.parent / 'referrals.json'

    if referrals_path.exists():
        with open(referrals_path, 'r') as f:
            referrals = json.load(f)
            return {data['referral_code'] for data in referrals.values()}

    return set()

def create_partner_code(handle):
    """
    Create a new partner code and ensure uniqueness
    Returns: (code, is_unique)
    """
    existing_codes = load_existing_codes()
    code = generate_unique_code(handle, existing_codes)

    return code

def bulk_generate_codes(handles):
    """Generate codes for multiple handles"""
    existing_codes = load_existing_codes()
    results = []

    for handle in handles:
        code = generate_unique_code(handle, existing_codes)
        existing_codes.add(code)  # Prevent duplicates in this batch
        results.append({
            'handle': handle,
            'code': code
        })

    return results

# Test cases
if __name__ == "__main__":
    print("Referral Code Generator")
    print("=" * 50)

    test_handles = [
        "@BenMoore_Sports",
        "@SharpBettor",
        "@NBAPicks247",
        "@BettingWithAustin",
        "@ActionNetworkHQ",
        "@OddsChecker",
        "@BetMGM",
        "@TheSharpSide",
    ]

    print("\nGenerating test codes...")
    print()

    codes = bulk_generate_codes(test_handles)

    for result in codes:
        print(f"{result['handle']:25} -> {result['code']}")

    print()
    print("[OK] All codes generated successfully")
    print(f"Total codes: {len(codes)}")

    # Check for uniqueness
    code_values = [c['code'] for c in codes]
    unique_codes = set(code_values)

    if len(code_values) == len(unique_codes):
        print("[OK] All codes are unique")
    else:
        print("[WARN] Duplicate codes detected!")
