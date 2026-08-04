"""Analytics engine routes — live odds analytics, edge, momentum, strategy performance."""
import time
import logging

from fastapi import APIRouter, HTTPException

from live_analytics_engine import analytics_engine
import app_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
async def get_analytics_summary():
    """Comprehensive live analytics summary — latency, data freshness, strategy metrics."""
    return analytics_engine.get_live_summary()


@router.get("/latency")
async def get_latency_metrics():
    """Detailed latency metrics by endpoint."""
    return {
        "average_latency_ms": round(analytics_engine.get_average_latency(), 2),
        "by_endpoint": {
            endpoint: round(latency, 2)
            for endpoint, latency in analytics_engine.get_latency_by_endpoint().items()
        },
        "recent_calls": len(analytics_engine.latency_history),
    }


@router.get("/edge/{game_id}")
async def get_game_edge(game_id: str):
    """Edge calculations and true odds for a specific game."""
    if game_id not in analytics_engine.true_odds_cache:
        raise HTTPException(status_code=404, detail="No edge calculation found for this game")
    return {
        "current": analytics_engine.true_odds_cache[game_id],
        "movement": analytics_engine.get_edge_movement(game_id),
        "history": analytics_engine.edge_history.get(game_id, [])[-10:],
    }


@router.post("/calculate-edge")
async def calculate_edge(
    game_id: str,
    market_over: int = -110,
    market_under: int = -110,
    our_probability: float = 0.55,
):
    """Calculate edge given market odds and our win probability."""
    start = time.time()
    result = analytics_engine.calculate_true_odds(
        game_id=game_id,
        market_odds={"over": market_over, "under": market_under},
        our_probability=our_probability,
    )
    analytics_engine.track_latency("calculate_edge", (time.time() - start) * 1000)
    return result


@router.get("/momentum/{game_id}")
async def get_game_momentum(game_id: str):
    """Momentum trends (scoring, pace, shooting pct, etc.) for a specific game."""
    momentum_data = {}
    for key in analytics_engine.momentum_history.keys():
        if key.startswith(game_id):
            metric = key.split("_", 1)[1]
            momentum_data[metric] = analytics_engine.calculate_momentum_trend(game_id, metric)

    if not momentum_data:
        raise HTTPException(status_code=404, detail="No momentum data found for this game")

    return {"game_id": game_id, "metrics": momentum_data, "timestamp": time.time()}


@router.post("/update-momentum")
async def update_momentum(game_id: str, metric: str, value: float):
    """Update momentum tracking for a game metric."""
    analytics_engine.update_momentum(game_id, metric, value)
    analytics_engine.update_data_freshness(f"momentum_{game_id}")
    return {
        "game_id": game_id,
        "metric": metric,
        "value": value,
        "trend": analytics_engine.calculate_momentum_trend(game_id, metric),
    }


@router.get("/trends/{game_id}")
async def get_game_trends(game_id: str):
    """Detected trends for a game — line movement, sharp money, momentum shifts."""
    if game_id not in analytics_engine.trend_indicators:
        return {"game_id": game_id, "trends": None, "message": "No trend data available"}
    return analytics_engine.trend_indicators[game_id]


@router.get("/strategy-performance")
async def get_strategy_performance():
    """Performance metrics for all betting strategies."""
    return analytics_engine.get_strategy_performance()


@router.post("/record-result")
async def record_strategy_result(strategy_name: str, won: bool, edge: float):
    """Record the outcome of a strategy prediction for long-term tracking."""
    analytics_engine.update_strategy_performance(strategy_name, won, edge)
    return {
        "strategy": strategy_name,
        "result": "win" if won else "loss",
        "edge": edge,
        "updated_performance": analytics_engine.strategy_metrics.get(strategy_name, {}),
    }


@router.get("/data-freshness")
async def get_data_freshness():
    """Seconds since last update for each data source."""
    return {"sources": analytics_engine.get_data_freshness(), "timestamp": time.time()}


@router.get("/live-dashboard")
async def get_live_dashboard():
    """All analytics combined — edge, momentum, trends for current tracked games."""
    games = app_state.tracker.get_all_games() if app_state.tracker else []
    game_analytics = []
    for game in games[:5]:
        game_id = game.get("id", game.get("game_id", ""))
        momentum = {}
        for key in analytics_engine.momentum_history.keys():
            if key.startswith(game_id):
                metric = key.split("_", 1)[1]
                momentum[metric] = analytics_engine.calculate_momentum_trend(game_id, metric)
        game_analytics.append({
            "game": game,
            "edge": analytics_engine.true_odds_cache.get(game_id),
            "momentum": momentum or None,
            "trends": analytics_engine.trend_indicators.get(game_id),
        })
    return {
        "system_status": analytics_engine.get_live_summary(),
        "games": game_analytics,
        "timestamp": time.time(),
    }
