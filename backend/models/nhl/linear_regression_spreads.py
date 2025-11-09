"""
Linear Regression Model for NHL Spreads (Puck Line) Prediction
Predicts home_margin (home_goals - away_goals)

Per sports-betting-models-guide.md:
- Simple, interpretable, fast
- Good for power ratings approach
- Excellent for real-time updates
"""

import numpy as np
import joblib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class LinearRegressionSpreadsModel:
    """Linear Regression model for predicting NHL spreads (puck line)"""

    def __init__(self):
        """Initialize Linear Regression spreads model by loading trained model"""
        model_dir = Path(__file__).parent.parent.parent / "ml" / "models"

        self.model = joblib.load(model_dir / "nhl_linear_regression_spreads_latest.joblib")
        metadata = joblib.load(model_dir / "nhl_spreads_metadata_latest.joblib")

        self.feature_names = metadata['feature_names']
        self.coefficients = self.model.coef_
        self.intercept = self.model.intercept_

        stats = metadata['training_stats']['linear_regression']

        self.model_performance = {
            'mae': stats['mae'],
            'rmse': stats['rmse'],
            'r2': stats['r2'],
            'puckline_accuracy': stats.get('puckline_accuracy', 0.0),
            'within_1_goal': stats.get('within_1_goal', 0.0),
            'games_trained': stats['n_samples']
        }

    def _extract_features(self, game_data: Dict) -> np.ndarray:
        """Extract features matching training data format"""
        home = game_data.get('home_stats', {})
        away = game_data.get('away_stats', {})

        features = np.zeros((1, len(self.feature_names)))

        # Team strength differential (key for spreads)
        features[0, 0] = home.get('goals_per_game', 3.0) - away.get('goals_per_game', 3.0)
        features[0, 1] = home.get('goals_against_per_game', 3.0) - away.get('goals_against_per_game', 3.0)
        features[0, 2] = home.get('win_pct', 0.500) - away.get('win_pct', 0.500)

        # Core stats
        features[0, 3] = home.get('goals_per_game', 3.0)
        features[0, 4] = away.get('goals_per_game', 3.0)
        features[0, 5] = home.get('goals_against_per_game', 3.0)
        features[0, 6] = away.get('goals_against_per_game', 3.0)

        # Goalie advantage
        home_goalie = game_data.get('home_goalie', {})
        away_goalie = game_data.get('away_goalie', {})
        features[0, 7] = home_goalie.get('save_pct', 0.910) - away_goalie.get('save_pct', 0.910)
        features[0, 8] = away_goalie.get('gaa', 2.8) - home_goalie.get('gaa', 2.8)  # Lower GAA is better

        # Home ice advantage (constant)
        features[0, 9] = 1.0

        return features

    def predict(self, game_data: Dict, market_spread: Optional[float] = None) -> Dict:
        """Generate prediction with confidence and market analysis"""
        features = self._extract_features(game_data)

        prediction = self.model.predict(features)[0]

        std_dev = 1.35  # NHL margin variance
        confidence = 0.66

        result = {
            'model_id': 'linear_regression',
            'model_name': 'Linear Regression',
            'sport': 'NHL',
            'prediction': {
                'spread': round(prediction, 1),
                'confidence': round(confidence, 2),
                'std_dev': round(std_dev, 1)
            },
            'model_performance': self.model_performance,
            'feature_importance': self._get_feature_importance(),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'success'
        }

        if market_spread is not None:
            edge = prediction - market_spread
            probability_home_covers = self._calculate_probability_over(prediction, std_dev, market_spread)
            probability_away_covers = 1 - probability_home_covers

            if abs(edge) < 0.45:  # Need larger edge with linear regression
                recommendation = 'PASS'
            elif edge > 0:
                recommendation = 'HOME'
            else:
                recommendation = 'AWAY'

            if recommendation == 'HOME':
                win_prob = probability_home_covers
            elif recommendation == 'AWAY':
                win_prob = probability_away_covers
            else:
                win_prob = 0.5

            if win_prob > 0.5 and recommendation != 'PASS':
                kelly_fraction = ((win_prob * 1.909) - 1) / 0.909
                kelly_fraction = min(kelly_fraction / 4, 0.03)
            else:
                kelly_fraction = 0.0

            result['market_analysis'] = {
                'market_line': market_spread,
                'edge': round(edge, 2),
                'recommendation': recommendation,
                'probability_home_covers': round(probability_home_covers, 3),
                'probability_away_covers': round(probability_away_covers, 3),
                'kelly_fraction': round(kelly_fraction, 3)
            }

        return result

    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from coefficients"""
        importance = {}
        for i, feature_name in enumerate(self.feature_names):
            importance[feature_name] = round(float(self.coefficients[i]), 4)
        return importance

    def _calculate_probability_over(self, predicted_margin: float, std_dev: float,
                                   market_spread: float) -> float:
        """Calculate probability that home team will cover the spread"""
        from scipy import stats
        z_score = (market_spread - predicted_margin) / std_dev
        probability_under = stats.norm.cdf(z_score)
        return 1 - probability_under


# Singleton instance
_model_instance = None

def get_nhl_linear_regression_spreads_model():
    """Get or create singleton Linear Regression spreads model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = LinearRegressionSpreadsModel()
    return _model_instance
