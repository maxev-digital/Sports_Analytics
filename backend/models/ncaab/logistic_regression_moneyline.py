"""
Logistic Regression Model for NCAAB Moneyline Prediction
Simple, interpretable win probability model for college basketball
"""

import numpy as np
import joblib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class LogisticRegressionMoneylineModel:
    """Logistic Regression classifier for predicting NCAAB moneyline outcomes"""

    def __init__(self):
        model_dir = Path(__file__).parent.parent.parent / "ml" / "models"
        self.model = joblib.load(model_dir / "ncaab_logistic_regression_moneyline_latest.joblib")
        metadata = joblib.load(model_dir / "ncaab_moneyline_metadata_latest.joblib")
        self.feature_names = metadata['feature_names']
        self.coefficients = self.model.coef_[0]
        self.intercept = self.model.intercept_[0]
        stats = metadata['training_stats']['logistic_regression']
        self.model_performance = {
            'accuracy': stats['accuracy'], 'precision': stats.get('precision', 0.0),
            'recall': stats.get('recall', 0.0), 'f1_score': stats.get('f1_score', 0.0),
            'roc_auc': stats.get('roc_auc', 0.0), 'log_loss': stats.get('log_loss', 0.0),
            'games_trained': stats['n_samples']
        }

    def _extract_features(self, game_data: Dict) -> np.ndarray:
        home, away = game_data.get('home_stats', {}), game_data.get('away_stats', {})
        features = np.zeros((1, len(self.feature_names)))

        # Efficiency differential (most important)
        features[0, 0] = home.get('adj_off_eff', 105.0) - away.get('adj_off_eff', 105.0)
        features[0, 1] = away.get('adj_def_eff', 100.0) - home.get('adj_def_eff', 100.0)
        features[0, 2] = home.get('adj_em', 5.0) - away.get('adj_em', 5.0)
        features[0, 3] = home.get('win_pct', 0.500) - away.get('win_pct', 0.500)

        # Core stats
        features[0, 4:8] = [home.get('points_per_game', 72.0), away.get('points_per_game', 72.0),
                            home.get('points_allowed_per_game', 68.0), away.get('points_allowed_per_game', 68.0)]

        # Shooting differential
        features[0, 8] = home.get('fg_pct', 45.0) - away.get('fg_pct', 45.0)
        features[0, 9] = home.get('three_pt_pct', 34.0) - away.get('three_pt_pct', 34.0)
        features[0, 10] = home.get('ft_pct', 72.0) - away.get('ft_pct', 72.0)

        # Margin differential
        features[0, 11] = home.get('rebound_margin', 0.0) - away.get('rebound_margin', 0.0)
        features[0, 12] = home.get('turnover_margin', 0.0) - away.get('turnover_margin', 0.0)

        # Record strength
        features[0, 13:15] = [home.get('win_pct', 0.500), away.get('win_pct', 0.500)]

        # Conference/schedule
        features[0, 15] = home.get('conference_rpi', 50.0) - away.get('conference_rpi', 50.0)
        features[0, 16] = home.get('sos', 50.0) - away.get('sos', 50.0)

        # Home court advantage
        features[0, 17] = 1.0
        return features

    def predict(self, game_data: Dict, market_odds: Optional[Dict] = None) -> Dict:
        features = self._extract_features(game_data)
        probabilities = self.model.predict_proba(features)[0]
        home_win_prob, away_win_prob = probabilities[1], probabilities[0]

        # Confidence based on probability distance from 0.5
        confidence = 0.67 + (abs(home_win_prob - 0.5) * 0.4)

        result = {
            'model_id': 'logistic_regression', 'model_name': 'Logistic Regression', 'sport': 'NCAAB',
            'prediction': {
                'home_win_probability': round(home_win_prob, 3),
                'away_win_probability': round(away_win_prob, 3),
                'predicted_winner': 'HOME' if home_win_prob > 0.5 else 'AWAY',
                'confidence': round(confidence, 2)
            },
            'model_performance': self.model_performance,
            'feature_importance': {name: round(float(coef), 4) for name, coef in zip(self.feature_names, self.coefficients)},
            'timestamp': datetime.utcnow().isoformat() + 'Z', 'status': 'success'
        }

        if market_odds:
            home_odds, away_odds = market_odds.get('home'), market_odds.get('away')
            home_implied = self._odds_to_prob(home_odds)
            away_implied = self._odds_to_prob(away_odds)
            home_edge, away_edge = home_win_prob - home_implied, away_win_prob - away_implied

            # Logistic regression needs larger threshold
            if abs(home_edge) > abs(away_edge) and home_edge > 0.05:
                rec, edge_val, prob, odds = 'HOME', home_edge, home_win_prob, home_odds
            elif abs(away_edge) > abs(home_edge) and away_edge > 0.05:
                rec, edge_val, prob, odds = 'AWAY', away_edge, away_win_prob, away_odds
            else:
                rec, edge_val, prob, odds = 'PASS', 0.0, 0.5, 0

            kelly = min(((prob * self._to_decimal(odds)) - 1) / (self._to_decimal(odds) - 1) / 4, 0.04) if rec != 'PASS' else 0.0

            result['market_analysis'] = {
                'home_market_odds': home_odds, 'away_market_odds': away_odds,
                'home_implied_prob': round(home_implied, 3), 'away_implied_prob': round(away_implied, 3),
                'home_edge': round(home_edge, 3), 'away_edge': round(away_edge, 3),
                'recommendation': rec, 'edge_value': round(edge_val, 3),
                'kelly_fraction': round(kelly, 3)
            }
        return result

    def _odds_to_prob(self, odds: int) -> float:
        return 100 / (odds + 100) if odds > 0 else abs(odds) / (abs(odds) + 100)

    def _to_decimal(self, odds: int) -> float:
        return (odds / 100) + 1 if odds > 0 else (100 / abs(odds)) + 1

_model_instance = None
def get_ncaab_logistic_regression_moneyline_model():
    global _model_instance
    if _model_instance is None:
        _model_instance = LogisticRegressionMoneylineModel()
    return _model_instance
