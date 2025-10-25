#!/usr/bin/env python3
"""Check what dates the games are scheduled for"""

import pandas as pd
from datetime import datetime

# Load latest odds
odds_df = pd.read_csv('backend/data/raw/odds/nba_odds_latest.csv')

# Convert commence_time to datetime
odds_df['game_date'] = pd.to_datetime(odds_df['commence_time'])
odds_df['date_only'] = odds_df['game_date'].dt.date
odds_df['time_only'] = odds_df['game_date'].dt.strftime('%I:%M %p')

# Get unique games with dates
unique_games = odds_df[['game_id', 'home_team', 'away_team', 'date_only', 'time_only']].drop_duplicates()

print("="*70)
print("SCHEDULED NBA GAMES")
print("="*70)

# Group by date
for date in sorted(unique_games['date_only'].unique()):
    games_on_date = unique_games[unique_games['date_only'] == date]
    print(f"\n📅 {date} ({date.strftime('%A')}) - {len(games_on_date)} games")
    print("-"*70)
    
    for _, game in games_on_date.iterrows():
        print(f"  {game['time_only']} - {game['away_team']} @ {game['home_team']}")

print("\n" + "="*70)
print(f"Total: {len(unique_games)} games across {len(unique_games['date_only'].unique())} days")
print("="*70)