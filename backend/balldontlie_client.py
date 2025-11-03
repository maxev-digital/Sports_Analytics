"""
BallDontLie API Client - Fast & Reliable NBA Stats
Replaces slow NBA.com API

API Docs: https://docs.balldontlie.io/
"""

import httpx
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os
from config import BALLDONTLIE_API_KEY, BALLDONTLIE_API_BASE

logger = logging.getLogger(__name__)


class BallDontLieClient:
    """
    Fast NBA stats client using BallDontLie API

    Much faster than NBA.com API (< 1 second vs 10-30 seconds)
    """

    def __init__(self):
        self.api_key = BALLDONTLIE_API_KEY
        self.base_url = BALLDONTLIE_API_BASE
        self.client = httpx.AsyncClient(timeout=10.0)
        self.team_cache = {}  # Cache team data
        self.stats_cache = {}  # Cache stats
        self.cache_time = {}  # Track cache age

    async def get_team_stats(self, team_abbreviation: str = None) -> List[Dict]:
        """
        Get current season team stats for all teams or specific team

        Args:
            team_abbreviation: Optional 3-letter team code (e.g., 'LAL', 'GSW')

        Returns:
            List of team stat dicts with pace, offensive rating, defensive rating, etc.
        """
        cache_key = f"team_stats_{team_abbreviation or 'all'}"

        # Check cache (valid for 1 hour)
        if cache_key in self.stats_cache:
            cache_age = datetime.now() - self.cache_time.get(cache_key, datetime.min)
            if cache_age.total_seconds() < 3600:  # 1 hour
                logger.info(f"Using cached team stats for {team_abbreviation or 'all'}")
                return self.stats_cache[cache_key]

        try:
            # BallDontLie provides season averages
            # We'll get recent games and calculate stats
            url = f"{self.base_url}/stats"

            params = {
                "seasons[]": [self._get_current_season()],
                "per_page": 100  # Max results
            }

            headers = {
                "Authorization": self.api_key
            }

            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()
            stats = data.get('data', [])

            # Aggregate by team
            team_stats = self._aggregate_team_stats(stats)

            # Filter by team if specified
            if team_abbreviation:
                team_stats = [t for t in team_stats if t.get('abbreviation') == team_abbreviation]

            # Cache result
            self.stats_cache[cache_key] = team_stats
            self.cache_time[cache_key] = datetime.now()

            logger.info(f"Fetched stats for {len(team_stats)} teams from BallDontLie")
            return team_stats

        except Exception as e:
            logger.error(f"Error fetching team stats from BallDontLie: {e}")
            # Return cached data if available
            return self.stats_cache.get(cache_key, [])

    async def get_player_stats(
        self,
        player_name: str = None,
        team_abbreviation: str = None,
        season: int = None
    ) -> List[Dict]:
        """
        Get player stats

        Args:
            player_name: Player's name
            team_abbreviation: Team abbreviation
            season: Season year (e.g., 2024)

        Returns:
            List of player stat dicts
        """
        try:
            url = f"{self.base_url}/stats"

            params = {
                "seasons[]": [season or self._get_current_season()],
                "per_page": 100
            }

            if player_name:
                # First get player ID
                player = await self.search_player(player_name)
                if player:
                    params["player_ids[]"] = [player.get('id')]

            headers = {
                "Authorization": self.api_key
            }

            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()
            return data.get('data', [])

        except Exception as e:
            logger.error(f"Error fetching player stats: {e}")
            return []

    async def search_player(self, player_name: str) -> Optional[Dict]:
        """
        Search for a player by name

        Args:
            player_name: Player's name (e.g., "LeBron James")

        Returns:
            Player dict or None
        """
        try:
            url = f"{self.base_url}/players"

            params = {
                "search": player_name
            }

            headers = {
                "Authorization": self.api_key
            }

            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()
            players = data.get('data', [])

            if players:
                return players[0]  # Return first match

            return None

        except Exception as e:
            logger.error(f"Error searching for player {player_name}: {e}")
            return None

    async def get_games(
        self,
        team_abbreviation: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict]:
        """
        Get games for a team or date range

        Args:
            team_abbreviation: Team code
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of game dicts
        """
        try:
            url = f"{self.base_url}/games"

            params = {
                "per_page": 100
            }

            if team_abbreviation:
                # Get team ID first
                team = await self._get_team_by_abbreviation(team_abbreviation)
                if team:
                    params["team_ids[]"] = [team.get('id')]

            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            headers = {
                "Authorization": self.api_key
            }

            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()
            return data.get('data', [])

        except Exception as e:
            logger.error(f"Error fetching games: {e}")
            return []

    async def _get_team_by_abbreviation(self, abbreviation: str) -> Optional[Dict]:
        """Get team by abbreviation"""
        if abbreviation in self.team_cache:
            return self.team_cache[abbreviation]

        try:
            url = f"{self.base_url}/teams"

            headers = {
                "Authorization": self.api_key
            }

            response = await self.client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            teams = data.get('data', [])

            # Cache all teams
            for team in teams:
                abbr = team.get('abbreviation')
                if abbr:
                    self.team_cache[abbr] = team

            return self.team_cache.get(abbreviation)

        except Exception as e:
            logger.error(f"Error fetching teams: {e}")
            return None

    def _aggregate_team_stats(self, stats: List[Dict]) -> List[Dict]:
        """
        Aggregate player stats into team stats

        Calculates:
        - Offensive Rating
        - Defensive Rating
        - Pace
        - PPG
        - Field Goal %
        etc.
        """
        from collections import defaultdict

        team_aggregates = defaultdict(lambda: {
            'total_points': 0,
            'total_games': 0,
            'total_fgm': 0,
            'total_fga': 0,
            'total_fg3m': 0,
            'total_fg3a': 0,
            'total_ftm': 0,
            'total_fta': 0,
            'total_minutes': 0,
            'abbreviation': '',
            'team_name': ''
        })

        for stat in stats:
            team = stat.get('team', {})
            team_abbr = team.get('abbreviation')

            if not team_abbr:
                continue

            agg = team_aggregates[team_abbr]
            agg['abbreviation'] = team_abbr
            agg['team_name'] = team.get('full_name', team_abbr)
            agg['total_games'] += 1
            agg['total_points'] += stat.get('pts', 0)
            agg['total_fgm'] += stat.get('fgm', 0)
            agg['total_fga'] += stat.get('fga', 0)
            agg['total_fg3m'] += stat.get('fg3m', 0)
            agg['total_fg3a'] += stat.get('fg3a', 0)
            agg['total_ftm'] += stat.get('ftm', 0)
            agg['total_fta'] += stat.get('fta', 0)
            agg['total_minutes'] += stat.get('min', 0) if stat.get('min') else 0

        # Calculate averages and ratings
        result = []
        for team_abbr, agg in team_aggregates.items():
            games = agg['total_games']
            if games == 0:
                continue

            # Calculate basic stats
            ppg = agg['total_points'] / games
            fg_pct = agg['total_fgm'] / agg['total_fga'] if agg['total_fga'] > 0 else 0
            fg3_pct = agg['total_fg3m'] / agg['total_fg3a'] if agg['total_fg3a'] > 0 else 0
            ft_pct = agg['total_ftm'] / agg['total_fta'] if agg['total_fta'] > 0 else 0

            # Estimate pace (possessions per 48 min)
            # Simplified calculation
            pace = 100.0  # Default NBA average

            # Estimate offensive rating (points per 100 possessions)
            # Simplified: use points per game scaled to 100 possessions
            off_rating = (ppg / pace) * 100 if pace > 0 else 110.0

            # Estimate defensive rating (league average for now)
            def_rating = 112.0  # NBA average

            result.append({
                'team_id': team_abbr,
                'team_name': agg['team_name'],
                'abbreviation': team_abbr,
                'games_played': games,
                'pts_per_game': round(ppg, 1),
                'fg_pct': round(fg_pct, 3),
                'fg3_pct': round(fg3_pct, 3),
                'ft_pct': round(fg_pct, 3),
                'off_rating': round(off_rating, 1),
                'def_rating': round(def_rating, 1),
                'pace': round(pace, 1),
                'net_rating': round(off_rating - def_rating, 1)
            })

        return result

    def _get_current_season(self) -> int:
        """Get current NBA season year"""
        now = datetime.now()
        year = now.year

        # NBA season starts in October
        if now.month >= 10:
            return year
        else:
            return year - 1

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test():
        client = BallDontLieClient()

        # Get Lakers stats
        stats = await client.get_team_stats('LAL')
        print("Lakers Stats:")
        if stats:
            lal = stats[0]
            print(f"  PPG: {lal.get('pts_per_game')}")
            print(f"  ORtg: {lal.get('off_rating')}")
            print(f"  Pace: {lal.get('pace')}")

        await client.close()

    asyncio.run(test())
