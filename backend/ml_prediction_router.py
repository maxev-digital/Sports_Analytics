#!/usr/bin/env python3
"""
ML Prediction Router
Routes prediction requests to the appropriate trained ML models for each sport

Replaces the placeholder random variation logic with real ML model predictions
"""
import sys
from pathlib import Path
from typing import Dict, Optional
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

logger = logging.getLogger(__name__)


class MLPredictionRouter:
    """Routes prediction requests to trained ML models"""

    def __init__(self):
        """Initialize ML model router"""
        self.models = {}
        self.supported_sports = ['nhl', 'ncaab', 'nba', 'nfl', 'ncaaf']

    def get_totals_prediction(self, sport: str, game_data: Dict) -> Optional[Dict]:
        """
        Get totals (over/under) prediction for a game using trained ML models

        Args:
            sport: Sport key (nhl, ncaab, nba, nfl, ncaaf)
            game_data: Dictionary with game info and team stats

        Returns:
            Prediction dictionary with ensemble and individual model predictions
        """
        sport = sport.lower()

        if sport not in self.supported_sports:
            logger.warning(f"Sport {sport} not supported for ML predictions")
            return None

        # Import the appropriate model modules
        try:
            if sport == 'nhl':
                return self._predict_nhl_totals(game_data)
            elif sport == 'ncaab':
                return self._predict_ncaab_totals(game_data)
            elif sport == 'nba':
                return self._predict_nba_totals(game_data)
            elif sport == 'nfl':
                return self._predict_nfl_totals(game_data)
            elif sport == 'ncaaf':
                return self._predict_ncaaf_totals(game_data)
        except Exception as e:
            logger.error(f"Error generating {sport.upper()} prediction: {e}")
            return None

    def _predict_nhl_totals(self, game_data: Dict) -> Dict:
        """Generate NHL totals prediction using trained models"""
        from models.nhl.lightgbm_totals import LightGBMTotalsModel
        from models.nhl.xgboost_totals import XGBoostTotalsModel
        from models.nhl.random_forest_totals import RandomForestTotalsModel
        from models.nhl.linear_regression_totals import LinearRegressionTotalsModel

        # Load models
        models = {
            'lightgbm': LightGBMTotalsModel(),
            'xgboost': XGBoostTotalsModel(),
            'random_forest': RandomForestTotalsModel(),
            'linear_regression': LinearRegressionTotalsModel()
        }

        # Get predictions from each model
        predictions = {}
        for model_name, model in models.items():
            try:
                result = model.predict(game_data)
                predictions[model_name] = result['prediction']['total']
            except Exception as e:
                logger.warning(f"NHL {model_name} failed: {e}")
                continue

        if not predictions:
            return None

        # Ensemble is median of all models
        import numpy as np
        ensemble_pred = np.median(list(predictions.values()))
        ensemble_std = np.std(list(predictions.values()))

        return {
            'ensemble': ensemble_pred,
            'individual_predictions': predictions,
            'ensemble_std': ensemble_std
        }

    def _predict_ncaab_totals(self, game_data: Dict) -> Dict:
        """Generate NCAAB totals prediction using trained models"""
        from models.ncaab.lightgbm_totals import LightGBMTotalsModel
        from models.ncaab.xgboost_totals import XGBoostTotalsModel
        from models.ncaab.random_forest_totals import RandomForestTotalsModel
        from models.ncaab.linear_regression_totals import LinearRegressionTotalsModel

        # Load models
        models = {
            'lightgbm': LightGBMTotalsModel(),
            'xgboost': XGBoostTotalsModel(),
            'random_forest': RandomForestTotalsModel(),
            'linear_regression': LinearRegressionTotalsModel()
        }

        # Get predictions from each model
        predictions = {}
        for model_name, model in models.items():
            try:
                result = model.predict(game_data)
                predictions[model_name] = result['prediction']['total']
            except Exception as e:
                logger.warning(f"NCAAB {model_name} failed: {e}")
                continue

        if not predictions:
            return None

        # Ensemble is median of all models
        import numpy as np
        ensemble_pred = np.median(list(predictions.values()))
        ensemble_std = np.std(list(predictions.values()))

        return {
            'ensemble': ensemble_pred,
            'individual_predictions': predictions,
            'ensemble_std': ensemble_std
        }

    def _predict_nba_totals(self, game_data: Dict) -> Dict:
        """Generate NBA totals prediction using trained models"""
        # NBA uses the existing random_forest_totals.py which is already integrated
        from models.random_forest_totals import get_nba_random_forest_model

        try:
            model = get_nba_random_forest_model()
            result = model.predict(game_data)

            return {
                'ensemble': result['prediction']['total'],
                'individual_predictions': {'random_forest': result['prediction']['total']},
                'ensemble_std': 0.0
            }
        except Exception as e:
            logger.error(f"NBA prediction failed: {e}")
            return None

    def _predict_nfl_totals(self, game_data: Dict) -> Dict:
        """Generate NFL totals prediction using placeholder (real models TBD)"""
        # NFL totals models exist but aren't implemented yet
        # For now, return None to fall back to placeholder logic
        logger.info("NFL real ML models not integrated yet, using placeholder")
        return None

    def _predict_ncaaf_totals(self, game_data: Dict) -> Dict:
        """Generate NCAAF totals prediction using placeholder (real models TBD)"""
        # NCAAF totals models exist but aren't implemented yet
        # For now, return None to fall back to placeholder logic
        logger.info("NCAAF real ML models not integrated yet, using placeholder")
        return None


def get_ml_prediction_router():
    """Get singleton instance of ML prediction router"""
    if not hasattr(get_ml_prediction_router, 'instance'):
        get_ml_prediction_router.instance = MLPredictionRouter()
    return get_ml_prediction_router.instance
