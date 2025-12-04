"""
Promo Code System
Manages promotional codes for special offers and beta campaigns
"""

from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Active promo codes configuration
PROMO_CODES = {
    "SPLASH": {
        "description": "Contest promotion - 2 months free access",
        "bonus_days": 60,  # 2 months = 60 days
        "active": True,
        "expires": None,  # No expiration
        "usage_limit": None,  # Unlimited uses during beta
        "tier_override": None,  # Uses default trial tier
    },
    # Add more promo codes here as needed
}


def validate_promo_code(code: str) -> Dict[str, Any]:
    """
    Validate a promo code

    Args:
        code: Promo code to validate (case-insensitive)

    Returns:
        dict: Validation result with 'valid', 'message', and optionally 'promo_data'
    """
    code_upper = code.strip().upper()

    if code_upper not in PROMO_CODES:
        return {
            "valid": False,
            "message": "Invalid promo code"
        }

    promo = PROMO_CODES[code_upper]

    # Check if promo is active
    if not promo.get("active", True):
        return {
            "valid": False,
            "message": "This promo code is no longer active"
        }

    # Check expiration
    if promo.get("expires"):
        try:
            expires_date = datetime.fromisoformat(promo["expires"])
            if datetime.now() > expires_date:
                return {
                    "valid": False,
                    "message": "This promo code has expired"
                }
        except Exception as e:
            logger.error(f"Error parsing expiration date: {e}")

    # Check usage limit (if tracked - for future implementation)
    # For now, unlimited during beta

    # Valid promo code
    bonus_days = promo.get("bonus_days", 0)
    description = promo.get("description", "Special promotion")

    if bonus_days > 0:
        months = bonus_days // 30
        if months > 0:
            time_desc = f"{months} month{'s' if months > 1 else ''}"
        else:
            time_desc = f"{bonus_days} days"
        message = f"✅ {time_desc} free access! ({description})"
    else:
        message = f"✅ {description}"

    return {
        "valid": True,
        "message": message,
        "promo_data": {
            "code": code_upper,
            "bonus_days": bonus_days,
            "description": description,
            "tier_override": promo.get("tier_override")
        }
    }


def apply_promo_code(code: str, username: str) -> Optional[Dict[str, Any]]:
    """
    Apply a promo code to a user account

    Args:
        code: Promo code to apply
        username: Username to apply code to

    Returns:
        dict: Promo data if valid, None if invalid
    """
    validation = validate_promo_code(code)

    if not validation["valid"]:
        logger.warning(f"Invalid promo code attempted by {username}: {code}")
        return None

    promo_data = validation["promo_data"]
    logger.info(f"Promo code {code} applied to user {username}: {promo_data['description']}")

    # Future: Track usage in database for analytics
    # For now, just return the promo data

    return promo_data


def get_active_promos() -> Dict[str, Dict[str, Any]]:
    """Get all currently active promo codes (for admin dashboard)"""
    return {
        code: data
        for code, data in PROMO_CODES.items()
        if data.get("active", True)
    }


def add_promo_code(
    code: str,
    description: str,
    bonus_days: int = 0,
    expires: Optional[str] = None,
    usage_limit: Optional[int] = None,
    tier_override: Optional[str] = None
) -> bool:
    """
    Add a new promo code (runtime only - not persisted to file)

    For permanent codes, add them directly to PROMO_CODES dict above
    """
    code_upper = code.strip().upper()

    if code_upper in PROMO_CODES:
        logger.warning(f"Promo code {code_upper} already exists")
        return False

    PROMO_CODES[code_upper] = {
        "description": description,
        "bonus_days": bonus_days,
        "active": True,
        "expires": expires,
        "usage_limit": usage_limit,
        "tier_override": tier_override
    }

    logger.info(f"Added promo code {code_upper}: {description}")
    return True


def deactivate_promo_code(code: str) -> bool:
    """Deactivate a promo code"""
    code_upper = code.strip().upper()

    if code_upper not in PROMO_CODES:
        return False

    PROMO_CODES[code_upper]["active"] = False
    logger.info(f"Deactivated promo code {code_upper}")
    return True
