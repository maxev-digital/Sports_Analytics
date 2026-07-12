#!/usr/bin/env python3
"""
Pipeline cron entry point.
Usage:
  python run_pipeline.py              # daily rule-based run
  python run_pipeline.py --use-ml     # with trained ML models
  python run_pipeline.py --weekly-audit  # trigger Opus weekly deep audit
"""

import sys
import os
import logging
import argparse

# Add backend root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/var/log/maxev_pipeline.log", mode="a"),
    ],
)
logger = logging.getLogger("run_pipeline")


def main():
    parser = argparse.ArgumentParser(description="MAX-EV Pipeline Runner")
    parser.add_argument("--use-ml", action="store_true", help="Use trained ML models")
    parser.add_argument("--weekly-audit", action="store_true", help="Run Opus weekly deep audit")
    args = parser.parse_args()

    if args.weekly_audit:
        logger.info("Starting Opus weekly deep audit...")
        try:
            from pipeline.db.connection import execute_query
            from pipeline.agents.opus_reflector import weekly_deep_audit, save_reflection_report

            week_picks   = execute_query(
                "SELECT * FROM predictions WHERE created_at_cst >= now() - INTERVAL '7 days'"
            )
            week_results = execute_query(
                "SELECT * FROM predictions WHERE status='graded' AND created_at_cst >= now() - INTERVAL '7 days'"
            )
            perf_history = execute_query(
                "SELECT * FROM model_performance ORDER BY computed_at_cst DESC LIMIT 50"
            )

            audit = weekly_deep_audit(week_picks, week_results, perf_history)
            save_reflection_report(audit, "weekly")
            logger.info(f"Weekly audit complete: {audit.get('methodology_assessment', '')[:100]}")
        except Exception as e:
            logger.error(f"Weekly audit failed: {e}")
        return

    logger.info(f"Starting daily pipeline (use_ml={args.use_ml})...")
    try:
        from pipeline.orchestrator import run_daily_pipeline
        result = run_daily_pipeline(use_ml=args.use_ml)
        logger.info(f"Pipeline complete: picks_saved={result.get('picks_saved')}, "
                    f"health={result.get('reflection_health')}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
