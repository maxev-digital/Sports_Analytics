"""
Live alert routes — arbitrage, steam moves, middles, sharp money,
schedule fatigue, empty-net, volatility-arb, injuries.

All routes read from app_state singletons set at startup.
"""
import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

import app_state
from settings_database import settings_db
from storage.alert_storage import alert_storage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["alerts"])


# ========== INJURY / GOALIE ENDPOINTS ==========

@router.get("/api/goalie-pull-opportunities")
async def get_goalie_pull_opportunities():
    """Get all current NHL goalie pull betting opportunities."""
    tracker = app_state.tracker
    opportunities = tracker.get_goalie_pull_opportunities()
    return {"count": len(opportunities), "opportunities": opportunities}


@router.get("/api/injuries/props")
async def get_injury_props_opportunities():
    """Get all current injury props betting opportunities (60-second window)."""
    tracker = app_state.tracker
    opportunities = tracker.get_injury_props_opportunities()

    serialized = []
    for opp in opportunities:
        if hasattr(opp, '__dict__'):
            serialized.append({
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
            })
        else:
            serialized.append(opp)

    return {"count": len(serialized), "opportunities": serialized}


@router.get("/api/injuries/alerts")
async def get_injury_alerts():
    """
    Get real-time injury alerts from the standalone monitoring service.
    Reads from a shared JSON file written by injury_monitor_service.py.
    """
    alerts_file = Path(__file__).parent.parent / "data" / "injury_alerts.json"

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

        return {"count": len(alerts), "alerts": alerts, "status": "ok"}

    except Exception as e:
        logger.error(f"Error reading injury alerts: {e}")
        return {"count": 0, "alerts": [], "status": "error", "message": str(e)}


# ========== ALERT ENDPOINTS ==========

