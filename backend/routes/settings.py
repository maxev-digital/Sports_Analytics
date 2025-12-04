"""
Settings API Routes
Handles user settings including bookmaker preferences, bankroll, and alerts
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import json
from datetime import datetime
from settings_database import settings_db, BOOKMAKER_PRESETS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

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

def create_user_settings(user_id: str):
    """Create default settings for a new user"""
    # Default bookmakers (popular US books)
    default_bookmakers = [
        'draftkings', 'fanduel', 'betmgm', 'caesars', 'betrivers',
        'pointsbet', 'williamhill_us', 'fanatics', 'espnbet',
        'betonlineag', 'bovada', 'pinnacle'
    ]

    with settings_db.get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO user_settings (
                user_id, enabled_bookmakers, total_bankroll, unit_size,
                risk_level, min_arb_profit, steam_move_threshold,
                line_movement_threshold, alert_sound_enabled,
                show_latency, highlight_pinnacle, dark_mode,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            json.dumps(default_bookmakers),
            10000.0,
            100.0,
            'medium',
            1.0,
            5.0,
            3.0,
            1,
            1,
            1,
            1,
            now,
            now
        ))

@router.get("")
async def get_settings(user_id: str = Query("default")):
    """Get all settings for a user"""
    try:
        settings = settings_db.get_settings(user_id)

        if not settings:
            # Create default settings for new user
            logger.info(f"Creating default settings for new user: {user_id}")
            create_user_settings(user_id)
            settings = settings_db.get_settings(user_id)

            if not settings:
                raise Exception(f"Failed to create settings for user {user_id}")

        return {
            "success": True,
            "settings": settings
        }
    except Exception as e:
        logger.error(f"Error fetching settings for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch settings: {str(e)}")

@router.put("/bookmakers")
async def update_bookmakers(
    update: BookmakerUpdate,
    user_id: str = Query("default")
):
    """Update enabled bookmakers"""
    try:
        success = settings_db.update_enabled_bookmakers(
            update.enabled_bookmakers,
            user_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "success": True,
            "enabled_bookmakers": update.enabled_bookmakers
        }
    except Exception as e:
        logger.error(f"Error updating bookmakers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/bankroll")
async def update_bankroll(
    update: BankrollUpdate,
    user_id: str = Query("default")
):
    """Update bankroll settings"""
    try:
        success = settings_db.update_bankroll_settings(
            update.total_bankroll,
            update.unit_size,
            update.risk_level,
            user_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "success": True,
            "bankroll": {
                "total_bankroll": update.total_bankroll,
                "unit_size": update.unit_size,
                "risk_level": update.risk_level
            }
        }
    except Exception as e:
        logger.error(f"Error updating bankroll: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/alerts")
async def update_alerts(
    update: AlertUpdate,
    user_id: str = Query("default")
):
    """Update alert settings"""
    try:
        success = settings_db.update_alert_settings(
            update.min_arb_profit,
            update.steam_move_threshold,
            update.line_movement_threshold,
            update.alert_sound_enabled,
            user_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "success": True,
            "alerts": update.dict()
        }
    except Exception as e:
        logger.error(f"Error updating alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/display")
async def update_display(
    update: DisplayUpdate,
    user_id: str = Query("default")
):
    """Update display settings"""
    try:
        success = settings_db.update_display_settings(
            update.show_latency,
            update.highlight_pinnacle,
            update.dark_mode,
            user_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "success": True,
            "display": update.dict()
        }
    except Exception as e:
        logger.error(f"Error updating display: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
async def reset_settings(user_id: str = Query("default")):
    """Reset settings to defaults"""
    try:
        # Delete existing settings
        with settings_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))

        # Create new default settings
        create_user_settings(user_id)
        settings = settings_db.get_settings(user_id)

        return {
            "success": True,
            "settings": settings
        }
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presets")
async def get_presets():
    """Get predefined bookmaker presets"""
    return {
        "success": True,
        "presets": BOOKMAKER_PRESETS
    }

@router.post("/presets/{preset_key}")
async def apply_preset(
    preset_key: str,
    user_id: str = Query("default")
):
    """Apply a bookmaker preset"""
    try:
        if preset_key not in BOOKMAKER_PRESETS:
            raise HTTPException(status_code=404, detail="Preset not found")

        preset = BOOKMAKER_PRESETS[preset_key]
        success = settings_db.update_enabled_bookmakers(
            preset["bookmakers"],
            user_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "success": True,
            "preset": preset,
            "enabled_bookmakers": preset["bookmakers"]
        }
    except Exception as e:
        logger.error(f"Error applying preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))
