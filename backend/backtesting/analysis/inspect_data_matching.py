"""Inspect how games are matching to odds"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from database.backtest_db import BacktestDB

db = BacktestDB()
conn = db.get_connection()
cursor = conn.cursor()

print("\n" + "="*80)
print("INSPECTING GAME-TO-ODDS MATCHING")
print("="*80 + "\n")

# Get first 5 matched games
cursor.execute("""
    SELECT
        g.date,
        g.home_team,
        g.away_team,
        g.home_score + g.away_score as actual_total,
        o.line_value as closing_total,
        (g.home_score + g.away_score) - o.line_value as deviation,
        o.timestamp,
        o.home_team as odds_home,
        o.away_team as odds_away
    FROM historical_games g
    JOIN odds_history o ON date(g.date) = date(o.timestamp)
        AND o.market_type = 'totals'
        AND o.sport = 'basketball_nba'
    WHERE g.home_score IS NOT NULL
      AND g.q1_home IS NOT NULL
      AND o.line_value IS NOT NULL
    LIMIT 10
""")

print("Sample Matched Games:")
print("-" * 80)
for row in cursor.fetchall():
    date, home, away, actual, closing, dev, timestamp, odds_home, odds_away = row
    print(f"\nGame Date: {date}")
    print(f"  Game: {away} @ {home}")
    print(f"  Actual Total: {actual}")
    print(f"  Closing Total: {closing}")
    print(f"  Deviation: {dev:+.1f}")
    print(f"  Odds Timestamp: {timestamp}")
    print(f"  Odds Matchup: {odds_away} @ {odds_home}")
    print(f"  Teams Match: {home == odds_home and away == odds_away}")

# Check odds table structure
print("\n" + "="*80)
print("ODDS TABLE SAMPLE")
print("="*80 + "\n")

cursor.execute("""
    SELECT timestamp, sport, home_team, away_team, market_type, line_value, odds, sportsbook
    FROM odds_history
    WHERE market_type = 'totals'
    LIMIT 5
""")

print("Sample Odds Records:")
print("-" * 80)
for row in cursor.fetchall():
    print(f"\nTimestamp: {row[0]}")
    print(f"  Sport: {row[1]}")
    print(f"  Matchup: {row[3]} @ {row[2]}")
    print(f"  Market: {row[4]}")
    print(f"  Line: {row[5]}")
    print(f"  Odds: {row[6]}")
    print(f"  Book: {row[7]}")

conn.close()
