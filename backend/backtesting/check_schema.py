from database.backtest_db import BacktestDB

db = BacktestDB()
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(historical_games)')
cols = cursor.fetchall()

print('historical_games columns:')
for col in cols:
    print(f'  {col[1]} ({col[2]})')

# Also show a sample row
cursor.execute('SELECT * FROM historical_games LIMIT 1')
sample = cursor.fetchone()
if sample:
    print('\nSample data:')
    for i, val in enumerate(sample):
        print(f'  {cols[i][1]}: {val}')

conn.close()
