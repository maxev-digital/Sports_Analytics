"""
Shared application state — singletons initialized at startup and imported by routers.

Routers import from this module to access tracker, ws_manager, etc. without
circular imports or re-creating instances.
"""
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from game_tracker import GameTracker
    from strategies.sharp_money_monitor_service import SharpMoneyService
    from strategies.schedule_fatigue_service import FatigueService

# These are populated by main.py during startup before any request is handled.
tracker: Optional["GameTracker"] = None
ws_manager = None  # ConnectionManager — defined in routes/games.py to avoid circular imports
alert_monitor = None  # AlertMonitor instance
sharp_money_service: Optional["SharpMoneyService"] = None
fatigue_service: Optional["FatigueService"] = None

# Props cache — populated and refreshed by main.py background task; read by routes/misc.py
props_cache: dict = {
    "nba":   {"props": [], "count": 0, "last_updated": None},
    "nfl":   {"props": [], "count": 0, "last_updated": None},
    "nhl":   {"props": [], "count": 0, "last_updated": None},
    "mlb":   {"props": [], "count": 0, "last_updated": None},
    "ncaab": {"props": [], "count": 0, "last_updated": None},
    "ncaaf": {"props": [], "count": 0, "last_updated": None},
}
