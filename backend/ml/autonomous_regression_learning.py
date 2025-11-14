"""
Autonomous Regression to Mean Strategy Learning System
CREATED: 2025-11-09

Automatically optimizes regression-to-mean strategy parameters based on results.

WHAT IT OPTIMIZES:
- z_score_threshold: How many std devs to trigger alert (default: 2.0)
- min_edge: Minimum edge in points to bet (default: 3.0)
- min_confidence: Minimum model confidence to bet (default: 0.60)

THEORY:
Regression alerts work best when live totals have deviated far from model predictions.
But "how far" is optimal? This system learns from results to find the sweet spot.

Run weekly via cron:
    0 8 * * 1 cd /root/sporttrader/backend && source venv/bin/activate && python3 ml/autonomous_regression_learning.py --sport nba
"""

import sys
import os
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import argparse
from scipy import optimize

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

# Setup logging
project_root = Path(__file__).parent.parent.parent if Path(__file__).parent.parent.name == 'backend' else Path(__file__).parent.parent
log_dir = project_root / "backend" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'autonomous_regression_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutonomousRegressionLearning:
    """Manages autonomous learning for Regression to Mean strategy"""

    def __init__(self, sport: str):
        self.sport = sport.lower()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Paths
        project_root = Path(__file__).parent.parent.parent
        self.tracking_dir = project_root / "backend" / "data" / "tracking" / "regression"
        self.tracking_dir.mkdir(parents=True, exist_ok=True)

        self.alerts_log = self.tracking_dir / f"{sport}_regression_alerts.csv"
        self.results_log = self.tracking_dir / f"{sport}_regression_results.csv"
        self.params_file = project_root / "backend" / "strategies" / "regression_to_mean" / f"{sport}_params.json"
        self.backup_dir = project_root / "backend" / "strategies" / "regression_to_mean" / "backups" / self.timestamp
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 80)
        logger.info(f"AUTONOMOUS REGRESSION LEARNING - {sport.upper()}")
        logger.info(f"Timestamp: {self.timestamp}")
        logger.info("=" * 80)

    def collect_regression_results(self) -> pd.DataFrame:
        """Collect results for regression alerts from past week"""
        logger.info("Step 1: Collecting regression alert results...")

        if not self.alerts_log.exists():
            logger.warning("No alerts log found - first run")
            return pd.DataFrame()

        alerts = pd.read_csv(self.alerts_log)

        # Get alerts from past 7 days
        cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        recent_alerts = alerts[alerts['game_date'] >= cutoff_date]

        logger.info(f"Found {len(recent_alerts)} alerts from past 7 days")

        # Fetch actual final scores
        actual_results = self._fetch_actual_scores(recent_alerts)

        if actual_results.empty:
            logger.warning("No actual results found")
            return pd.DataFrame()

        # Merge
        merged = recent_alerts.merge(
            actual_results,
            on=['game_date', 'game_id'],
            how='left'
        )

        # Calculate if regression alert was correct
        merged['was_correct'] = (
            ((merged['recommendation'] == 'OVER') & (merged['actual_total'] > merged['live_total'])) |
            ((merged['recommendation'] == 'UNDER') & (merged['actual_total'] < merged['live_total']))
        )

        merged['profit'] = merged['was_correct'].apply(lambda x: 0.91 if x else -1.0)

        # Save results
        if self.results_log.exists():
            existing = pd.read_csv(self.results_log)
            merged = pd.concat([existing, merged], ignore_index=True).drop_duplicates('alert_id')

        merged.to_csv(self.results_log, index=False)
        logger.info(f"Saved {len(merged)} alert results")

        return merged

    def _fetch_actual_scores(self, alerts: pd.DataFrame) -> pd.DataFrame:
        """Fetch actual game scores"""
        logger.info("Fetching actual scores...")

        if self.sport == 'nba':
            from scrapers.nba.game_results_scraper import fetch_nba_results
            results = fetch_nba_results(alerts['game_date'].unique())
        elif self.sport == 'ncaab':
            from scrapers.ncaab.game_results_scraper_espn import fetch_ncaab_results
            results = fetch_ncaab_results(alerts['game_date'].unique())
        else:
            return pd.DataFrame()

        results['game_id'] = results['prediction_id']
        results = results[['game_date', 'game_id', 'actual_total']]

        return results

    def evaluate_current_parameters(self) -> Dict[str, float]:
        """Evaluate current strategy parameters"""
        logger.info("Step 2: Evaluating current parameters...")

        if not self.results_log.exists():
            logger.warning("No results to evaluate")
            return {'win_rate': 0.0, 'roi': 0.0, 'total_alerts': 0}

        results = pd.read_csv(self.results_log)

        # Last 30 days
        cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        recent = results[results['game_date'] >= cutoff]

        if len(recent) == 0:
            return {'win_rate': 0.0, 'roi': 0.0, 'total_alerts': 0}

        metrics = {
            'win_rate': recent['was_correct'].mean(),
            'roi': (recent['profit'].sum() / len(recent)) * 100,
            'total_alerts': len(recent),
            'avg_z_score': recent['z_score'].mean(),
            'avg_edge': recent['edge'].mean()
        }

        logger.info(f"Current Performance (last 30 days):")
        logger.info(f"  Win Rate: {metrics['win_rate']:.1%}")
        logger.info(f"  ROI: {metrics['roi']:+.1f}%")
        logger.info(f"  Total Alerts: {metrics['total_alerts']}")

        return metrics

    def optimize_parameters(self, current_metrics: Dict) -> Dict[str, float]:
        """Optimize strategy parameters"""
        logger.info("Step 3: Optimizing parameters...")

        if not self.results_log.exists():
            return self._load_current_params()

        results = pd.read_csv(self.results_log)

        if len(results) < 50:
            logger.warning(f"Only {len(results)} alerts - need at least 50 for optimization")
            return self._load_current_params()

        def objective_function(params):
            """
            Objective: Maximize ROI while maintaining reasonable alert frequency

            Returns: -ROI (since we're minimizing)
            """
            z_threshold, min_edge, min_confidence = params

            # Filter alerts that would pass these thresholds
            passed = results[
                (results['z_score'].abs() >= z_threshold) &
                (results['edge'].abs() >= min_edge) &
                (results['confidence'] >= min_confidence)
            ]

            if len(passed) < 10:  # Need minimum alerts
                return 100.0  # Penalize

            # Calculate ROI
            roi = (passed['profit'].sum() / len(passed)) * 100

            # Penalty for too few alerts (want reasonable frequency)
            alert_frequency_penalty = max(0, (30 - len(passed)) * 0.5)

            return -roi + alert_frequency_penalty  # Minimize (maximize ROI)

        # Optimize
        current = self._load_current_params()
        initial_guess = [
            current.get('z_score_threshold', 2.0),
            current.get('min_edge', 3.0),
            current.get('min_confidence', 0.60)
        ]

        bounds = [(1.5, 3.0), (2.0, 5.0), (0.50, 0.75)]

        result = optimize.minimize(
            objective_function,
            initial_guess,
            method='L-BFGS-B',
            bounds=bounds
        )

        new_params = {
            'z_score_threshold': float(result.x[0]),
            'min_edge': float(result.x[1]),
            'min_confidence': float(result.x[2]),
            'timestamp': self.timestamp,
            'expected_roi': float(-result.fun)
        }

        logger.info(f"Optimized Parameters:")
        logger.info(f"  Z-Score Threshold: {current.get('z_score_threshold', 2.0):.2f} → {new_params['z_score_threshold']:.2f}")
        logger.info(f"  Min Edge: {current.get('min_edge', 3.0):.1f} → {new_params['min_edge']:.1f}")
        logger.info(f"  Min Confidence: {current.get('min_confidence', 0.60):.2f} → {new_params['min_confidence']:.2f}")
        logger.info(f"  Expected ROI: {new_params['expected_roi']:.1f}%")

        return new_params

    def _load_current_params(self) -> Dict[str, float]:
        """Load current parameters"""
        if self.params_file.exists():
            with open(self.params_file, 'r') as f:
                return json.load(f)
        else:
            return {
                'z_score_threshold': 2.0,
                'min_edge': 3.0,
                'min_confidence': 0.60
            }

    def validate_new_parameters(self, new_params: Dict, current_metrics: Dict) -> bool:
        """Validate if new parameters are better"""
        logger.info("Step 4: Validating new parameters...")

        current_roi = current_metrics.get('roi', 0.0)
        expected_roi = new_params.get('expected_roi', 0.0)

        improvement = expected_roi - current_roi

        if improvement >= 2.0:  # At least 2% ROI improvement
            logger.info(f"✅ NEW PARAMETERS ARE BETTER - ROI improvement: {improvement:+.1f}%")
            return True
        else:
            logger.info(f"❌ NEW PARAMETERS NOT BETTER - ROI improvement: {improvement:+.1f}%")
            return False

    def deploy_new_parameters(self, new_params: Dict):
        """Deploy new parameters"""
        logger.info("Step 5: Deploying new parameters...")

        # Backup current
        current = self._load_current_params()
        backup_file = self.backup_dir / f"{self.sport}_params.json"
        with open(backup_file, 'w') as f:
            json.dump(current, f, indent=2)
        logger.info(f"Backed up current parameters to: {backup_file}")

        # Save new
        with open(self.params_file, 'w') as f:
            json.dump(new_params, f, indent=2)
        logger.info(f"Deployed new parameters to: {self.params_file}")

        logger.info("✅ Deployment complete")

    def run_full_pipeline(self):
        """Execute the complete autonomous learning pipeline"""
        try:
            logger.info(f"Starting autonomous regression learning for {self.sport.upper()}...")

            # Step 1: Collect results
            results = self.collect_regression_results()

            if results.empty:
                logger.warning("⚠️  No results available - skipping optimization")
                return True

            # Step 2: Evaluate current
            current_metrics = self.evaluate_current_parameters()

            if current_metrics['total_alerts'] < 50:
                logger.warning(f"⚠️  Only {current_metrics['total_alerts']} alerts - need at least 50")
                return True

            # Step 3: Optimize
            new_params = self.optimize_parameters(current_metrics)

            # Step 4: Validate
            should_deploy = self.validate_new_parameters(new_params, current_metrics)

            # Step 5: Deploy if better
            if should_deploy:
                self.deploy_new_parameters(new_params)
                logger.info("✅ Pipeline completed - NEW PARAMETERS DEPLOYED")
            else:
                logger.info("✅ Pipeline completed - KEEPING CURRENT PARAMETERS")

            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return False


def main():
    parser = argparse.ArgumentParser(description='Autonomous Regression Learning System')
    parser.add_argument('--sport', required=True, choices=['nba', 'ncaab'],
                       help='Sport to optimize for')

    args = parser.parse_args()

    system = AutonomousRegressionLearning(sport=args.sport)
    success = system.run_full_pipeline()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
