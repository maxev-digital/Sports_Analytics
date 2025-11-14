"""
Initialize player props database
Run this script once to create all tables
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.connection import init_database, get_db_session, engine
from database.models import (
    PlayerPropsLine,
    PlayerPropsResult,
    PlayerPropsPrediction,
    PlayerStatsCache
)
from sqlalchemy import inspect


def check_database_status():
    """
    Check if database exists and show table info
    """
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if not tables:
        print("❌ No tables found - database needs initialization")
        return False

    print(f"✓ Database found with {len(tables)} tables:")
    for table in tables:
        columns = inspector.get_columns(table)
        print(f"  - {table} ({len(columns)} columns)")

    # Check record counts
    db = get_db_session()
    try:
        lines_count = db.query(PlayerPropsLine).count()
        results_count = db.query(PlayerPropsResult).count()
        predictions_count = db.query(PlayerPropsPrediction).count()
        stats_count = db.query(PlayerStatsCache).count()

        print(f"\n📊 Current record counts:")
        print(f"  - Props lines: {lines_count}")
        print(f"  - Props results: {results_count}")
        print(f"  - Predictions: {predictions_count}")
        print(f"  - Stats cache: {stats_count}")
    finally:
        db.close()

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("PLAYER PROPS ML DATABASE INITIALIZATION")
    print("=" * 60)

    # Create data directory if it doesn't exist
    data_dir = Path("backend/data")
    data_dir.mkdir(exist_ok=True)
    print(f"✓ Data directory: {data_dir.absolute()}")

    # Initialize database
    print("\n🔧 Initializing database...")
    init_database()

    # Check status
    print("\n📋 Database status:")
    check_database_status()

    print("\n" + "=" * 60)
    print("✅ DATABASE READY FOR DATA COLLECTION")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run daily_props_scraper.py to collect props lines")
    print("2. Run results_tracker.py to grade completed props")
    print("3. After 1-2 months of data, train ML models")
