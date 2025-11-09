"""
BALLDONTLIE API Client
Free NBA API with 10+ years of historical game data
No API key required!

API Docs: https://docs.balldontlie.io/
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import sys

# Add parent directory to path for database imports
sys.path.append(str(Path(__file__).parent.parent))
from database.backtest_db import BacktestDB


class BallDontLieClient:
    """Client for BALLDONTLIE NBA API"""

    BASE_URL = "https://api.balldontlie.io/v1"

    def __init__(self):
        self.session = requests.Session()
        self.db = BacktestDB()

    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make GET request to API"""
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            # Rate limit: 60 requests per minute (free tier)
            time.sleep(1)  # Be conservative

            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {}

    def get_games(self, season: int, start_date: str = None, end_date: str = None, per_page: int = 100) -> List[Dict]:
        """
        Get games for a season

        Args:
            season: Year (e.g., 2023 for 2023-24 season)
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
            per_page: Results per page (max 100)

        Returns:
            List of game dictionaries
        """
        all_games = []
        page = 1

        while True:
            params = {
                'seasons[]': season,
                'per_page': per_page,
                'page': page
            }

            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date

            print(f"Fetching page {page} for season {season}...")
            data = self._get('games', params=params)

            if not data or 'data' not in data:
                break

            games = data['data']
            if not games:
                break

            all_games.extend(games)

            # Check if there are more pages
            meta = data.get('meta', {})
            if page >= meta.get('total_pages', 1):
                break

            page += 1

        print(f"Fetched {len(all_games)} games for season {season}")
        return all_games

    def get_box_score(self, game_id: int) -> Dict:
        """
        Get detailed box score for a game
        Includes quarter-by-quarter scoring

        Args:
            game_id: Game ID from BALLDONTLIE

        Returns:
            Box score dictionary with quarter scores
        """
        data = self._get(f'stats', params={'game_ids[]': game_id})

        if not data or 'data' not in data:
            return {}

        return data

    def parse_game_to_db_format(self, game: Dict) -> Dict:
        """
        Convert BALLDONTLIE game format to our database format

        Args:
            game: Game dict from API

        Returns:
            Dict ready for database insertion
        """
        # Extract teams
        home_team = game.get('home_team', {})
        away_team = game.get('visitor_team', {})

        # Parse date
        date_str = game.get('date', '')[:10]  # YYYY-MM-DD

        # Determine season
        game_date = datetime.strptime(date_str, '%Y-%m-%d')
        season = game_date.year if game_date.month >= 10 else game_date.year - 1

        return {
            'game_id': f"nba_{game['id']}",
            'sport': 'NBA',
            'date': date_str,
            'season': season,
            'home_team': home_team.get('full_name', home_team.get('name', 'Unknown')),
            'away_team': away_team.get('full_name', away_team.get('name', 'Unknown')),
            'home_score': game.get('home_team_score', 0),
            'away_score': game.get('visitor_team_score', 0),
            # Quarter scores (need to fetch separately from box score)
            'q1_home': 0,
            'q1_away': 0,
            'q2_home': 0,
            'q2_away': 0,
            'q3_home': 0,
            'q3_away': 0,
            'q4_home': 0,
            'q4_away': 0,
            'ot_home': 0,
            'ot_away': 0,
            'data_source': 'balldontlie'
        }

    def import_season(self, season: int, save_to_db: bool = True) -> List[Dict]:
        """
        Import entire season and optionally save to database

        Args:
            season: Year (e.g., 2023 for 2023-24 season)
            save_to_db: Whether to save games to database

        Returns:
            List of imported games
        """
        print(f"\n{'='*60}")
        print(f"Importing NBA season {season}-{season+1}")
        print(f"{'='*60}\n")

        games = self.get_games(season)

        if save_to_db:
            saved_count = 0
            for game in games:
                game_data = self.parse_game_to_db_format(game)
                if self.db.insert_game(game_data):
                    saved_count += 1

            print(f"\n[OK] Saved {saved_count}/{len(games)} games to database")

        return games

    def import_date_range(self, start_date: str, end_date: str, season: int = None, save_to_db: bool = True) -> List[Dict]:
        """
        Import games from a specific date range

        Args:
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
            season: Season year (optional, will auto-detect)
            save_to_db: Whether to save to database

        Returns:
            List of imported games
        """
        if not season:
            # Auto-detect season from start_date
            date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            season = date_obj.year if date_obj.month >= 10 else date_obj.year - 1

        print(f"\nImporting NBA games from {start_date} to {end_date}")

        games = self.get_games(season, start_date=start_date, end_date=end_date)

        if save_to_db:
            saved_count = 0
            for game in games:
                game_data = self.parse_game_to_db_format(game)
                if self.db.insert_game(game_data):
                    saved_count += 1

            print(f"[OK] Saved {saved_count}/{len(games)} games to database")

        return games


def main():
    """CLI for testing"""
    client = BallDontLieClient()

    print("\n" + "="*60)
    print("BALLDONTLIE API CLIENT - NBA Historical Data Importer")
    print("="*60)

    # Test: Import recent season
    print("\nTest 1: Import 2023-24 season (first 100 games)")
    games = client.get_games(season=2023, per_page=100)
    print(f"  Result: {len(games)} games fetched")

    if games:
        # Show sample game
        sample = games[0]
        print(f"\n  Sample game:")
        print(f"    Date: {sample.get('date', 'N/A')}")
        print(f"    {sample.get('visitor_team', {}).get('full_name')} @ {sample.get('home_team', {}).get('full_name')}")
        print(f"    Score: {sample.get('visitor_team_score')} - {sample.get('home_team_score')}")

    # Test: Save one game to database
    if games:
        print("\nTest 2: Save sample game to database")
        game_data = client.parse_game_to_db_format(games[0])
        if client.db.insert_game(game_data):
            print("  [OK] Game saved successfully!")

        # Verify it's in the database
        saved_games = client.db.get_games(sport='NBA', limit=1)
        if saved_games:
            print(f"  [OK] Verified: {len(saved_games)} games in database")
            print(f"       Latest: {saved_games[0]['home_team']} vs {saved_games[0]['away_team']}")

    print("\n" + "="*60)
    print("TESTS COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    main()
