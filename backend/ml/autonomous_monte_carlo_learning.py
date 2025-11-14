"""
Autonomous Monte Carlo Simulation Learning System
CREATED: 2025-11-09

Automatically calibrates Monte Carlo variance parameters based on live betting results.

WHAT IT DOES:
1. Monitors all live games automatically
2. Runs Monte Carlo simulations (tracks predictions)
3. Compares simulated probabilities vs actual final scores
4. Retrains variance parameters weekly for better accuracy
5. Auto-deploys improved parameters

CALIBRATION PARAMETERS:
- PACE_VARIANCE: How much pace varies per possession
- EFFICIENCY_VARIANCE: How much scoring efficiency varies
- These control simulation spread/accuracy

Run weekly via cron:
    0 6 * * 1 cd /root/sporttrader/backend && source venv/bin/activate && python3 ml/autonomous_monte_carlo_learning.py --sport nba
"""

import sys
import os
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
from scipy import stats, optimize

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
        logging.FileHandler(log_dir / f'autonomous_monte_carlo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutonomousMonteCarloLearning:
    """Manages autonomous learning for Monte Carlo simulations"""

    def __init__(self, sport: str):
        self.sport = sport.lower()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Paths
        project_root = Path(__file__).parent.parent.parent
        self.tracking_dir = project_root / "backend" / "data" / "tracking" / "monte_carlo"
        self.tracking_dir.mkdir(parents=True, exist_ok=True)

        self.simulations_log = self.tracking_dir / f"{sport}_simulations_log.csv"
        self.results_log = self.tracking_dir / f"{sport}_simulation_results.csv"
        self.params_file = project_root / "backend" / "simulation" / f"{sport}_monte_carlo_params.json"
        self.backup_dir = project_root / "backend" / "simulation" / "backups" / self.timestamp
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 80)
        logger.info(f"AUTONOMOUS MONTE CARLO LEARNING - {sport.upper()}")
        logger.info(f"Timestamp: {self.timestamp}")
        logger.info("=" * 80)

    def collect_simulation_results(self) -> pd.DataFrame:
        """
        Collect results for Monte Carlo simulations from past week

        Returns:
            DataFrame with simulation predictions vs actual outcomes
        """
        logger.info("Step 1: Collecting simulation results...")

        if not self.simulations_log.exists():
            logger.warning("No simulations log found - first run")
            return pd.DataFrame()

        simulations = pd.read_csv(self.simulations_log)

        # Get simulations from past 7 days
        cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        recent_sims = simulations[simulations['game_date'] >= cutoff_date]

        logger.info(f"Found {len(recent_sims)} simulations from past 7 days")

        # Fetch actual final scores
        actual_results = self._fetch_actual_scores(recent_sims)

        if actual_results.empty:
            logger.warning("No actual results found")
            return pd.DataFrame()

        # Merge simulations with actual outcomes
        merged = recent_sims.merge(
            actual_results,
            on=['game_date', 'game_id'],
            how='left'
        )

        # Calculate calibration metrics
        merged['prediction_error'] = abs(merged['simulated_mean'] - merged['actual_total'])
        merged['within_1std'] = (
            (merged['actual_total'] >= merged['simulated_mean'] - merged['simulated_std']) &
            (merged['actual_total'] <= merged['simulated_mean'] + merged['simulated_std'])
        )
        merged['within_2std'] = (
            (merged['actual_total'] >= merged['simulated_mean'] - 2*merged['simulated_std']) &
            (merged['actual_total'] <= merged['simulated_mean'] + 2*merged['simulated_std'])
        )

        # Save results
        if self.results_log.exists():
            existing = pd.read_csv(self.results_log)
            merged = pd.concat([existing, merged], ignore_index=True).drop_duplicates('simulation_id')

        merged.to_csv(self.results_log, index=False)
        logger.info(f"Saved {len(merged)} simulation results")

        return merged

    def _fetch_actual_scores(self, simulations: pd.DataFrame) -> pd.DataFrame:
        """Fetch actual game scores"""
        logger.info("Fetching actual scores...")

        if self.sport == 'nba':
            from scrapers.nba.game_results_scraper import fetch_nba_results
            results = fetch_nba_results(simulations['game_date'].unique())
        elif self.sport == 'ncaab':
            from scrapers.ncaab.game_results_scraper_espn import fetch_ncaab_results
            results = fetch_ncaab_results(simulations['game_date'].unique())
        else:
            return pd.DataFrame()

        # Format for matching
        results['game_id'] = results['prediction_id']
        results = results[['game_date', 'game_id', 'actual_total']]

        return results

    def evaluate_current_parameters(self) -> Dict[str, float]:
        """Evaluate current Monte Carlo variance parameters"""
        logger.info("Step 2: Evaluating current parameters...")

        results = pd.read_csv(self.results_log)

        # Last 30 days performance
        cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        recent = results[results['game_date'] >= cutoff]

        if len(recent) == 0:
            logger.warning("No recent results to evaluate")
            return {
                'mae': 999.0,
                'calibration_1std': 0.0,
                'calibration_2std': 0.0,
                'total_simulations': 0
            }

        metrics = {
            'mae': recent['prediction_error'].mean(),
            'calibration_1std': recent['within_1std'].mean(),  # Should be ~68%
            'calibration_2std': recent['within_2std'].mean(),  # Should be ~95%
            'total_simulations': len(recent),
            'current_pace_variance': self._load_current_params()['pace_variance'],
            'current_eff_variance': self._load_current_params()['efficiency_variance']
        }

        logger.info(f"Current Performance (last 30 days):")
        logger.info(f"  MAE: {metrics['mae']:.2f}")
        logger.info(f"  Calibration (1σ): {metrics['calibration_1std']:.1%} (target: 68%)")
        logger.info(f"  Calibration (2σ): {metrics['calibration_2std']:.1%} (target: 95%)")
        logger.info(f"  Total Simulations: {metrics['total_simulations']}")

        return metrics

    def _load_current_params(self) -> Dict[str, float]:
        """Load current Monte Carlo parameters"""
        if self.params_file.exists():
            with open(self.params_file, 'r') as f:
                return json.load(f)
        else:
            # Default parameters
            return {
                'pace_variance': 0.10,
                'efficiency_variance': 0.08
            }

    def optimize_parameters(self, current_metrics: Dict) -> Dict[str, float]:
        """
        Optimize variance parameters to minimize MAE and improve calibration

        Uses historical simulation data to find optimal variance parameters
        """
        logger.info("Step 3: Optimizing variance parameters...")

        results = pd.read_csv(self.results_log)

        # Use last 100 simulations for optimization
        recent = results.tail(100)

        if len(recent) < 20:
            logger.warning(f"Only {len(recent)} simulations - need at least 20")
            return self._load_current_params()

        def objective_function(params):
            """
            Objective: Minimize MAE while maintaining proper calibration

            Calibration penalties:
            - 1σ should contain ~68% of outcomes
            - 2σ should contain ~95% of outcomes
            """
            pace_var, eff_var = params

            # Simulate with these parameters
            predicted_stds = []
            for _, row in recent.iterrows():
                # Estimate std dev with these variance params
                estimated_std = self._estimate_std_with_params(
                    row['remaining_time'],
                    row['avg_pace'],
                    pace_var,
                    eff_var
                )
                predicted_stds.append(estimated_std)

            predicted_stds = np.array(predicted_stds)

            # Calculate calibration
            within_1std = (
                (recent['actual_total'] >= recent['simulated_mean'] - predicted_stds) &
                (recent['actual_total'] <= recent['simulated_mean'] + predicted_stds)
            ).mean()

            within_2std = (
                (recent['actual_total'] >= recent['simulated_mean'] - 2*predicted_stds) &
                (recent['actual_total'] <= recent['simulated_mean'] + 2*predicted_stds)
            ).mean()

            # Penalties for miscalibration
            calibration_penalty = (
                abs(within_1std - 0.68) * 10 +  # Target: 68%
                abs(within_2std - 0.95) * 10     # Target: 95%
            )

            # MAE (mean absolute error)
            mae = recent['prediction_error'].mean()

            return mae + calibration_penalty

        # Optimize
        current = self._load_current_params()
        initial_guess = [current['pace_variance'], current['efficiency_variance']]

        bounds = [(0.05, 0.20), (0.04, 0.15)]  # Reasonable ranges

        result = optimize.minimize(
            objective_function,
            initial_guess,
            method='L-BFGS-B',
            bounds=bounds
        )

        new_params = {
            'pace_variance': float(result.x[0]),
            'efficiency_variance': float(result.x[1]),
            'timestamp': self.timestamp,
            'mae_improvement': current_metrics['mae'] - result.fun,
            'optimization_score': float(result.fun)
        }

        logger.info(f"Optimized Parameters:")
        logger.info(f"  Pace Variance: {current['pace_variance']:.4f} → {new_params['pace_variance']:.4f}")
        logger.info(f"  Efficiency Variance: {current['efficiency_variance']:.4f} → {new_params['efficiency_variance']:.4f}")
        logger.info(f"  Expected MAE Improvement: {new_params['mae_improvement']:+.2f}")

        return new_params

    def _estimate_std_with_params(self, remaining_time: float, avg_pace: float,
                                   pace_var: float, eff_var: float) -> float:
        """Estimate standard deviation with given variance parameters"""
        remaining_poss = (avg_pace / 48.0) * remaining_time
        # Simple model: std grows with sqrt of remaining possessions
        return np.sqrt(remaining_poss) * (pace_var + eff_var) * 10

    def validate_new_parameters(self, new_params: Dict, current_metrics: Dict) -> bool:
        """Validate if new parameters are better"""
        logger.info("Step 4: Validating new parameters...")

        # Check if improvement is significant
        mae_improvement = new_params.get('mae_improvement', 0)

        if mae_improvement >= 0.5:  # At least 0.5 point improvement
            logger.info(f"✅ NEW PARAMETERS ARE BETTER - MAE improvement: {mae_improvement:+.2f}")
            return True
        else:
            logger.info(f"❌ NEW PARAMETERS NOT BETTER - MAE improvement: {mae_improvement:+.2f}")
            return False

    def deploy_new_parameters(self, new_params: Dict):
        """Deploy new Monte Carlo parameters"""
        logger.info("Step 5: Deploying new parameters...")

        # Backup current parameters
        current = self._load_current_params()
        backup_file = self.backup_dir / f"{self.sport}_monte_carlo_params.json"
        with open(backup_file, 'w') as f:
            json.dump(current, f, indent=2)
        logger.info(f"Backed up current parameters to: {backup_file}")

        # Save new parameters
        with open(self.params_file, 'w') as f:
            json.dump(new_params, f, indent=2)
        logger.info(f"Deployed new parameters to: {self.params_file}")

        logger.info("✅ Deployment complete")

    def run_full_pipeline(self):
        """Execute the complete autonomous learning pipeline"""
        try:
            logger.info(f"Starting autonomous Monte Carlo learning for {self.sport.upper()}...")

            # Step 1: Collect results
            results = self.collect_simulation_results()

            if results.empty:
                logger.warning("⚠️  No simulation results available - skipping optimization")
                return True

            # Step 2: Evaluate current parameters
            current_metrics = self.evaluate_current_parameters()

            if current_metrics['total_simulations'] < 20:
                logger.warning(f"⚠️  Only {current_metrics['total_simulations']} simulations - need at least 20")
                return True

            # Step 3: Optimize parameters
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
    parser = argparse.ArgumentParser(description='Autonomous Monte Carlo Learning System')
    parser.add_argument('--sport', required=True, choices=['nba', 'ncaab'],
                       help='Sport to optimize for')

    args = parser.parse_args()

    system = AutonomousMonteCarloLearning(sport=args.sport)
    success = system.run_full_pipeline()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
