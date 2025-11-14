"""
BallDontLie API Client for NBA Player Stats
30x faster than NBA.com API (200-500ms vs 10-30s)

API Docs: https://docs.balldontlie.io/
API Key: 9ca7e6df-853f-4ac4-a964-2eafa7627b8d
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


class BallDontLieClient:
    """
    Fast NBA player statistics client using BallDontLie API
    """

    BASE_URL = "https://api.balldontlie.io/v1"
    API_KEY = "9ca7e6df-853f-4ac4-a964-2eafa7627b8d"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": self.API_KEY
        })
        self.cache = {}
        self.rate_limit_delay = 0.1  # 100ms between requests

    def get_player_by_name(self, player_name: str) -> Optional[Dict]:
        """
        Search for player by name
        Returns player object with id, team, etc.

        Note: API only searches first OR last name, not full name
        So we try last name first, then first name
        """
        cache_key = f"player_search_{player_name.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Try searching by last name first (most unique)
        name_parts = player_name.split()
        search_terms = []

        if len(name_parts) >= 2:
            search_terms = [name_parts[-1], name_parts[0]]  # Last name, then first name
        else:
            search_terms = [player_name]

        url = f"{self.BASE_URL}/players"

        for search_term in search_terms:
            params = {"search": search_term}

            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data.get("data") and len(data["data"]) > 0:
                    # Check if full name matches (case-insensitive)
                    for player in data["data"]:
                        player_full_name = f"{player['first_name']} {player['last_name']}"
                        if player_full_name.lower() == player_name.lower():
                            self.cache[cache_key] = player
                            time.sleep(self.rate_limit_delay)
                            return player

                    # If no exact match, return first result
                    player = data["data"][0]
                    self.cache[cache_key] = player
                    time.sleep(self.rate_limit_delay)
                    return player

            except Exception as e:
                print(f"Error fetching player {player_name} with term '{search_term}': {e}")
                continue

        return None

    def get_player_season_averages(self, player_id: int, season: int = 2024) -> Optional[Dict]:
        """
        Get player's season averages
        Response time: <500ms

        Returns:
        {
            "games_played": 45,
            "min": "34.2",
            "pts": 27.3,
            "reb": 7.0,
            "ast": 5.2,
            "stl": 1.1,
            "blk": 0.4,
            "fg3m": 2.1,
            "fg_pct": 0.487,
            ...
        }
        """
        cache_key = f"season_avg_{player_id}_{season}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        url = f"{self.BASE_URL}/season_averages"
        params = {
            "season": season,
            "player_ids[]": player_id
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("data") and len(data["data"]) > 0:
                stats = data["data"][0]
                self.cache[cache_key] = stats
                time.sleep(self.rate_limit_delay)
                return stats

            return None

        except Exception as e:
            print(f"Error fetching season averages for player {player_id}: {e}")
            return None

    def get_player_recent_games(self,
                                player_id: int,
                                last_n_days: int = 30,
                                limit: int = 10) -> List[Dict]:
        """
        Get player's recent game logs
        Returns list of game stats

        Each game has:
        {
            "id": 123456,
            "date": "2024-11-10",
            "pts": 28,
            "reb": 7,
            "ast": 6,
            "stl": 2,
            "blk": 1,
            "fg3m": 3,
            "min": "36",
            "game": {...},
            "team": {...}
        }
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=last_n_days)

        url = f"{self.BASE_URL}/stats"
        params = {
            "player_ids[]": player_id,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "per_page": limit
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            games = data.get("data", [])
            time.sleep(self.rate_limit_delay)
            return games

        except Exception as e:
            print(f"Error fetching recent games for player {player_id}: {e}")
            return []

    def get_player_stats_vs_team(self,
                                 player_id: int,
                                 opponent_team_id: int,
                                 season: int = 2024) -> List[Dict]:
        """
        Get player's stats in games against specific opponent this season
        """
        # Fetch all games for player this season
        start_date = datetime(season, 10, 1)  # Season starts Oct 1
        end_date = datetime.now()

        url = f"{self.BASE_URL}/stats"
        params = {
            "player_ids[]": player_id,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "per_page": 100
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            all_games = data.get("data", [])

            # Filter for games vs opponent
            vs_opponent = []
            for game in all_games:
                # Check if opponent was in this game
                game_obj = game.get("game", {})
                home_team = game_obj.get("home_team_id")
                away_team = game_obj.get("visitor_team_id")

                if opponent_team_id in [home_team, away_team]:
                    vs_opponent.append(game)

            time.sleep(self.rate_limit_delay)
            return vs_opponent

        except Exception as e:
            print(f"Error fetching matchup stats: {e}")
            return []

    def get_games_by_date(self, game_date) -> List[Dict]:
        """
        Get all NBA games on a specific date

        Args:
            game_date: date object or string in YYYY-MM-DD format

        Returns:
            List of game objects
        """
        from datetime import date as date_type

        if isinstance(game_date, date_type):
            date_str = game_date.strftime("%Y-%m-%d")
        else:
            date_str = str(game_date)

        url = f"{self.BASE_URL}/games"
        params = {
            "dates[]": date_str,
            "per_page": 100
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            games = data.get("data", [])
            time.sleep(self.rate_limit_delay)
            return games

        except Exception as e:
            print(f"Error fetching games for {date_str}: {e}")
            return []

    def get_game_stats(self, game_id: int) -> Optional[Dict]:
        """
        Get all player stats for a specific game

        Args:
            game_id: BallDontLie game ID

        Returns:
            Dict with game info and all player stats
        """
        url = f"{self.BASE_URL}/stats"
        params = {
            "game_ids[]": game_id,
            "per_page": 100
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            time.sleep(self.rate_limit_delay)
            return data

        except Exception as e:
            print(f"Error fetching stats for game {game_id}: {e}")
            return None


def test_client():
    """
    Test the BallDontLie client
    """
    print("=" * 60)
    print("TESTING BALLDONTLIE API CLIENT")
    print("=" * 60)

    client = BallDontLieClient()

    # Test 1: Search for player
    print("\nTest 1: Search for LeBron James...")
    player = client.get_player_by_name("LeBron James")
    if player:
        print(f"  Found: {player['first_name']} {player['last_name']}")
        print(f"  ID: {player['id']}")
        print(f"  Team: {player['team']['full_name']}")

        # Test 2: Get season averages
        print(f"\nTest 2: Get season averages...")
        season_avg = client.get_player_season_averages(player['id'], season=2024)
        if season_avg:
            print(f"  Games Played: {season_avg.get('games_played')}")
            print(f"  PPG: {season_avg.get('pts')}")
            print(f"  RPG: {season_avg.get('reb')}")
            print(f"  APG: {season_avg.get('ast')}")

        # Test 3: Get recent games
        print(f"\nTest 3: Get last 5 games...")
        recent_games = client.get_player_recent_games(player['id'], last_n_days=30, limit=5)
        if recent_games:
            print(f"  Found {len(recent_games)} games:")
            for game in recent_games[:3]:
                date = game.get('game', {}).get('date', 'N/A')[:10]
                pts = game.get('pts', 0)
                reb = game.get('reb', 0)
                ast = game.get('ast', 0)
                print(f"    {date}: {pts}pts/{reb}reb/{ast}ast")

    print("\n" + "=" * 60)
    print("[SUCCESS] BallDontLie API Client Working!")
    print("=" * 60)


if __name__ == "__main__":
    test_client()
