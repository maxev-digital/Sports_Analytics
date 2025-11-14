#!/usr/bin/env python3
"""
Automated Database Sync - D: Drive to VPS
Ensures all local database work is backed up and deployed to production

Runs: Daily at 2:00 AM CST (before predictions generate)
"""
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
VPS_HOST = "root@148.230.87.135"
SSH_KEY = str(Path.home() / ".ssh" / "hostinger_vps")

# Database files to sync
DATABASE_SYNC_MAP = {
    # Source (D: drive) -> Destination (VPS)
    "D:/backend/data/player_props.db": "/root/sporttrader/backend/data/player_props.db",
    "D:/backend/data/tracking/predictions_log.csv": "/root/sporttrader/backend/data/tracking/predictions_log.csv",
    "D:/backend/data/tracking/predictions_log_multi_bet.csv": "/root/sporttrader/backend/data/tracking/predictions_log_multi_bet.csv",
    "D:/backend/data/tracking/results_log.csv": "/root/sporttrader/backend/data/tracking/results_log.csv",
}

def sync_file(local_path: str, remote_path: str) -> bool:
    """Sync a single file to VPS using scp"""
    local_file = Path(local_path)

    if not local_file.exists():
        logger.warning(f"Local file not found: {local_path}")
        return False

    file_size = local_file.stat().st_size / (1024 * 1024)  # MB
    logger.info(f"Syncing {local_file.name} ({file_size:.2f} MB) to VPS...")

    try:
        # Create remote directory if needed
        remote_dir = str(Path(remote_path).parent)
        subprocess.run(
            ["ssh", "-i", SSH_KEY, VPS_HOST, f"mkdir -p {remote_dir}"],
            check=True,
            capture_output=True
        )

        # SCP the file
        result = subprocess.run(
            ["scp", "-i", SSH_KEY, local_path, f"{VPS_HOST}:{remote_path}"],
            check=True,
            capture_output=True,
            text=True
        )

        logger.info(f"✓ Synced {local_file.name}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to sync {local_file.name}: {e.stderr}")
        return False

def verify_sync(remote_path: str, expected_size_mb: float) -> bool:
    """Verify file was synced successfully"""
    try:
        result = subprocess.run(
            ["ssh", "-i", SSH_KEY, VPS_HOST, f"stat -c%s {remote_path}"],
            check=True,
            capture_output=True,
            text=True
        )

        remote_size_mb = int(result.stdout.strip()) / (1024 * 1024)

        # Allow 1% size difference
        if abs(remote_size_mb - expected_size_mb) / expected_size_mb < 0.01:
            logger.info(f"✓ Verified {Path(remote_path).name} ({remote_size_mb:.2f} MB)")
            return True
        else:
            logger.warning(f"Size mismatch: local={expected_size_mb:.2f}MB, remote={remote_size_mb:.2f}MB")
            return False

    except subprocess.CalledProcessError as e:
        logger.error(f"Verification failed: {e.stderr}")
        return False

def create_backup_on_vps(remote_path: str):
    """Create timestamped backup before overwriting"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{remote_path}.backup_{timestamp}"

    try:
        subprocess.run(
            ["ssh", "-i", SSH_KEY, VPS_HOST,
             f"if [ -f {remote_path} ]; then cp {remote_path} {backup_path}; fi"],
            check=True,
            capture_output=True
        )
        logger.info(f"✓ Created backup: {Path(backup_path).name}")
    except subprocess.CalledProcessError:
        logger.warning("No existing file to backup")

def cleanup_old_backups(remote_path: str, keep_days: int = 7):
    """Remove backups older than N days"""
    try:
        subprocess.run(
            ["ssh", "-i", SSH_KEY, VPS_HOST,
             f"find $(dirname {remote_path}) -name '$(basename {remote_path}).backup_*' -mtime +{keep_days} -delete"],
            check=True,
            capture_output=True
        )
        logger.info(f"✓ Cleaned up backups older than {keep_days} days")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Cleanup warning: {e.stderr}")

def main():
    logger.info("="*70)
    logger.info("DATABASE SYNC - D: DRIVE → VPS")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("="*70)

    success_count = 0
    fail_count = 0

    for local_path, remote_path in DATABASE_SYNC_MAP.items():
        local_file = Path(local_path)

        if not local_file.exists():
            logger.warning(f"SKIP: {local_path} (not found)")
            continue

        file_size_mb = local_file.stat().st_size / (1024 * 1024)

        # Create backup of existing file on VPS
        create_backup_on_vps(remote_path)

        # Sync the file
        if sync_file(local_path, remote_path):
            # Verify sync
            if verify_sync(remote_path, file_size_mb):
                success_count += 1
            else:
                fail_count += 1
        else:
            fail_count += 1

    # Cleanup old backups
    for remote_path in DATABASE_SYNC_MAP.values():
        cleanup_old_backups(remote_path, keep_days=7)

    logger.info("")
    logger.info("="*70)
    logger.info("SYNC COMPLETE")
    logger.info("="*70)
    logger.info(f"Success: {success_count}")
    logger.info(f"Failed: {fail_count}")
    logger.info("="*70)

    if fail_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
