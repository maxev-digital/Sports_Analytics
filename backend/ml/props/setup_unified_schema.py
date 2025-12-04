"""
Unified Database Schema Setup for Player Props + DFS Crusher
==============================================================

This script adds player props tables to the existing ml/predictions.db
(which already contains team totals predictions).

UNIFIED DATABASE: backend/ml/predictions.db

NEW TABLES TO ADD:
1. player_props_predictions - ML predictions with edges
2. correlated_combos - DFS combos for PrizePicks/Underdog
3. player_stats_cache - Player statistics cache
4. team_stats_cache - Team statistics cache
5. props_results - Historical results for grading

EXISTING TABLES (untouched):
- predictions (team totals/spreads/moneyline)
- results
- model_performance
- daily_performance

Usage:
    python backend/ml/props/setup_unified_schema.py
    python backend/ml/props/setup_unified_schema.py --verify-only
"""

import sqlite3
import argparse
from pathlib import Path
from datetime import datetime


# Path to unified database
DB_PATH = Path(__file__).parent.parent / "predictions.db"


def setup_player_props_tables(db_path: str):
    """Add player props tables to ml/predictions.db"""
    print("=" * 80)
    print("PLAYER PROPS + DFS CRUSHER - UNIFIED DATABASE SETUP")
    print("=" * 80)
    print(f"Database: {db_path}")
    print()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Player Props Predictions Table
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
            model_type TEXT DEFAULT 'enhanced_ensemble_7_models',
            sport TEXT NOT NULL DEFAULT 'nba',

            -- 7-Model Breakdown (matching team totals architecture)
            xgboost_pred REAL,
            lightgbm_pred REAL,
            rf_pred REAL,
            linear_pred REAL,
            pytorch_pred REAL,
            catboost_pred REAL,
            ensemble_pred REAL,

            -- Results (for grading)
            result TEXT,
            actual_value REAL,
            graded_at TEXT,

            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(prediction_date, player_name, prop_type, sport)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_preds_date_sport ON player_props_predictions(prediction_date, sport)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_preds_result ON player_props_predictions(result)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_preds_confidence ON player_props_predictions(confidence_level)")
    print("  [OK] player_props_predictions")

    # 2. Correlated Combos Table (DFS Crusher)
    print("Creating correlated_combos table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS correlated_combos (
            combo_id TEXT PRIMARY KEY,
            sport TEXT NOT NULL,
            players TEXT NOT NULL,
            props TEXT NOT NULL,
            lines TEXT NOT NULL,
            directions TEXT NOT NULL,
            true_probability REAL NOT NULL,
            prize_picks_payout REAL NOT NULL,
            expected_value_percent REAL NOT NULL,
            demon_goblin_score REAL,
            site_with_best_line TEXT,

            -- Sacred display fields
            display_edge REAL,
            display_confidence TEXT,
            display_recommendation TEXT,
            display_win_rate TEXT,
            display_units REAL,
            display_roi TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(combo_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_combos_date_sport ON correlated_combos(created_at, sport)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_combos_ev ON correlated_combos(expected_value_percent)")
    print("  [OK] correlated_combos")

    # 3. Player Stats Cache
    print("Creating player_stats_cache table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_stats_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            team TEXT NOT NULL,
            sport TEXT NOT NULL,
            season TEXT DEFAULT '2025-26',

            -- Season Averages
            points_per_game REAL,
            rebounds_per_game REAL,
            assists_per_game REAL,
            fg3_per_game REAL,
            blocks_per_game REAL,
            steals_per_game REAL,
            field_goal_pct REAL,
            three_point_pct REAL,
            free_throw_pct REAL,
            minutes_per_game REAL,
            usage_rate REAL,

            -- Advanced Stats
            player_offensive_rating REAL,
            player_defensive_rating REAL,
            turnover_rate REAL,
            assist_rate REAL,
            rebound_rate REAL,
            PER REAL,
            true_shooting_pct REAL,

            -- Recent Form (Last 10 games)
            last_10_ppg REAL,
            last_10_rpg REAL,
            last_10_apg REAL,
            home_ppg REAL,
            away_ppg REAL,

            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(player_name, team, sport, season)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_cache_name_sport ON player_stats_cache(player_name, sport)")
    print("  [OK] player_stats_cache")

    # 4. Team Stats Cache
    print("Creating team_stats_cache table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_stats_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT NOT NULL,
            sport TEXT NOT NULL,
            season TEXT DEFAULT '2025-26',

            offensive_rating REAL,
            defensive_rating REAL,
            pace REAL,
            assists_per_game REAL,
            turnovers_per_game REAL,
            steals_per_game REAL,
            blocks_per_game REAL,
            rebounds_per_game REAL,
            points_per_game REAL,
            points_allowed REAL,

            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(team, sport, season)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_cache_team_sport ON team_stats_cache(team, sport)")
    print("  [OK] team_stats_cache")

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
    print("  [OK] props_results")

    # 6. Player Props Lines Table (today's market data)
    print("Creating player_props_lines table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_props_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            player_name TEXT NOT NULL,
            team TEXT NOT NULL,
            opponent TEXT NOT NULL,
            home_away TEXT NOT NULL,
            sport TEXT NOT NULL,
            prop_type TEXT NOT NULL,
            market_line REAL NOT NULL,
            over_odds INTEGER,
            under_odds INTEGER,
            bookmaker TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, player_name, prop_type, bookmaker, sport)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_lines_date_sport ON player_props_lines(date, sport)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_lines_player ON player_props_lines(player_name, sport)")
    print("  [OK] player_props_lines")

    conn.commit()
    conn.close()

    print()
    print("=" * 80)
    print("SCHEMA SETUP COMPLETE")
    print("=" * 80)
    print()
    print("Tables added to ml/predictions.db:")
    print("  1. player_props_predictions  - ML predictions (7-model ensemble)")
    print("  2. correlated_combos         - DFS PrizePicks combos")
    print("  3. player_stats_cache        - Player statistics")
    print("  4. team_stats_cache          - Team statistics")
    print("  5. props_results             - Historical results")
    print("  6. player_props_lines        - Today's market lines")
    print()
    print("Existing tables (untouched):")
    print("  - predictions (team totals)")
    print("  - results")
    print("  - model_performance")
    print()
    print("[SUCCESS] Ready to use!")
    print()


def verify_schema(db_path: str):
    """Verify all tables exist"""
    print("Verifying schema...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    required_tables = [
        'player_props_predictions',
        'correlated_combos',
        'player_stats_cache',
        'team_stats_cache',
        'props_results',
        'player_props_lines'
    ]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}

    all_exist = True
    print("\nPlayer Props Tables:")
    for table in required_tables:
        if table in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  [OK] {table:<30} ({count} rows)")
        else:
            print(f"  [MISSING] {table:<30}")
            all_exist = False

    print("\nExisting Team Totals Tables:")
    for table in ['predictions', 'results', 'model_performance']:
        if table in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  [OK] {table:<30} ({count} rows)")

    conn.close()

    if all_exist:
        print("\n[SUCCESS] All player props tables verified successfully")
    else:
        print("\n[WARNING] Some tables are missing - run setup again")

    return all_exist


def main():
    parser = argparse.ArgumentParser(description='Setup player props tables in ml/predictions.db')
    parser.add_argument('--verify-only', action='store_true',
                       help='Only verify schema without creating tables')

    args = parser.parse_args()

    # Ensure ml directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if args.verify_only:
        verify_schema(str(DB_PATH))
    else:
        setup_player_props_tables(str(DB_PATH))
        verify_schema(str(DB_PATH))


if __name__ == "__main__":
    main()
