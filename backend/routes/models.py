"""
ML Models API Routes
FastAPI endpoints for various prediction models (Random Forest, XGBoost, LightGBM, Linear Regression)
and ensemble comparison
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import sys
from pathlib import Path
import asyncio

# Add models directories to path
models_path = Path(__file__).parent.parent / "models"
ncaab_models_path = models_path / "ncaab"
sys.path.append(str(models_path))
sys.path.append(str(ncaab_models_path))

# NBA models
from random_forest_totals import get_random_forest_model as get_nba_random_forest
from nba.xgboost_totals import get_nba_xgboost_totals_model
from nba.lightgbm_totals import get_nba_lightgbm_totals_model
from nba.linear_regression_totals import get_nba_linear_regression_totals_model
from nba.random_forest_spreads import get_nba_random_forest_spreads_model
from nba.linear_regression_spreads import get_nba_linear_regression_spreads_model
from nba.xgboost_spreads import get_nba_xgboost_spreads_model
from nba.random_forest_moneyline import get_nba_random_forest_moneyline_model
from nba.logistic_regression_moneyline import get_nba_logistic_regression_moneyline_model

# NCAAB models
from ncaab.random_forest_totals import get_ncaab_random_forest_model
from ncaab.xgboost_totals import get_ncaab_xgboost_model
from ncaab.lightgbm_totals import get_ncaab_lightgbm_model
from ncaab.linear_regression_totals import get_ncaab_linear_regression_model

# NHL models
from nhl.random_forest_totals import get_nhl_random_forest_totals_model
from nhl.xgboost_totals import get_nhl_xgboost_totals_model
from nhl.lightgbm_totals import get_nhl_lightgbm_totals_model
from nhl.linear_regression_totals import get_nhl_linear_regression_totals_model

router = APIRouter(prefix="/api/models", tags=["models"])

# ========== REQUEST/RESPONSE MODELS ==========

class TeamStats(BaseModel):
    """Team statistics for prediction"""
    pace: float = Field(..., description="Possessions per 48 minutes")
    off_rating: float = Field(..., description="Offensive rating (points per 100 possessions)")
    def_rating: float = Field(..., description="Defensive rating (points allowed per 100 possessions)")
    rest_days: Optional[int] = Field(1, description="Days of rest before game")

    class Config:
        schema_extra = {
            "example": {
                "pace": 100.5,
                "off_rating": 118.2,
                "def_rating": 110.5,
                "rest_days": 2
            }
        }


class PredictionRequest(BaseModel):
    """Request model for model prediction"""
    game_id: str = Field(..., description="Unique game identifier")
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    home_stats: TeamStats = Field(..., description="Home team statistics")
    away_stats: TeamStats = Field(..., description="Away team statistics")
    market_total: Optional[float] = Field(None, description="Current betting market total")
    sport: str = Field("nba", description="Sport type: nba or ncaab")

    class Config:
        schema_extra = {
            "example": {
                "game_id": "nba_20251108_LAL_BOS",
                "home_team": "Lakers",
                "away_team": "Celtics",
                "home_stats": {
                    "pace": 100.5,
                    "off_rating": 118.2,
                    "def_rating": 110.5,
                    "rest_days": 2
                },
                "away_stats": {
                    "pace": 98.3,
                    "off_rating": 115.8,
                    "def_rating": 108.9,
                    "rest_days": 1
                },
                "market_total": 228.5
            }
        }


class PredictionResponse(BaseModel):
    """Response model for model prediction"""
    model_id: str
    model_name: str
    prediction: Dict[str, float]
    market_analysis: Optional[Dict[str, Any]] = None
    model_performance: Dict[str, float]
    feature_importance: Optional[Dict[str, float]] = None
    timestamp: str
    status: str

    class Config:
        schema_extra = {
            "example": {
                "model_id": "random_forest",
                "model_name": "Random Forest",
                "prediction": {
                    "total": 226.8,
                    "confidence": 0.75,
                    "std_dev": 3.2
                },
                "market_analysis": {
                    "market_line": 228.5,
                    "edge": -1.7,
                    "recommendation": "UNDER",
                    "probability_over": 0.430,
                    "probability_under": 0.570,
                    "kelly_fraction": 0.028
                },
                "model_performance": {
                    "mae": 7.8,
                    "rmse": 10.1,
                    "accuracy": 0.652,
                    "games_trained": 1203
                },
                "feature_importance": {
                    "home_pace": 0.25,
                    "away_pace": 0.23,
                    "home_off_rating": 0.18,
                    "away_off_rating": 0.17,
                    "rest_days": 0.10,
                    "home_court": 0.07
                },
                "timestamp": "2025-11-08T16:30:00Z",
                "status": "success"
            }
        }


class ComparisonRequest(BaseModel):
    """Request model for model comparison"""
    game_id: str
    home_team: str
    away_team: str
    home_stats: TeamStats
    away_stats: TeamStats
    market_total: float
    sport: str = "nba"

    class Config:
        schema_extra = {
            "example": {
                "game_id": "nba_20251108_LAL_BOS",
                "home_team": "Lakers",
                "away_team": "Celtics",
                "home_stats": {
                    "pace": 100.5,
                    "off_rating": 118.2,
                    "def_rating": 110.5,
                    "rest_days": 2
                },
                "away_stats": {
                    "pace": 98.3,
                    "off_rating": 115.8,
                    "def_rating": 108.9,
                    "rest_days": 1
                },
                "market_total": 228.5
            }
        }


# ========== ENDPOINTS ==========

@router.post("/random-forest/predict", response_model=PredictionResponse)
async def predict_random_forest(request: PredictionRequest):
    """
    Random Forest prediction for game totals (NBA or NCAAB)

    **Best for NBA totals** according to sports-betting-models-guide.md
    - Handles non-linear pace × efficiency interactions
    - Less prone to overfitting than XGBoost
    - Provides feature importance rankings
    """
    try:
        # Route to correct model based on sport
        if request.sport.lower() == "ncaab":
            model = get_ncaab_random_forest_model()
        elif request.sport.lower() == "nhl":
            model = get_nhl_random_forest_totals_model()
        else:
            model = get_nba_random_forest()

        game_data = {
            'home_team': request.home_team,
            'away_team': request.away_team,
            'home_stats': {
                'pace': request.home_stats.pace,
                'off_rating': request.home_stats.off_rating,
                'def_rating': request.home_stats.def_rating,
                'rest_days': request.home_stats.rest_days
            },
            'away_stats': {
                'pace': request.away_stats.pace,
                'off_rating': request.away_stats.off_rating,
                'def_rating': request.away_stats.def_rating,
                'rest_days': request.away_stats.rest_days
            }
        }

        result = model.predict(game_data, request.market_total)

        return PredictionResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/xgboost/predict")
async def predict_xgboost(request: PredictionRequest):
    """
    XGBoost prediction for game totals (NBA or NCAAB)

    **Strong baseline model** - Good all-around performance
    - Handles complex feature interactions
    - Built-in regularization
    - Fast predictions
    """
    try:
        # Route to correct model based on sport
        if request.sport.lower() == "ncaab":
            model = get_ncaab_xgboost_model()
        elif request.sport.lower() == "nhl":
            model = get_nhl_xgboost_totals_model()
        else:
            # Use NBA XGBoost totals model
            model = get_nba_xgboost_totals_model()

        game_data = {
            'home_team': request.home_team,
            'away_team': request.away_team,
            'home_stats': {
                'pace': request.home_stats.pace,
                'off_rating': request.home_stats.off_rating,
                'def_rating': request.home_stats.def_rating,
                'rest_days': request.home_stats.rest_days
            },
            'away_stats': {
                'pace': request.away_stats.pace,
                'off_rating': request.away_stats.off_rating,
                'def_rating': request.away_stats.def_rating,
                'rest_days': request.away_stats.rest_days
            }
        }

        result = model.predict(game_data, request.market_total)

        return PredictionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/lightgbm/predict")
async def predict_lightgbm(request: PredictionRequest):
    """
    LightGBM prediction for game totals (NBA or NCAAB)

    **Fastest gradient boosting model**
    - Faster training and prediction than XGBoost
    - Often better accuracy
    - Memory efficient
    """
    try:
        # Route to correct model based on sport
        if request.sport.lower() == "ncaab":
            model = get_ncaab_lightgbm_model()
        elif request.sport.lower() == "nhl":
            model = get_nhl_lightgbm_totals_model()
        else:
            # Use NBA LightGBM totals model
            model = get_nba_lightgbm_totals_model()

        game_data = {
            'home_team': request.home_team,
            'away_team': request.away_team,
            'home_stats': {
                'pace': request.home_stats.pace,
                'off_rating': request.home_stats.off_rating,
                'def_rating': request.home_stats.def_rating,
                'rest_days': request.home_stats.rest_days
            },
            'away_stats': {
                'pace': request.away_stats.pace,
                'off_rating': request.away_stats.off_rating,
                'def_rating': request.away_stats.def_rating,
                'rest_days': request.away_stats.rest_days
            }
        }

        result = model.predict(game_data, request.market_total)

        return PredictionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/linear-regression/predict")
async def predict_linear_regression(request: PredictionRequest):
    """
    Linear Regression prediction for game totals (NBA or NCAAB)

    **Simple baseline model**
    - Fast and interpretable
    - Good for linear relationships
    - Recommended for NFL (linear sport)
    """
    try:
        # Route to correct model based on sport
        if request.sport.lower() == "ncaab":
            model = get_ncaab_linear_regression_model()
        elif request.sport.lower() == "nhl":
            model = get_nhl_linear_regression_totals_model()
        else:
            # Use NBA Linear Regression totals model
            model = get_nba_linear_regression_totals_model()

        game_data = {
            'home_team': request.home_team,
            'away_team': request.away_team,
            'home_stats': {
                'pace': request.home_stats.pace,
                'off_rating': request.home_stats.off_rating,
                'def_rating': request.home_stats.def_rating,
                'rest_days': request.home_stats.rest_days
            },
            'away_stats': {
                'pace': request.away_stats.pace,
                'off_rating': request.away_stats.off_rating,
                'def_rating': request.away_stats.def_rating,
                'rest_days': request.away_stats.rest_days
            }
        }

        result = model.predict(game_data, request.market_total)

        return PredictionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/compare-all")
async def compare_all_models(request: ComparisonRequest):
    """
    Run all models and return ensemble consensus

    This is the primary endpoint for Edge Lab
    - Runs all 4 models in parallel
    - Calculates weighted ensemble average
    - Provides consensus recommendation
    - Shows agreement/disagreement between models
    """
    try:
        # Convert to PredictionRequest format
        pred_request = PredictionRequest(
            game_id=request.game_id,
            home_team=request.home_team,
            away_team=request.away_team,
            home_stats=request.home_stats,
            away_stats=request.away_stats,
            market_total=request.market_total,
            sport=request.sport
        )

        # Run all models in parallel
        results = await asyncio.gather(
            predict_random_forest(pred_request),
            predict_xgboost(pred_request),
            predict_lightgbm(pred_request),
            predict_linear_regression(pred_request),
            return_exceptions=True
        )

        # Collect successful predictions
        models_data = {}
        model_names = ['random_forest', 'xgboost', 'lightgbm', 'linear_regression']

        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                models_data[model_names[idx]] = {
                    'status': 'error',
                    'error': str(result)
                }
            else:
                # Convert Pydantic model to dict if necessary
                result_dict = result.dict() if hasattr(result, 'dict') else result
                # Store the full model result, not just a subset of fields
                models_data[model_names[idx]] = result_dict

        # Calculate ensemble
        predictions = [
            d['prediction']['total'] for d in models_data.values()
            if d.get('status') == 'success' and 'prediction' in d
        ]
        confidences = [
            d['prediction']['confidence'] for d in models_data.values()
            if d.get('status') == 'success' and 'prediction' in d
        ]

        if predictions and confidences:
            import numpy as np
            weighted_avg = np.average(predictions, weights=confidences)
            ensemble_confidence = np.mean(confidences) * 1.1  # Ensemble bonus
            ensemble_confidence = min(ensemble_confidence, 0.95)  # Cap at 95%

            # Determine consensus
            recommendations = [
                d.get('market_analysis', {}).get('recommendation') for d in models_data.values()
                if d.get('status') == 'success' and d.get('market_analysis', {}).get('recommendation')
            ]
            agreement_count = max(recommendations.count('OVER'), recommendations.count('UNDER'))
            disagreement_count = len(recommendations) - agreement_count

            if agreement_count >= 3:
                consensus_strength = 'STRONG'
                ensemble_recommendation = max(set(recommendations), key=recommendations.count)
            elif agreement_count == 2:
                consensus_strength = 'MODERATE'
                ensemble_recommendation = max(set(recommendations), key=recommendations.count)
            else:
                consensus_strength = 'WEAK'
                ensemble_recommendation = None

            ensemble_edge = weighted_avg - request.market_total

            # Kelly fraction for ensemble
            if ensemble_recommendation and abs(ensemble_edge) > 2.0:
                kelly_fraction = min(abs(ensemble_edge) / 100, 0.05)
            else:
                kelly_fraction = 0.0

        else:
            weighted_avg = None
            ensemble_confidence = 0.0
            consensus_strength = 'NONE'
            ensemble_recommendation = None
            agreement_count = 0
            disagreement_count = 0
            ensemble_edge = 0.0
            kelly_fraction = 0.0

        # Determine best model
        best_model_id = None
        best_model_reason = None
        if models_data:
            # Find model with highest confidence and significant edge
            best_candidates = [
                (k, v) for k, v in models_data.items()
                if v.get('status') == 'success' and abs(v.get('market_analysis', {}).get('edge', 0)) > 2.0
            ]
            if best_candidates:
                best_model_id = max(best_candidates, key=lambda x: x[1]['prediction']['confidence'])[0]
                best_model_reason = "Highest confidence with strong edge"

        return {
            "game_id": request.game_id,
            "market_line": round(request.market_total, 1),
            "models": models_data,
            "ensemble": {
                "weighted_average": round(weighted_avg, 1) if weighted_avg else None,
                "confidence": round(ensemble_confidence, 2),
                "recommendation": ensemble_recommendation,
                "consensus_strength": consensus_strength,
                "agreement_count": agreement_count,
                "disagreement_count": disagreement_count,
                "edge": round(ensemble_edge, 1),
                "kelly_fraction": round(kelly_fraction, 3)
            },
            "best_model": {
                "id": best_model_id,
                "reason": best_model_reason
            } if best_model_id else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ML Models API",
        "available_models": [
            "random_forest",
            "xgboost",
            "lightgbm",
            "linear_regression"
        ],
        "version": "1.0.0"
    }

# Force reload
