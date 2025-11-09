"""API routes for system alert preferences"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import sys
from pathlib import Path

# Add parent directory to path to import storage module
sys.path.append(str(Path(__file__).parent.parent))

from storage.system_alert_preferences import system_alert_prefs

router = APIRouter(prefix="/api/alert-preferences", tags=["alert-preferences"])


# ========== REQUEST MODELS ==========

class EnableAlertRequest(BaseModel):
    """Request body for enabling system alerts"""
    system_id: int
    notification_method: str = 'in_app'  # 'in_app', 'email', 'sms', or 'all'
    min_strength: float = 50.0  # Minimum strength threshold (0-100)


class DisableAlertRequest(BaseModel):
    """Request body for disabling system alerts"""
    system_id: int


class ToggleAlertRequest(BaseModel):
    """Request body for toggling system alerts"""
    system_id: int


class UpdateNotificationMethodRequest(BaseModel):
    """Request body for updating notification method"""
    system_id: int
    notification_method: str


class UpdateMinStrengthRequest(BaseModel):
    """Request body for updating minimum strength threshold"""
    system_id: int
    min_strength: float


# ========== ROUTES ==========

@router.get("/{user_id}")
async def get_alert_preferences(user_id: str):
    """
    Get all alert preferences for a user

    Returns:
        {
            "user_id": str,
            "preferences": {
                system_id: {
                    "alerts_enabled": bool,
                    "notification_method": str,
                    "min_strength_threshold": float,
                    "enabled_at": str,
                    "updated_at": str
                }
            },
            "enabled_systems": [system_id_1, system_id_2, ...]
        }
    """
    try:
        all_prefs = system_alert_prefs.get_all_preferences(user_id)
        enabled_systems = system_alert_prefs.get_enabled_systems(user_id)

        return {
            "user_id": user_id,
            "preferences": all_prefs,
            "enabled_systems": enabled_systems
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch preferences: {str(e)}")


@router.get("/{user_id}/system/{system_id}")
async def get_system_preference(user_id: str, system_id: int):
    """
    Get alert preferences for a specific system

    Returns:
        {
            "user_id": str,
            "system_id": int,
            "preferences": {
                "alerts_enabled": bool,
                "notification_method": str,
                "min_strength_threshold": float,
                "enabled_at": str,
                "updated_at": str
            } or null if not configured
        }
    """
    try:
        prefs = system_alert_prefs.get_system_preferences(user_id, system_id)

        return {
            "user_id": user_id,
            "system_id": system_id,
            "preferences": prefs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch system preferences: {str(e)}")


@router.post("/{user_id}/enable")
async def enable_system_alerts(user_id: str, request: EnableAlertRequest):
    """
    Enable alerts for a specific system

    Request body:
        {
            "system_id": int,
            "notification_method": str (optional, default: "in_app"),
            "min_strength": float (optional, default: 50.0)
        }

    Returns:
        {
            "success": bool,
            "message": str,
            "system_id": int,
            "alerts_enabled": true
        }
    """
    try:
        # Validate notification method
        valid_methods = ['in_app', 'email', 'sms', 'all']
        if request.notification_method not in valid_methods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid notification method. Must be one of: {', '.join(valid_methods)}"
            )

        # Validate min_strength
        if not 0 <= request.min_strength <= 100:
            raise HTTPException(
                status_code=400,
                detail="min_strength must be between 0 and 100"
            )

        success = system_alert_prefs.enable_system_alerts(
            user_id=user_id,
            system_id=request.system_id,
            notification_method=request.notification_method,
            min_strength=request.min_strength
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to enable system alerts")

        return {
            "success": True,
            "message": f"Alerts enabled for system {request.system_id}",
            "system_id": request.system_id,
            "alerts_enabled": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable alerts: {str(e)}")


@router.post("/{user_id}/disable")
async def disable_system_alerts(user_id: str, request: DisableAlertRequest):
    """
    Disable alerts for a specific system

    Request body:
        {
            "system_id": int
        }

    Returns:
        {
            "success": bool,
            "message": str,
            "system_id": int,
            "alerts_enabled": false
        }
    """
    try:
        success = system_alert_prefs.disable_system_alerts(
            user_id=user_id,
            system_id=request.system_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="System alerts not found or already disabled")

        return {
            "success": True,
            "message": f"Alerts disabled for system {request.system_id}",
            "system_id": request.system_id,
            "alerts_enabled": False
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable alerts: {str(e)}")


@router.post("/{user_id}/toggle")
async def toggle_system_alerts(user_id: str, request: ToggleAlertRequest):
    """
    Toggle alerts for a specific system (enable if disabled, disable if enabled)

    Request body:
        {
            "system_id": int
        }

    Returns:
        {
            "success": bool,
            "message": str,
            "system_id": int,
            "alerts_enabled": bool (new state)
        }
    """
    try:
        success, new_state = system_alert_prefs.toggle_system_alerts(
            user_id=user_id,
            system_id=request.system_id
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to toggle system alerts")

        action = "enabled" if new_state else "disabled"
        return {
            "success": True,
            "message": f"Alerts {action} for system {request.system_id}",
            "system_id": request.system_id,
            "alerts_enabled": new_state
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle alerts: {str(e)}")


@router.post("/{user_id}/update-notification-method")
async def update_notification_method(user_id: str, request: UpdateNotificationMethodRequest):
    """
    Update notification method for a system

    Request body:
        {
            "system_id": int,
            "notification_method": str ('in_app', 'email', 'sms', 'all')
        }

    Returns:
        {
            "success": bool,
            "message": str
        }
    """
    try:
        # Validate notification method
        valid_methods = ['in_app', 'email', 'sms', 'all']
        if request.notification_method not in valid_methods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid notification method. Must be one of: {', '.join(valid_methods)}"
            )

        success = system_alert_prefs.update_notification_method(
            user_id=user_id,
            system_id=request.system_id,
            method=request.notification_method
        )

        if not success:
            raise HTTPException(status_code=404, detail="System preferences not found")

        return {
            "success": True,
            "message": f"Notification method updated to {request.notification_method}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update notification method: {str(e)}")


@router.post("/{user_id}/update-min-strength")
async def update_min_strength(user_id: str, request: UpdateMinStrengthRequest):
    """
    Update minimum strength threshold for alerts

    Request body:
        {
            "system_id": int,
            "min_strength": float (0-100)
        }

    Returns:
        {
            "success": bool,
            "message": str
        }
    """
    try:
        # Validate min_strength
        if not 0 <= request.min_strength <= 100:
            raise HTTPException(
                status_code=400,
                detail="min_strength must be between 0 and 100"
            )

        success = system_alert_prefs.update_min_strength(
            user_id=user_id,
            system_id=request.system_id,
            min_strength=request.min_strength
        )

        if not success:
            raise HTTPException(status_code=404, detail="System preferences not found")

        return {
            "success": True,
            "message": f"Minimum strength threshold updated to {request.min_strength}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update min strength: {str(e)}")


@router.get("/{user_id}/should-alert/{system_id}")
async def should_send_alert(user_id: str, system_id: int, strength: float):
    """
    Check if an alert should be sent for this system based on strength

    Query params:
        strength: float (0-100 scale)

    Returns:
        {
            "should_send": bool,
            "notification_method": str or null
        }
    """
    try:
        should_send, method = system_alert_prefs.should_send_alert(
            user_id=user_id,
            system_id=system_id,
            strength=strength
        )

        return {
            "should_send": should_send,
            "notification_method": method
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check alert status: {str(e)}")
