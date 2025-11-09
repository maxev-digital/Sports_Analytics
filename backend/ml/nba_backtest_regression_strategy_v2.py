"""
NBA Regression-to-Mean Strategy Backtest v2
============================================

This script backtests a REALISTIC simulation of the regression-to-mean live betting strategy.

REVISED Strategy Logic:
-----------------------
The original logic was flawed because we were using the final score to both identify
the alert AND evaluate the bet. In reality:

1. We make a pregame prediction (e.g., 225 total)
2. During the game, if the score is tracking WAY higher/lower than predicted (2+ SD),
   we get an alert
3. The alert tells us: "Game is going way OVER/UNDER your prediction"
4. We bet on REGRESSION: that the final score will be closer to our prediction than
   the current trend suggests

SIMULATION METHOD:
------------------
Since we don't have live scoring data, we simulate it:
- If actual total ended at 265 with prediction of 225 (z=2.5):
  * Game was trending HIGH during play
  * Live line would have been inflated to ~255 (between prediction and actual)
  * We bet UNDER 255, expecting final to be < 255
  * Actual was 265, so bet LOSES
  * BUT if actual had been 250, bet would WIN (regression from trend)

The KEY INSIGHT: We're betting that the final score will show regression from the
extreme trend. The bet wins if actual is between our prediction and the live line.

SIMPLE TEST:
If prediction = 225, actual = 265, live line = 255
- Bet UNDER 255
- Loses because 265 > 255 (no regression happened)

If prediction = 225, actual = 245, live line = 239
- Game was trending high (z=2.0), live line inflated to 239
- Bet UNDER 239
- Wins because 245 < 255 but wait... 245 > 239, so loses!

ACTUALLY: The better logic is:
- When z >= 2.0, it means game FINISHED way over prediction
- In a live betting scenario, we would have bet DURING the game
- Since we don't have intra-game data, we can't truly backtest this
- BUT we can estimate: games with high z-scores are those that DIDN'T regress
- So high z-score games would have been LOSING bets
- Low z-score games (close to prediction) would have been winning bets

CORRECT INTERPRETATION:
-----------------------
For a true backtest, we need to think about it differently:
- Z-score >= 2.0 means the game had EXTREME momentum that DID NOT REGRESS
- These would have been losing bets (we bet against momentum, momentum continued)
- Z-score between 0.5-1.5 means moderate deviation that DID REGRESS somewhat
- These would have been winning bets

So the backtest should identify:
1. Games that HAD extreme momentum at some point (simulated)
2. Check if they regressed by game end
3. Calculate wins/losses based on regression amount

NEW APPROACH:
-------------
Simulate "mid-game score" at 70% of game completion:
- Mid-game total = 0.7 * actual + 0.3 * predicted
- Calculate z-score at mid-game
- If |z| >= 2.0 at mid-game, trigger alert
- Bet on regression: final will be closer to predicted
- Win if: |actual - predicted| < |midgame - predicted|
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from datetime import datetime
import os

class NBARegressionBacktestV2:
    """Backtest with realistic simulation of mid-game alerts and regression betting"""

    def __init__(self):
        self.data_path = "C:/Users/nashr/backend/data/historical/nba/nba_historical_latest.csv"
        self.model_dir = "C:/Users/nashr/backend/ml/models/"
        self.results_dir = "C:/Users/nashr/backend/data/backtesting/"
        os.makedirs(self.results_dir, exist_ok=True)

        # Simulation parameters
        self.midgame_point = 0.75  # Trigger alerts at 75% of game (end of 3rd quarter)
        self.momentum_weight = 0.85  # How much actual vs predicted influences mid-game score
        self.z_threshold_medium = 2.0
        self.z_threshold_high = 2.5

        # Betting parameters
        self.risk_amount = 110
        self.win_amount = 100

    def load_models(self):
        """Load the three trained XGBoost models"""
        print("="*70)
        print("LOADING XGBOOST MODELS")
        print("="*70)

        models = {}
        for model_type in ['lower', 'mean', 'upper']:
            model_path = f"{self.model_dir}nba_quantile_{model_type}_latest.json"
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model not found: {model_path}")
            model = xgb.Booster()
            model.load_model(model_path)
            models[model_type] = model
            file_size = os.path.getsize(model_path) / 1024
            print(f"[OK] Loaded {model_type} model: {file_size:.1f} KB")

        print(f"\n[SUCCESS] All 3 models loaded")
        return models

    def load_data(self):
        """Load NBA historical data"""
        print(f"\n{'='*70}")
        print("LOADING NBA HISTORICAL DATA")
        print("="*70)
        df = pd.read_csv(self.data_path)
        print(f"[OK] Loaded {len(df)} games")
        print(f"[OK] Date range: {df['game_date'].min()} to {df['game_date'].max()}")
        print(f"[OK] Average total: {df['actual_total'].mean():.1f} points")
        return df

    def prepare_features(self, df):
        """Prepare features exactly as done during training"""
        exclude_cols = [
            'actual_total', 'game_id', 'season', 'game_date',
            'home_team', 'away_team', 'home_score', 'away_score'
        ]
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        feature_cols = [col for col in feature_cols if df[col].dtype in ['int64', 'float64']]
        X = df[feature_cols].copy()
        X = X.fillna(X.mean())
        print(f"\n[FEATURES] Using {len(feature_cols)} features")
        return X, feature_cols

    def make_predictions(self, models, X):
        """Make predictions with all three models"""
        print(f"\n{'='*70}")
        print("GENERATING PREDICTIONS")
        print("="*70)
        dmatrix = xgb.DMatrix(X)
        predictions = {}
        for model_type, model in models.items():
            predictions[model_type] = model.predict(dmatrix)
            print(f"[OK] {model_type.upper()}: {len(predictions[model_type])} predictions")
        return predictions

    def simulate_midgame_alerts(self, df, predictions):
        """Simulate mid-game alerts and regression betting"""
        print(f"\n{'='*70}")
        print("SIMULATING MID-GAME ALERTS AND REGRESSION BETTING")
        print("="*70)

        results = df[['game_id', 'season', 'game_date', 'home_team', 'away_team',
                      'actual_total', 'home_score', 'away_score']].copy()

        # Add predictions
        results['pred_lower'] = predictions['lower']
        results['pred_mean'] = predictions['mean']
        results['pred_upper'] = predictions['upper']
        results['pred_std'] = (results['pred_upper'] - results['pred_lower']) / 2.56

        # Simulate mid-game score (at 75% of game completion, end of Q3)
        # If game ended OVER prediction, it was trending OVER during Q3
        # If game ended UNDER prediction, it was trending UNDER during Q3
        # Mid-game score is weighted average, leaning heavily toward actual
        results['midgame_total'] = (
            self.momentum_weight * results['actual_total'] +
            (1 - self.momentum_weight) * results['pred_mean']
        )

        # Calculate z-score at mid-game
        results['midgame_zscore'] = (
            (results['midgame_total'] - results['pred_mean']) / results['pred_std']
        )
        results['abs_midgame_zscore'] = np.abs(results['midgame_zscore'])

        # Trigger alert if |z| >= 2.0 at mid-game
        results['is_alert'] = results['abs_midgame_zscore'] >= self.z_threshold_medium

        # Confidence level
        results['confidence'] = results['abs_midgame_zscore'].apply(
            lambda z: 'HIGH' if z >= self.z_threshold_high else
                     'MEDIUM' if z >= self.z_threshold_medium else 'NONE'
        )

        # Bet direction: opposite of momentum
        # If midgame trending OVER (z > 0), bet UNDER
        # If midgame trending UNDER (z < 0), bet OVER
        results['bet_direction'] = np.where(
            results['midgame_zscore'] >= self.z_threshold_medium, 'UNDER',
            np.where(results['midgame_zscore'] <= -self.z_threshold_medium, 'OVER', 'NONE')
        )

        # Simulated live line = midgame total (what line would be based on momentum)
        results['live_line'] = results['midgame_total']

        # Bet outcome: Did regression happen?
        # UNDER bet wins if actual < live_line (regression from high trend)
        # OVER bet wins if actual > live_line (regression from low trend)
        results['bet_wins'] = np.where(
            results['bet_direction'] == 'UNDER',
            results['actual_total'] < results['live_line'],
            np.where(
                results['bet_direction'] == 'OVER',
                results['actual_total'] > results['live_line'],
                False
            )
        )

        # Calculate profit/loss
        results['pnl'] = np.where(
            results['is_alert'],
            np.where(results['bet_wins'], self.win_amount, -self.risk_amount),
            0
        )

        alerts = results[results['is_alert']].copy()
        print(f"[OK] Total games analyzed: {len(results)}")
        print(f"[OK] Mid-game alerts found: {len(alerts)}")
        print(f"[OK] Alert rate: {len(alerts)/len(results)*100:.1f}%")

        return results, alerts

    def analyze_results(self, alerts):
        """Calculate comprehensive performance metrics"""
        print(f"\n{'='*70}")
        print("BACKTEST RESULTS")
        print("="*70)

        if len(alerts) == 0:
            print("[WARNING] No alerts found!")
            return {}

        total_alerts = len(alerts)
        total_wins = alerts['bet_wins'].sum()
        total_losses = total_alerts - total_wins
        win_rate = (total_wins / total_alerts * 100) if total_alerts > 0 else 0
        total_pnl = alerts['pnl'].sum()
        total_risked = total_alerts * self.risk_amount
        roi = (total_pnl / total_risked * 100) if total_risked > 0 else 0

        print(f"\nOVERALL PERFORMANCE:")
        print(f"  Total Alerts: {total_alerts}")
        print(f"  Wins: {total_wins}")
        print(f"  Losses: {total_losses}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Total P&L: ${total_pnl:+,.0f}")
        print(f"  Total Risked: ${total_risked:,.0f}")
        print(f"  ROI: {roi:+.1f}%")

        # Breakdown by confidence
        print(f"\nBY CONFIDENCE LEVEL:")
        for conf in ['HIGH', 'MEDIUM']:
            conf_alerts = alerts[alerts['confidence'] == conf]
            if len(conf_alerts) == 0:
                continue
            conf_wins = conf_alerts['bet_wins'].sum()
            conf_total = len(conf_alerts)
            conf_win_rate = (conf_wins / conf_total * 100) if conf_total > 0 else 0
            conf_pnl = conf_alerts['pnl'].sum()
            conf_risked = conf_total * self.risk_amount
            conf_roi = (conf_pnl / conf_risked * 100) if conf_risked > 0 else 0
            print(f"\n  {conf}:")
            print(f"    Alerts: {conf_total}")
            print(f"    Wins: {conf_wins}")
            print(f"    Win Rate: {conf_win_rate:.1f}%")
            print(f"    P&L: ${conf_pnl:+,.0f}")
            print(f"    ROI: {conf_roi:+.1f}%")

        # Breakdown by direction
        print(f"\nBY BET DIRECTION:")
        for direction in ['OVER', 'UNDER']:
            dir_alerts = alerts[alerts['bet_direction'] == direction]
            if len(dir_alerts) == 0:
                continue
            dir_wins = dir_alerts['bet_wins'].sum()
            dir_total = len(dir_alerts)
            dir_win_rate = (dir_wins / dir_total * 100) if dir_total > 0 else 0
            dir_pnl = dir_alerts['pnl'].sum()
            print(f"\n  {direction} bets:")
            print(f"    Count: {dir_total}")
            print(f"    Wins: {dir_wins}")
            print(f"    Win Rate: {dir_win_rate:.1f}%")
            print(f"    P&L: ${dir_pnl:+,.0f}")

        metrics = {
            'total_alerts': total_alerts,
            'wins': total_wins,
            'losses': total_losses,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'roi': roi
        }

        return metrics

    def show_sample_alerts(self, alerts, n=10):
        """Display sample regression opportunities"""
        print(f"\n{'='*70}")
        print(f"SAMPLE ALERTS (showing {n} examples)")
        print("="*70)

        sample = alerts.nlargest(n, 'abs_midgame_zscore')[
            ['game_date', 'home_team', 'away_team', 'pred_mean', 'midgame_total',
             'actual_total', 'midgame_zscore', 'confidence', 'bet_direction',
             'live_line', 'bet_wins', 'pnl']
        ].copy()

        for idx, row in sample.iterrows():
            print(f"\n{row['game_date']} - {row['away_team']} @ {row['home_team']}")
            print(f"  Predicted Total: {row['pred_mean']:.1f}")
            print(f"  Mid-game Total (Q3): {row['midgame_total']:.1f}")
            print(f"  Mid-game Z-Score: {row['midgame_zscore']:+.2f} ({row['confidence']})")
            print(f"  Live Line: {row['live_line']:.1f}")
            print(f"  Bet: {row['bet_direction']} {row['live_line']:.1f}")
            print(f"  Actual Final: {row['actual_total']:.0f}")
            regression_amount = row['midgame_total'] - row['actual_total']
            print(f"  Regression: {regression_amount:+.1f} pts")
            print(f"  Result: {'WIN' if row['bet_wins'] else 'LOSS'} (${row['pnl']:+.0f})")

    def save_results(self, results, alerts, metrics):
        """Save backtest results to CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        results_file = f"{self.results_dir}nba_regression_v2_full_{timestamp}.csv"
        results.to_csv(results_file, index=False)
        print(f"\n[SAVED] Full results: {results_file}")

        alerts_file = f"{self.results_dir}nba_regression_v2_alerts_{timestamp}.csv"
        alerts.to_csv(alerts_file, index=False)
        print(f"[SAVED] Alerts only: {alerts_file}")

        summary_file = f"{self.results_dir}nba_regression_v2_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("NBA REGRESSION-TO-MEAN STRATEGY BACKTEST V2 SUMMARY\n")
            f.write("="*70 + "\n\n")
            f.write(f"Backtest Date: {timestamp}\n")
            f.write(f"Total Games: {len(results)}\n")
            f.write(f"Total Alerts: {metrics.get('total_alerts', 0)}\n")
            f.write(f"Win Rate: {metrics.get('win_rate', 0):.1f}%\n")
            f.write(f"Total P&L: ${metrics.get('total_pnl', 0):+,.0f}\n")
            f.write(f"ROI: {metrics.get('roi', 0):+.1f}%\n")

        print(f"[SAVED] Summary: {summary_file}")
        return results_file, alerts_file, summary_file

    def run(self):
        """Execute complete backtest"""
        print("\n" + "="*70)
        print("NBA REGRESSION-TO-MEAN STRATEGY BACKTEST V2")
        print("="*70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        models = self.load_models()
        df = self.load_data()
        X, feature_cols = self.prepare_features(df)
        predictions = self.make_predictions(models, X)
        results, alerts = self.simulate_midgame_alerts(df, predictions)
        metrics = self.analyze_results(alerts)

        if len(alerts) > 0:
            self.show_sample_alerts(alerts, n=10)

        results_file, alerts_file, summary_file = self.save_results(results, alerts, metrics)

        print(f"\n{'='*70}")
        print("[COMPLETE] Backtest finished successfully!")
        print("="*70)
        print(f"\nOutput files:")
        print(f"  1. {results_file}")
        print(f"  2. {alerts_file}")
        print(f"  3. {summary_file}")
        print()

        return results, alerts, metrics


if __name__ == "__main__":
    backtest = NBARegressionBacktestV2()
    results, alerts, metrics = backtest.run()
