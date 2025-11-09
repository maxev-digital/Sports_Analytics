"""
NCAAB Regression-to-Mean Live Analyzer
Calculates z-scores for live NCAAB games and identifies betting opportunities

This module:
1. Loads trained Max EV Boost ML models (KenPom-based)
2. Takes current game state (KenPom efficiency, tempo)
3. Predicts expected total with confidence intervals
4. Calculates z-score vs live betting line
5. Returns alerts when z >= 2.0 SD
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import os
from typing import Dict, List, Optional

class NCAABRegressionAnalyzer:
    """Analyzes live NCAAB games for regression-to-mean opportunities"""

    # CRITICAL: Feature order MUST match training data exactly (from XGBoost model)
    # Training used only raw KenPom features, no differentials
    FEATURE_ORDER = [
        'home_adj_em', 'away_adj_em',
        'home_off_eff', 'away_off_eff',
        'home_def_eff', 'away_def_eff',
        'home_tempo', 'away_tempo'
    ]

    def __init__(self):
        # Use absolute path to models directory
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_dir = os.path.join(script_dir, "models") + os.sep
        self.models = {}
        self._load_models()

    def _load_models(self):
        """Load the three quantile models (lower, mean, upper)"""
        for model_type in ['lower', 'mean', 'upper']:
            model_path = f"{self.model_dir}ncaab_quantile_{model_type}_latest.json"

            if not os.path.exists(model_path):
                print(f"[WARNING] Model not found: {model_path}")
                continue

            model = xgb.Booster()
            model.load_model(model_path)
            self.models[model_type] = model

    def prepare_game_features(self, game_data: Dict) -> pd.DataFrame:
        """
        Convert live game data to model features

        Expected game_data format:
        {
            'home_team': 'Duke',
            'away_team': 'North Carolina',
            'home_stats': {
                'adj_em': 28.5,      # KenPom adjusted efficiency margin
                'off_eff': 118.2,    # Offensive efficiency
                'def_eff': 89.7,     # Defensive efficiency
                'tempo': 70.5        # Adjusted tempo (possessions per 40 min)
            },
            'away_stats': {
                'adj_em': 25.3,
                'off_eff': 115.8,
                'def_eff': 90.5,
                'tempo': 68.2
            },
            'live_total': 145.5  # Current live betting line (optional)
        }
        """

        home = game_data['home_stats']
        away = game_data['away_stats']

        features = {
            # Home team KenPom stats
            'home_adj_em': home.get('adj_em', 10.0),
            'home_off_eff': home.get('off_eff', 105.0),
            'home_def_eff': home.get('def_eff', 95.0),
            'home_tempo': home.get('tempo', 68.0),

            # Away team KenPom stats
            'away_adj_em': away.get('adj_em', 10.0),
            'away_off_eff': away.get('off_eff', 105.0),
            'away_def_eff': away.get('def_eff', 95.0),
            'away_tempo': away.get('tempo', 68.0),
        }

        # Create DataFrame with exact feature order from training (CRITICAL for XGBoost)
        df = pd.DataFrame([features])
        return df[self.FEATURE_ORDER]

    def analyze_game(self, game_data: Dict) -> Dict:
        """
        Analyze a live game for regression-to-mean opportunities

        Returns:
        {
            'predicted_mean': 142.5,
            'predicted_lower': 130.2,
            'predicted_upper': 154.8,
            'std_dev': 9.6,
            'live_total': 145.5,
            'z_score': 0.31,
            'is_alert': False,
            'alert_type': None,
            'confidence': 'LOW',
            'recommended_bet': None,
            'kelly_pct': 0.0
        }
        """

        # Prepare features
        X = self.prepare_game_features(game_data)
        dmatrix = xgb.DMatrix(X)

        # Make predictions
        predictions = {
            'lower': self.models['lower'].predict(dmatrix)[0],
            'mean': self.models['mean'].predict(dmatrix)[0],
            'upper': self.models['upper'].predict(dmatrix)[0]
        }

        # Calculate standard deviation
        interval_width = predictions['upper'] - predictions['lower']
        std_dev = interval_width / 2.56  # 80% interval = 2.56 SD

        # Get live total if provided
        live_total = game_data.get('live_total', None)

        result = {
            'predicted_mean': round(predictions['mean'], 1),
            'predicted_lower': round(predictions['lower'], 1),
            'predicted_upper': round(predictions['upper'], 1),
            'std_dev': round(std_dev, 2),
            'interval_width': round(interval_width, 1),
            'live_total': live_total
        }

        # Calculate z-score if live total available
        if live_total is not None:
            z_score = (live_total - predictions['mean']) / std_dev
            result['z_score'] = round(z_score, 2)

            # Run Monte Carlo simulation for probability distribution
            monte_carlo = self._simulate_total_distribution(
                predictions['mean'],
                std_dev,
                live_total
            )
            result['monte_carlo'] = monte_carlo

            # Determine alert status
            is_alert = abs(z_score) >= 2.0
            result['is_alert'] = is_alert

            if z_score >= 2.5:
                result['alert_type'] = 'UNDER'
                result['confidence'] = 'EXTREME'
            elif z_score >= 2.0:
                result['alert_type'] = 'UNDER'
                result['confidence'] = 'STRONG'
            elif z_score <= -2.5:
                result['alert_type'] = 'OVER'
                result['confidence'] = 'EXTREME'
            elif z_score <= -2.0:
                result['alert_type'] = 'OVER'
                result['confidence'] = 'STRONG'
            elif abs(z_score) >= 1.5:
                if z_score > 0:
                    result['alert_type'] = 'UNDER'
                else:
                    result['alert_type'] = 'OVER'
                result['confidence'] = 'MODERATE'
            else:
                result['alert_type'] = None
                result['confidence'] = 'LOW'

            # Recommended bet (only for 2.0+ SD)
            if is_alert:
                result['recommended_bet'] = result['alert_type']
                result['kelly_pct'] = self._calculate_kelly(abs(z_score))
            else:
                result['recommended_bet'] = None
                result['kelly_pct'] = 0.0

        else:
            result['z_score'] = None
            result['is_alert'] = False
            result['alert_type'] = None
            result['confidence'] = 'N/A'
            result['recommended_bet'] = None
            result['kelly_pct'] = 0.0
            result['monte_carlo'] = None

        return result

    def _simulate_total_distribution(self, predicted_mean: float, std_dev: float,
                                    live_total: float, n_simulations: int = 10000) -> Dict:
        """
        Run Monte Carlo simulation to generate probability distribution

        Returns probabilities, expected value, and distribution metrics
        """
        # Generate simulated game totals using normal distribution
        simulated_totals = np.random.normal(predicted_mean, std_dev, n_simulations)

        # Calculate win probabilities
        over_probability = np.mean(simulated_totals > live_total)
        under_probability = np.mean(simulated_totals < live_total)
        push_probability = 1 - (over_probability + under_probability)

        # Calculate expected value (assuming -110 odds both sides)
        # American -110 = 1.909 decimal odds, returns $0.909 profit per $1 bet
        over_ev = (over_probability * 0.909) - (under_probability * 1.0)
        under_ev = (under_probability * 0.909) - (over_probability * 1.0)

        # Distribution percentiles
        percentiles = {
            '10th': np.percentile(simulated_totals, 10),
            '25th': np.percentile(simulated_totals, 25),
            '50th': np.percentile(simulated_totals, 50),
            '75th': np.percentile(simulated_totals, 75),
            '90th': np.percentile(simulated_totals, 90)
        }

        return {
            'over_probability': round(over_probability, 4),
            'under_probability': round(under_probability, 4),
            'push_probability': round(push_probability, 4),
            'over_ev': round(over_ev, 4),
            'under_ev': round(under_ev, 4),
            'percentiles': percentiles,
            'simulated_mean': round(np.mean(simulated_totals), 1),
            'simulated_std': round(np.std(simulated_totals), 2)
        }

    def _calculate_kelly(self, z_score: float) -> float:
        """
        Calculate recommended Kelly Criterion bet size

        Based on historical win rates:
        - 2.0-2.49 SD: 62% win rate
        - 2.5+ SD: 68% win rate
        """

        if z_score >= 2.5:
            win_prob = 0.68
        elif z_score >= 2.0:
            win_prob = 0.62
        else:
            return 0.0

        # Assuming -110 odds (1.909 decimal)
        decimal_odds = 1.909

        # Kelly formula: (p * odds - 1) / (odds - 1)
        kelly = (win_prob * decimal_odds - 1) / (decimal_odds - 1)

        # Use quarter Kelly for safety
        quarter_kelly = kelly / 4

        # Cap at 5% for safety
        return min(round(quarter_kelly * 100, 1), 5.0)

    def analyze_multiple_games(self, games_data: List[Dict]) -> List[Dict]:
        """Analyze multiple live games at once"""
        results = []

        for game_data in games_data:
            try:
                result = self.analyze_game(game_data)
                result['game_id'] = game_data.get('game_id')
                result['home_team'] = game_data.get('home_team')
                result['away_team'] = game_data.get('away_team')
                results.append(result)
            except Exception as e:
                print(f"[ERROR] Failed to analyze game {game_data.get('game_id')}: {e}")
                continue

        return results

    def get_alerts_only(self, games_data: List[Dict]) -> List[Dict]:
        """Return only games with 2.0+ SD alerts"""
        all_results = self.analyze_multiple_games(games_data)
        return [r for r in all_results if r.get('is_alert', False)]


# Example usage
if __name__ == "__main__":
    analyzer = NCAABRegressionAnalyzer()

    # Example game data
    example_game = {
        'game_id': 'test_001',
        'home_team': 'Duke',
        'away_team': 'North Carolina',
        'home_stats': {
            'adj_em': 28.5,      # Strong team
            'off_eff': 118.2,
            'def_eff': 89.7,
            'tempo': 70.5
        },
        'away_stats': {
            'adj_em': 25.3,      # Good team
            'off_eff': 115.8,
            'def_eff': 90.5,
            'tempo': 68.2
        },
        'live_total': 160.5  # Live line drifted high
    }

    print("=" * 70)
    print("NCAAB REGRESSION ANALYZER - TEST")
    print("=" * 70)
    print()

    result = analyzer.analyze_game(example_game)

    print(f"Game: {example_game['away_team']} @ {example_game['home_team']}")
    print()
    print(f"Predicted Total: {result['predicted_mean']} points")
    print(f"80% Range: {result['predicted_lower']} - {result['predicted_upper']}")
    print(f"Standard Deviation: {result['std_dev']} points")
    print()
    print(f"Live Total: {result['live_total']}")
    print(f"Z-Score: {result['z_score']} SD")
    print()
    print(f"Alert: {result['is_alert']}")
    print(f"Alert Type: {result['alert_type']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Recommended Bet: {result['recommended_bet']}")
    print(f"Kelly %: {result['kelly_pct']}% of bankroll")
    print()
