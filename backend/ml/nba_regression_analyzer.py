"""
NBA Regression-to-Mean Live Analyzer
Calculates z-scores for live NBA games and identifies betting opportunities

This module:
1. Loads trained Max EV Boost ML models
2. Takes current game state (team stats, pace, score, etc.)
3. Predicts expected total with confidence intervals
4. Calculates z-score vs live betting line
5. Returns alerts when z >= 2.0 SD
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import os
from typing import Dict, List, Optional

class NBARegressionAnalyzer:
    """Analyzes live NBA games for regression-to-mean opportunities"""

    # CRITICAL: Feature order MUST match training data exactly (from XGBoost model)
    FEATURE_ORDER = [
        'home_games_played', 'home_wins', 'home_win_pct', 'home_ppg', 'home_opp_ppg',
        'home_point_diff', 'home_fg_pct', 'home_fg3_pct', 'home_ft_pct', 'home_rebounds',
        'home_assists', 'home_turnovers', 'home_steals', 'home_blocks', 'home_plus_minus',
        'home_last_5_ppg', 'home_last_10_ppg', 'home_last_5_wins', 'home_last_10_wins',
        'away_games_played', 'away_wins', 'away_win_pct', 'away_ppg', 'away_opp_ppg',
        'away_point_diff', 'away_fg_pct', 'away_fg3_pct', 'away_ft_pct', 'away_rebounds',
        'away_assists', 'away_turnovers', 'away_steals', 'away_blocks', 'away_plus_minus',
        'away_last_5_ppg', 'away_last_10_ppg', 'away_last_5_wins', 'away_last_10_wins',
        'win_pct_diff', 'ppg_diff', 'point_diff_diff', 'fg_pct_diff', 'fg3_pct_diff',
        'turnover_diff', 'rebound_diff', 'expected_total_simple', 'expected_total_vs_defense',
        'home_momentum', 'away_momentum'
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
            model_path = f"{self.model_dir}nba_quantile_{model_type}_latest.json"

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
            'home_team': 'LAL',
            'away_team': 'GSW',
            'home_stats': {
                'ppg': 115.5,
                'opp_ppg': 112.3,
                'fg_pct': 0.467,
                'fg3_pct': 0.365,
                'ft_pct': 0.785,
                'rebounds': 45.2,
                'assists': 25.3,
                'steals': 7.8,
                'blocks': 5.2,
                'turnovers': 13.5,
                'plus_minus': 3.2,
                'point_diff': 3.2,
                'win_pct': 0.580,
                'wins': 47,
                'games_played': 81,
                'last_5_ppg': 118.2,
                'last_5_wins': 3,
                'last_10_ppg': 116.8,
                'last_10_wins': 6,
                'momentum': 5.5
            },
            'away_stats': { ... same structure ... },
            'live_total': 230.5  # Current live betting line (optional)
        }
        """

        home = game_data['home_stats']
        away = game_data['away_stats']

        features = {
            # Home team stats
            'home_ppg': home.get('ppg', 110.0),
            'home_opp_ppg': home.get('opp_ppg', 110.0),
            'home_fg_pct': home.get('fg_pct', 0.460),
            'home_fg3_pct': home.get('fg3_pct', 0.360),
            'home_ft_pct': home.get('ft_pct', 0.780),
            'home_rebounds': home.get('rebounds', 44.0),
            'home_assists': home.get('assists', 25.0),
            'home_steals': home.get('steals', 7.5),
            'home_blocks': home.get('blocks', 5.0),
            'home_turnovers': home.get('turnovers', 13.5),
            'home_plus_minus': home.get('plus_minus', 0.0),
            'home_point_diff': home.get('point_diff', 0.0),
            'home_win_pct': home.get('win_pct', 0.500),
            'home_wins': home.get('wins', 41),
            'home_games_played': home.get('games_played', 82),
            'home_last_5_ppg': home.get('last_5_ppg', 110.0),
            'home_last_5_wins': home.get('last_5_wins', 2),
            'home_last_10_ppg': home.get('last_10_ppg', 110.0),
            'home_last_10_wins': home.get('last_10_wins', 5),
            'home_momentum': home.get('momentum', 0.0),

            # Away team stats
            'away_ppg': away.get('ppg', 110.0),
            'away_opp_ppg': away.get('opp_ppg', 110.0),
            'away_fg_pct': away.get('fg_pct', 0.460),
            'away_fg3_pct': away.get('fg3_pct', 0.360),
            'away_ft_pct': away.get('ft_pct', 0.780),
            'away_rebounds': away.get('rebounds', 44.0),
            'away_assists': away.get('assists', 25.0),
            'away_steals': away.get('steals', 7.5),
            'away_blocks': away.get('blocks', 5.0),
            'away_turnovers': away.get('turnovers', 13.5),
            'away_plus_minus': away.get('plus_minus', 0.0),
            'away_point_diff': away.get('point_diff', 0.0),
            'away_win_pct': away.get('win_pct', 0.500),
            'away_wins': away.get('wins', 41),
            'away_games_played': away.get('games_played', 82),
            'away_last_5_ppg': away.get('last_5_ppg', 110.0),
            'away_last_5_wins': away.get('last_5_wins', 2),
            'away_last_10_ppg': away.get('last_10_ppg', 110.0),
            'away_last_10_wins': away.get('last_10_wins', 5),
            'away_momentum': away.get('momentum', 0.0),
        }

        # Calculate differentials
        features['ppg_diff'] = features['home_ppg'] - features['away_ppg']
        features['fg_pct_diff'] = features['home_fg_pct'] - features['away_fg_pct']
        features['fg3_pct_diff'] = features['home_fg3_pct'] - features['away_fg3_pct']
        features['rebound_diff'] = features['home_rebounds'] - features['away_rebounds']
        features['turnover_diff'] = features['home_turnovers'] - features['away_turnovers']
        features['point_diff_diff'] = features['home_point_diff'] - features['away_point_diff']
        features['win_pct_diff'] = features['home_win_pct'] - features['away_win_pct']

        # Expected totals
        features['expected_total_simple'] = features['home_ppg'] + features['away_ppg']
        features['expected_total_vs_defense'] = features['home_ppg'] + features['away_opp_ppg']

        # Create DataFrame with exact feature order from training (CRITICAL for XGBoost)
        df = pd.DataFrame([features])
        return df[self.FEATURE_ORDER]

    def analyze_game(self, game_data: Dict) -> Dict:
        """
        Analyze a live game for regression-to-mean opportunities

        Returns:
        {
            'predicted_mean': 228.5,
            'predicted_lower': 212.3,
            'predicted_upper': 244.7,
            'std_dev': 16.2,
            'live_total': 230.5,
            'z_score': 0.12,
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
    analyzer = NBARegressionAnalyzer()

    # Example game data
    example_game = {
        'game_id': 'test_001',
        'home_team': 'LAL',
        'away_team': 'GSW',
        'home_stats': {
            'ppg': 115.5,
            'opp_ppg': 112.3,
            'fg_pct': 0.467,
            'fg3_pct': 0.365,
            'ft_pct': 0.785,
            'rebounds': 45.2,
            'assists': 25.3,
            'steals': 7.8,
            'blocks': 5.2,
            'turnovers': 13.5,
            'plus_minus': 3.2,
            'point_diff': 3.2,
            'win_pct': 0.580,
            'wins': 47,
            'games_played': 81,
            'last_5_ppg': 118.2,
            'last_5_wins': 3,
            'last_10_ppg': 116.8,
            'last_10_wins': 6,
            'momentum': 5.5
        },
        'away_stats': {
            'ppg': 118.2,
            'opp_ppg': 114.5,
            'fg_pct': 0.481,
            'fg3_pct': 0.385,
            'ft_pct': 0.765,
            'rebounds': 43.8,
            'assists': 27.1,
            'steals': 8.2,
            'blocks': 4.8,
            'turnovers': 14.2,
            'plus_minus': 3.7,
            'point_diff': 3.7,
            'win_pct': 0.610,
            'wins': 50,
            'games_played': 82,
            'last_5_ppg': 121.4,
            'last_5_wins': 4,
            'last_10_ppg': 119.6,
            'last_10_wins': 7,
            'momentum': 8.2
        },
        'live_total': 255.5  # Live line has drifted way up
    }

    print("=" * 70)
    print("NBA REGRESSION ANALYZER - TEST")
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
