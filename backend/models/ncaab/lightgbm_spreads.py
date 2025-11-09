"""
LightGBM Model for NCAAB Spreads Prediction
Fastest gradient boosting for college basketball spreads
"""

import numpy as np
import joblib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class LightGBMSpreadsModel:
    """LightGBM model for predicting NCAAB spreads"""

    def __init__(self):
        model_dir = Path(__file__).parent.parent.parent / "ml" / "models"
        self.model = joblib.load(model_dir / "ncaab_lightgbm_spreads_latest.joblib")
        metadata = joblib.load(model_dir / "ncaab_spreads_metadata_latest.joblib")
        self.feature_names = metadata['feature_names']
        stats = metadata['training_stats']['lightgbm']
        self.model_performance = {
            'mae': stats['mae'], 'rmse': stats['rmse'], 'r2': stats['r2'],
            'ats_accuracy': stats.get('ats_accuracy', 0.0),
            'within_3_pts': stats.get('within_3_pts', 0.0),
            'games_trained': stats['n_samples']
        }

    def _extract_features(self, game_data: Dict) -> np.ndarray:
        home, away = game_data.get('home_stats', {}), game_data.get('away_stats', {})
        features = np.zeros((1, len(self.feature_names)))
        features[0, 0] = home.get('adj_off_eff', 105.0) - away.get('adj_off_eff', 105.0)
        features[0, 1] = away.get('adj_def_eff', 100.0) - home.get('adj_def_eff', 100.0)
        features[0, 2:8] = [home.get('adj_off_eff', 105.0), away.get('adj_off_eff', 105.0),
                            home.get('adj_def_eff', 100.0), away.get('adj_def_eff', 100.0),
                            home.get('adj_tempo', 68.0), away.get('adj_tempo', 68.0)]
        features[0, 8:16] = [home.get('points_per_game', 72.0), away.get('points_per_game', 72.0),
                             home.get('points_allowed_per_game', 68.0), away.get('points_allowed_per_game', 68.0),
                             home.get('fg_pct', 45.0), away.get('fg_pct', 45.0),
                             home.get('three_pt_pct', 34.0), away.get('three_pt_pct', 34.0)]
        features[0, 16:24] = [home.get('rebound_margin', 0.0), away.get('rebound_margin', 0.0),
                              home.get('turnover_margin', 0.0), away.get('turnover_margin', 0.0),
                              home.get('win_pct', 0.500), away.get('win_pct', 0.500),
                              home.get('conference_rpi', 50.0), away.get('conference_rpi', 50.0)]
        features[0, 24] = 1.0
        return features

    def predict(self, game_data: Dict, market_spread: Optional[float] = None) -> Dict:
        features = self._extract_features(game_data)
        prediction = self.model.predict(features)[0]
        std_dev, confidence = 10.5, 0.75

        result = {
            'model_id': 'lightgbm', 'model_name': 'LightGBM', 'sport': 'NCAAB',
            'prediction': {'spread': round(prediction, 1), 'confidence': round(confidence, 2), 'std_dev': round(std_dev, 1)},
            'model_performance': self.model_performance,
            'timestamp': datetime.utcnow().isoformat() + 'Z', 'status': 'success'
        }

        if market_spread is not None:
            edge = prediction - market_spread
            from scipy import stats
            probability_home_covers = 1 - stats.norm.cdf((market_spread - prediction) / std_dev)
            recommendation = 'PASS' if abs(edge) < 2.0 else ('HOME' if edge > 0 else 'AWAY')
            win_prob = probability_home_covers if recommendation == 'HOME' else (1 - probability_home_covers if recommendation == 'AWAY' else 0.5)
            kelly_fraction = min(((win_prob * 1.909) - 1) / 0.909 / 4, 0.04) if win_prob > 0.5 and recommendation != 'PASS' else 0.0

            result['market_analysis'] = {
                'market_line': market_spread, 'edge': round(edge, 1), 'recommendation': recommendation,
                'probability_home_covers': round(probability_home_covers, 3),
                'probability_away_covers': round(1 - probability_home_covers, 3),
                'kelly_fraction': round(kelly_fraction, 3)
            }
        return result

_model_instance = None
def get_ncaab_lightgbm_spreads_model():
    global _model_instance
    if _model_instance is None:
        _model_instance = LightGBMSpreadsModel()
    return _model_instance
