"""
NHL API Client - Live game state fetcher for goalie pull timing system

Fetches real-time game data from NHL Stats API:
- Current period and time remaining
- Score differential
- Strength state (5v5, 4v5, etc.)
- Zone and possession
- Coach information

Polls every 5-10 seconds during the final 5 minutes of games.
"""

import requests
import time
from datetime import datetime
from typing import Dict, List, Optional
from database_schema import GoaliePullDB


class NHLAPIClient:
    """Client for NHL Stats API - live game data"""

    def __init__(self):
        self.base_url = "https://api-web.nhle.com/v1"
        self.db = GoaliePullDB()

        # Cache for team info and rosters
        self.team_cache = {}
        self.coach_cache = {}

        # NHL team abbreviations mapping
        self.team_abbrev = {
            'Anaheim Ducks': 'ANA', 'Boston Bruins': 'BOS', 'Buffalo Sabres': 'BUF',
            'Calgary Flames': 'CGY', 'Carolina Hurricanes': 'CAR', 'Chicago Blackhawks': 'CHI',
            'Colorado Avalanche': 'COL', 'Columbus Blue Jackets': 'CBJ', 'Dallas Stars': 'DAL',
            'Detroit Red Wings': 'DET', 'Edmonton Oilers': 'EDM', 'Florida Panthers': 'FLA',
            'Los Angeles Kings': 'LAK', 'Minnesota Wild': 'MIN', 'Montreal Canadiens': 'MTL',
            'Nashville Predators': 'NSH', 'New Jersey Devils': 'NJD', 'New York Islanders': 'NYI',
            'New York Rangers': 'NYR', 'Ottawa Senators': 'OTT', 'Philadelphia Flyers': 'PHI',
            'Pittsburgh Penguins': 'PIT', 'San Jose Sharks': 'SJS', 'Seattle Kraken': 'SEA',
            'St. Louis Blues': 'STL', 'Tampa Bay Lightning': 'TBL', 'Toronto Maple Leafs': 'TOR',
            'Vancouver Canucks': 'VAN', 'Vegas Golden Knights': 'VGK', 'Washington Capitals': 'WSH',
            'Winnipeg Jets': 'WPG', 'Arizona Coyotes': 'ARI', 'Utah Hockey Club': 'UTA'
        }

    def get_live_games(self) -> List[Dict]:
        """
        Get all games currently in progress

        Returns:
            List of game dicts with basic info
        """
        try:
            # NHL API endpoint for today's schedule
            today = datetime.now().strftime('%Y-%m-%d')
            url = f"{self.base_url}/score/{today}"

            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            live_games = []

            # Parse games
            if 'games' in data:
                for game in data['games']:
                    # Only include games that are currently live
                    if game.get('gameState') in ['LIVE', 'CRIT']:  # LIVE or CRITICAL (close game)
                        live_games.append({
                            'game_id': str(game['id']),
                            'home_team': game['homeTeam']['abbrev'],
                            'away_team': game['awayTeam']['abbrev'],
                            'home_score': game['homeTeam']['score'],
                            'away_score': game['awayTeam']['score'],
                            'period': game.get('period', 3),
                            'game_state': game.get('gameState')
                        })

            return live_games

        except Exception as e:
            print(f"[ERROR] Failed to fetch live games: {e}")
            return []

    def get_game_state(self, game_id: str) -> Optional[Dict]:
        """
        Get detailed game state for monitoring

        Args:
            game_id: NHL game ID (e.g., '2024020100')

        Returns:
            Dict with complete game state or None if error
        """
        try:
            # NHL API endpoint for live game feed
            url = f"{self.base_url}/gamecenter/{game_id}/play-by-play"

            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            # Extract game info
            game_state = self._parse_game_state(data, game_id)

            return game_state

        except Exception as e:
            print(f"[ERROR] Failed to fetch game state for {game_id}: {e}")
            return None

    def _parse_game_state(self, data: Dict, game_id: str) -> Dict:
        """Parse NHL API response into our game state format"""

        # Get current period info
        clock = data.get('clock', {})
        period = data.get('period', 3)
        time_remaining_str = clock.get('timeRemaining', '0:00')

        # Parse time remaining (format: "MM:SS")
        try:
            parts = time_remaining_str.split(':')
            minutes = int(parts[0])
            seconds = int(parts[1])
            time_remaining_seconds = minutes * 60 + seconds
        except:
            time_remaining_seconds = 0

        # Get team info
        home_team_data = data.get('homeTeam', {})
        away_team_data = data.get('awayTeam', {})

        home_team = home_team_data.get('abbrev', 'UNK')
        away_team = away_team_data.get('abbrev', 'UNK')

        home_score = home_team_data.get('score', 0)
        away_score = away_team_data.get('score', 0)

        score_differential = home_score - away_score

        # Determine trailing team
        if score_differential < 0:
            trailing_team = home_team
            coach_id = self._get_coach_id(home_team)
        elif score_differential > 0:
            trailing_team = away_team
            coach_id = self._get_coach_id(away_team)
        else:
            trailing_team = None
            coach_id = None

        # Get current situation (strength state)
        situation = data.get('situation', {})
        home_strength = situation.get('homeStrength', 5)
        away_strength = situation.get('awayStrength', 5)
        strength_state = f"{home_strength}v{away_strength}"

        # Get zone and possession
        zone = situation.get('zone', 'Neutral')  # Offensive, Defensive, Neutral
        possession_team = situation.get('possession', None)

        # Determine if trailing team has possession
        has_possession = False
        if trailing_team and possession_team:
            has_possession = (possession_team == trailing_team)

        # Build game state dict
        game_state = {
            'game_id': game_id,
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'period': period,
            'time_remaining_seconds': time_remaining_seconds,
            'score_differential': abs(score_differential),
            'trailing_team': trailing_team,
            'coach_id': coach_id,
            'strength_state': strength_state,
            'zone': zone,
            'has_possession': has_possession,
            'timestamp': datetime.now().isoformat()
        }

        return game_state

    def _get_coach_id(self, team_abbrev: str) -> Optional[str]:
        """
        Get coach ID for team

        For now, returns cached coach names.
        In production, would fetch from NHL roster API.
        """
        # Check cache first
        if team_abbrev in self.coach_cache:
            return self.coach_cache[team_abbrev]

        # Coach mapping (2024-25 season)
        # Update at start of each season
        coach_mapping = {
            'TBL': 'JON_COOPER',
            'CAR': 'ROD_BRINDAMOUR',
            'FLA': 'PAUL_MAURICE',
            'NYR': 'PETER_LAVIOLETTE',
            'COL': 'JARED_BEDNAR',
            'BOS': 'JIM_MONTGOMERY',
            'VGK': 'BRUCE_CASSIDY',
            'DAL': 'PETER_DEBOER',
            'TOR': 'CRAIG_BERUBE',
            'EDM': 'KRIS_KNOBLAUCH',
            'VAN': 'RICK_TOCCHET',
            'WPG': 'SCOTT_ARNIEL',
            'MIN': 'JOHN_HYNES',
            'LAK': 'JIM_HILLER',
            'NJD': 'SHELDON_KEEFE',
            'NSH': 'ANDREW_BRUNETTE',
            'WSH': 'SPENCER_CARBERY',
            'STL': 'DREW_BANNISTER',
            'DET': 'DEREK_LALONDE',
            'OTT': 'TRAVIS_GREEN',
            'UTA': 'ANDRE_TOURIGNY',
            'SEA': 'DAN_BYLSMA',
            'PHI': 'JOHN_TORTORELLA',
            'PIT': 'MIKE_SULLIVAN',
            'CGY': 'RYAN_HUSKA',
            'MTL': 'MARTIN_ST_LOUIS',
            'NYI': 'PATRICK_ROY',
            'BUF': 'LINDY_RUFF',
            'CBJ': 'DEAN_EVASON',
            'ANA': 'GREG_CRONIN',
            'CHI': 'LUKE_RICHARDSON',
            'SJS': 'RYAN_WARSOFSKY'
        }

        coach_id = coach_mapping.get(team_abbrev)

        # Cache it
        if coach_id:
            self.coach_cache[team_abbrev] = coach_id

        return coach_id

    def monitor_games_in_window(self) -> List[Dict]:
        """
        Get all games in the monitoring window (final 5 minutes)

        Returns:
            List of game states ready for propensity evaluation
        """
        live_games = self.get_live_games()

        games_in_window = []

        for game in live_games:
            # Only monitor period 3 or OT
            if game['period'] < 3:
                continue

            # Get detailed state
            game_state = self.get_game_state(game['game_id'])

            if not game_state:
                continue

            # Check if in time window (1:00 to 5:00 remaining)
            time_remaining = game_state['time_remaining_seconds']

            if 60 <= time_remaining <= 300:
                # Check if there's a trailing team
                if game_state['trailing_team']:
                    games_in_window.append(game_state)

        return games_in_window

    def get_current_odds(self, game_id: str, bookmaker: str = 'draftkings') -> Optional[int]:
        """
        Get current odds for "OVER 0.5 goals in period"

        This is a placeholder - needs integration with odds API
        (The Odds API, Pinnacle, or sportsbook-specific APIs)

        Args:
            game_id: NHL game ID
            bookmaker: Which sportsbook to check

        Returns:
            American odds (e.g., +160) or None
        """
        # TODO: Integrate with live odds API
        # For now, return None to indicate odds unavailable

        # In production, would call:
        # - The Odds API (https://the-odds-api.com)
        # - DraftKings API
        # - FanDuel API
        # - Pinnacle API

        print(f"[TODO] Fetch live odds for game {game_id} from {bookmaker}")
        return None


