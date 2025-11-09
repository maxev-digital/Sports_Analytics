"""
XGBoost Model for NCAAB Moneyline Prediction
High-accuracy gradient boosting for college basketball win probability
"""

import numpy as np
import joblib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class XGBoostMoneylineModel:
    """XGBoost classifier for predicting NCAAB moneyline outcomes"""

    def __init__(self):
        model_dir = Path(__file__).parent.parent.parent / "ml" / "models"
        self.model = joblib.load(model_dir / "ncaab_xgboost_moneyline_latest.joblib")
        metadata = joblib.load(model_dir / "ncaab_moneyline_metadata_latest.joblib")
        self.feature_names = metadata['feature_names']
        stats = metadata['training_stats']['xgboost']
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
        home, away = game_data.get('home_stats', {}), game_data.get('away_stats', {})
        features = np.zeros((1, len(self.feature_names)))

        # Efficiency differential
        features[0, :3] = [
            home.get('adj_off_eff', 105.0) - away.get('adj_off_eff', 105.0),
            away.get('adj_def_eff', 100.0) - home.get('adj_def_eff', 100.0),
            home.get('adj_em', 5.0) - away.get('adj_em', 5.0)
        ]

        # KenPom ratings
        features[0, 3:9] = [
            home.get('adj_off_eff', 105.0), away.get('adj_off_eff', 105.0),
            home.get('adj_def_eff', 100.0), away.get('adj_def_eff', 100.0),
            home.get('adj_tempo', 68.0), away.get('adj_tempo', 68.0)
        ]

        # Performance stats
        features[0, 9:13] = [
            home.get('points_per_game', 72.0), away.get('points_per_game', 72.0),
            home.get('points_allowed_per_game', 68.0), away.get('points_allowed_per_game', 68.0)
        ]

        # Shooting
        features[0, 13:19] = [
            home.get('fg_pct', 45.0), away.get('fg_pct', 45.0),
            home.get('three_pt_pct', 34.0), away.get('three_pt_pct', 34.0),
            home.get('ft_pct', 72.0), away.get('ft_pct', 72.0)
        ]

        # Advanced
        features[0, 19:25] = [
            home.get('rebound_margin', 0.0), away.get('rebound_margin', 0.0),
            home.get('turnover_margin', 0.0), away.get('turnover_margin', 0.0),
            home.get('assist_turnover_ratio', 1.2), away.get('assist_turnover_ratio', 1.2)
        ]

        # Record/conference
        features[0, 25:33] = [
            home.get('win_pct', 0.500), away.get('win_pct', 0.500),
            home.get('wins', 15), away.get('wins', 15),
            home.get('conference_rpi', 50.0), away.get('conference_rpi', 50.0),
            home.get('sos', 50.0), away.get('sos', 50.0)
        ]

        features[0, 33] = 1.0  # Home court
        return features

    def predict(self, game_data: Dict, market_odds: Optional[Dict] = None) -> Dict:
        features = self._extract_features(game_data)
        probabilities = self.model.predict_proba(features)[0]
        home_win_prob, away_win_prob = probabilities[1], probabilities[0]
        confidence = 0.75

        result = {
            'model_id': 'xgboost', 'model_name': 'XGBoost', 'sport': 'NCAAB',
            'prediction': {
                'home_win_probability': round(home_win_prob, 3),
                'away_win_probability': round(away_win_prob, 3),
                'predicted_winner': 'HOME' if home_win_prob > 0.5 else 'AWAY',
                'confidence': round(confidence, 2)
            },
            'model_performance': self.model_performance,
            'timestamp': datetime.utcnow().isoformat() + 'Z', 'status': 'success'
        }

        if market_odds is not None:
            home_odds, away_odds = market_odds.get('home'), market_odds.get('away')
            home_implied_prob = self._american_odds_to_probability(home_odds)
            away_implied_prob = self._american_odds_to_probability(away_odds)
            home_edge, away_edge = home_win_prob - home_implied_prob, away_win_prob - away_implied_prob

            if abs(home_edge) > abs(away_edge) and home_edge > 0.04:
                recommendation, edge_value, bet_prob, bet_odds = 'HOME', home_edge, home_win_prob, home_odds
            elif abs(away_edge) > abs(home_edge) and away_edge > 0.04:
                recommendation, edge_value, bet_prob, bet_odds = 'AWAY', away_edge, away_win_prob, away_odds
            else:
                recommendation, edge_value, bet_prob, bet_odds = 'PASS', 0.0, 0.5, 0

            if recommendation != 'PASS':
                decimal_odds = self._american_to_decimal(bet_odds)
                kelly_fraction = min(((bet_prob * decimal_odds) - 1) / (decimal_odds - 1) / 4, 0.04)
            else:
                kelly_fraction = 0.0

            result['market_analysis'] = {
                'home_market_odds': home_odds, 'away_market_odds': away_odds,
                'home_implied_prob': round(home_implied_prob, 3),
                'away_implied_prob': round(away_implied_prob, 3),
                'home_edge': round(home_edge, 3), 'away_edge': round(away_edge, 3),
                'recommendation': recommendation, 'edge_value': round(edge_value, 3),
                'kelly_fraction': round(kelly_fraction, 3)
            }
        return result

    def _american_odds_to_probability(self, odds: int) -> float:
        return 100 / (odds + 100) if odds > 0 else abs(odds) / (abs(odds) + 100)

    def _american_to_decimal(self, odds: int) -> float:
        return (odds / 100) + 1 if odds > 0 else (100 / abs(odds)) + 1

_model_instance = None
def get_ncaab_xgboost_moneyline_model():
    global _model_instance
    if _model_instance is None:
        _model_instance = XGBoostMoneylineModel()
    return _model_instance
