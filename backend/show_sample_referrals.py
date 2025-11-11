"""Show sample referrals with realistic names"""
import json
import random

refs = json.load(open('referrals.json'))
print("Sample of 20 referrals with realistic names:\n")
print(f"{'#':<4} {'Name':<25} {'Username':<35} {'Tier':<15} {'Commission':<12} {'Status':<10}")
print("=" * 110)

samples = random.sample(list(refs.items()), min(20, len(refs)))
for i, (username, r) in enumerate(samples, 1):
    name = r.get('full_name', 'Unknown')
    tier = r['subscription_tier'].capitalize()
    commission = f"${r['monthly_commission']:.2f}/mo"
    status = r['status'].capitalize()
    print(f"{i:<4} {name:<25} {username:<35} {tier:<15} {commission:<12} {status:<10}")
