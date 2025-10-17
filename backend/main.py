"""FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from game_tracker import GameTracker
from models import LiveGame
from alert_monitor import AlertMonitor, ArbitrageAlert, SteamMoveAlert, LineMovementAlert
from typing import List, Dict, Any
import asyncio
import logging
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='../../../.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NBA Live Betting API")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Game tracker instance
tracker = GameTracker()

# Alert monitor instance
alert_monitor = AlertMonitor(odds_api_key=os.getenv('ODDS_API_KEY', ''))

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

@app.on_event("shutdown")
async def shutdown():
    """Stop tracking on shutdown"""
    await tracker.stop()

@app.get("/")
async def root():
    return {"message": "NBA Live Betting API", "status": "running"}

@app.get("/api/games", response_model=List[LiveGame])
async def get_games():
    """Get all live games"""
    return tracker.get_all_games()

@app.get("/api/games/{game_id}", response_model=LiveGame)
async def get_game(game_id: str):
    """Get specific game"""
    game = tracker.get_game(game_id)
    if not game:
        return {"error": "Game not found"}
    return game

@app.get("/api/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "games_tracked": len(tracker.games)
    }

# ========== ALERT ENDPOINTS ==========

@app.get("/api/alerts/arbitrage")
async def get_arbitrage_alerts():
    """Get all current arbitrage opportunities"""
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
async def get_steam_move_alerts():
    """Get all current steam move alerts"""
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
async def get_line_movement_alerts():
    """Get all current line movement alerts"""
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
async def get_all_alerts():
    """Get all alerts (arbitrage, steam moves, line movements)"""
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

