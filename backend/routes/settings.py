"""
Settings API Routes
Handles user settings including bookmaker preferences, bankroll, and alerts
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
import logging
from settings_database import settings_db, BOOKMAKER_PRESETS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


class BookmakerUpdate(BaseModel):
    enabled_bookmakers: List[str]


class BankrollUpdate(BaseModel):
    total_bankroll: float
    unit_size: float
    risk_level: str


class AlertUpdate(BaseModel):
    min_arb_profit: float
    steam_move_threshold: float
    line_movement_threshold: float
    alert_sound_enabled: bool


class DisplayUpdate(BaseModel):
    show_latency: bool
    highlight_pinnacle: bool
    dark_mode: bool


class AllSettingsUpdate(BaseModel):
    enabled_bookmakers: List[str]
    total_bankroll: float = 10000.0
    unit_size: float = 100.0
    risk_level: str = "medium"
    min_arb_profit: float = 1.0
    steam_move_threshold: float = 5.0
    line_movement_threshold: float = 3.0
    alert_sound_enabled: bool = True
    show_latency: bool = True
    highlight_pinnacle: bool = True
    dark_mode: bool = True


@router.get("")
async def get_settings(user_id: str = Query("default")):
    """Get all settings for a user, creating defaults on first access."""
    try:
        settings = settings_db.get_settings(user_id)
        if not settings:
            logger.info(f"Creating default settings for new user: {user_id}")
            settings_db.reset_to_defaults(user_id)
            settings = settings_db.get_settings(user_id)
            if not settings:
                raise Exception(f"Failed to create settings for user {user_id}")
        return {"success": True, "settings": settings}
    except Exception as e:
        logger.error(f"Error fetching settings for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch settings: {str(e)}")


@router.put("")
async def update_all_settings(update: AllSettingsUpdate, user_id: str = Query("default")):
    """Update all settings at once."""
    try:
        success = settings_db.update_all_settings(update.dict(), user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User settings not found")
        return {"success": True, "settings": update.dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating all settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.put("/bookmakers")
async def update_bookmakers(update: BookmakerUpdate, user_id: str = Query("default")):
    """Update enabled bookmakers list."""
    try:
        success = settings_db.update_enabled_bookmakers(update.enabled_bookmakers, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "enabled_bookmakers": update.enabled_bookmakers}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bookmakers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/bankroll")
async def update_bankroll(update: BankrollUpdate, user_id: str = Query("default")):
    """Update bankroll management settings."""
    try:
        success = settings_db.update_bankroll_settings(
            update.total_bankroll, update.unit_size, update.risk_level, user_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "success": True,
            "bankroll": {
                "total_bankroll": update.total_bankroll,
                "unit_size": update.unit_size,
                "risk_level": update.risk_level,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bankroll: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/alerts")
async def update_alerts(update: AlertUpdate, user_id: str = Query("default")):
    """Update alert threshold settings."""
    try:
        success = settings_db.update_alert_settings(
            update.min_arb_profit,
            update.steam_move_threshold,
            update.line_movement_threshold,
            update.alert_sound_enabled,
            user_id,
        )
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "alerts": update.dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/display")
async def update_display(update: DisplayUpdate, user_id: str = Query("default")):
    """Update display preferences."""
    try:
        success = settings_db.update_display_settings(
            update.show_latency, update.highlight_pinnacle, update.dark_mode, user_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "display": update.dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating display: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_settings(user_id: str = Query("default")):
    """Reset all settings to defaults."""
    try:
        settings_db.reset_to_defaults(user_id)
        settings = settings_db.get_settings(user_id)
        return {"success": True, "settings": settings}
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/presets")
async def get_presets():
    """Get all predefined bookmaker presets."""
    return {"success": True, "presets": BOOKMAKER_PRESETS}


@router.put("/presets/{preset_name}")
async def apply_preset(preset_name: str, user_id: str = Query("default")):
    """Apply a bookmaker preset to user settings."""
    try:
        if preset_name not in BOOKMAKER_PRESETS:
            raise HTTPException(
                status_code=404,
                detail=f"Preset '{preset_name}' not found. Available: {list(BOOKMAKER_PRESETS.keys())}",
            )
        preset = BOOKMAKER_PRESETS[preset_name]
        success = settings_db.update_enabled_bookmakers(preset["bookmakers"], user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "success": True,
            "preset_name": preset_name,
            "enabled_bookmakers": preset["bookmakers"],
            "count": len(preset["bookmakers"]),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))
