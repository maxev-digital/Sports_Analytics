"""Admin routes — user management, sessions, activity logs"""
from fastapi import APIRouter, HTTPException
import logging

import auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _require_admin(token: str) -> str:
    """Verify token and assert admin role. Returns username or raises."""
    username = auth.verify_session(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    users = auth.load_users()
    if users.get(username, {}).get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return username


@router.get("/users")
async def get_all_users(token: str):
    """Get list of all users (admin only)."""
    try:
        _require_admin(token)
        users_list = auth.get_all_users_list()
        return {"count": len(users_list), "users": users_list}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve users")


@router.get("/active-sessions")
async def get_active_sessions(token: str):
    """Get all active sessions (admin only)."""
    try:
        _require_admin(token)
        sessions = auth.get_active_sessions()
        return {"count": len(sessions), "sessions": sessions}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")


@router.get("/activity-log")
async def get_activity_log(token: str, username: str = None, limit: int = 100):
    """Get user activity log (admin only)."""
    try:
        _require_admin(token)
        activity = auth.get_user_activity(username, limit)
        return {
            "count": len(activity),
            "activity": activity,
            "filtered_by": username if username else "all users"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get activity log error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve activity log")


@router.get("/user-stats/{username}")
async def get_user_stats(username: str, token: str):
    """Get statistics for a specific user (admin only)."""
    try:
        _require_admin(token)
        stats = auth.get_user_statistics(username)
        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user statistics")


@router.get("/all-user-stats")
async def get_all_user_stats(token: str):
    """Get statistics for all users (admin only)."""
    try:
        _require_admin(token)
        users_list = auth.get_all_users_list()
        all_stats = [auth.get_user_statistics(u["username"]) for u in users_list]
        return {"count": len(all_stats), "statistics": all_stats}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get all user stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
