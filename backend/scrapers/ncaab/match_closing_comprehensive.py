#!/usr/bin/env python3
"""
Comprehensive Closing Line Matching
Uses complete team name mapping for maximum match rate
"""

import pandas as pd
import json
import os
from datetime import datetime

def match_with_complete_mapping():
    """Match closing lines with actual results using complete mapping"""
    print("="*70)
    print("COMPREHENSIVE CLOSING LINE MATCHING")
    print("="*70)

    # Load complete mapping
    mapping_file = "backend/data/team_name_mapping_complete.json"
    print(f"\n Loading complete team mapping...")
    with open(mapping_file, 'r') as f:
        team_mapping = json.load(f)
    print(f"   Loaded {len(team_mapping)} team mappings")

    # Load datasets
    closing_file = "backend/data/historical/closing_vs_actual_2024_20251011_104312.csv"
    results_file = "backend/data/historical/game_results_2024_season_20251010_125603.csv"

    print(f"\n Loading closing lines...")
    closing_df = pd.read_csv(closing_file)
    print(f"   {len(closing_df)} games from Odds API")

    print(f"\n Loading game results...")
    results_df = pd.read_csv(results_file)
    print(f"   {len(results_df)} games from ESPN")

    # Apply mapping to closing data
    print(f"\n Applying team name mappings...")

    def map_team(team_name):
        if team_name in team_mapping and team_mapping[team_name]:
            return team_mapping[team_name].lower().strip()
        return None

    closing_df['Home_Team_mapped'] = closing_df['Home_Team'].apply(map_team)
    closing_df['Away_Team_mapped'] = closing_df['Away_Team'].apply(map_team)

    # Normalize results teams
    results_df['Home_Team_norm'] = results_df['Home_Team'].str.lower().str.strip()
    results_df['Away_Team_norm'] = results_df['Away_Team'].str.lower().str.strip()

    # Remove unmapped games
    closing_df = closing_df[
        closing_df['Home_Team_mapped'].notna() &
        closing_df['Away_Team_mapped'].notna()
    ]
    print(f"   {len(closing_df)} games with valid mappings")

    # Merge on date and mapped teams
    print(f"\n Merging datasets...")
    merged = pd.merge(
        closing_df,
        results_df[['Date', 'Home_Team_norm', 'Away_Team_norm', 'Actual_Total']],
        left_on=['Date', 'Home_Team_mapped', 'Away_Team_mapped'],
        right_on=['Date', 'Home_Team_norm', 'Away_Team_norm'],
        how='inner'
    )

    # Clean up
    merged = merged.drop(columns=['Home_Team_mapped', 'Away_Team_mapped',
                                   'Home_Team_norm', 'Away_Team_norm'])

    print(f"\n MATCHED: {len(merged)} games ({len(merged)/len(results_df)*100:.1f}%)")

    if len(merged) > 0:
        # Calculate statistics
        merged['Deviation'] = merged['Actual_Total'] - merged['Closing_Total']
        merged['Abs_Deviation'] = abs(merged['Deviation'])

        print(f"\n DEVIATION STATISTICS:")
        print(f"   Mean: {merged['Deviation'].mean():.2f} pts")
        print(f"   MAE: {merged['Abs_Deviation'].mean():.2f} pts")
        print(f"   Std: {merged['Deviation'].std():.2f} pts")
        print(f"   Min: {merged['Deviation'].min():.1f} pts")
        print(f"   Max: {merged['Deviation'].max():.1f} pts")
        print(f"\n   >5 pts: {(merged['Abs_Deviation'] > 5).sum()} ({(merged['Abs_Deviation'] > 5).sum()/len(merged)*100:.1f}%)")
        print(f"   >10 pts: {(merged['Abs_Deviation'] > 10).sum()} ({(merged['Abs_Deviation'] > 10).sum()/len(merged)*100:.1f}%)")
        print(f"   >15 pts: {(merged['Abs_Deviation'] > 15).sum()} ({(merged['Abs_Deviation'] > 15).sum()/len(merged)*100:.1f}%)")
        print(f"   >20 pts: {(merged['Abs_Deviation'] > 20).sum()} ({(merged['Abs_Deviation'] > 20).sum()/len(merged)*100:.1f}%)")
        print(f"   >25 pts: {(merged['Abs_Deviation'] > 25).sum()} ({(merged['Abs_Deviation'] > 25).sum()/len(merged)*100:.1f}%)")
        print(f"   >30 pts: {(merged['Abs_Deviation'] > 30).sum()} ({(merged['Abs_Deviation'] > 30).sum()/len(merged)*100:.1f}%)")

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"backend/data/analysis/comprehensive_closing_vs_actual_{timestamp}.csv"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        merged.to_csv(output_file, index=False)

        print(f"\n Saved: {output_file}")
        print(f"\n SUCCESS! Ready for full regression analysis with {len(merged)} games")

        return merged, output_file
    else:
        print("\nERROR: No matches found")
        return None, None


if __name__ == "__main__":
    import sys
    matched_df, output_file = match_with_complete_mapping()
    sys.exit(0 if matched_df is not None else 1)
