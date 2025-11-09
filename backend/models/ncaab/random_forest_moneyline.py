"""
Random Forest Model for NCAAB Moneyline Prediction
Predicts win probability for home and away teams

College basketball has more variance than NBA due to:
- Larger home court advantage (3-4 points)
- Greater talent disparity between conferences
- March Madness upsets (tournament variance)
"""

import numpy as np
import joblib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class RandomForestMoneylineModel:
    """Random Forest classifier for predicting NCAAB moneyline outcomes"""

    def __init__(self):
        """Initialize Random Forest moneyline model by loading trained model"""
        model_dir = Path(__file__).parent.parent.parent / "ml" / "models"

        self.model = joblib.load(model_dir / "ncaab_random_forest_moneyline_latest.joblib")
        metadata = joblib.load(model_dir / "ncaab_moneyline_metadata_latest.joblib")

        self.feature_names = metadata['feature_names']
        stats = metadata['training_stats']['random_forest']

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

        # KenPom efficiency differential (most predictive for win/loss)
        features[0, 0] = home.get('adj_off_eff', 105.0) - away.get('adj_off_eff', 105.0)
        features[0, 1] = away.get('adj_def_eff', 100.0) - home.get('adj_def_eff', 100.0)
        features[0, 2] = home.get('adj_em', 5.0) - away.get('adj_em', 5.0)  # Efficiency margin

        # KenPom ratings
        features[0, 3] = home.get('adj_off_eff', 105.0)
        features[0, 4] = away.get('adj_off_eff', 105.0)
        features[0, 5] = home.get('adj_def_eff', 100.0)
        features[0, 6] = away.get('adj_def_eff', 100.0)
        features[0, 7] = home.get('adj_tempo', 68.0)
        features[0, 8] = away.get('adj_tempo', 68.0)

        # Team performance
        features[0, 9] = home.get('points_per_game', 72.0)
        features[0, 10] = away.get('points_per_game', 72.0)
        features[0, 11] = home.get('points_allowed_per_game', 68.0)
        features[0, 12] = away.get('points_allowed_per_game', 68.0)

        # Shooting efficiency
        features[0, 13] = home.get('fg_pct', 45.0)
        features[0, 14] = away.get('fg_pct', 45.0)
        features[0, 15] = home.get('three_pt_pct', 34.0)
        features[0, 16] = away.get('three_pt_pct', 34.0)
        features[0, 17] = home.get('ft_pct', 72.0)
        features[0, 18] = away.get('ft_pct', 72.0)

        # Advanced stats
        features[0, 19] = home.get('rebound_margin', 0.0)
        features[0, 20] = away.get('rebound_margin', 0.0)
        features[0, 21] = home.get('turnover_margin', 0.0)
        features[0, 22] = away.get('turnover_margin', 0.0)
        features[0, 23] = home.get('assist_turnover_ratio', 1.2)
        features[0, 24] = away.get('assist_turnover_ratio', 1.2)

        # Record/momentum
        features[0, 25] = home.get('win_pct', 0.500)
        features[0, 26] = away.get('win_pct', 0.500)
        features[0, 27] = home.get('wins', 15)
        features[0, 28] = away.get('wins', 15)

        # Conference strength
        features[0, 29] = home.get('conference_rpi', 50.0)
        features[0, 30] = away.get('conference_rpi', 50.0)
        features[0, 31] = home.get('sos', 50.0)  # Strength of schedule
        features[0, 32] = away.get('sos', 50.0)

        # Home court advantage
        features[0, 33] = 1.0

        return features

    def predict(self, game_data: Dict, market_odds: Optional[Dict] = None) -> Dict:
        """Generate prediction with confidence and market analysis"""
        features = self._extract_features(game_data)

        # Get win probability from Random Forest
        probabilities = self.model.predict_proba(features)[0]
        home_win_prob = probabilities[1]
        away_win_prob = probabilities[0]

        # Calculate confidence from tree consensus
        if hasattr(self.model, 'estimators_'):
            tree_probs = np.array([
                tree.predict_proba(features)[0][1]
                for tree in self.model.estimators_
            ])
            consensus = np.std(tree_probs)
            confidence = 1 - min(consensus * 2, 0.4)
        else:
            confidence = 0.72

        result = {
            'model_id': 'random_forest',
            'model_name': 'Random Forest',
            'sport': 'NCAAB',
            'prediction': {
                'home_win_probability': round(home_win_prob, 3),
                'away_win_probability': round(away_win_prob, 3),
                'predicted_winner': 'HOME' if home_win_prob > 0.5 else 'AWAY',
                'confidence': round(confidence, 2)
            },
            'model_performance': self.model_performance,
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

            # Need 4% edge in college basketball due to higher variance
            if abs(home_edge) > abs(away_edge) and home_edge > 0.04:
                recommendation = 'HOME'
                edge_value = home_edge
                bet_prob = home_win_prob
                bet_odds = home_odds
            elif abs(away_edge) > abs(home_edge) and away_edge > 0.04:
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
                kelly_fraction = min(kelly_fraction / 4, 0.04)  # Quarter Kelly, max 4%
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

def get_ncaab_random_forest_moneyline_model():
    """Get or create singleton Random Forest moneyline model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = RandomForestMoneylineModel()
    return _model_instance
