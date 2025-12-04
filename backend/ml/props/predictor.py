#!/usr/bin/env python3
"""
BULLETPROOF PLAYER PROPS - PREDICTOR
====================================
7-Model Ensemble + Neural Weighter for Player Props

This is the main prediction engine for player props, mirroring
the main model architecture exactly:
- XGBoost, LightGBM, CatBoost, Random Forest, Linear
- PyTorch Tabular Net
- Neural Ensemble Weighter

IMPORTANT: This file is BULLETPROOF. Do not simplify or rename.
"""

import sys
import json
import sqlite3
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Import feature engineering
from ml.props.enhanced_feature_engineering import PropsFeatureEngineer

# Optional imports
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    logger.warning("XGBoost not available")
    XGB_AVAILABLE = False

try:
    import lightgbm as lgb
    LGB_AVAILABLE = True
except ImportError:
    logger.warning("LightGBM not available")
    LGB_AVAILABLE = False

try:
    import catboost as cb
    CATBOOST_AVAILABLE = True
except ImportError:
    logger.warning("CatBoost not available")
    CATBOOST_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available")
    TORCH_AVAILABLE = False


class PropsPredictor:
    """
    BULLETPROOF Props Predictor

    7-Model Ensemble:
    1. XGBoost
    2. LightGBM
    3. CatBoost
    4. Random Forest
    5. Linear/Logistic Regression
    6. PyTorch Tabular Net
    7. Neural Ensemble Weighter

    Matches main model architecture 1:1
    """

    # Model file names (mirror main models exactly)
    MODEL_FILES = {
        'xgb': 'xgb_props.pkl',
        'lgb': 'lgb_props.pkl',
        'catboost': 'catboost_props.cbm',
        'random_forest': 'random_forest_props.pkl',
        'linear': 'linear_props.pkl',
        'pytorch_tabular': 'pytorch_tabular_props.pt',
        'neural_ensemble': 'neural_ensemble_weighter_props.pt'
    }

    def __init__(
        self,
        sport: str = "nba",
        models_dir: str = None,
        props_db_path: str = None,
        predictions_db_path: str = None
    ):
        """
        Initialize the predictor with model paths
        """
        if models_dir is None:
            models_dir = Path(__file__).parent / 'models'
        if props_db_path is None:
            props_db_path = Path(__file__).parent.parent.parent / 'data' / 'player_props.db'
        if predictions_db_path is None:
            predictions_db_path = Path(__file__).parent.parent / 'predictions.db'

        self.sport = sport.lower()
        self.models_dir = Path(models_dir)
        self.props_db_path = str(props_db_path)
        self.predictions_db_path = str(predictions_db_path)

        # Initialize feature engineer
        self.feature_engineer = PropsFeatureEngineer(
            props_db_path=self.props_db_path,
            predictions_db_path=self.predictions_db_path
        )

        # Load models
        self.models = self._load_models()

        # Model weights (trained or default)
        self.model_weights = self._load_model_weights()

        logger.info(f"PropsPredictor initialized")
        logger.info(f"  Models loaded: {list(self.models.keys())}")
        logger.info(f"  Props DB: {self.props_db_path}")
        logger.info(f"  Predictions DB: {self.predictions_db_path}")

    def _load_models(self) -> Dict[str, Any]:
        """Load all available models"""
        models = {}

        # XGBoost
        xgb_path = self.models_dir / self.MODEL_FILES['xgb']
        if xgb_path.exists() and XGB_AVAILABLE:
            try:
                models['xgb'] = joblib.load(xgb_path)
                logger.info(f"  Loaded: XGBoost")
            except Exception as e:
                logger.warning(f"  Failed to load XGBoost: {e}")

        # LightGBM
        lgb_path = self.models_dir / self.MODEL_FILES['lgb']
        if lgb_path.exists() and LGB_AVAILABLE:
            try:
                models['lgb'] = joblib.load(lgb_path)
                logger.info(f"  Loaded: LightGBM")
            except Exception as e:
                logger.warning(f"  Failed to load LightGBM: {e}")

        # CatBoost
        cb_path = self.models_dir / self.MODEL_FILES['catboost']
        if cb_path.exists() and CATBOOST_AVAILABLE:
            try:
                models['catboost'] = cb.CatBoostRegressor()
                models['catboost'].load_model(str(cb_path))
                logger.info(f"  Loaded: CatBoost")
            except Exception as e:
                logger.warning(f"  Failed to load CatBoost: {e}")

        # Random Forest
        rf_path = self.models_dir / self.MODEL_FILES['random_forest']
        if rf_path.exists():
            try:
                models['random_forest'] = joblib.load(rf_path)
                logger.info(f"  Loaded: Random Forest")
            except Exception as e:
                logger.warning(f"  Failed to load Random Forest: {e}")

        # Linear Regression
        linear_path = self.models_dir / self.MODEL_FILES['linear']
        if linear_path.exists():
            try:
                models['linear'] = joblib.load(linear_path)
                logger.info(f"  Loaded: Linear")
            except Exception as e:
                logger.warning(f"  Failed to load Linear: {e}")

        # PyTorch Tabular (if available)
        pt_path = self.models_dir / self.MODEL_FILES['pytorch_tabular']
        if pt_path.exists() and TORCH_AVAILABLE:
            try:
                # Load PyTorch model
                from ml.pytorch_models.tabular_net import TabularNet
                models['pytorch_tabular'] = torch.load(pt_path)
                models['pytorch_tabular'].eval()
                logger.info(f"  Loaded: PyTorch Tabular")
            except Exception as e:
                logger.warning(f"  Failed to load PyTorch Tabular: {e}")

        # If no models loaded, use fallback
        if not models:
            logger.warning("No trained models found. Using baseline predictor.")

        return models

    def _load_model_weights(self) -> Dict[str, float]:
        """Load model weights for ensemble"""
        weights_path = self.models_dir / 'ensemble_weights.json'

        if weights_path.exists():
            try:
                with open(weights_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load ensemble weights: {e}")

        # Default equal weights
        return {
            'xgb': 0.20,
            'lgb': 0.20,
            'catboost': 0.15,
            'random_forest': 0.15,
            'linear': 0.10,
            'pytorch_tabular': 0.20
        }

    # ==========================================================================
    # PREDICTION METHODS
    # ==========================================================================

    def predict_single_prop(
        self,
        player_name: str,
        team: str,
        opponent: str,
        prop_type: str,
        market_line: float,
        game_date: date,
        home_away: str = "HOME",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate prediction for a single prop

        Returns:
            Dict with prediction details:
            - predicted_value: Model's predicted stat value
            - model_fair_line: Fair line based on model
            - edge: Difference from market line
            - over_probability: Probability of going over
            - under_probability: Probability of going under
            - confidence: Confidence level (0-100)
            - recommendation: OVER, UNDER, or NO_PLAY
            - kelly_fraction: Kelly criterion bet size
            - model_predictions: Individual model predictions
        """
        # Extract features
        features = self.feature_engineer.extract_features_for_prop(
            player_name=player_name,
            team=team,
            opponent=opponent,
            prop_type=prop_type,
            market_line=market_line,
            game_date=game_date,
            home_away=home_away,
            **kwargs
        )

        # Convert to DataFrame for model input
        feature_names = self.feature_engineer.get_all_feature_names()
        X = pd.DataFrame([{k: features.get(k, 0.0) for k in feature_names}])

        # Get predictions from all models
        model_predictions = {}

        for name, model in self.models.items():
            try:
                if name == 'pytorch_tabular' and TORCH_AVAILABLE:
                    # PyTorch model
                    with torch.no_grad():
                        tensor = torch.FloatTensor(X.values)
                        pred = model(tensor).item()
                else:
                    # Sklearn-style model
                    pred = model.predict(X)[0]

                model_predictions[name] = float(pred)
            except Exception as e:
                logger.warning(f"Model {name} prediction failed: {e}")

        # If no models available, use baseline
        if not model_predictions:
            baseline = self._baseline_prediction(features, prop_type, market_line)
            model_predictions['baseline'] = baseline

        # Calculate ensemble prediction
        predicted_value = self._ensemble_prediction(model_predictions)

        # Calculate edge and probabilities
        edge = predicted_value - market_line

        # Calculate over probability based on consistency and edge
        consistency = features.get('consistency_score', 0.5)
        std_dev = features.get('last_10_std', 3.0)

        if std_dev > 0:
            z_score = edge / std_dev
            # Convert to probability (sigmoid-like)
            over_prob = 1 / (1 + np.exp(-z_score * 1.5))
        else:
            over_prob = 0.5 + (edge / (abs(edge) + 1)) * 0.3

        over_prob = max(0.1, min(0.9, over_prob))
        under_prob = 1 - over_prob

        # Calculate confidence (0-100)
        confidence = self._calculate_confidence(
            edge=edge,
            std_dev=std_dev,
            consistency=consistency,
            recent_form=features.get('trend_l3_vs_l10', 0),
            hit_rate=features.get('hit_rate_at_current_line', 0.5)
        )

        # Determine recommendation
        if abs(edge) < 1.0 or confidence < 55:
            recommendation = "NO_PLAY"
        elif edge > 0:
            recommendation = "OVER"
        else:
            recommendation = "UNDER"

        # Calculate Kelly fraction
        if recommendation != "NO_PLAY":
            prob = over_prob if recommendation == "OVER" else under_prob
            kelly = self._kelly_criterion(prob, odds=-110)
        else:
            kelly = 0.0

        return {
            'player_name': player_name,
            'team': team,
            'opponent': opponent,
            'prop_type': prop_type,
            'market_line': market_line,
            'predicted_value': round(predicted_value, 2),
            'model_fair_line': round(predicted_value, 1),
            'edge': round(edge, 2),
            'over_probability': round(over_prob * 100, 1),
            'under_probability': round(under_prob * 100, 1),
            'confidence': round(confidence, 1),
            'recommendation': recommendation,
            'kelly_fraction': round(kelly, 4),
            'model_predictions': model_predictions,
            'game_date': str(game_date),
            'home_away': home_away,
            'generated_at': datetime.now().isoformat()
        }

    def _ensemble_prediction(self, model_predictions: Dict[str, float]) -> float:
        """Calculate weighted ensemble prediction"""
        if not model_predictions:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for name, pred in model_predictions.items():
            weight = self.model_weights.get(name, 0.1)
            weighted_sum += pred * weight
            total_weight += weight

        if total_weight > 0:
            return weighted_sum / total_weight

        # Equal weights fallback
        return np.mean(list(model_predictions.values()))

    def _baseline_prediction(
        self,
        features: Dict[str, float],
        prop_type: str,
        market_line: float
    ) -> float:
        """
        Baseline prediction when no trained models available
        Uses feature-based heuristics
        """
        # Use recent averages with weights
        season_avg = features.get('season_avg', market_line)
        last_5_avg = features.get('last_5_avg', season_avg)
        last_10_avg = features.get('last_10_avg', season_avg)

        # Weight recent games more heavily
        baseline = (
            season_avg * 0.2 +
            last_10_avg * 0.3 +
            last_5_avg * 0.5
        )

        # Adjust for trend
        trend = features.get('trend_l3_vs_l10', 0)
        baseline += trend * 0.3

        # Adjust for matchup difficulty
        matchup = features.get('matchup_difficulty', 0.5)
        baseline *= (1 - (matchup - 0.5) * 0.1)

        # Adjust for rest
        rest = features.get('rest_days', 1)
        if rest == 0:  # Back-to-back
            baseline *= 0.95

        return max(0, baseline)

    def _calculate_confidence(
        self,
        edge: float,
        std_dev: float,
        consistency: float,
        recent_form: float,
        hit_rate: float
    ) -> float:
        """Calculate prediction confidence (0-100)"""
        # Base confidence from edge size
        edge_confidence = min(30, abs(edge) * 5)

        # Consistency bonus (0-25)
        consistency_bonus = consistency * 25

        # Historical hit rate bonus (0-25)
        hit_rate_bonus = (hit_rate - 0.4) * 50 if hit_rate > 0.4 else 0

        # Recent form bonus (0-20)
        form_bonus = min(20, max(-10, recent_form * 3))

        total = 50 + edge_confidence + consistency_bonus + hit_rate_bonus + form_bonus

        return max(30, min(95, total))

    def _kelly_criterion(self, prob: float, odds: int = -110) -> float:
        """Calculate Kelly criterion bet sizing"""
        # Convert American odds to decimal
        if odds < 0:
            decimal_odds = 1 + (100 / abs(odds))
        else:
            decimal_odds = 1 + (odds / 100)

        # Kelly formula: (bp - q) / b
        b = decimal_odds - 1
        p = prob
        q = 1 - p

        kelly = (b * p - q) / b if b > 0 else 0

        # Fractional Kelly (25% for safety)
        return max(0, min(0.25, kelly * 0.25))

    # ==========================================================================
    # BATCH PREDICTION
    # ==========================================================================

    def generate_all_props_edges(
        self,
        props_date: date = None,
        min_confidence: int = 55,
        save_to_db: bool = True
    ) -> List[Dict]:
        """
        Generate predictions for all props on a given date

        This is the main entry point for the daily autonomous pipeline.
        Called by cron at 10:30 AM.

        Args:
            props_date: Date to generate predictions for (default: today)
            min_confidence: Minimum confidence to include in edges
            save_to_db: Whether to save predictions to unified database

        Returns:
            List of prediction dicts for props meeting threshold
        """
        if props_date is None:
            props_date = date.today()

        logger.info(f"{'='*70}")
        logger.info(f"BULLETPROOF PROPS - GENERATING ALL EDGES")
        logger.info(f"{'='*70}")
        logger.info(f"Date: {props_date}")
        logger.info(f"Min Confidence: {min_confidence}")

        # Get all props from database
        props = self._get_props_for_date(props_date)

        if not props:
            logger.warning(f"No props found for {props_date}")
            return []

        logger.info(f"Found {len(props)} props to analyze")

        # Generate predictions
        all_predictions = []
        edges = []

        for i, prop in enumerate(props, 1):
            if i % 50 == 0:
                logger.info(f"Progress: {i}/{len(props)} ({i/len(props)*100:.1f}%)")

            try:
                prediction = self.predict_single_prop(
                    player_name=prop['player_name'],
                    team=prop['team'],
                    opponent=prop['opponent'],
                    prop_type=prop['prop_type'],
                    market_line=prop['market_line'],
                    game_date=props_date,
                    home_away=prop.get('home_away', 'HOME')
                )

                # Add prop metadata
                prediction['prop_id'] = prop.get('id')
                prediction['game_id'] = prop.get('game_id')
                prediction['sportsbook'] = prop.get('sportsbook', 'fanduel')

                all_predictions.append(prediction)

                # Track edges
                if prediction['confidence'] >= min_confidence and prediction['recommendation'] != "NO_PLAY":
                    edges.append(prediction)

            except Exception as e:
                logger.error(f"Error predicting {prop['player_name']} {prop['prop_type']}: {e}")

        logger.info(f"Predictions generated: {len(all_predictions)}")
        logger.info(f"Edges found (>={min_confidence}% confidence): {len(edges)}")

        # Save to database
        if save_to_db and all_predictions:
            self._save_predictions_to_db(all_predictions, props_date)

        # Sort edges by confidence
        edges.sort(key=lambda x: x['confidence'], reverse=True)

        logger.info(f"{'='*70}")
        logger.info(f"EDGE GENERATION COMPLETE")
        logger.info(f"{'='*70}")

        return edges

    def _get_props_for_date(self, props_date: date) -> List[Dict]:
        """Get all props from database for a given date"""
        props = []

        try:
            conn = sqlite3.connect(self.props_db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, player_name, team, opponent, home_away,
                       prop_type, market_line, bookmaker, game_id
                FROM player_props_lines
                WHERE date = ?
            """, (str(props_date),))

            for row in cursor.fetchall():
                props.append({
                    'id': row[0],
                    'player_name': row[1],
                    'team': row[2],
                    'opponent': row[3],
                    'home_away': row[4],
                    'prop_type': row[5],
                    'market_line': row[6],
                    'sportsbook': row[7],
                    'game_id': row[8]
                })

            conn.close()
        except Exception as e:
            logger.error(f"Error fetching props: {e}")

        return props

    def _save_predictions_to_db(self, predictions: List[Dict], props_date: date):
        """
        Save predictions to unified predictions.db

        Uses the same table structure as main predictions
        """
        try:
            conn = sqlite3.connect(self.predictions_db_path)
            cursor = conn.cursor()

            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS player_prop_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_date TEXT NOT NULL,
                    player_name TEXT NOT NULL,
                    team TEXT,
                    opponent TEXT,
                    prop_type TEXT NOT NULL,
                    market_line REAL NOT NULL,
                    predicted_value REAL NOT NULL,
                    edge REAL NOT NULL,
                    over_probability REAL,
                    under_probability REAL,
                    confidence REAL,
                    recommendation TEXT,
                    kelly_fraction REAL,
                    sportsbook TEXT,
                    game_id TEXT,
                    model_predictions TEXT,
                    generated_at TEXT,
                    result TEXT,
                    actual_value REAL,
                    graded_at TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert predictions
            for pred in predictions:
                cursor.execute("""
                    INSERT INTO player_prop_predictions (
                        prediction_date, player_name, team, opponent,
                        prop_type, market_line, predicted_value, edge,
                        over_probability, under_probability, confidence,
                        recommendation, kelly_fraction, sportsbook, game_id,
                        model_predictions, generated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(props_date),
                    pred['player_name'],
                    pred['team'],
                    pred['opponent'],
                    pred['prop_type'],
                    pred['market_line'],
                    pred['predicted_value'],
                    pred['edge'],
                    pred['over_probability'],
                    pred['under_probability'],
                    pred['confidence'],
                    pred['recommendation'],
                    pred['kelly_fraction'],
                    pred.get('sportsbook', 'fanduel'),
                    pred.get('game_id'),
                    json.dumps(pred.get('model_predictions', {})),
                    pred['generated_at']
                ))

            conn.commit()
            conn.close()

            logger.info(f"Saved {len(predictions)} predictions to unified database")

        except Exception as e:
            logger.error(f"Error saving predictions: {e}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def generate_all_props_edges(props_date: date = None) -> List[Dict]:
    """
    Main entry point for cron job

    Called by autonomous_learning_system.py at 10:30 AM
    """
    predictor = PropsPredictor()
    return predictor.generate_all_props_edges(props_date=props_date)


# =============================================================================
# TESTING
# =============================================================================

def test_predictor():
    """Test the predictor"""
    from datetime import date

    print("\n" + "="*70)
    print("BULLETPROOF PROPS - PREDICTOR TEST")
    print("="*70)

    predictor = PropsPredictor(
        props_db_path='/root/sporttrader/backend/data/player_props.db',
        predictions_db_path='/root/sporttrader/backend/ml/predictions.db'
    )

    # Test single prediction
    print("\nTesting single prop prediction...")

    result = predictor.predict_single_prop(
        player_name="LeBron James",
        team="LAL",
        opponent="BOS",
        prop_type="points",
        market_line=25.5,
        game_date=date.today(),
        home_away="HOME"
    )

    print(f"\nPrediction Result:")
    print(f"  Player: {result['player_name']}")
    print(f"  Prop: {result['prop_type']} O/U {result['market_line']}")
    print(f"  Predicted: {result['predicted_value']}")
    print(f"  Edge: {result['edge']}")
    print(f"  Confidence: {result['confidence']}%")
    print(f"  Recommendation: {result['recommendation']}")
    print(f"  Kelly: {result['kelly_fraction']}")

    print("\n" + "="*70)


if __name__ == "__main__":
    test_predictor()


def generate_single_prop_prediction(player_name: str, stat_type: str, market_line: float, sport: str = 'nba') -> dict:
    """
    Generate prediction for a single player prop (used by DFS scanner)
    
    Args:
        player_name: Player name
        stat_type: Stat type (e.g., 'points', 'assists')
        market_line: DFS platform line
        sport: Sport code (nba, nhl, nfl)
    
    Returns:
        dict with prediction, confidence, edge, probabilities
    """
    try:
        predictor = PropsPredictor(sport=sport)
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Try to find existing prediction for today
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT predicted_value, edge_pct, confidence_level, recommendation
            FROM player_props_predictions
            WHERE prediction_date = ? 
              AND player_name = ? 
              AND prop_type = ?
              AND ABS(market_line - ?) < 1.0
            ORDER BY timestamp DESC
            LIMIT 1
        """, (today, player_name, stat_type, market_line))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            predicted_value, edge_pct, confidence_level, recommendation = result
            
            # Calculate probabilities from prediction
            over_prob = 0.5 + (edge_pct / 200.0) if recommendation == 'OVER' else 0.5 - (edge_pct / 200.0)
            under_prob = 1.0 - over_prob
            
            return {
                'player_name': player_name,
                'stat_type': stat_type,
                'market_line': market_line,
                'predicted_value': predicted_value,
                'edge': edge_pct,
                'confidence': confidence_level,
                'recommendation': recommendation,
                'over_probability': max(0.0, min(1.0, over_prob)),
                'under_probability': max(0.0, min(1.0, under_prob))
            }
        else:
            # No prediction found
            return None
            
    except Exception as e:
        logger.error(f"Error generating single prop prediction: {e}")
        return None
