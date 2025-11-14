"""
Simple database initialization script for player props
Creates SQLite database with all required tables
"""
import sqlite3
from pathlib import Path

# Database file location
DB_PATH = Path("data/player_props.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Create database connection
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

print("=" * 60)
print("PLAYER PROPS ML DATABASE INITIALIZATION")
print("=" * 60)
print(f"Database location: {DB_PATH.absolute()}")

# Create player_props_lines table
print("\nCreating table: player_props_lines...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS player_props_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    game_id TEXT,
    player_id TEXT NOT NULL,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    opponent TEXT NOT NULL,
    home_away TEXT,
    prop_type TEXT NOT NULL,
    market_line REAL NOT NULL,
    over_odds INTEGER,
    under_odds INTEGER,
    bookmaker TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, player_id, prop_type, bookmaker)
)
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_lines_date ON player_props_lines(date)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_lines_player ON player_props_lines(player_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_lines_type ON player_props_lines(prop_type)")

# Create player_props_results table
print("Creating table: player_props_results...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS player_props_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    game_id TEXT,
    player_id TEXT NOT NULL,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    opponent TEXT NOT NULL,
    prop_type TEXT NOT NULL,
    market_line REAL NOT NULL,
    actual_value REAL NOT NULL,
    hit INTEGER NOT NULL,
    difference REAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, player_id, prop_type)
)
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_results_date ON player_props_results(date)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_results_player ON player_props_results(player_id)")

# Create player_props_predictions table
print("Creating table: player_props_predictions...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS player_props_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_date DATE NOT NULL,
    game_date DATE NOT NULL,
    player_id TEXT NOT NULL,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    opponent TEXT NOT NULL,
    prop_type TEXT NOT NULL,
    market_line REAL NOT NULL,
    predicted_value REAL NOT NULL,
    confidence REAL,
    model_type TEXT,
    edge_pct REAL,
    recommendation TEXT,
    actual_value REAL,
    result TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(prediction_date, player_id, prop_type, model_type)
)
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_predictions_date ON player_props_predictions(game_date)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_predictions_player ON player_props_predictions(player_id)")

# Create player_stats_cache table
print("Creating table: player_stats_cache...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS player_stats_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT NOT NULL,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    date DATE NOT NULL,
    games_played INTEGER,
    minutes_per_game REAL,
    points_per_game REAL,
    rebounds_per_game REAL,
    assists_per_game REAL,
    fg3_per_game REAL,
    blocks_per_game REAL,
    steals_per_game REAL,
    fg_pct REAL,
    last_10_ppg REAL,
    last_10_rpg REAL,
    last_10_apg REAL,
    trend_direction TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, date)
)
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_cache_player ON player_stats_cache(player_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_cache_date ON player_stats_cache(date)")

# Commit changes
conn.commit()

# Check what was created
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("\n[SUCCESS] Database initialized successfully!")
print(f"\nCreated {len(tables)} tables:")
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"  - {table[0]}: {count} records")

conn.close()

print("\n" + "=" * 60)
print("[SUCCESS] DATABASE READY FOR DATA COLLECTION")
print("=" * 60)
print("\nNext steps:")
print("1. Run: python backend/scrapers/props/daily_props_scraper.py")
print("2. Run: python backend/scrapers/props/results_tracker.py")
print("3. After 1-2 months of data, train ML models")
print("\nDatabase location:", DB_PATH.absolute())
