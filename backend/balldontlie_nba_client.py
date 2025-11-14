"""BallDontLie NBA API Client for team stats, injuries, and live data"""
import httpx
import logging
import os
from typing import Dict, Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class BallDontLieNBAClient:
    def __init__(self):
        self.api_key = os.getenv('BALLDONTLIE_API_KEY')
        if not self.api_key:
            logger.error("BALLDONTLIE_API_KEY not found in environment")
            raise ValueError("BallDontLie API key required")

        self.base_url = "https://api.balldontlie.io/v1"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.stats_cache = {}  # Cache team stats
        self.injury_cache = {}  # Cache player injuries
        self.leaders_cache = {}  # Cache statistical leaders

    async def get_all_teams(self) -> Optional[List[Dict]]:
        """
        Fetch all NBA teams with their IDs
        Returns list of teams with id, full_name, abbreviation, city, conference, division
        """
        try:
            url = f"{self.base_url}/teams"
            headers = {"Authorization": self.api_key}

            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            return data.get('data', [])
        except Exception as e:
            logger.error(f"Error fetching NBA teams: {e}")
            return None

    async def get_team_from_standings(self, team_id: int, season: int = 2025) -> Optional[Dict]:
        """
        Fetch team record and standings data from BallDontLie

        NOTE: BallDontLie NBA API does NOT provide season averages (FG%, pace, ratings, etc.)
        Use this only for accurate win-loss records and standings.
        For detailed stats, use TeamRankings or aggregate from player data.

        Args:
            team_id: NBA team ID from BallDontLie
            season: Season year (e.g., 2024 for 2024-25 season)

        Returns:
            Dict with wins, losses, win_pct, conference_rank, home_record, etc.
        """
        try:
            # Fetch all standings and find this team
            standings = await self.get_team_standings(season=season)
            if standings:
                for standing in standings:
                    if standing.get('team', {}).get('id') == team_id:
                        logger.info(f"✅ Fetched BallDontLie NBA record for team {team_id}: {standing.get('wins')}-{standing.get('losses')}")
                        return standing
            return None

        except Exception as e:
            logger.error(f"Error fetching BallDontLie NBA standings for team {team_id}: {e}")
            return None

    async def get_team_standings(self, season: int = 2025, conference: str = None) -> Optional[List[Dict]]:
        """
        Fetch team standings with records and rankings

        Args:
            season: Season year
            conference: Optional - filter by "Eastern" or "Western"

        Returns:
            List of teams with wins, losses, win_pct, home/road records, etc.
        """
        try:
            cache_key = f"standings_{season}_{conference or 'all'}"
            if cache_key in self.stats_cache:
                return self.stats_cache[cache_key]

            url = f"{self.base_url}/standings"  # FIXED: Correct endpoint
            headers = {"Authorization": self.api_key}
            params = {"season": season}

            if conference:
                params["conference"] = conference

            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            standings = data.get('data', [])
            self.stats_cache[cache_key] = standings
            logger.info(f"✅ Fetched BallDontLie NBA standings for {len(standings)} teams")
            return standings

        except Exception as e:
            logger.error(f"Error fetching NBA standings: {e}")
            return None

    async def get_player_injuries(self) -> Optional[List[Dict]]:
        """
        Fetch current player injuries across all teams

        Returns:
            List of injured players with status, expected return, team, etc.
        """
        try:
            # Check cache (refresh every 30 min for injuries)
            cache_key = "injuries_current"
            cached = self.injury_cache.get(cache_key)
            if cached and (datetime.now() - cached['timestamp']).seconds < 1800:
                return cached['data']

            url = f"{self.base_url}/injuries"
            headers = {"Authorization": self.api_key}

            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            injuries = data.get('data', [])

            # Cache with timestamp
            self.injury_cache[cache_key] = {
                'data': injuries,
                'timestamp': datetime.now()
            }

            logger.info(f"✅ Fetched {len(injuries)} player injuries")
            return injuries

        except Exception as e:
            logger.error(f"Error fetching player injuries: {e}")
            return None

    async def get_statistical_leaders(self, season: int = 2024, stat_type: str = "pts") -> Optional[List[Dict]]:
        """
        Fetch statistical leaders for a specific stat

        Args:
            season: Season year
            stat_type: "pts", "reb", "ast", "stl", "blk", "turnover", "mins", "off_reb", "def_reb"

        Returns:
            List of top players in that category
        """
        try:
            cache_key = f"leaders_{season}_{stat_type}"
            if cache_key in self.leaders_cache:
                return self.leaders_cache[cache_key]

            url = f"{self.base_url}/stats/leaders"
            headers = {"Authorization": self.api_key}
            params = {
                "season": season,
                "stat_type": stat_type
            }

            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            leaders = data.get('data', [])
            self.leaders_cache[cache_key] = leaders
            return leaders

        except Exception as e:
            logger.error(f"Error fetching statistical leaders: {e}")
            return None

    async def get_live_box_scores(self, date: str = None) -> Optional[List[Dict]]:
        """
        Fetch live box scores for current day or specific date
        Updates every ~5 minutes

        Args:
            date: Optional date in YYYY-MM-DD format (defaults to today)

        Returns:
            List of games with live stats for all players
        """
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")

            url = f"{self.base_url}/box_scores/live"
            headers = {"Authorization": self.api_key}
            params = {"date": date}

            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            return data.get('data', [])

        except Exception as e:
            logger.error(f"Error fetching live box scores: {e}")
            return None

    def get_team_id_by_name(self, team_name: str) -> Optional[int]:
        """
        Map team name to BallDontLie team ID
        """
        team_id_map = {
            'Atlanta Hawks': 1,
            'Boston Celtics': 2,
            'Brooklyn Nets': 3,
            'Charlotte Hornets': 4,
            'Chicago Bulls': 5,
            'Cleveland Cavaliers': 6,
            'Dallas Mavericks': 7,
            'Denver Nuggets': 8,
            'Detroit Pistons': 9,
            'Golden State Warriors': 10,
            'Houston Rockets': 11,
            'Indiana Pacers': 12,
            'LA Clippers': 13,
            'Los Angeles Clippers': 13,
            'LA Lakers': 14,
            'Los Angeles Lakers': 14,
            'Memphis Grizzlies': 15,
            'Miami Heat': 16,
            'Milwaukee Bucks': 17,
            'Minnesota Timberwolves': 18,
            'New Orleans Pelicans': 19,
            'New York Knicks': 20,
            'Oklahoma City Thunder': 21,
            'Orlando Magic': 22,
            'Philadelphia 76ers': 23,
            'Phoenix Suns': 24,
            'Portland Trail Blazers': 25,
            'Sacramento Kings': 26,
            'San Antonio Spurs': 27,
            'Toronto Raptors': 28,
            'Utah Jazz': 29,
            'Washington Wizards': 30,
        }
        return team_id_map.get(team_name)

    async def close(self):
        await self.client.aclose()
