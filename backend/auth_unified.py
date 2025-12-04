"""
Authentication Module - Unified Database + Bcrypt
Replaces auth.py with secure password hashing and unified database
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

# Install bcrypt if not available
try:
    import bcrypt
except ImportError:
    logger.error("bcrypt not installed. Run: pip install bcrypt")
    raise

from database.unified_db import (
    get_user_by_username,
    get_user_by_email,
    create_user as db_create_user,
    update_user_last_login,
    get_user_by_id,
    create_session as db_create_session,
    get_session_by_token,
    update_session_activity,
    delete_session as db_delete_session,
    delete_expired_sessions,
    log_user_activity as db_log_activity,
    get_user_activity as db_get_activity
)


# ==================== PASSWORD HASHING ====================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with salt
    Returns base64-encoded hash string
    """
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds = good security/performance balance
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')


def verify_password(username: str, password: str) -> bool:
    """
    Verify password for a user
    Handles both old SHA256 hashes (migration) and new bcrypt hashes
    """
    user = get_user_by_username(username)
    if not user:
        return False

    stored_hash = user['password_hash']

    # Check if this is an old SHA256 hash (64 hex chars)
    if len(stored_hash) == 64 and all(c in '0123456789abcdef' for c in stored_hash):
        # OLD SHA256 HASH - verify using old method
        import hashlib
        test_hash = hashlib.sha256(password.encode()).hexdigest()
        if test_hash == stored_hash:
            # Password correct - upgrade to bcrypt automatically
            logger.info(f"Upgrading password hash for user: {username}")
            new_hash = hash_password(password)

            # Update database with new hash
            from database.unified_db import get_db
            with get_db() as db:
                db.execute(
                    "UPDATE users SET password_hash = ? WHERE username = ?",
                    (new_hash, username)
                )

            return True
        return False

    # NEW BCRYPT HASH - verify normally
    try:
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error for {username}: {e}")
        return False


# ==================== SESSION MANAGEMENT ====================

def create_session(username: str, ip_address: str = None, user_agent: str = None) -> str:
    """
    Create a new session for a user
    Returns session token
    """
    user = get_user_by_username(username)
    if not user:
        raise ValueError(f"User not found: {username}")

    user_id = user['user_id']

    # Generate secure token
    token = secrets.token_urlsafe(32)

    # 7 day expiration
    expires_at = (datetime.now() + timedelta(days=7)).isoformat()

    # Create session in database
    db_create_session(user_id, token, expires_at)

    # Update last login
    update_user_last_login(user_id)

    # Log login event
    log_user_activity(user_id, "login", {"token_preview": token[:8] + "..."}, ip_address, user_agent)

    logger.info(f"Session created for {username} (expires in 7 days)")
    return token


def verify_session(token: str) -> Optional[str]:
    """
    Verify a session token
    Returns username if valid, None if invalid/expired
    Also updates last_activity timestamp
    """
    session = get_session_by_token(token)
    if not session:
        return None

    # Check if expired
    expires_at = datetime.fromisoformat(session['expires_at'])
    if datetime.now() > expires_at:
        logger.info(f"Session expired for {session['username']}")
        # Clean up expired session
        delete_session(token)
        return None

    # Update activity
    update_session_activity(token)

    return session['username']


def delete_session(token: str):
    """
    Delete a session (logout)
    Logs logout event with session duration
    """
    session = get_session_by_token(token)
    if session:
        user_id = session['user_id']
        created_at = datetime.fromisoformat(session['created_at'])
        duration = (datetime.now() - created_at).total_seconds()

        # Log logout
        log_user_activity(
            user_id,
            "logout",
            {
                "duration_seconds": duration,
                "duration_formatted": format_duration(duration),
                "activity_count": session.get('activity_count', 0)
            }
        )

    db_delete_session(token)


