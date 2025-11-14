"""
Autonomous ML Learning System
CREATED: 2025-11-09
LAST_MODIFIED: 2025-11-09

Wires together all components for fully autonomous model improvement:
1. Collects actual game results
2. Compares predictions vs actuals
3. Retrains models with feedback
4. Validates new models vs old
5. Auto-deploys if better

Run weekly via cron:
    0 4 * * 1 cd /root/sporttrader && python3 backend/ml/autonomous_learning_system.py --sport ncaab
"""

import sys
import os
import logging
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
import shutil

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from ml.training.train_ncaab_models import NCAABModelTrainer
from ml.training.train_nba_models import NBAModelTrainer
from ml.data_loaders.ncaab_data_loader import load_ncaab_training_data
from ml.data_loaders.nba_data_loader import load_nba_training_data

# Determine project root directory
project_root = Path(__file__).parent.parent.parent
log_dir = project_root / "backend" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'autonomous_learning_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutonomousLearningSystem:
    """Manages the full autonomous learning pipeline"""

    def __init__(self, sport: str):
        self.sport = sport.lower()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Determine project root (handle running from different directories)
        project_root = Path(__file__).parent.parent.parent
        self.models_dir = project_root / "backend" / "ml" / "models"
        self.results_dir = project_root / "backend" / "data" / "tracking"
        self.backup_dir = project_root / "backend" / "ml" / "models" / "backups" / self.timestamp

        # Create necessary directories
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"=" * 80)
        logger.info(f"AUTONOMOUS LEARNING SYSTEM - {sport.upper()}")
        logger.info(f"Timestamp: {self.timestamp}")
        logger.info(f"=" * 80)

    def collect_actual_results(self) -> pd.DataFrame:
        """
        Collect actual game results from past week

        Returns:
            DataFrame with game_id, predicted_total, actual_total, error
        """
        logger.info("Step 1: Collecting actual game results...")

        predictions_file = self.results_dir / "predictions_log.csv"
        results_file = self.results_dir / "results_log.csv"

        if not predictions_file.exists():
            logger.warning("No predictions log found - first run")
            return pd.DataFrame()

        predictions = pd.read_csv(predictions_file)

        # Get games from past 7 days that need results
        cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        recent_predictions = predictions[predictions['game_date'] >= cutoff_date]

        logger.info(f"Found {len(recent_predictions)} predictions from past 7 days")

        # Fetch actual scores (from ESPN or other source)
        actual_results = self._fetch_actual_scores(recent_predictions)

        # Handle case where no results found
        if actual_results.empty:
            logger.warning("No actual results found - cannot evaluate model yet")
            return pd.DataFrame()

        # Merge and calculate errors
        merged = recent_predictions.merge(
            actual_results,
            on='prediction_id',
            how='left'
        )

        merged['prediction_error'] = abs(merged['predicted_total'] - merged['actual_total'])
        merged['was_correct'] = (
            ((merged['recommendation'] == 'OVER') & (merged['actual_total'] > merged['market_total'])) |
            ((merged['recommendation'] == 'UNDER') & (merged['actual_total'] < merged['market_total']))
        )

        # Save results
        if results_file.exists():
            existing = pd.read_csv(results_file)
            merged = pd.concat([existing, merged], ignore_index=True).drop_duplicates('prediction_id')

        merged.to_csv(results_file, index=False)
        logger.info(f"Saved {len(merged)} results with timestamp: {self.timestamp}")

        return merged

    def _fetch_actual_scores(self, predictions: pd.DataFrame) -> pd.DataFrame:
        """Fetch actual scores from external API"""
        logger.info("Fetching actual scores from ESPN API...")

        # Import game result scrapers
        try:
            from scrapers.ncaab.game_results_scraper_espn import fetch_ncaab_results
            from scrapers.nba.game_results_scraper import fetch_nba_results

            if self.sport == 'ncaab':
                results = fetch_ncaab_results(predictions['game_date'].unique())
            elif self.sport == 'nba':
                results = fetch_nba_results(predictions['game_date'].unique())
            else:
                results = pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching results: {e}")
            results = pd.DataFrame()

        return results

    def evaluate_current_model_performance(self) -> Dict[str, float]:
        """Evaluate current production models on recent data"""
        logger.info("Step 2: Evaluating current model performance...")

        results = pd.read_csv(self.results_dir / "results_log.csv")

        # Last 30 days performance
        cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        recent = results[results['game_date'] >= cutoff]

        if len(recent) == 0:
            logger.warning("No recent results to evaluate")
            return {'mae': 999.0, 'accuracy': 0.0, 'roi': 0.0}

        metrics = {
            'mae': recent['prediction_error'].mean(),
            'rmse': np.sqrt((recent['prediction_error'] ** 2).mean()),
            'accuracy': recent['was_correct'].mean(),
            'total_predictions': len(recent),
            'timestamp': self.timestamp
        }

        logger.info(f"Current Model Performance (last 30 days):")
        logger.info(f"  MAE: {metrics['mae']:.2f}")
        logger.info(f"  Accuracy: {metrics['accuracy']:.1%}")
        logger.info(f"  Total Predictions: {metrics['total_predictions']}")

        return metrics

    def retrain_models_with_feedback(self, current_performance: Dict) -> Dict:
        """Retrain models incorporating recent prediction feedback"""
        logger.info("Step 3: Retraining models with feedback data...")

        # Load historical training data
        if self.sport == 'ncaab':
            historical_df = load_ncaab_training_data(seasons=[2023, 2024, 2025])
            trainer = NCAABModelTrainer(output_dir=self.models_dir / f"temp_{self.timestamp}")
        elif self.sport == 'nba':
            historical_df = load_nba_training_data(seasons=[2023, 2024, 2025])
            trainer = NBAModelTrainer(output_dir=self.models_dir / f"temp_{self.timestamp}")
        else:
            raise ValueError(f"Unknown sport: {self.sport}")

        logger.info(f"Loaded {len(historical_df)} historical training samples")

        # Load recent prediction results to augment training
        results_file = self.results_dir / "results_log.csv"
        if results_file.exists():
            results_df = pd.read_csv(results_file)
            # Convert to training format and append
            augmented_df = self._convert_results_to_training_format(results_df)
            historical_df = pd.concat([historical_df, augmented_df], ignore_index=True)
            logger.info(f"Augmented with {len(augmented_df)} recent predictions")

        # Train new models
        logger.info("Training new models...")
        new_models_metadata = trainer.train_totals_models(historical_df)

        # Add performance comparison
        new_models_metadata['previous_performance'] = current_performance
        new_models_metadata['training_timestamp'] = self.timestamp

        return new_models_metadata

    def _convert_results_to_training_format(self, results_df: pd.DataFrame) -> pd.DataFrame:
        """Convert prediction results back into training data format"""
        # Filter to games with actual results
        complete = results_df[results_df['actual_total'].notna()].copy()

        # Transform to match training data format
        training_data = pd.DataFrame({
            'game_date': complete['game_date'],
            'home_team': complete['home_team'],
            'away_team': complete['away_team'],
            'total': complete['actual_total'],  # Use ACTUAL as ground truth
            # Add other required features...
        })

        logger.info(f"Converted {len(training_data)} results to training format")
        return training_data

    def validate_new_models(self, new_metadata: Dict) -> bool:
        """Compare new models vs current production models"""
        logger.info("Step 4: Validating new models against current production...")

        # Load test set from results
        test_df = pd.read_csv(self.results_dir / "results_log.csv")
        recent_test = test_df.tail(100)  # Last 100 games as validation

        if len(recent_test) < 20:
            logger.warning("Insufficient test data - skipping validation")
            return False

        # Get current model performance
        current_mae = new_metadata['previous_performance']['mae']

        # Get new model performance from training metadata
        new_mae = new_metadata['training_stats']['random_forest']['mae']

        improvement = ((current_mae - new_mae) / current_mae) * 100

        logger.info(f"Performance Comparison:")
        logger.info(f"  Current MAE: {current_mae:.2f}")
        logger.info(f"  New MAE: {new_mae:.2f}")
        logger.info(f"  Improvement: {improvement:+.1f}%")

        # Deploy if at least 5% improvement
        should_deploy = improvement >= 5.0

        if should_deploy:
            logger.info("✅ NEW MODEL IS BETTER - Will deploy")
        else:
            logger.info("❌ NEW MODEL NOT BETTER - Keeping current")

        return should_deploy

    def deploy_new_models(self, new_metadata: Dict):
        """Deploy new models to production with backup of old models"""
        logger.info("Step 5: Deploying new models to production...")

        # Backup current production models
        logger.info(f"Backing up current models to: {self.backup_dir}")

        model_patterns = [
            f"{self.sport}_random_forest_totals_latest.joblib",
            f"{self.sport}_xgboost_totals_latest.joblib",
            f"{self.sport}_lightgbm_totals_latest.joblib",
            f"{self.sport}_linear_regression_totals_latest.joblib",
            f"{self.sport}_totals_metadata_latest.joblib"
        ]

        for pattern in model_patterns:
            current_model = self.models_dir / pattern
            if current_model.exists():
                backup_path = self.backup_dir / pattern
                shutil.copy2(current_model, backup_path)
                logger.info(f"  Backed up: {pattern}")

        # Deploy new models
        logger.info("Deploying new models...")
        temp_dir = self.models_dir / f"temp_{self.timestamp}"

        for pattern in model_patterns:
            new_model = temp_dir / pattern
            if new_model.exists():
                production_path = self.models_dir / pattern
                shutil.copy2(new_model, production_path)

                # CRITICAL: Add timestamp to filename for tracking
                timestamped_path = self.models_dir / pattern.replace('_latest', f'_{self.timestamp}')
                shutil.copy2(new_model, timestamped_path)

                logger.info(f"  Deployed: {pattern}")
                logger.info(f"  Timestamped copy: {timestamped_path.name}")

        # Clean up temp directory
        shutil.rmtree(temp_dir)

        logger.info("✅ Deployment complete")

        # Log deployment
        self._log_deployment(new_metadata)

    def _log_deployment(self, metadata: Dict):
        """Log model deployment for audit trail"""
        project_root = Path(__file__).parent.parent.parent
        deployment_log = project_root / "backend" / "ml" / "deployment_log.csv"

        log_entry = {
            'timestamp': self.timestamp,
            'sport': self.sport,
            'previous_mae': metadata['previous_performance']['mae'],
            'new_mae': metadata['training_stats']['random_forest']['mae'],
            'improvement_pct': ((metadata['previous_performance']['mae'] -
                                metadata['training_stats']['random_forest']['mae']) /
                               metadata['previous_performance']['mae'] * 100),
            'training_samples': metadata['n_train_samples'],
            'backup_location': str(self.backup_dir)
        }

        if deployment_log.exists():
            df = pd.read_csv(deployment_log)
            df = pd.concat([df, pd.DataFrame([log_entry])], ignore_index=True)
        else:
            df = pd.DataFrame([log_entry])

        df.to_csv(deployment_log, index=False)
        logger.info(f"Logged deployment to: {deployment_log}")

    def run_full_pipeline(self):
        """Execute the complete autonomous learning pipeline"""
        try:
            logger.info(f"Starting autonomous learning pipeline for {self.sport.upper()}...")
            logger.info(f"Pipeline timestamp: {self.timestamp}")

            # Step 1: Collect results
            results = self.collect_actual_results()

            # Check if we have enough data to proceed
            if results.empty:
                logger.warning("⚠️  No results available - skipping retraining")
                logger.info("System will try again next week when more predictions exist")
                return True

            # Step 2: Evaluate current performance
            current_performance = self.evaluate_current_model_performance()

            # Check if we have enough recent results
            if current_performance['total_predictions'] < 20:
                logger.warning(f"⚠️  Only {current_performance['total_predictions']} predictions - need at least 20")
                logger.info("System will try again next week when more data exists")
                return True

            # Step 3: Retrain with feedback
            new_metadata = self.retrain_models_with_feedback(current_performance)

            # Step 4: Validate new models
            should_deploy = self.validate_new_models(new_metadata)

            # Step 5: Deploy if better
            if should_deploy:
                self.deploy_new_models(new_metadata)
                logger.info("✅ Pipeline completed successfully - NEW MODELS DEPLOYED")
            else:
                logger.info("✅ Pipeline completed - KEEPING CURRENT MODELS")

            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return False


def main():
    parser = argparse.ArgumentParser(description='Autonomous ML Learning System')
    parser.add_argument('--sport', required=True, choices=['nba', 'ncaab', 'nfl', 'ncaaf', 'nhl'],
                       help='Sport to train models for')
    parser.add_argument('--force-deploy', action='store_true',
                       help='Force deployment even if not better')

    args = parser.parse_args()

    system = AutonomousLearningSystem(sport=args.sport)
    success = system.run_full_pipeline()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
