"""
One-time setup script — run this on the VPS to initialize the pipeline.
  python pipeline/setup_pipeline.py

Does:
1. Creates PostgreSQL schema (all tables)
2. Schedules daily cron jobs (10 AM and 12 PM CST)
3. Runs a quick sanity check on all connections
4. Performs first ingestion run (rule-based, no ML)
"""

import sys
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def setup_schema():
    logger.info("Setting up PostgreSQL schema...")
    from pipeline.db.schema import create_all_tables, get_engine
    engine = get_engine()
    create_all_tables(engine)
    logger.info("Schema created successfully")


def test_connections():
    logger.info("Testing connections...")
    errors = []

    # Test PostgreSQL
    try:
        from pipeline.db.connection import execute_query
        result = execute_query("SELECT 1 AS ok")
        assert result[0]["ok"] == 1
        logger.info("  PostgreSQL: OK")
    except Exception as e:
        errors.append(f"PostgreSQL: {e}")
        logger.error(f"  PostgreSQL: FAILED — {e}")

    # Test Odds API
    try:
        from pipeline.ingestion.live_odds import fetch_live_odds
        games = fetch_live_odds("baseball_mlb")
        logger.info(f"  Odds API: OK — {len(games)} MLB games found")
    except Exception as e:
        errors.append(f"Odds API: {e}")
        logger.error(f"  Odds API: FAILED — {e}")

    # Test Baseball Savant
    try:
        from pipeline.ingestion.mlb_statcast import fetch_pitching_statcast
        df = fetch_pitching_statcast()
        logger.info(f"  Baseball Savant: OK — {len(df)} pitcher records")
    except Exception as e:
        errors.append(f"Baseball Savant: {e}")
        logger.error(f"  Baseball Savant: FAILED — {e}")

    # Test Anthropic (optional)
    try:
        from pipeline.config import ANTHROPIC_API_KEY
        if ANTHROPIC_API_KEY:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            r = client.messages.create(model="claude-haiku-4-5-20251001", max_tokens=10,
                                       messages=[{"role": "user", "content": "ping"}])
            logger.info("  Anthropic API: OK")
        else:
            logger.warning("  Anthropic API: MISSING KEY — agent layer will be disabled")
    except Exception as e:
        errors.append(f"Anthropic: {e}")
        logger.error(f"  Anthropic API: FAILED — {e}")

    return errors


def install_cron():
    """Add daily pipeline cron jobs in CST."""
    logger.info("Installing cron jobs...")
    python = sys.executable
    script  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run_pipeline.py")

    cron_lines = [
        # 10 AM CST (16:00 UTC) — morning lines
        f"0 16 * * * {python} {script} >> /var/log/maxev_pipeline.log 2>&1",
        # 12 PM CST (18:00 UTC) — after lineups post
        f"0 18 * * * {python} {script} >> /var/log/maxev_pipeline.log 2>&1",
        # 3 AM CST Sunday (09:00 UTC Monday) — weekly Opus deep audit
        f"0 9 * * 1 {python} {script} --weekly-audit >> /var/log/maxev_pipeline.log 2>&1",
    ]

    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        existing = result.stdout if result.returncode == 0 else ""

        new_lines = []
        for line in cron_lines:
            if line not in existing:
                new_lines.append(line)

        if not new_lines:
            logger.info("  Cron jobs already installed")
            return

        updated = existing.rstrip() + "\n" + "\n".join(new_lines) + "\n"
        proc = subprocess.run(["crontab", "-"], input=updated, text=True, capture_output=True)
        if proc.returncode == 0:
            logger.info(f"  Installed {len(new_lines)} new cron job(s)")
        else:
            logger.error(f"  Cron install failed: {proc.stderr}")
    except Exception as e:
        logger.error(f"  Cron install failed: {e}")


def run_first_pipeline():
    """Run an initial rule-based pipeline to verify everything works end-to-end."""
    logger.info("Running initial pipeline (rule-based mode)...")
    from pipeline.orchestrator import run_daily_pipeline
    result = run_daily_pipeline(use_ml=False)
    logger.info(f"Initial run complete: {result}")
    return result


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("MAX-EV Sports — Pipeline Setup")
    logger.info("=" * 60)

    # 1. Schema
    try:
        setup_schema()
    except Exception as e:
        logger.error(f"Schema setup failed: {e}")
        sys.exit(1)

    # 2. Connection tests
    errors = test_connections()

    # 3. Cron
    install_cron()

    # 4. First run (skip if Odds API is down)
    if not any("Odds API" in e for e in errors):
        try:
            run_first_pipeline()
        except Exception as e:
            logger.error(f"First pipeline run failed: {e}")
    else:
        logger.warning("Skipping first pipeline run — Odds API connection failed")

    # Summary
    logger.info("=" * 60)
    if errors:
        logger.warning(f"Setup complete with {len(errors)} warning(s):")
        for e in errors:
            logger.warning(f"  - {e}")
    else:
        logger.info("Setup complete — all systems nominal")
    logger.info("=" * 60)
