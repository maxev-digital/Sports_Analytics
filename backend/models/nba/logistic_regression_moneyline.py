"""
Logistic Regression for NBA Moneyline Prediction
Outputs clean probabilities, handles classification well

Per sports-betting-models-guide.md:
- Outputs clean probabilities
- Regression-based power ratings
- 66.40% accuracy in training
- 0.7197 ROC-AUC score
- Interpretable coefficients
"""

import numpy as np
import joblib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class LogisticRegressionMoneylineModel:
    """Logistic Regression model for predicting NBA moneyline (winner)"""

    def __init__(self):
        """Initialize Logistic Regression moneyline model by loading trained model"""
        # Load trained model and metadata
        model_dir = Path(__file__).parent.parent.parent / "ml" / "models"

        self.model = joblib.load(model_dir / "nba_logistic_regression_moneyline_latest.joblib")
        metadata = joblib.load(model_dir / "nba_moneyline_metadata_latest.joblib")

        self.feature_names = metadata['feature_names']
        stats = metadata['training_stats']['logistic_regression']

        self.model_performance = {
            'accuracy': stats['accuracy'],
            'roc_auc': stats['roc_auc'],
            'log_loss': stats['log_loss'],
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

    def predict(self, game_data: Dict, home_odds: Optional[float] = None,
                away_odds: Optional[float] = None) -> Dict:
        """
        Generate prediction with win probabilities and market analysis

        Args:
            game_data: Game and team statistics
            home_odds: Home team moneyline odds (American odds, optional)
            away_odds: Away team moneyline odds (American odds, optional)

        Returns:
            Complete prediction with probabilities, edge, and recommendations
        """
        # Extract features
        features = self._extract_features(game_data)

        # Get win probabilities from Logistic Regression
        probabilities = self.model.predict_proba(features)[0]
        prob_away_wins = probabilities[0]  # Class 0 = away wins
        prob_home_wins = probabilities[1]  # Class 1 = home wins

        # Winner prediction
        predicted_winner = 'HOME' if prob_home_wins > prob_away_wins else 'AWAY'

        # Confidence is max probability
        confidence = max(prob_home_wins, prob_away_wins)

        result = {
            'model_id': 'logistic_regression',
            'model_name': 'Logistic Regression',
            'prediction': {
                'winner': predicted_winner,
                'probability_home_wins': round(prob_home_wins, 3),
                'probability_away_wins': round(prob_away_wins, 3),
                'confidence': round(confidence, 2)
            },
            'model_performance': self.model_performance,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'success'
        }

        # Add market analysis if odds provided
        if home_odds is not None and away_odds is not None:
            # Convert American odds to implied probabilities
            home_implied_prob = self._american_odds_to_probability(home_odds)
            away_implied_prob = self._american_odds_to_probability(away_odds)

            # Calculate edge (our probability - market implied probability)
            home_edge = prob_home_wins - home_implied_prob
            away_edge = prob_away_wins - away_implied_prob

            # Determine recommendation (need at least 3% edge for value)
            if abs(home_edge) < 0.03 and abs(away_edge) < 0.03:
                recommendation = 'PASS'
                rec_team = None
                win_prob_for_kelly = 0.5
                decimal_odds = 1.0
            elif home_edge > away_edge:
                recommendation = 'HOME'
                rec_team = 'HOME'
                win_prob_for_kelly = prob_home_wins
                decimal_odds = self._american_to_decimal(home_odds)
            else:
                recommendation = 'AWAY'
                rec_team = 'AWAY'
                win_prob_for_kelly = prob_away_wins
                decimal_odds = self._american_to_decimal(away_odds)

            # Calculate Kelly fraction
            if recommendation != 'PASS':
                # Kelly = (p * decimal_odds - 1) / (decimal_odds - 1)
                kelly_fraction = (win_prob_for_kelly * decimal_odds - 1) / (decimal_odds - 1)
                kelly_fraction = max(0, min(kelly_fraction / 4, 0.05))  # Quarter Kelly, max 5%
            else:
                kelly_fraction = 0.0

            result['market_analysis'] = {
                'home_odds': home_odds,
                'away_odds': away_odds,
                'home_implied_prob': round(home_implied_prob, 3),
                'away_implied_prob': round(away_implied_prob, 3),
                'home_edge': round(home_edge, 3),
                'away_edge': round(away_edge, 3),
                'recommendation': recommendation,
                'recommended_team': rec_team,
                'kelly_fraction': round(kelly_fraction, 3)
            }

        return result

    def _american_odds_to_probability(self, american_odds: float) -> float:
        """Convert American odds to implied probability"""
        if american_odds > 0:
            # Underdog odds (e.g., +150)
            return 100 / (american_odds + 100)
        else:
            # Favorite odds (e.g., -150)
            return abs(american_odds) / (abs(american_odds) + 100)

    def _american_to_decimal(self, american_odds: float) -> float:
        """Convert American odds to decimal odds"""
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1


# Singleton instance
_model_instance = None


def get_nba_logistic_regression_moneyline_model():
    """Get or create singleton Logistic Regression moneyline model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = LogisticRegressionMoneylineModel()
    return _model_instance
