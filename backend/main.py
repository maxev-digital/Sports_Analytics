"""FastAPI application"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sys
import os

from game_tracker import GameTracker
from live_models import LiveGame
from alert_monitor import AlertMonitor, ArbitrageAlert, SteamMoveAlert, LineMovementAlert
from live_analytics_engine import analytics_engine
from plays_database import plays_db
from settings_database import settings_db, BOOKMAKER_PRESETS
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio
import logging
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import auth  # Authentication module

# Betting ensemble temporarily disabled to avoid import conflicts
# from backend.models.ensemble.betting_ensemble import BettingEnsemble, GameData, EnsemblePrediction
BettingEnsemble = None
GameData = None
EnsemblePrediction = None

# Load .env from the same directory as main.py (backend folder)
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NBA Live Betting API")

# CORS configuration - supports both production (env var) and local development
cors_origins_env = os.getenv('CORS_ORIGINS', '')
if cors_origins_env:
    # Production: use comma-separated list from environment
    cors_origins = [origin.strip() for origin in cors_origins_env.split(',')]
else:
    # Local development: allow all local ports
    cors_origins = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
        "http://127.0.0.1:5179"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Game tracker instance
tracker = GameTracker()

# Alert monitor instance
alert_monitor = AlertMonitor(odds_api_key=os.getenv('ODDS_API_KEY', ''))

# Betting ensemble instance (temporarily disabled)
# betting_ensemble = BettingEnsemble(
#     pace_weight=0.40,
#     fatigue_weight=0.30,
#     regression_weight=0.30,
#     min_edge=3.0,
#     min_confidence=0.50
# )
betting_ensemble = None

# ========== WEBSOCKET CONNECTION MANAGER ==========

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.last_broadcast_data = None

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        # Store last broadcast for new connections
        self.last_broadcast_data = message

        # Send to all active connections
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_initial_data(self, websocket: WebSocket):
        """Send current game state to newly connected client"""
        if self.last_broadcast_data:
            try:
                await websocket.send_json(self.last_broadcast_data)
            except Exception as e:
                logger.error(f"Error sending initial data: {e}")

# WebSocket manager instance
ws_manager = ConnectionManager()

@app.on_event("startup")
async def startup():
    """Start game tracking and alert monitoring on app startup"""
    logger.info("Starting NBA Live Betting API...")
    asyncio.create_task(tracker.start())

    # Start alert monitoring for NBA, NFL, and NHL
    asyncio.create_task(
        alert_monitor.start_monitoring(
            sports=['basketball_nba', 'americanfootball_nfl', 'icehockey_nhl'],
            interval_seconds=10
        )
    )
    logger.info("Alert monitoring started for NBA, NFL, NHL (10s intervals - real-time arbitrage detection)")

    # Start WebSocket broadcaster for real-time updates
    asyncio.create_task(broadcast_game_updates())
    logger.info("WebSocket broadcaster started (3s intervals - real-time odds pushes)")

@app.on_event("shutdown")
async def shutdown():
    """Stop tracking on shutdown"""
    await tracker.stop()

@app.get("/")
async def root():
    return {"message": "NBA Live Betting API", "status": "running"}

# ========== WEBSOCKET ENDPOINT ==========

@app.websocket("/ws/live-odds")
async def websocket_live_odds(websocket: WebSocket):
    """
    WebSocket endpoint for real-time odds updates
    Clients connect here to receive live game data pushes
    """
    await ws_manager.connect(websocket)

    try:
        # Send initial data immediately upon connection
        await ws_manager.send_initial_data(websocket)

        # Keep connection alive and listen for client messages
        while True:
            # Wait for any message from client (ping/pong to keep alive)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo back to confirm connection is alive
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
            except asyncio.TimeoutError:
                # Send ping if no message received
                await websocket.send_json({"type": "ping", "timestamp": datetime.now().isoformat()})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

# ========== WEBSOCKET BROADCASTER TASK ==========

async def broadcast_game_updates():
    """
    Background task that broadcasts game updates to all connected WebSocket clients
    Runs every 3 seconds to push live data
    """
    logger.info("Starting WebSocket broadcaster...")
    previous_data = None

    while True:
        try:
            # Get current games from tracker
            games = list(tracker.games.values())

            if games:
                # Serialize games to dict format
                games_data = [
                    {
                        "state": {
                            "id": game.state.id,
                            "sport_key": game.state.sport_key,
                            "home_team": {
                                "name": game.state.home_team.name,
                                "score": game.state.home_team.score,
                                "spread": game.state.home_team.spread,
                                "spread_price": game.state.home_team.spread_price,
                                "money_line": game.state.home_team.money_line,
                                "momentum": game.state.home_team.momentum,
                            },
                            "away_team": {
                                "name": game.state.away_team.name,
                                "score": game.state.away_team.score,
                                "spread": game.state.away_team.spread,
                                "spread_price": game.state.away_team.spread_price,
                                "money_line": game.state.away_team.money_line,
                                "momentum": game.state.away_team.momentum,
                            },
                            "commence_time": game.state.commence_time,
                            "status": game.state.status,
                            "quarter": game.state.quarter,
                            "time_remaining": game.state.time_remaining,
                        },
                        "odds": [
                            {
                                "bookmaker": odd.bookmaker,
                                "total": odd.total,
                                "over_price": odd.over_price,
                                "under_price": odd.under_price,
                                "is_best_over": odd.is_best_over,
                                "is_best_under": odd.is_best_under,
                                "latency_ms": odd.latency_ms,
                                "home_spread": odd.home_spread,
                                "away_spread": odd.away_spread,
                                "home_spread_price": odd.home_spread_price,
                                "away_spread_price": odd.away_spread_price,
                                "home_ml": odd.home_ml,
                                "away_ml": odd.away_ml,
                            }
                            for odd in game.odds
                        ],
                        "projection": {
                            "current_total": game.projection.current_total if game.projection else None,
                            "projected_final": game.projection.projected_final if game.projection else None,
                            "edge": game.projection.edge if game.projection else None,
                            "confidence": game.projection.confidence if game.projection else None,
                            "recommendation": game.projection.recommendation if game.projection else None,
                        } if game.projection else None,
                    }
                    for game in games
                ]

                # Create broadcast message
                message = {
                    "type": "games_update",
                    "timestamp": datetime.now().isoformat(),
                    "count": len(games_data),
                    "games": games_data
                }

                # Only broadcast if data changed (avoid spamming same data)
                current_data_str = json.dumps(games_data, sort_keys=True)
                if current_data_str != previous_data:
                    await ws_manager.broadcast(message)
                    logger.debug(f"Broadcasted {len(games_data)} games to {len(ws_manager.active_connections)} clients")
                    previous_data = current_data_str

        except Exception as e:
            logger.error(f"Error in broadcast task: {e}", exc_info=True)

        # Wait 3 seconds before next update (much faster than 30s polling!)
        await asyncio.sleep(3)

def normalize_bookmaker_name(name: str) -> str:
    """
    Normalize bookmaker names to a consistent format for comparison.
    The Odds API returns display names like "DraftKings", "Bally Bet"
    but our settings use keys like "draftkings", "ballybet"
    """
    import re
    # Remove parentheses and their contents first (e.g., " (AU)" -> "")
    normalized = re.sub(r'\s*\([^)]*\)', '', name)
    # Convert to lowercase
    normalized = normalized.lower()
    # Remove ALL special characters except alphanumeric
    normalized = re.sub(r'[^a-z0-9]', '', normalized)
    return normalized

def filter_games_by_bookmakers(games: List[LiveGame], enabled_bookmakers: List[str]) -> List[LiveGame]:
    """
    Filter games to only include odds from enabled bookmakers
    Returns games that have at least 2 enabled bookmakers for comparison
    """
    filtered_games = []
    # Normalize all enabled bookmakers for comparison
    enabled_set = {normalize_bookmaker_name(bm) for bm in enabled_bookmakers}

    # DEBUG logging
    if games:
        logger.info(f"[FILTER DEBUG] Enabled bookmakers count: {len(enabled_set)}")
        logger.info(f"[FILTER DEBUG] Sample enabled: {list(enabled_set)[:5]}")
        first_game_bookmakers = [normalize_bookmaker_name(odd.bookmaker) for odd in games[0].odds]
        logger.info(f"[FILTER DEBUG] First game has {len(games[0].odds)} odds")
        logger.info(f"[FILTER DEBUG] First game normalized bookmakers: {first_game_bookmakers[:5]}")
        matches = [bm for bm in first_game_bookmakers if bm in enabled_set]
        logger.info(f"[FILTER DEBUG] Matches found: {matches[:5]}")

    for game in games:
        # Filter odds to only enabled bookmakers (with normalization)
        filtered_odds = [odd for odd in game.odds if normalize_bookmaker_name(odd.bookmaker) in enabled_set]

        # Only include games with at least 2 bookmakers for comparison
        if len(filtered_odds) >= 2:
            # Create new game object with filtered odds
            filtered_game = game.copy(deep=True)
            filtered_game.odds = filtered_odds
            filtered_games.append(filtered_game)

    return filtered_games


@app.get("/api/games", response_model=List[LiveGame])
async def get_games(user_id: str = 'default'):
    """
    Get all live games filtered by user's enabled bookmakers
    Only returns games with at least 2 enabled bookmakers
    """
    try:
        # Get user settings
        settings = settings_db.get_settings(user_id)
        if not settings:
            # If no settings found, return all games (backwards compatible)
            return tracker.get_all_games()

        # Get all games
        all_games = tracker.get_all_games()

        # Filter by enabled bookmakers
        filtered_games = filter_games_by_bookmakers(all_games, settings['enabled_bookmakers'])

        return filtered_games

    except Exception as e:
        logger.error(f"Error filtering games: {str(e)}")
        # On error, return all games (fail-safe)
        return tracker.get_all_games()

@app.get("/api/games/{game_id}", response_model=LiveGame)
async def get_game(game_id: str, user_id: str = 'default'):
    """Get specific game filtered by user's enabled bookmakers"""
    try:
        game = tracker.get_game(game_id)
        if not game:
            return {"error": "Game not found"}

        # Get user settings
        settings = settings_db.get_settings(user_id)
        if not settings:
            return game

        # Filter bookmakers
        enabled_set = set(settings['enabled_bookmakers'])
        filtered_odds = [odd for odd in game.odds if odd.bookmaker in enabled_set]

        # Return game with filtered odds
        filtered_game = game.copy(deep=True)
        filtered_game.odds = filtered_odds
        return filtered_game

    except Exception as e:
        logger.error(f"Error filtering game: {str(e)}")
        # On error, return unfiltered game
        return tracker.get_game(game_id) or {"error": "Game not found"}

