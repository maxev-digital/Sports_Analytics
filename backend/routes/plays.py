"""Play tracking routes — log, result, query, dashboard"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from plays_database import plays_db

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plays", tags=["plays"])


# ========== REQUEST MODELS ==========

class RecommendedPlayRequest(BaseModel):
    game_id: str
    sport: str = "NBA"
    home_team: str
    away_team: str
    game_time: str
    strategy_name: str
    strategy_category: str
    confidence_level: str  # HIGH, MEDIUM, LOW
    play_type: str          # TOTALS, SPREAD, MONEYLINE, PROP
    recommended_side: str
    recommended_line: Optional[float] = None
    recommended_price: int
    best_book: str
    alternate_books: Optional[List[Dict[str, Any]]] = None
    our_probability: float
    market_probability: float
    edge_percentage: float
    expected_value: float
    momentum_indicator: Optional[str] = None
    trend_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class PlayResultRequest(BaseModel):
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


# ========== ENDPOINTS ==========

@router.post("/log")
async def log_recommended_play(request: RecommendedPlayRequest):
    """Log a new recommended play with strategy, edge, and bookmaker details."""
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


@router.post("/result")
async def record_play_result(request: PlayResultRequest):
    """Record the result of a recommended play."""
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


@router.get("/all")
async def get_all_plays(limit: int = 100, status: Optional[str] = None):
    """Get all recommended plays with optional status filter (pending/won/lost/push)."""
    try:
        plays = plays_db.get_all_plays(limit=limit, status=status)
        return {"count": len(plays), "plays": plays}
    except Exception as e:
        logger.error(f"Error fetching plays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch plays: {str(e)}")


@router.get("/pending")
async def get_pending_plays():
    """Get all plays waiting for results."""
    try:
        plays = plays_db.get_pending_plays()
        return {"count": len(plays), "pending_plays": plays}
    except Exception as e:
        logger.error(f"Error fetching pending plays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pending plays: {str(e)}")


@router.get("/recent")
async def get_recent_results(days: int = 7):
    """Get recent settled plays (last N days)."""
    try:
        plays = plays_db.get_recent_results(days=days)
        return {"count": len(plays), "days": days, "plays": plays}
    except Exception as e:
        logger.error(f"Error fetching recent results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent results: {str(e)}")


@router.get("/categories")
async def get_alert_categories():
    """Get all alert categories with display names and icons."""
    try:
        categories = plays_db.get_alert_categories()
        return {"count": len(categories), "categories": categories}
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch categories: {str(e)}")


@router.get("/dashboard")
async def get_plays_dashboard():
    """Comprehensive plays dashboard — categories, pending, recent, performance."""
    try:
        categories = plays_db.get_alert_categories()
        pending = plays_db.get_pending_plays()
        recent = plays_db.get_recent_results(days=7)
        performance = plays_db.get_strategy_performance()

        category_plays = {}
        for cat in categories:
            cat_plays = plays_db.get_plays_by_category(cat['category_name'], limit=10)
            category_plays[cat['category_name']] = {
                "display_name": cat['display_name'],
                "description": cat['description'],
                "color": cat['color_code'],
                "icon": cat['icon'],
                "count": len(cat_plays),
                "recent_plays": cat_plays[:5]
            }

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


@router.get("/performance")
async def get_all_strategy_performance():
    """Get performance metrics for all strategies — win rate, profit, ROI."""
    try:
        performance = plays_db.get_strategy_performance()
        return {"count": len(performance), "strategies": performance}
    except Exception as e:
        logger.error(f"Error fetching performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance: {str(e)}")


@router.get("/performance/by-sport")
async def get_performance_by_sport(sport: Optional[str] = None):
    """Get performance metrics grouped by sport."""
    try:
        performance = plays_db.get_performance_by_sport(sport=sport)
        return {"sport_filter": sport, "sports": performance}
    except Exception as e:
        logger.error(f"Error fetching sport performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sport performance: {str(e)}")


@router.get("/performance/{strategy_name}")
async def get_strategy_specific_performance(strategy_name: str):
    """Get detailed performance for a specific strategy."""
    try:
        performance = plays_db.get_strategy_performance(strategy_name=strategy_name)
        if not performance:
            return {"strategy": strategy_name, "message": "No performance data found", "performance": None}
        return {"strategy": strategy_name, "performance": performance[0]}
    except Exception as e:
        logger.error(f"Error fetching strategy performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance: {str(e)}")


@router.get("/strategy/{strategy_name}")
async def get_plays_by_strategy(strategy_name: str, limit: int = 50):
    """Get all plays for a specific strategy."""
    try:
        plays = plays_db.get_plays_by_strategy(strategy_name, limit=limit)
        return {"strategy": strategy_name, "count": len(plays), "plays": plays}
    except Exception as e:
        logger.error(f"Error fetching strategy plays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch strategy plays: {str(e)}")


@router.get("/category/{category}")
async def get_plays_by_category(category: str, limit: int = 50):
    """Get all plays for a specific alert category."""
    try:
        plays = plays_db.get_plays_by_category(category, limit=limit)
        return {"category": category, "count": len(plays), "plays": plays}
    except Exception as e:
        logger.error(f"Error fetching category plays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch category plays: {str(e)}")


@router.get("/sport/{sport}")
async def get_plays_for_sport(sport: str, limit: int = 50):
    """Get all plays for a specific sport."""
    try:
        plays = plays_db.get_plays_by_sport(sport, limit=limit)
        return {"sport": sport, "count": len(plays), "plays": plays}
    except Exception as e:
        logger.error(f"Error fetching sport plays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sport plays: {str(e)}")