def _serialize_arb(alert) -> dict:
    return {
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


def _serialize_middle(alert) -> dict:
    return {
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


@router.get("/api/alerts/arbitrage")
async def get_arbitrage_alerts(user_id: str = 'default'):
    """Get arbitrage opportunities filtered by user's enabled bookmakers."""
    alert_monitor = app_state.alert_monitor
    try:
        settings = settings_db.get_settings(user_id)
        enabled = set(settings['enabled_bookmakers']) if settings else None

        alerts = alert_monitor.active_alerts.get('arbitrage', [])
        if enabled:
            alerts = [a for a in alerts if a.book_a in enabled and a.book_b in enabled]

        return {"count": len(alerts), "alerts": [_serialize_arb(a) for a in alerts]}

    except Exception as e:
        logger.error(f"Error filtering arbitrage alerts: {str(e)}")
        alerts = alert_monitor.active_alerts.get('arbitrage', [])
        return {"count": len(alerts), "alerts": [_serialize_arb(a) for a in alerts]}


@router.get("/api/alerts/steam-moves")
async def get_steam_move_alerts(user_id: str = 'default'):
    """Get steam move alerts filtered by user's enabled bookmakers."""
    alert_monitor = app_state.alert_monitor
    try:
        settings = settings_db.get_settings(user_id)
        enabled = set(settings['enabled_bookmakers']) if settings else None

        alerts = alert_monitor.active_alerts.get('steam_moves', [])
        if enabled:
            alerts = [a for a in alerts if any(b in enabled for b in a.books_moved)]

        return {
            "count": len(alerts),
            "alerts": [
                {
                    "game_id": a.game_id,
                    "sport": a.sport,
                    "home_team": a.home_team,
                    "away_team": a.away_team,
                    "market_type": a.market_type,
                    "side": a.side,
                    "original_line": a.original_line,
                    "new_line": a.new_line,
                    "movement": round(a.movement, 1),
                    "books_moved": a.books_moved,
                    "consensus_percent": round(a.consensus_percent, 1),
                    "timestamp": a.timestamp.isoformat()
                }
                for a in alerts
            ]
        }

    except Exception as e:
        logger.error(f"Error filtering steam move alerts: {str(e)}")
        alerts = alert_monitor.active_alerts.get('steam_moves', [])
        return {
            "count": len(alerts),
            "alerts": [
                {
                    "game_id": a.game_id,
                    "sport": a.sport,
                    "home_team": a.home_team,
                    "away_team": a.away_team,
                    "market_type": a.market_type,
                    "side": a.side,
                    "original_line": a.original_line,
                    "new_line": a.new_line,
                    "movement": round(a.movement, 1),
                    "books_moved": a.books_moved,
                    "consensus_percent": round(a.consensus_percent, 1),
                    "timestamp": a.timestamp.isoformat()
                }
                for a in alerts
            ]
        }


@router.get("/api/alerts/middles")
async def get_middle_alerts(user_id: str = 'default'):
    """Get middle opportunity alerts filtered by user's enabled bookmakers."""
    alert_monitor = app_state.alert_monitor
    try:
        settings = settings_db.get_settings(user_id)
        enabled = set(settings['enabled_bookmakers']) if settings else None

        alerts = alert_monitor.active_alerts.get('middles', [])
        if enabled:
            alerts = [a for a in alerts if a.book_low in enabled and a.book_high in enabled]

        return {"count": len(alerts), "alerts": [_serialize_middle(a) for a in alerts]}

    except Exception as e:
        logger.error(f"Error filtering middle alerts: {str(e)}")
        alerts = alert_monitor.active_alerts.get('middles', [])
        return {"count": len(alerts), "alerts": [_serialize_middle(a) for a in alerts]}


@router.get("/api/alerts/sharp-money")
async def get_sharp_money_alerts(user_id: str = 'default'):
    """Get sharp money alerts filtered by user's enabled bookmakers."""
    try:
        settings = settings_db.get_settings(user_id)
        enabled = set(settings['enabled_bookmakers']) if settings else None

        tracked = alert_storage.get_alerts_by_type('sharp_money', status='pending', limit=50)

        alerts = []
        for ta in tracked:
            details = ta.strategy_details or {}
            if enabled:
                sharp_books = details.get('sharp_books_involved', [])
                if not any(b in enabled for b in sharp_books):
                    continue

            alerts.append({
                "game_id": ta.game_id,
                "sport": ta.sport,
                "home_team": ta.home_team,
                "away_team": ta.away_team,
                "alert_type": details.get('alert_type', 'sharp_money'),
                "market_type": ta.market_type,
                "recommendation": ta.recommended_side,
                "opening_line": details.get('opening_line'),
                "current_line": details.get('current_line'),
                "movement": details.get('movement'),
                "sharp_books_involved": details.get('sharp_books_involved', []),
                "confidence": details.get('confidence', 0),
                "confidence_level": details.get('confidence_level', 'MEDIUM'),
                "reasoning": details.get('reasoning', ''),
                "key_factors": details.get('key_factors', []),
                "edge_percent": ta.edge_percent,
                "timestamp": ta.generated_at.isoformat(),
                "id": ta.id
            })

        return {"count": len(alerts), "alerts": alerts}

    except Exception as e:
        logger.error(f"Error fetching sharp money alerts: {str(e)}")
        return {"count": 0, "alerts": [], "error": str(e)}


@router.get("/api/alerts/schedule-fatigue")
async def get_schedule_fatigue_alerts(user_id: str = 'default'):
    """Get schedule fatigue alerts."""
    try:
        tracked = alert_storage.get_alerts_by_type('schedule_fatigue', status='pending', limit=50)

        alerts = []
        for ta in tracked:
            details = ta.strategy_details or {}
            alerts.append({
                "game_id": ta.game_id,
                "sport": ta.sport,
                "home_team": ta.home_team,
                "away_team": ta.away_team,
                "fatigue_type": details.get('fatigue_type', 'rest_advantage'),
                "favored_side": details.get('favored_side', 'home'),
                "recommended_side": ta.recommended_side,
                "home_rest_days": details.get('home_rest_days', 0),
                "away_rest_days": details.get('away_rest_days', 0),
                "rest_differential": details.get('rest_differential', 0),
                "home_is_b2b": details.get('home_is_b2b', False),
                "away_is_b2b": details.get('away_is_b2b', False),
                "confidence": details.get('confidence', 0),
                "confidence_level": details.get('confidence_level', 'MEDIUM'),
                "reasoning": details.get('reasoning', ''),
                "key_factors": details.get('key_factors', []),
                "edge_percent": ta.edge_percent,
                "timestamp": ta.generated_at.isoformat(),
                "id": ta.id
            })

        return {"count": len(alerts), "alerts": alerts}

    except Exception as e:
        logger.error(f"Error fetching schedule fatigue alerts: {str(e)}")
        return {"count": 0, "alerts": [], "error": str(e)}


@router.get("/api/alerts/all")
async def get_all_alerts(user_id: str = 'default'):
    """Get all alert types filtered by user's enabled bookmakers."""
    alert_monitor = app_state.alert_monitor
    try:
        settings = settings_db.get_settings(user_id)
        enabled = set(settings['enabled_bookmakers']) if settings else None

        arb_alerts = alert_monitor.active_alerts.get('arbitrage', [])
        steam_alerts = alert_monitor.active_alerts.get('steam_moves', [])
        middle_alerts = alert_monitor.active_alerts.get('middles', [])
        sharp_tracked = alert_storage.get_alerts_by_type('sharp_money', status='pending', limit=50)
        fatigue_tracked = alert_storage.get_alerts_by_type('schedule_fatigue', status='pending', limit=50)

        if enabled:
            arb_alerts = [a for a in arb_alerts if a.book_a in enabled and a.book_b in enabled]
            steam_alerts = [a for a in steam_alerts if any(b in enabled for b in a.books_moved)]
            middle_alerts = [a for a in middle_alerts if a.book_low in enabled and a.book_high in enabled]
            sharp_tracked = [
                ta for ta in sharp_tracked
                if any(b in enabled for b in (ta.strategy_details or {}).get('sharp_books_involved', []))
            ]

        return {
            "arbitrage": {"count": len(arb_alerts), "alerts": arb_alerts},
            "steam_moves": {"count": len(steam_alerts), "alerts": steam_alerts},
            "middles": {"count": len(middle_alerts), "alerts": [_serialize_middle(a) for a in middle_alerts]},
            "sharp_money": {
                "count": len(sharp_tracked),
                "alerts": [
                    {
                        "game_id": ta.game_id,
                        "sport": ta.sport,
                        "home_team": ta.home_team,
                        "away_team": ta.away_team,
                        "alert_type": (ta.strategy_details or {}).get('alert_type', 'sharp_money'),
                        "market_type": ta.market_type,
                        "recommendation": ta.recommended_side,
                        "confidence_level": (ta.strategy_details or {}).get('confidence_level', 'MEDIUM'),
                        "sharp_books_involved": (ta.strategy_details or {}).get('sharp_books_involved', []),
                        "timestamp": ta.generated_at.isoformat(),
                        "id": ta.id
                    }
                    for ta in sharp_tracked
                ]
            },
            "schedule_fatigue": {
                "count": len(fatigue_tracked),
                "alerts": [
                    {
                        "game_id": ta.game_id,
                        "sport": ta.sport,
                        "home_team": ta.home_team,
                        "away_team": ta.away_team,
                        "fatigue_type": (ta.strategy_details or {}).get('fatigue_type', 'rest_advantage'),
                        "favored_side": (ta.strategy_details or {}).get('favored_side', 'home'),
                        "recommended_side": ta.recommended_side,
                        "confidence_level": (ta.strategy_details or {}).get('confidence_level', 'MEDIUM'),
                        "rest_differential": (ta.strategy_details or {}).get('rest_differential', 0),
                        "timestamp": ta.generated_at.isoformat(),
                        "id": ta.id
                    }
                    for ta in fatigue_tracked
                ]
            },
            "last_updated": alert_monitor.active_alerts.get('last_updated')
        }

    except Exception as e:
        logger.error(f"Error fetching all alerts: {str(e)}")
        alert_monitor = app_state.alert_monitor
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
            "middles": {"count": len(middles_raw), "alerts": [_serialize_middle(a) for a in middles_raw]},
            "sharp_money": {"count": 0, "alerts": []},
            "schedule_fatigue": {"count": 0, "alerts": []},
            "last_updated": alert_monitor.active_alerts.get('last_updated')
        }


@router.get("/api/alerts/config")
async def get_alert_config():
    """Get current alert configuration."""
    alert_monitor = app_state.alert_monitor
    return {
        "arbitrage_min_profit": alert_monitor.arbitrage_min_profit,
        "steam_move_threshold": alert_monitor.steam_move_threshold,
        "line_movement_threshold": alert_monitor.line_movement_threshold,
        "monitored_sports": ['basketball_nba', 'americanfootball_nfl', 'icehockey_nhl'],
        "refresh_interval_seconds": 10
    }


@router.get("/api/alerts/performance")
async def get_alert_performance():
    """Get performance stats for all alert types."""
    alert_monitor = app_state.alert_monitor

    def _safe_stats(alert_type: str) -> dict:
        if alert_type in alert_monitor.performance_stats:
            s = alert_monitor.performance_stats[alert_type]
            return {
                "total_alerts": s.total_alerts,
                "successful_alerts": s.successful_alerts,
                "failed_alerts": s.failed_alerts,
                "pending_alerts": s.pending_alerts,
                "win_rate": s.win_rate,
                "avg_profit": s.avg_profit,
                "total_profit": s.total_profit,
            }
        return {
            "total_alerts": 0, "successful_alerts": 0, "failed_alerts": 0,
            "pending_alerts": 0, "win_rate": 0.0, "avg_profit": 0.0, "total_profit": 0.0,
        }

    return {
        "arbitrage": _safe_stats('arbitrage'),
        "steam_moves": _safe_stats('steam_moves'),
        "middles": _safe_stats('middles')
    }


@router.get("/api/alerts/empty-net")
async def get_empty_net_alerts(user_id: str = 'default'):
    """Get NHL empty net / goalie pull alerts."""
    try:
        tracked = alert_storage.get_alerts_by_type('empty_net', status='pending', limit=50)
        alerts = [
            {
                'id': ta.id,
                'game_id': ta.game_id,
                'sport': ta.sport,
                'home_team': ta.home_team,
                'away_team': ta.away_team,
                'commence_time': ta.commence_time,
                'market_type': ta.market_type,
                'recommended_side': ta.recommended_side,
                'recommended_odds': ta.recommended_odds,
                'recommended_bookmaker': ta.recommended_bookmaker,
                'confidence': ta.confidence,
                'edge_percent': ta.edge_percent,
                'profit_potential': ta.profit_potential,
                'generated_at': ta.generated_at,
                'status': ta.status,
                'strategy_details': ta.strategy_details or {}
            }
            for ta in tracked
        ]
        return {'count': len(alerts), 'alerts': alerts, 'alert_type': 'empty_net'}

    except Exception as e:
        logger.error(f"Error getting empty net alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/alerts/volatility-arb")
async def get_volatility_arb_alerts(user_id: str = 'default'):
    """Get volatility arbitrage hedge alerts."""
    try:
        tracked = alert_storage.get_alerts_by_type('volatility_arb', status='pending', limit=50)
        alerts = [
            {
                'id': ta.id,
                'game_id': ta.game_id,
                'sport': ta.sport,
                'home_team': ta.home_team,
                'away_team': ta.away_team,
                'commence_time': ta.commence_time,
                'market_type': ta.market_type,
                'recommended_side': ta.recommended_side,
                'recommended_odds': ta.recommended_odds,
                'recommended_bookmaker': ta.recommended_bookmaker,
                'confidence': ta.confidence,
                'edge_percent': ta.edge_percent,
                'profit_potential': ta.profit_potential,
                'generated_at': ta.generated_at,
                'status': ta.status,
                'strategy_details': ta.strategy_details or {}
            }
            for ta in tracked
        ]
        return {'count': len(alerts), 'alerts': alerts, 'alert_type': 'volatility_arb'}

    except Exception as e:
        logger.error(f"Error getting volatility arb alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
