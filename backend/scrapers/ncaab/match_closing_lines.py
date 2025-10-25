#!/usr/bin/env python3
"""
Match closing lines with actual game results
Handles team name normalization between Odds API and ESPN data
"""

import pandas as pd
import glob
import os
from datetime import datetime

def normalize_team_name(team_name, manual_fixes=None):
    """
    Normalize team names by removing mascots and standardizing format

    Args:
        team_name: Full team name (e.g., "Oregon Ducks" or "St. John's Red Storm")
        manual_fixes: Dictionary of manual name mappings

    Returns:
        Normalized team name (e.g., "oregon" or "st. john's")
    """
    if pd.isna(team_name):
        return ""

    # Check manual fixes first
    if manual_fixes and team_name in manual_fixes:
        return manual_fixes[team_name].lower().strip()

    team = team_name.lower().strip()

    # Remove common mascots and keep school name
    mascots_to_remove = [
        ' aggies', ' anteaters', ' aztecs', ' badgers', ' bears', ' beavers',
        ' bearcats', ' billikens', ' black knights', ' blue demons', ' blue devils',
        ' blue jays', ' bobcats', ' boilermakers', ' bonnies', ' braves', ' broncos',
        ' bruins', ' buckeyes', ' buffalo', ' bulldogs', ' bulls', ' bison',
        ' cardinals', ' catamounts', ' cavaliers', ' chanticleers', ' chippewas',
        ' clippers', ' cougars', ' cowboys', ' crimson', ' crimson tide',
        ' crusaders', ' cyclones', ' demons', ' demon deacons', ' dragons',
        ' dukes', ' ducks', ' eagles', ' explorers', ' falcons', ' flames',
        ' flyers', ' friars', ' gamecocks', ' gators', ' golden bears',
        ' golden eagles', ' golden gophers', ' golden hurricanes', ' grizzlies',
        ' hawkeyes', ' hilltoppers', ' hokies', ' hoosiers', ' hornets', ' huskies',
        ' hurricanes', ' illini', ' jayhawks', ' jaguars', ' knights', ' lobos',
        ' longhorns', ' lumberjacks', ' matadors', ' mean green', ' midshipmen',
        ' minutemen', ' monarchs', ' mountain hawks', ' mountaineers', ' musketeers',
        ' mustangs', ' nittany lions', ' owls', ' panthers', ' peacocks', ' penguins',
        ' phoenix', ' pirates', ' pioneers', ' ragin cajuns', ' ramblers', ' rams',
        ' razorbacks', ' rebels', ' red flash', ' red raiders', ' red storm',
        ' redbirds', ' redhawks', ' retrievers', ' river hawks', ' roadrunners',
        ' rockets', ' running rebels', ' salukis', ' scarlet knights', ' seminoles',
        ' shockers', ' sooners', ' spartans', ' spiders', ' stags', ' sun devils',
        ' tar heels', ' terrapins', ' terriers', ' thundering herd', ' tigers',
        ' titans', ' trojans', ' utes', ' vandals', ' volunteers', ' warriors',
        ' wildcats', ' wolfpack', ' wolverines', ' warhawks', ' rainbow warriors',
        ' miners', ' hilltoppers', ' colonials', ' rams', ' pirates'
    ]

    for mascot in mascots_to_remove:
        if team.endswith(mascot):
            team = team[:-len(mascot)].strip()
            break

    # Additional normalization
    team = team.replace('st.', 'st').replace('st ', 'st')
    team = team.replace('  ', ' ')

    return team.strip()


