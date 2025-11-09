"""
Linear Regression Model for NFL Spreads Prediction
Predicts home_margin (home_score - away_score)

Per sports-betting-models-guide.md:
- PRIMARY model for NFL spreads
- Clear power ratings work well in NFL
- Linear enough relationships that regression often beats ML
- Much faster for live updates
- TeamRankings stats → point impact values works perfectly
"""

import numpy as np
import joblib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class LinearRegressionSpreadsModel:
    """Linear Regression model for predicting NFL spreads"""

    def __init__(self):
        """Initialize Linear Regression spreads model by loading trained model"""
        model_dir = Path(__file__).parent.parent.parent / "ml" / "models"

        self.model = joblib.load(model_dir / "nfl_linear_regression_spreads_latest.joblib")
        metadata = joblib.load(model_dir / "nfl_spreads_metadata_latest.joblib")

        self.feature_names = metadata['feature_names']
        self.coefficients = self.model.coef_
        self.intercept = self.model.intercept_

        stats = metadata['training_stats']['linear_regression']

        self.model_performance = {
            'mae': stats['mae'],
            'rmse': stats['rmse'],
            'r2': stats['r2'],
            'ats_accuracy': stats.get('ats_accuracy', 0.0),
            'within_3_pts': stats.get('within_3_pts', 0.0),
            'within_7_pts': stats.get('within_7_pts', 0.0),
            'games_trained': stats['n_samples']
        }

    def _extract_features(self, game_data: Dict) -> np.ndarray:
        """Extract features matching training data format"""
        home = game_data.get('home_stats', {})
        away = game_data.get('away_stats', {})

        features = np.zeros((1, len(self.feature_names)))

        # Power rating differential (most important)
        features[0, 0] = home.get('points_per_game', 22.0) - away.get('points_per_game', 22.0)
        features[0, 1] = home.get('points_allowed_per_game', 22.0) - away.get('points_allowed_per_game', 22.0)

        # Offensive efficiency
        features[0, 2] = home.get('points_per_game', 22.0)
        features[0, 3] = away.get('points_per_game', 22.0)
        features[0, 4] = home.get('yards_per_play', 5.5)
        features[0, 5] = away.get('yards_per_play', 5.5)
        features[0, 6] = home.get('third_down_pct', 40.0)
        features[0, 7] = away.get('third_down_pct', 40.0)

        # Defensive efficiency
        features[0, 8] = home.get('points_allowed_per_game', 22.0)
        features[0, 9] = away.get('points_allowed_per_game', 22.0)
        features[0, 10] = home.get('yards_per_play_allowed', 5.5)
        features[0, 11] = away.get('yards_per_play_allowed', 5.5)
        features[0, 12] = home.get('third_down_pct_defense', 40.0)
        features[0, 13] = away.get('third_down_pct_defense', 40.0)

        # Turnover differential
        features[0, 14] = home.get('turnover_margin', 0.0)
        features[0, 15] = away.get('turnover_margin', 0.0)

        # Home field advantage (typically 2.5 points in NFL)
        features[0, 16] = 1.0  # Binary home indicator

        return features

    def predict(self, game_data: Dict, market_spread: Optional[float] = None) -> Dict:
        """Generate prediction with confidence and market analysis"""
        features = self._extract_features(game_data)

        prediction = self.model.predict(features)[0]

        # NFL spreads have ~10-14 point variance
        std_dev = 11.0
        confidence = 0.72  # Linear regression is highly effective for NFL

        result = {
            'model_id': 'linear_regression',
            'model_name': 'Linear Regression',
            'sport': 'NFL',
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

            # NFL key numbers: 3, 7, 10 points
            # Need at least 1.5-2 point edge
            if abs(edge) < 1.5:
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
                kelly_fraction = min(kelly_fraction / 4, 0.04)  # Quarter Kelly, max 4% for NFL
            else:
                kelly_fraction = 0.0

            result['market_analysis'] = {
                'market_line': market_spread,
                'edge': round(edge, 2),
                'recommendation': recommendation,
                'probability_home_covers': round(probability_home_covers, 3),
                'probability_away_covers': round(probability_away_covers, 3),
                'kelly_fraction': round(kelly_fraction, 3),
                'crosses_key_number': self._crosses_key_number(market_spread, prediction)
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

    def _crosses_key_number(self, market_spread: float, prediction: float) -> bool:
        """Check if prediction crosses NFL key numbers (3, 7, 10)"""
        key_numbers = [3, 7, 10, -3, -7, -10]
        for key in key_numbers:
            if (market_spread < key < prediction) or (prediction < key < market_spread):
                return True
        return False


# Singleton instance
_model_instance = None

def get_nfl_linear_regression_spreads_model():
    """Get or create singleton Linear Regression spreads model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = LinearRegressionSpreadsModel()
    return _model_instance
