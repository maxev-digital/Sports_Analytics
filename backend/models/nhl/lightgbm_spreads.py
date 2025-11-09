"""
LightGBM Model for NHL Spreads (Puck Line) Prediction
Predicts home_margin (home_goals - away_goals)

Per sports-betting-models-guide.md:
- LightGBM is faster than XGBoost with similar/better accuracy
- Excellent for real-time predictions
- NHL puck lines typically ±1.5 goals
"""

import numpy as np
import joblib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class LightGBMSpreadsModel:
    """LightGBM model for predicting NHL spreads (puck line)"""

    def __init__(self):
        """Initialize LightGBM spreads model by loading trained model"""
        # Load trained model and metadata
        model_dir = Path(__file__).parent.parent.parent / "ml" / "models"

        self.model = joblib.load(model_dir / "nhl_lightgbm_spreads_latest.joblib")
        metadata = joblib.load(model_dir / "nhl_spreads_metadata_latest.joblib")

        self.feature_names = metadata['feature_names']
        stats = metadata['training_stats']['lightgbm']

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

        # Team strength differential
        features[0, 0] = home.get('goals_per_game', 3.0) - away.get('goals_per_game', 3.0)
        features[0, 1] = home.get('goals_against_per_game', 3.0) - away.get('goals_against_per_game', 3.0)

        # Offensive stats
        features[0, 2] = home.get('goals_per_game', 3.0)
        features[0, 3] = away.get('goals_per_game', 3.0)
        features[0, 4] = home.get('shots_per_game', 30.0)
        features[0, 5] = away.get('shots_per_game', 30.0)
        features[0, 6] = home.get('shooting_pct', 10.0)
        features[0, 7] = away.get('shooting_pct', 10.0)
        features[0, 8] = home.get('power_play_pct', 20.0)
        features[0, 9] = away.get('power_play_pct', 20.0)

        # Defensive stats
        features[0, 10] = home.get('goals_against_per_game', 3.0)
        features[0, 11] = away.get('goals_against_per_game', 3.0)
        features[0, 12] = home.get('shots_against_per_game', 30.0)
        features[0, 13] = away.get('shots_against_per_game', 30.0)
        features[0, 14] = home.get('penalty_kill_pct', 80.0)
        features[0, 15] = away.get('penalty_kill_pct', 80.0)
        features[0, 16] = home.get('save_pct', 0.910)
        features[0, 17] = away.get('save_pct', 0.910)

        # Advanced stats
        features[0, 18] = home.get('pdo', 100.0)
        features[0, 19] = away.get('pdo', 100.0)
        features[0, 20] = home.get('faceoff_win_pct', 50.0)
        features[0, 21] = away.get('faceoff_win_pct', 50.0)
        features[0, 22] = home.get('win_pct', 0.500)
        features[0, 23] = away.get('win_pct', 0.500)

        # Goalie stats
        home_goalie = game_data.get('home_goalie', {})
        away_goalie = game_data.get('away_goalie', {})
        features[0, 24] = home_goalie.get('save_pct', 0.910)
        features[0, 25] = away_goalie.get('save_pct', 0.910)
        features[0, 26] = home_goalie.get('gaa', 2.8)
        features[0, 27] = away_goalie.get('gaa', 2.8)

        # Home ice advantage
        features[0, 28] = 1.0

        return features

    def predict(self, game_data: Dict, market_spread: Optional[float] = None) -> Dict:
        """Generate prediction with confidence and market analysis"""
        features = self._extract_features(game_data)
        prediction = self.model.predict(features)[0]

        std_dev = 1.25  # LightGBM often has slightly lower variance
        confidence = 0.73

        result = {
            'model_id': 'lightgbm',
            'model_name': 'LightGBM',
            'sport': 'NHL',
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

            if abs(edge) < 0.4:
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

    def _calculate_probability_over(self, predicted_margin: float, std_dev: float,
                                   market_spread: float) -> float:
        """Calculate probability that home team will cover the spread"""
        from scipy import stats
        z_score = (market_spread - predicted_margin) / std_dev
        probability_under = stats.norm.cdf(z_score)
        return 1 - probability_under


# Singleton instance
_model_instance = None

def get_nhl_lightgbm_spreads_model():
    """Get or create singleton LightGBM spreads model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = LightGBMSpreadsModel()
    return _model_instance
