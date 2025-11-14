"""
Weekly Model Retraining System
Retrains all 28 player props models with latest results

Runs: Sunday 3am CST (weekly)
Duration: ~20-30 minutes

Models retrained:
- 7 prop types (points, rebounds, assists, threes, blocks, steals, PRA)
- 4 algorithms each (XGBoost, LightGBM, Random Forest, Linear)
- Total: 28 models
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WeeklyModelRetrainer:
    """
    Retrains all player props models with latest data
    """

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.trainer_script = self.base_dir / "nba_props_trainer_enhanced.py"
        self.prop_types = ['points', 'rebounds', 'assists', 'threes', 'blocks', 'steals', 'PRA']
        self.results = {}

    def retrain_single_prop(self, prop_type: str) -> bool:
        """
        Retrain all models for a single prop type
        """
        logger.info(f"Retraining {prop_type} models...")

        try:
            result = subprocess.run(
                [sys.executable, str(self.trainer_script), '--prop-type', prop_type, '--min-samples', '100'],
                capture_output=True,
                text=True,
                timeout=900,  # 15 minutes per prop type
                cwd=self.base_dir
            )

            if result.returncode == 0:
                logger.info(f"✓ {prop_type} models trained successfully")
                return True
            else:
                logger.error(f"✗ {prop_type} training failed")
                logger.error(f"Error: {result.stderr[:500]}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"✗ {prop_type} training timed out")
            return False
        except Exception as e:
            logger.error(f"✗ {prop_type} error: {str(e)}")
            return False

    def retrain_all_models(self):
        """
        Retrain all 28 models sequentially
        """
        logger.info("="*70)
        logger.info("WEEKLY MODEL RETRAINING - STARTING")
        logger.info("="*70)
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        logger.info(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"Prop types: {len(self.prop_types)}")
        logger.info(f"Total models: {len(self.prop_types) * 4}")
        logger.info("")

        start_time = datetime.now()

        for i, prop_type in enumerate(self.prop_types, 1):
            logger.info(f"[{i}/{len(self.prop_types)}] Processing {prop_type}...")
            success = self.retrain_single_prop(prop_type)
            self.results[prop_type] = success

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60

        # Summary
        success_count = sum(1 for r in self.results.values() if r)

        logger.info("")
        logger.info("="*70)
        logger.info("WEEKLY RETRAINING COMPLETE")
        logger.info("="*70)
        logger.info(f"Duration: {duration:.1f} minutes")
        logger.info(f"Success: {success_count}/{len(self.prop_types)}")
        logger.info("")

        for prop_type, success in self.results.items():
            status = "✓" if success else "✗"
            logger.info(f"{status} {prop_type}")

        logger.info("="*70)

        return success_count == len(self.prop_types)


def main():
    """Main entry point"""
    retrainer = WeeklyModelRetrainer()
    success = retrainer.retrain_all_models()

    if success:
        logger.info("[SUCCESS] All models retrained successfully!")
        sys.exit(0)
    else:
        logger.error("[FAILED] Some models failed to retrain")
        sys.exit(1)


if __name__ == "__main__":
    main()
