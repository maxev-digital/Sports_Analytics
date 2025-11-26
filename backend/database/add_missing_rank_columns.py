"""
Add missing ranking columns to nfl_team_stats table
"""
import sqlite3
import os

# Database path
db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'nfl_stats.db')

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Missing ranking columns to add
missing_columns = [
    'passing_yards_per_game_rank',
    'rushing_yards_per_game_rank',
    'first_downs_rank',
    'third_down_pct_rank',
    'red_zone_pct_rank',  # Alias for red_zone_scoring_pct_rank
    'turnover_differential_rank',
    'total_yards_per_game_rank',
    'sacks_rank',  # Alias for sacks_per_game_rank
    'points_allowed_per_game_rank',  # Alias for opponent_points_per_game_rank
    'yards_allowed_per_game_rank',
    'passing_yards_allowed_rank',
    'rushing_yards_allowed_rank',
    'opponent_third_down_pct_rank',
    'opponent_red_zone_pct_rank',  # Alias for opponent_red_zone_scoring_pct_rank
    'penalties_rank',
    'touchdowns_per_game_rank',  # Alias for total_touchdowns_per_game_rank
]

print("Adding missing ranking columns to nfl_team_stats table...")

for column in missing_columns:
    try:
        cursor.execute(f'ALTER TABLE nfl_team_stats ADD COLUMN {column} INTEGER')
        print(f"  [OK] Added {column}")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print(f"  [SKIP] {column} already exists")
        else:
            print(f"  [ERROR] Adding {column}: {e}")

conn.commit()
conn.close()

print("\nMigration complete!")
print("Now re-run the collection script to populate the new columns:")
print("  python D:/Max_EV_Sports/current_vps/nfl_database_system/python_files/collect_nfl_stats.py")
