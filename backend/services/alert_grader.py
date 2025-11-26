"""
Alert Grading Service
Automatically grades pending alerts when games finish
Runs as background task every 30 minutes
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import httpx
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.alert_logger import (
    get_pending_alerts,
    log_alert_result,
    grade_alert,
    update_alert_status
)
from storage.alert_storage import alert_storage
import config

logger = logging.getLogger(__name__)


class AlertGrader:
    """
    Background service to grade pending alerts
    """

    def __init__(self):
        self.odds_api_key = config.ODDS_API_KEY
        self.base_url = "https://api.the-odds-api.com/v4"
        self.grading_interval = 1800  # 30 minutes in seconds

    async def start(self):
        """
        Start the grading service (runs continuously)
        """
        logger.info("🏁 Alert Grading Service started")
        logger.info(f"Grading interval: {self.grading_interval / 60} minutes")

        while True:
            try:
                await self.grade_pending_alerts()
            except Exception as e:
                logger.error(f"Error in grading cycle: {str(e)}")

            # Wait for next cycle
            await asyncio.sleep(self.grading_interval)

    async def grade_pending_alerts(self):
        """
        Grade all pending alerts by matching to completed games
        """
        try:
            logger.info("🔍 Checking for pending alerts to grade...")

            # Get all pending alerts from CSV
            pending = get_pending_alerts()

            if not pending:
                logger.info("No pending alerts to grade")
                return

            logger.info(f"Found {len(pending)} pending alerts")

            # Group by sport for efficient API calls
            alerts_by_sport = {}
            for alert in pending:
                sport = alert.get('sport', '')
                if sport not in alerts_by_sport:
                    alerts_by_sport[sport] = []
                alerts_by_sport[sport].append(alert)

            # Grade alerts for each sport
            graded_count = 0
            for sport, sport_alerts in alerts_by_sport.items():
                logger.info(f"Grading {len(sport_alerts)} {sport} alerts...")
                count = await self.grade_sport_alerts(sport, sport_alerts)
                graded_count += count

            logger.info(f"✅ Graded {graded_count} alerts")

        except Exception as e:
            logger.error(f"Error grading pending alerts: {str(e)}")

    async def grade_sport_alerts(self, sport: str, alerts: List[Dict]) -> int:
        """
        Grade alerts for a specific sport

        Args:
            sport: Sport key (e.g., 'basketball_nba', 'icehockey_nhl')
            alerts: List of alert dictionaries

        Returns:
            int: Number of alerts graded
        """
        try:
            # Fetch completed games for this sport
            completed_games = await self.fetch_completed_games(sport)

            if not completed_games:
                logger.debug(f"No completed games found for {sport}")
                return 0

            graded_count = 0

            for alert in alerts:
                game_id = alert.get('game_id', '')
                alert_id = alert.get('alert_id', '')

                # Find matching completed game
                game_result = self.find_game_result(game_id, completed_games, sport)

                if not game_result:
                    # Game not finished yet
                    continue

                # Grade the alert
                try:
                    outcome, profit_loss, notes = grade_alert(
                        alert_type=alert.get('alert_type', ''),
                        recommended_side=alert.get('recommended_side', ''),
                        recommended_odds=float(alert.get('recommended_odds', 0)),
                        actual_result=game_result,
                        market_type=alert.get('market_type', '')
                    )

                    # Log the result
                    log_alert_result(
                        alert_id=alert_id,
                        alert_type=alert.get('alert_type', ''),
                        game_id=game_id,
                        outcome=outcome,
                        actual_result=game_result,
                        recommended_side=alert.get('recommended_side', ''),
                        profit_loss=profit_loss,
                        grading_method='auto',
                        notes=notes
                    )

                    # Update status in alerts_log.csv
                    update_alert_status(alert_id, outcome)

                    # Update JSON storage
                    alert_storage.settle_alert(
                        alert_id=alert_id,
                        outcome=outcome,
                        actual_result=game_result
                    )

                    logger.info(f"✅ Graded {alert_id}: {outcome.upper()} ({notes})")
                    graded_count += 1

                except Exception as grade_error:
                    logger.error(f"Error grading alert {alert_id}: {str(grade_error)}")

            return graded_count

        except Exception as e:
            logger.error(f"Error grading {sport} alerts: {str(e)}")
            return 0

    async def fetch_completed_games(self, sport: str) -> List[Dict]:
        """
        Fetch completed games from Odds API scores endpoint

        Args:
            sport: Sport key

        Returns:
            List of completed game dictionaries
        """
        try:
            url = f"{self.base_url}/sports/{sport}/scores/"

            params = {
                'apiKey': self.odds_api_key,
                'daysFrom': 3  # Look back 3 days for completed games
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

                if response.status_code != 200:
                    logger.error(f"Odds API error: {response.status_code}")
                    return []

                data = response.json()

                # Filter to only completed games
                completed = [
                    game for game in data
                    if game.get('completed', False)
                ]

                logger.debug(f"Found {len(completed)} completed {sport} games")
                return completed

        except Exception as e:
            logger.error(f"Error fetching completed games for {sport}: {str(e)}")
            return []

    def find_game_result(
        self,
        game_id: str,
        completed_games: List[Dict],
        sport: str
    ) -> Optional[Dict]:
        """
        Find the result for a specific game

        Args:
            game_id: Game identifier
            completed_games: List of completed games from API
            sport: Sport key

        Returns:
            Dictionary with game result or None if not found
        """
        try:
            # Try to match by game_id
            for game in completed_games:
                if game.get('id') == game_id:
                    return self.extract_game_result(game, sport)

            # If not found by ID, try matching by teams and date
            # This is fallback for older alerts that might have different IDs
            # Extract teams from game_id if possible
            # game_id format often: "sport_away_home" or API format

            return None

        except Exception as e:
            logger.error(f"Error finding game result: {str(e)}")
            return None

    def extract_game_result(self, game: Dict, sport: str) -> Dict:
        """
        Extract result data from completed game

        Args:
            game: Game dictionary from API
            sport: Sport key

        Returns:
            Dictionary with standardized result data
        """
        try:
            scores = game.get('scores', [])

            # Find home and away scores
            away_score = None
            home_score = None

            for score in scores:
                if score.get('name') == game.get('away_team'):
                    away_score = score.get('score')
                elif score.get('name') == game.get('home_team'):
                    home_score = score.get('score')

            if away_score is None or home_score is None:
                # Try alternative score format
                if len(scores) >= 2:
                    away_score = scores[0].get('score')
                    home_score = scores[1].get('score')

            result = {
                'away_team': game.get('away_team'),
                'home_team': game.get('home_team'),
                'away_score': int(away_score) if away_score else 0,
                'home_score': int(home_score) if home_score else 0,
                'actual_total': int(away_score or 0) + int(home_score or 0),
                'completed': game.get('completed', False),
                'completed_at': game.get('last_update'),
            }

            # Add sport-specific data
            if 'icehockey' in sport:
                # Check for empty net goals (would need additional data source)
                result['en_goal_scored'] = False  # Placeholder
                result['goalie_pulled'] = False  # Placeholder

            return result

        except Exception as e:
            logger.error(f"Error extracting game result: {str(e)}")
            return {
                'away_score': 0,
                'home_score': 0,
                'actual_total': 0
            }


def run_grader():
    """
    Run the grader service (synchronous entry point)
    """
    grader = AlertGrader()
    asyncio.run(grader.start())


async def grade_once():
    """
    Grade pending alerts once (for testing/manual runs)
    """
    grader = AlertGrader()
    await grader.grade_pending_alerts()


if __name__ == "__main__":
    # Test run - grade once
    print("Running Alert Grader (single cycle)...")
    asyncio.run(grade_once())