@app.get("/api/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "games_tracked": len(tracker.games)
    }


# ========== AUTH REQUEST MODELS ==========

class LoginRequest(BaseModel):
    """Request model for user login"""
    username: str
    password: str


class LogoutRequest(BaseModel):
    """Request model for user logout"""
    token: str


class ChangePasswordRequest(BaseModel):
    """Request model for changing password"""
    old_password: str
    new_password: str


# ========== AUTHENTICATION ENDPOINTS ==========

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """
    User login endpoint
    Returns session token on success
    """
    try:
        # Verify credentials
        if not auth.verify_password(request.username, request.password):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Create session
        token = auth.create_session(request.username)

        return {
            "success": True,
            "message": "Login successful",
            "token": token,
            "username": request.username
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


@app.post("/api/auth/logout")
async def logout(request: LogoutRequest):
    """
    User logout endpoint
    Invalidates session token
    """
    try:
        auth.delete_session(request.token)
        return {
            "success": True,
            "message": "Logout successful"
        }
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")


@app.get("/api/auth/verify")
async def verify_session(token: str):
    """
    Verify session token
    Returns username if valid, 401 if invalid
    """
    try:
        username = auth.verify_session(token)
        if not username:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        return {
            "success": True,
            "valid": True,
            "username": username
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification failed")


class ChangePasswordWithTokenRequest(BaseModel):
    """Request model for changing password with token"""
    token: str
    old_password: str
    new_password: str


@app.post("/api/auth/change-password")
async def change_password(request: ChangePasswordWithTokenRequest):
    """
    Change user password
    Requires valid session token
    """
    try:
        # Verify session
        username = auth.verify_session(request.token)
        if not username:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        # Change password
        success = auth.change_password(username, request.old_password, request.new_password)
        if not success:
            raise HTTPException(status_code=400, detail="Old password is incorrect")

        return {
            "success": True,
            "message": "Password changed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(status_code=500, detail="Password change failed")

# ========== ADMIN ENDPOINTS (User Activity Tracking) ==========

@app.get("/api/admin/users")
async def get_all_users(token: str):
    """Get list of all users (Admin only)"""
    try:
        username = auth.verify_session(token)
        if not username:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        # Check if user is admin
        users = auth.load_users()
        if users.get(username, {}).get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        users_list = auth.get_all_users_list()
        return {
            "count": len(users_list),
            "users": users_list
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve users")

@app.get("/api/admin/active-sessions")
async def get_active_sessions(token: str):
    """Get all active sessions (Admin only)"""
    try:
        username = auth.verify_session(token)
        if not username:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        # Check if user is admin
        users = auth.load_users()
        if users.get(username, {}).get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        sessions = auth.get_active_sessions()
        return {
            "count": len(sessions),
            "sessions": sessions
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")

@app.get("/api/admin/activity-log")
async def get_activity_log(token: str, username: str = None, limit: int = 100):
    """Get user activity log (Admin only)"""
    try:
        admin_username = auth.verify_session(token)
        if not admin_username:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        # Check if user is admin
        users = auth.load_users()
        if users.get(admin_username, {}).get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

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

@app.get("/api/admin/user-stats/{username}")
async def get_user_stats(username: str, token: str):
    """Get statistics for a specific user (Admin only)"""
    try:
        admin_username = auth.verify_session(token)
        if not admin_username:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        # Check if user is admin
        users = auth.load_users()
        if users.get(admin_username, {}).get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        stats = auth.get_user_statistics(username)
        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user statistics")

@app.get("/api/admin/all-user-stats")
async def get_all_user_stats(token: str):
    """Get statistics for all users (Admin only)"""
    try:
        admin_username = auth.verify_session(token)
        if not admin_username:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        # Check if user is admin
        users = auth.load_users()
        if users.get(admin_username, {}).get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        users_list = auth.get_all_users_list()
        all_stats = []

        for user in users_list:
            stats = auth.get_user_statistics(user["username"])
            all_stats.append(stats)

        return {
            "count": len(all_stats),
            "statistics": all_stats
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get all user stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@app.get("/api/goalie-pull-opportunities")
async def get_goalie_pull_opportunities():
    """Get all current NHL goalie pull betting opportunities"""
    opportunities = tracker.get_goalie_pull_opportunities()
    return {
        "count": len(opportunities),
        "opportunities": opportunities
    }

# ========== ALERT ENDPOINTS ==========

@app.get("/api/alerts/arbitrage")
async def get_arbitrage_alerts(user_id: str = 'default'):
    """Get arbitrage opportunities filtered by user's enabled bookmakers"""
    try:
        # Get user settings
        settings = settings_db.get_settings(user_id)
        enabled_bookmakers = set(settings['enabled_bookmakers']) if settings else None

        alerts = alert_monitor.active_alerts.get('arbitrage', [])

        # Filter alerts to only include those involving enabled bookmakers
        if enabled_bookmakers:
            alerts = [
                alert for alert in alerts
                if alert.book_a in enabled_bookmakers and alert.book_b in enabled_bookmakers
            ]

        return {
            "count": len(alerts),
            "alerts": [
                {
                    "game_id": alert.game_id,
                    "sport": alert.sport,
                    "home_team": alert.home_team,
                    "away_team": alert.away_team,
                    "market_type": alert.market_type,
                    "book_a": alert.book_a,
                    "book_b": alert.book_b,
                    "odds_a": alert.odds_a,
                    "odds_b": alert.odds_b,
                    "profit_percent": round(alert.profit_percent, 2),
                    "stake_a": round(alert.stake_a, 2),
                    "stake_b": round(alert.stake_b, 2),
                    "total_stake": round(alert.total_stake, 2),
                    "guaranteed_profit": round(alert.guaranteed_profit, 2),
                    "timestamp": alert.timestamp.isoformat(),
                    "expires_in": alert.expires_in
                }
                for alert in alerts
            ]
        }

    except Exception as e:
        logger.error(f"Error filtering arbitrage alerts: {str(e)}")
        # On error, return all alerts
        alerts = alert_monitor.active_alerts.get('arbitrage', [])
        return {
            "count": len(alerts),
            "alerts": [
                {
                    "game_id": alert.game_id,
                    "sport": alert.sport,
                    "home_team": alert.home_team,
                    "away_team": alert.away_team,
                    "market_type": alert.market_type,
                    "book_a": alert.book_a,
                    "book_b": alert.book_b,
                    "odds_a": alert.odds_a,
                    "odds_b": alert.odds_b,
                    "profit_percent": round(alert.profit_percent, 2),
                    "stake_a": round(alert.stake_a, 2),
                    "stake_b": round(alert.stake_b, 2),
                    "total_stake": round(alert.total_stake, 2),
                    "guaranteed_profit": round(alert.guaranteed_profit, 2),
                    "timestamp": alert.timestamp.isoformat(),
                    "expires_in": alert.expires_in
                }
                for alert in alerts
            ]
        }

@app.get("/api/alerts/steam-moves")
async def get_steam_move_alerts(user_id: str = 'default'):
    """Get steam move alerts filtered by user's enabled bookmakers"""
    try:
        # Get user settings
        settings = settings_db.get_settings(user_id)
        enabled_bookmakers = set(settings['enabled_bookmakers']) if settings else None

        alerts = alert_monitor.active_alerts.get('steam_moves', [])

        # Filter alerts where at least one of the books that moved is enabled
        if enabled_bookmakers:
            alerts = [
                alert for alert in alerts
                if any(book in enabled_bookmakers for book in alert.books_moved)
            ]

        return {
            "count": len(alerts),
            "alerts": [
                {
                    "game_id": alert.game_id,
                    "sport": alert.sport,
                    "home_team": alert.home_team,
                    "away_team": alert.away_team,
                    "market_type": alert.market_type,
                    "side": alert.side,
                    "original_line": alert.original_line,
                    "new_line": alert.new_line,
                    "movement": round(alert.movement, 1),
                    "books_moved": alert.books_moved,
                    "consensus_percent": round(alert.consensus_percent, 1),
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in alerts
            ]
        }

    except Exception as e:
        logger.error(f"Error filtering steam move alerts: {str(e)}")
        # On error, return all alerts
        alerts = alert_monitor.active_alerts.get('steam_moves', [])
        return {
            "count": len(alerts),
            "alerts": [
                {
                    "game_id": alert.game_id,
                    "sport": alert.sport,
                    "home_team": alert.home_team,
                    "away_team": alert.away_team,
                    "market_type": alert.market_type,
                    "side": alert.side,
                    "original_line": alert.original_line,
                    "new_line": alert.new_line,
                    "movement": round(alert.movement, 1),
                    "books_moved": alert.books_moved,
                    "consensus_percent": round(alert.consensus_percent, 1),
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in alerts
            ]
        }

@app.get("/api/alerts/line-movements")
async def get_line_movement_alerts(user_id: str = 'default'):
    """Get line movement alerts filtered by user's enabled bookmakers"""
    try:
        # Get user settings
        settings = settings_db.get_settings(user_id)
        enabled_bookmakers = set(settings['enabled_bookmakers']) if settings else None

        alerts = alert_monitor.active_alerts.get('line_movements', [])

        # Filter alerts to only include enabled bookmakers
        if enabled_bookmakers:
            alerts = [
                alert for alert in alerts
                if alert.bookmaker in enabled_bookmakers
            ]

        return {
            "count": len(alerts),
            "alerts": [
                {
                    "game_id": alert.game_id,
                    "sport": alert.sport,
                    "home_team": alert.home_team,
                    "away_team": alert.away_team,
                    "market_type": alert.market_type,
                    "bookmaker": alert.bookmaker,
                    "original_line": alert.original_line,
                    "new_line": alert.new_line,
                    "movement": round(alert.movement, 1),
                    "movement_percent": round(alert.movement_percent, 1),
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in alerts
            ]
        }

    except Exception as e:
        logger.error(f"Error filtering line movement alerts: {str(e)}")
        # On error, return all alerts
        alerts = alert_monitor.active_alerts.get('line_movements', [])
        return {
            "count": len(alerts),
            "alerts": [
                {
                    "game_id": alert.game_id,
                    "sport": alert.sport,
                    "home_team": alert.home_team,
                    "away_team": alert.away_team,
                    "market_type": alert.market_type,
                    "bookmaker": alert.bookmaker,
                    "original_line": alert.original_line,
                    "new_line": alert.new_line,
                    "movement": round(alert.movement, 1),
                    "movement_percent": round(alert.movement_percent, 1),
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in alerts
            ]
        }

@app.get("/api/alerts/all")
async def get_all_alerts(user_id: str = 'default'):
    """Get all alerts filtered by user's enabled bookmakers"""
    try:
        # Get user settings
        settings = settings_db.get_settings(user_id)
        enabled_bookmakers = set(settings['enabled_bookmakers']) if settings else None

        # Get all alerts
        arb_alerts = alert_monitor.active_alerts.get('arbitrage', [])
        steam_alerts = alert_monitor.active_alerts.get('steam_moves', [])
        line_alerts = alert_monitor.active_alerts.get('line_movements', [])

        # Filter if settings exist
        if enabled_bookmakers:
            arb_alerts = [
                alert for alert in arb_alerts
                if alert.book_a in enabled_bookmakers and alert.book_b in enabled_bookmakers
            ]
            steam_alerts = [
                alert for alert in steam_alerts
                if any(book in enabled_bookmakers for book in alert.books_moved)
            ]
            line_alerts = [
                alert for alert in line_alerts
                if alert.bookmaker in enabled_bookmakers
            ]

        return {
            "arbitrage": {
                "count": len(arb_alerts),
                "alerts": arb_alerts
            },
            "steam_moves": {
                "count": len(steam_alerts),
                "alerts": steam_alerts
            },
            "line_movements": {
                "count": len(line_alerts),
                "alerts": line_alerts
            },
            "last_updated": alert_monitor.active_alerts.get('last_updated', None)
        }

    except Exception as e:
        logger.error(f"Error filtering all alerts: {str(e)}")
        # On error, return all alerts
        return {
            "arbitrage": {
                "count": len(alert_monitor.active_alerts.get('arbitrage', [])),
                "alerts": alert_monitor.active_alerts.get('arbitrage', [])
            },
            "steam_moves": {
                "count": len(alert_monitor.active_alerts.get('steam_moves', [])),
                "alerts": alert_monitor.active_alerts.get('steam_moves', [])
            },
            "line_movements": {
                "count": len(alert_monitor.active_alerts.get('line_movements', [])),
                "alerts": alert_monitor.active_alerts.get('line_movements', [])
            },
            "last_updated": alert_monitor.active_alerts.get('last_updated', None)
        }

@app.get("/api/alerts/config")
async def get_alert_config():
    """Get current alert configuration"""
    return {
        "arbitrage_min_profit": alert_monitor.arbitrage_min_profit,
        "steam_move_threshold": alert_monitor.steam_move_threshold,
        "line_movement_threshold": alert_monitor.line_movement_threshold,
        "monitored_sports": ['basketball_nba', 'americanfootball_nfl', 'icehockey_nhl'],
        "refresh_interval_seconds": 10
    }

@app.get("/api/alerts/performance")
async def get_alert_performance():
    """Get performance stats for all alert types"""
    return {
        "arbitrage": {
            "total_alerts": alert_monitor.performance_stats['arbitrage'].total_alerts,
            "successful_alerts": alert_monitor.performance_stats['arbitrage'].successful_alerts,
            "failed_alerts": alert_monitor.performance_stats['arbitrage'].failed_alerts,
            "pending_alerts": alert_monitor.performance_stats['arbitrage'].pending_alerts,
            "win_rate": alert_monitor.performance_stats['arbitrage'].win_rate,
            "avg_profit": alert_monitor.performance_stats['arbitrage'].avg_profit,
            "total_profit": alert_monitor.performance_stats['arbitrage'].total_profit,
        },
        "steam_moves": {
            "total_alerts": alert_monitor.performance_stats['steam_moves'].total_alerts,
            "successful_alerts": alert_monitor.performance_stats['steam_moves'].successful_alerts,
            "failed_alerts": alert_monitor.performance_stats['steam_moves'].failed_alerts,
            "pending_alerts": alert_monitor.performance_stats['steam_moves'].pending_alerts,
            "win_rate": alert_monitor.performance_stats['steam_moves'].win_rate,
            "avg_profit": alert_monitor.performance_stats['steam_moves'].avg_profit,
            "total_profit": alert_monitor.performance_stats['steam_moves'].total_profit,
        },
        "line_movements": {
            "total_alerts": alert_monitor.performance_stats['line_movements'].total_alerts,
            "successful_alerts": alert_monitor.performance_stats['line_movements'].successful_alerts,
            "failed_alerts": alert_monitor.performance_stats['line_movements'].failed_alerts,
            "pending_alerts": alert_monitor.performance_stats['line_movements'].pending_alerts,
            "win_rate": alert_monitor.performance_stats['line_movements'].win_rate,
            "avg_profit": alert_monitor.performance_stats['line_movements'].avg_profit,
            "total_profit": alert_monitor.performance_stats['line_movements'].total_profit,
        }
    }

# ========== PROPS ENDPOINTS ==========

@app.get("/api/props/{sport}")
async def get_player_props(sport: str):
    """Get player props for a specific sport from The Odds API"""
    import requests

    api_key = os.getenv('ODDS_API_KEY', '')

    # Map frontend sport names to Odds API sport keys
    sport_map = {
        'nba': 'basketball_nba',
        'nfl': 'americanfootball_nfl',
        'nhl': 'icehockey_nhl',
        'mlb': 'baseball_mlb',
        'ncaab': 'basketball_ncaab',
        'ncaaf': 'americanfootball_ncaaf'
    }

    odds_api_sport = sport_map.get(sport.lower(), sport)

    # Fetch player props from The Odds API
    url = f'https://api.the-odds-api.com/v4/sports/{odds_api_sport}/events'

    try:
        # First get events
        events_response = requests.get(url, params={
            'apiKey': api_key,
            'dateFormat': 'iso'
        })

        if events_response.status_code != 200:
            logger.error(f"Failed to fetch events: {events_response.status_code}")
            return {"error": "Failed to fetch events", "props": []}

        events = events_response.json()
        all_props = []

        logger.info(f"Found {len(events)} events for {odds_api_sport}")

        # For each event, fetch player props
        for event in events[:5]:  # Limit to first 5 games to save API calls
            event_id = event['id']
            props_url = f'https://api.the-odds-api.com/v4/sports/{odds_api_sport}/events/{event_id}/odds'

            props_response = requests.get(props_url, params={
                'apiKey': api_key,
                'regions': 'us',
                'markets': 'player_points,player_rebounds,player_assists,player_threes,player_pass_tds,player_rush_yds,player_receptions',
                'oddsFormat': 'american',
                'dateFormat': 'iso'
            })

            if props_response.status_code == 200:
                event_data = props_response.json()
                logger.info(f"Event {event['home_team']} vs {event['away_team']}: {len(event_data.get('bookmakers', []))} bookmakers")

                # Process bookmakers and outcomes
                for bookmaker in event_data.get('bookmakers', []):
                    markets = bookmaker.get('markets', [])
                    logger.info(f"Bookmaker {bookmaker['title']}: {len(markets)} markets")
                    for market in markets:
                        logger.info(f"Market type: {market['key']}, outcomes: {len(market.get('outcomes', []))}")
                        for outcome in market.get('outcomes', []):
                            prop = {
                                'event_id': event_id,
                                'home_team': event['home_team'],
                                'away_team': event['away_team'],
                                'commence_time': event['commence_time'],
                                'player_name': outcome.get('description', 'Unknown'),
                                'prop_type': market['key'],
                                'line': outcome.get('point'),
                                'odds': outcome.get('price'),
                                'bookmaker': bookmaker['title'],
                                'last_update': bookmaker['last_update']
                            }
                            all_props.append(prop)
            else:
                logger.error(f"Failed to fetch props for event {event_id}: {props_response.status_code}")

        logger.info(f"Fetched {len(all_props)} props for {sport}")

        # If no props found, add sample data for demonstration
        if len(all_props) == 0 and len(events) > 0:
            logger.info("No props available from API, generating sample data for demonstration")
            sample_props = []
            for event in events[:3]:
                # Sample player props for demonstration
                players = [
                    {"name": "LeBron James", "pts": 25.5, "reb": 7.5, "ast": 7.5},
                    {"name": "Stephen Curry", "pts": 27.5, "reb": 5.5, "ast": 6.5},
                    {"name": "Kevin Durant", "pts": 28.5, "reb": 6.5, "ast": 5.5},
                ] if sport == 'nba' else [
                    {"name": "Patrick Mahomes", "yds": 275.5, "tds": 2.5, "rec": None},
                    {"name": "Travis Kelce", "rec": 5.5, "yds": 65.5, "tds": 0.5},
                ] if sport == 'nfl' else []

                for player in players:
                    for prop_type, line in player.items():
                        if prop_type == 'name' or line is None:
                            continue
                        for book, odds_over, odds_under in [
                            ('DraftKings', -110, -110),
                            ('FanDuel', -105, -115),
                            ('BetMGM', -108, -112),
                            ('Caesars', -110, -110)
                        ]:
                            sample_props.extend([
                                {
                                    'event_id': event['id'],
                                    'home_team': event['home_team'],
                                    'away_team': event['away_team'],
                                    'commence_time': event['commence_time'],
                                    'player_name': f"{player['name']} Over",
                                    'prop_type': f'player_{prop_type}',
                                    'line': line,
                                    'odds': odds_over,
                                    'bookmaker': book,
                                    'last_update': event['commence_time']
                                },
                                {
                                    'event_id': event['id'],
                                    'home_team': event['home_team'],
                                    'away_team': event['away_team'],
                                    'commence_time': event['commence_time'],
                                    'player_name': f"{player['name']} Under",
                                    'prop_type': f'player_{prop_type}',
                                    'line': line,
                                    'odds': odds_under,
                                    'bookmaker': book,
                                    'last_update': event['commence_time']
                                }
                            ])
            all_props = sample_props
            logger.info(f"Generated {len(sample_props)} sample props")

        return {"sport": sport, "count": len(all_props), "props": all_props}

    except Exception as e:
        logger.error(f"Error fetching props: {str(e)}")
        return {"error": str(e), "props": []}


# ========== ENSEMBLE BETTING ENGINE ENDPOINTS ==========

class EnsembleAnalysisRequest(BaseModel):
    """Request model for ensemble analysis"""
    game_id: str
    home_team: str
    away_team: str
    game_time: str
    market_total: float
    market_total_odds: float = -110
    market_spread: Optional[float] = None
    market_spread_odds: Optional[float] = None

    # Pace data
    home_pace: float = 100.0
    away_pace: float = 100.0
    home_off_rating: float = 110.0
    away_off_rating: float = 110.0
    home_def_rating: float = 110.0
    away_def_rating: float = 110.0

    # Schedule/Fatigue data
    home_rest_days: int = 1
    away_rest_days: int = 1
    home_back_to_back: bool = False
    away_back_to_back: bool = False
    home_miles_traveled: float = 0.0
    away_miles_traveled: float = 0.0
    home_time_zones: int = 0
    away_time_zones: int = 0
    home_games_last_7: int = 3
    away_games_last_7: int = 3

    # Performance history data
    home_season_ppg: float = 110.0
    away_season_ppg: float = 110.0
    home_last_5_ppg: float = 110.0
    away_last_5_ppg: float = 110.0
    home_season_papg: float = 110.0
    away_season_papg: float = 110.0
    home_last_5_papg: float = 110.0
    away_last_5_papg: float = 110.0
    home_fg_pct_season: float = 0.46
    away_fg_pct_season: float = 0.46
    home_fg_pct_last_5: float = 0.46
    away_fg_pct_last_5: float = 0.46
    home_3pt_pct_season: float = 0.36
    away_3pt_pct_season: float = 0.36
    home_3pt_pct_last_5: float = 0.36
    away_3pt_pct_last_5: float = 0.36

    # Bet sizing
    bankroll: float = 10000


@app.post("/api/ensemble/analyze")
async def analyze_game(request: EnsembleAnalysisRequest):
    """
    Run ensemble analysis on a game

    Combines pace-based, fatigue, and regression strategies to generate
    a comprehensive betting recommendation with EV calculation
    """
    try:
        # Convert request to GameData
        game_data = GameData(
            game_id=request.game_id,
            home_team=request.home_team,
            away_team=request.away_team,
            game_time=request.game_time,
            market_total=request.market_total,
            market_total_odds=request.market_total_odds,
            market_spread=request.market_spread,
            market_spread_odds=request.market_spread_odds,
            home_pace=request.home_pace,
            away_pace=request.away_pace,
            home_off_rating=request.home_off_rating,
            away_off_rating=request.away_off_rating,
            home_def_rating=request.home_def_rating,
            away_def_rating=request.away_def_rating,
            home_rest_days=request.home_rest_days,
            away_rest_days=request.away_rest_days,
            home_back_to_back=request.home_back_to_back,
            away_back_to_back=request.away_back_to_back,
            home_miles_traveled=request.home_miles_traveled,
            away_miles_traveled=request.away_miles_traveled,
            home_time_zones=request.home_time_zones,
            away_time_zones=request.away_time_zones,
            home_games_last_7=request.home_games_last_7,
            away_games_last_7=request.away_games_last_7,
            home_season_ppg=request.home_season_ppg,
            away_season_ppg=request.away_season_ppg,
            home_last_5_ppg=request.home_last_5_ppg,
            away_last_5_ppg=request.away_last_5_ppg,
            home_season_papg=request.home_season_papg,
            away_season_papg=request.away_season_papg,
            home_last_5_papg=request.home_last_5_papg,
            away_last_5_papg=request.away_last_5_papg,
            home_fg_pct_season=request.home_fg_pct_season,
            away_fg_pct_season=request.away_fg_pct_season,
            home_fg_pct_last_5=request.home_fg_pct_last_5,
            away_fg_pct_last_5=request.away_fg_pct_last_5,
            home_3pt_pct_season=request.home_3pt_pct_season,
            away_3pt_pct_season=request.away_3pt_pct_season,
            home_3pt_pct_last_5=request.home_3pt_pct_last_5,
            away_3pt_pct_last_5=request.away_3pt_pct_last_5
        )

        # Generate prediction
        prediction = betting_ensemble.predict(game_data, bankroll=request.bankroll)

        # Return as JSON
        return {
            "game_id": prediction.game_id,
            "home_team": prediction.home_team,
            "away_team": prediction.away_team,
            "predicted_total": round(prediction.predicted_total, 1),
            "market_total": prediction.market_total,
            "edge": round(prediction.edge, 1),
            "edge_percentage": round(prediction.edge_percentage, 2),
            "recommendation": prediction.recommendation,
            "bet_decision": prediction.bet_decision,
            "confidence": round(prediction.confidence, 3),
            "confidence_tier": prediction.confidence_tier,
            "expected_value": round(prediction.expected_value, 2),
            "recommended_bet_size": round(prediction.recommended_bet_size, 2),
            "strategy_breakdown": {
                "pace": {
                    "prediction": round(prediction.pace_prediction, 1),
                    "weight": prediction.pace_weight,
                    "confidence": round(prediction.strategy_insights['pace']['confidence'], 3),
                    "scenario": prediction.strategy_insights['pace']['scenario']
                },
                "fatigue": {
                    "prediction": round(prediction.fatigue_prediction, 1),
                    "weight": prediction.fatigue_weight,
                    "confidence": round(prediction.strategy_insights['fatigue']['confidence'], 3),
                    "edge_type": prediction.strategy_insights['fatigue']['edge_type']
                },
                "regression": {
                    "prediction": round(prediction.regression_prediction, 1),
                    "weight": prediction.regression_weight,
                    "confidence": round(prediction.strategy_insights['regression']['confidence'], 3),
                    "direction": prediction.strategy_insights['regression']['direction']
                }
            },
            "key_factors": prediction.key_factors
        }

    except Exception as e:
        logger.error(f"Error in ensemble analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/ensemble/sample")
async def get_sample_prediction():
    """
    Get a sample ensemble prediction for demonstration
    """
    # Create sample game
    sample_game = GameData(
        game_id="LAL_BOS_SAMPLE",
        home_team="Lakers",
        away_team="Celtics",
        game_time="2025-01-15 19:00",
        market_total=225.5,
        market_total_odds=-110,
        # Pace data - Lakers fast, Celtics moderate
        home_pace=102.0,
        away_pace=98.0,
        home_off_rating=116.0,
        away_off_rating=118.0,
        home_def_rating=112.0,
        away_def_rating=110.0,
        # Schedule - Lakers rested, Celtics on back-to-back
        home_rest_days=2,
        away_rest_days=0,
        home_back_to_back=False,
        away_back_to_back=True,
        away_miles_traveled=2800,
        away_time_zones=3,
        home_games_last_7=3,
        away_games_last_7=5,
        # Performance - Lakers hot, Celtics cold
        home_season_ppg=115.0,
        away_season_ppg=117.0,
        home_last_5_ppg=120.0,
        away_last_5_ppg=112.0,
        home_last_5_papg=108.0,
        away_last_5_papg=115.0,
        home_fg_pct_season=0.475,
        away_fg_pct_season=0.470,
        home_fg_pct_last_5=0.490,
        away_fg_pct_last_5=0.430
    )

    prediction = betting_ensemble.predict(sample_game, bankroll=10000)

    return {
        "game_id": prediction.game_id,
        "home_team": prediction.home_team,
        "away_team": prediction.away_team,
        "predicted_total": round(prediction.predicted_total, 1),
        "market_total": prediction.market_total,
        "edge": round(prediction.edge, 1),
        "edge_percentage": round(prediction.edge_percentage, 2),
        "recommendation": prediction.recommendation,
        "bet_decision": prediction.bet_decision,
        "confidence": round(prediction.confidence, 3),
        "confidence_tier": prediction.confidence_tier,
        "expected_value": round(prediction.expected_value, 2),
        "recommended_bet_size": round(prediction.recommended_bet_size, 2),
        "strategy_breakdown": {
            "pace": {
                "prediction": round(prediction.pace_prediction, 1),
                "weight": prediction.pace_weight,
                "confidence": round(prediction.strategy_insights['pace']['confidence'], 3),
                "scenario": prediction.strategy_insights['pace']['scenario']
            },
            "fatigue": {
                "prediction": round(prediction.fatigue_prediction, 1),
                "weight": prediction.fatigue_weight,
                "confidence": round(prediction.strategy_insights['fatigue']['confidence'], 3),
                "edge_type": prediction.strategy_insights['fatigue']['edge_type']
            },
            "regression": {
                "prediction": round(prediction.regression_prediction, 1),
                "weight": prediction.regression_weight,
                "confidence": round(prediction.strategy_insights['regression']['confidence'], 3),
                "direction": prediction.strategy_insights['regression']['direction']
            }
        },
        "key_factors": prediction.key_factors,
        "note": "This is a sample prediction for demonstration purposes"
    }


# ========== LIVE ANALYTICS ENGINE ENDPOINTS ==========

@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """
    Get comprehensive live analytics summary
    - System performance (latency, data freshness)
    - Strategy performance metrics
    - Active trends and momentum
    """
    return analytics_engine.get_live_summary()


@app.get("/api/analytics/latency")
async def get_latency_metrics():
    """Get detailed latency metrics"""
    return {
        "average_latency_ms": round(analytics_engine.get_average_latency(), 2),
        "by_endpoint": {
            endpoint: round(latency, 2)
            for endpoint, latency in analytics_engine.get_latency_by_endpoint().items()
        },
        "recent_calls": len(analytics_engine.latency_history)
    }


@app.get("/api/analytics/edge/{game_id}")
async def get_game_edge(game_id: str):
    """
    Get edge calculations and true odds for a specific game
    Shows our probability vs market probability
    """
    if game_id not in analytics_engine.true_odds_cache:
        raise HTTPException(status_code=404, detail="No edge calculation found for this game")

    edge_data = analytics_engine.true_odds_cache[game_id]
    edge_movement = analytics_engine.get_edge_movement(game_id)

    return {
        "current": edge_data,
        "movement": edge_movement,
        "history": analytics_engine.edge_history.get(game_id, [])[-10:]  # Last 10 updates
    }


@app.post("/api/analytics/calculate-edge")
async def calculate_edge(
    game_id: str,
    market_over: int = -110,
    market_under: int = -110,
    our_probability: float = 0.55
):
    """
    Calculate edge for a game given market odds and our probability

    Example:
    - market_over: -110 (odds for over)
    - market_under: -110 (odds for under)
    - our_probability: 0.55 (we think there's 55% chance of over)
    """
    start_time = time.time()

    result = analytics_engine.calculate_true_odds(
        game_id=game_id,
        market_odds={'over': market_over, 'under': market_under},
        our_probability=our_probability
    )

    # Track latency
    latency_ms = (time.time() - start_time) * 1000
    analytics_engine.track_latency('calculate_edge', latency_ms)

    return result


@app.get("/api/analytics/momentum/{game_id}")
async def get_game_momentum(game_id: str):
    """
    Get momentum analysis for a specific game
    Shows trends in scoring, pace, shooting percentage, etc.
    """
    momentum_data = {}

    # Check all metrics we're tracking for this game
    for key in analytics_engine.momentum_history.keys():
        if key.startswith(game_id):
            metric = key.split('_', 1)[1]  # Extract metric name
            trend = analytics_engine.calculate_momentum_trend(game_id, metric)
            momentum_data[metric] = trend

    if not momentum_data:
        raise HTTPException(status_code=404, detail="No momentum data found for this game")

    return {
        "game_id": game_id,
        "metrics": momentum_data,
        "timestamp": time.time()
    }


@app.post("/api/analytics/update-momentum")
async def update_momentum(
    game_id: str,
    metric: str,
    value: float
):
    """
    Update momentum tracking for a game metric

    Metrics can be: score_diff, pace, shooting_pct, turnovers, etc.
    """
    analytics_engine.update_momentum(game_id, metric, value)
    analytics_engine.update_data_freshness(f'momentum_{game_id}')

    trend = analytics_engine.calculate_momentum_trend(game_id, metric)

    return {
        "game_id": game_id,
        "metric": metric,
        "value": value,
        "trend": trend
    }


@app.get("/api/analytics/trends/{game_id}")
async def get_game_trends(game_id: str):
    """
    Get detected trends for a specific game
    - Line movement patterns
    - Sharp money indicators
    - Momentum shifts
    """
    if game_id not in analytics_engine.trend_indicators:
        return {
            "game_id": game_id,
            "trends": None,
            "message": "No trend data available for this game"
        }

    return analytics_engine.trend_indicators[game_id]


@app.get("/api/analytics/strategy-performance")
async def get_strategy_performance():
    """
    Get detailed performance metrics for all betting strategies
    """
    return analytics_engine.get_strategy_performance()


@app.post("/api/analytics/record-result")
async def record_strategy_result(
    strategy_name: str,
    won: bool,
    edge: float
):
    """
    Record the result of a strategy prediction
    Used to track long-term performance
    """
    analytics_engine.update_strategy_performance(strategy_name, won, edge)

    return {
        "strategy": strategy_name,
        "result": "win" if won else "loss",
        "edge": edge,
        "updated_performance": analytics_engine.strategy_metrics.get(strategy_name, {})
    }


@app.get("/api/analytics/data-freshness")
async def get_data_freshness():
    """
    Check how fresh our data sources are
    Returns seconds since last update for each source
    """
    return {
        "sources": analytics_engine.get_data_freshness(),
        "timestamp": time.time()
    }


@app.get("/api/analytics/live-dashboard")
async def get_live_dashboard():
    """
    Get comprehensive live dashboard data
    Combines all analytics into one endpoint for dashboard display
    """
    # Get all games being tracked
    games = tracker.get_all_games()

    # For each game, get analytics
    game_analytics = []
    for game in games[:5]:  # Limit to first 5 games
        game_id = game.get('id', game.get('game_id', ''))

        # Get edge if available
        edge_data = analytics_engine.true_odds_cache.get(game_id)

        # Get momentum if available
        momentum = {}
        for key in analytics_engine.momentum_history.keys():
            if key.startswith(game_id):
                metric = key.split('_', 1)[1]
                trend = analytics_engine.calculate_momentum_trend(game_id, metric)
                momentum[metric] = trend

        # Get trends if available
        trends = analytics_engine.trend_indicators.get(game_id)

        game_analytics.append({
            "game": game,
            "edge": edge_data,
            "momentum": momentum if momentum else None,
            "trends": trends
        })

    return {
        "system_status": analytics_engine.get_live_summary(),
        "games": game_analytics,
        "timestamp": time.time()
    }


# ========== PERSISTENT PLAY TRACKING ENDPOINTS ==========

class RecommendedPlayRequest(BaseModel):
    """Request model for logging a recommended play"""
    game_id: str
    sport: str = "NBA"
    home_team: str
    away_team: str
    game_time: str

    # Strategy info
    strategy_name: str
    strategy_category: str
    confidence_level: str  # HIGH, MEDIUM, LOW

    # Play details
    play_type: str  # TOTALS, SPREAD, MONEYLINE, PROP
    recommended_side: str  # OVER, UNDER, HOME, AWAY, etc.
    recommended_line: Optional[float] = None
    recommended_price: int  # American odds

    # Bookmaker info
    best_book: str
    alternate_books: Optional[List[Dict[str, Any]]] = None

    # Edge calculation
    our_probability: float
    market_probability: float
    edge_percentage: float
    expected_value: float

    # Context
    momentum_indicator: Optional[str] = None
    trend_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class PlayResultRequest(BaseModel):
    """Request model for recording a play result"""
    play_id: str
    result: str  # won, lost, push
    actual_total: Optional[float] = None
    final_score_home: Optional[int] = None
    final_score_away: Optional[int] = None
    closing_line: Optional[float] = None
    closing_price: Optional[int] = None
    line_movement: Optional[float] = None
    profit_loss: float
    roi: float
    verified: bool = True


# ========== SETTINGS REQUEST MODELS ==========

class BookmakerSettingsRequest(BaseModel):
    """Request model for updating enabled bookmakers"""
    enabled_bookmakers: List[str]


class BankrollSettingsRequest(BaseModel):
    """Request model for updating bankroll settings"""
    total_bankroll: float
    unit_size: float
    risk_level: str  # low, medium, high


class AlertSettingsRequest(BaseModel):
    """Request model for updating alert settings"""
    min_arb_profit: float
    steam_move_threshold: float
    line_movement_threshold: float
    alert_sound_enabled: bool


class DisplaySettingsRequest(BaseModel):
    """Request model for updating display settings"""
    show_latency: bool
    highlight_pinnacle: bool
    dark_mode: bool


class AllSettingsRequest(BaseModel):
    """Request model for updating all settings"""
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


@app.post("/api/plays/log")
async def log_recommended_play(request: RecommendedPlayRequest):
    """
    Log a new recommended play with all details
    - Strategy name and category
    - Best available line and bookmaker
    - Edge calculation
    - Confidence level
    """
    try:
        play_data = {
            'timestamp': datetime.now().isoformat(),
            'game_id': request.game_id,
            'sport': request.sport,
            'home_team': request.home_team,
            'away_team': request.away_team,
            'game_time': request.game_time,
            'strategy_name': request.strategy_name,
            'strategy_category': request.strategy_category,
            'confidence_level': request.confidence_level,
            'play_type': request.play_type,
            'recommended_side': request.recommended_side,
            'recommended_line': request.recommended_line,
            'recommended_price': request.recommended_price,
            'best_book': request.best_book,
            'alternate_books': request.alternate_books or [],
            'our_probability': request.our_probability,
            'market_probability': request.market_probability,
            'edge_percentage': request.edge_percentage,
            'expected_value': request.expected_value,
            'momentum_indicator': request.momentum_indicator,
            'trend_data': request.trend_data or {},
            'notes': request.notes or ''
        }

        play_id = plays_db.log_recommended_play(play_data)

        return {
            "success": True,
            "play_id": play_id,
            "message": "Play logged successfully",
            "play_data": play_data
        }

    except Exception as e:
        logger.error(f"Error logging play: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to log play: {str(e)}")


@app.post("/api/plays/result")
async def record_play_result(request: PlayResultRequest):
    """
    Record the result of a recommended play
    - Final score and outcome
    - Closing line (to measure line value)
    - Profit/loss and ROI
    """
    try:
        result_data = {
            'result': request.result,
            'actual_total': request.actual_total,
            'final_score_home': request.final_score_home,
            'final_score_away': request.final_score_away,
            'closing_line': request.closing_line,
            'closing_price': request.closing_price,
            'line_movement': request.line_movement or 0.0,
            'profit_loss': request.profit_loss,
            'roi': request.roi,
            'verified': request.verified
        }

        success = plays_db.record_play_result(request.play_id, result_data)

        return {
            "success": success,
            "play_id": request.play_id,
            "result": request.result,
            "profit_loss": request.profit_loss,
            "message": "Result recorded successfully"
        }

    except Exception as e:
        logger.error(f"Error recording result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to record result: {str(e)}")


@app.get("/api/plays/all")
async def get_all_plays(limit: int = 100, status: Optional[str] = None):
    """
    Get all recommended plays with optional status filter
    - All plays across all strategies
    - Filter by pending, won, lost, push
    """
    try:
        plays = plays_db.get_all_plays(limit=limit, status=status)
        return {
            "count": len(plays),
            "plays": plays
        }
    except Exception as e:
        logger.error(f"Error fetching plays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch plays: {str(e)}")


@app.get("/api/plays/pending")
async def get_pending_plays():
    """Get all plays waiting for results"""
    try:
        plays = plays_db.get_pending_plays()
        return {
            "count": len(plays),
            "pending_plays": plays
        }
    except Exception as e:
        logger.error(f"Error fetching pending plays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pending plays: {str(e)}")


@app.get("/api/plays/recent")
async def get_recent_results(days: int = 7):
    """Get recent settled plays (last N days)"""
    try:
        plays = plays_db.get_recent_results(days=days)
        return {
            "count": len(plays),
            "days": days,
            "plays": plays
        }
    except Exception as e:
        logger.error(f"Error fetching recent results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent results: {str(e)}")


@app.get("/api/plays/strategy/{strategy_name}")
async def get_plays_by_strategy(strategy_name: str, limit: int = 50):
    """Get all plays for a specific strategy with results"""
    try:
        plays = plays_db.get_plays_by_strategy(strategy_name, limit=limit)
        return {
            "strategy": strategy_name,
            "count": len(plays),
            "plays": plays
        }
    except Exception as e:
        logger.error(f"Error fetching strategy plays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch strategy plays: {str(e)}")


@app.get("/api/plays/category/{category}")
async def get_plays_by_category(category: str, limit: int = 50):
    """Get all plays for a specific alert category"""
    try:
        plays = plays_db.get_plays_by_category(category, limit=limit)
        return {
            "category": category,
            "count": len(plays),
            "plays": plays
        }
    except Exception as e:
        logger.error(f"Error fetching category plays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch category plays: {str(e)}")


@app.get("/api/plays/performance")
async def get_all_strategy_performance():
    """
    Get performance metrics for all strategies
    - Win rate, total profit, ROI
    - Breakdown by confidence level
    - Historical tracking
    """
    try:
        performance = plays_db.get_strategy_performance()
        return {
            "count": len(performance),
            "strategies": performance
        }
    except Exception as e:
        logger.error(f"Error fetching performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance: {str(e)}")


@app.get("/api/plays/performance/{strategy_name}")
async def get_strategy_specific_performance(strategy_name: str):
    """Get detailed performance for a specific strategy"""
    try:
        performance = plays_db.get_strategy_performance(strategy_name=strategy_name)
        if not performance:
            return {
                "strategy": strategy_name,
                "message": "No performance data found",
                "performance": None
            }
        return {
            "strategy": strategy_name,
            "performance": performance[0]
        }
    except Exception as e:
        logger.error(f"Error fetching strategy performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance: {str(e)}")


@app.get("/api/plays/categories")
async def get_alert_categories():
    """
    Get all alert categories beyond arbitrage/steam/line movements
    - Pace-based, fatigue, regression, moneyline, etc.
    - Display names and icons for frontend
    """
    try:
        categories = plays_db.get_alert_categories()
        return {
            "count": len(categories),
            "categories": categories
        }
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch categories: {str(e)}")


@app.get("/api/plays/dashboard")
async def get_plays_dashboard():
    """
    Comprehensive plays dashboard
    - All categories with recent plays
    - Performance summary
    - Pending plays
    """
    try:
        categories = plays_db.get_alert_categories()
        pending = plays_db.get_pending_plays()
        recent = plays_db.get_recent_results(days=7)
        performance = plays_db.get_strategy_performance()

        # Group plays by category
        category_plays = {}
        for category in categories:
            cat_plays = plays_db.get_plays_by_category(category['category_name'], limit=10)
            category_plays[category['category_name']] = {
                "display_name": category['display_name'],
                "description": category['description'],
                "color": category['color_code'],
                "icon": category['icon'],
                "count": len(cat_plays),
                "recent_plays": cat_plays[:5]
            }

        # Calculate overall stats
        total_profit = sum(p.get('total_profit', 0) for p in performance)
        total_plays = sum(p.get('total_plays', 0) for p in performance)
        total_wins = sum(p.get('wins', 0) for p in performance)
        overall_win_rate = (total_wins / total_plays * 100) if total_plays > 0 else 0.0

        return {
            "summary": {
                "total_plays": total_plays,
                "pending_plays": len(pending),
                "total_profit": round(total_profit, 2),
                "overall_win_rate": round(overall_win_rate, 2),
                "categories_tracked": len(categories)
            },
            "categories": category_plays,
            "pending_plays": pending[:10],
            "recent_results": recent[:10],
            "top_strategies": sorted(performance, key=lambda x: x.get('win_rate', 0), reverse=True)[:5]
        }

    except Exception as e:
        logger.error(f"Error fetching dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard: {str(e)}")


@app.get("/api/plays/performance/by-sport")
async def get_performance_by_sport(sport: Optional[str] = None):
    """
    Get performance metrics grouped by sport
    Useful for Multi-Sport page to show per-sport results
    """
    try:
        performance = plays_db.get_performance_by_sport(sport=sport)
        return {
            "sport_filter": sport,
            "sports": performance
        }
    except Exception as e:
        logger.error(f"Error fetching sport performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sport performance: {str(e)}")


@app.get("/api/plays/sport/{sport}")
async def get_plays_for_sport(sport: str, limit: int = 50):
    """Get all plays for a specific sport"""
    try:
        plays = plays_db.get_plays_by_sport(sport, limit=limit)
        return {
            "sport": sport,
            "count": len(plays),
            "plays": plays
        }
    except Exception as e:
        logger.error(f"Error fetching sport plays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sport plays: {str(e)}")


# ========== SETTINGS ENDPOINTS ==========

@app.get("/api/settings")
async def get_user_settings(user_id: str = 'default'):
    """
    Get all user settings
    - Enabled bookmakers for filtering
    - Bankroll management settings
    - Alert threshold settings
    - Display preferences
    """
    try:
        settings = settings_db.get_settings(user_id)
        if not settings:
            raise HTTPException(status_code=404, detail="Settings not found for user")

        return {
            "success": True,
            "settings": settings
        }

    except Exception as e:
        logger.error(f"Error fetching settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch settings: {str(e)}")


@app.put("/api/settings/bookmakers")
async def update_bookmaker_settings(request: BookmakerSettingsRequest, user_id: str = 'default'):
    """
    Update enabled bookmakers list
    This controls which bookmakers appear in odds feeds and alerts
    """
    try:
        success = settings_db.update_enabled_bookmakers(
            bookmakers=request.enabled_bookmakers,
            user_id=user_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="User settings not found")

        return {
            "success": True,
            "message": "Bookmaker settings updated",
            "enabled_bookmakers": request.enabled_bookmakers
        }

    except Exception as e:
        logger.error(f"Error updating bookmaker settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update bookmaker settings: {str(e)}")


@app.put("/api/settings/bankroll")
async def update_bankroll_settings(request: BankrollSettingsRequest, user_id: str = 'default'):
    """
    Update bankroll management settings
    - Total bankroll
    - Unit size
    - Risk level (low/medium/high)
    """
    try:
        success = settings_db.update_bankroll_settings(
            total_bankroll=request.total_bankroll,
            unit_size=request.unit_size,
            risk_level=request.risk_level,
            user_id=user_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="User settings not found")

        return {
            "success": True,
            "message": "Bankroll settings updated",
            "bankroll": request.total_bankroll,
            "unit_size": request.unit_size,
            "risk_level": request.risk_level
        }

    except Exception as e:
        logger.error(f"Error updating bankroll settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update bankroll settings: {str(e)}")


@app.put("/api/settings/alerts")
async def update_alert_settings(request: AlertSettingsRequest, user_id: str = 'default'):
    """
    Update alert threshold settings
    - Minimum arbitrage profit %
    - Steam move threshold
    - Line movement threshold
    - Alert sound on/off
    """
    try:
        success = settings_db.update_alert_settings(
            min_arb_profit=request.min_arb_profit,
            steam_move_threshold=request.steam_move_threshold,
            line_movement_threshold=request.line_movement_threshold,
            alert_sound_enabled=request.alert_sound_enabled,
            user_id=user_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="User settings not found")

        return {
            "success": True,
            "message": "Alert settings updated",
            "alert_settings": {
                "min_arb_profit": request.min_arb_profit,
                "steam_move_threshold": request.steam_move_threshold,
                "line_movement_threshold": request.line_movement_threshold,
                "alert_sound_enabled": request.alert_sound_enabled
            }
        }

    except Exception as e:
        logger.error(f"Error updating alert settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update alert settings: {str(e)}")


@app.put("/api/settings/display")
async def update_display_settings(request: DisplaySettingsRequest, user_id: str = 'default'):
    """
    Update display preferences
    - Show latency indicators
    - Highlight Pinnacle odds
    - Dark mode
    """
    try:
        success = settings_db.update_display_settings(
            show_latency=request.show_latency,
            highlight_pinnacle=request.highlight_pinnacle,
            dark_mode=request.dark_mode,
            user_id=user_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="User settings not found")

        return {
            "success": True,
            "message": "Display settings updated",
            "display_settings": {
                "show_latency": request.show_latency,
                "highlight_pinnacle": request.highlight_pinnacle,
                "dark_mode": request.dark_mode
            }
        }

    except Exception as e:
        logger.error(f"Error updating display settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update display settings: {str(e)}")


@app.put("/api/settings")
async def update_all_settings(request: AllSettingsRequest, user_id: str = 'default'):
    """
    Update all settings at once
    Useful for initial setup or bulk updates
    """
    try:
        settings_dict = request.dict()
        success = settings_db.update_all_settings(settings_dict, user_id)

        if not success:
            raise HTTPException(status_code=404, detail="User settings not found")

        return {
            "success": True,
            "message": "All settings updated",
            "settings": settings_dict
        }

    except Exception as e:
        logger.error(f"Error updating all settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@app.post("/api/settings/reset")
async def reset_settings(user_id: str = 'default'):
    """
    Reset all settings to defaults
    - Resets to popular US bookmakers
    - Default bankroll and thresholds
    """
    try:
        success = settings_db.reset_to_defaults(user_id)

        return {
            "success": True,
            "message": "Settings reset to defaults",
            "settings": settings_db.get_settings(user_id)
        }

    except Exception as e:
        logger.error(f"Error resetting settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset settings: {str(e)}")


@app.get("/api/settings/presets")
async def get_bookmaker_presets():
    """
    Get all available bookmaker presets
    Returns predefined groups of bookmakers for quick selection

    Available presets:
    - sharp_books: Low-margin books preferred by pros
    - us_major: Top US legal sportsbooks
    - us_all: All US-accessible books
    - offshore: US offshore books
    - uk_major: Top UK bookmakers
    - uk_all: All UK books
    - australia: Australian sportsbooks
    - europe: European bookmakers
    - low_vig: Lowest margin books
    - high_limits: Books accepting large wagers
    - exchanges: Betting exchanges
    - popular_only: Most commonly used books
    - arbitrage_focused: Books with frequent arb opportunities
    """
    try:
        return {
            "success": True,
            "presets": BOOKMAKER_PRESETS
        }
    except Exception as e:
        logger.error(f"Error fetching presets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch presets: {str(e)}")


@app.put("/api/settings/presets/{preset_name}")
async def apply_bookmaker_preset(preset_name: str, user_id: str = 'default'):
    """
    Apply a bookmaker preset to user's settings

    Example: PUT /api/settings/presets/sharp_books?user_id=default

    This will replace the user's current enabled bookmakers with the preset's bookmakers
    """
    try:
        # Check if preset exists
        if preset_name not in BOOKMAKER_PRESETS:
            raise HTTPException(
                status_code=404,
                detail=f"Preset '{preset_name}' not found. Available presets: {list(BOOKMAKER_PRESETS.keys())}"
            )

        # Get the bookmakers from the preset
        preset = BOOKMAKER_PRESETS[preset_name]
        bookmakers = preset["bookmakers"]

        # Update user's enabled bookmakers
        success = settings_db.update_enabled_bookmakers(bookmakers, user_id)

        if not success:
            raise HTTPException(status_code=404, detail="User settings not found")

        return {
            "success": True,
            "message": f"Applied preset: {preset['name']}",
            "preset_name": preset_name,
            "preset_description": preset["description"],
            "enabled_bookmakers": bookmakers,
            "count": len(bookmakers)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying preset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to apply preset: {str(e)}")


# ========== WEBSOCKET ENDPOINT ==========

# Track active WebSocket connections
active_websocket_connections = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alerts
    Sends arbitrage opportunities, steam moves, and line movements to connected clients
    """
    try:
        logger.info("[WS] Attempting to accept WebSocket connection...")
        await websocket.accept()
        logger.info("[WS] WebSocket accepted!")

        active_websocket_connections.append(websocket)
        logger.info(f"[WS] Total connections: {len(active_websocket_connections)}")

        # Send initial connection message
        logger.info("[WS] Sending connection_established message...")
        initial_data = {
            "type": "connection_established",
            "message": "Connected to ARB Auto Bettor™ WebSocket",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_json(initial_data)
        logger.info("[WS] Connection message sent!")

        # Get and serialize arbitrage alerts
        logger.info("[WS] Getting arbitrage alerts...")
        try:
            arbitrage_alerts = alert_monitor.active_alerts.get('arbitrage', [])
            logger.info(f"[WS] Found {len(arbitrage_alerts)} arbitrage alerts")
        except Exception as e:
            logger.error(f"[WS] Error getting alerts: {e}")
            arbitrage_alerts = []

        # Serialize alerts
        serialized_alerts = []
        for i, alert in enumerate(arbitrage_alerts):
            try:
                serialized_alert = {
                    "game_id": str(alert.game_id),
                    "sport": str(alert.sport),
                    "home_team": str(alert.home_team),
                    "away_team": str(alert.away_team),
                    "game": f"{alert.away_team} @ {alert.home_team}",
                    "market_type": str(alert.market_type),
                    "book1": str(alert.book_a),
                    "book2": str(alert.book_b),
                    "bookmaker1": str(alert.book_a),
                    "bookmaker2": str(alert.book_b),
                    "odds1": float(alert.odds_a),
                    "odds2": float(alert.odds_b),
                    "profit_percentage": float(alert.profit_percent),
                    "stake1": float(alert.stake_a),
                    "stake2": float(alert.stake_b),
                    "total_stake": float(alert.total_stake),
                    "guaranteed_profit": float(alert.guaranteed_profit),
                    "selection1": f"{alert.market_type} {alert.book_a}",
                    "selection2": f"{alert.market_type} {alert.book_b}",
                    "timestamp": alert.timestamp.isoformat(),
                    "expires_in": int(alert.expires_in),
                    "id": str(alert.game_id)
                }
                serialized_alerts.append(serialized_alert)
                logger.info(f"[WS] Serialized alert {i+1}/{len(arbitrage_alerts)}")
            except Exception as e:
                logger.error(f"[WS] Error serializing alert {i}: {e}")
                continue

        # Send opportunities
        logger.info(f"[WS] Sending {len(serialized_alerts)} opportunities...")
        opportunities_data = {
            "type": "opportunities_update",
            "opportunities": serialized_alerts
        }
        await websocket.send_json(opportunities_data)
        logger.info("[WS] Opportunities sent!")

        # Keep connection alive and listen for messages
        while True:
            try:
                # Wait for messages from client (with timeout)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data) if data else {}

                # Handle subscribe message
                if message.get('type') == 'subscribe':
                    channel = message.get('channel', 'all')
                    logger.info(f"Client subscribed to: {channel}")

                    # Send acknowledgment
                    await websocket.send_json({
                        "type": "subscribed",
                        "channel": channel,
                        "message": f"Subscribed to {channel}"
                    })

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
        if websocket in active_websocket_connections:
            active_websocket_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        if websocket in active_websocket_connections:
            active_websocket_connections.remove(websocket)
        raise  # Re-raise to see full error

# ========== STRATEGY ENDPOINTS (PHASE 1 - LIVE BETTING STRATEGIES) ==========

# Import strategy modules
import sys
from pathlib import Path

# Add strategies directory to path
strategies_path = Path(__file__).parent.parent.parent.parent / "backend" / "strategies"
if str(strategies_path) not in sys.path:
    sys.path.insert(0, str(strategies_path))

from halftime_tracker import HalftimeTracker
from fatigue_detector import FatigueDetector
from weather_integration import WeatherIntegration
from momentum_detector import MomentumDetector

# Initialize strategy instances
halftime_tracker = HalftimeTracker()
fatigue_detector = FatigueDetector()
weather_integration = WeatherIntegration()
momentum_detector = MomentumDetector(window_size_minutes=5)


# Request models for strategy endpoints
class HalftimeUpdateRequest(BaseModel):
    """Request model for halftime/period updates"""
    game_id: str
    sport: str
    period: str
    time_remaining: str
    home_score: int
    away_score: int
    home_team: str
    away_team: str


class FatigueAnalysisRequest(BaseModel):
    """Request model for fatigue analysis"""
    home_team: str
    away_team: str
    sport: str
    game_date: str  # ISO format
    home_miles_traveled: Optional[float] = 0.0
    away_miles_traveled: Optional[float] = 0.0
    home_time_zones: Optional[int] = 0
    away_time_zones: Optional[int] = 0


class WeatherUpdateRequest(BaseModel):
    """Request model for weather updates"""
    game_id: str
    location: str
    temperature: Optional[float] = None
    precipitation: Optional[str] = None  # 'none', 'rain', 'snow'
    wind_speed: Optional[float] = None
    wind_direction: Optional[str] = None
    humidity: Optional[float] = None
    conditions: Optional[str] = None


class WeatherAnalysisRequest(BaseModel):
    """Request model for weather impact analysis"""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    current_total: Optional[float] = None


class MomentumEventRequest(BaseModel):
    """Request model for adding momentum events"""
    game_id: str
    event_type: str
    team: str  # 'home' or 'away'
    value: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


class MomentumAnalysisRequest(BaseModel):
    """Request model for momentum analysis"""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int


# ========== HALFTIME/PERIOD TRACKING ENDPOINTS ==========

@app.post("/api/strategies/halftime/update")
async def update_halftime_state(request: HalftimeUpdateRequest):
    """
    Update game state for halftime/period tracking

    Analyzes period transitions and generates betting opportunities
    for halftime adjustments and period-specific bets
    """
    try:
        from datetime import datetime

        analysis = halftime_tracker.update_game_state(
            game_id=request.game_id,
            sport=request.sport,
            period=request.period,
            time_remaining=request.time_remaining,
            home_score=request.home_score,
            away_score=request.away_score,
            home_team=request.home_team,
            away_team=request.away_team
        )

        return {
            "success": True,
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"Error updating halftime state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update halftime state: {str(e)}")


@app.get("/api/strategies/halftime/history/{game_id}")
async def get_halftime_history(game_id: str):
    """
    Get period history for a game

    Returns all period-by-period data and transitions
    """
    try:
        history = halftime_tracker.get_period_history(game_id)

        return {
            "success": True,
            "game_id": game_id,
            "period_count": len(history),
            "history": history
        }

    except Exception as e:
        logger.error(f"Error getting halftime history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get halftime history: {str(e)}")


# ========== FATIGUE DETECTION ENDPOINTS ==========

@app.post("/api/strategies/fatigue/analyze")
async def analyze_fatigue(request: FatigueAnalysisRequest):
    """
    Analyze schedule fatigue for both teams

    Detects back-to-back games, rest day differentials, and travel impact
    Generates betting opportunities based on fatigue mismatches
    """
    try:
        from datetime import datetime

        game_date = datetime.fromisoformat(request.game_date)

        analysis = fatigue_detector.analyze_fatigue(
            home_team=request.home_team,
            away_team=request.away_team,
            sport=request.sport,
            game_date=game_date,
            home_miles_traveled=request.home_miles_traveled,
            away_miles_traveled=request.away_miles_traveled,
            home_time_zones=request.home_time_zones,
            away_time_zones=request.away_time_zones
        )

        return {
            "success": True,
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"Error analyzing fatigue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze fatigue: {str(e)}")


@app.post("/api/strategies/fatigue/schedule/{team_name}")
async def update_team_schedule(team_name: str, sport: str, games: List[Dict[str, Any]]):
    """
    Update team schedule for fatigue tracking

    Provide list of games with date, location, opponent for accurate rest day calculation
    """
    try:
        from datetime import datetime

        # Convert date strings to datetime objects
        for game in games:
            if isinstance(game.get('date'), str):
                game['date'] = datetime.fromisoformat(game['date'])

        fatigue_detector.update_team_schedule(
            team_name=team_name,
            sport=sport,
            games=games
        )

        return {
            "success": True,
            "message": f"Schedule updated for {team_name}",
            "game_count": len(games)
        }

    except Exception as e:
        logger.error(f"Error updating team schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update team schedule: {str(e)}")


# ========== WEATHER INTEGRATION ENDPOINTS ==========

@app.post("/api/strategies/weather/update")
async def update_weather(request: WeatherUpdateRequest):
    """
    Update weather conditions for a game

    Provide current weather data for outdoor sports (NFL, NCAAF, MLB, MLS, Golf)
    """
    try:
        weather_data = weather_integration.update_weather(
            game_id=request.game_id,
            location=request.location,
            temperature=request.temperature,
            precipitation=request.precipitation,
            wind_speed=request.wind_speed,
            wind_direction=request.wind_direction,
            humidity=request.humidity,
            conditions=request.conditions
        )

        return {
            "success": True,
            "weather": weather_data
        }

    except Exception as e:
        logger.error(f"Error updating weather: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update weather: {str(e)}")


@app.post("/api/strategies/weather/analyze")
async def analyze_weather_impact(request: WeatherAnalysisRequest):
    """
    Analyze weather impact on betting opportunities

    Generates recommendations based on rain, snow, wind, temperature
    Historical data: Rain -12% passing (NFL), Wind >10mph affects scoring (MLB)
    """
    try:
        analysis = weather_integration.analyze_weather_impact(
            game_id=request.game_id,
            sport=request.sport,
            home_team=request.home_team,
            away_team=request.away_team,
            current_total=request.current_total
        )

        return {
            "success": True,
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"Error analyzing weather impact: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze weather impact: {str(e)}")


@app.get("/api/strategies/weather/{game_id}")
async def get_weather(game_id: str):
    """Get cached weather data for a game"""
    try:
        weather = weather_integration.get_weather(game_id)

        if not weather:
            raise HTTPException(status_code=404, detail="No weather data found for this game")

        return {
            "success": True,
            "weather": weather
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting weather: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get weather: {str(e)}")


# ========== MOMENTUM DETECTION ENDPOINTS ==========

@app.post("/api/strategies/momentum/event")
async def add_momentum_event(request: MomentumEventRequest):
    """
    Add a game event for momentum tracking

    Event types: score, shot, turnover, possession, penalty, hit, save
    Tracks events over 5-minute sliding window
    """
    try:
        momentum_detector.add_event(
            game_id=request.game_id,
            event_type=request.event_type,
            team=request.team,
            value=request.value,
            metadata=request.metadata
        )

        return {
            "success": True,
            "message": "Event added to momentum tracker"
        }

    except Exception as e:
        logger.error(f"Error adding momentum event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add momentum event: {str(e)}")


@app.post("/api/strategies/momentum/analyze")
async def analyze_momentum(request: MomentumAnalysisRequest):
    """
    Analyze current momentum and generate betting opportunities

    Detects:
    - Momentum shifts (Corsi >60% in NHL, 8-0 runs in NBA)
    - Scoring runs and streaks
    - Comeback opportunities

    Historical performance: Momentum teams cover 57-63% ATS (NBA)
    """
    try:
        analysis = momentum_detector.calculate_momentum(
            game_id=request.game_id,
            sport=request.sport,
            home_team=request.home_team,
            away_team=request.away_team,
            home_score=request.home_score,
            away_score=request.away_score
        )

        return {
            "success": True,
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"Error analyzing momentum: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze momentum: {str(e)}")


@app.get("/api/strategies/momentum/current/{game_id}")
async def get_current_momentum(game_id: str):
    """Get current momentum state for a game"""
    try:
        momentum = momentum_detector.get_current_momentum(game_id)

        if not momentum:
            raise HTTPException(status_code=404, detail="No momentum data found for this game")

        return {
            "success": True,
            "momentum": momentum
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current momentum: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get current momentum: {str(e)}")


@app.get("/api/strategies/momentum/history/{game_id}")
async def get_momentum_history(game_id: str):
    """Get momentum history for a game"""
    try:
        history = momentum_detector.get_momentum_history(game_id)

        return {
            "success": True,
            "game_id": game_id,
            "history_count": len(history),
            "history": history
        }

    except Exception as e:
        logger.error(f"Error getting momentum history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get momentum history: {str(e)}")


# ========== COMBINED STRATEGY ANALYSIS ENDPOINT ==========

@app.post("/api/strategies/analyze-all")
async def analyze_all_strategies(
    game_id: str,
    sport: str,
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
    period: Optional[str] = None,
    time_remaining: Optional[str] = None,
    game_date: Optional[str] = None
):
    """
    Run all strategy analyses for a game

    Combines:
    - Halftime/period analysis
    - Fatigue detection
    - Weather impact
    - Momentum detection

    Returns comprehensive betting opportunities from all strategies
    """
    try:
        all_opportunities = []

        # Halftime analysis (if period info available)
        if period and time_remaining:
            halftime_analysis = halftime_tracker.update_game_state(
                game_id=game_id,
                sport=sport,
                period=period,
                time_remaining=time_remaining,
                home_score=home_score,
                away_score=away_score,
                home_team=home_team,
                away_team=away_team
            )
            all_opportunities.extend(halftime_analysis.get('opportunities', []))

        # Momentum analysis (if we have event data)
        momentum_analysis = momentum_detector.calculate_momentum(
            game_id=game_id,
            sport=sport,
            home_team=home_team,
            away_team=away_team,
            home_score=home_score,
            away_score=away_score
        )
        if momentum_analysis.get('has_momentum_data', True):
            all_opportunities.extend(momentum_analysis.get('opportunities', []))

        # Weather analysis (if outdoor sport and weather data available)
        if sport in ['NFL', 'NCAAF', 'MLB', 'MLS', 'PGA', 'NCAAG']:
            weather_analysis = weather_integration.analyze_weather_impact(
                game_id=game_id,
                sport=sport,
                home_team=home_team,
                away_team=away_team,
                current_total=None
            )
            if weather_analysis.get('has_weather_data', False):
                all_opportunities.extend(weather_analysis.get('opportunities', []))

        # Sort opportunities by edge percentage (highest first)
        all_opportunities.sort(key=lambda x: x.get('edge_percentage', 0), reverse=True)

        return {
            "success": True,
            "game_id": game_id,
            "sport": sport,
            "opportunity_count": len(all_opportunities),
            "opportunities": all_opportunities,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error analyzing all strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze all strategies: {str(e)}")


# Mount static files (production frontend)
# Serve production build from ../frontend/dist
import os.path
frontend_dist_path = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="static")


