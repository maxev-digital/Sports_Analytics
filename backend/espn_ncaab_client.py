"""ESPN NCAAB API client for live game clock data"""
import requests
import logging
from typing import Dict, Optional
import re

logger = logging.getLogger(__name__)

class ESPNNCAABClient:
    """Client for fetching live NCAAB game data from ESPN"""

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.espn.com/'
        })
        self.scoreboard_cache = {}

    def fetch_scoreboard(self) -> Dict:
        """Fetch NCAAB scoreboard with all live and upcoming games"""
        try:
            url = f"{self.BASE_URL}/scoreboard"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Cache for quick lookup
            self.scoreboard_cache = {}
            for event in data.get('events', []):
                competitions = event.get('competitions', [])
                if competitions:
                    comp = competitions[0]
                    competitors = comp.get('competitors', [])

                    # Extract team names and game info
                    for competitor in competitors:
                        team_name = competitor.get('team', {}).get('displayName', '')
                        if team_name:
                            self.scoreboard_cache[team_name.lower()] = {
                                'event': event,
                                'competition': comp
                            }

            logger.info(f"Fetched ESPN NCAAB scoreboard with {len(data.get('events', []))} games")
            return data
        except Exception as e:
            logger.error(f"Error fetching ESPN NCAAB scoreboard: {e}")
            return {'events': []}

    def get_live_game_info(self, team_name: str) -> Optional[Dict]:
        """
        Get live game information for a specific team
        Returns dict with:
        - is_live: bool
        - period: int (quarter/period number)
        - clock: str (time remaining, e.g., "12:34")
        """
        try:
            # Normalize team name for lookup
            search_name = team_name.lower()

            # Check cache
            if search_name not in self.scoreboard_cache:
                # Try partial match
                for cached_name in self.scoreboard_cache.keys():
                    if search_name in cached_name or cached_name in search_name:
                        search_name = cached_name
                        break
                else:
                    return None

            game_data = self.scoreboard_cache[search_name]
            event = game_data['event']
            comp = game_data['competition']

            # Check if game is live
            status = event.get('status', {})
            status_type = status.get('type', {}).get('state', '')

            if status_type != 'in':
                return {'is_live': False}

            # Extract period and clock
            period = status.get('period', 1)
            display_clock = status.get('displayClock', '0:00')

            return {
                'is_live': True,
                'period': period,
                'clock': display_clock,
                'status_detail': status.get('type', {}).get('detail', '')
            }

        except Exception as e:
            logger.error(f"Error getting live NCAAB game info for {team_name}: {e}")
            return None

    def normalize_team_name(self, team_name: str) -> str:
        """Normalize team name for matching"""
        # Remove common suffixes
        name = team_name.lower()
        name = re.sub(r'\s+(basketball|hoops|college)\s*$', '', name)
        return name.strip()
