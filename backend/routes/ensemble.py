"""Ensemble betting engine routes — multi-strategy game analysis."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ensemble", tags=["ensemble"])

# Lazy import — ensemble model may not always be available
try:
    from models.ensemble.betting_ensemble import BettingEnsemble, GameData
    betting_ensemble = BettingEnsemble()
    _ENSEMBLE_AVAILABLE = True
except Exception as e:
    logger.warning(f"Ensemble model not available: {e}")
    _ENSEMBLE_AVAILABLE = False


class EnsembleAnalysisRequest(BaseModel):
    game_id: str
    home_team: str
    away_team: str
    game_time: str
    market_total: float
    market_total_odds: float = -110
    market_spread: Optional[float] = None
    market_spread_odds: Optional[float] = None
    home_pace: float = 100.0
    away_pace: float = 100.0
    home_off_rating: float = 110.0
    away_off_rating: float = 110.0
    home_def_rating: float = 110.0
    away_def_rating: float = 110.0
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
    bankroll: float = 10000


def _prediction_to_dict(prediction) -> dict:
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
                "confidence": round(prediction.strategy_insights["pace"]["confidence"], 3),
                "scenario": prediction.strategy_insights["pace"]["scenario"],
            },
            "fatigue": {
                "prediction": round(prediction.fatigue_prediction, 1),
                "weight": prediction.fatigue_weight,
                "confidence": round(prediction.strategy_insights["fatigue"]["confidence"], 3),
                "edge_type": prediction.strategy_insights["fatigue"]["edge_type"],
            },
            "regression": {
                "prediction": round(prediction.regression_prediction, 1),
                "weight": prediction.regression_weight,
                "confidence": round(prediction.strategy_insights["regression"]["confidence"], 3),
                "direction": prediction.strategy_insights["regression"]["direction"],
            },
        },
        "key_factors": prediction.key_factors,
    }


@router.post("/analyze")
async def analyze_game(request: EnsembleAnalysisRequest):
    """Run multi-strategy ensemble analysis on a game."""
    if not _ENSEMBLE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Ensemble model not available")
    try:
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
            away_3pt_pct_last_5=request.away_3pt_pct_last_5,
        )
        prediction = betting_ensemble.predict(game_data, bankroll=request.bankroll)
        return _prediction_to_dict(prediction)
    except Exception as e:
        logger.error(f"Error in ensemble analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/sample")
async def get_sample_prediction():
    """Sample ensemble prediction using a Lakers vs Celtics demo game."""
    if not _ENSEMBLE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Ensemble model not available")
    try:
        sample_game = GameData(
            game_id="LAL_BOS_SAMPLE",
            home_team="Lakers",
            away_team="Celtics",
            game_time="2025-01-15 19:00",
            market_total=225.5,
            market_total_odds=-110,
            home_pace=102.0,
            away_pace=98.0,
            home_off_rating=116.0,
            away_off_rating=118.0,
            home_def_rating=112.0,
            away_def_rating=110.0,
            home_rest_days=2,
            away_rest_days=0,
            home_back_to_back=False,
            away_back_to_back=True,
            away_miles_traveled=2800.0,
            away_time_zones=3,
            home_games_last_7=3,
            away_games_last_7=5,
            home_season_ppg=115.0,
            away_season_ppg=117.0,
            home_last_5_ppg=120.0,
            away_last_5_ppg=112.0,
            home_last_5_papg=108.0,
            away_last_5_papg=115.0,
            home_fg_pct_season=0.475,
            away_fg_pct_season=0.470,
            home_fg_pct_last_5=0.490,
            away_fg_pct_last_5=0.430,
        )
        prediction = betting_ensemble.predict(sample_game, bankroll=10000)
        result = _prediction_to_dict(prediction)
        result["note"] = "Sample prediction for demonstration purposes"
        return result
    except Exception as e:
        logger.error(f"Error generating sample prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Sample failed: {str(e)}")
