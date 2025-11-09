"""
Random Forest Model for NHL Moneyline Prediction
Predicts win probability for home and away teams

Per sports-betting-models-guide.md:
- NHL is highly random sport with small edges
- Goalie quality is critical factor
- Random Forest good for classification with many variables
- Outputs clean win probabilities
"""

import numpy as np
import joblib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class RandomForestMoneylineModel:
    """Random Forest classifier for predicting NHL moneyline outcomes"""

    def __init__(self):
        """Initialize Random Forest moneyline model by loading trained model"""
        # Load trained model and metadata
        model_dir = Path(__file__).parent.parent.parent / "ml" / "models"

        self.model = joblib.load(model_dir / "nhl_random_forest_moneyline_latest.joblib")
        metadata = joblib.load(model_dir / "nhl_moneyline_metadata_latest.joblib")

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

        # Create feature array matching training format
        features = np.zeros((1, len(self.feature_names)))

        # Team strength differential
        features[0, 0] = home.get('goals_per_game', 3.0) - away.get('goals_per_game', 3.0)
        features[0, 1] = home.get('goals_against_per_game', 3.0) - away.get('goals_against_per_game', 3.0)
        features[0, 2] = home.get('win_pct', 0.500) - away.get('win_pct', 0.500)

        # Offensive stats
        features[0, 3] = home.get('goals_per_game', 3.0)
        features[0, 4] = away.get('goals_per_game', 3.0)
        features[0, 5] = home.get('shots_per_game', 30.0)
        features[0, 6] = away.get('shots_per_game', 30.0)
        features[0, 7] = home.get('shooting_pct', 10.0)
        features[0, 8] = away.get('shooting_pct', 10.0)
        features[0, 9] = home.get('power_play_pct', 20.0)
        features[0, 10] = away.get('power_play_pct', 20.0)

        # Defensive stats
        features[0, 11] = home.get('goals_against_per_game', 3.0)
        features[0, 12] = away.get('goals_against_per_game', 3.0)
        features[0, 13] = home.get('shots_against_per_game', 30.0)
        features[0, 14] = away.get('shots_against_per_game', 30.0)
        features[0, 15] = home.get('penalty_kill_pct', 80.0)
        features[0, 16] = away.get('penalty_kill_pct', 80.0)
        features[0, 17] = home.get('save_pct', 0.910)
        features[0, 18] = away.get('save_pct', 0.910)

        # Advanced stats
        features[0, 19] = home.get('pdo', 100.0)
        features[0, 20] = away.get('pdo', 100.0)
        features[0, 21] = home.get('faceoff_win_pct', 50.0)
        features[0, 22] = away.get('faceoff_win_pct', 50.0)

        # Record stats
        features[0, 23] = home.get('win_pct', 0.500)
        features[0, 24] = away.get('win_pct', 0.500)
        features[0, 25] = home.get('points', 50) / 82  # Normalize to 0-1 scale
        features[0, 26] = away.get('points', 50) / 82

        # Goalie stats (critical for NHL)
        home_goalie = game_data.get('home_goalie', {})
        away_goalie = game_data.get('away_goalie', {})
        features[0, 27] = home_goalie.get('save_pct', 0.910)
        features[0, 28] = away_goalie.get('save_pct', 0.910)
        features[0, 29] = home_goalie.get('gaa', 2.8)
        features[0, 30] = away_goalie.get('gaa', 2.8)
        features[0, 31] = home_goalie.get('wins', 15) / max(home_goalie.get('games_started', 30), 1)
        features[0, 32] = away_goalie.get('wins', 15) / max(away_goalie.get('games_started', 30), 1)

        # Home ice advantage
        features[0, 33] = 1.0  # Binary home indicator

        return features

    def predict(self, game_data: Dict, market_odds: Optional[Dict] = None) -> Dict:
        """
        Generate prediction with confidence and market analysis

        Args:
            game_data: Game and team statistics
            market_odds: Current betting market odds (optional)
                        Format: {'home': -150, 'away': +130}

        Returns:
            Complete prediction with confidence, edge, and recommendations
        """
        # Extract features
        features = self._extract_features(game_data)

        # Get win probability from Random Forest
        # Class 0 = Away win, Class 1 = Home win
        probabilities = self.model.predict_proba(features)[0]
        home_win_prob = probabilities[1]
        away_win_prob = probabilities[0]

        # Calculate confidence from tree consensus
        if hasattr(self.model, 'estimators_'):
            # Get all tree predictions
            tree_probs = np.array([
                tree.predict_proba(features)[0][1]  # Home win prob from each tree
                for tree in self.model.estimators_
            ])
            consensus = np.std(tree_probs)
            confidence = 1 - min(consensus * 2, 0.4)  # Convert variance to confidence
        else:
            confidence = 0.70

        result = {
            'model_id': 'random_forest',
            'model_name': 'Random Forest',
            'sport': 'NHL',
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

        # Add market analysis if market odds provided
        if market_odds is not None:
            home_odds = market_odds.get('home')
            away_odds = market_odds.get('away')

            # Convert American odds to implied probability
            home_implied_prob = self._american_odds_to_probability(home_odds)
            away_implied_prob = self._american_odds_to_probability(away_odds)

            # Calculate edge (difference between model prob and market prob)
            home_edge = home_win_prob - home_implied_prob
            away_edge = away_win_prob - away_implied_prob

            # Determine recommendation (need significant edge in NHL)
            if abs(home_edge) > abs(away_edge) and home_edge > 0.05:  # 5% edge threshold
                recommendation = 'HOME'
                edge_value = home_edge
                bet_prob = home_win_prob
                bet_odds = home_odds
            elif abs(away_edge) > abs(home_edge) and away_edge > 0.05:
                recommendation = 'AWAY'
                edge_value = away_edge
                bet_prob = away_win_prob
                bet_odds = away_odds
            else:
                recommendation = 'PASS'
                edge_value = 0.0
                bet_prob = 0.5
                bet_odds = 0

            # Calculate Kelly fraction
            if recommendation != 'PASS':
                decimal_odds = self._american_to_decimal(bet_odds)
                kelly_fraction = ((bet_prob * decimal_odds) - 1) / (decimal_odds - 1)
                kelly_fraction = min(kelly_fraction / 4, 0.03)  # Quarter Kelly, max 3% for NHL
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


def get_nhl_random_forest_moneyline_model():
    """Get or create singleton Random Forest moneyline model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = RandomForestMoneylineModel()
    return _model_instance
