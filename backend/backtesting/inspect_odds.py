"""Inspect odds_history table data"""
from database.backtest_db import BacktestDB

db = BacktestDB()
conn = db.get_connection()
cursor = conn.cursor()

# Check sample odds records
cursor.execute('''
    SELECT timestamp, home_team, away_team, market_type, line_value, odds
    FROM odds_history
    LIMIT 5
''')

print("Sample odds records from database:")
print("="*80)
for row in cursor.fetchall():
    timestamp, home, away, market, line, odds = row
    date = timestamp[:10] if timestamp else "N/A"
    print(f"Date: {date}")
    print(f"  Matchup: {away} @ {home}")
    print(f"  Market: {market}, Line: {line}, Odds: {odds}")
    print()

# Check a sample game from our dataset
cursor.execute('''
    SELECT date, home_team, away_team
    FROM games
    WHERE date BETWEEN '2023-10-24' AND '2023-10-26'
    LIMIT 3
''')

print("\nSample games from our dataset:")
print("="*80)
for row in cursor.fetchall():
    date, home, away = row
    print(f"Date: {date}, {away} @ {home}")

conn.close()
