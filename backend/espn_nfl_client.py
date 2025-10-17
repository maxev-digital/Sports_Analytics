"""ESPN NFL API client for live game data"""
import requests
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ESPNNFLClient:
    """Client for fetching NFL live data from ESPN's unofficial API"""

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_scoreboard(self) -> Dict:
        """Fetch NFL scoreboard with all live games"""
        try:
            url = f"{self.BASE_URL}/scoreboard"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching ESPN scoreboard: {e}")
            return {}

    def fetch_game_summary(self, game_id: str) -> Dict:
        """Fetch detailed game summary including boxscore stats"""
        try:
            url = f"{self.BASE_URL}/summary?event={game_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching ESPN game summary for {game_id}: {e}")
            return {}

    def get_live_game_info(self, team_name: str, scoreboard_data: Dict) -> Optional[Dict]:
        """
        Extract live game info for a specific team from scoreboard data

        Returns dict with:
        - is_live: bool
        - period: int (quarter)
        - clock: str (time remaining)
        - game_id: str (ESPN event ID)
        """
        events = scoreboard_data.get('events', [])

        for event in events:
            competitions = event.get('competitions', [])
            if not competitions:
                continue

            comp = competitions[0]
            competitors = comp.get('competitors', [])

            # Check if this game involves the team
            team_found = False
            for competitor in competitors:
                team = competitor.get('team', {})
                team_display = team.get('displayName', '')
                if team_name.lower() in team_display.lower() or team_display.lower() in team_name.lower():
                    team_found = True
                    break

            if not team_found:
                continue

            # Extract game status
            status = comp.get('status', {})
            status_type = status.get('type', {}).get('name', '')

            is_live = status_type in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD']

            if is_live:
                return {
                    'is_live': True,
                    'period': status.get('period', 1),
                    'clock': status.get('displayClock', '15:00'),
                    'game_id': event.get('id'),
                    'status_detail': status.get('type', {}).get('detail', '')
                }

        return None

    def parse_game_stats(self, summary_data: Dict) -> Dict[str, Dict]:
        """
        Parse boxscore statistics from game summary

        Returns dict with team names as keys and stats dict as values
        """
        result = {}

        boxscore = summary_data.get('boxscore', {})
        teams = boxscore.get('teams', [])

        for team_data in teams:
            team_info = team_data.get('team', {})
            team_name = team_info.get('displayName', '')

            stats_dict = {}
            statistics = team_data.get('statistics', [])

            for stat in statistics:
                stat_name = stat.get('name', '')
                stat_value = stat.get('displayValue', '')
                stats_dict[stat_name] = stat_value

            result[team_name] = stats_dict

        return result
