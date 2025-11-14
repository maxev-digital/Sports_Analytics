"""
Update partner commission rates from 50% to 25%
Updates all referrals.json commission amounts
"""

import json

# Correct commission rates (25%)
COMMISSION_RATES = {
    'starter': 7.25,    # 25% of $29
    'semipro': 19.75,   # 25% of $79
    'professional': 37.25,  # 25% of $149
    'elite': 74.75,     # 25% of $299
    'elitepro': 199.75,  # 25% of $799
    'beta': 2.00        # 25% of $8 (or whatever beta price is)
}

def update_referrals():
    """Update all referral commissions to 25%"""

    try:
        with open('referrals.json', 'r') as f:
            referrals = json.load(f)

        updated_count = 0

        for username, referral in referrals.items():
            tier = referral.get('subscription_tier', '').lower()

            # Map tier names to keys
            tier_key = tier
            if tier == 'semi-pro' or tier == 'semi pro':
                tier_key = 'semipro'
            elif tier == 'elite pro' or tier == 'elite-pro':
                tier_key = 'elitepro'

            # Update commission if tier found
            if tier_key in COMMISSION_RATES:
                old_commission = referral.get('monthly_commission', 0)
                new_commission = COMMISSION_RATES[tier_key]

                if old_commission != new_commission:
                    referral['monthly_commission'] = new_commission
                    updated_count += 1
                    print(f"Updated {username}: {tier} ${old_commission} -> ${new_commission}")

        # Save updated referrals
        with open('referrals.json', 'w') as f:
            json.dump(referrals, f, indent=2)

        print(f"\n[OK] Updated {updated_count} referrals")

        # Calculate new total commissions
        total_monthly = sum(r['monthly_commission'] for r in referrals.values() if r.get('status') == 'active')
        total_annual = total_monthly * 12

        print(f"\n[SUMMARY] New Commission Summary:")
        print(f"   Monthly: ${total_monthly:,.2f}")
        print(f"   Annual: ${total_annual:,.2f}")

    except FileNotFoundError:
        print("[ERROR] Error: referrals.json not found")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

if __name__ == "__main__":
    update_referrals()