if __name__ == "__main__":
    print("=" * 80)
    print("NHL API CLIENT TEST")
    print("=" * 80)

    client = NHLAPIClient()

    # Test 1: Get live games
    print("\n[TEST 1] Fetching live games...")
    live_games = client.get_live_games()

    if live_games:
        print(f"  Found {len(live_games)} live games:")
        for game in live_games:
            print(f"    {game['away_team']} @ {game['home_team']}: {game['away_score']}-{game['home_score']} (P{game['period']})")
    else:
        print("  No live games found (or off-season)")

    # Test 2: Monitor games in window
    print("\n[TEST 2] Checking games in monitoring window (5:00-1:00 remaining)...")
    games_in_window = client.monitor_games_in_window()

    if games_in_window:
        print(f"  Found {len(games_in_window)} games in window:")
        for game in games_in_window:
            mins = game['time_remaining_seconds'] // 60
            secs = game['time_remaining_seconds'] % 60
            print(f"    {game['game_id']}: {game['trailing_team']} down {game['score_differential']}, {mins}:{secs:02d} left")
            print(f"      Coach: {game['coach_id']}")
            print(f"      Strength: {game['strength_state']}, Zone: {game['zone']}")
    else:
        print("  No games in monitoring window")

    # Test 3: Simulate a specific game (if live games exist)
    if live_games:
        print("\n[TEST 3] Fetching detailed game state for first live game...")
        test_game_id = live_games[0]['game_id']
        game_state = client.get_game_state(test_game_id)

        if game_state:
            print(f"  Game ID: {game_state['game_id']}")
            print(f"  Teams: {game_state['away_team']} @ {game_state['home_team']}")
            print(f"  Score: {game_state['away_score']}-{game_state['home_score']}")
            print(f"  Period: {game_state['period']}")
            print(f"  Time Remaining: {game_state['time_remaining_seconds']}s")
            print(f"  Trailing Team: {game_state['trailing_team']}")
            print(f"  Coach: {game_state['coach_id']}")
            print(f"  Strength: {game_state['strength_state']}")

    print("\n" + "=" * 80)
    print("[OK] NHL API client test complete!")
    print("=" * 80)
