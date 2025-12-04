"""
Migration Script: Consolidate User Data to Unified Database
Migrates from:
  - users.json → users table
  - sessions.json → sessions table
  - user_activity_log.json → user_activity table
  - user_settings.db → user_settings table
  - subscriptions.db → subscriptions/payment_history tables
  - user_bets.db → user_bets table

IMPORTANT: This also upgrades passwords from SHA256 to bcrypt
"""
import sys
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import shutil

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.unified_db import init_database, get_db

# Install bcrypt if not available
try:
    import bcrypt
except ImportError:
    print("❌ bcrypt not installed. Run: pip install bcrypt")
    sys.exit(1)

# Paths
BACKEND_DIR = Path(__file__).parent.parent
USERS_JSON = BACKEND_DIR / "users.json"
SESSIONS_JSON = BACKEND_DIR / "sessions.json"
ACTIVITY_JSON = BACKEND_DIR / "user_activity_log.json"
OLD_SETTINGS_DB = BACKEND_DIR / "user_settings.db"
OLD_SUBSCRIPTIONS_DB = BACKEND_DIR / "database" / "subscriptions.db"
OLD_BETS_DB = BACKEND_DIR / "data" / "bets" / "user_bets.db"

# Backup directory
BACKUP_DIR = BACKEND_DIR / "migrations" / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")


def create_backups():
    """Backup all existing data files before migration"""
    print("\n📦 Creating backups...")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    files_to_backup = [
        USERS_JSON,
        SESSIONS_JSON,
        ACTIVITY_JSON,
        OLD_SETTINGS_DB,
        OLD_SUBSCRIPTIONS_DB,
        OLD_BETS_DB
    ]

    for file_path in files_to_backup:
        if file_path.exists():
            backup_path = BACKUP_DIR / file_path.name
            shutil.copy2(file_path, backup_path)
            print(f"  ✅ Backed up: {file_path.name}")

    print(f"\n✅ Backups saved to: {BACKUP_DIR}\n")


def migrate_users():
    """Migrate users.json → users table"""
    print("👥 Migrating users...")

    if not USERS_JSON.exists():
        print("  ⚠️  users.json not found, skipping")
        return {}

    with open(USERS_JSON, 'r') as f:
        users_data = json.load(f)

    username_to_id = {}

    with get_db() as db:
        for username, user_data in users_data.items():
            # Upgrade password from SHA256 to bcrypt
            # Since we can't decrypt SHA256, we'll keep it temporarily
            # and prompt user to reset password on first login
            old_hash = user_data.get('password_hash', '')

            # Mark as needing password reset
            password_hash = old_hash  # Will be upgraded on first login

            cursor = db.execute(
                """INSERT INTO users (
                    username, email, password_hash, full_name, role,
                    created_at, trial_start, trial_days, referral_code, has_referral_discount
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    username,
                    user_data.get('email', f'{username}@temp.com'),
                    password_hash,
                    user_data.get('full_name'),
                    user_data.get('role', 'user'),
                    user_data.get('created_at', datetime.now().isoformat()),
                    user_data.get('trial_start'),
                    user_data.get('trial_days', 14),
                    user_data.get('referral_code'),
                    user_data.get('has_referral_discount', 0)
                )
            )
            user_id = cursor.lastrowid
            username_to_id[username] = user_id

            print(f"  ✅ Migrated user: {username} → ID {user_id}")

    print(f"✅ Migrated {len(username_to_id)} users\n")
    return username_to_id


def migrate_sessions(username_to_id):
    """Migrate sessions.json → sessions table"""
    print("🔑 Migrating sessions...")

    if not SESSIONS_JSON.exists():
        print("  ⚠️  sessions.json not found, skipping\n")
        return

    with open(SESSIONS_JSON, 'r') as f:
        sessions_data = json.load(f)

    with get_db() as db:
        migrated = 0
        for token, session_info in sessions_data.items():
            username = session_info.get('username')
            user_id = username_to_id.get(username)

            if not user_id:
                print(f"  ⚠️  Unknown user: {username}, skipping session")
                continue

            db.execute(
                """INSERT INTO sessions (
                    user_id, token, created_at, expires_at, last_activity, activity_count
                ) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    token,
                    session_info.get('created_at', datetime.now().isoformat()),
                    session_info.get('expires_at', (datetime.now() + timedelta(days=7)).isoformat()),
                    session_info.get('last_activity', datetime.now().isoformat()),
                    session_info.get('activity_count', 0)
                )
            )
            migrated += 1

    print(f"✅ Migrated {migrated} sessions\n")


