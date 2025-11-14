"""FastAPI application"""
print("=" * 80)
print("LOADING main.py from:", __file__)
print("=" * 80)
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sys
import os

from game_tracker import GameTracker
from live_models import LiveGame
from alert_monitor import AlertMonitor, ArbitrageAlert, SteamMoveAlert, MiddleAlert
from strategies.sharp_money_monitor_service import get_sharp_money_service
from strategies.schedule_fatigue_service import get_fatigue_service
from storage.alert_storage import alert_storage
from live_analytics_engine import analytics_engine
from plays_database import plays_db
from settings_database import settings_db, BOOKMAKER_PRESETS
from bet_grader import initialize_bet_grader
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio
import stripe
import logging
import time
import json
import sqlite3
from db_utils import get_optimized_connection
from datetime import datetime
from dotenv import load_dotenv
import auth  # Authentication module
from brevo_crm import sync_signup_to_brevo, send_welcome_email, send_admin_signup_notification, send_admin_payment_notification  # Brevo CRM integration

# Twitter injury monitoring - DISABLED (now runs as separate service)
# from twitter_injury_monitor import TwitterInjuryMonitor
# from injury_props_analyzer import InjuryPropsAnalyzer

# Betting ensemble temporarily disabled to avoid import conflicts
# from backend.models.ensemble.betting_ensemble import BettingEnsemble, GameData, EnsemblePrediction
BettingEnsemble = None
GameData = None
EnsemblePrediction = None

# Load .env from the same directory as main.py (backend folder)
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Utility to convert numpy types to Python types
import numpy as np

def convert_numpy_types(obj):
    """Recursively convert numpy types to Python types for JSON serialization"""
    if isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

app = FastAPI(title="NBA Live Betting API")

# CORS configuration - supports both production (env var) and local development
cors_origins_env = os.getenv('CORS_ORIGINS', '')
if cors_origins_env:
    # Production: use comma-separated list from environment
    cors_origins = [origin.strip() for origin in cors_origins_env.split(',')]
else:
    # Local development: allow all local ports + Chrome extensions
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
    allow_origin_regex=r"chrome-extension://.*",  # Allow Chrome/Brave extensions
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== BET TRACKING ROUTER ==========
print("DEBUG: About to import bet router...")
from routes.bets import router as bets_router
print(f"DEBUG: Bet router imported successfully: {bets_router}")
app.include_router(bets_router)
print(f"DEBUG: Bet router registered with prefix: {bets_router.prefix}")

# Import and register strategies router
from routes.strategies import router as strategies_router
app.include_router(strategies_router)
print(f"DEBUG: Strategies router registered with prefix: {strategies_router.prefix}")

# Import and register bankroll router
from routes.bankroll import router as bankroll_router
app.include_router(bankroll_router)
print(f"DEBUG: Bankroll router registered with prefix: {bankroll_router.prefix}")

# Import and register Max EV Boost router
from routes.max_ev_boost import router as max_ev_boost_router
app.include_router(max_ev_boost_router)
print(f"DEBUG: Max EV Boost router registered with prefix: {max_ev_boost_router.prefix}")

# Import and register Alert Preferences router
from routes.alert_preferences import router as alert_preferences_router
app.include_router(alert_preferences_router)
print(f"DEBUG: Alert Preferences router registered with prefix: {alert_preferences_router.prefix}")

# Import and register Goalie Pull router
try:
    print("DEBUG: About to import goalie_pull router...")
    from routes.goalie_pull import router as goalie_pull_router
    print("DEBUG: Goalie Pull router imported successfully")
    app.include_router(goalie_pull_router)
    print(f"DEBUG: Goalie Pull router registered with prefix: {goalie_pull_router.prefix}")
