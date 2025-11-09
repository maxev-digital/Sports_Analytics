"""
Odds Trigger Lookup Calculator
Calculates minimum acceptable betting odds based on strategy win rate

Formula:
- If win_rate > 50%: American Odds = -100 / (decimal - 1) where decimal = 1 / win_probability
- If win_rate < 50%: American Odds = 100 * (decimal - 1) where decimal = 1 / win_probability
- If win_rate = 50%: American Odds = +100 (even money)
"""

import json
import csv
from pathlib import Path


def calculate_break_even_odds(win_rate_pct: float) -> dict:
    """
    Calculate minimum acceptable odds for a given win rate

    Args:
        win_rate_pct: Win rate as percentage (e.g., 53.4 for 53.4%)

    Returns:
        Dictionary with american_odds, decimal_odds, win_rate
    """
    win_probability = win_rate_pct / 100

    # Calculate fair decimal odds
    decimal_odds = 1 / win_probability

    # Calculate American odds
    if win_probability > 0.50:
        # Favorite (negative odds)
        american_odds = -100 / (decimal_odds - 1)
    elif win_probability < 0.50:
        # Underdog (positive odds)
        american_odds = 100 * (decimal_odds - 1)
    else:
        # Even money
        american_odds = 100

    # Round to nearest 5 (standard sportsbook practice)
    american_odds_rounded = round(american_odds / 5) * 5

    return {
        "win_rate_pct": round(win_rate_pct, 1),
        "win_probability": round(win_probability, 4),
        "decimal_odds": round(decimal_odds, 2),
        "american_odds_exact": round(american_odds, 1),
        "american_odds_rounded": int(american_odds_rounded),
        "min_acceptable_odds": f"{'+' if american_odds_rounded >= 0 else ''}{int(american_odds_rounded)}"
    }


def generate_lookup_table():
    """Generate complete lookup table from 50% to 75% win rate"""

    lookup_data = []

    # Generate for every 0.1% from 50% to 75%
    win_rate = 50.0
    while win_rate <= 75.0:
        odds_data = calculate_break_even_odds(win_rate)
        lookup_data.append(odds_data)
        win_rate += 0.1

    return lookup_data


def save_to_json(data: list, filepath: str):
    """Save lookup table as JSON"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"[OK] Saved JSON: {filepath}")


def save_to_csv(data: list, filepath: str):
    """Save lookup table as CSV"""
    fieldnames = data[0].keys()
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"[OK] Saved CSV: {filepath}")


def create_key_milestones_table():
    """Create a simplified table with key win rate milestones"""
    key_rates = [
        50.0, 51.0, 52.0, 52.5, 53.0, 53.4, 54.0, 55.0,
        56.0, 57.0, 58.0, 59.0, 60.0, 61.0, 62.0, 63.0,
        64.0, 65.0, 66.0, 67.0, 68.0, 69.0, 70.0, 75.0
    ]

    return [calculate_break_even_odds(rate) for rate in key_rates]


def main():
    """Generate all lookup files"""
    print("=" * 80)
    print("ODDS TRIGGER LOOKUP TABLE GENERATOR")
    print("=" * 80)
    print("\nCalculating break-even odds for win rates 50.0% to 75.0%...\n")

    # Generate complete lookup table (every 0.1%)
    full_data = generate_lookup_table()

    # Generate key milestones table
    key_data = create_key_milestones_table()

    # Save complete data
    save_to_json(full_data, "data/odds_trigger_full_lookup.json")
    save_to_csv(full_data, "data/odds_trigger_full_lookup.csv")

    # Save key milestones
    save_to_json(key_data, "data/odds_trigger_key_milestones.json")
    save_to_csv(key_data, "data/odds_trigger_key_milestones.csv")

    print(f"\n[OK] Generated {len(full_data)} complete entries")
    print(f"[OK] Generated {len(key_data)} key milestone entries")

    # Print sample output
    print("\n" + "=" * 80)
    print("SAMPLE OUTPUT (Key Milestones):")
    print("=" * 80)
    print(f"\n{'Win Rate':<12} {'Probability':<14} {'Decimal':<10} {'American':<12} {'Min Accept'}")
    print("-" * 80)

    for entry in key_data[:15]:  # Show first 15
        print(f"{entry['win_rate_pct']:<11}% {entry['win_probability']:<14} {entry['decimal_odds']:<10} "
              f"{entry['american_odds_exact']:<12.1f} {entry['min_acceptable_odds']}")

    print("\n" + "=" * 80)
    print("FILES CREATED:")
    print("=" * 80)
    print("1. data/odds_trigger_full_lookup.json    - Complete table (every 0.1%)")
    print("2. data/odds_trigger_full_lookup.csv     - Complete table (CSV format)")
    print("3. data/odds_trigger_key_milestones.json - Key win rates only")
    print("4. data/odds_trigger_key_milestones.csv  - Key win rates (CSV format)")
    print("=" * 80)


if __name__ == "__main__":
    main()
