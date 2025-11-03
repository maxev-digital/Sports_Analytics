"""
Schedule Tracker - Determines rest days and back-to-back situations
Uses The Odds API to fetch game schedules
"""

import httpx
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import os

logger = logging.getLogger(__name__)


class ScheduleTracker:
    """
    Tracks team schedules to determine rest days and back-to-backs

    Uses The Odds API's event listing to build schedule
    """

    def __init__(self):
        self.api_key = os.getenv('ODDS_API_KEY', '')
        self.base_url = os.getenv('ODDS_API_BASE', 'https://api.the-odds-api.com/v4')
        self.schedule_cache: Dict[str, Dict] = {}  # sport -> team schedules
        self.last_fetch: Dict[str, datetime] = {}  # sport -> last fetch time

    async def get_team_rest_days(
        self,
        sport_key: str,
        team_name: str,
        current_game_time: datetime
    ) -> Dict:
        """
        Get rest day information for a team

        Args:
            sport_key: e.g., 'basketball_nba', 'icehockey_nhl'
            team_name: Team name
            current_game_time: Time of current game

        Returns:
            Dict with rest_days, is_back_to_back, is_rested, games_last_7_days
        """
        # Fetch schedule if not cached or stale
        if sport_key not in self.schedule_cache or self._is_cache_stale(sport_key):
            await self._fetch_schedule(sport_key)

        team_schedule = self.schedule_cache.get(sport_key, {}).get(team_name, {})

        if not team_schedule or 'games' not in team_schedule:
            # No schedule data, return defaults
            return {
                'rest_days': 1,  # Default to 1 day
                'is_back_to_back': False,
                'is_rested': False,
                'games_last_7_days': 0,
                'games_next_7_days': 0
            }

        games = team_schedule['games']

        # Find games before and after current game
        previous_games = [
            g for g in games
            if g['commence_time'] < current_game_time
        ]
        future_games = [
            g for g in games
            if g['commence_time'] > current_game_time
        ]

        # Calculate rest days (days since last game)
        rest_days = 1  # Default
        is_back_to_back = False

        if previous_games:
            # Sort by time (most recent first)
            previous_games.sort(key=lambda x: x['commence_time'], reverse=True)
            last_game = previous_games[0]

            time_diff = current_game_time - last_game['commence_time']
            rest_days = time_diff.days

            # B2B if less than 24 hours
            if time_diff.total_seconds() < (24 * 3600):
                is_back_to_back = True
                rest_days = 0

        is_rested = rest_days >= 3

        # Count games in last 7 days
        seven_days_ago = current_game_time - timedelta(days=7)
        games_last_7 = len([
            g for g in previous_games
            if g['commence_time'] >= seven_days_ago
        ])

        # Count games in next 7 days
        seven_days_later = current_game_time + timedelta(days=7)
        games_next_7 = len([
            g for g in future_games
            if g['commence_time'] <= seven_days_later
        ])

        return {
            'rest_days': rest_days,
            'is_back_to_back': is_back_to_back,
            'is_rested': is_rested,
            'games_last_7_days': games_last_7 + 1,  # +1 for current game
            'games_next_7_days': games_next_7
        }

    async def _fetch_schedule(self, sport_key: str):
        """Fetch schedule from The Odds API"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.base_url}/sports/{sport_key}/events"

                response = await client.get(url, params={
                    'apiKey': self.api_key,
                    'dateFormat': 'iso'
                })

                if response.status_code != 200:
                    logger.error(f"Failed to fetch schedule for {sport_key}: {response.status_code}")
                    return

                games = response.json()

                # Build team schedules
                team_schedules = defaultdict(lambda: {'games': []})

                for game in games:
                    home_team = game.get('home_team')
                    away_team = game.get('away_team')
                    commence_time = datetime.fromisoformat(game.get('commence_time').replace('Z', '+00:00'))

                    game_info = {
                        'game_id': game.get('id'),
                        'commence_time': commence_time,
                        'opponent': away_team,
                        'is_home': True
                    }

                    team_schedules[home_team]['games'].append(game_info)

                    # Add for away team
                    game_info_away = game_info.copy()
                    game_info_away['opponent'] = home_team
                    game_info_away['is_home'] = False
                    team_schedules[away_team]['games'].append(game_info_away)

                # Sort each team's games by time
                for team_name in team_schedules:
                    team_schedules[team_name]['games'].sort(
                        key=lambda x: x['commence_time']
                    )

                self.schedule_cache[sport_key] = dict(team_schedules)
                self.last_fetch[sport_key] = datetime.now()

                logger.info(f"Fetched schedule for {sport_key}: {len(team_schedules)} teams")

        except Exception as e:
            logger.error(f"Error fetching schedule for {sport_key}: {e}")

    def _is_cache_stale(self, sport_key: str) -> bool:
        """Check if cache is stale (older than 1 hour)"""
        if sport_key not in self.last_fetch:
            return True

        age = datetime.now() - self.last_fetch[sport_key]
        return age.total_seconds() > 3600  # 1 hour


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test():
        tracker = ScheduleTracker()

        # Test NBA
        rest_info = await tracker.get_team_rest_days(
            sport_key='basketball_nba',
            team_name='Los Angeles Lakers',
            current_game_time=datetime.now()
        )

        print("Lakers Rest Info:")
        print(f"  Rest Days: {rest_info['rest_days']}")
        print(f"  Back-to-Back: {rest_info['is_back_to_back']}")
        print(f"  Rested (3+): {rest_info['is_rested']}")
        print(f"  Games Last 7: {rest_info['games_last_7_days']}")

    asyncio.run(test())