except Exception as e:
    print(f"ERROR importing/registering goalie_pull router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Import and register Simulation router
try:
    print("DEBUG: About to import simulation router...")
    from routes.simulation import router as simulation_router
    print("DEBUG: Simulation router imported successfully")
    app.include_router(simulation_router)
    print(f"DEBUG: Simulation router registered with prefix: {simulation_router.prefix}")
except Exception as e:
    print(f"ERROR importing/registering simulation router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Import and register Models router (Random Forest, XGBoost, LightGBM, Linear Regression)
try:
    print("DEBUG: About to import models router...")
    from routes.models import router as models_router
    print("DEBUG: Models router imported successfully")
    app.include_router(models_router)
    print(f"DEBUG: Models router registered with prefix: {models_router.prefix}")
except Exception as e:
    print(f"ERROR importing/registering models router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Import and register Edge Scanner router
try:
    print("DEBUG: About to import edge_scanner router...")
    from routes.edge_scanner import router as edge_scanner_router
    print("DEBUG: Edge Scanner router imported successfully")
    app.include_router(edge_scanner_router)
    print(f"DEBUG: Edge Scanner router registered with prefix: {edge_scanner_router.prefix}")
except Exception as e:
    print(f"ERROR importing/registering edge_scanner router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Import and register Model Performance router
try:
    print("DEBUG: About to import model_performance router...")
    from routes.model_performance import router as model_performance_router
    print("DEBUG: Model Performance router imported successfully")
    app.include_router(model_performance_router)
    print(f"DEBUG: Model Performance router registered with prefix: {model_performance_router.prefix}")
except Exception as e:
    print(f"ERROR importing/registering model_performance router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Import and register Performance (Historical Results) router
try:
    print("DEBUG: About to import performance router...")
    from routes.performance import router as performance_router
    print("DEBUG: Performance router imported successfully")
    app.include_router(performance_router)
    print(f"DEBUG: Performance router registered with prefix: {performance_router.prefix}")
except Exception as e:
    print(f"ERROR importing/registering performance router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Import and register Influencer router
try:
    print("DEBUG: About to import influencer router...")
    from routes.influencer import router as influencer_router
    print("DEBUG: Influencer router imported successfully")
    app.include_router(influencer_router)
    print(f"DEBUG: Influencer router registered with prefix: {influencer_router.prefix}")
except Exception as e:
    print(f"ERROR importing/registering influencer router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Game tracker instance
tracker = GameTracker()

# Twitter injury monitoring DISABLED - now runs as separate service (injury_monitor_service.py)
# This prevents Twitter API issues from crashing the main site
twitter_injury_monitor = None
injury_props_analyzer = None
# if os.getenv("TWITTER_BEARER_TOKEN"):
#     logger.info("Twitter API token found - initializing injury monitoring...")
#     twitter_injury_monitor = TwitterInjuryMonitor(
#         bearer_token=os.getenv("TWITTER_BEARER_TOKEN")
#     )
#     injury_props_analyzer = InjuryPropsAnalyzer(tracker.odds_client)
#     twitter_injury_monitor.set_props_analyzer(injury_props_analyzer)
#     logger.info("Twitter injury monitor initialized (Tier 1 reporters only)")
# else:
#     logger.warning("No TWITTER_BEARER_TOKEN found - Twitter injury monitoring disabled")

# Alert monitor instance
alert_monitor = AlertMonitor(odds_api_key=os.getenv('ODDS_API_KEY', ''))

# Sharp money monitor instance
sharp_money_service = get_sharp_money_service(api_key=os.getenv('ODDS_API_KEY', ''))

# Schedule fatigue monitor instance
fatigue_service = get_fatigue_service(api_key=os.getenv('ODDS_API_KEY', ''))

# Betting ensemble instance (temporarily disabled)
# betting_ensemble = BettingEnsemble(
#     pace_weight=0.40,
#     fatigue_weight=0.30,
#     regression_weight=0.30,
#     min_edge=3.0,
#     min_confidence=0.50
# )
betting_ensemble = None

# ========== PROPS CACHE ==========
# In-memory cache for player props (production-ready caching)
props_cache = {
    'nba': {'props': [], 'count': 0, 'last_updated': None},
    'nfl': {'props': [], 'count': 0, 'last_updated': None},
    'nhl': {'props': [], 'count': 0, 'last_updated': None},
    'mlb': {'props': [], 'count': 0, 'last_updated': None},
    'ncaab': {'props': [], 'count': 0, 'last_updated': None},
    'ncaaf': {'props': [], 'count': 0, 'last_updated': None}
}

# ========== WEBSOCKET CONNECTION MANAGER ==========

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        # Store connections with their user_id: {websocket: user_id}
        self.active_connections: Dict[WebSocket, str] = {}
        self.unfiltered_game_data = None  # Store raw game data before filtering

    async def connect(self, websocket: WebSocket, user_id: str = 'default'):
        """Accept new WebSocket connection with user_id"""
        await websocket.accept()
        self.active_connections[websocket] = user_id
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            user_id = self.active_connections[websocket]
            del self.active_connections[websocket]
            logger.info(f"WebSocket disconnected for user {user_id}. Total connections: {len(self.active_connections)}")

    def _filter_games_for_user(self, games_data: List[dict], user_id: str) -> List[dict]:
        """Filter game odds based on user's enabled bookmakers"""
        from settings_database import SettingsDatabase

        # Get user's enabled bookmakers
        settings_db = SettingsDatabase()
        settings = settings_db.get_settings(user_id)

        if not settings:
            # If no settings found, return games as-is
            return games_data

        enabled_bookmakers = set(settings.get('enabled_bookmakers', []))

        # If no bookmakers enabled, return games with empty odds arrays
        if not enabled_bookmakers:
            return [{**game, 'odds': []} for game in games_data]

        # Normalize bookmaker names for comparison
        def normalize_name(name: str) -> str:
            import re
            normalized = re.sub(r'\s*\([^)]*\)', '', name)
            normalized = normalized.lower()
            normalized = re.sub(r'[^a-z0-9]', '', normalized)
            return normalized

        enabled_set = {normalize_name(b) for b in enabled_bookmakers}

        # Filter odds for each game
        filtered_games = []
        for game in games_data:
            filtered_odds = [
                odd for odd in game.get('odds', [])
                if normalize_name(odd['bookmaker']) in enabled_set
            ]
            filtered_game = {**game, 'odds': filtered_odds}
            filtered_games.append(filtered_game)

        return filtered_games

    async def broadcast(self, unfiltered_games: List[dict]):
        """Broadcast game data to all connected clients with per-user filtering"""
        # Store unfiltered data for new connections
        self.unfiltered_game_data = unfiltered_games

        # Send to all active connections with user-specific filtering
        disconnected = []
        for websocket, user_id in list(self.active_connections.items()):
            try:
                # Filter games for this specific user
                filtered_games = self._filter_games_for_user(unfiltered_games, user_id)

                message = {
                    "type": "games_update",
                    "timestamp": datetime.now().isoformat(),
                    "count": len(filtered_games),
                    "games": filtered_games
                }

                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected.append(websocket)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_initial_data(self, websocket: WebSocket, user_id: str):
        """Send current game state to newly connected client with user-specific filtering"""
        if self.unfiltered_game_data:
            try:
                # Filter for this specific user
                filtered_games = self._filter_games_for_user(self.unfiltered_game_data, user_id)

                message = {
                    "type": "games_update",
                    "timestamp": datetime.now().isoformat(),
                    "count": len(filtered_games),
                    "games": filtered_games
                }

                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending initial data to user {user_id}: {e}")

# WebSocket manager instance
ws_manager = ConnectionManager()

@app.on_event("startup")
async def startup():
    """Start game tracking and alert monitoring on app startup"""
    logger.info("Starting NBA Live Betting API...")
    asyncio.create_task(tracker.start())

    # Initialize bet grader with game tracker
    initialize_bet_grader(tracker)
    logger.info("Bet grader initialized")

    # Start alert monitoring for NBA, NFL, NHL, and Tennis
    asyncio.create_task(
        alert_monitor.start_monitoring(
            sports=['basketball_nba', 'americanfootball_nfl', 'icehockey_nhl', 'tennis_atp', 'tennis_wta'],
            interval_seconds=10
        )
    )
    logger.info("Alert monitoring started for NBA, NFL, NHL (10s intervals - real-time arbitrage detection)")

    # Start sharp money monitoring for NBA, NFL, NHL
    asyncio.create_task(
        sharp_money_service.monitor_loop(
            sports=['basketball_nba', 'americanfootball_nfl', 'icehockey_nhl'],
            interval_seconds=120  # Check every 2 minutes for sharp money movements
        )
    )
    logger.info("Sharp money monitoring started for NBA, NFL, NHL (120s intervals - tracking sharp book movements)")

    # Start schedule fatigue monitoring for NBA, NFL, NHL
    asyncio.create_task(
        fatigue_service.monitor_loop(
            sports=['basketball_nba', 'americanfootball_nfl', 'icehockey_nhl'],
            interval_seconds=3600  # Check every hour for schedule changes
        )
    )
    logger.info("Schedule fatigue monitoring started for NBA, NFL, NHL (hourly - tracking B2B and rest advantages)")

    # Start WebSocket broadcaster for real-time updates
    asyncio.create_task(broadcast_game_updates())
    logger.info("WebSocket broadcaster started (3s intervals - real-time odds pushes)")

    # Twitter injury monitoring DISABLED - now runs as separate service
    # This prevents Twitter API crashes from killing the main site
    # Run injury_monitor_service.py separately to enable injury alerts
    # if twitter_injury_monitor:
    #     asyncio.create_task(
    #         twitter_injury_monitor.start_monitoring(
    #             interval_seconds=60,  # Check every 60 seconds
    #             sport=None  # Monitor all in-season sports (NBA, NFL, NHL)
    #         )
    #     )
    #     logger.info("Twitter injury monitoring started (60s intervals - tracking Woj, Shams, Schefter, etc.)")

    # Start automatic bet grading task
    asyncio.create_task(auto_grade_bets())
    logger.info("Automatic bet grading started (5min intervals - grades completed games)")

    # Start props cache refresh task (once daily at 8 AM EST)
    asyncio.create_task(refresh_props_cache())
    logger.info("Props cache refresh started (daily at 8 AM EST - saves API costs)")

@app.on_event("shutdown")
async def shutdown():
    """Stop tracking on shutdown"""
    await tracker.stop()

@app.get("/")
async def root():
    return {"message": "NBA Live Betting API", "status": "running"}

# ========== WEBSOCKET ENDPOINT ==========

@app.websocket("/ws/live-odds")
async def websocket_live_odds(websocket: WebSocket, user_id: str = 'default'):
    """
    WebSocket endpoint for real-time odds updates
    Clients connect here to receive live game data pushes

    Query params:
        user_id: User ID to filter bookmakers (default: 'default')
    """
    await ws_manager.connect(websocket, user_id)

    try:
        # Send initial data immediately upon connection
        await ws_manager.send_initial_data(websocket, user_id)

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
        logger.info(f"Client disconnected (user_id={user_id})")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
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
                            "commence_time": game.state.commence_time.isoformat() if hasattr(game.state.commence_time, 'isoformat') else str(game.state.commence_time),
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

                # Only broadcast if data changed (avoid spamming same data)
                current_data_str = json.dumps(games_data, sort_keys=True)
                if current_data_str != previous_data:
                    # Pass unfiltered games_data to broadcast, which will filter per-user
                    await ws_manager.broadcast(games_data)
                    logger.debug(f"Broadcasted {len(games_data)} games to {len(ws_manager.active_connections)} clients")
                    previous_data = current_data_str

        except Exception as e:
            logger.error(f"Error in broadcast task: {e}", exc_info=True)

        # Wait 5 seconds before next update (optimized for live games)
        await asyncio.sleep(5)

# ========== AUTOMATIC BET GRADING TASK ==========

async def auto_grade_bets():
    """
    Background task that automatically grades active bets when games complete
    Runs every 5 minutes to check for finished games
    """
    logger.info("Starting automatic bet grading task...")

    while True:
        try:
            from bet_grader import bet_grader

            if bet_grader is None:
                logger.warning("Bet grader not initialized yet")
                await asyncio.sleep(300)  # Wait 5 minutes
                continue

            # Grade all active bets
            results = bet_grader.grade_active_bets()

            if results['graded'] > 0:
                logger.info(
                    f"Auto-graded {results['graded']} bets: "
                    f"{results['won']} won, {results['lost']} lost, {results['push']} push"
                )
            elif results['checked'] > 0:
                logger.debug(f"Checked {results['checked']} active bets, none ready to grade")

            if results['errors'] > 0:
                logger.warning(f"Encountered {results['errors']} errors while grading bets")

        except Exception as e:
            logger.error(f"Error in auto-grading task: {e}", exc_info=True)

        # Wait 5 minutes before next grading cycle
        await asyncio.sleep(300)

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
    ALWAYS shows all upcoming games (even without odds) so cards display at all times
    For games with odds: requires at least 2 enabled bookmakers for comparison
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
        # ALWAYS include "consensus" bookmaker (from Sports Data IO)
        filtered_odds = [
            odd for odd in game.odds
            if normalize_bookmaker_name(odd.bookmaker) in enabled_set
            or normalize_bookmaker_name(odd.bookmaker) == 'consensus'
        ]

        # ALWAYS show all games (upcoming and live)
        # The odds list will only contain the user's enabled bookmakers + consensus
        # Games without matching bookmakers will simply have an empty odds array
        filtered_game = game.model_copy()  # Use model_copy() instead of deep copy for better performance
        filtered_game.odds = filtered_odds
        filtered_games.append(filtered_game)

    return filtered_games


@app.get("/api/games")
async def get_games(user_id: str = 'default', show_all: bool = False):
    """
    Get all live games filtered by user's enabled bookmakers
    Normal mode: Only returns games with at least 2 enabled bookmakers
    show_all=True: Returns all games regardless of odds availability (for testing)
    """
    try:
        # If show_all parameter is set, return all games (bypasses bookmaker filtering)
        if show_all:
            logger.info("Bypassing bookmaker filter - showing all games for odds testing")
            games = tracker.get_all_games()
            # Convert Pydantic models to dicts and handle numpy types
            games_dicts = [game.model_dump() for game in games]
            return convert_numpy_types(games_dicts)

        # Get user settings
        settings = settings_db.get_settings(user_id)
        if not settings:
            # If no settings found, return all games (backwards compatible)
            logger.info(f"No settings found for user {user_id}, returning all games")
            games = tracker.get_all_games()
            games_dicts = [game.model_dump() for game in games]
            return convert_numpy_types(games_dicts)

        # Get all games
        all_games = tracker.get_all_games()
        logger.info(f"[DEBUG /api/games] Total games from tracker: {len(all_games)}")

        nhl_games_before = [g for g in all_games if g.sport_key == 'icehockey_nhl']
        logger.info(f"[DEBUG /api/games] NHL games before filtering: {len(nhl_games_before)}")
        if nhl_games_before:
            logger.info(f"[DEBUG /api/games] First NHL game: {nhl_games_before[0].away_team} @ {nhl_games_before[0].home_team}, odds count: {len(nhl_games_before[0].odds)}")

        # Filter by enabled bookmakers (uses model_copy for performance)
        filtered_games = filter_games_by_bookmakers(all_games, settings['enabled_bookmakers'])
        logger.info(f"[DEBUG /api/games] Total games after filtering: {len(filtered_games)}")

        nhl_games_after = [g for g in filtered_games if g.sport_key == 'icehockey_nhl']
        logger.info(f"[DEBUG /api/games] NHL games after filtering: {len(nhl_games_after)}")
        if nhl_games_after:
            logger.info(f"[DEBUG /api/games] First NHL game after filter: {nhl_games_after[0].away_team} @ {nhl_games_after[0].home_team}, odds count: {len(nhl_games_after[0].odds)}")

        # Convert to dicts and handle numpy types
        games_dicts = [game.model_dump() for game in filtered_games]
        return convert_numpy_types(games_dicts)

    except Exception as e:
        logger.error(f"Error filtering games: {str(e)}")
        # On error, return all games (fail-safe)
        games = tracker.get_all_games()
        games_dicts = [game.model_dump() for game in games]
        return convert_numpy_types(games_dicts)

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
        filtered_game = game.model_copy()  # Use model_copy() instead of deep copy for better performance
        filtered_game.odds = filtered_odds
        return filtered_game

    except Exception as e:
        logger.error(f"Error filtering game: {str(e)}")
        # On error, return unfiltered game
        return tracker.get_game(game_id) or {"error": "Game not found"}

@app.get("/api/debug-nhl")
async def debug_nhl():
    """Debug NHL games in tracker"""
    all_games = tracker.get_all_games()
    nhl_games = [g for g in all_games if g.sport_key == 'icehockey_nhl']
    return {
        "total_games": len(all_games),
        "nhl_count": len(nhl_games),
        "nhl_samples": [{"away": g.state.away_team.name, "home": g.state.home_team.name, "odds": len(g.odds)} for g in nhl_games[:3]]
    }

@app.get("/api/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "games_tracked": len(tracker.games)
    }

@app.get("/api/version")
async def get_version():
    """Get API version info"""
    import subprocess
    try:
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
    except:
        commit = 'unknown'
    return {
        "version": "2.0.1",
        "commit": commit,
        "has_side_point_fields": True  # This version includes side_a/side_b/point_a/point_b
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

@app.post("/api/auth/register")
async def register(request: Request):
    """
    User registration endpoint
    Creates new user with 14-day free trial (Semi Pro tier access)
    Optional: accepts referral code for 50% discount on first 2 months
    """
    try:
        data = await request.json()
        full_name = data.get('full_name')
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        referral_code = data.get('referral_code', '').strip()  # Optional referral code

        if not all([full_name, email, username, password]):
            raise HTTPException(status_code=400, detail="All fields required")

        # Check if username already exists
        users = auth.load_users()
        if username in users:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Validate referral code if provided
        influencer_code_valid = False
        influencer_username = None
        if referral_code:
            try:
                from influencer_system import validate_referral_code, get_influencer_by_code
                validation = validate_referral_code(referral_code)
                if validation['valid']:
                    influencer_code_valid = True
                    influencer = get_influencer_by_code(referral_code)
                    if influencer:
                        influencer_username = influencer['username']
                        logger.info(f"Valid referral code used: {referral_code} (influencer: {influencer_username})")
            except Exception as ref_error:
                logger.warning(f"Error validating referral code: {ref_error}")

        # Create user account
        users[username] = {
            "password_hash": auth.hash_password(password),
            "role": "user",
            "created_at": datetime.now().isoformat(),
            "full_name": full_name,
            "email": email,
            "trial_start": datetime.now().isoformat(),
            "trial_days": 14,
            "referral_code": referral_code if influencer_code_valid else None,
            "has_referral_discount": influencer_code_valid
        }
        auth.save_users(users)
        
        # Create session
        token = auth.create_session(username)
        
        # Create 14-day trial subscription with Semi Pro access
        SubscriptionDB.create_subscription(
            user_id=username,
            stripe_subscription_id=None,
            stripe_customer_id=None,
            tier="semipro",
            status="trialing"
        )

        # Track referral if valid code was used
        if influencer_code_valid and influencer_username:
            try:
                from influencer_system import track_referral
                success = track_referral(
                    username=username,
                    referral_code=referral_code,
                    subscription_tier="free_trial"
                )
                if success:
                    logger.info(f"Referral tracked: {username} referred by {influencer_username}")
                else:
                    logger.warning(f"Failed to track referral for {username}")
            except Exception as track_error:
                logger.error(f"Error tracking referral: {track_error}")

        # Sync new user signup to Brevo CRM
        try:
            trial_start = users[username]["trial_start"]
            sync_signup_to_brevo(
                email=email,
                full_name=full_name,
                username=username,
                trial_start=trial_start,
                trial_days=7
            )
            logger.info(f"Successfully synced new signup to Brevo: {email}")

            # Send welcome email with Chrome extension download links
            send_welcome_email(
                email=email,
                full_name=full_name
            )
            logger.info(f"Successfully sent welcome email to: {email}")

            # Send admin notification for new signup
            send_admin_signup_notification(
                email=email,
                full_name=full_name,
                username=username
            )
            logger.info(f"Successfully sent admin signup notification for: {email}")

        except Exception as brevo_error:
            # Don't fail registration if Brevo sync fails
            logger.error(f"Failed to sync to Brevo (non-critical): {brevo_error}")

        return {
            "success": True,
            "message": "Registration successful",
            "token": token,
            "username": username,
            "email": email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")



@app.post("/api/auth/signup")
async def signup_email_only(request: Request):
    """
    Lightweight signup endpoint for Pricing page email capture
    Validates email and checks if it already exists
    Returns success so frontend can redirect to full signup page
    """
    try:
        data = await request.json()
        email = data.get('email', '').strip()
        username = data.get('username', '').strip()

        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[1]:
            raise HTTPException(status_code=400, detail="Invalid email format")

        # Check if email already exists
        users = auth.load_users()
        for existing_username, user_data in users.items():
            if user_data.get('email', '').lower() == email.lower():
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered. Please log in instead."
                )

        # Check if username already exists (if provided)
        if username and username in users:
            raise HTTPException(
                status_code=400,
                detail="Username already exists. Please choose another."
            )

        # Success - email is valid and not yet registered
        return {
            "success": True,
            "message": "Email validated successfully",
            "email": email
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email signup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Signup validation failed")


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
        
        # Get user email and role
        users = auth.load_users()
        user_data = users.get(request.username, {})
        user_email = user_data.get('email', f"{request.username}@max-ev-sports.com")
        user_role = user_data.get('role', 'user')  # Default to 'user' if not specified

        return {
            "success": True,
            "message": "Login successful",
            "token": token,
            "username": request.username,
            "email": user_email,
            "role": user_role
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

# ========== STRIPE SUBSCRIPTION ENDPOINTS ==========

from stripe_service import StripeService, handle_webhook_event
from subscription_db import SubscriptionDB
from fastapi import Request

class CheckoutSessionRequest(BaseModel):
    """Request model for creating checkout session"""
    price_id: str
    user_id: str
    user_email: str
    apply_beta_discount: bool = False  # Auto-apply 50% OFF promo code


class PortalSessionRequest(BaseModel):
    """Request model for creating portal session"""
    user_id: str


@app.post("/api/stripe/create-checkout-session")
async def create_checkout_session(request: CheckoutSessionRequest):
    """
    Create a Stripe Checkout Session for subscription
    Redirects user to Stripe hosted checkout page
    """
    try:
        # Get or create user in database
        user = SubscriptionDB.get_user(request.user_id)
        if not user:
            SubscriptionDB.create_or_update_user(
                user_id=request.user_id,
                email=request.user_email
            )
            user = SubscriptionDB.get_user(request.user_id)

        # Create Stripe customer if needed
        if not user.get('stripe_customer_id'):
            customer_id = StripeService.create_customer(
                email=request.user_email,
                user_id=request.user_id
            )
            if customer_id:
                SubscriptionDB.create_or_update_user(
                    user_id=request.user_id,
                    email=request.user_email,
                    stripe_customer_id=customer_id
                )

        # Create checkout session with optional beta discount
        session = StripeService.create_checkout_session(
            price_id=request.price_id,
            user_id=request.user_id,
            user_email=request.user_email,
            apply_beta_discount=request.apply_beta_discount
        )

        return {
            "success": True,
            "session_id": session['session_id'],
            "url": session['url']
        }

    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


@app.post("/api/stripe/create-portal-session")
async def create_portal_session(request: PortalSessionRequest):
    """
    Create a Stripe Customer Portal Session
    Allows users to manage subscription, payment methods, and invoices
    """
    try:
        # Get user
        user = SubscriptionDB.get_user(request.user_id)
        if not user or not user.get('stripe_customer_id'):
            raise HTTPException(status_code=404, detail="No subscription found for user")

        # Create portal session
        session = StripeService.create_portal_session(
            customer_id=user['stripe_customer_id']
        )

        return {
            "success": True,
            "url": session['url']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating portal session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create portal session: {str(e)}")


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events
    Updates subscription status in database based on Stripe events
    """
    try:
        # Get raw body and signature
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')

        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing signature header")

        # Verify webhook signature
        event = StripeService.verify_webhook_signature(payload, sig_header)
        if not event:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

        # Process the event
        result = handle_webhook_event(event)

        if result['processed']:
            # Update database based on event
            if result['action'] == 'create_subscription':
                # Get user_id - if not in webhook metadata, look up by customer_id
                user_id = result['user_id']
                if not user_id and result['customer_id']:
                    # Try to find user by stripe_customer_id
                    from subscription_db import get_db_connection
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute('SELECT id FROM users WHERE stripe_customer_id = ?', (result['customer_id'],))
                        row = cursor.fetchone()
                        if row:
                            user_id = row['id']
                            logger.info(f"Found user_id {user_id} for customer {result['customer_id']}")

                if user_id:
                    # Create subscription in database
                    SubscriptionDB.create_subscription(
                        user_id=user_id,
                        stripe_subscription_id=result['subscription_id'],
                        stripe_customer_id=result['customer_id'],
                        tier=result['tier'],
                        status=result['status']
                    )
                    logger.info(f"Created subscription for user {user_id}, tier {result['tier']}")

                    # Send admin notification for successful payment
                    try:
                        users = auth.load_users()
                        if user_id in users:
                            user_data = users[user_id]
                            # Get amount from event (assumes price in metadata or amount_total)
                            amount = result.get('amount', 0) / 100 if result.get('amount') else 0  # Stripe amounts are in cents
                            send_admin_payment_notification(
                                email=user_data.get('email', 'unknown'),
                                full_name=user_data.get('full_name', user_id),
                                tier=result['tier'],
                                amount=amount
                            )
                            logger.info(f"Successfully sent admin payment notification for: {user_id}")
                    except Exception as notification_error:
                        logger.error(f"Failed to send admin payment notification (non-critical): {notification_error}")
                else:
                    logger.warning(f"Could not find user_id for customer {result['customer_id']}")

            elif result['action'] == 'update_subscription':
                # Update subscription
                SubscriptionDB.update_subscription(
                    stripe_subscription_id=result['subscription_id'],
                    tier=result['tier'],
                    status=result['status']
                )

            elif result['action'] == 'cancel_subscription':
                # Cancel subscription
                SubscriptionDB.cancel_subscription(
                    stripe_subscription_id=result['subscription_id']
                )

        return {"received": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@app.post("/api/subscription/verify-checkout")
async def verify_checkout(request: Request):
    """
    Verify Stripe checkout session and create/update subscription
    This is a backup system in case the webhook hasn't fired yet
    """
    try:
        data = await request.json()
        session_id = data.get('session_id')
        user_id = data.get('user_id')

        if not session_id or not user_id:
            raise HTTPException(status_code=400, detail="Missing session_id or user_id")

        # Retrieve Stripe session
        session = StripeService.retrieve_checkout_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Checkout session not found")

        # Check if payment was successful
        if session.payment_status != 'paid':
            logger.warning(f"Payment not completed for session {session_id}, status: {session.payment_status}")
            return {
                "success": False,
                "message": "Payment not yet completed",
                "payment_status": session.payment_status
            }

        # Get subscription details from session
        stripe_subscription_id = session.subscription
        stripe_customer_id = session.customer

        # Get the price_id from the session to determine tier
        line_items = stripe.checkout.Session.list_line_items(session_id, limit=1)
        if not line_items or not line_items.data:
            raise HTTPException(status_code=500, detail="No line items found in session")

        price_id = line_items.data[0].price.id
        tier = StripeService.get_price_tier(price_id)

        logger.info(f"Verifying checkout for user {user_id}: tier={tier}, subscription_id={stripe_subscription_id}")

        # Check if subscription already exists
        existing_sub = SubscriptionDB.get_subscription(user_id)

        if existing_sub and existing_sub.get('stripe_subscription_id') == stripe_subscription_id:
            # Subscription already created (probably by webhook)
            logger.info(f"Subscription already exists for user {user_id}")
            return {
                "success": True,
                "message": "Subscription already active",
                "tier": tier,
                "created_by": "webhook"
            }

        # Create or update subscription
        SubscriptionDB.create_subscription(
            user_id=user_id,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            tier=tier,
            status='active'
        )

        logger.info(f"✅ Created subscription for user {user_id}, tier {tier} via manual verification")

        return {
            "success": True,
            "message": "Subscription activated",
            "tier": tier,
            "created_by": "manual_verification"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying checkout: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to verify checkout: {str(e)}")


@app.get("/api/subscription/status")
async def get_subscription_status(user_id: str):
    """
    Get subscription status for a user
    Returns tier, status, and expiration date
    """
    try:
        subscription = SubscriptionDB.get_subscription(user_id)

        if not subscription:
            return {
                "tier": "free",
                "status": "none"
            }

        return {
            "tier": subscription['tier'],
            "status": subscription['status'],
            "current_period_end": subscription.get('current_period_end'),
            "cancel_at_period_end": bool(subscription.get('cancel_at_period_end')),
            "trial_end": subscription.get('trial_end')
        }

    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get subscription status: {str(e)}")


@app.get("/api/subscription/features")
async def get_subscription_features(user_id: str):
    """
    Get available features for user's subscription tier
    """
    try:
        tier = SubscriptionDB.get_subscription_tier(user_id)
        
        features = {
            'free': ['live_games_limited', 'basic_odds'],
            'pro': [
                'live_games_limited', 'basic_odds',
                'all_sports', 'alerts', 'arbitrage', 'steam_moves', 'middles',
                'email_notifications', 'unlimited_views'
            ],
            'elite': [
                'live_games_limited', 'basic_odds',
                'all_sports', 'alerts', 'arbitrage', 'steam_moves', 'middles',
                'email_notifications', 'unlimited_views',
                'goalie_pulls', 'api_access', 'sms_notifications', 'custom_alerts',
                'advanced_analytics'
            ]
        }

        return {
            "tier": tier,
            "features": features.get(tier, features['free'])
        }

    except Exception as e:
        logger.error(f"Error getting subscription features: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get subscription features: {str(e)}")


@app.get("/api/subscription/check-access")
async def check_feature_access(user_id: str, feature: str):
    """
    Check if user has access to a specific feature
    """
    try:
        has_access = SubscriptionDB.has_feature_access(user_id, feature)

        return {
            "feature": feature,
            "has_access": has_access,
            "tier": SubscriptionDB.get_subscription_tier(user_id)
        }

    except Exception as e:
        logger.error(f"Error checking feature access: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check feature access: {str(e)}")


@app.get("/api/subscription/beta-count")
async def get_beta_subscriber_count():
    """
    Get the count of beta subscribers (real-time counter for pricing page)
    Beta price ID: price_1SQEZcR1TzxiBDhGeZgpoWVN
    """
    try:
        # Query subscription database for active beta subscriptions
        conn = get_optimized_connection("subscriptions.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM subscriptions
            WHERE tier = 'beta'
            AND status = 'active'
        """)

        count = cursor.fetchone()[0]
        conn.close()

        return {
            "success": True,
            "count": count
        }

    except Exception as e:
        logger.error(f"Error fetching beta count: {str(e)}")
        return {
            "success": False,
            "count": 0
        }


@app.post("/api/waitlist/add")
async def add_to_waitlist(request: dict):
    """
    Add email to waitlist for full launch notification
    Syncs to both database and Brevo CRM
    """
    try:
        email = request.get('email')
        tier = request.get('tier', 'full_launch')
        price = request.get('price', 29.99)

        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        # Store in database
        conn = get_optimized_connection("subscriptions.db")
        cursor = conn.cursor()

        # Create waitlist table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS waitlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                tier TEXT,
                price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert email
        cursor.execute("""
            INSERT OR IGNORE INTO waitlist (email, tier, price)
            VALUES (?, ?, ?)
        """, (email, tier, price))

        conn.commit()
        conn.close()

        logger.info(f"Added {email} to waitlist for {tier} at ${price}")

        # Sync to Brevo CRM
        try:
            from brevo_crm import brevo_client

            # Add contact to Brevo with waitlist attributes
            waitlist_list_id = os.getenv("BREVO_WAITLIST_LIST_ID")  # Optional: Create a waitlist in Brevo
            list_ids = [int(waitlist_list_id)] if waitlist_list_id else []

            attributes = {
                "WAITLIST_TIER": tier,
                "WAITLIST_PRICE": price,
                "WAITLIST_DATE": datetime.now().isoformat(),
                "LEAD_SOURCE": "pricing_page_waitlist"
            }

            brevo_client.create_or_update_contact(
                email=email,
                attributes=attributes,
                list_ids=list_ids
            )

            logger.info(f"Synced {email} to Brevo waitlist")

            # Send admin notification
            try:
                from brevo_crm import send_admin_waitlist_notification
                send_admin_waitlist_notification(email, tier, price)
                logger.info(f"Sent admin notification for waitlist signup: {email}")
            except Exception as notification_error:
                logger.warning(f"Failed to send admin notification (continuing anyway): {notification_error}")

        except Exception as brevo_error:
            logger.warning(f"Failed to sync to Brevo (continuing anyway): {brevo_error}")

        return {
            "success": True,
            "message": "Successfully added to waitlist"
        }

    except Exception as e:
        logger.error(f"Error adding to waitlist: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add to waitlist: {str(e)}")


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


@app.get("/api/favorite-comeback-opportunities")
async def get_favorite_comeback_opportunities():
    """Get all current NBA favorite comeback betting opportunities"""
    opportunities = tracker.get_favorite_comeback_opportunities()
    return {
        "count": len(opportunities),
        "opportunities": opportunities
    }

@app.get("/api/halftime-opportunities")
async def get_halftime_opportunities():
    """Get all current NBA halftime betting opportunities (2H spread and total)"""
    opportunities = tracker.get_halftime_opportunities()
    return {
        "count": len(opportunities),
        "opportunities": opportunities
    }

@app.get("/api/momentum-opportunities")
async def get_momentum_opportunities():
    """Get all current momentum surge betting opportunities (NHL & NBA)"""
    opportunities = tracker.get_momentum_opportunities()
    return {
        "count": len(opportunities),
        "opportunities": opportunities
    }

@app.get("/api/quarter-reversal-opportunities")
async def get_quarter_reversal_opportunities():
    """Get all current NBA quarter reversal betting opportunities"""
    opportunities = tracker.get_quarter_reversal_opportunities()
    return {
        "count": len(opportunities),
        "opportunities": opportunities
    }

@app.get("/api/injuries/props")
async def get_injury_props_opportunities():
    """Get all current injury props betting opportunities (60-second window)"""
    # Get opportunities from Twitter injury monitor if available
    if twitter_injury_monitor and hasattr(twitter_injury_monitor, 'prop_opportunities'):
        opportunities = twitter_injury_monitor.prop_opportunities
        # Filter to only show opportunities within 60-second window
        opportunities = [
            opp for opp in opportunities
            if hasattr(opp, 'time_since_tweet') and opp.time_since_tweet < 60
        ]
    else:
        # Fallback to tracker opportunities
        opportunities = tracker.get_injury_props_opportunities()

    # Convert to dict format for JSON serialization
    serialized_opportunities = []
    for opp in opportunities:
        if hasattr(opp, '__dict__'):
            opp_dict = {
                'player_name': opp.player_name,
                'team': opp.team,
                'sport': opp.sport,
                'injury_status': opp.injury_status,
                'prop_type': opp.prop_type,
                'prop_line': opp.prop_line,
                'prop_side': opp.prop_side,
                'best_odds': opp.best_odds,
                'best_book': opp.best_book,
                'expected_value': opp.expected_value,
                'confidence': opp.confidence,
                'reasoning': opp.reasoning,
                'timestamp': opp.timestamp.isoformat() if hasattr(opp.timestamp, 'isoformat') else str(opp.timestamp),
                'time_since_tweet': opp.time_since_tweet
            }
            serialized_opportunities.append(opp_dict)
        else:
            serialized_opportunities.append(opp)

    return {
        "count": len(serialized_opportunities),
        "opportunities": serialized_opportunities
    }

@app.get("/api/injuries/alerts")
async def get_injury_alerts():
    """
    Get real-time injury alerts from standalone monitoring service

    This endpoint reads from a shared JSON file written by injury_monitor_service.py
    The monitoring service runs separately, so if it crashes, main.py stays up!
    """
    import json
    from pathlib import Path

    alerts_file = Path(__file__).parent / "data" / "injury_alerts.json"

    try:
        if not alerts_file.exists():
            return {
                "count": 0,
                "alerts": [],
                "status": "no_alerts_yet",
                "message": "Injury monitor service hasn't generated alerts yet"
            }

        with open(alerts_file, 'r') as f:
            alerts = json.load(f)

        return {
            "count": len(alerts),
            "alerts": alerts,
            "status": "ok"
        }

    except Exception as e:
        logger.error(f"Error reading injury alerts: {e}")
        return {
            "count": 0,
            "alerts": [],
            "status": "error",
            "message": str(e)
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
                    "side_a": alert.side_a,
                    "side_b": alert.side_b,
                    "point_a": alert.point_a,
                    "point_b": alert.point_b,
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
                    "side_a": alert.side_a,
                    "side_b": alert.side_b,
                    "point_a": alert.point_a,
                    "point_b": alert.point_b,
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

@app.get("/api/alerts/middles")
async def get_middle_alerts(user_id: str = 'default'):
    """Get middle opportunity alerts filtered by user's enabled bookmakers"""
    try:
        # Get user settings
        settings = settings_db.get_settings(user_id)
        enabled_bookmakers = set(settings['enabled_bookmakers']) if settings else None

        alerts = alert_monitor.active_alerts.get('middles', [])

        # Filter alerts to only include enabled bookmakers
        if enabled_bookmakers:
            alerts = [
                alert for alert in alerts
                if alert.book_low in enabled_bookmakers and alert.book_high in enabled_bookmakers
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
                    "book_low": alert.book_low,
                    "book_high": alert.book_high,
                    "low_line": alert.low_line,
                    "high_line": alert.high_line,
                    "gap": round(alert.gap, 1),
                    "side_low": alert.side_low,
                    "side_high": alert.side_high,
                    "odds_low": alert.odds_low,
                    "odds_high": alert.odds_high,
                    "timestamp": alert.timestamp.isoformat(),
                    "expires_in": alert.expires_in
                }
                for alert in alerts
            ]
        }

    except Exception as e:
        logger.error(f"Error filtering middle alerts: {str(e)}")
        # On error, return all alerts
        alerts = alert_monitor.active_alerts.get('middles', [])
        return {
            "count": len(alerts),
            "alerts": [
                {
                    "game_id": alert.game_id,
                    "sport": alert.sport,
                    "home_team": alert.home_team,
                    "away_team": alert.away_team,
                    "market_type": alert.market_type,
                    "book_low": alert.book_low,
                    "book_high": alert.book_high,
                    "low_line": alert.low_line,
                    "high_line": alert.high_line,
                    "gap": round(alert.gap, 1),
                    "side_low": alert.side_low,
                    "side_high": alert.side_high,
                    "odds_low": alert.odds_low,
                    "odds_high": alert.odds_high,
                    "timestamp": alert.timestamp.isoformat(),
                    "expires_in": alert.expires_in
                }
                for alert in alerts
            ]
        }

@app.get("/api/alerts/sharp-money")
async def get_sharp_money_alerts(user_id: str = 'default'):
    """Get sharp money alerts filtered by user's enabled bookmakers"""
    try:
        # Get user settings
        settings = settings_db.get_settings(user_id)
        enabled_bookmakers = set(settings['enabled_bookmakers']) if settings else None

        # Get sharp money alerts from storage (status='pending' means active)
        tracked_alerts = alert_storage.get_alerts_by_type('sharp_money', status='pending', limit=50)

        # Convert to response format and filter by bookmakers
        alerts = []
        for tracked_alert in tracked_alerts:
            details = tracked_alert.strategy_details or {}

            # Filter by sharp books involved if user has bookmaker preferences
            if enabled_bookmakers:
                sharp_books = details.get('sharp_books_involved', [])
                # Only include if at least one sharp book is in user's enabled list
                if not any(book in enabled_bookmakers for book in sharp_books):
                    continue

            alerts.append({
                "game_id": tracked_alert.game_id,
                "sport": tracked_alert.sport,
                "home_team": tracked_alert.home_team,
                "away_team": tracked_alert.away_team,
                "alert_type": details.get('alert_type', 'sharp_money'),
                "market_type": tracked_alert.market_type,
                "recommendation": tracked_alert.recommended_side,
                "opening_line": details.get('opening_line'),
                "current_line": details.get('current_line'),
                "movement": details.get('movement'),
                "sharp_books_involved": details.get('sharp_books_involved', []),
                "confidence": details.get('confidence', 0),
                "confidence_level": details.get('confidence_level', 'MEDIUM'),
                "reasoning": details.get('reasoning', ''),
                "key_factors": details.get('key_factors', []),
                "edge_percent": tracked_alert.edge_percent,
                "timestamp": tracked_alert.generated_at.isoformat(),
                "id": tracked_alert.id
            })

        return {
            "count": len(alerts),
            "alerts": alerts
        }

    except Exception as e:
        logger.error(f"Error fetching sharp money alerts: {str(e)}")
        return {
            "count": 0,
            "alerts": [],
            "error": str(e)
        }

@app.get("/api/alerts/schedule-fatigue")
async def get_schedule_fatigue_alerts(user_id: str = 'default'):
    """Get schedule fatigue alerts"""
    try:
        # Get schedule fatigue alerts from storage (status='pending' means active)
        tracked_alerts = alert_storage.get_alerts_by_type('schedule_fatigue', status='pending', limit=50)

        # Convert to response format
        alerts = []
        for tracked_alert in tracked_alerts:
            details = tracked_alert.strategy_details or {}

            alerts.append({
                "game_id": tracked_alert.game_id,
                "sport": tracked_alert.sport,
                "home_team": tracked_alert.home_team,
                "away_team": tracked_alert.away_team,
                "fatigue_type": details.get('fatigue_type', 'rest_advantage'),
                "favored_side": details.get('favored_side', 'home'),
                "recommended_side": tracked_alert.recommended_side,
                "home_rest_days": details.get('home_rest_days', 0),
                "away_rest_days": details.get('away_rest_days', 0),
                "rest_differential": details.get('rest_differential', 0),
                "home_is_b2b": details.get('home_is_b2b', False),
                "away_is_b2b": details.get('away_is_b2b', False),
                "confidence": details.get('confidence', 0),
                "confidence_level": details.get('confidence_level', 'MEDIUM'),
                "reasoning": details.get('reasoning', ''),
                "key_factors": details.get('key_factors', []),
                "edge_percent": tracked_alert.edge_percent,
                "timestamp": tracked_alert.generated_at.isoformat(),
                "id": tracked_alert.id
            })

        return {
            "count": len(alerts),
            "alerts": alerts
        }

    except Exception as e:
        logger.error(f"Error fetching schedule fatigue alerts: {str(e)}")
        return {
            "count": 0,
            "alerts": [],
            "error": str(e)
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
        middle_alerts = alert_monitor.active_alerts.get('middles', [])

        # Get sharp money alerts from storage
        sharp_money_tracked = alert_storage.get_alerts_by_type('sharp_money', status='pending', limit=50)

        # Get schedule fatigue alerts from storage
        fatigue_tracked = alert_storage.get_alerts_by_type('schedule_fatigue', status='pending', limit=50)

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
            middle_alerts = [
                alert for alert in middle_alerts
                if alert.book_low in enabled_bookmakers and alert.book_high in enabled_bookmakers
            ]

            # Filter sharp money by bookmakers
            sharp_money_filtered = []
            for tracked_alert in sharp_money_tracked:
                details = tracked_alert.strategy_details or {}
                sharp_books = details.get('sharp_books_involved', [])
                if any(book in enabled_bookmakers for book in sharp_books):
                    sharp_money_filtered.append(tracked_alert)
            sharp_money_tracked = sharp_money_filtered

        return {
            "arbitrage": {
                "count": len(arb_alerts),
                "alerts": arb_alerts
            },
            "steam_moves": {
                "count": len(steam_alerts),
                "alerts": steam_alerts
            },
            "middles": {
                "count": len(middle_alerts),
                "alerts": [
                    {
                        "game_id": alert.game_id,
                        "sport": alert.sport,
                        "home_team": alert.home_team,
                        "away_team": alert.away_team,
                        "market_type": alert.market_type,
                        "book_low": alert.book_low,
                        "book_high": alert.book_high,
                        "low_line": alert.low_line,
                        "high_line": alert.high_line,
                        "gap": round(alert.gap, 1),
                        "side_low": alert.side_low,
                        "side_high": alert.side_high,
                        "odds_low": alert.odds_low,
                        "odds_high": alert.odds_high,
                        "timestamp": alert.timestamp.isoformat(),
                        "expires_in": alert.expires_in
                    }
                    for alert in middle_alerts
                ]
            },
            "sharp_money": {
                "count": len(sharp_money_tracked),
                "alerts": [
                    {
                        "game_id": tracked_alert.game_id,
                        "sport": tracked_alert.sport,
                        "home_team": tracked_alert.home_team,
                        "away_team": tracked_alert.away_team,
                        "alert_type": (tracked_alert.strategy_details or {}).get('alert_type', 'sharp_money'),
                        "market_type": tracked_alert.market_type,
                        "recommendation": tracked_alert.recommended_side,
                        "confidence_level": (tracked_alert.strategy_details or {}).get('confidence_level', 'MEDIUM'),
                        "sharp_books_involved": (tracked_alert.strategy_details or {}).get('sharp_books_involved', []),
                        "timestamp": tracked_alert.generated_at.isoformat(),
                        "id": tracked_alert.id
                    }
                    for tracked_alert in sharp_money_tracked
                ]
            },
            "schedule_fatigue": {
                "count": len(fatigue_tracked),
                "alerts": [
                    {
                        "game_id": tracked_alert.game_id,
                        "sport": tracked_alert.sport,
                        "home_team": tracked_alert.home_team,
                        "away_team": tracked_alert.away_team,
                        "fatigue_type": (tracked_alert.strategy_details or {}).get('fatigue_type', 'rest_advantage'),
                        "favored_side": (tracked_alert.strategy_details or {}).get('favored_side', 'home'),
                        "recommended_side": tracked_alert.recommended_side,
                        "confidence_level": (tracked_alert.strategy_details or {}).get('confidence_level', 'MEDIUM'),
                        "rest_differential": (tracked_alert.strategy_details or {}).get('rest_differential', 0),
                        "timestamp": tracked_alert.generated_at.isoformat(),
                        "id": tracked_alert.id
                    }
                    for tracked_alert in fatigue_tracked
                ]
            },
            "last_updated": alert_monitor.active_alerts.get('last_updated', None)
        }

    except Exception as e:
        logger.error(f"Error filtering all alerts: {str(e)}")
        # On error, return all alerts
        middles_raw = alert_monitor.active_alerts.get('middles', [])
        return {
            "arbitrage": {
                "count": len(alert_monitor.active_alerts.get('arbitrage', [])),
                "alerts": alert_monitor.active_alerts.get('arbitrage', [])
            },
            "steam_moves": {
                "count": len(alert_monitor.active_alerts.get('steam_moves', [])),
                "alerts": alert_monitor.active_alerts.get('steam_moves', [])
            },
            "middles": {
                "count": len(middles_raw),
                "alerts": [
                    {
                        "game_id": alert.game_id,
                        "sport": alert.sport,
                        "home_team": alert.home_team,
                        "away_team": alert.away_team,
                        "market_type": alert.market_type,
                        "book_low": alert.book_low,
                        "book_high": alert.book_high,
                        "low_line": alert.low_line,
                        "high_line": alert.high_line,
                        "gap": round(alert.gap, 1),
                        "side_low": alert.side_low,
                        "side_high": alert.side_high,
                        "odds_low": alert.odds_low,
                        "odds_high": alert.odds_high,
                        "timestamp": alert.timestamp.isoformat(),
                        "expires_in": alert.expires_in
                    }
                    for alert in middles_raw
                ]
            },
            "sharp_money": {
                "count": 0,
                "alerts": []
            },
            "schedule_fatigue": {
                "count": 0,
                "alerts": []
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

    def get_safe_stats(alert_type: str):
        """Safely get stats for an alert type, returning defaults if not available"""
        if alert_type in alert_monitor.performance_stats:
            stats = alert_monitor.performance_stats[alert_type]
            return {
                "total_alerts": stats.total_alerts,
                "successful_alerts": stats.successful_alerts,
                "failed_alerts": stats.failed_alerts,
                "pending_alerts": stats.pending_alerts,
                "win_rate": stats.win_rate,
                "avg_profit": stats.avg_profit,
                "total_profit": stats.total_profit,
            }
        else:
            # Return default values if stats not available
            return {
                "total_alerts": 0,
                "successful_alerts": 0,
                "failed_alerts": 0,
                "pending_alerts": 0,
                "win_rate": 0.0,
                "avg_profit": 0.0,
                "total_profit": 0.0,
            }

    return {
        "arbitrage": get_safe_stats('arbitrage'),
        "steam_moves": get_safe_stats('steam_moves'),
        "middles": get_safe_stats('middles')
    }

# ========== PROPS CACHING SYSTEM ==========

async def fetch_props_for_sport(sport: str, odds_api_sport: str) -> dict:
    """
    Fetch player props for a specific sport from The Odds API
    This function is used by the background refresh task
    """
    import requests

    api_key = os.getenv('ODDS_API_KEY', '')
    url = f'https://api.the-odds-api.com/v4/sports/{odds_api_sport}/events'

    try:
        # Get events
        events_response = requests.get(url, params={
            'apiKey': api_key,
            'dateFormat': 'iso'
        }, timeout=10)

        if events_response.status_code != 200:
            logger.error(f"[PROPS CACHE] Failed to fetch {sport} events: {events_response.status_code}")
            return {'props': [], 'count': 0}

        events = events_response.json()
        if not events:
            logger.info(f"[PROPS CACHE] No {sport} events available")
            return {'props': [], 'count': 0}

        all_props = []

        # Sport-specific prop markets
        markets_by_sport = {
            'basketball_nba': 'player_points,player_rebounds,player_assists,player_threes',
            'americanfootball_nfl': 'player_pass_tds,player_rush_yds,player_receptions',
            'icehockey_nhl': 'player_shots_on_goal,player_goals,player_blocked_shots,player_hits',
            'baseball_mlb': 'player_hits,player_home_runs,player_strikeouts',
            'basketball_ncaab': 'player_points,player_rebounds,player_assists',
            'americanfootball_ncaaf': 'player_pass_tds,player_rush_yds,player_receptions'
        }

        prop_markets = markets_by_sport.get(odds_api_sport, 'player_points,player_rebounds,player_assists')
        major_books = ['DraftKings', 'FanDuel', 'BetMGM', 'Caesars', 'PointsBet', 'PrizePicks', 'Underdog', 'DraftKings (Pick6)']

        # Fetch props for all available games (production: fetch all, not just 1)
        for event in events[:5]:  # Limit to 5 games for API quota management
            event_id = event['id']
            props_url = f'https://api.the-odds-api.com/v4/sports/{odds_api_sport}/events/{event_id}/odds'

            props_response = requests.get(props_url, params={
                'apiKey': api_key,
                'regions': 'us,us2,us_dfs',
                'markets': prop_markets,
                'oddsFormat': 'american',
                'dateFormat': 'iso'
            }, timeout=10)

            if props_response.status_code != 200:
                continue

            event_data = props_response.json()

            for bookmaker in event_data.get('bookmakers', []):
                if bookmaker.get('title') not in major_books:
                    continue

                for market in bookmaker.get('markets', []):
                    for outcome in market.get('outcomes', []):
                        outcome_name = outcome.get('name', '')
                        player_name = outcome.get('description', 'Unknown')

                        if outcome_name in ['Over', 'Under']:
                            display_name = f"{player_name} {outcome_name}"
                        else:
                            display_name = player_name

                        prop = {
                            'event_id': event_id,
                            'home_team': event['home_team'],
                            'away_team': event['away_team'],
                            'commence_time': event['commence_time'],
                            'player_name': display_name,
                            'prop_type': market['key'],
                            'line': outcome.get('point'),
                            'odds': outcome.get('price'),
                            'bookmaker': bookmaker['title'],
                            'last_update': bookmaker.get('last_update', event.get('commence_time'))
                        }
                        all_props.append(prop)

        logger.info(f"[PROPS CACHE] Fetched {len(all_props)} props for {sport}")
        return {'props': all_props, 'count': len(all_props)}

    except Exception as e:
        logger.error(f"[PROPS CACHE] Error fetching {sport} props: {str(e)}")
        return {'props': [], 'count': 0}


async def refresh_props_cache():
    """
    Background task to refresh props cache ONCE PER DAY at 8 AM EST
    Fetches immediately on startup, then switches to daily schedule
    """
    import pytz

    sport_map = {
        'nba': 'basketball_nba',
        'nfl': 'americanfootball_nfl',
        'nhl': 'icehockey_nhl',
        'mlb': 'baseball_mlb',
        'ncaab': 'basketball_ncaab',
        'ncaaf': 'americanfootball_ncaaf'
    }

    # INITIAL FETCH ON STARTUP - populate cache immediately
    try:
        logger.info("[PROPS CACHE] Initial fetch on startup...")
        for sport, odds_api_sport in sport_map.items():
            props_data = await fetch_props_for_sport(sport, odds_api_sport)
            props_cache[sport] = {
                'props': props_data['props'],
                'count': props_data['count'],
                'last_updated': datetime.now().isoformat()
            }
        logger.info("[PROPS CACHE] Initial fetch complete. Switching to daily 8 AM EST schedule...")
    except Exception as e:
        logger.error(f"[PROPS CACHE] Error in initial fetch: {str(e)}")

    # DAILY REFRESH LOOP
    while True:
        try:
            # Check current time in Eastern Time
            eastern = pytz.timezone('US/Eastern')
            now_eastern = datetime.now(eastern)
            current_hour = now_eastern.hour

            # Only refresh at 8 AM EST (once per day)
            if current_hour == 8:
                logger.info("[PROPS CACHE] Starting daily refresh at 8 AM EST...")

                for sport, odds_api_sport in sport_map.items():
                    props_data = await fetch_props_for_sport(sport, odds_api_sport)
                    props_cache[sport] = {
                        'props': props_data['props'],
                        'count': props_data['count'],
                        'last_updated': datetime.now().isoformat()
                    }

                logger.info("[PROPS CACHE] Daily refresh complete. Next refresh in 24 hours (8 AM EST)")
                # Sleep until next day's 8 AM (check every hour to stay synced)
                await asyncio.sleep(3600)  # 1 hour
            else:
                # Not 8 AM yet - check again in 30 minutes
                logger.debug(f"[PROPS CACHE] Current hour: {current_hour}. Waiting for 8 AM EST refresh...")
                await asyncio.sleep(1800)  # 30 minutes

        except Exception as e:
            logger.error(f"[PROPS CACHE] Error in refresh cycle: {str(e)}")
            await asyncio.sleep(300)  # Retry after 5 minutes on error


# ========== PROPS ENDPOINTS ==========

@app.get("/api/props/{sport}")
async def get_player_props(sport: str):
    """
    Get player props for a specific sport (from cache)
    Production-ready: Returns cached data instantly with background refresh
    """
    sport_lower = sport.lower()

    # Return cached data instantly
    if sport_lower in props_cache:
        cached_data = props_cache[sport_lower]
        return {
            "sport": sport,
            "count": cached_data['count'],
            "props": cached_data['props'],
            "last_updated": cached_data['last_updated'],
            "cached": True
        }
    else:
        return {
            "sport": sport,
            "count": 0,
            "props": [],
            "error": "Invalid sport",
            "cached": False
        }


# ========== ADVANCED PLAYER PROPS ENDPOINTS (WITH PROJECTIONS & EDGES) ==========

@app.get("/api/player-props/nba/edges")
async def get_nba_props_with_edges(min_edge_pct: float = 5.0):
    """
    Get NBA player props with ML-powered projections and edge analysis

    Fetches predictions from the autonomous ML props system database

    Args:
        min_edge_pct: Minimum edge percentage to filter (default 5.0%)

    Returns:
        PlayerPropsResponse with props that have calculated edges
    """
    try:
        logger.info(f"Fetching ML NBA props with edges (min_edge: {min_edge_pct}%)")

        # Connect to ML props database
        db_path = "D:/backend/data/player_props.db"
        if not os.path.exists(db_path):
            logger.warning(f"ML props database not found at {db_path}")
            return {
                "games": [],
                "total_props": 0,
                "total_strong_bets": 0,
                "total_moderate_bets": 0,
                "last_updated": datetime.now().isoformat()
            }

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get today's date
        today = datetime.now().date().isoformat()

        # Query predictions with edges >= min_edge_pct
        cursor.execute("""
            SELECT
                p.player_name,
                p.team,
                p.opponent,
                p.prop_type,
                p.market_line,
                p.predicted_value,
                p.recommendation,
                p.confidence,
                p.edge_pct,
                p.game_date,
                p.game_time,
                p.event_id,
                s.minutes_per_game,
                s.season_avg,
                s.last_10_avg
            FROM player_props_predictions p
            LEFT JOIN player_stats_cache s
                ON p.player_name = s.player_name AND p.prop_type = s.stat_type
            WHERE p.game_date = ?
              AND p.recommendation != 'PASS'
              AND ABS(p.edge_pct) >= ?
            ORDER BY ABS(p.edge_pct) DESC
        """, (today, min_edge_pct))

        predictions = cursor.fetchall()
        conn.close()

        # Group predictions by game
        games_dict = {}
        total_strong = 0
        total_moderate = 0

        for pred in predictions:
            event_id = pred['event_id'] or f"{pred['team']}-{pred['opponent']}-{pred['game_date']}"

            if event_id not in games_dict:
                games_dict[event_id] = {
                    "event_id": event_id,
                    "sport_key": "basketball_nba",
                    "home_team": pred['team'] if pred['opponent'] else "TBD",
                    "away_team": pred['opponent'] if pred['opponent'] else "TBD",
                    "commence_time": pred['game_time'] or pred['game_date'],
                    "props": []
                }

            # Determine bet strength
            edge_pct = abs(pred['edge_pct'])
            if edge_pct >= 10.0:
                bet_strength = "STRONG"
                total_strong += 1
            elif edge_pct >= 7.0:
                bet_strength = "MODERATE"
                total_moderate += 1
            else:
                bet_strength = "WEAK"

            # Build prop with edge
            prop = {
                "player_name": pred['player_name'],
                "team": pred['team'],
                "opponent": pred['opponent'],
                "game_time": pred['game_time'] or pred['game_date'],
                "prop_type": pred['prop_type'],
                "market_odds": {
                    "player_name": pred['player_name'],
                    "prop_type": pred['prop_type'],
                    "line": pred['market_line'],
                    "bookmakers": [],
                    "best_over_odds": -110,
                    "best_under_odds": -110,
                    "best_over_book": "DraftKings",
                    "best_under_book": "DraftKings"
                },
                "projection": {
                    "prop_type": pred['prop_type'],
                    "projection": round(pred['predicted_value'], 1),
                    "confidence": "HIGH" if pred['confidence'] >= 0.75 else "MEDIUM" if pred['confidence'] >= 0.60 else "LOW",
                    "confidence_score": pred['confidence'],
                    "factors": {
                        "baseline": pred['season_avg'] if pred['season_avg'] else pred['predicted_value'],
                        "recent_avg": pred['last_10_avg'] if pred['last_10_avg'] else pred['predicted_value'],
                        "trend": "stable",
                        "matchup_adjustment": 0.0,
                        "pace_adjustment": 0.0,
                        "total_adjustment": round(pred['predicted_value'] - pred['market_line'], 1)
                    },
                    "reasoning": f"ML model predicts {pred['predicted_value']:.1f} vs market line {pred['market_line']}. {pred['recommendation']} has {edge_pct:.1f}% edge."
                },
                "edge": {
                    "edge": round(pred['predicted_value'] - pred['market_line'], 1),
                    "edge_pct": round(pred['edge_pct'], 1),
                    "recommendation": pred['recommendation'],
                    "bet_strength": bet_strength
                }
            }

            games_dict[event_id]["props"].append(prop)

        games_list = list(games_dict.values())

        logger.info(
            f"Returning {len(predictions)} ML props from {len(games_list)} games "
            f"({total_strong} strong, {total_moderate} moderate)"
        )

        return {
            "games": games_list,
            "total_props": len(predictions),
            "total_strong_bets": total_strong,
            "total_moderate_bets": total_moderate,
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching ML NBA props: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
    Get all alert categories beyond arbitrage/steam/middles
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
    Sends arbitrage opportunities, steam moves, and middle opportunities to connected clients
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
strategies_path = Path(__file__).parent / "strategies"
if str(strategies_path) not in sys.path:
    sys.path.insert(0, str(strategies_path))

from halftime_tracker import HalftimeTracker
from fatigue_detector import FatigueDetector
from weather_integration import WeatherIntegration
from strategies.momentum_detector import MomentumDetector
from favorite_comeback_detector import FavoriteComebackDetector

# Initialize strategy instances
halftime_tracker = HalftimeTracker()
fatigue_detector = FatigueDetector()
weather_integration = WeatherIntegration()
momentum_detector = MomentumDetector()
favorite_comeback_detector = FavoriteComebackDetector()


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


class FavoriteComebackRequest(BaseModel):
    """Request model for favorite comeback analysis"""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    period: str
    time_remaining: str
    home_team_favorite: bool
    pregame_spread: float
    current_spread: Optional[float] = None
    home_season_stats: Optional[Dict[str, Any]] = None
    away_season_stats: Optional[Dict[str, Any]] = None
    quarter_stats: Optional[Dict[str, Any]] = None


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


# ========== FAVORITE COMEBACK DETECTION ENDPOINT ==========

@app.post("/api/strategies/favorite-comeback/analyze")
async def analyze_favorite_comeback(request: FavoriteComebackRequest):
    """
    Analyze if a favorite comeback opportunity exists

    Detects when favorites trail underdogs after hot starts and are
    likely to regress to their true talent level.

    Historical data:
    - Favorites trailing after Q1: 58% cover 2H spread
    - Favorites trailing at halftime: 60.3% ATS in 2H (2005-2023)
    """
    try:
        analysis = favorite_comeback_detector.analyze_comeback_opportunity(
            game_id=request.game_id,
            sport=request.sport,
            home_team=request.home_team,
            away_team=request.away_team,
            home_score=request.home_score,
            away_score=request.away_score,
            period=request.period,
            time_remaining=request.time_remaining,
            home_team_favorite=request.home_team_favorite,
            pregame_spread=request.pregame_spread,
            current_spread=request.current_spread,
            home_season_stats=request.home_season_stats,
            away_season_stats=request.away_season_stats,
            quarter_stats=request.quarter_stats
        )

        return {
            "success": True,
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"Error analyzing favorite comeback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze favorite comeback: {str(e)}")


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


# ========== BET GRADING ENDPOINT ==========

@app.post("/api/bets/grade-now")
async def manual_grade_bets():
    """
    Manually trigger bet grading for all active bets
    Useful for testing or forcing an immediate grading cycle
    """
    try:
        from bet_grader import bet_grader

        if bet_grader is None:
            raise HTTPException(status_code=503, detail="Bet grader not initialized")

        # Run grading
        results = bet_grader.grade_active_bets()

        return {
            "success": True,
            "checked": results['checked'],
            "graded": results['graded'],
            "won": results['won'],
            "lost": results['lost'],
            "push": results['push'],
            "errors": results['errors'],
            "message": f"Graded {results['graded']} bets ({results['won']} won, {results['lost']} lost, {results['push']} push)",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error manually grading bets: {str(e)}")

@app.get("/api/bets/user-statistics")
async def get_user_bet_statistics(request: Request):
    """
    Get betting statistics for the current user
    Returns win rate, ROI, total bets, and total profit from settled bets
    """
    try:
        # Get username from auth token
        auth_header = request.headers.get('authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Authentication required")

        token = auth_header.split(' ')[1]
        username = auth.verify_session(token)

        if not username:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        # Get all settled bets for user (win, loss, push)
        from storage.bet_storage import bet_storage
        all_bets = bet_storage.get_user_bets(username)

        # Filter to only settled bets with results
        settled_bets = [b for b in all_bets if b.status in ['win', 'loss', 'push'] and b.result and b.stake]

        if not settled_bets:
            return {
                "total_bets": 0,
                "wins": 0,
                "losses": 0,
                "pushes": 0,
                "win_rate": 0.0,
                "roi": 0.0,
                "total_profit": 0.0,
                "total_wagered": 0.0
            }

        # Calculate statistics
        wins = len([b for b in settled_bets if b.result == 'win'])
        losses = len([b for b in settled_bets if b.result == 'loss'])
        pushes = len([b for b in settled_bets if b.result == 'push'])

        total_profit = sum(b.profit_loss for b in settled_bets if b.profit_loss is not None)
        total_wagered = sum(b.stake for b in settled_bets if b.stake is not None)

        # Win rate (excluding pushes)
        decisive_bets = wins + losses
        win_rate = (wins / decisive_bets * 100) if decisive_bets > 0 else 0.0

        # ROI
        roi = (total_profit / total_wagered * 100) if total_wagered > 0 else 0.0

        return {
            "total_bets": len(settled_bets),
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "win_rate": round(win_rate, 1),
            "roi": round(roi, 1),
            "total_profit": round(total_profit, 2),
            "total_wagered": round(total_wagered, 2)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating user bet statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate statistics: {str(e)}")

# ========== FEEDBACK ENDPOINTS ==========

from storage.feedback_storage import feedback_storage

class FeedbackRequest(BaseModel):
    """Request model for user feedback"""
    type: str  # bug, feature, general
    comment: str
    page: str
    timestamp: str

@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest, request: Request):
    """Submit user feedback (bugs, features, general comments)"""
    try:
        # Get username from auth token if available, otherwise use 'anonymous'
        username = 'anonymous'
        auth_header = request.headers.get('authorization')
        logger.info(f"DEBUG: Authorization header present: {auth_header is not None}")
        if auth_header:
            logger.info(f"DEBUG: Authorization header value: {auth_header[:20]}...")

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            logger.info(f"DEBUG: Token extracted: {token[:20]}...")
            # Verify token and get username
            verified_username = auth.verify_session(token)
            logger.info(f"DEBUG: Verified username: {verified_username}")
            if verified_username:
                username = verified_username

        # Store feedback
        feedback_entry = feedback_storage.add_feedback(
            username=username,
            feedback_type=feedback.type,
            comment=feedback.comment,
            page=feedback.page,
            timestamp=feedback.timestamp
        )

        logger.info(f"Feedback received from {username}: {feedback.type} on {feedback.page}")

        return {
            "status": "success",
            "message": "Thank you for your feedback!",
            "feedback_id": feedback_entry['id']
        }

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@app.get("/api/feedback/all")
async def get_all_feedback(status: Optional[str] = None):
    """Get all feedback (admin only)"""
    try:
        feedback_list = feedback_storage.get_all_feedback(status=status)
        stats = feedback_storage.get_stats()

        return {
            "feedback": feedback_list,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback")

@app.post("/api/feedback/{feedback_id}/respond")
async def respond_to_feedback(feedback_id: str, request: Request):
    """Send admin response to user feedback"""
    try:
        data = await request.json()
        admin_response = data.get('response', '')

        if not admin_response:
            raise HTTPException(status_code=400, detail="Response cannot be empty")

        # Get feedback to find user email
        feedback_list = feedback_storage.get_all_feedback()
        feedback_item = next((f for f in feedback_list if f['id'] == feedback_id), None)

        if not feedback_item:
            raise HTTPException(status_code=404, detail="Feedback not found")

        # Load users to get email
        users = auth.load_users()
        username = feedback_item.get('username', 'anonymous')
        user_email = None

        if username != 'anonymous' and username in users:
            user_email = users[username].get('email')

        # Update feedback with admin response
        feedback_item['admin_response'] = admin_response
        feedback_item['admin_response_date'] = datetime.now().isoformat()
        feedback_item['status'] = 'responded'

        # Save updated feedback
        feedback_storage._save_feedback(feedback_list)

        # Send email notification if user has email
        if user_email:
            try:
                from brevo_service import send_feedback_response_email
                send_feedback_response_email(
                    to_email=user_email,
                    username=username,
                    original_feedback=feedback_item['comment'],
                    admin_response=admin_response,
                    feedback_type=feedback_item['type']
                )
                logger.info(f"Sent feedback response email to {user_email}")
            except Exception as email_error:
                logger.error(f"Failed to send email (non-critical): {email_error}")

        return {
            "status": "success",
            "message": "Response sent successfully",
            "email_sent": user_email is not None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error responding to feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to send response")

@app.get("/api/feedback/my-feedback")
async def get_my_feedback(request: Request):
    """Get feedback submitted by the current user"""
    try:
        # Get username from auth token
        auth_header = request.headers.get('authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Not authenticated")

        token = auth_header.split(' ')[1]
        username = auth.verify_session(token)

        if not username:
            raise HTTPException(status_code=401, detail="Invalid session")

        # Get all feedback for this user
        all_feedback = feedback_storage.get_all_feedback()
        user_feedback = [f for f in all_feedback if f.get('username') == username]

        # Sort by timestamp (newest first)
        user_feedback.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return {
            "feedback": user_feedback
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback")

@app.post("/api/feedback/{feedback_id}/mark-viewed")
async def mark_feedback_viewed(feedback_id: str, request: Request):
    """Mark an admin response as viewed by the user"""
    try:
        # Get username from auth token
        auth_header = request.headers.get('authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Not authenticated")

        token = auth_header.split(' ')[1]
        username = auth.verify_session(token)

        if not username:
            raise HTTPException(status_code=401, detail="Invalid session")

        # Get feedback
        all_feedback = feedback_storage.get_all_feedback()
        feedback_item = next((f for f in all_feedback if f['id'] == feedback_id), None)

        if not feedback_item:
            raise HTTPException(status_code=404, detail="Feedback not found")

        # Verify this feedback belongs to the user
        if feedback_item.get('username') != username:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Mark as viewed
        feedback_item['response_viewed'] = True
        feedback_item['response_viewed_date'] = datetime.now().isoformat()

        # Save
        feedback_storage._save_feedback(all_feedback)

        return {
            "status": "success",
            "message": "Marked as viewed"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking feedback as viewed: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark as viewed")

        raise HTTPException(status_code=500, detail=f"Failed to grade bets: {str(e)}")


# Mount static files (production frontend)
# Serve production build from ../frontend/dist
import os.path
frontend_dist_path = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="static")
 


# ========== FEEDBACK ENDPOINTS ==========

from storage.feedback_storage import feedback_storage

class FeedbackRequest(BaseModel):
    """Request model for user feedback"""
    type: str  # bug, feature, general
    comment: str
    page: str
    timestamp: str

@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest, request: Request):
    """Submit user feedback (bugs, features, general comments)"""
    try:
        # Get username from auth token if available, otherwise use 'anonymous'
        username = 'anonymous'
        auth_header = request.headers.get('authorization')
        logger.info(f"DEBUG: Authorization header present: {auth_header is not None}")
        if auth_header:
            logger.info(f"DEBUG: Authorization header value: {auth_header[:20]}...")

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            logger.info(f"DEBUG: Token extracted: {token[:20]}...")
            # Verify token and get username
            verified_username = auth.verify_session(token)
            logger.info(f"DEBUG: Verified username: {verified_username}")
            if verified_username:
                username = verified_username

        # Store feedback
        feedback_entry = feedback_storage.add_feedback(
            username=username,
            feedback_type=feedback.type,
            comment=feedback.comment,
            page=feedback.page,
            timestamp=feedback.timestamp
        )

        logger.info(f"Feedback received from {username}: {feedback.type} on {feedback.page}")

        return {
            "status": "success",
            "message": "Thank you for your feedback!",
            "feedback_id": feedback_entry['id']
        }

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@app.get("/api/feedback/all")
async def get_all_feedback(status: Optional[str] = None):
    """Get all feedback (admin only)"""
    try:
        feedback_list = feedback_storage.get_all_feedback(status=status)
        stats = feedback_storage.get_stats()

        return {
            "feedback": feedback_list,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback")


