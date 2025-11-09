"""
Basketball Reversal Strategy - Automated Scheduler
Runs every 5 minutes to check live games and fire quarter reversal alerts

This scheduler:
1. Checks all live NBA games
2. Detects Q1-Q2→Q3, Q2-Q3→Q4, and Q3-Q4→OT reversal triggers
3. Generates alerts with bet recommendations
4. Logs all opportunities to database
5. Broadcasts via WebSocket to connected clients

Usage:
    python reversal_scheduler.py

    Or integrate into main.py as background task
"""

import asyncio
import logging
from datetime import datetime, time
from typing import List, Dict
from pathlib import Path
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data directory for logs
LOG_DIR = Path(__file__).parent / "data" / "reversal_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class ReversalScheduler:
    """
    Automated scheduler for quarter reversal detection
    Runs every 5 minutes during basketball game hours
    """

    def __init__(self):
        self.is_running = False
        self.check_interval = 300  # 5 minutes in seconds
        self.opportunities_logged = set()  # Track logged opportunities to avoid duplicates

        # Basketball season months (October - June)
        self.active_months = [10, 11, 12, 1, 2, 3, 4, 5, 6]

        # Game hours (12 PM to 2 AM ET)
        self.start_hour = 12  # noon
        self.end_hour = 2  # 2 AM next day

    def is_basketball_season(self) -> bool:
        """Check if currently in basketball season"""
        current_month = datetime.now().month
        return current_month in self.active_months

    def is_game_hours(self) -> bool:
        """
        Check if currently in typical game hours
        Games run from 12 PM to 2 AM ET (next day)
        """
        current_hour = datetime.now().hour

        # 12 PM (noon) to 11:59 PM
        if self.start_hour <= current_hour <= 23:
            return True

        # 12 AM to 2 AM (next day)
        if 0 <= current_hour < self.end_hour:
            return True

        return False

    async def check_live_games(self) -> List[Dict]:
        """
        Check all live NBA games for quarter reversal opportunities

        Returns:
            List of quarter reversal alerts
        """
        try:
            # Import game tracker
            from game_tracker import game_tracker as tracker
            from strategies.nba_quarter_reversal import QuarterReversalDetector

            detector = QuarterReversalDetector()
            opportunities = []

            # Get all live NBA games
            live_games = [
                game for game in tracker.games.values()
                if game.state.sport_key == 'basketball_nba' and game.state.status == 'live'
            ]

            logger.info(f"Checking {len(live_games)} live NBA games...")

            for game in live_games:
                # Skip if no quarter data
                if not hasattr(game, 'quarters') or not game.quarters:
                    continue

                # Build game data
                game_data = {
                    'id': game.state.id,
                    'period': game.state.quarter or 1,
                    'home_team': {'name': game.state.home_team.name},
                    'away_team': {'name': game.state.away_team.name},
                    'quarters': game.quarters
                }

                # Analyze for reversals
                alert = detector.analyze_game(game_data)

                # Only log HIGH and CRITICAL alerts
                if alert and alert.get('alert_level') in ['HIGH', 'CRITICAL']:
                    # Create unique ID to avoid duplicate logging
                    alert_id = f"{game.state.id}_{alert['quarter']}_{alert['strategy']}"

                    if alert_id not in self.opportunities_logged:
                        opportunities.append(alert)
                        self.opportunities_logged.add(alert_id)

                        logger.info(
                            f"NEW ALERT: {alert['matchup']} - {alert['strategy']} "
                            f"({alert['alert_level']}) - {len(alert['recommendations'])} bets"
                        )

            return opportunities

        except Exception as e:
            logger.error(f"Error checking live games: {e}", exc_info=True)
            return []

    async def log_opportunity(self, alert: Dict):
        """
        Log opportunity to JSON file for tracking

        Args:
            alert: Quarter reversal alert dict
        """
        try:
            log_file = LOG_DIR / f"opportunities_{datetime.now().strftime('%Y_%m_%d')}.json"

            # Read existing logs
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            # Add new opportunity
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'game_id': alert['game_id'],
                'matchup': alert['matchup'],
                'strategy': alert['strategy'],
                'quarter': alert['quarter'],
                'hot_team': alert['hot_team'],
                'reversal_team': alert['reversal_team'],
                'trigger': alert['trigger'],
                'reversal_prob': alert['reversal_prob'],
                'expected_roi': alert['expected_roi'],
                'alert_level': alert['alert_level'],
                'num_bets': len(alert['recommendations']),
                'top_bet': alert['recommendations'][0] if alert['recommendations'] else None
            }

            logs.append(log_entry)

            # Save logs
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)

            logger.info(f"Logged opportunity to {log_file}")

        except Exception as e:
            logger.error(f"Error logging opportunity: {e}")

    async def broadcast_opportunities(self, opportunities: List[Dict]):
        """
        Broadcast opportunities via WebSocket

        Args:
            opportunities: List of quarter reversal alerts
        """
        if not opportunities:
            return

        try:
            # Import WebSocket manager
            from main import ws_manager

            message = {
                "type": "quarter_reversal_batch",
                "timestamp": datetime.now().isoformat(),
                "count": len(opportunities),
                "opportunities": opportunities
            }

            await ws_manager.broadcast_to_all(message)
            logger.info(f"Broadcasted {len(opportunities)} opportunities via WebSocket")

        except Exception as e:
            logger.error(f"Error broadcasting opportunities: {e}")

    async def run_check_cycle(self):
        """Run a single check cycle"""
        logger.info("="*60)
        logger.info("RUNNING REVERSAL CHECK CYCLE")
        logger.info("="*60)

        # Check if we should run
        if not self.is_basketball_season():
            logger.info("Not in basketball season (Oct-Jun). Skipping check.")
            return

        if not self.is_game_hours():
            logger.info(f"Not in game hours (12 PM - 2 AM ET). Current: {datetime.now().strftime('%I:%M %p')}. Skipping check.")
            return

        # Check live games
        opportunities = await self.check_live_games()

        if opportunities:
            logger.info(f"Found {len(opportunities)} quarter reversal opportunities!")

            # Log each opportunity
            for alert in opportunities:
                await self.log_opportunity(alert)

            # Broadcast to connected clients
            await self.broadcast_opportunities(opportunities)
        else:
            logger.info("No quarter reversal opportunities detected.")

        logger.info(f"Next check in {self.check_interval} seconds ({self.check_interval/60:.0f} minutes)")

    async def start(self):
        """Start the scheduler (runs indefinitely)"""
        logger.info("="*60)
        logger.info("QUARTER REVERSAL SCHEDULER STARTED")
        logger.info("="*60)
        logger.info(f"Check interval: {self.check_interval} seconds ({self.check_interval/60:.0f} minutes)")
        logger.info(f"Active months: {self.active_months}")
        logger.info(f"Active hours: {self.start_hour}:00 - {self.end_hour}:00 ET")
        logger.info(f"Logs directory: {LOG_DIR}")
        logger.info("="*60)

        self.is_running = True

        while self.is_running:
            try:
                # Run check cycle
                await self.run_check_cycle()

                # Wait for next cycle
                await asyncio.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                logger.info(f"Continuing... next check in {self.check_interval} seconds")
                await asyncio.sleep(self.check_interval)

    def stop(self):
        """Stop the scheduler"""
        logger.info("Stopping scheduler...")
        self.is_running = False


# Standalone execution
async def main():
    """Run scheduler as standalone process"""
    scheduler = ReversalScheduler()

    try:
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("\nShutting down scheduler...")
        scheduler.stop()


if __name__ == "__main__":
    # Run scheduler
    asyncio.run(main())
