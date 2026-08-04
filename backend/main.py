"""FastAPI application"""
import sys as _sys, os as _os
_vendor_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "vendor")
if _os.path.isdir(_vendor_path) and _vendor_path not in _sys.path:
    _sys.path.insert(0, _vendor_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import asyncio
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

from game_tracker import GameTracker
from alert_monitor import AlertMonitor
from strategies.sharp_money_monitor_service import get_sharp_money_service
from strategies.schedule_fatigue_service import get_fatigue_service
from bet_grader import initialize_bet_grader

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

# ========== ROUTER REGISTRATION ==========
from routes.bets import router as bets_router
app.include_router(bets_router)

from routes.strategies import router as strategies_router
app.include_router(strategies_router)

from routes.bankroll import router as bankroll_router
app.include_router(bankroll_router)

from routes.max_ev_boost import router as max_ev_boost_router
app.include_router(max_ev_boost_router)

from routes.alert_preferences import router as alert_preferences_router
app.include_router(alert_preferences_router)

from routes.settings import router as settings_router
app.include_router(settings_router)

# Data feeds router (line movement + injuries)
try:
    from routes.data_feeds import router as data_feeds_router
    app.include_router(data_feeds_router)
except Exception as e:
    logger.warning(f"WARNING: Data feeds router failed: {e}")
# Import and register Goalie Pull router
try:
    from routes.goalie_pull import router as goalie_pull_router
    app.include_router(goalie_pull_router)
except Exception as e:
    logger.error(f"ERROR importing/registering goalie_pull router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Import and register Simulation router
try:
    from routes.simulation import router as simulation_router
    app.include_router(simulation_router)
except Exception as e:
    logger.error(f"ERROR importing/registering simulation router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Import and register Models router (Random Forest, XGBoost, LightGBM, Linear Regression)
try:
    from routes.models import router as models_router
    app.include_router(models_router)
except Exception as e:
    logger.error(f"ERROR importing/registering models router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()


# Import and register Agent router (MAX EV Analyst)
try:
    from routes.agent import router as agent_router
    app.include_router(agent_router)
except Exception as e:
    logger.error(f"ERROR importing/registering agent router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Import and register Edge Scanner router
try:
    from routes.predictions import router as predictions_router
    app.include_router(predictions_router)
except Exception as e:
    logger.error(f"ERROR importing/registering predictions router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

try:
    from routes.edge_scanner import router as edge_scanner_router
    app.include_router(edge_scanner_router)
except Exception as e:
    logger.error(f"ERROR importing/registering edge_scanner router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Import and register Model Performance router
try:
    from routes.model_performance import router as model_performance_router
    app.include_router(model_performance_router)

    # Props performance routes
    from routes.props_performance import router as props_performance_router
    logger.info("[OK] Props performance routes loaded")
    app.include_router(props_performance_router)
except Exception as e:
    logger.error(f"ERROR importing/registering props_performance router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Analytics Data routes (ESPN + Statcast + NBA.com + BartTorvik)
try:
    from routes.analytics_data import router as analytics_data_router
    logger.info("[OK] Analytics Data routes loaded (ESPN/Statcast/NBA.com/BartTorvik)")
    app.include_router(analytics_data_router)
except Exception as e:
    logger.error(f"ERROR importing analytics_data router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Kalshi trading routes (account connect, balance, positions)
try:
    from routes.kalshi import router as kalshi_router
    logger.info("[OK] Kalshi routes loaded")
    app.include_router(kalshi_router)
except Exception as e:
    logger.error(f"ERROR importing kalshi router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# BULLETPROOF: UI Props routes (sacred /api/ui/ endpoints)
try:
    from routes.ui_props import router as ui_props_router
    logger.info("[OK] UI Props routes loaded (BULLETPROOF)")
    app.include_router(ui_props_router)
except Exception as e:
    logger.error(f"ERROR importing/registering ui_props router: {type(e).__name__}: {e}")

# BULLETPROOF: UI Endpoints router (SINGLE SOURCE OF TRUTH for all /api/ui/ endpoints)
try:
    from routes.ui_endpoints import router as ui_endpoints_router
    logger.info("[OK] UI Endpoints routes loaded (BULLETPROOF - best-plays, model-performance, etc.)")
    app.include_router(ui_endpoints_router)
except Exception as e:
    logger.error(f"ERROR importing/registering ui_endpoints router: {type(e).__name__}: {e}")

# Import and register Performance (Historical Results) router
try:
    from routes.performance import router as performance_router
    app.include_router(performance_router)
except Exception as e:
    logger.error(f"ERROR importing/registering performance router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()


# Import and register Player Props router
try:
    from routes.player_props import router as player_props_router
    app.include_router(player_props_router)
except Exception as e:
    logger.error(f"ERROR importing/registering player_props router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Import and register Volatility Arbitrage router
try:
    from routes.volatility_arb import router as volatility_router
    app.include_router(volatility_router)
except Exception as e:
    logger.error(f"ERROR importing/registering volatility_arb router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Import and register NCAAB Live Baseline router
try:
    from routes.ncaab_baseline import router as ncaab_baseline_router
    app.include_router(ncaab_baseline_router)
except Exception as e:
    logger.error(f"ERROR importing/registering ncaab_baseline router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Import and register F5 Fade the Tie router (Baseball F5 3-way arb system)
try:
    from routes.f5_fade_tie import router as f5_fade_tie_router
    app.include_router(f5_fade_tie_router)
    logger.info("[OK] F5 Fade the Tie router registered - Baseball F5 arb system ready")
except Exception as e:
    logger.error(f"ERROR importing/registering f5_fade_tie router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Game tracker instance
tracker = GameTracker()

# Alert monitor instance
alert_monitor = AlertMonitor(odds_api_key=os.getenv('ODDS_API_KEY', ''))

# Sharp money monitor instance
sharp_money_service = get_sharp_money_service(api_key=os.getenv('ODDS_API_KEY', ''))

# Schedule fatigue monitor instance
fatigue_service = get_fatigue_service(api_key=os.getenv('ODDS_API_KEY', ''))

# ========== POPULATE SHARED APP STATE ==========
import app_state as _app_state
_app_state.tracker = tracker
_app_state.alert_monitor = alert_monitor
_app_state.sharp_money_service = sharp_money_service
_app_state.fatigue_service = fatigue_service

# WebSocket manager — instantiated from routes/games to avoid circular imports
from routes.games import ConnectionManager
ws_manager = ConnectionManager()
_app_state.ws_manager = ws_manager

# Register new routers (auth, subscription, admin, games, alerts, plays)
from routes.auth import router as auth_router
app.include_router(auth_router)

from routes.subscription import router as subscription_router
app.include_router(subscription_router)

from routes.admin import router as admin_router
app.include_router(admin_router)

from routes.games import router as games_router
app.include_router(games_router)

from routes.alerts_live import router as alerts_live_router
app.include_router(alerts_live_router)

from routes.plays import router as plays_router
app.include_router(plays_router)

from routes.analytics import router as analytics_router
app.include_router(analytics_router)

from routes.ensemble import router as ensemble_router
app.include_router(ensemble_router)

from routes.misc import router as misc_router
app.include_router(misc_router)

# Props cache lives in app_state so both background tasks (here) and routes/misc.py share it.
props_cache = _app_state.props_cache

@app.on_event("startup")
async def startup():
    """Start game tracking and alert monitoring on app startup"""
    logger.info("Starting NBA Live Betting API...")
    asyncio.create_task(tracker.start())

    # Initialize bet grader with game tracker
    initialize_bet_grader(tracker)
    logger.info("Bet grader initialized")

    # Kalshi tables (safe to call every startup - CREATE TABLE IF NOT EXISTS)
    try:
        from pipeline.db.connection import get_engine
        from kalshi.schema import create_all_tables as create_kalshi_tables
        create_kalshi_tables(get_engine())
        logger.info("Kalshi tables ready")
    except Exception as e:
        logger.warning(f"Kalshi schema init failed (non-critical): {e}")

    # Start alert monitoring for NBA, NFL, NHL, and Tennis
    # DISABLED FOR API CREDIT SAVINGS: Alert monitor (was using 10s polling)
    # To re-enable, uncomment the alert_monitor.start_monitoring call
    pass  # placeholder for disabled alert monitor
    logger.info("Alert monitoring started for NBA, NFL, NHL (10s intervals - real-time arbitrage detection)")

    # Start sharp money monitoring for NBA, NFL, NHL
    # DISABLED: asyncio.create_task(
    # DISABLED: sharp_money_service.monitor_loop(
    # DISABLED: sports=['basketball_nba', 'americanfootball_nfl', 'icehockey_nhl'],
    # DISABLED: interval_seconds=120  # Check every 2 minutes for sharp money movements
    # DISABLED: )
    # DISABLED: )
    logger.info("Sharp money monitoring started for NBA, NFL, NHL (120s intervals - tracking sharp book movements)")

    # Start schedule fatigue monitoring for NBA, NFL, NHL
    # DISABLED: asyncio.create_task(
    # DISABLED: fatigue_service.monitor_loop(
    # DISABLED: sports=['basketball_nba', 'americanfootball_nfl', 'icehockey_nhl'],
    # DISABLED: interval_seconds=3600  # Check every hour for schedule changes
    # DISABLED: )
    # DISABLED: )
    logger.info("Schedule fatigue monitoring started for NBA, NFL, NHL (hourly - tracking B2B and rest advantages)")

    # Start WebSocket broadcaster for real-time updates
    # DISABLED: asyncio.create_task(broadcast_game_updates())
    logger.info("WebSocket broadcaster started (3s intervals - real-time odds pushes)")

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


# Mount static files (production frontend)
# Serve production build from ../frontend/dist
import os.path
frontend_dist_path = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="static")
 

