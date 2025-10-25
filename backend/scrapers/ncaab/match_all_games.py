#!/usr/bin/env python3
"""
Comprehensive Matching with Expanded Team Mappings
Goal: Match ~2000 games from Odds API with ESPN results
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta

def match_all_games():
    """Match closing lines with results using expanded mappings"""
    print("="*70)
    print("COMPREHENSIVE GAME MATCHING - EXPANDED MAPPINGS")
    print("="*70)

    # Load expanded mapping
    mapping_file = "backend/data/team_name_mapping_complete.json"
    print(f"\nLoading team mappings...")
    with open(mapping_file, 'r') as f:
        team_mapping = json.load(f)
    print(f"   Loaded {len(team_mapping)} team mappings")

    # Load datasets
    closing_file = "backend/data/historical/closing_vs_actual_2024_20251011_104312.csv"
    results_file = "backend/data/historical/game_results_2024_season_20251010_125603.csv"

    print(f"\nLoading datasets...")
    closing_df = pd.read_csv(closing_file)
    results_df = pd.read_csv(results_file)
    print(f"   Closing lines: {len(closing_df)} games")
    print(f"   Game results: {len(results_df)} games")

    # Apply mapping to closing data
    print(f"\nApplying team name mappings...")

    def map_team(team_name):
        if team_name in team_mapping and team_mapping[team_name]:
            return team_mapping[team_name].lower().strip()
        return None

    closing_df['Home_Team_mapped'] = closing_df['Home_Team'].apply(map_team)
    closing_df['Away_Team_mapped'] = closing_df['Away_Team'].apply(map_team)

    # Remove unmapped games
    closing_df = closing_df[
        closing_df['Home_Team_mapped'].notna() &
        closing_df['Away_Team_mapped'].notna()
    ].copy()
    print(f"   Games with valid mappings: {len(closing_df)}")

    # Normalize results teams
    results_df['Home_Team_norm'] = results_df['Home_Team'].str.lower().str.strip()
    results_df['Away_Team_norm'] = results_df['Away_Team'].str.lower().str.strip()

    # Convert dates
    closing_df['Date_dt'] = pd.to_datetime(closing_df['Date'])
    results_df['Date_dt'] = pd.to_datetime(results_df['Date'])

    print(f"\nMatching with flexible date tolerance (+/-1 day)...")

    # Flexible date matching
    matches = []
    for _, c_row in closing_df.iterrows():
        c_date = c_row['Date_dt']
        c_home = c_row['Home_Team_mapped']
        c_away = c_row['Away_Team_mapped']

        # Try exact date and +/- 1 day
        for days_offset in [0, -1, 1]:
            target_date = c_date + timedelta(days=days_offset)

            match = results_df[
                (results_df['Date_dt'] == target_date) &
                (results_df['Home_Team_norm'] == c_home) &
                (results_df['Away_Team_norm'] == c_away)
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
                    'Result_Date': match_row['Date'],
                    'Days_Diff': days_offset
                })
                break

    # Create matched DataFrame
    matched_df = pd.DataFrame(matches)

    if len(matched_df) == 0:
        print("\nERROR: No matches found")
        return None

    # Calculate deviations
    matched_df['Deviation'] = matched_df['Actual_Total'] - matched_df['Closing_Total']
    matched_df['Abs_Deviation'] = abs(matched_df['Deviation'])

    print(f"\n MATCHED: {len(matched_df)} games ({len(matched_df)/len(results_df)*100:.1f}% of results)")
    print(f"   Improvement: {len(matched_df)/215*100:.0f}% increase from 215 baseline")

    # Statistics
    print(f"\n CLOSING LINE ACCURACY STATISTICS:")
    print(f"   Mean Deviation: {matched_df['Deviation'].mean():.2f} pts")
    print(f"   MAE: {matched_df['Abs_Deviation'].mean():.2f} pts")
    print(f"   Std Dev: {matched_df['Deviation'].std():.2f} pts")
    print(f"   Min: {matched_df['Deviation'].min():.1f} pts")
    print(f"   Max: {matched_df['Deviation'].max():.1f} pts")

    # Distribution
    print(f"\n ACCURACY DISTRIBUTION:")
    for threshold in [5, 10, 15, 20, 25, 30]:
        count = (matched_df['Abs_Deviation'] <= threshold).sum()
        pct = count / len(matched_df) * 100
        print(f"   Within {threshold} pts: {count} games ({pct:.1f}%)")

    print(f"\n GAMES EXCEEDING THRESHOLDS:")
    for threshold in [5, 10, 15, 20, 25, 30]:
        count = (matched_df['Abs_Deviation'] > threshold).sum()
        pct = count / len(matched_df) * 100
        print(f"   >{threshold} pts: {count} games ({pct:.1f}%)")

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"backend/data/analysis/all_matched_games_{timestamp}.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    matched_df.to_csv(output_file, index=False)

    print(f"\n Saved: {output_file}")
    print(f"\n SUCCESS! Ready for Google Sheets upload")
    print("="*70)

    return matched_df, output_file


if __name__ == "__main__":
    import sys
    matched_df, output_file = match_all_games()
    sys.exit(0 if matched_df is not None else 1)
