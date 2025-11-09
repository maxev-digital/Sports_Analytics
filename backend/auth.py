"""Authentication module for user management with session tracking"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import hashlib
import json
from pathlib import Path

# Session storage (persisted to file)
sessions: Dict[str, dict] = {}
users_file = Path("users.json")
activity_log_file = Path("user_activity_log.json")
sessions_file = Path("sessions.json")

# Default users - 4 accounts + admin
DEFAULT_USERS = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "created_at": datetime.now().isoformat(),
        "role": "admin",
        "email": "admin@max-ev-sports.com"
    },
    "user1": {
        "password_hash": hashlib.sha256("SportTrader1!".encode()).hexdigest(),
        "created_at": datetime.now().isoformat(),
        "role": "user",
        "email": "user1@max-ev-sports.com"
    },
    "user2": {
        "password_hash": hashlib.sha256("SportTrader2!".encode()).hexdigest(),
        "created_at": datetime.now().isoformat(),
        "role": "user",
        "email": "user2@max-ev-sports.com"
    },
    "user3": {
        "password_hash": hashlib.sha256("SportTrader3!".encode()).hexdigest(),
        "created_at": datetime.now().isoformat(),
        "role": "user",
        "email": "user3@max-ev-sports.com"
    },
    "user4": {
        "password_hash": hashlib.sha256("SportTrader4!".encode()).hexdigest(),
        "created_at": datetime.now().isoformat(),
        "role": "user",
        "email": "user4@max-ev-sports.com"
    }
}

def load_users():
    """Load users from file"""
    if users_file.exists():
        with open(users_file, 'r') as f:
            return json.load(f)
    else:
        # Create default users file
        save_users(DEFAULT_USERS)
        return DEFAULT_USERS

def save_users(users: dict):
    """Save users to file"""
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)

def load_sessions():
    """Load sessions from file"""
    global sessions
    if sessions_file.exists():
        try:
            with open(sessions_file, 'r') as f:
                data = json.load(f)
                # Convert ISO strings back to datetime objects
                for token, session in data.items():
                    session['created_at'] = datetime.fromisoformat(session['created_at'])
                    session['expires_at'] = datetime.fromisoformat(session['expires_at'])
                    session['last_activity'] = datetime.fromisoformat(session['last_activity'])
                sessions = data
                print(f"[AUTH] Loaded {len(sessions)} sessions from file")
        except Exception as e:
            print(f"[AUTH] Error loading sessions: {e}")
            sessions = {}
    else:
        sessions = {}

def save_sessions():
    """Save sessions to file"""
    try:
        # Convert datetime objects to ISO strings for JSON serialization
        serializable_sessions = {}
        for token, session in sessions.items():
            serializable_sessions[token] = {
                'username': session['username'],
                'created_at': session['created_at'].isoformat(),
                'expires_at': session['expires_at'].isoformat(),
                'last_activity': session['last_activity'].isoformat(),
                'activity_count': session.get('activity_count', 0)
            }
        with open(sessions_file, 'w') as f:
            json.dump(serializable_sessions, f, indent=2)
    except Exception as e:
        print(f"[AUTH] Error saving sessions: {e}")

def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(username: str, password: str) -> bool:
    """Verify username and password"""
    users = load_users()
    if username not in users:
        return False

    password_hash = hash_password(password)
    return users[username]["password_hash"] == password_hash

def create_session(username: str) -> str:
    """Create a new session for a user and log the login"""
    token = secrets.token_urlsafe(32)
    login_time = datetime.now()
    sessions[token] = {
        "username": username,
        "created_at": login_time,
        "expires_at": login_time + timedelta(days=7),  # 7 day expiration
        "last_activity": login_time,
        "activity_count": 0
    }

    # Log the login event
    log_user_activity(username, "login", {"token": token[:8] + "..."})

    # Persist sessions to file
    save_sessions()

    return token

def verify_session(token: str) -> Optional[str]:
    """Verify a session token and return username if valid"""
    if token not in sessions:
        return None

    session = sessions[token]
    if datetime.now() > session["expires_at"]:
        # Session expired
        username = session["username"]
        duration = (datetime.now() - session["created_at"]).total_seconds()
        log_user_activity(username, "session_expired", {
            "duration_seconds": duration,
            "activity_count": session.get("activity_count", 0)
        })
        del sessions[token]
        save_sessions()  # Persist deletion
        return None

    # Update last activity time
    session["last_activity"] = datetime.now()
    session["activity_count"] = session.get("activity_count", 0) + 1

    # Persist activity update (only save occasionally to reduce I/O)
    if session["activity_count"] % 10 == 0:  # Save every 10 activities
        save_sessions()

    return session["username"]

def delete_session(token: str):
    """Delete a session (logout) and log the event"""
    if token in sessions:
        session = sessions[token]
        username = session["username"]
        duration = (datetime.now() - session["created_at"]).total_seconds()

        # Log logout event with session duration
        log_user_activity(username, "logout", {
            "duration_seconds": duration,
            "duration_formatted": format_duration(duration),
            "activity_count": session.get("activity_count", 0)
        })

        del sessions[token]

        # Persist session deletion
        save_sessions()

def add_user(username: str, password: str) -> bool:
    """Add a new user"""
    users = load_users()
    if username in users:
        return False

    users[username] = {
        "password_hash": hash_password(password),
        "created_at": datetime.now().isoformat()
    }
    save_users(users)
    return True

def change_password(username: str, old_password: str, new_password: str) -> bool:
    """Change user password"""
    if not verify_password(username, old_password):
        return False

    users = load_users()
    users[username]["password_hash"] = hash_password(new_password)
    save_users(users)

    # Log password change
    log_user_activity(username, "password_changed", {})

    return True

# ========== ACTIVITY LOGGING FUNCTIONS ==========

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

def load_activity_log() -> List[dict]:
    """Load activity log from file"""
    if activity_log_file.exists():
        with open(activity_log_file, 'r') as f:
            return json.load(f)
    return []

def save_activity_log(log: List[dict]):
    """Save activity log to file"""
    with open(activity_log_file, 'w') as f:
        json.dump(log, f, indent=2)

def log_user_activity(username: str, action: str, details: dict):
    """Log user activity with timestamp"""
    log = load_activity_log()

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "username": username,
        "action": action,
        "details": details
    }

    log.append(log_entry)

    # Keep only last 10,000 entries to prevent file from growing too large
    if len(log) > 10000:
        log = log[-10000:]

    save_activity_log(log)

def get_user_activity(username: Optional[str] = None, limit: int = 100) -> List[dict]:
    """Get activity log for a specific user or all users"""
    log = load_activity_log()

    if username:
        # Filter by username
        log = [entry for entry in log if entry["username"] == username]

    # Return most recent entries
    return log[-limit:][::-1]  # Reverse to show newest first

def get_active_sessions() -> List[dict]:
    """Get all currently active sessions"""
    active = []
    now = datetime.now()

    for token, session in sessions.items():
        if now < session["expires_at"]:
            duration = (now - session["created_at"]).total_seconds()
            active.append({
                "username": session["username"],
                "login_time": session["created_at"].isoformat(),
                "last_activity": session["last_activity"].isoformat(),
                "duration_seconds": duration,
                "duration_formatted": format_duration(duration),
                "activity_count": session.get("activity_count", 0),
                "token_preview": token[:8] + "..."
            })

    return active

def get_user_statistics(username: str) -> dict:
    """Get statistics for a specific user"""
    log = load_activity_log()
    user_log = [entry for entry in log if entry["username"] == username]

    logins = [entry for entry in user_log if entry["action"] == "login"]
    logouts = [entry for entry in user_log if entry["action"] == "logout"]

    total_duration = sum(
        entry["details"].get("duration_seconds", 0)
        for entry in logouts
    )

    return {
        "username": username,
        "total_logins": len(logins),
        "total_logouts": len(logouts),
        "total_session_time_seconds": total_duration,
        "total_session_time_formatted": format_duration(total_duration),
        "average_session_duration": format_duration(total_duration / len(logouts)) if logouts else "N/A",
        "last_login": logins[-1]["timestamp"] if logins else None,
        "last_logout": logouts[-1]["timestamp"] if logouts else None
    }

def get_all_users_list() -> List[dict]:
    """Get list of all users with their info"""
    users = load_users()
    return [
        {
            "username": username,
            "role": user_data.get("role", "user"),
            "email": user_data.get("email", ""),
            "created_at": user_data.get("created_at", "")
        }
        for username, user_data in users.items()
    ]

# Load sessions on module import
load_sessions()
