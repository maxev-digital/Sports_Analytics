"""BallDontLie NHL API Client for advanced team statistics"""
import httpx
import logging
import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class BallDontLieNHLClient:
    def __init__(self):
        self.api_key = os.getenv('BALLDONTLIE_API_KEY')
        if not self.api_key:
            logger.error("BALLDONTLIE_API_KEY not found in environment")
            raise ValueError("BallDontLie API key required")

        self.base_url = "https://api.balldontlie.io/nhl/v1"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.stats_cache = {}  # Cache team stats

    async def get_team_season_stats(self, team_id: int, season: str = "2024") -> Optional[Dict]:
        """
        Fetch team season stats from BallDontLie

        Args:
            team_id: NHL team ID from BallDontLie
            season: Season year (e.g., "2024" for 2024-25 season)

        Returns:
            Dict with power_play_pct, penalty_kill_pct, shots_per_game, etc.
        """
        try:
            cache_key = f"{team_id}_{season}"
            if cache_key in self.stats_cache:
                return self.stats_cache[cache_key]

            url = f"{self.base_url}/teams/{team_id}/season_stats"
            headers = {"Authorization": self.api_key}
            params = {"season": season}

            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            # Cache the result
            self.stats_cache[cache_key] = data
            logger.info(f"✅ Fetched BallDontLie stats for team {team_id}")
            return data

        except Exception as e:
            logger.error(f"Error fetching BallDontLie NHL stats for team {team_id}: {e}")
            return None

    def get_team_id_by_abbr(self, team_abbr: str) -> Optional[int]:
        """
        Map team abbreviation to BallDontLie team ID (correct mapping from API)
        """
        team_id_map = {
            'ana': 56,  # Anaheim Ducks
            'bos': 51,  # Boston Bruins
            'buf': 4,   # Buffalo Sabres
            'car': 18,  # Carolina Hurricanes
            'cbj': 15,  # Columbus Blue Jackets
            'cgy': 50,  # Calgary Flames
            'chi': 53,  # Chicago Blackhawks
            'col': 34,  # Colorado Avalanche
            'dal': 20,  # Dallas Stars
            'det': 54,  # Detroit Red Wings
            'edm': 47,  # Edmonton Oilers
            'fla': 17,  # Florida Panthers
            'lak': 38,  # Los Angeles Kings
            'min': 40,  # Minnesota Wild
            'mtl': 2,   # Montreal Canadiens
            'njd': 32,  # New Jersey Devils
            'nsh': 23,  # Nashville Predators
            'nyi': 7,   # New York Islanders
            'nyr': 61,  # New York Rangers
            'ott': 33,  # Ottawa Senators
            'phi': 55,  # Philadelphia Flyers
            'pit': 59,  # Pittsburgh Penguins
            'sjs': 13,  # San Jose Sharks
            'sea': 57,  # Seattle Kraken
            'stl': 52,  # St. Louis Blues
            'tbl': 22,  # Tampa Bay Lightning
            'tor': 46,  # Toronto Maple Leafs
            'van': 60,  # Vancouver Canucks
            'vgk': 19,  # Vegas Golden Knights
            'wsh': 36,  # Washington Capitals
            'wpg': 21,  # Winnipeg Jets
            'uta': 58,  # Utah Hockey Club
        }
        return team_id_map.get(team_abbr.lower())

    async def close(self):
        await self.client.aclose()
