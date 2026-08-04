"""
Games routes — HTTP game endpoints + WebSocket live-odds connection.

ConnectionManager lives here so app_state can hold a reference without
creating circular imports through main.py.
"""
import json
import logging
import subprocess
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

import app_state
from settings_database import settings_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["games"])


# ========== WEBSOCKET CONNECTION MANAGER ==========

class ConnectionManager:
    """Manages WebSocket connections for real-time game updates."""

    def __init__(self):
        self.active_connections: Dict[WebSocket, str] = {}
        self.unfiltered_game_data: Optional[List[dict]] = None

    async def connect(self, websocket: WebSocket, user_id: str = 'default'):
        await websocket.accept()
        self.active_connections[websocket] = user_id
        logger.info(f"WebSocket connected for user {user_id}. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            user_id = self.active_connections.pop(websocket)
            logger.info(f"WebSocket disconnected for user {user_id}. Total: {len(self.active_connections)}")

    def _filter_games_for_user(self, games_data: List[dict], user_id: str) -> List[dict]:
        """Filter game odds to user's enabled bookmakers."""
        import re
        from settings_database import SettingsDatabase

        db = SettingsDatabase()
        settings = db.get_settings(user_id)
        if not settings:
            return games_data

        enabled_bookmakers = set(settings.get('enabled_bookmakers', []))
        if not enabled_bookmakers:
            return [{**game, 'odds': []} for game in games_data]

        def _norm(name: str) -> str:
            n = re.sub(r'\s*\([^)]*\)', '', name)
            return re.sub(r'[^a-z0-9]', '', n.lower())

        enabled_set = {_norm(b) for b in enabled_bookmakers}

        filtered = []
        for game in games_data:
            filtered_odds = [o for o in game.get('odds', []) if _norm(o['bookmaker']) in enabled_set]
            filtered.append({**game, 'odds': filtered_odds})
        return filtered

    async def broadcast(self, unfiltered_games: List[dict]):
        """Broadcast game data to all connected clients with per-user filtering."""
        self.unfiltered_game_data = unfiltered_games
        disconnected = []
        for websocket, user_id in list(self.active_connections.items()):
            try:
                filtered = self._filter_games_for_user(unfiltered_games, user_id)
                await websocket.send_json({
                    "type": "games_update",
                    "timestamp": datetime.now().isoformat(),
                    "count": len(filtered),
                    "games": filtered
                })
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected.append(websocket)

        for conn in disconnected:
            self.disconnect(conn)

    async def send_initial_data(self, websocket: WebSocket, user_id: str):
        """Send current game state to newly connected client."""
        if not self.unfiltered_game_data:
            return
        try:
            filtered = self._filter_games_for_user(self.unfiltered_game_data, user_id)
            await websocket.send_json({
                "type": "games_update",
                "timestamp": datetime.now().isoformat(),
                "count": len(filtered),
                "games": filtered
            })
        except Exception as e:
            logger.error(f"Error sending initial data to user {user_id}: {e}")


# ========== HTTP ENDPOINTS ==========

@router.get("/api/games")
async def get_games(user_id: str = 'default', show_all: bool = False):
    """
    Get all live games filtered by user's enabled bookmakers.
    show_all=True bypasses filtering (for testing).
    """
    from game_cache import get_all_games_response, games_serialized_cache
    import re as _re

    logger.info(f"[GET /api/games] user_id={user_id}, show_all={show_all}")
    try:
        if show_all:
            return get_all_games_response()

        settings = settings_db.get_settings(user_id)
        if not settings:
            return get_all_games_response()

        # Tier check — free users get a fixed popular bookmaker set
        try:
            from subscriptions_database import subscriptions_db
            subscription = subscriptions_db.get_subscription(user_id)
            user_tier = subscription.get("tier", "free") if subscription else "free"
            if user_tier == "free":
                settings["enabled_bookmakers"] = [
                    "draftkings", "fanduel", "betmgm", "caesars", "betrivers",
                    "pointsbet", "williamhill_us", "fanatics", "espnbet",
                    "betonlineag", "bovada", "pinnacle"
                ]
        except Exception as e:
            logger.warning(f"[TIER CHECK] Error checking tier for {user_id}: {e}")

        # Use serialized cache — rebuild if needed
        cache = games_serialized_cache
        all_games_data = cache.get("list_data") or []
        if not all_games_data:
            get_all_games_response()
            all_games_data = cache.get("list_data") or []

        def _norm(s): return _re.sub(r'[^a-z0-9]', '', s.lower())
        enabled_set = {_norm(b) for b in settings['enabled_bookmakers']}

        filtered = []
        for gd in all_games_data:
            matching = [o for o in gd.get('odds', []) if _norm(o.get('bookmaker', '')) in enabled_set]
            if len(matching) >= 2 or not gd.get('odds'):
                gd_copy = dict(gd)
                gd_copy['odds'] = matching
                filtered.append(gd_copy)

        logger.info(f"[/api/games] {len(filtered)} games after filter")
        return Response(content=json.dumps(filtered).encode("utf-8"), media_type="application/json")

    except Exception as e:
        logger.error(f"Error filtering games: {str(e)}", exc_info=True)
        from game_cache import get_all_games_response
        return get_all_games_response()


@router.get("/api/games/{game_id}")
async def get_game(game_id: str, user_id: str = 'default'):
    """Get specific game filtered by user's enabled bookmakers."""
    tracker = app_state.tracker
    try:
        game = tracker.get_game(game_id)
        if not game:
            return {"error": "Game not found"}

        settings = settings_db.get_settings(user_id)
        if not settings:
            return game

        enabled_set = set(settings['enabled_bookmakers'])
        filtered_game = game.model_copy()
        filtered_game.odds = [odd for odd in game.odds if odd.bookmaker in enabled_set]
        return filtered_game

    except Exception as e:
        logger.error(f"Error filtering game: {str(e)}")
        return tracker.get_game(game_id) or {"error": "Game not found"}


@router.get("/api/debug-nhl")
async def debug_nhl():
    """Debug NHL games in tracker."""
    tracker = app_state.tracker
    all_games = tracker.get_all_games()
    nhl_games = [g for g in all_games if g.sport_key == 'icehockey_nhl']
    return {
        "total_games": len(all_games),
        "nhl_count": len(nhl_games),
        "nhl_samples": [
            {"away": g.state.away_team.name, "home": g.state.home_team.name, "odds": len(g.odds)}
            for g in nhl_games[:3]
        ]
    }


@router.get("/api/health")
async def health():
    """Health check."""
    tracker = app_state.tracker
    return {
        "status": "healthy",
        "games_tracked": len(tracker.games) if tracker else 0
    }


@router.get("/api/version")
async def get_version():
    """Get API version info."""
    try:
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
    except Exception:
        commit = 'unknown'
    return {
        "version": "2.0.1",
        "commit": commit,
        "has_side_point_fields": True
    }


# ========== WEBSOCKET ENDPOINT ==========

@router.websocket("/ws/live-odds")
async def websocket_live_odds(websocket: WebSocket, user_id: str = 'default'):
    """
    WebSocket endpoint for real-time odds updates.
    Query param user_id filters bookmakers per user's settings.
    """
    ws_manager: ConnectionManager = app_state.ws_manager
    await ws_manager.connect(websocket, user_id)

    try:
        await ws_manager.send_initial_data(websocket, user_id)

        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping", "timestamp": datetime.now().isoformat()})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info(f"Client disconnected (user_id={user_id})")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        ws_manager.disconnect(websocket)