def cleanup_expired_sessions():
    """Clean up expired sessions (call this periodically)"""
    count = delete_expired_sessions()
    if count > 0:
        logger.info(f"Cleaned up {count} expired sessions")
    return count


# ==================== USER MANAGEMENT ====================

def add_user(
    username: str,
    email: str,
    password: str,
    full_name: str = None,
    role: str = 'user',
    **kwargs
) -> int:
    """
    Create a new user
    Returns user_id
    """
    # Check if username already exists
    if get_user_by_username(username):
        raise ValueError(f"Username already exists: {username}")

    # Check if email already exists
    if get_user_by_email(email):
        raise ValueError(f"Email already exists: {email}")

    # Hash password with bcrypt
    password_hash = hash_password(password)

    # Create user
    user_id = db_create_user(
        username=username,
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        role=role,
        **kwargs
    )

    logger.info(f"User created: {username} (ID: {user_id})")
    return user_id


def change_password(username: str, old_password: str, new_password: str) -> bool:
    """Change user password"""
    if not verify_password(username, old_password):
        return False

    user = get_user_by_username(username)
    if not user:
        return False

    new_hash = hash_password(new_password)

    from database.unified_db import get_db
    with get_db() as db:
        db.execute(
            "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
            (new_hash, username)
        )

    # Log password change
    log_user_activity(user['user_id'], "password_changed", {})

    logger.info(f"Password changed for user: {username}")
    return True


# ==================== ACTIVITY LOGGING ====================

def log_user_activity(
    user_id: int,
    action: str,
    details: dict = None,
    ip_address: str = None,
    user_agent: str = None
):
    """Log user activity"""
    import json
    details_json = json.dumps(details) if details else None
    db_log_activity(user_id, action, details_json, ip_address, user_agent)


def get_user_activity(username: str, limit: int = 100) -> List[dict]:
    """Get activity log for a user"""
    user = get_user_by_username(username)
    if not user:
        return []

    return db_get_activity(user['user_id'], limit)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


# ==================== UTILITY FUNCTIONS ====================

def get_all_users_list() -> List[dict]:
    """Get list of all users"""
    from database.unified_db import get_all_users
    return get_all_users()


def get_user_statistics(username: str) -> dict:
    """Get statistics for a user"""
    user = get_user_by_username(username)
    if not user:
        return {}

    activities = get_user_activity(username, limit=10000)

    logins = [a for a in activities if a['action'] == 'login']
    logouts = [a for a in activities if a['action'] == 'logout']

    total_duration = 0
    for logout in logouts:
        try:
            import json
            details = json.loads(logout.get('details', '{}'))
            total_duration += details.get('duration_seconds', 0)
        except:
            pass

    return {
        "username": username,
        "total_logins": len(logins),
        "total_logouts": len(logouts),
        "total_session_time_seconds": total_duration,
        "total_session_time_formatted": format_duration(total_duration),
        "average_session_duration": format_duration(total_duration / len(logouts)) if logouts else "N/A",
        "last_login": logins[0]['created_at'] if logins else None,
        "last_logout": logouts[0]['created_at'] if logouts else None
    }


def get_active_sessions() -> List[dict]:
    """Get all currently active sessions"""
    from database.unified_db import get_db

    with get_db() as db:
        rows = db.execute(
            """SELECT s.*, u.username
               FROM sessions s
               JOIN users u ON s.user_id = u.user_id
               WHERE s.expires_at > CURRENT_TIMESTAMP
               ORDER BY s.created_at DESC"""
        ).fetchall()

        active = []
        for row in rows:
            created_at = datetime.fromisoformat(row['created_at'])
            duration = (datetime.now() - created_at).total_seconds()

            active.append({
                "username": row['username'],
                "login_time": row['created_at'],
                "last_activity": row['last_activity'],
                "duration_seconds": duration,
                "duration_formatted": format_duration(duration),
                "activity_count": row['activity_count'],
                "token_preview": row['token'][:8] + "..."
            })

        return active
