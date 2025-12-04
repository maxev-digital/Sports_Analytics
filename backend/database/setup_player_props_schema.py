"""
Player Props Database Schema Setup
===================================
Creates all necessary tables for multi-sport player props system

Tables:
- player_props_lines: Current market lines from bookmakers
- player_props_predictions: ML model predictions with edges
- player_stats_cache: Cached player statistics
- team_stats_cache: Cached team statistics
- props_results: Game results for grading predictions

Usage:
    python backend/database/setup_player_props_schema.py
    python backend/database/setup_player_props_schema.py --db custom_path.db
"""

import sqlite3
import argparse
from pathlib import Path
from datetime import datetime


def setup_schema(db_path: str):
    """Create all tables for player props system"""
    print("=" * 70)
    print("PLAYER PROPS DATABASE SCHEMA SETUP")
    print("=" * 70)
    print(f"Database: {db_path}")
    print()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Player Props Lines Table (current market lines)
    print("Creating player_props_lines table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_props_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            game_id TEXT NOT NULL,
            player_id TEXT NOT NULL,
            player_name TEXT NOT NULL,
            team TEXT NOT NULL,
            opponent TEXT NOT NULL,
            home_away TEXT NOT NULL,
            prop_type TEXT NOT NULL,
            market_line REAL NOT NULL,
            over_odds INTEGER,
            under_odds INTEGER,
            bookmaker TEXT NOT NULL,
            sport TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, player_name, prop_type, bookmaker, sport)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_lines_date_sport ON player_props_lines(date, sport)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_lines_player ON player_props_lines(player_name, sport)")
    print("  ✓ player_props_lines")

    # 2. Player Props Predictions Table (ML predictions)
    print("Creating player_props_predictions table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_props_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_date TEXT NOT NULL,
            player_name TEXT NOT NULL,
            team TEXT NOT NULL,
            opponent TEXT NOT NULL,
            home_away TEXT NOT NULL,
            prop_type TEXT NOT NULL,
            market_line REAL NOT NULL,
            predicted_value REAL NOT NULL,
            edge REAL,
            edge_pct REAL,
            confidence REAL,
            confidence_level TEXT,
            recommendation TEXT,
            over_odds INTEGER,
            under_odds INTEGER,
            bookmaker TEXT,
            model_type TEXT,
            sport TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            result TEXT,
            actual_value REAL,
            graded_at TEXT,
            UNIQUE(prediction_date, player_name, prop_type, sport)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_date_sport ON player_props_predictions(prediction_date, sport)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_result ON player_props_predictions(result)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_recommendation ON player_props_predictions(recommendation)")
    print("  ✓ player_props_predictions")

    # 3. Player Stats Cache Table
    print("Creating player_stats_cache table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_stats_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            team TEXT NOT NULL,
            sport TEXT NOT NULL,
            season TEXT,
            points_per_game REAL,
            rebounds_per_game REAL,
            assists_per_game REAL,
            fg3_per_game REAL,
            blocks_per_game REAL,
            steals_per_game REAL,
            field_goal_pct REAL,
            minutes_per_game REAL,
            usage_rate REAL,
            last_10_ppg REAL,
            last_10_rpg REAL,
            last_10_apg REAL,
            home_ppg REAL,
            away_ppg REAL,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(player_name, team, sport, season)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_stats_name_sport ON player_stats_cache(player_name, sport)")
    print("  ✓ player_stats_cache")

    # 4. Team Stats Cache Table
    print("Creating team_stats_cache table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_stats_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT NOT NULL,
            sport TEXT NOT NULL,
            season TEXT,
            offensive_rating REAL,
            defensive_rating REAL,
            pace REAL,
            assists_per_game REAL,
            turnovers_per_game REAL,
            steals_per_game REAL,
            blocks_per_game REAL,
            rebounds_per_game REAL,
            points_allowed REAL,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(team, sport, season)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_stats_team_sport ON team_stats_cache(team, sport)")
    print("  ✓ team_stats_cache")

    # 5. Props Results Table (for grading)
    print("Creating props_results table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS props_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_date TEXT NOT NULL,
            game_id TEXT NOT NULL,
            player_name TEXT NOT NULL,
            team TEXT NOT NULL,
            opponent TEXT NOT NULL,
            sport TEXT NOT NULL,
            prop_type TEXT NOT NULL,
            actual_value REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(game_date, player_name, prop_type, sport)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_date_sport ON props_results(game_date, sport)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_player ON props_results(player_name, sport)")
    print("  ✓ props_results")

    # 6. Model Performance Tracking Table
    print("Creating model_performance_tracking table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_performance_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sport TEXT NOT NULL,
            prop_type TEXT NOT NULL,
            date_range_start TEXT NOT NULL,
            date_range_end TEXT NOT NULL,
            total_predictions INTEGER DEFAULT 0,
            correct_predictions INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            pushes INTEGER DEFAULT 0,
            units_won REAL DEFAULT 0,
            roi REAL DEFAULT 0,
            avg_edge REAL,
            avg_confidence REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(sport, prop_type, date_range_start, date_range_end)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_perf_sport ON model_performance_tracking(sport, prop_type)")
    print("  ✓ model_performance_tracking")

    conn.commit()
    conn.close()

    print()
    print("=" * 70)
    print("SCHEMA SETUP COMPLETE")
    print("=" * 70)
    print()
    print("Tables created:")
    print("  1. player_props_lines       - Market lines from bookmakers")
    print("  2. player_props_predictions - ML predictions with edges")
    print("  3. player_stats_cache       - Player statistics cache")
    print("  4. team_stats_cache         - Team statistics cache")
    print("  5. props_results            - Game results for grading")
    print("  6. model_performance_tracking - Model performance metrics")
    print()
    print("Ready to use!")
    print()


def verify_schema(db_path: str):
    """Verify all tables exist"""
    print("Verifying schema...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = [
        'player_props_lines',
        'player_props_predictions',
        'player_stats_cache',
        'team_stats_cache',
        'props_results',
        'model_performance_tracking'
    ]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}

    all_exist = True
    for table in tables:
        if table in existing_tables:
            print(f"  ✓ {table}")
        else:
            print(f"  ✗ {table} - MISSING")
            all_exist = False

    conn.close()

    if all_exist:
        print("\n✓ All tables verified successfully")
    else:
        print("\n✗ Some tables are missing - run setup again")

    return all_exist


def main():
    parser = argparse.ArgumentParser(description='Setup player props database schema')
    parser.add_argument('--db', type=str, default='data/player_props.db',
                       help='Database path (default: data/player_props.db)')
    parser.add_argument('--verify-only', action='store_true',
                       help='Only verify schema without creating tables')

    args = parser.parse_args()

    # Ensure data directory exists
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if args.verify_only:
        verify_schema(str(db_path))
    else:
        setup_schema(str(db_path))
        verify_schema(str(db_path))


if __name__ == "__main__":
    main()
