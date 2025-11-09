"""
Linear Regression Model for NBA Spreads Prediction
Primary model for NBA spreads - power ratings approach

Per sports-betting-models-guide.md:
- Primary model for NBA spreads
- Regression with rest, travel, motivation factors
- 65.2% ATS accuracy in training
"""

import numpy as np
import joblib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class LinearRegressionSpreadsModel:
    """Linear Regression model for predicting NBA spreads (home margin)"""

    def __init__(self):
        """Initialize Linear Regression spreads model by loading trained model"""
        # Load trained model and metadata
        model_dir = Path(__file__).parent.parent.parent / "ml" / "models"

        self.model = joblib.load(model_dir / "nba_linear_regression_spreads_latest.joblib")
        metadata = joblib.load(model_dir / "nba_spreads_metadata_latest.joblib")

        self.feature_names = metadata['feature_names']
        stats = metadata['training_stats']['linear_regression']

        self.model_performance = {
            'mae': stats['mae'],
            'rmse': stats['rmse'],
            'r2': stats['r2'],
            'ats_accuracy': stats['ats_accuracy'],
            'within_3_pts': stats['within_3_pts'],
            'within_7_pts': stats['within_7_pts'],
            'games_trained': stats['n_samples']
        }

    def _extract_features(self, game_data: Dict) -> np.ndarray:
        """Extract features matching training data format"""
        home = game_data.get('home_stats', {})
        away = game_data.get('away_stats', {})

        features = np.zeros((1, len(self.feature_names)))

        features[0, 0] = home.get('pace', 98.0)
        features[0, 1] = away.get('pace', 98.0)
        features[0, 2] = home.get('off_rating', 110.0)
        features[0, 3] = away.get('off_rating', 110.0)
        features[0, 4] = home.get('def_rating', 110.0)
        features[0, 5] = away.get('def_rating', 110.0)

        return features

    def predict(self, game_data: Dict, market_spread: Optional[float] = None) -> Dict:
        """
        Generate prediction with confidence and market analysis

        Args:
            game_data: Game and team statistics
            market_spread: Current betting market spread (home team perspective, optional)

        Returns:
            Complete prediction with confidence, edge, and recommendations
        """
        # Extract features
        features = self._extract_features(game_data)

        # Get prediction from Linear Regression (home margin)
        prediction = self.model.predict(features)[0]

        # Linear regression has constant variance
        confidence = 0.68
        std_dev = 4.7

        result = {
            'model_id': 'linear_regression',
            'model_name': 'Linear Regression',
            'prediction': {
                'spread': round(prediction, 1),
                'confidence': round(confidence, 2),
                'std_dev': round(std_dev, 1)
            },
            'model_performance': self.model_performance,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'success'
        }

        # Add market analysis if market spread provided
        if market_spread is not None:
            edge = prediction - market_spread

            # Calculate probability of covering
            probability_home_covers = self._calculate_probability_over(prediction, std_dev, market_spread)
            probability_away_covers = 1 - probability_home_covers

            # Determine recommendation
            if abs(edge) < 2.0:
                recommendation = 'PASS'
            elif edge > 0:
                recommendation = 'HOME'
            else:
                recommendation = 'AWAY'

            # Calculate Kelly fraction
            if recommendation == 'HOME':
                win_prob = probability_home_covers
            elif recommendation == 'AWAY':
                win_prob = probability_away_covers
            else:
                win_prob = 0.5

            if win_prob > 0.5 and recommendation != 'PASS':
                kelly_fraction = ((win_prob * 1.909) - 1) / 0.909
                kelly_fraction = min(kelly_fraction / 4, 0.05)
            else:
                kelly_fraction = 0.0

            result['market_analysis'] = {
                'market_line': market_spread,
                'edge': round(edge, 1),
                'recommendation': recommendation,
                'probability_home_covers': round(probability_home_covers, 3),
                'probability_away_covers': round(probability_away_covers, 3),
                'kelly_fraction': round(kelly_fraction, 3)
            }

        return result

    def _calculate_probability_over(self, predicted_margin: float, std_dev: float,
                                   market_spread: float) -> float:
        """Calculate probability that home team will cover the spread"""
        from scipy import stats

        z_score = (market_spread - predicted_margin) / std_dev
        probability_under = stats.norm.cdf(z_score)
        probability_over = 1 - probability_under

        return probability_over


# Singleton instance
_model_instance = None


def get_nba_linear_regression_spreads_model():
    """Get or create singleton Linear Regression spreads model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = LinearRegressionSpreadsModel()
    return _model_instance
