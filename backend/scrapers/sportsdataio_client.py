#!/usr/bin/env python3
"""
Sports Data IO Comprehensive Client
Handles NBA, NHL, and CBB data across all available feeds
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import time
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class SportsDataIOClient:
    """
    Comprehensive client for Sports Data IO API
    Supports: NBA, NHL, CBB (College Basketball)

    Available Feeds:
    - Competition: Teams, Standings, Games/Schedule
    - Betting: Game Odds, Player Props, Alternate Lines, Live Odds, Futures
    - Stats: Player Stats, Team Stats, Game Stats
    """

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('SPORTSDATAIO_API_KEY')
        self.base_url = 'https://api.sportsdata.io'

        if not self.api_key:
            raise ValueError("SPORTSDATAIO_API_KEY not found in .env file")

        # Track API calls for rate limiting
        self.api_calls = []
        self.max_calls_per_minute = 100  # Adjust based on your plan

    def _rate_limit(self):
        """Simple rate limiting"""
        now = time.time()
        # Remove calls older than 1 minute
        self.api_calls = [t for t in self.api_calls if now - t < 60]

        if len(self.api_calls) >= self.max_calls_per_minute:
            sleep_time = 60 - (now - self.api_calls[0])
            if sleep_time > 0:
                print(f"Rate limit reached. Waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time)

        self.api_calls.append(now)

    def _make_request(self, endpoint):
        """Make API request with error handling"""
        self._rate_limit()

        url = f'{self.base_url}/{endpoint}'
        logger.info(f"[Sports Data IO] Calling: {url}")

        try:
            response = requests.get(url, params={'key': self.api_key}, timeout=30)

            logger.info(f"[Sports Data IO] Response status: {response.status_code}, Data length: {len(response.text)}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"[Sports Data IO] Returned {len(data) if isinstance(data, list) else 'non-list'} items")
                return data
            elif response.status_code == 401:
                logger.error(f"[Sports Data IO] Unauthorized access to {endpoint} - Check API key")
                return None
            elif response.status_code == 404:
                logger.error(f"[Sports Data IO] Endpoint not found: {endpoint}")
                return None
            else:
                logger.error(f"[Sports Data IO] HTTP {response.status_code} for {endpoint}: {response.text[:200]}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"[Sports Data IO] Timeout accessing {endpoint}")
            return None
        except Exception as e:
            logger.error(f"[Sports Data IO] Error: {str(e)}", exc_info=True)
            return None

    # ==================== COMPETITION FEEDS ====================

    def get_teams(self, sport='NBA'):
        """
        Get all teams for a sport

        Args:
            sport: 'NBA', 'NHL', or 'CBB'

        Returns:
            List of team dictionaries
        """
        sport_lower = sport.lower()
        endpoint = f'v3/{sport_lower}/scores/json/teams' if sport != 'CBB' else 'v3/cbb/scores/json/Teams'

        data = self._make_request(endpoint)
        return data if data else []

    def get_standings(self, sport='NBA', season=2025):
        """
        Get standings for a sport/season

        Args:
            sport: 'NBA', 'NHL' (CBB doesn't have standings)
            season: Year (2025 for NBA/NHL 2024-25 season)

        Returns:
            List of standing dictionaries
        """
        if sport == 'CBB':
            print("WARNING: CBB doesn't have standings endpoint")
            return []

        sport_lower = sport.lower()
        endpoint = f'v3/{sport_lower}/scores/json/Standings/{season}'

        data = self._make_request(endpoint)
        return data if data else []

    def get_games(self, sport='NBA', season=2025):
        """
        Get all games for a season

        Args:
            sport: 'NBA', 'NHL', or 'CBB'
            season: Year (2025 for current season)

        Returns:
            List of game dictionaries
        """
        sport_lower = sport.lower()
        endpoint = f'v3/{sport_lower}/scores/json/Games/{season}'

        data = self._make_request(endpoint)
        return data if data else []

    # ==================== BETTING FEEDS ====================

    def _calculate_nfl_week(self, date_str):
        """
        Calculate NFL week number from date
        NFL season starts first Thursday of September
        Regular season is 18 weeks
        """
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')

        # 2025 NFL season starts Sept 4, 2025 (Week 1)
        season_start = datetime(2025, 9, 4)

        if date_obj < season_start:
            # Preseason (Aug 8 - Aug 25, 2025)
            preseason_start = datetime(2025, 8, 8)
            if date_obj >= preseason_start:
                weeks_elapsed = (date_obj - preseason_start).days // 7
                return 'PRE', min(weeks_elapsed + 1, 4)
            return None, None

        # Regular season
        weeks_elapsed = (date_obj - season_start).days // 7
        week = min(weeks_elapsed + 1, 18)

        if week <= 18:
            return 'REG', week

        # Playoffs (starts after Week 18)
        playoff_start = season_start + timedelta(days=18*7)
        if date_obj >= playoff_start:
            playoff_weeks = (date_obj - playoff_start).days // 7
            playoff_week = min(playoff_weeks + 1, 4)  # Wild Card, Divisional, Conference, Super Bowl
            return 'POST', playoff_week

        return 'REG', 18

    def get_game_odds(self, sport='NBA', date=None):
        """
        Get game odds for a specific date (using scores endpoint that includes odds)

        Args:
            sport: 'NBA', 'NHL', 'NFL', 'CFB', or 'CBB'
            date: 'YYYY-MM-DD' format. Defaults to today.

        Returns:
            List of game dictionaries with odds data included
        """
        if date is None:
            # Use current date
            date = datetime.now().strftime('%Y-%m-%d')

        sport_lower = sport.lower()

        # NFL uses week-based endpoint instead of date-based
        if sport.upper() == 'NFL':
            season_type, week = self._calculate_nfl_week(date)
            if season_type is None:
                logger.warning(f"Date {date} is outside NFL season")
                return []
            endpoint = f'v3/nfl/scores/json/ScoresByWeek/2025{season_type}/{week}'
            logger.info(f"[NFL] Using week-based endpoint: {endpoint}")
        else:
            # Use scores endpoints which include odds data and we have access to
            endpoint = f'v3/{sport_lower}/scores/json/GamesByDate/{date}'

        data = self._make_request(endpoint)
        return data if data else []

    def get_player_props(self, sport='NBA', date=None):
        """
        Get player props for a specific date

        ONLY available for NBA and NHL

        Args:
            sport: 'NBA' or 'NHL'
            date: 'YYYY-MM-DD' format. Defaults to today.

        Returns:
            List of player prop dictionaries
        """
        if sport == 'CBB':
            print("WARNING: CBB doesn't have player props endpoint")
            return []

        if date is None:
            date = datetime.now().replace(year=2024).strftime('%Y-%m-%d')

        sport_lower = sport.lower()
        endpoint = f'v3/{sport_lower}/odds/json/PlayerPropsByDate/{date}'

        data = self._make_request(endpoint)
        return data if data else []

    def get_alternate_lines(self, sport='NBA', date=None):
        """
        Get alternate market odds (quarters, halves, etc.)

        ONLY available for NBA and NHL

        Args:
            sport: 'NBA' or 'NHL'
            date: 'YYYY-MM-DD' format. Defaults to today.

        Returns:
            List of alternate market odds dictionaries
        """
        if sport == 'CBB':
            print("WARNING: CBB doesn't have alternate lines endpoint")
            return []

        if date is None:
            date = datetime.now().replace(year=2024).strftime('%Y-%m-%d')

        sport_lower = sport.lower()
        endpoint = f'v3/{sport_lower}/odds/json/AlternateMarketGameOddsByDate/{date}'

        data = self._make_request(endpoint)
        return data if data else []

    def get_live_odds(self, sport='NBA', date=None):
        """
        Get live in-game odds

        Available for NBA, NHL, and CBB

        Args:
            sport: 'NBA', 'NHL', or 'CBB'
            date: 'YYYY-MM-DD' format. Defaults to today.

        Returns:
            List of live odds dictionaries
        """
        if date is None:
            date = datetime.now().replace(year=2024).strftime('%Y-%m-%d')

        sport_lower = sport.lower()
        endpoint = f'v3/{sport_lower}/odds/json/LiveGameOddsByDate/{date}'

        data = self._make_request(endpoint)
        return data if data else []

    def get_futures(self, sport='NBA', season=2025):
        """
        Get betting futures (championship odds, etc.)

        ONLY available for NBA and NHL

        Args:
            sport: 'NBA' or 'NHL'
            season: Year (2025 for current season)

        Returns:
            List of futures dictionaries
        """
        if sport == 'CBB':
            print("WARNING: CBB doesn't have futures endpoint")
            return []

        sport_lower = sport.lower()
        endpoint = f'v3/{sport_lower}/odds/json/BettingFuturesBySeason/{season}'

        data = self._make_request(endpoint)
        return data if data else []

    def get_betting_markets(self, sport='NBA', game_id=None):
        """
        Get betting markets with individual sportsbook odds for a specific game

        Available for NBA, NHL, NFL, CFB, and CBB

        Args:
            sport: 'NBA', 'NHL', 'NFL', 'CFB', or 'CBB'
            game_id: Game ID to fetch betting markets for

        Returns:
            List of betting market dictionaries with BettingOutcomes from each sportsbook
        """
        if game_id is None:
            logger.warning("get_betting_markets requires a game_id")
            return []

        sport_lower = sport.lower()
        endpoint = f'v3/{sport_lower}/odds/json/BettingMarketsByGameID/{game_id}'

        data = self._make_request(endpoint)
        return data if data else []

    # ==================== STATS FEEDS ====================

    def get_player_season_stats(self, sport='NBA', season=2025):
        """
        Get player season statistics

        Args:
            sport: 'NBA', 'NHL', or 'CBB'
            season: Year (2025 for current season)

        Returns:
            List of player stat dictionaries
        """
        sport_lower = sport.lower()
        endpoint = f'v3/{sport_lower}/stats/json/PlayerSeasonStats/{season}'

        data = self._make_request(endpoint)
        return data if data else []

    def get_team_season_stats(self, sport='NBA', season=2025):
        """
        Get team season statistics

        Args:
            sport: 'NBA', 'NHL', or 'CBB'
            season: Year (2025 for current season)

        Returns:
            List of team stat dictionaries
        """
        sport_lower = sport.lower()
        endpoint = f'v3/{sport_lower}/stats/json/TeamSeasonStats/{season}'

        data = self._make_request(endpoint)
        return data if data else []

    def get_injured_players(self, sport='NBA'):
        """
        Get currently injured players

        Available for NBA, NHL, and NFL

        Args:
            sport: 'NBA', 'NHL', or 'NFL'

        Returns:
            List of injured player dictionaries with InjuryStatus, InjuryBodyPart, etc.
        """
        sport_lower = sport.lower()
        endpoint = f'v3/{sport_lower}/projections/json/InjuredPlayers'

        data = self._make_request(endpoint)
        return data if data else []

    def get_player_game_stats(self, sport='NBA', date=None):
        """
        Get player statistics for a specific game date

        Available for NBA, NHL, and CBB

        Args:
            sport: 'NBA', 'NHL', or 'CBB'
            date: 'YYYY-MM-DD' format. Defaults to today.

        Returns:
            List of player game stat dictionaries
        """
        if date is None:
            date = datetime.now().replace(year=2024).strftime('%Y-%m-%d')

        sport_lower = sport.lower()
        endpoint = f'v3/{sport_lower}/stats/json/PlayerGameStatsByDate/{date}'

        data = self._make_request(endpoint)
        return data if data else []

    def get_team_game_stats(self, sport='NBA', date=None):
        """
        Get team statistics for a specific game date

        Available for NBA, NHL, and CBB

        Args:
            sport: 'NBA', 'NHL', or 'CBB'
            date: 'YYYY-MM-DD' format. Defaults to today.

        Returns:
            List of team game stat dictionaries
        """
        if date is None:
            date = datetime.now().replace(year=2024).strftime('%Y-%m-%d')

        sport_lower = sport.lower()
        endpoint = f'v3/{sport_lower}/stats/json/TeamGameStatsByDate/{date}'

        data = self._make_request(endpoint)
        return data if data else []

    def get_box_scores(self, sport='NBA', date=None):
        """
        Get complete box scores for all games on a date

        Available for NBA, NHL, and CBB

        Args:
            sport: 'NBA', 'NHL', or 'CBB'
            date: 'YYYY-MM-DD' format. Defaults to today.

        Returns:
            List of box score dictionaries with complete game details
        """
        if date is None:
            date = datetime.now().replace(year=2024).strftime('%Y-%m-%d')

        sport_lower = sport.lower()
        endpoint = f'v3/{sport_lower}/stats/json/BoxScores/{date}'

        data = self._make_request(endpoint)
        return data if data else []

    # ==================== CONVENIENCE METHODS ====================

    def get_daily_package(self, sport='NBA', date=None, include_props=True):
        """
        Get complete daily package of data for a sport

        Args:
            sport: 'NBA', 'NHL', or 'CBB'
            date: 'YYYY-MM-DD' format. Defaults to today.
            include_props: Whether to include player props (NBA/NHL only)

        Returns:
            Dictionary with all available data for the day
        """
        print(f"\nFetching daily package for {sport} on {date or 'today'}...")
        print("-" * 70)

        package = {
            'sport': sport,
            'date': date or datetime.now().replace(year=2024).strftime('%Y-%m-%d'),
            'game_odds': [],
            'player_props': [],
            'alternate_lines': [],
            'live_odds': [],
            'player_game_stats': [],
            'team_game_stats': [],
            'box_scores': [],
            'teams': [],
        }

        # Get game odds
        print("  Fetching game odds...")
        package['game_odds'] = self.get_game_odds(sport, date)
        print(f"    Got {len(package['game_odds'])} games with odds")

        # Get player props (NBA/NHL only)
        if include_props and sport in ['NBA', 'NHL']:
            print("  Fetching player props...")
            package['player_props'] = self.get_player_props(sport, date)
            print(f"    Got {len(package['player_props'])} player props")

        # Get alternate lines (NBA/NHL only)
        if sport in ['NBA', 'NHL']:
            print("  Fetching alternate lines...")
            package['alternate_lines'] = self.get_alternate_lines(sport, date)
            print(f"    Got {len(package['alternate_lines'])} alternate line games")

        # Get live odds (ALL SPORTS)
        print("  Fetching live odds...")
        package['live_odds'] = self.get_live_odds(sport, date)
        print(f"    Got {len(package['live_odds'])} games with live odds")

        # Get player game stats (ALL SPORTS)
        print("  Fetching player game stats...")
        package['player_game_stats'] = self.get_player_game_stats(sport, date)
        print(f"    Got {len(package['player_game_stats'])} player game stats")

        # Get team game stats (ALL SPORTS)
        print("  Fetching team game stats...")
        package['team_game_stats'] = self.get_team_game_stats(sport, date)
        print(f"    Got {len(package['team_game_stats'])} team game stats")

        # Get box scores (ALL SPORTS)
        print("  Fetching box scores...")
        package['box_scores'] = self.get_box_scores(sport, date)
        print(f"    Got {len(package['box_scores'])} box scores")

        # Get teams
        print("  Fetching teams...")
        package['teams'] = self.get_teams(sport)
        print(f"    Got {len(package['teams'])} teams")

        print(f"\nDaily package complete for {sport}!")
        return package

    def save_daily_package(self, sport='NBA', date=None, output_dir='backend/data/sportsdataio'):
        """
        Fetch and save complete daily package to JSON files

        Args:
            sport: 'NBA', 'NHL', or 'CBB'
            date: 'YYYY-MM-DD' format
            output_dir: Directory to save files
        """
        import json

        os.makedirs(output_dir, exist_ok=True)

        package = self.get_daily_package(sport, date)

        date_str = package['date'].replace('-', '')
        sport_lower = sport.lower()

        # Save each component
        for key, data in package.items():
            if key in ['sport', 'date']:
                continue

            if data:
                filename = f'{output_dir}/{sport_lower}_{key}_{date_str}.json'
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"Saved: {filename}")

        return package


if __name__ == "__main__":
    print("=" * 70)
    print("SPORTS DATA IO CLIENT - DEMO")
    print("=" * 70)

    client = SportsDataIOClient()

    # Demo: Get NBA daily package
    print("\n### NBA DAILY PACKAGE ###")
    nba_package = client.get_daily_package('NBA', date='2024-11-07')

    print(f"\nSample NBA Game Odds:")
    if nba_package['game_odds']:
        game = nba_package['game_odds'][0]
        print(f"  {game['AwayTeamName']} @ {game['HomeTeamName']}")
        print(f"  Pregame odds: {len(game.get('PregameOdds', []))} sportsbooks")
        if game.get('PregameOdds'):
            odds = game['PregameOdds'][0]
            print(f"  Sample: {odds['Sportsbook']} - O/U {odds.get('OverUnder')}")

    print(f"\nSample Player Props:")
    if nba_package['player_props']:
        prop = nba_package['player_props'][0]
        print(f"  Player: {prop.get('PlayerName', 'Unknown')}")
        print(f"  Prop: {prop.get('PropType', 'Unknown')}")
        print(f"  Line: {prop.get('OverUnder', 'N/A')}")

    print("\n" + "=" * 70)
    print("Demo complete!")