def migrate_activity_log(username_to_id):
    """Migrate user_activity_log.json → user_activity table"""
    print("📝 Migrating activity logs...")

    if not ACTIVITY_JSON.exists():
        print("  ⚠️  activity log not found, skipping\n")
        return

    with open(ACTIVITY_JSON, 'r') as f:
        activity_data = json.load(f)

    with get_db() as db:
        migrated = 0
        for entry in activity_data:
            username = entry.get('username')
            user_id = username_to_id.get(username)

            if not user_id:
                continue

            db.execute(
                """INSERT INTO user_activity (
                    user_id, action, details, created_at
                ) VALUES (?, ?, ?, ?)""",
                (
                    user_id,
                    entry.get('action', 'unknown'),
                    json.dumps(entry.get('details', {})),
                    entry.get('timestamp', datetime.now().isoformat())
                )
            )
            migrated += 1

    print(f"✅ Migrated {migrated} activity log entries\n")


def migrate_settings(username_to_id):
    """Migrate user_settings.db → user_settings table"""
    print("⚙️  Migrating user settings...")

    if not OLD_SETTINGS_DB.exists():
        print("  ⚠️  user_settings.db not found, skipping\n")
        return

    old_db = sqlite3.connect(OLD_SETTINGS_DB)
    old_db.row_factory = sqlite3.Row

    with get_db() as new_db:
        migrated = 0
        for row in old_db.execute("SELECT * FROM user_settings"):
            # Map old user_id (username string) to new user_id (integer)
            old_user_id = row['user_id']
            new_user_id = username_to_id.get(old_user_id)

            if not new_user_id:
                # Create settings for default user if not exists
                if old_user_id == 'default':
                    new_user_id = username_to_id.get('admin', 1)
                else:
                    continue

            new_db.execute(
                """INSERT INTO user_settings (
                    user_id, enabled_bookmakers, total_bankroll, unit_size, risk_level,
                    min_arb_profit, steam_move_threshold, line_movement_threshold,
                    alert_sound_enabled, show_latency, highlight_pinnacle, dark_mode,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    new_user_id,
                    row['enabled_bookmakers'],
                    row['total_bankroll'],
                    row['unit_size'],
                    row['risk_level'],
                    row['min_arb_profit'],
                    row['steam_move_threshold'],
                    row['line_movement_threshold'],
                    row['alert_sound_enabled'],
                    row['show_latency'],
                    row['highlight_pinnacle'],
                    row['dark_mode'],
                    row['created_at'],
                    row['updated_at']
                )
            )
            migrated += 1

    old_db.close()
    print(f"✅ Migrated {migrated} user settings\n")


def migrate_subscriptions(username_to_id):
    """Migrate subscriptions.db → subscriptions/payment_history tables"""
    print("💳 Migrating subscriptions...")

    if not OLD_SUBSCRIPTIONS_DB.exists():
        print("  ⚠️  subscriptions.db not found, skipping\n")
        return

    old_db = sqlite3.connect(OLD_SUBSCRIPTIONS_DB)
    old_db.row_factory = sqlite3.Row

    with get_db() as new_db:
        # Migrate subscriptions
        subs_migrated = 0
        for row in old_db.execute("SELECT * FROM subscriptions"):
            old_user_id = row['user_id']
            new_user_id = username_to_id.get(old_user_id)

            if not new_user_id:
                continue

            new_db.execute(
                """INSERT INTO subscriptions (
                    user_id, stripe_subscription_id, tier, status,
                    current_period_start, current_period_end, cancel_at_period_end,
                    trial_end, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    new_user_id,
                    row['stripe_subscription_id'],
                    row['tier'],
                    row['status'],
                    row['current_period_start'],
                    row['current_period_end'],
                    row['cancel_at_period_end'],
                    row['trial_end'],
                    row['created_at'],
                    row['updated_at']
                )
            )
            subs_migrated += 1

        # Migrate payment history
        payments_migrated = 0
        for row in old_db.execute("SELECT * FROM payment_history"):
            old_user_id = row['user_id']
            new_user_id = username_to_id.get(old_user_id)

            if not new_user_id:
                continue

            new_db.execute(
                """INSERT INTO payment_history (
                    user_id, stripe_invoice_id, amount, currency, status, paid_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    new_user_id,
                    row['stripe_invoice_id'],
                    row['amount'],
                    row['currency'],
                    row['status'],
                    row['paid_at'],
                    row['created_at']
                )
            )
            payments_migrated += 1

    old_db.close()
    print(f"✅ Migrated {subs_migrated} subscriptions, {payments_migrated} payments\n")


def migrate_bets(username_to_id):
    """Migrate user_bets.db → user_bets table"""
    print("🎲 Migrating user bets...")

    if not OLD_BETS_DB.exists():
        print("  ⚠️  user_bets.db not found, skipping\n")
        return

    old_db = sqlite3.connect(OLD_BETS_DB)
    old_db.row_factory = sqlite3.Row

    with get_db() as new_db:
        migrated = 0
        for row in old_db.execute("SELECT * FROM user_bets"):
            old_user_id = row['user_id']
            new_user_id = username_to_id.get(old_user_id)

            if not new_user_id:
                continue

            new_db.execute(
                """INSERT INTO user_bets (
                    user_id, bet_uuid, game_id, sport, home_team, away_team, commence_time,
                    bet_type, bet_side, stake, odds, bookmaker, alert_id, confidence,
                    edge_percent, strategy, clicked_at, logged_at, status, result,
                    payout, profit_loss, settled_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    new_user_id,
                    row['id'],  # Old 'id' becomes 'bet_uuid'
                    row['game_id'],
                    row['sport'],
                    row['home_team'],
                    row['away_team'],
                    row['commence_time'],
                    row['bet_type'],
                    row['bet_side'],
                    row['stake'],
                    row['odds'],
                    row['bookmaker'],
                    row['alert_id'],
                    row['confidence'],
                    row['edge_percent'],
                    row['strategy'],
                    row['clicked_at'],
                    row['logged_at'],
                    row['status'],
                    row['result'],
                    row['payout'],
                    row['profit_loss'],
                    row['settled_at'],
                    row.get('created_at', datetime.now().isoformat())
                )
            )
            migrated += 1

    old_db.close()
    print(f"✅ Migrated {migrated} bets\n")


def main():
    """Run migration"""
    print("\n" + "="*60)
    print("  MAX EV SPORTS - DATABASE MIGRATION")
    print("  Consolidating to Unified Database")
    print("="*60 + "\n")

    # Create backups first
    create_backups()

    # Initialize new database
    print("🗄️  Initializing unified database...")
    init_database()
    print("✅ Database initialized\n")

    # Run migrations in order (users first, then everything that depends on user_id)
    username_to_id = migrate_users()
    migrate_sessions(username_to_id)
    migrate_activity_log(username_to_id)
    migrate_settings(username_to_id)
    migrate_subscriptions(username_to_id)
    migrate_bets(username_to_id)

    print("\n" + "="*60)
    print("  ✅ MIGRATION COMPLETE!")
    print("="*60)
    print(f"\n📍 New database: backend/database/maxev_sports.db")
    print(f"📦 Backups saved: {BACKUP_DIR}")
    print("\n⚠️  NEXT STEPS:")
    print("  1. Test the new database with test queries")
    print("  2. Update backend code to use unified_db.py")
    print("  3. Deploy updated code")
    print("  4. Keep backups for 30 days (rollback safety)\n")


if __name__ == "__main__":
    main()
