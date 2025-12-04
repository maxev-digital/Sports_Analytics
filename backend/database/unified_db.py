"""
Unified Database Client for Max EV Sports
Replaces fragmented JSON/SQLite storage with single database
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent / "maxev_sports.db"
SCHEMA_PATH = Path(__file__).parent / "create_unified_schema.sql"


@contextmanager
def get_db():
    """Context manager for database connections with foreign keys enabled"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize database with schema"""
    logger.info(f"Initializing unified database at {DB_PATH}")

    # Create database directory if not exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Read and execute schema
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    with open(SCHEMA_PATH, 'r') as f:
        schema_sql = f.read()

    with get_db() as db:
        db.executescript(schema_sql)

    logger.info("✅ Unified database initialized successfully")


# ==================== USER OPERATIONS ====================

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None


def create_user(
    username: str,
    email: str,
    password_hash: str,
    full_name: str = None,
    role: str = 'user',
    **kwargs
) -> int:
    """
    Create new user and default settings
    Returns user_id
    """
    with get_db() as db:
        cursor = db.execute(
            """INSERT INTO users (
                username, email, password_hash, full_name, role,
                trial_start, trial_days, referral_code, has_referral_discount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                username,
                email,
                password_hash,
                full_name,
                role,
                kwargs.get('trial_start'),
                kwargs.get('trial_days', 14),
                kwargs.get('referral_code'),
                kwargs.get('has_referral_discount', 0)
            )
        )
        user_id = cursor.lastrowid

        # Create default settings
        db.execute(
            """INSERT INTO user_settings (user_id, enabled_bookmakers)
               VALUES (?, ?)""",
            (user_id, '["draftkings", "fanduel", "betmgm", "caesars", "pinnacle"]')
        )

        logger.info(f"Created user: {username} (ID: {user_id})")
        return user_id


def update_user_last_login(user_id: int):
    """Update user's last login timestamp"""
    with get_db() as db:
        db.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,)
        )


def get_all_users() -> List[Dict[str, Any]]:
    """Get all users"""
    with get_db() as db:
        rows = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]


# ==================== SESSION OPERATIONS ====================

def create_session(user_id: int, token: str, expires_at: str) -> int:
    """Create new session, returns session_id"""
    with get_db() as db:
        cursor = db.execute(
            """INSERT INTO sessions (user_id, token, expires_at, last_activity)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
            (user_id, token, expires_at)
        )
        return cursor.lastrowid


def get_session_by_token(token: str) -> Optional[Dict[str, Any]]:
    """Get session by token"""
    with get_db() as db:
        row = db.execute(
            """SELECT s.*, u.username
               FROM sessions s
               JOIN users u ON s.user_id = u.user_id
               WHERE s.token = ?""",
            (token,)
        ).fetchone()
        return dict(row) if row else None


def update_session_activity(token: str):
    """Update session last activity and increment count"""
    with get_db() as db:
        db.execute(
            """UPDATE sessions
               SET last_activity = CURRENT_TIMESTAMP,
                   activity_count = activity_count + 1
               WHERE token = ?""",
            (token,)
        )


def delete_session(token: str):
    """Delete session (logout)"""
    with get_db() as db:
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))


def delete_expired_sessions():
    """Clean up expired sessions"""
    with get_db() as db:
        cursor = db.execute(
            "DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP"
        )
        return cursor.rowcount


def get_active_sessions_for_user(user_id: int) -> List[Dict[str, Any]]:
    """Get all active sessions for a user"""
    with get_db() as db:
        rows = db.execute(
            """SELECT * FROM sessions
               WHERE user_id = ? AND expires_at > CURRENT_TIMESTAMP
               ORDER BY created_at DESC""",
            (user_id,)
        ).fetchall()
        return [dict(row) for row in rows]


# ==================== ACTIVITY LOG ====================

def log_user_activity(
    user_id: int,
    action: str,
    details: str = None,
    ip_address: str = None,
    user_agent: str = None
):
    """Log user activity"""
    with get_db() as db:
        db.execute(
            """INSERT INTO user_activity (user_id, action, details, ip_address, user_agent)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, action, details, ip_address, user_agent)
        )


def get_user_activity(user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Get user activity log"""
    with get_db() as db:
        rows = db.execute(
            """SELECT * FROM user_activity
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (user_id, limit)
        ).fetchall()
        return [dict(row) for row in rows]


# ==================== SETTINGS OPERATIONS ====================

def get_user_settings(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user settings"""
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM user_settings WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None


def update_user_settings(user_id: int, settings: Dict[str, Any]):
    """Update user settings"""
    with get_db() as db:
        # Build dynamic update query
        set_clauses = []
        params = []

        for key, value in settings.items():
            if key in ['enabled_bookmakers', 'total_bankroll', 'unit_size',
                       'risk_level', 'min_arb_profit', 'steam_move_threshold',
                       'line_movement_threshold', 'alert_sound_enabled',
                       'show_latency', 'highlight_pinnacle', 'dark_mode']:
                set_clauses.append(f"{key} = ?")
                params.append(value)

        if not set_clauses:
            return

        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)

        query = f"UPDATE user_settings SET {', '.join(set_clauses)} WHERE user_id = ?"
        db.execute(query, params)


# ==================== SUBSCRIPTION OPERATIONS ====================

def get_user_subscription(user_id: int) -> Optional[Dict[str, Any]]:
    """Get active subscription for user"""
    with get_db() as db:
        row = db.execute(
            """SELECT * FROM subscriptions
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT 1""",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None


def create_subscription(
    user_id: int,
    tier: str,
    status: str = 'active',
    stripe_subscription_id: str = None,
    **kwargs
) -> int:
    """Create subscription, returns subscription_id"""
    with get_db() as db:
        cursor = db.execute(
            """INSERT INTO subscriptions (
                user_id, stripe_subscription_id, tier, status,
                current_period_start, current_period_end, trial_end
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                stripe_subscription_id,
                tier,
                status,
                kwargs.get('current_period_start'),
                kwargs.get('current_period_end'),
                kwargs.get('trial_end')
            )
        )
        subscription_id = cursor.lastrowid

        # Log to history
        db.execute(
            """INSERT INTO subscription_history (
                user_id, subscription_id, event_type, tier, status
            ) VALUES (?, ?, ?, ?, ?)""",
            (user_id, subscription_id, 'subscription_created', tier, status)
        )

        return subscription_id


def update_subscription(subscription_id: int, **kwargs):
    """Update subscription"""
    with get_db() as db:
        set_clauses = []
        params = []

        for key, value in kwargs.items():
            if key in ['tier', 'status', 'current_period_start',
                       'current_period_end', 'cancel_at_period_end']:
                set_clauses.append(f"{key} = ?")
                params.append(value)

        if not set_clauses:
            return

        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(subscription_id)

        query = f"UPDATE subscriptions SET {', '.join(set_clauses)} WHERE subscription_id = ?"
        db.execute(query, params)


# Initialize database on module import
if __name__ == "__main__":
    init_database()
    print(f"✅ Database initialized at {DB_PATH}")
