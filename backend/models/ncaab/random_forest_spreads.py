"""
Random Forest Model for NCAAB Spreads Prediction
Predicts home_margin (home_score - away_score)

Per sports-betting-models-guide.md:
- Similar to NBA approach with KenPom data
- Random Forest captures non-linear interactions
- Home court advantage is larger in college (3-4 points)
- Conference strength matters significantly
"""

import numpy as np
import joblib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class RandomForestSpreadsModel:
    """Random Forest model for predicting NCAAB spreads"""

    def __init__(self):
        """Initialize Random Forest spreads model by loading trained model"""
        model_dir = Path(__file__).parent.parent.parent / "ml" / "models"

        self.model = joblib.load(model_dir / "ncaab_random_forest_spreads_latest.joblib")
        metadata = joblib.load(model_dir / "ncaab_spreads_metadata_latest.joblib")

        self.feature_names = metadata['feature_names']
        stats = metadata['training_stats']['random_forest']

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

        # KenPom efficiency differential (most important for college)
        features[0, 0] = home.get('adj_off_eff', 105.0) - away.get('adj_off_eff', 105.0)
        features[0, 1] = away.get('adj_def_eff', 100.0) - home.get('adj_def_eff', 100.0)  # Lower is better

        # KenPom ratings
        features[0, 2] = home.get('adj_off_eff', 105.0)
        features[0, 3] = away.get('adj_off_eff', 105.0)
        features[0, 4] = home.get('adj_def_eff', 100.0)
        features[0, 5] = away.get('adj_def_eff', 100.0)
        features[0, 6] = home.get('adj_tempo', 68.0)
        features[0, 7] = away.get('adj_tempo', 68.0)

        # Team performance stats
        features[0, 8] = home.get('points_per_game', 72.0)
        features[0, 9] = away.get('points_per_game', 72.0)
        features[0, 10] = home.get('points_allowed_per_game', 68.0)
        features[0, 11] = away.get('points_allowed_per_game', 68.0)

        # Shooting efficiency
        features[0, 12] = home.get('fg_pct', 45.0)
        features[0, 13] = away.get('fg_pct', 45.0)
        features[0, 14] = home.get('three_pt_pct', 34.0)
        features[0, 15] = away.get('three_pt_pct', 34.0)
        features[0, 16] = home.get('ft_pct', 72.0)
        features[0, 17] = away.get('ft_pct', 72.0)

        # Advanced stats
        features[0, 18] = home.get('rebound_margin', 0.0)
        features[0, 19] = away.get('rebound_margin', 0.0)
        features[0, 20] = home.get('turnover_margin', 0.0)
        features[0, 21] = away.get('turnover_margin', 0.0)

        # Record/momentum
        features[0, 22] = home.get('win_pct', 0.500)
        features[0, 23] = away.get('win_pct', 0.500)

        # Conference strength (if available)
        features[0, 24] = home.get('conference_rpi', 50.0)
        features[0, 25] = away.get('conference_rpi', 50.0)

        # Home court advantage (larger in college - 3-4 points)
        features[0, 26] = 1.0

        return features

    def predict(self, game_data: Dict, market_spread: Optional[float] = None) -> Dict:
        """Generate prediction with confidence and market analysis"""
        features = self._extract_features(game_data)

        # Get prediction from Random Forest
        prediction = self.model.predict(features)[0]

        # Calculate confidence from tree variance
        if hasattr(self.model, 'estimators_'):
            tree_predictions = np.array([
                tree.predict(features)[0]
                for tree in self.model.estimators_
            ])
            std_dev = np.std(tree_predictions)
            confidence = 1 / (1 + std_dev / 10)  # Normalize for college basketball
        else:
            std_dev = 11.5
            confidence = 0.71

        result = {
            'model_id': 'random_forest',
            'model_name': 'Random Forest',
            'sport': 'NCAAB',
            'prediction': {
                'spread': round(prediction, 1),
                'confidence': round(confidence, 2),
                'std_dev': round(std_dev, 1)
            },
            'model_performance': self.model_performance,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'success'
        }

        if market_spread is not None:
            edge = prediction - market_spread
            probability_home_covers = self._calculate_probability_over(prediction, std_dev, market_spread)
            probability_away_covers = 1 - probability_home_covers

            # Need at least 2 point edge in college basketball
            if abs(edge) < 2.0:
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
                kelly_fraction = min(kelly_fraction / 4, 0.04)  # Quarter Kelly, max 4%
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
        return 1 - probability_under


# Singleton instance
_model_instance = None

def get_ncaab_random_forest_spreads_model():
    """Get or create singleton Random Forest spreads model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = RandomForestSpreadsModel()
    return _model_instance
