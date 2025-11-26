"""
Odds Archive Data Retention Script
Automatically archives and removes old data to keep database size manageable

Run monthly via cron to keep database under 50GB
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "odds_history.db"

# Retention settings
DAYS_TO_KEEP = 365  # Keep 1 year of detailed odds
KEEP_PROP_RESULTS_FOREVER = True  # Always keep graded prop results


def get_database_size():
    """Get database file size in MB"""
    if DB_PATH.exists():
        return DB_PATH.stat().st_size / (1024 * 1024)
    return 0


def archive_old_game_odds(days_to_keep: int) -> int:
    """
    Archive game odds older than specified days

    Returns:
        Count of records archived/deleted
    """
    cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Count records to be archived
    cursor.execute("""
        SELECT COUNT(*) FROM game_odds_pregame WHERE game_date < ?
    """, (cutoff_date,))
    pregame_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM game_odds_live WHERE game_date < ?
    """, (cutoff_date,))
    live_count = cursor.fetchone()[0]

    total_count = pregame_count + live_count

    if total_count == 0:
        logger.info(f"No game odds older than {days_to_keep} days to archive")
        conn.close()
        return 0

    logger.info(f"Archiving {total_count:,} game odds records older than {cutoff_date}")

    # Delete old pregame odds
    cursor.execute("DELETE FROM game_odds_pregame WHERE game_date < ?", (cutoff_date,))
    logger.info(f"  • Deleted {pregame_count:,} pregame odds records")

    # Delete old live odds
    cursor.execute("DELETE FROM game_odds_live WHERE game_date < ?", (cutoff_date,))
    logger.info(f"  • Deleted {live_count:,} live odds records")

    conn.commit()
    conn.close()

    return total_count


def archive_old_prop_odds(days_to_keep: int) -> int:
    """
    Archive player prop odds older than specified days
    Keep prop_results forever (they're small and valuable)

    Returns:
        Count of records archived/deleted
    """
    cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Count records to be archived
    cursor.execute("""
        SELECT COUNT(*) FROM prop_odds_pregame WHERE game_date < ?
    """, (cutoff_date,))
    pregame_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM prop_odds_live WHERE game_date < ?
    """, (cutoff_date,))
    live_count = cursor.fetchone()[0]

    total_count = pregame_count + live_count

    if total_count == 0:
        logger.info(f"No prop odds older than {days_to_keep} days to archive")
        conn.close()
        return 0

    logger.info(f"Archiving {total_count:,} prop odds records older than {cutoff_date}")

    # Delete old pregame props
    cursor.execute("DELETE FROM prop_odds_pregame WHERE game_date < ?", (cutoff_date,))
    logger.info(f"  • Deleted {pregame_count:,} pregame prop records")

    # Delete old live props
    cursor.execute("DELETE FROM prop_odds_live WHERE game_date < ?", (cutoff_date,))
    logger.info(f"  • Deleted {live_count:,} live prop records")

    conn.commit()
    conn.close()

    return total_count


def vacuum_database():
    """
    Reclaim space from deleted records
    This actually reduces the database file size
    """
    logger.info("Running VACUUM to reclaim space...")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("VACUUM")
    conn.execute("ANALYZE")
    conn.close()

    logger.info("✓ Database vacuumed and analyzed")


def run_retention_cleanup():
    """Main retention cleanup workflow"""
    logger.info("=" * 70)
    logger.info("ODDS ARCHIVE RETENTION CLEANUP")
    logger.info("=" * 70)

    # Get initial size
    initial_size = get_database_size()
    logger.info(f"\nInitial database size: {initial_size:.2f} MB")
    logger.info(f"Retention period: {DAYS_TO_KEEP} days\n")

    # Archive old game odds
    game_odds_archived = archive_old_game_odds(DAYS_TO_KEEP)

    # Archive old prop odds
    prop_odds_archived = archive_old_prop_odds(DAYS_TO_KEEP)

    # Get size before vacuum
    size_before_vacuum = get_database_size()

    # Reclaim space
    if game_odds_archived > 0 or prop_odds_archived > 0:
        vacuum_database()

    # Get final size
    final_size = get_database_size()
    space_saved = initial_size - final_size

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("RETENTION CLEANUP SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Game odds archived:     {game_odds_archived:,} records")
    logger.info(f"Prop odds archived:     {prop_odds_archived:,} records")
    logger.info(f"Total archived:         {game_odds_archived + prop_odds_archived:,} records")
    logger.info(f"\nInitial size:           {initial_size:.2f} MB")
    logger.info(f"After deletion:         {size_before_vacuum:.2f} MB")
    logger.info(f"After VACUUM:           {final_size:.2f} MB")
    logger.info(f"Space reclaimed:        {space_saved:.2f} MB")
    logger.info("=" * 70 + "\n")

    # Get current record counts
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM game_odds_pregame")
    game_odds_remaining = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM prop_odds_pregame")
    props_remaining = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM prop_results")
    prop_results_count = cursor.fetchone()[0]

    conn.close()

    logger.info("REMAINING DATA:")
    logger.info(f"  Game odds:        {game_odds_remaining:,} records")
    logger.info(f"  Player props:     {props_remaining:,} records")
    logger.info(f"  Prop results:     {prop_results_count:,} records (kept forever)")
    logger.info("")


if __name__ == "__main__":
    run_retention_cleanup()
