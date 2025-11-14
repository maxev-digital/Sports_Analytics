"""
Fast Clock Fetcher - Optimized ESPN API calls
Uses ESPN scoreboard endpoints that return ALL games in one call
Caches responses for 10 seconds to avoid repeated calls
"""

import requests
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class FastClockFetcher:
    """Fetch game clock data efficiently from ESPN scoreboard endpoints"""

    def __init__(self):
        self.cache = {}
        self.cache_duration = 10  # seconds

    def get_all_nba_clocks(self) -> Dict[str, Dict]:
        """Fetch ALL NBA game clocks in one API call"""
        cache_key = 'nba_scoreboard'

        # Check cache
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_duration:
                return cached_data

        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            # Parse all games
            games_data = {}
            for event in data.get('events', []):
                competition = event.get('competitions', [{}])[0]
                status = competition.get('status', {})

                # Get team names
                competitors = competition.get('competitors', [])
                home_team = None
                away_team = None
                for comp in competitors:
                    if comp.get('homeAway') == 'home':
                        home_team = comp.get('team', {}).get('displayName')
                    else:
                        away_team = comp.get('team', {}).get('displayName')

                if not home_team or not away_team:
                    continue

                # Get clock data
                period = status.get('period')
                clock = status.get('displayClock', '0:00')
                is_live = status.get('type', {}).get('state') == 'in'

                if is_live and period:
                    key = f"{away_team}@{home_team}"
                    games_data[key] = {
                        'period': period,
                        'clock': clock,
                        'home_team': home_team,
                        'away_team': away_team
                    }

            # Cache result
            self.cache[cache_key] = (datetime.now(), games_data)
            logger.info(f"Fetched {len(games_data)} live NBA games with clocks")
            return games_data

        except Exception as e:
            logger.error(f"Error fetching NBA clocks: {e}")
            return {}

    def get_all_nhl_clocks(self) -> Dict[str, Dict]:
        """Fetch ALL NHL game clocks in one API call"""
        cache_key = 'nhl_scoreboard'

        # Check cache
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_duration:
                return cached_data

        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            # Parse all games
            games_data = {}
            for event in data.get('events', []):
                competition = event.get('competitions', [{}])[0]
                status = competition.get('status', {})

                # Get team names
                competitors = competition.get('competitors', [])
                home_team = None
                away_team = None
                for comp in competitors:
                    if comp.get('homeAway') == 'home':
                        home_team = comp.get('team', {}).get('displayName')
                    else:
                        away_team = comp.get('team', {}).get('displayName')

                if not home_team or not away_team:
                    continue

                # Get clock data
                period = status.get('period')
                clock = status.get('displayClock', '0:00')
                is_live = status.get('type', {}).get('state') == 'in'

                if is_live and period:
                    key = f"{away_team}@{home_team}"
                    games_data[key] = {
                        'period': period,
                        'clock': clock,
                        'home_team': home_team,
                        'away_team': away_team
                    }

            # Cache result
            self.cache[cache_key] = (datetime.now(), games_data)
            logger.info(f"Fetched {len(games_data)} live NHL games with clocks")
            return games_data

        except Exception as e:
            logger.error(f"Error fetching NHL clocks: {e}")
            return {}

    def get_all_nfl_clocks(self) -> Dict[str, Dict]:
        """Fetch ALL NFL game clocks in one API call"""
        cache_key = 'nfl_scoreboard'

        # Check cache
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_duration:
                return cached_data

        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            # Parse all games
            games_data = {}
            for event in data.get('events', []):
                competition = event.get('competitions', [{}])[0]
                status = competition.get('status', {})

                # Get team names
                competitors = competition.get('competitors', [])
                home_team = None
                away_team = None
                for comp in competitors:
                    if comp.get('homeAway') == 'home':
                        home_team = comp.get('team', {}).get('displayName')
                    else:
                        away_team = comp.get('team', {}).get('displayName')

                if not home_team or not away_team:
                    continue

                # Get clock data
                period = status.get('period')
                clock = status.get('displayClock', '0:00')
                is_live = status.get('type', {}).get('state') == 'in'

                if is_live and period:
                    key = f"{away_team}@{home_team}"
                    games_data[key] = {
                        'period': period,
                        'clock': clock,
                        'home_team': home_team,
                        'away_team': away_team
                    }

            # Cache result
            self.cache[cache_key] = (datetime.now(), games_data)
            logger.info(f"Fetched {len(games_data)} live NFL games with clocks")
            return games_data

        except Exception as e:
            logger.error(f"Error fetching NFL clocks: {e}")
            return {}

    def get_all_ncaab_clocks(self) -> Dict[str, Dict]:
        """Fetch ALL NCAAB game clocks in one API call"""
        cache_key = 'ncaab_scoreboard'

        # Check cache
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_duration:
                return cached_data

        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            # Parse all games
            games_data = {}
            for event in data.get('events', []):
                competition = event.get('competitions', [{}])[0]
                status = competition.get('status', {})

                # Get team names
                competitors = competition.get('competitors', [])
                home_team = None
                away_team = None
                for comp in competitors:
                    if comp.get('homeAway') == 'home':
                        home_team = comp.get('team', {}).get('displayName')
                    else:
                        away_team = comp.get('team', {}).get('displayName')

                if not home_team or not away_team:
                    continue

                # Get clock data
                period = status.get('period')
                clock = status.get('displayClock', '0:00')
                is_live = status.get('type', {}).get('state') == 'in'

                if is_live and period:
                    key = f"{away_team}@{home_team}"
                    games_data[key] = {
                        'period': period,
                        'clock': clock,
                        'home_team': home_team,
                        'away_team': away_team
                    }

            # Cache result
            self.cache[cache_key] = (datetime.now(), games_data)
            logger.info(f"Fetched {len(games_data)} live NCAAB games with clocks")
            return games_data

        except Exception as e:
            logger.error(f"Error fetching NCAAB clocks: {e}")
            return {}

    def get_clock(self, sport_key: str, home_team: str, away_team: str) -> Optional[Dict]:
        """
        Get clock for a specific game

        Returns:
            {'period': 3, 'clock': '5:24'} or None
        """
        # Fetch all clocks for this sport (cached)
        if 'basketball_nba' in sport_key:
            all_clocks = self.get_all_nba_clocks()
        elif 'hockey' in sport_key:
            all_clocks = self.get_all_nhl_clocks()
        elif 'americanfootball_nfl' in sport_key:
            all_clocks = self.get_all_nfl_clocks()
        elif 'basketball_ncaab' in sport_key or 'basketball_mens_college' in sport_key:
            all_clocks = self.get_all_ncaab_clocks()
        else:
            return None

        # Try to find game by team names
        key = f"{away_team}@{home_team}"
        if key in all_clocks:
            return all_clocks[key]

        # Try partial match
        for game_key, clock_data in all_clocks.items():
            if home_team in clock_data['home_team'] and away_team in clock_data['away_team']:
                return clock_data

        return None
