#!/usr/bin/env python3
"""
Daily Predictions Backup Script
Runs BEFORE predictions are generated to preserve historical data

Schedule: 7:55 AM CST daily (5 minutes before first predictions)
"""
import shutil
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
TRACKING_DIR = Path("/root/sporttrader/backend/data/tracking")
BACKUP_DIR = Path("/root/sporttrader/backend/data/tracking/backups")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def backup_file(filename: str):
    """Backup a single tracking file with timestamp"""
    source = TRACKING_DIR / filename

    if not source.exists():
        logger.warning(f"File not found: {source}")
        return

    # Create timestamped backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{source.stem}_{timestamp}{source.suffix}"
    destination = BACKUP_DIR / backup_name

    shutil.copy2(source, destination)
    logger.info(f"✓ Backed up: {filename} -> {backup_name}")

    # Also keep a "latest" backup
    latest_backup = BACKUP_DIR / f"{source.stem}_latest{source.suffix}"
    shutil.copy2(source, latest_backup)

    return destination

def cleanup_old_backups(days_to_keep: int = 30):
    """Remove backups older than N days"""
    import time
    cutoff = time.time() - (days_to_keep * 86400)

    removed = 0
    for backup_file in BACKUP_DIR.glob("*.csv"):
        if "_latest" in backup_file.name:
            continue  # Keep latest backups forever

        if backup_file.stat().st_mtime < cutoff:
            backup_file.unlink()
            removed += 1

    if removed > 0:
        logger.info(f"Cleaned up {removed} old backups (older than {days_to_keep} days)")

def main():
    logger.info("="*70)
    logger.info("DAILY PREDICTIONS BACKUP")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("="*70)

    # Backup all tracking files
    files_to_backup = [
        "predictions_log.csv",
        "predictions_log_multi_bet.csv",
        "results_log.csv"
    ]

    for filename in files_to_backup:
        backup_file(filename)

    # Cleanup old backups
    cleanup_old_backups(days_to_keep=30)

    logger.info("="*70)
    logger.info("✅ BACKUP COMPLETE")
    logger.info("="*70)

if __name__ == "__main__":
    main()
