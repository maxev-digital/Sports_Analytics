import sqlite3

conn = sqlite3.connect('backend/data/nhl_goalie_pulls.db')
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print(f"Tables: {tables}")

# Count rows in each table
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table}: {count} rows")

# If goalie_pull_events exists, show date range and top teams
if 'goalie_pull_events' in tables:
    cursor.execute("SELECT MIN(game_date), MAX(game_date) FROM goalie_pull_events")
    dates = cursor.fetchone()
    print(f"\nDate range: {dates[0]} to {dates[1]}")

    cursor.execute("SELECT team, COUNT(*) as pulls FROM goalie_pull_events GROUP BY team ORDER BY pulls DESC LIMIT 10")
    print("\nTop 10 teams by goalie pulls:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} pulls")

conn.close()
