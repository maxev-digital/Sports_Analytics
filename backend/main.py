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
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio
import logging
import time
import json
from datetime import datetime
from dotenv import load_dotenv

# Betting ensemble temporarily disabled to avoid import conflicts
# from backend.models.ensemble.betting_ensemble import BettingEnsemble, GameData, EnsemblePrediction
BettingEnsemble = None
GameData = None
EnsemblePrediction = None

load_dotenv(dotenv_path='../../../.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NBA Live Betting API")

# CORS for local development - allow all local ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
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
    ],
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

# Mount static files (production frontend)
# Serve production build from ../frontend/dist
import os.path
frontend_dist_path = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="static")


