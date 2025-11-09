"""
Logistic Regression Model for NHL Moneyline Prediction
Predicts win probability for home and away teams

Per sports-betting-models-guide.md:
- Outputs clean probabilities for binary outcomes
- Fast and interpretable
- Good for win/loss classification
- Excellent baseline for moneyline betting
"""

import numpy as np
import joblib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class LogisticRegressionMoneylineModel:
    """Logistic Regression classifier for predicting NHL moneyline outcomes"""

    def __init__(self):
        """Initialize Logistic Regression moneyline model by loading trained model"""
        model_dir = Path(__file__).parent.parent.parent / "ml" / "models"

        self.model = joblib.load(model_dir / "nhl_logistic_regression_moneyline_latest.joblib")
        metadata = joblib.load(model_dir / "nhl_moneyline_metadata_latest.joblib")

        self.feature_names = metadata['feature_names']
        self.coefficients = self.model.coef_[0]
        self.intercept = self.model.intercept_[0]

        stats = metadata['training_stats']['logistic_regression']

        self.model_performance = {
            'accuracy': stats['accuracy'],
            'precision': stats.get('precision', 0.0),
            'recall': stats.get('recall', 0.0),
            'f1_score': stats.get('f1_score', 0.0),
            'roc_auc': stats.get('roc_auc', 0.0),
            'log_loss': stats.get('log_loss', 0.0),
            'games_trained': stats['n_samples']
        }

    def _extract_features(self, game_data: Dict) -> np.ndarray:
        """Extract features matching training data format"""
        home = game_data.get('home_stats', {})
        away = game_data.get('away_stats', {})

        features = np.zeros((1, len(self.feature_names)))

        # Team strength differential (most important for win/loss)
        features[0, 0] = home.get('goals_per_game', 3.0) - away.get('goals_per_game', 3.0)
        features[0, 1] = home.get('goals_against_per_game', 3.0) - away.get('goals_against_per_game', 3.0)
        features[0, 2] = home.get('win_pct', 0.500) - away.get('win_pct', 0.500)

        # Core team stats
        features[0, 3] = home.get('goals_per_game', 3.0)
        features[0, 4] = away.get('goals_per_game', 3.0)
        features[0, 5] = home.get('goals_against_per_game', 3.0)
        features[0, 6] = away.get('goals_against_per_game', 3.0)
        features[0, 7] = home.get('shooting_pct', 10.0)
        features[0, 8] = away.get('shooting_pct', 10.0)
        features[0, 9] = home.get('save_pct', 0.910)
        features[0, 10] = away.get('save_pct', 0.910)

        # Record/standings
        features[0, 11] = home.get('win_pct', 0.500)
        features[0, 12] = away.get('win_pct', 0.500)

        # Goalie differential (critical for NHL)
        home_goalie = game_data.get('home_goalie', {})
        away_goalie = game_data.get('away_goalie', {})
        features[0, 13] = home_goalie.get('save_pct', 0.910) - away_goalie.get('save_pct', 0.910)
        features[0, 14] = away_goalie.get('gaa', 2.8) - home_goalie.get('gaa', 2.8)

        # Home ice advantage
        features[0, 15] = 1.0

        return features

    def predict(self, game_data: Dict, market_odds: Optional[Dict] = None) -> Dict:
        """Generate prediction with confidence and market analysis"""
        features = self._extract_features(game_data)

        # Get win probability from Logistic Regression
        # Class 0 = Away win, Class 1 = Home win
        probabilities = self.model.predict_proba(features)[0]
        home_win_prob = probabilities[1]
        away_win_prob = probabilities[0]

        # Logistic regression confidence based on probability distance from 0.5
        prob_distance = abs(home_win_prob - 0.5)
        confidence = 0.65 + (prob_distance * 0.4)  # Range: 0.65-0.85

        result = {
            'model_id': 'logistic_regression',
            'model_name': 'Logistic Regression',
            'sport': 'NHL',
            'prediction': {
                'home_win_probability': round(home_win_prob, 3),
                'away_win_probability': round(away_win_prob, 3),
                'predicted_winner': 'HOME' if home_win_prob > 0.5 else 'AWAY',
                'confidence': round(confidence, 2)
            },
            'model_performance': self.model_performance,
            'feature_importance': self._get_feature_importance(),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'success'
        }

        if market_odds is not None:
            home_odds = market_odds.get('home')
            away_odds = market_odds.get('away')

            home_implied_prob = self._american_odds_to_probability(home_odds)
            away_implied_prob = self._american_odds_to_probability(away_odds)

            home_edge = home_win_prob - home_implied_prob
            away_edge = away_win_prob - away_implied_prob

            # Logistic regression needs larger edge threshold
            if abs(home_edge) > abs(away_edge) and home_edge > 0.06:  # 6% edge threshold
                recommendation = 'HOME'
                edge_value = home_edge
                bet_prob = home_win_prob
                bet_odds = home_odds
            elif abs(away_edge) > abs(home_edge) and away_edge > 0.06:
                recommendation = 'AWAY'
                edge_value = away_edge
                bet_prob = away_win_prob
                bet_odds = away_odds
            else:
                recommendation = 'PASS'
                edge_value = 0.0
                bet_prob = 0.5
                bet_odds = 0

            if recommendation != 'PASS':
                decimal_odds = self._american_to_decimal(bet_odds)
                kelly_fraction = ((bet_prob * decimal_odds) - 1) / (decimal_odds - 1)
                kelly_fraction = min(kelly_fraction / 4, 0.03)
            else:
                kelly_fraction = 0.0

            result['market_analysis'] = {
                'home_market_odds': home_odds,
                'away_market_odds': away_odds,
                'home_implied_prob': round(home_implied_prob, 3),
                'away_implied_prob': round(away_implied_prob, 3),
                'home_edge': round(home_edge, 3),
                'away_edge': round(away_edge, 3),
                'recommendation': recommendation,
                'edge_value': round(edge_value, 3),
                'kelly_fraction': round(kelly_fraction, 3)
            }

        return result

    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from coefficients (interpretability advantage)"""
        importance = {}
        for i, feature_name in enumerate(self.feature_names):
            importance[feature_name] = round(float(self.coefficients[i]), 4)
        return importance

    def _american_odds_to_probability(self, odds: int) -> float:
        """Convert American odds to implied probability"""
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)

    def _american_to_decimal(self, odds: int) -> float:
        """Convert American odds to decimal odds"""
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1


# Singleton instance
_model_instance = None

def get_nhl_logistic_regression_moneyline_model():
    """Get or create singleton Logistic Regression moneyline model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = LogisticRegressionMoneylineModel()
    return _model_instance
