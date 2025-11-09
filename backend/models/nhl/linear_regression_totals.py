"""
Linear Regression Model for NHL Totals Prediction
Predicts total goals scored in NHL games

Per sports-betting-models-guide.md:
- Simple, interpretable, fast
- Good baseline model
- Works well when relationships are relatively linear
- Excellent for real-time live betting due to speed
"""

import numpy as np
import joblib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class LinearRegressionTotalsModel:
    """Linear Regression model for predicting NHL game totals"""

    def __init__(self):
        """Initialize Linear Regression totals model by loading trained model"""
        model_dir = Path(__file__).parent.parent.parent / "ml" / "models"

        self.model = joblib.load(model_dir / "nhl_linear_regression_totals_latest.joblib")
        metadata = joblib.load(model_dir / "nhl_totals_metadata_latest.joblib")

        self.feature_names = metadata['feature_names']
        self.coefficients = self.model.coef_
        self.intercept = self.model.intercept_

        stats = metadata['training_stats']['linear_regression']

        self.model_performance = {
            'mae': stats['mae'],
            'rmse': stats['rmse'],
            'r2': stats['r2'],
            'over_under_accuracy': stats.get('over_under_accuracy', 0.0),
            'within_half_goal': stats.get('within_half_goal', 0.0),
            'within_one_goal': stats.get('within_one_goal', 0.0),
            'games_trained': stats['n_samples']
        }

    def _extract_features(self, game_data: Dict) -> np.ndarray:
        """Extract features matching training data format"""
        home = game_data.get('home_stats', {})
        away = game_data.get('away_stats', {})

        features = np.zeros((1, len(self.feature_names)))

        # Core offensive stats
        features[0, 0] = home.get('goals_per_game', 3.0)
        features[0, 1] = away.get('goals_per_game', 3.0)
        features[0, 2] = home.get('shooting_pct', 10.0)
        features[0, 3] = away.get('shooting_pct', 10.0)

        # Core defensive stats
        features[0, 4] = home.get('goals_against_per_game', 3.0)
        features[0, 5] = away.get('goals_against_per_game', 3.0)
        features[0, 6] = home.get('save_pct', 0.910)
        features[0, 7] = away.get('save_pct', 0.910)

        # Goalie stats (critical)
        home_goalie = game_data.get('home_goalie', {})
        away_goalie = game_data.get('away_goalie', {})
        features[0, 8] = home_goalie.get('save_pct', 0.910)
        features[0, 9] = away_goalie.get('save_pct', 0.910)
        features[0, 10] = home_goalie.get('gaa', 2.8)
        features[0, 11] = away_goalie.get('gaa', 2.8)

        return features

    def predict(self, game_data: Dict, market_total: Optional[float] = None) -> Dict:
        """Generate prediction with confidence and market analysis"""
        features = self._extract_features(game_data)

        # Get prediction from Linear Regression
        prediction = self.model.predict(features)[0]

        # Linear regression has consistent variance
        std_dev = 0.58  # NHL totals variance
        confidence = 0.68  # Linear regression typically lower confidence than ensemble methods

        result = {
            'model_id': 'linear_regression',
            'model_name': 'Linear Regression',
            'sport': 'NHL',
            'prediction': {
                'total': round(prediction, 1),
                'confidence': round(confidence, 2),
                'std_dev': round(std_dev, 2)
            },
            'model_performance': self.model_performance,
            'feature_importance': self._get_feature_importance(),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'success'
        }

        if market_total is not None:
            edge = prediction - market_total
            probability_over = self._calculate_probability_over(prediction, std_dev, market_total)
            probability_under = 1 - probability_over

            if abs(edge) < 0.35:  # Linear regression needs slightly larger edge
                recommendation = 'PASS'
            elif edge > 0:
                recommendation = 'OVER'
            else:
                recommendation = 'UNDER'

            if recommendation == 'OVER':
                win_prob = probability_over
            elif recommendation == 'UNDER':
                win_prob = probability_under
            else:
                win_prob = 0.5

            if win_prob > 0.5 and recommendation != 'PASS':
                kelly_fraction = ((win_prob * 1.909) - 1) / 0.909
                kelly_fraction = min(kelly_fraction / 4, 0.03)
            else:
                kelly_fraction = 0.0

            result['market_analysis'] = {
                'market_line': market_total,
                'edge': round(edge, 2),
                'recommendation': recommendation,
                'probability_over': round(probability_over, 3),
                'probability_under': round(probability_under, 3),
                'kelly_fraction': round(kelly_fraction, 3)
            }

        return result

    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from coefficients (interpretability advantage)"""
        importance = {}
        for i, feature_name in enumerate(self.feature_names):
            importance[feature_name] = round(float(self.coefficients[i]), 4)
        return importance

    def _calculate_probability_over(self, predicted_total: float, std_dev: float,
                                   market_total: float) -> float:
        """Calculate probability that game total will go over the line"""
        from scipy import stats
        z_score = (market_total - predicted_total) / std_dev
        probability_under = stats.norm.cdf(z_score)
        return 1 - probability_under


# Singleton instance
_model_instance = None

def get_nhl_linear_regression_totals_model():
    """Get or create singleton Linear Regression totals model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = LinearRegressionTotalsModel()
    return _model_instance
