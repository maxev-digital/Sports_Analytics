"""
Max EV Boost API Routes
FastAPI endpoints for NBA and NCAAB regression-to-mean live analysis
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import sys
from pathlib import Path

# Add ML directory to path
ml_path = Path(__file__).parent.parent / "ml"
sys.path.append(str(ml_path))

from nba_regression_analyzer import NBARegressionAnalyzer
from ncaab_regression_analyzer import NCAABRegressionAnalyzer

router = APIRouter(prefix="/api/max-ev-boost", tags=["max-ev-boost"])

# Initialize analyzers (singleton pattern)
nba_analyzer = None
ncaab_analyzer = None


def get_nba_analyzer():
    """Lazy load NBA analyzer"""
    global nba_analyzer
    if nba_analyzer is None:
        nba_analyzer = NBARegressionAnalyzer()
    return nba_analyzer


def get_ncaab_analyzer():
    """Lazy load NCAAB analyzer"""
    global ncaab_analyzer
    if ncaab_analyzer is None:
        ncaab_analyzer = NCAABRegressionAnalyzer()
    return ncaab_analyzer


# ========== REQUEST/RESPONSE MODELS ==========

class NBAGameRequest(BaseModel):
    """Request model for NBA game analysis"""
    game_id: str = Field(..., description="Unique game identifier")
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")

    # Home team stats
    home_stats: Dict[str, float] = Field(..., description="Home team season statistics")

    # Away team stats
    away_stats: Dict[str, float] = Field(..., description="Away team season statistics")

    # Live betting line
    live_total: Optional[float] = Field(None, description="Current live total line")

    class Config:
        schema_extra = {
            "example": {
                "game_id": "nba_20250108_LAL_BOS",
                "home_team": "Los Angeles Lakers",
                "away_team": "Boston Celtics",
                "home_stats": {
                    "games_played": 35,
                    "wins": 22,
                    "win_pct": 0.629,
                    "ppg": 118.5,
                    "opp_ppg": 112.3,
                    "point_diff": 6.2,
                    "fg_pct": 0.478,
                    "fg3_pct": 0.371,
                    "ft_pct": 0.812,
                    "rebounds": 45.2,
                    "assists": 26.8,
                    "turnovers": 13.5,
                    "steals": 8.2,
                    "blocks": 5.1,
                    "plus_minus": 6.2,
                    "last_5_ppg": 121.2,
                    "last_10_ppg": 119.8,
                    "last_5_wins": 4,
                    "last_10_wins": 7
                },
                "away_stats": {
                    "games_played": 36,
                    "wins": 25,
                    "win_pct": 0.694,
                    "ppg": 122.1,
                    "opp_ppg": 110.5,
                    "point_diff": 11.6,
                    "fg_pct": 0.492,
                    "fg3_pct": 0.385,
                    "ft_pct": 0.825,
                    "rebounds": 47.3,
                    "assists": 28.2,
                    "turnovers": 12.8,
                    "steals": 7.9,
                    "blocks": 6.3,
                    "plus_minus": 11.6,
                    "last_5_ppg": 125.4,
                    "last_10_ppg": 123.2,
                    "last_5_wins": 5,
                    "last_10_wins": 8
                },
                "live_total": 235.5
            }
        }


class NCAABGameRequest(BaseModel):
    """Request model for NCAAB game analysis"""
    game_id: str = Field(..., description="Unique game identifier")
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")

    # KenPom stats
    home_stats: Dict[str, float] = Field(..., description="Home team KenPom statistics")
    away_stats: Dict[str, float] = Field(..., description="Away team KenPom statistics")

    # Live betting line
    live_total: Optional[float] = Field(None, description="Current live total line")

    class Config:
        schema_extra = {
            "example": {
                "game_id": "ncaab_20250108_DUKE_UNC",
                "home_team": "Duke",
                "away_team": "North Carolina",
                "home_stats": {
                    "adj_em": 28.5,
                    "off_eff": 118.2,
                    "def_eff": 89.7,
                    "tempo": 70.5
                },
                "away_stats": {
                    "adj_em": 25.3,
                    "off_eff": 115.8,
                    "def_eff": 90.5,
                    "tempo": 68.2
                },
                "live_total": 160.5
            }
        }


class MaxEVBoostResponse(BaseModel):
    """Response model for Max EV Boost analysis"""
    status: str = Field(..., description="success or error")
    game_id: str
    home_team: str
    away_team: str

    # Predictions
    predicted_mean: float
    predicted_lower: float
    predicted_upper: float
    std_dev: float

    # Alert information
    live_total: Optional[float]
    z_score: Optional[float]
    is_alert: bool
    alert_type: Optional[str] = Field(None, description="OVER or UNDER")
    confidence: str = Field(..., description="EXTREME, STRONG, MODERATE, or LOW")

    # Betting recommendation
    recommended_bet: Optional[str] = Field(None, description="OVER or UNDER if alert triggered")
    kelly_pct: float = Field(..., description="Recommended bet size as % of bankroll")

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "game_id": "nba_20250108_LAL_BOS",
                "home_team": "Los Angeles Lakers",
                "away_team": "Boston Celtics",
                "predicted_mean": 232.5,
                "predicted_lower": 218.3,
                "predicted_upper": 246.7,
                "std_dev": 11.1,
                "live_total": 235.5,
                "z_score": 0.27,
                "is_alert": False,
                "alert_type": None,
                "confidence": "LOW",
                "recommended_bet": None,
                "kelly_pct": 0.0
            }
        }


# ========== NBA ENDPOINTS ==========

@router.post("/nba/analyze", response_model=MaxEVBoostResponse)
async def analyze_nba_game(request: NBAGameRequest):
    """
    Analyze an NBA game for regression-to-mean betting opportunities

    **Max EV Boost Strategy (NBA)**
    - Uses XGBoost quantile regression trained on 3,690 NBA games
    - 66.3% win rate, +26.5% ROI in backtests (163 alerts)
    - Identifies when live totals drift 2+ standard deviations from prediction
    - Bets on statistical regression toward expected value

    **Confidence Levels:**
    - EXTREME: 2.5+ SD deviation (highest edge)
    - STRONG: 2.0-2.49 SD deviation
    - MODERATE: 1.5-1.99 SD deviation
    - LOW: <1.5 SD deviation (no bet recommended)

    **Kelly Sizing:**
    - Automatically calculates optimal bet size (3-5% of bankroll)
    - Based on historical win rates at each confidence level
    """
    try:
        analyzer = get_nba_analyzer()

        # Prepare game data for analyzer
        game_data = {
            'game_id': request.game_id,
            'home_team': request.home_team,
            'away_team': request.away_team,
            'home_stats': request.home_stats,
            'away_stats': request.away_stats,
            'live_total': request.live_total
        }

        # Run analysis
        result = analyzer.analyze_game(game_data)

        # Add metadata
        result['status'] = 'success'
        result['game_id'] = request.game_id
        result['home_team'] = request.home_team
        result['away_team'] = request.away_team

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NBA analysis failed: {str(e)}")


@router.post("/nba/analyze-batch", response_model=List[MaxEVBoostResponse])
async def analyze_nba_games_batch(requests: List[NBAGameRequest]):
    """
    Analyze multiple NBA games at once

    Useful for scanning all live games simultaneously to find alerts.
    """
    try:
        analyzer = get_nba_analyzer()

        results = []
        for request in requests:
            game_data = {
                'game_id': request.game_id,
                'home_team': request.home_team,
                'away_team': request.away_team,
                'home_stats': request.home_stats,
                'away_stats': request.away_stats,
                'live_total': request.live_total
            }

            result = analyzer.analyze_game(game_data)
            result['status'] = 'success'
            result['game_id'] = request.game_id
            result['home_team'] = request.home_team
            result['away_team'] = request.away_team

            results.append(result)

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NBA batch analysis failed: {str(e)}")


# ========== NCAAB ENDPOINTS ==========

@router.post("/ncaab/analyze", response_model=MaxEVBoostResponse)
async def analyze_ncaab_game(request: NCAABGameRequest):
    """
    Analyze an NCAAB game for regression-to-mean betting opportunities

    **Max EV Boost Strategy (NCAAB)**
    - Uses XGBoost quantile regression trained on 675 NCAAB games
    - 60.0% win rate, +14.5% ROI in backtests (30 alerts)
    - Features: KenPom efficiency ratings (AdjEM, OffEff, DefEff, Tempo)
    - Identifies when live totals drift 2+ standard deviations from prediction

    **Confidence Levels:**
    - EXTREME: 2.5+ SD deviation
    - STRONG: 2.0-2.49 SD deviation
    - MODERATE: 1.5-1.99 SD deviation
    - LOW: <1.5 SD deviation (no bet recommended)

    **Kelly Sizing:**
    - Automatically calculates optimal bet size (3-5% of bankroll)
    - Based on historical 60% win rate at 2+ SD threshold
    """
    try:
        analyzer = get_ncaab_analyzer()

        # Prepare game data for analyzer
        game_data = {
            'game_id': request.game_id,
            'home_team': request.home_team,
            'away_team': request.away_team,
            'home_stats': request.home_stats,
            'away_stats': request.away_stats,
            'live_total': request.live_total
        }

        # Run analysis
        result = analyzer.analyze_game(game_data)

        # Add metadata
        result['status'] = 'success'
        result['game_id'] = request.game_id
        result['home_team'] = request.home_team
        result['away_team'] = request.away_team

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NCAAB analysis failed: {str(e)}")


@router.post("/ncaab/analyze-batch", response_model=List[MaxEVBoostResponse])
async def analyze_ncaab_games_batch(requests: List[NCAABGameRequest]):
    """
    Analyze multiple NCAAB games at once

    Useful for scanning all live games simultaneously to find alerts.
    """
    try:
        analyzer = get_ncaab_analyzer()

        results = []
        for request in requests:
            game_data = {
                'game_id': request.game_id,
                'home_team': request.home_team,
                'away_team': request.away_team,
                'home_stats': request.home_stats,
                'away_stats': request.away_stats,
                'live_total': request.live_total
            }

            result = analyzer.analyze_game(game_data)
            result['status'] = 'success'
            result['game_id'] = request.game_id
            result['home_team'] = request.home_team
            result['away_team'] = request.away_team

            results.append(result)

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NCAAB batch analysis failed: {str(e)}")


# ========== UTILITY ENDPOINTS ==========

@router.get("/status")
async def get_max_ev_boost_status():
    """
    Get status of Max EV Boost systems

    Returns information about loaded models and system health.
    """
    try:
        status = {
            "nba": {
                "status": "operational",
                "models_loaded": nba_analyzer is not None,
                "performance": {
                    "win_rate": 66.3,
                    "roi": 26.5,
                    "backtest_alerts": 163,
                    "backtest_games": 3690
                }
            },
            "ncaab": {
                "status": "operational",
                "models_loaded": ncaab_analyzer is not None,
                "performance": {
                    "win_rate": 60.0,
                    "roi": 14.5,
                    "backtest_alerts": 30,
                    "backtest_games": 675
                }
            }
        }

        # Try to load analyzers if not already loaded
        if not nba_analyzer:
            try:
                get_nba_analyzer()
                status["nba"]["models_loaded"] = True
            except Exception as e:
                status["nba"]["status"] = "error"
                status["nba"]["error"] = str(e)

        if not ncaab_analyzer:
            try:
                get_ncaab_analyzer()
                status["ncaab"]["models_loaded"] = True
            except Exception as e:
                status["ncaab"]["status"] = "error"
                status["ncaab"]["error"] = str(e)

        return status

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/alerts-only/nba")
async def get_nba_alerts_only(requests: List[NBAGameRequest]):
    """
    Scan NBA games and return only those with active alerts (2+ SD)

    Useful for filtering down to only high-value opportunities.
    """
    try:
        analyzer = get_nba_analyzer()

        alerts = []
        for request in requests:
            game_data = {
                'game_id': request.game_id,
                'home_team': request.home_team,
                'away_team': request.away_team,
                'home_stats': request.home_stats,
                'away_stats': request.away_stats,
                'live_total': request.live_total
            }

            result = analyzer.analyze_game(game_data)

            # Only include if alert triggered
            if result.get('is_alert', False):
                result['status'] = 'success'
                result['game_id'] = request.game_id
                result['home_team'] = request.home_team
                result['away_team'] = request.away_team
                alerts.append(result)

        return {
            "status": "success",
            "total_games_analyzed": len(requests),
            "alerts_found": len(alerts),
            "alerts": alerts
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NBA alerts scan failed: {str(e)}")


@router.get("/alerts-only/ncaab")
async def get_ncaab_alerts_only(requests: List[NCAABGameRequest]):
    """
    Scan NCAAB games and return only those with active alerts (2+ SD)

    Useful for filtering down to only high-value opportunities.
    """
    try:
        analyzer = get_ncaab_analyzer()

        alerts = []
        for request in requests:
            game_data = {
                'game_id': request.game_id,
                'home_team': request.home_team,
                'away_team': request.away_team,
                'home_stats': request.home_stats,
                'away_stats': request.away_stats,
                'live_total': request.live_total
            }

            result = analyzer.analyze_game(game_data)

            # Only include if alert triggered
            if result.get('is_alert', False):
                result['status'] = 'success'
                result['game_id'] = request.game_id
                result['home_team'] = request.home_team
                result['away_team'] = request.away_team
                alerts.append(result)

        return {
            "status": "success",
            "total_games_analyzed": len(requests),
            "alerts_found": len(alerts),
            "alerts": alerts
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NCAAB alerts scan failed: {str(e)}")
