#!/usr/bin/env python3
"""
Diagnose Team Name Mismatches
Identifies which teams from game results aren't found in KenPom data
"""

import pandas as pd
import glob

print("="*70)
print("TEAM NAME MISMATCH DIAGNOSTIC")
print("="*70)

# Load your historical files
kenpom_pattern = "backend/data/historical/kenpom_*_season_*.csv"
games_pattern = "backend/data/historical/game_results_*_season_*.csv"

kenpom_files = glob.glob(kenpom_pattern)
games_files = glob.glob(games_pattern)

if not kenpom_files:
    print("❌ No KenPom files found")
    exit(1)

if not games_files:
    print("❌ No game result files found")  
    exit(1)

# Use the latest files
kenpom_file = max(kenpom_files)
games_file = max(games_files)

print(f"\n📊 Data Loaded:")
print(f"   KenPom file: {kenpom_file}")
print(f"   Games file: {games_file}")

# Load data
try:
    kenpom = pd.read_csv(kenpom_file)
    games = pd.read_csv(games_file)
    
    print(f"   KenPom teams: {len(kenpom)}")
    print(f"   Games: {len(games)}")
    
except Exception as e:
    print(f"❌ Error loading data: {str(e)}")
    exit(1)

# Get unique team names from each source
kenpom_teams = set(kenpom['Team'].str.strip())
game_home_teams = set(games['Home_Team'].str.strip())
game_away_teams = set(games['Away_Team'].str.strip())
game_teams = game_home_teams.union(game_away_teams)

print(f"\n   Unique teams in games: {len(game_teams)}")
print(f"   Unique teams in KenPom: {len(kenpom_teams)}")

# Find teams in games but not in KenPom
missing_teams = game_teams - kenpom_teams

print(f"\n❌ TEAMS IN GAMES BUT NOT IN KENPOM: {len(missing_teams)}")
print("-"*70)

# Count how many games each missing team appears in
missing_counts = {}
for team in missing_teams:
    home_count = (games['Home_Team'] == team).sum()
    away_count = (games['Away_Team'] == team).sum()
    total = home_count + away_count
    missing_counts[team] = total

# Sort by frequency
sorted_missing = sorted(missing_counts.items(), key=lambda x: x[1], reverse=True)

print("\nTop 30 most frequent missing teams:")
print(f"{'Team Name (in Games)':<40} {'# of Games':<10} {'Possible KenPom Match'}")
print("-"*90)

for team, count in sorted_missing[:30]:
    # Try to find similar KenPom team
    possible_matches = []
    for kp_team in kenpom_teams:
        # Check if any word from game team appears in KenPom team
        game_words = set(team.lower().split())
        kp_words = set(kp_team.lower().split())
        
        # If there's word overlap, it might be a match
        if game_words.intersection(kp_words):
            possible_matches.append(kp_team)
    
    match_str = possible_matches[0] if possible_matches else "NOT FOUND"
    if len(possible_matches) > 1:
        match_str += f" (+{len(possible_matches)-1} more)"
        
    print(f"{team:<40} {count:<10} {match_str}")

# Calculate impact
total_games = len(games)
games_with_missing = 0

for _, game in games.iterrows():
    if game['Home_Team'] in missing_teams or game['Away_Team'] in missing_teams:
        games_with_missing += 1

pct_affected = (games_with_missing / total_games) * 100

print(f"\n📊 IMPACT ANALYSIS:")
print(f"   Total games: {total_games:,}")
print(f"   Games with missing teams: {games_with_missing:,}")
print(f"   Percentage affected: {pct_affected:.1f}%")

print(f"\n💡 SOLUTIONS:")
print(f"   1. Create team name mapping in totals_predictor.py")
print(f"   2. Map game result names → KenPom names")
print(f"   3. This should reduce failed predictions from {pct_affected:.1f}% to <10%")

# Show some examples of potential mappings
print(f"\n🔧 EXAMPLE MAPPINGS NEEDED:")
print("# Add these to totals_predictor.py:")
print("TEAM_NAME_MAP = {")
for team, count in sorted_missing[:10]:
    possible_matches = []
    for kp_team in kenpom_teams:
        game_words = set(team.lower().split())
        kp_words = set(kp_team.lower().split())
        if game_words.intersection(kp_words):
            possible_matches.append(kp_team)
    
    if possible_matches:
        print(f"    '{team}': '{possible_matches[0]}',")
    else:
        print(f"    '{team}': 'NEED_TO_FIND_MATCH',")

print("}")
