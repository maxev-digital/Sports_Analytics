"""
Import NHL Goalie Pull data from CSV into database
"""

import pandas as pd
import sys
import os
from datetime import datetime

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ml.data_collection.goalie_pull_database import GoaliePullDatabase


def import_csv_to_database(csv_path: str):
    """
    Import goalie pull data from CSV file into database

    CSV columns:
    - game_id
    - date
    - team
    - period
    - estimated_pull_time
    - time_remaining_seconds
    - score_differential
    - trailing_goals
    - outcome
    - empty_net_goal_time
    """

    print(f"Loading CSV from: {csv_path}")
    df = pd.read_csv(csv_path)

    print(f"Found {len(df)} goalie pull events")

    # Initialize database
    db = GoaliePullDatabase()

    # Import each row
    imported_count = 0
    skipped_count = 0

    for idx, row in df.iterrows():
        # Determine if playoff game
        game_id_str = str(row['game_id'])
        playoff_game = game_id_str.startswith('2023030')  # Playoff games have '03' in game type

        # Create event dictionary
        event = {
            'game_id': row['game_id'],
            'team': row['team'],
            'coach': None,  # Will be looked up separately
            'period': row['period'],
            'time_remaining': row['estimated_pull_time'],
            'time_remaining_seconds': row['time_remaining_seconds'],
            'score_differential': row['score_differential'],
            'home_score': None,  # Not in CSV
            'away_score': None,  # Not in CSV
            'opponent': None,  # Not in CSV
            'home_game': None,  # Not in CSV
            'division_game': False,  # Unknown
            'playoff_game': playoff_game,
            'season': '20232024',
            'game_date': row['date'],
            'pull_timestamp': None,  # Not in CSV
            'goalie_name': None,  # Not in CSV
            'result': 'empty_net_goal' if row['outcome'] == 'no_tie' else 'tied_game',
            'goal_scored_by': 'opponent' if row['outcome'] == 'no_tie' else 'trailing_team',
            'time_to_goal_seconds': None,  # Not in CSV
            'final_outcome': row['outcome']
        }

        try:
            row_id = db.insert_pull_event(event)
            if row_id:
                imported_count += 1
                if imported_count % 50 == 0:
                    print(f"Imported {imported_count}/{len(df)} events...")
            else:
                skipped_count += 1
        except Exception as e:
            print(f"Error importing row {idx}: {e}")
            skipped_count += 1

    print("\n" + "="*60)
    print("IMPORT COMPLETE!")
    print("="*60)
    print(f"Total events in CSV: {len(df)}")
    print(f"Successfully imported: {imported_count}")
    print(f"Skipped (duplicates/errors): {skipped_count}")

    # Show statistics
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)

    import sqlite3
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()

    # Total events
    cursor.execute("SELECT COUNT(*) FROM goalie_pulls")
    total = cursor.fetchone()[0]
    print(f"Total goalie pull events in database: {total}")

    # By score differential
    cursor.execute("""
        SELECT score_differential, COUNT(*)
        FROM goalie_pulls
        GROUP BY score_differential
        ORDER BY score_differential
    """)
    print("\nBy score differential:")
    for diff, count in cursor.fetchall():
        print(f"  {diff} goals behind: {count} pulls")

    # By outcome
    cursor.execute("""
        SELECT final_outcome, COUNT(*)
        FROM goalie_pulls
        GROUP BY final_outcome
    """)
    print("\nBy outcome:")
    for outcome, count in cursor.fetchall():
        print(f"  {outcome}: {count}")

    # Playoff vs regular season
    cursor.execute("""
        SELECT
            CASE WHEN playoff_game THEN 'Playoff' ELSE 'Regular Season' END as game_type,
            COUNT(*)
        FROM goalie_pulls
        GROUP BY playoff_game
    """)
    print("\nBy game type:")
    for game_type, count in cursor.fetchall():
        print(f"  {game_type}: {count}")

    conn.close()

    return imported_count


if __name__ == "__main__":
    # Path to CSV file
    csv_path = "C:/Users/nashr/backend/strategies/nhl_goalie_pulls_2023_2024_full.csv"

    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found at {csv_path}")
        sys.exit(1)

    import_csv_to_database(csv_path)
