#!/usr/bin/env python3
"""
Match Closing Lines with Sports-Reference Data
Uses improved team name mappings for maximum match rate
"""

import pandas as pd
import json
from datetime import datetime, timedelta
import os

def match_with_sports_reference():
    """Match closing lines with Sports-Reference game results"""

    print("="*70)
    print("MATCHING CLOSING LINES WITH SPORTS-REFERENCE")
    print("="*70)

    # Load data
    closing_file = "backend/data/historical/closing_vs_actual_2024_20251011_104312.csv"
    sports_ref_file = "backend/data/historical/sports_ref_targeted_20251011_114658.csv"
    mapping_file = "backend/data/team_name_mapping_complete.json"

    print(f"\nLoading datasets...")
    closing_df = pd.read_csv(closing_file)
    sports_ref_df = pd.read_csv(sports_ref_file)

    with open(mapping_file, 'r') as f:
        team_mapping = json.load(f)

    print(f"   Closing lines: {len(closing_df)} games")
    print(f"   Sports-Reference: {len(sports_ref_df)} games")
    print(f"   Team mappings: {len(team_mapping)} teams")

    # Apply mappings to closing data
    def map_team(team_name):
        if team_name in team_mapping and team_mapping[team_name]:
            return team_mapping[team_name].lower().strip()
        return None

    closing_df['Home_mapped'] = closing_df['Home_Team'].apply(map_team)
    closing_df['Away_mapped'] = closing_df['Away_Team'].apply(map_team)

    # Normalize Sports-Reference teams
    sports_ref_df['Home_norm'] = sports_ref_df['Home_Team'].str.lower().str.strip()
    sports_ref_df['Away_norm'] = sports_ref_df['Away_Team'].str.lower().str.strip()

    # Convert dates
    closing_df['Date_dt'] = pd.to_datetime(closing_df['Date'])
    sports_ref_df['Date_dt'] = pd.to_datetime(sports_ref_df['Date'])

    print(f"\nMatching with flexible date tolerance...")

    matches = []
    unmatched_odds = []
    unmatched_ref = []

    for _, c_row in closing_df.iterrows():
        if pd.isna(c_row['Home_mapped']) or pd.isna(c_row['Away_mapped']):
            continue

        c_date = c_row['Date_dt']
        c_home = c_row['Home_mapped']
        c_away = c_row['Away_mapped']

        matched = False
        for days_offset in [0, -1, 1]:
            target_date = c_date + timedelta(days=days_offset)

            match = sports_ref_df[
                (sports_ref_df['Date_dt'] == target_date) &
                (sports_ref_df['Home_norm'] == c_home) &
                (sports_ref_df['Away_norm'] == c_away)
            ]

            if len(match) > 0:
                match_row = match.iloc[0]
                matches.append({
                    'Date': c_row['Date'],
                    'Home_Team': c_row['Home_Team'],
                    'Away_Team': c_row['Away_Team'],
                    'Closing_Total': c_row['Closing_Total'],
                    'Num_Books': c_row['Num_Books'],
                    'Actual_Total': match_row['Actual_Total'],
                    'Deviation': match_row['Actual_Total'] - c_row['Closing_Total'],
                    'Abs_Deviation': abs(match_row['Actual_Total'] - c_row['Closing_Total'])
                })
                matched = True
                break

        if not matched:
            unmatched_odds.append(c_row)

    matched_df = pd.DataFrame(matches)

    print(f"\n MATCHED: {len(matched_df)} games")
    print(f" Match rate: {len(matched_df)/len(closing_df)*100:.1f}% of closing lines")
    print(f" Improvement from ESPN: {len(matched_df)/396*100:.0f}% increase")

    # Statistics
    print(f"\n CLOSING LINE ACCURACY:")
    print(f"   Mean Deviation: {matched_df['Deviation'].mean():.2f} pts")
    print(f"   MAE: {matched_df['Abs_Deviation'].mean():.2f} pts")
    print(f"   Std Dev: {matched_df['Deviation'].std():.2f} pts")
    print(f"   Range: {matched_df['Deviation'].min():.1f} to {matched_df['Deviation'].max():.1f} pts")

    # Distribution
    print(f"\n ACCURACY DISTRIBUTION:")
    for threshold in [5, 10, 15, 20, 25, 30]:
        within = (matched_df['Abs_Deviation'] <= threshold).sum()
        pct = within / len(matched_df) * 100
        print(f"   Within {threshold} pts: {within} ({pct:.1f}%)")

    print(f"\n GAMES EXCEEDING THRESHOLDS:")
    for threshold in [5, 10, 15, 20, 25, 30]:
        over = (matched_df['Abs_Deviation'] > threshold).sum()
        pct = over / len(matched_df) * 100
        print(f"   >{threshold} pts: {over} ({pct:.1f}%)")

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"backend/data/analysis/final_matched_games_{timestamp}.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    matched_df.to_csv(output_file, index=False)

    print(f"\n Saved: {output_file}")
    print("="*70)

    return matched_df, output_file


if __name__ == "__main__":
    import sys
    df, output_file = match_with_sports_reference()
    sys.exit(0 if df is not None and len(df) > 0 else 1)
