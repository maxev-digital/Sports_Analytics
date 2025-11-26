#!/bin/bash
#
# Odds Archive Database Backup Script
# Runs daily to create timestamped backups
#
# Backup strategy:
# - Daily backups kept for 7 days
# - Weekly backups (Sunday) kept for 4 weeks
# - Monthly backups (1st of month) kept forever
#

set -e  # Exit on error

# Paths
DB_PATH="/root/sporttrader/backend/data/odds_archive/odds_history.db"
BACKUP_DIR="/root/sporttrader/backups/odds_archive"
DAILY_DIR="$BACKUP_DIR/daily"
WEEKLY_DIR="$BACKUP_DIR/weekly"
MONTHLY_DIR="$BACKUP_DIR/monthly"
LOG_FILE="$BACKUP_DIR/backup.log"

# Create backup directories
mkdir -p "$DAILY_DIR" "$WEEKLY_DIR" "$MONTHLY_DIR"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE=$(date +%Y-%m-%d)
DAY_OF_WEEK=$(date +%u)  # 1=Monday, 7=Sunday
DAY_OF_MONTH=$(date +%d)

# Log function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================================================="
log "ODDS ARCHIVE BACKUP STARTED"
log "=========================================================================="

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    log "ERROR: Database not found at $DB_PATH"
    exit 1
fi

# Get database size
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
log "Database size: $DB_SIZE"

# Backup filename
BACKUP_FILE="odds_history_${TIMESTAMP}.db"

# 1. DAILY BACKUP (always)
log "Creating daily backup..."
cp "$DB_PATH" "$DAILY_DIR/$BACKUP_FILE"
DAILY_SIZE=$(du -h "$DAILY_DIR/$BACKUP_FILE" | cut -f1)
log "✓ Daily backup created: $DAILY_DIR/$BACKUP_FILE ($DAILY_SIZE)"

# 2. WEEKLY BACKUP (Sunday only)
if [ "$DAY_OF_WEEK" -eq 7 ]; then
    log "Creating weekly backup (Sunday)..."
    WEEKLY_FILE="odds_history_week_${TIMESTAMP}.db"
    cp "$DB_PATH" "$WEEKLY_DIR/$WEEKLY_FILE"
    log "✓ Weekly backup created: $WEEKLY_DIR/$WEEKLY_FILE"
fi

# 3. MONTHLY BACKUP (1st of month only)
if [ "$DAY_OF_MONTH" -eq "01" ]; then
    log "Creating monthly backup (1st of month)..."
    MONTHLY_FILE="odds_history_$(date +%Y-%m).db"
    cp "$DB_PATH" "$MONTHLY_DIR/$MONTHLY_FILE"
    log "✓ Monthly backup created: $MONTHLY_DIR/$MONTHLY_FILE"
fi

# 4. CLEANUP OLD BACKUPS

# Remove daily backups older than 7 days
log "Cleaning up old daily backups (>7 days)..."
find "$DAILY_DIR" -name "odds_history_*.db" -type f -mtime +7 -delete
DAILY_COUNT=$(ls -1 "$DAILY_DIR" | wc -l)
log "✓ Daily backups remaining: $DAILY_COUNT"

# Remove weekly backups older than 28 days (4 weeks)
log "Cleaning up old weekly backups (>28 days)..."
find "$WEEKLY_DIR" -name "odds_history_*.db" -type f -mtime +28 -delete
WEEKLY_COUNT=$(ls -1 "$WEEKLY_DIR" | wc -l)
log "✓ Weekly backups remaining: $WEEKLY_COUNT"

# Monthly backups kept forever (no cleanup)
MONTHLY_COUNT=$(ls -1 "$MONTHLY_DIR" 2>/dev/null | wc -l)
log "✓ Monthly backups: $MONTHLY_COUNT (kept forever)"

# 5. BACKUP VERIFICATION
log "Verifying backup integrity..."
sqlite3 "$DAILY_DIR/$BACKUP_FILE" "PRAGMA integrity_check;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log "✓ Backup integrity verified"
else
    log "ERROR: Backup integrity check failed!"
    exit 1
fi

# 6. SUMMARY
BACKUP_DIR_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log ""
log "=========================================================================="
log "BACKUP SUMMARY"
log "=========================================================================="
log "Source database:     $DB_PATH ($DB_SIZE)"
log "Backup directory:    $BACKUP_DIR ($BACKUP_DIR_SIZE)"
log "Daily backups:       $DAILY_COUNT (last 7 days)"
log "Weekly backups:      $WEEKLY_COUNT (last 4 weeks)"
log "Monthly backups:     $MONTHLY_COUNT (kept forever)"
log "=========================================================================="
log "BACKUP COMPLETED SUCCESSFULLY"
log "=========================================================================="
log ""

exit 0
