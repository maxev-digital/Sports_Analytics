"""
Volatility Arbitrage API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import logging

from strategies.volatility_arbitrage import (
    VolatilityArbDetector,
    VolatilityPositionTracker,
    EntryOpportunity,
    VolatilityPosition,
    HedgeAlert
)
from database.volatility_positions_db import volatility_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/volatility", tags=["volatility"])

# Global instances (will be initialized in main.py)
detector = VolatilityArbDetector()
position_tracker = VolatilityPositionTracker()


# Pydantic models for API
class PositionCreate(BaseModel):
    """Request to create new position"""
    user_id: str
    game_id: str
    sport: str
    home_team: str
    away_team: str
    entry_team: str
    entry_side: str
    entry_odds: int
    entry_stake: float
    entry_bookmaker: str
    trigger_price: int
    trigger_min_profit: float
    entry_quarter: Optional[str] = ''
    entry_score: Optional[str] = ''


class HedgeExecute(BaseModel):
    """Request to execute hedge"""
    hedge_stake: float
    hedge_odds: int
    hedge_bookmaker: str


class PositionClose(BaseModel):
    """Request to close position"""
    winning_team: str


@router.get("/opportunities")
async def get_entry_opportunities(
    user_id: str = Query(..., description="User ID"),
    sport: Optional[str] = Query(None, description="Filter by sport")
):
    """
    Get current entry opportunities for volatility arbitrage

    Returns list of +EV positions at +money odds
    """
    try:
        # This would normally integrate with game_tracker
        # For now, return placeholder
        # In production, would call:
        # opportunities = detector.detect_entry_opportunities(live_games, ml_predictions)

        return {
            'opportunities': [],
            'count': 0,
            'last_updated': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting entry opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/positions")
async def create_position(position: PositionCreate):
    """
    Create new volatility arbitrage position

    User enters first leg of position
    """
    try:
        # Create position in tracker
        vol_position = position_tracker.create_position(
            user_id=position.user_id,
            game_id=position.game_id,
            sport=position.sport,
            home_team=position.home_team,
            away_team=position.away_team,
            entry_team=position.entry_team,
            entry_side=position.entry_side,
            entry_odds=position.entry_odds,
            entry_stake=position.entry_stake,
            entry_bookmaker=position.entry_bookmaker,
            trigger_price=position.trigger_price,
            trigger_min_profit=position.trigger_min_profit,
            entry_quarter=position.entry_quarter,
            entry_score=position.entry_score
        )

        # Save to database
        volatility_db.create_position({
            'id': vol_position.id,
            'user_id': vol_position.user_id,
            'game_id': vol_position.game_id,
            'sport': vol_position.sport,
            'home_team': vol_position.home_team,
            'away_team': vol_position.away_team,
            'first_team': vol_position.first_team,
            'first_side': vol_position.first_side,
            'first_odds': vol_position.first_odds,
            'first_stake': vol_position.first_stake,
            'first_timestamp': vol_position.first_timestamp.isoformat(),
            'first_bookmaker': vol_position.first_bookmaker,
            'trigger_price': vol_position.trigger_price,
            'trigger_min_profit': vol_position.trigger_min_profit,
            'entry_quarter': vol_position.entry_quarter,
            'entry_score': vol_position.entry_score
        })

        return {
            'success': True,
            'position': vol_position.to_dict(),
            'message': 'Position created successfully'
        }

    except Exception as e:
        logger.error(f"Error creating position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions(
    user_id: str = Query(..., description="User ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum results")
):
    """
    Get user's volatility arbitrage positions

    Returns positions with current status and profit
    """
    try:
        positions = volatility_db.get_user_positions(user_id, status, limit)

        return {
            'positions': positions,
            'count': len(positions)
        }

    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions/{position_id}")
async def get_position(position_id: str):
    """Get specific position by ID"""
    try:
        position = volatility_db.get_position(position_id)

        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        return position

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting position {position_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/positions/{position_id}/hedge")
async def execute_hedge(position_id: str, hedge: HedgeExecute):
    """
    Execute hedge on open position

    Takes opposite side to lock in profit
    """
    try:
        # Get position from tracker
        position = position_tracker.get_position(position_id)

        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        if position.status != 'open':
            raise HTTPException(status_code=400, detail=f"Position is {position.status}, cannot hedge")

        # Execute hedge in tracker
        updated_position = position_tracker.execute_hedge(
            position_id,
            hedge.hedge_stake,
            hedge.hedge_odds,
            hedge.hedge_bookmaker
        )

        # Update database
        opposite_team = position.away_team if position.first_side == 'home' else position.home_team

        volatility_db.execute_hedge(position_id, {
            'second_team': opposite_team,
            'second_odds': hedge.hedge_odds,
            'second_stake': hedge.hedge_stake,
            'second_timestamp': datetime.now().isoformat(),
            'second_bookmaker': hedge.hedge_bookmaker,
            'locked_profit': updated_position.locked_profit
        })

        return {
            'success': True,
            'position': updated_position.to_dict(),
            'locked_profit': updated_position.locked_profit,
            'message': f'Hedge executed - locked ${updated_position.locked_profit:.2f} profit'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing hedge on position {position_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/positions/{position_id}/close")
async def close_position(position_id: str, close_data: PositionClose):
    """
    Manually close position (when game ends)

    Calculates final profit based on winner
    """
    try:
        # Close in tracker
        closed_position = position_tracker.close_position(position_id, close_data.winning_team)

        if not closed_position:
            raise HTTPException(status_code=404, detail="Position not found")

        # Update database
        status = 'closed_won' if closed_position.actual_profit > 0 else 'closed_lost'
        volatility_db.close_position(position_id, closed_position.actual_profit, status)

        return {
            'success': True,
            'position': closed_position.to_dict(),
            'actual_profit': closed_position.actual_profit,
            'message': f'Position closed - {status}'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing position {position_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_hedge_alerts(user_id: str = Query(..., description="User ID")):
    """
    Get active hedge alerts for user

    Returns alerts when opposite side hits trigger price
    """
    try:
        # This would normally be called by background scanner
        # For now, return empty
        # In production: alerts = position_tracker.check_hedge_triggers(live_games, ml_predictions)

        open_positions = position_tracker.get_open_positions(user_id)

        return {
            'alerts': [],
            'open_positions': len(open_positions),
            'last_checked': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting hedge alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance(
    user_id: str = Query(..., description="User ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)")
):
    """
    Get volatility arbitrage performance statistics

    Returns profit, ROI, trigger rate, etc.
    """
    try:
        stats = volatility_db.get_performance_stats(user_id, start_date, end_date)

        # Calculate additional metrics
        total = stats['total_positions']
        hedged = stats['hedged_positions']

        actual_trigger_rate = (hedged / total * 100) if total > 0 else 0
        expected_trigger_rate = 35.0  # From config

        # Expected profit (using 15.7% EV from config)
        expected_profit = stats['total_wagered'] * 0.157

        variance = stats['total_profit'] - expected_profit
        variance_pct = (variance / expected_profit * 100) if expected_profit > 0 else 0

        return {
            **stats,
            'actual_trigger_rate': round(actual_trigger_rate, 1),
            'expected_trigger_rate': expected_trigger_rate,
            'expected_profit': round(expected_profit, 2),
            'variance': round(variance, 2),
            'variance_percent': round(variance_pct, 1),
            'start_date': start_date,
            'end_date': end_date
        }

    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_strategy_info():
    """
    Get information about volatility arbitrage strategy

    Returns expected EV, trigger rates, bankroll requirements
    """
    from strategies.volatility_arbitrage.config import (
        EXPECTED_EV_PER_ATTEMPT,
        HEDGE_TRIGGER_RATE,
        BANKROLL_REQUIREMENTS,
        SPORT_VOLATILITY
    )

    return {
        'expected_ev_per_attempt': EXPECTED_EV_PER_ATTEMPT,
        'expected_trigger_rate': HEDGE_TRIGGER_RATE,
        'bankroll_requirements': {
            str(k): {
                'aggressive': v[0],
                'standard': v[1],
                'conservative': v[2]
            }
            for k, v in BANKROLL_REQUIREMENTS.items()
        },
        'sport_volatility': SPORT_VOLATILITY,
        'description': 'Hybrid volatility arbitrage - enter +money positions during favorable game states, optionally hedge when opposite side reaches target price'
    }
