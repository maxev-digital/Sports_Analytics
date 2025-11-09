"""
NHL Goalie Pull Data from Moneypuck Shot Data
Downloads and analyzes 122,472 shots from 2023-24 season
"""

import pandas as pd
import requests
import zipfile
import io
from datetime import datetime

print("=" * 80)
print("MONEYPUCK GOALIE PULL DATA SCRAPER")
print("=" * 80)

# Download the zip file
print("\nDownloading Moneypuck shot data (2023-24 season)...")
url = "https://peter-tanner.com/moneypuck/downloads/shots_2023.zip"

try:
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    # Extract CSV from ZIP
    print("Extracting CSV data...")
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        csv_filename = z.namelist()[0]  # Get first file in zip
        with z.open(csv_filename) as f:
            df = pd.read_csv(f, low_memory=False)

    print(f"Loaded {len(df):,} total shots")

except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

print("\nAnalyzing shot data columns...")
print(f"Total columns: {len(df.columns)}")
print(f"\nFirst few column names:")
for col in df.columns[:20]:
    print(f"  - {col}")

# Check if empty_net column exists
if 'emptyNet' in df.columns or 'empty_net' in df.columns or 'isEmptyNet' in df.columns:
    empty_col = next((c for c in ['emptyNet', 'empty_net', 'isEmptyNet'] if c in df.columns), None)
    print(f"\nFound empty net column: {empty_col}")

    # Filter for empty net shots
    empty_net_shots = df[df[empty_col] == 1]
    print(f"Empty net shots: {len(empty_net_shots):,}")

    # Analyze by team
    if 'team' in df.columns:
        print("\nEmpty net shots by team:")
        print(empty_net_shots['team'].value_counts().head(10))

    # Check what other useful columns we have
    useful_cols = ['game_id', 'date', 'team', 'period', 'time', 'goal',
                   'home_score', 'away_score', 'home_team', 'away_team']
    available = [c for c in useful_cols if c in df.columns or c.lower() in df.columns]
    print(f"\nAvailable useful columns: {available}")

    # Save sample
    sample = empty_net_shots.head(100)
    sample.to_csv('moneypuck_empty_net_sample.csv', index=False)
    print("\nSaved sample to: moneypuck_empty_net_sample.csv")

else:
    print("\nSearching for empty net indicator in columns...")
    empty_cols = [c for c in df.columns if 'empty' in c.lower() or 'net' in c.lower()]
    print(f"Columns with 'empty' or 'net': {empty_cols}")

# Save full column list for inspection
with open('moneypuck_columns.txt', 'w') as f:
    for col in df.columns:
        f.write(f"{col}\n")
print("\nSaved full column list to: moneypuck_columns.txt")

print("\n" + "=" * 80)
print("DATA INSPECTION COMPLETE")
print("=" * 80)