def match_closing_with_actuals(closing_file, results_file, output_file=None):
    """
    Match closing lines with actual results

    Args:
        closing_file: Path to CSV with closing lines from Odds API
        results_file: Path to CSV with actual game results
        output_file: Optional output path (auto-generated if None)

    Returns:
        DataFrame with matched games
    """
    print("="*70)
    print("MATCHING CLOSING LINES WITH ACTUAL RESULTS")
    print("="*70)

    # Load manual fixes
    import json
    fixes_file = "backend/scrapers/ncaab/team_name_fixes.json"
    manual_fixes = {}
    if os.path.exists(fixes_file):
        with open(fixes_file, 'r') as f:
            manual_fixes = json.load(f)
        print(f"\n Loaded {len(manual_fixes)} manual team name mappings")

    # Load data
    print(f"\n Loading closing lines from: {os.path.basename(closing_file)}")
    closing_df = pd.read_csv(closing_file)
    print(f"   Closing lines: {len(closing_df)} games")

    print(f"\n Loading results from: {os.path.basename(results_file)}")
    results_df = pd.read_csv(results_file)
    print(f"   Results: {len(results_df)} games")

    # Normalize team names with manual fixes
    print("\n Normalizing team names...")
    closing_df['Home_Team_norm'] = closing_df['Home_Team'].apply(lambda x: normalize_team_name(x, manual_fixes))
    closing_df['Away_Team_norm'] = closing_df['Away_Team'].apply(lambda x: normalize_team_name(x, manual_fixes))
    results_df['Home_Team_norm'] = results_df['Home_Team'].apply(normalize_team_name)
    results_df['Away_Team_norm'] = results_df['Away_Team'].apply(normalize_team_name)

    # Show samples
    print("\n Sample normalization:")
    print(f"   Closing: '{closing_df['Home_Team'].iloc[0]}' -> '{closing_df['Home_Team_norm'].iloc[0]}'")
    print(f"   Results: '{results_df['Home_Team'].iloc[0]}' -> '{results_df['Home_Team_norm'].iloc[0]}'")

    # Merge on date and normalized team names
    print("\n Merging datasets...")
    merged = pd.merge(
        closing_df,
        results_df[['Date', 'Home_Team_norm', 'Away_Team_norm', 'Actual_Total']],
        on=['Date', 'Home_Team_norm', 'Away_Team_norm'],
        how='inner'
    )

    print(f"\n Matched {len(merged)} games ({len(merged)/len(results_df)*100:.1f}%)")

    if len(merged) > 0:
        # Calculate deviations
        merged['Deviation'] = merged['Actual_Total'] - merged['Closing_Total']
        merged['Abs_Deviation'] = abs(merged['Deviation'])

        # Drop normalized columns
        merged = merged.drop(columns=['Home_Team_norm', 'Away_Team_norm'])

        # Show statistics
        print("\n DEVIATION STATISTICS:")
        print(f"   Mean: {merged['Deviation'].mean():.2f} pts")
        print(f"   MAE: {merged['Abs_Deviation'].mean():.2f} pts")
        print(f"   Std: {merged['Deviation'].std():.2f} pts")
        print(f"   Min: {merged['Deviation'].min():.1f} pts")
        print(f"   Max: {merged['Deviation'].max():.1f} pts")
        print(f"\n   >10 pts: {(merged['Abs_Deviation'] > 10).sum()} ({(merged['Abs_Deviation'] > 10).sum()/len(merged)*100:.1f}%)")
        print(f"   >20 pts: {(merged['Abs_Deviation'] > 20).sum()} ({(merged['Abs_Deviation'] > 20).sum()/len(merged)*100:.1f}%)")
        print(f"   >30 pts: {(merged['Abs_Deviation'] > 30).sum()} ({(merged['Abs_Deviation'] > 30).sum()/len(merged)*100:.1f}%)")

        # Save
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"backend/data/analysis/real_closing_vs_actual_{timestamp}.csv"

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        merged.to_csv(output_file, index=False)
        print(f"\n Saved: {output_file}")

        return merged
    else:
        print("\nERROR: No matches found")
        print("\nDebugging info:")
        print(f"Sample closing teams: {closing_df['Home_Team_norm'].head(3).tolist()}")
        print(f"Sample results teams: {results_df['Home_Team_norm'].head(3).tolist()}")
        return pd.DataFrame()


def main():
    """Main execution"""
    # Find latest files
    closing_pattern = "backend/data/historical/closing_vs_actual_*.csv"
    closing_files = glob.glob(closing_pattern)

    results_pattern = "backend/data/historical/game_results_*_season_*.csv"
    results_files = glob.glob(results_pattern)

    if not closing_files:
        print("ERROR: No closing lines file found")
        return False

    if not results_files:
        print("ERROR: No game results file found")
        return False

    latest_closing = max(closing_files)
    latest_results = max(results_files)

    # Match
    matched_df = match_closing_with_actuals(latest_closing, latest_results)

    if matched_df is not None and len(matched_df) > 0:
        print("\n" + "="*70)
        print(" SUCCESS!")
        print("="*70)
        print(f"\nReady for regression analysis with REAL closing lines!")
        print(f"Next step: Run complete analysis pipeline")
        return True
    else:
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
