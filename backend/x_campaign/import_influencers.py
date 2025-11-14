"""
Import Influencers from CSV
Loads influencer list into campaign database
CSV format: handle, followers, niche, why_target, engagement_rate
"""
import csv
import sys
from pathlib import Path

# Handle both direct execution and module import
try:
    from .db_setup import add_partner, print_stats
except ImportError:
    # Add parent directory to path for direct execution
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from x_campaign.db_setup import add_partner, print_stats

def import_from_csv(csv_path):
    """
    Import influencers from CSV file

    CSV Format:
        handle, followers, niche, why_target, engagement_rate

    Example:
        @BenMoore_Sports, 50000, nba, High NBA engagement, 4.5
        @SharpBettor, 30000, betting, Sharp betting content, 3.8
    """
    csv_path = Path(csv_path)

    if not csv_path.exists():
        print(f"[ERROR] File not found: {csv_path}")
        return

    print(f"\nImporting influencers from {csv_path.name}")
    print("="*60)

    imported = 0
    skipped = 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            handle = row['handle'].strip()
            followers = int(row['followers'])
            niche = row['niche'].strip()
            why_target = row['why_target'].strip()
            engagement_rate = float(row.get('engagement_rate', 0)) if row.get('engagement_rate') else None

            result = add_partner(
                handle=handle,
                followers=followers,
                niche=niche,
                why_target=why_target,
                engagement_rate=engagement_rate
            )

            if result:
                imported += 1
            else:
                skipped += 1

    print()
    print("="*60)
    print(f"Import Complete")
    print(f"Imported: {imported}")
    print(f"Skipped (duplicates): {skipped}")
    print("="*60)

    print_stats()

def create_sample_csv(output_path='influencers_sample.csv'):
    """Create a sample CSV file for testing"""
    sample_data = [
        {
            'handle': '@BenMoore_Sports',
            'followers': 50000,
            'niche': 'nba',
            'why_target': 'High NBA engagement, verified account',
            'engagement_rate': 4.5
        },
        {
            'handle': '@SharpBettor',
            'followers': 30000,
            'niche': 'betting',
            'why_target': 'Sharp betting content, active community',
            'engagement_rate': 3.8
        },
        {
            'handle': '@NBAPicks247',
            'followers': 75000,
            'niche': 'nba',
            'why_target': 'Daily NBA picks, large following',
            'engagement_rate': 5.2
        },
        {
            'handle': '@BettingWithAustin',
            'followers': 40000,
            'niche': 'sports_betting',
            'why_target': 'Multi-sport analyst, engaged audience',
            'engagement_rate': 4.1
        },
        {
            'handle': '@ActionNetworkHQ',
            'followers': 200000,
            'niche': 'sports_betting',
            'why_target': 'Major betting media outlet',
            'engagement_rate': 6.5
        },
    ]

    output_path = Path(output_path)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['handle', 'followers', 'niche', 'why_target', 'engagement_rate']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(sample_data)

    print(f"[OK] Created sample CSV: {output_path}")
    return output_path

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        import_from_csv(csv_file)
    else:
        print("Usage: python import_influencers.py <csv_file>")
        print()
        print("Creating sample CSV for testing...")
        sample_file = create_sample_csv()
        print()
        print("To import, run:")
        print(f"  python -m backend.x_campaign.import_influencers {sample_file}")
