"""
Import Moneypuck Goalie Pull Data into ML Database
Replaces old incorrect NHL API data with verified Moneypuck statistics
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MONEYPUCK_CSV = os.path.join(BASE_DIR, 'strategies', 'moneypuck_goalie_pulls_2023_2024_FINAL.csv')
TIMING_CSV = os.path.join(BASE_DIR, 'strategies', 'goalie_pull_timing_by_team.csv')
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'goalie_pulls.db')

print("=" * 80)
print("IMPORTING MONEYPUCK DATA INTO ML DATABASE")
print("=" * 80)

# Load CSV files
print("\n[1/5] Loading Moneypuck CSV files...")
df_pulls = pd.read_csv(MONEYPUCK_CSV)
df_timing = pd.read_csv(TIMING_CSV)

print(f"  - Loaded {len(df_pulls)} goalie pull events")
print(f"  - Loaded {len(df_timing)} timing records")

# Merge timing data with pull data
print("\n[2/5] Merging timing data...")
df_merged = df_pulls.merge(
    df_timing[['game_id', 'pulling_team', 'seconds_remaining', 'time_remaining']],
    left_on=['game_id', 'pulling_team'],
    right_on=['game_id', 'pulling_team'],
    how='left'
)

print(f"  - Merged {len(df_merged)} records with timing data")

# Connect to database
print("\n[3/5] Connecting to database...")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Clear old data
print("\n[4/5] Clearing old incorrect data...")
cursor.execute('SELECT COUNT(*) FROM goalie_pulls')
old_count = cursor.fetchone()[0]
print(f"  - Found {old_count} old records")

cursor.execute('DELETE FROM goalie_pulls')
cursor.execute('DELETE FROM team_pull_stats')
conn.commit()
print(f"  - Deleted {old_count} old records")

# Import new data
print("\n[5/5] Importing Moneypuck data...")

imported = 0
skipped = 0

for idx, row in df_merged.iterrows():
    # RECALCULATE success correctly (CSV has buggy data)
    # Success = net goals gained >= deficit to overcome
    net_goals_gained = row['goals_by_pulling_team'] - row['goals_by_opponent']
    deficit_to_overcome = abs(row['score_differential'])

    actually_tied_or_won = net_goals_gained >= deficit_to_overcome

    # Determine who scored
    if row['outcome'] == 'pulling_team_scored':
        goal_scored_by = 'pulling_team'
    elif row['outcome'] == 'opponent_scored':
        goal_scored_by = 'opponent'
    elif row['outcome'] == 'both_scored':
        goal_scored_by = 'both'
    else:
        goal_scored_by = 'none'

    # Map to result field (database expects 'goal_for' for success)
    if actually_tied_or_won:
        result = 'goal_for'  # Team tied or won (success)
        final_outcome = 'tied_or_won'
    else:
        result = 'goal_against' if goal_scored_by == 'opponent' else 'no_result'
        final_outcome = 'lost'

    # Prepare event data
    event = {
        'game_id': str(row['game_id']),
        'team': row['pulling_team'],
        'period': int(row['period']),
        'time_remaining': row.get('time_remaining', '00:00'),
        'time_remaining_seconds': int(row.get('seconds_remaining', 0)) if pd.notna(row.get('seconds_remaining')) else 0,
        'score_differential': int(row['score_differential']),
        'home_score': None,  # Not in CSV
        'away_score': None,  # Not in CSV
        'opponent': None,  # Not in CSV
        'home_game': None,  # Not in CSV
        'division_game': None,
        'playoff_game': False,  # Moneypuck is regular season
        'season': '20232024',
        'game_date': '2023-10-10',  # Default date (season start)
        'pull_timestamp': None,
        'goalie_name': None,
        'result': result,
        'goal_scored_by': goal_scored_by,
        'time_to_goal_seconds': None,
        'final_outcome': final_outcome,
        'coach': None
    }

    try:
        cursor.execute('''
            INSERT INTO goalie_pulls (
                game_id, team, coach, period, time_remaining, time_remaining_seconds,
                score_differential, home_score, away_score, opponent, home_game,
                division_game, playoff_game, season, game_date, pull_timestamp,
                goalie_name, result, goal_scored_by, time_to_goal_seconds, final_outcome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event['game_id'],
            event['team'],
            event['coach'],
            event['period'],
            event['time_remaining'],
            event['time_remaining_seconds'],
            event['score_differential'],
            event['home_score'],
            event['away_score'],
            event['opponent'],
            event['home_game'],
            event['division_game'],
            event['playoff_game'],
            event['season'],
            event['game_date'],
            event['pull_timestamp'],
            event['goalie_name'],
            event['result'],
            event['goal_scored_by'],
            event['time_to_goal_seconds'],
            event['final_outcome']
        ))
        imported += 1

        if (imported % 100) == 0:
            print(f"  - Imported {imported}/{len(df_merged)} records...")

    except sqlite3.IntegrityError:
        skipped += 1

conn.commit()
conn.close()

print(f"\n  - Successfully imported {imported} records")
print(f"  - Skipped {skipped} duplicates")

# Verify import
print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM goalie_pulls')
total = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM goalie_pulls WHERE final_outcome = "tied_or_won"')
success_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(DISTINCT team) FROM goalie_pulls')
team_count = cursor.fetchone()[0]

cursor.execute('''
    SELECT score_differential, COUNT(*)
    FROM goalie_pulls
    GROUP BY score_differential
    ORDER BY score_differential
''')
score_diffs = cursor.fetchall()

conn.close()

print(f"\nTotal records in database: {total}")
print(f"Unique teams: {team_count}")
print(f"Success rate: {success_count}/{total} ({success_count/total*100:.1f}%)")

print(f"\nScore differential breakdown:")
for diff, count in score_diffs:
    print(f"  Down by {abs(diff)}: {count} pulls")

print("\n" + "=" * 80)
print("IMPORT COMPLETE!")
print("=" * 80)
print("\nNext step: Test ML predictor with new data")
print("Run: python backend/ml/models/goalie_pull_predictor.py")
