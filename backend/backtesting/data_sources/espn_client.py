"""
ESPN API Client (Unofficial but Free!)
Access to NBA game data with quarter-by-quarter scores

No API key required - uses ESPN's public JSON endpoints
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


class ESPNClient:
    """Client for ESPN's unofficial NBA API"""

    NBA_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    NBA_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"

    def __init__(self):
        self.session = requests.Session()
        self.db = BacktestDB()

    def _get(self, url: str, params: Dict = None) -> Dict:
        """Make GET request"""
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            time.sleep(0.5)  # Be nice to ESPN's servers
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {}

    def get_scoreboard(self, date: str) -> Dict:
        """
        Get all games for a specific date

        Args:
            date: YYYYMMDD format

        Returns:
            Scoreboard data with all games
        """
        params = {'dates': date}
        return self._get(self.NBA_SCOREBOARD_URL, params)

    def get_game_summary(self, game_id: str) -> Dict:
        """Get detailed game summary including quarter scores"""
        url = f"{self.NBA_SUMMARY_URL}?event={game_id}"
        return self._get(url)

    def parse_game(self, event: Dict, date_str: str) -> Optional[Dict]:
        """
        Parse ESPN game event to our database format

        Args:
            event: Game event from ESPN API
            date_str: Date string YYYY-MM-DD

        Returns:
            Dict ready for database or None if incomplete
        """
        try:
            # Get competition data
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])

            if len(competitors) != 2:
                return None

            # Identify home and away
            home = next((c for c in competitors if c.get('homeAway') == 'home'), {})
            away = next((c for c in competitors if c.get('homeAway') == 'away'), {})

            # Get scores
            home_score = int(home.get('score', 0))
            away_score = int(away.get('score', 0))

            # Only include completed games
            status = competition.get('status', {})
            if status.get('type', {}).get('state') != 'post':
                return None  # Skip in-progress or future games

            # Extract linescore (quarter-by-quarter)
            home_linescore = home.get('linescores', [])
            away_linescore = away.get('linescores', [])

            # Parse quarters (handle OT)
            q1_home = home_linescore[0].get('value', 0) if len(home_linescore) > 0 else 0
            q1_away = away_linescore[0].get('value', 0) if len(away_linescore) > 0 else 0
            q2_home = home_linescore[1].get('value', 0) if len(home_linescore) > 1 else 0
            q2_away = away_linescore[1].get('value', 0) if len(away_linescore) > 1 else 0
            q3_home = home_linescore[2].get('value', 0) if len(home_linescore) > 2 else 0
            q3_away = away_linescore[2].get('value', 0) if len(away_linescore) > 2 else 0
            q4_home = home_linescore[3].get('value', 0) if len(home_linescore) > 3 else 0
            q4_away = away_linescore[3].get('value', 0) if len(away_linescore) > 3 else 0

            # OT scoring (sum all OT periods)
            ot_home = sum(ls.get('value', 0) for ls in home_linescore[4:])
            ot_away = sum(ls.get('value', 0) for ls in away_linescore[4:])

            # Determine season
            game_date = datetime.strptime(date_str, '%Y-%m-%d')
            season = game_date.year if game_date.month >= 10 else game_date.year - 1

            return {
                'game_id': f"nba_{event.get('id')}",
                'sport': 'NBA',
                'date': date_str,
                'season': season,
                'home_team': home.get('team', {}).get('displayName', 'Unknown'),
                'away_team': away.get('team', {}).get('displayName', 'Unknown'),
                'home_score': home_score,
                'away_score': away_score,
                'q1_home': q1_home,
                'q1_away': q1_away,
                'q2_home': q2_home,
                'q2_away': q2_away,
                'q3_home': q3_home,
                'q3_away': q3_away,
                'q4_home': q4_home,
                'q4_away': q4_away,
                'ot_home': ot_home,
                'ot_away': ot_away,
                'data_source': 'espn'
            }

        except Exception as e:
            print(f"Error parsing game: {e}")
            return None

    def import_date(self, date: str, save_to_db: bool = True) -> List[Dict]:
        """
        Import all games from a specific date

        Args:
            date: YYYY-MM-DD format
            save_to_db: Whether to save to database

        Returns:
            List of imported games
        """
        # Convert to ESPN format (YYYYMMDD)
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        espn_date = date_obj.strftime('%Y%m%d')

        print(f"Fetching NBA games for {date}...")
        data = self.get_scoreboard(espn_date)

        events = data.get('events', [])
        print(f"  Found {len(events)} games")

        imported_games = []
        saved_count = 0

        for event in events:
            game_data = self.parse_game(event, date)
            if game_data:
                imported_games.append(game_data)

                if save_to_db:
                    if self.db.insert_game(game_data):
                        saved_count += 1

        if save_to_db:
            print(f"  [OK] Saved {saved_count}/{len(imported_games)} completed games to database")

        return imported_games

    def import_date_range(self, start_date: str, end_date: str, save_to_db: bool = True) -> List[Dict]:
        """
        Import games from a date range

        Args:
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
            save_to_db: Whether to save to database

        Returns:
            List of all imported games
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        print(f"\n{'='*60}")
        print(f"Importing NBA games from {start_date} to {end_date}")
        print(f"{'='*60}\n")

        all_games = []
        current_date = start

        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            games = self.import_date(date_str, save_to_db=save_to_db)
            all_games.extend(games)

            current_date += timedelta(days=1)
            time.sleep(1)  # Rate limiting

        print(f"\n{'='*60}")
        print(f"IMPORT COMPLETE")
        print(f"Total games imported: {len(all_games)}")
        print(f"{'='*60}\n")

        return all_games

    def import_season(self, season: int, save_to_db: bool = True) -> List[Dict]:
        """
        Import an entire NBA season

        Args:
            season: Starting year (e.g., 2023 for 2023-24 season)
            save_to_db: Whether to save to database

        Returns:
            List of imported games
        """
        # NBA season runs roughly Oct 15 - Apr 15
        start_date = f"{season}-10-15"
        end_date = f"{season+1}-04-30"

        print(f"Importing {season}-{season+1} season")
        print(f"Date range: {start_date} to {end_date}")

        return self.import_date_range(start_date, end_date, save_to_db=save_to_db)


def main():
    """CLI for testing"""
    client = ESPNClient()

    print("\n" + "="*60)
    print("ESPN API CLIENT - NBA Historical Data Importer")
    print("="*60)

    # Test: Import yesterday's games (most likely to have completed games)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    print(f"\nTest 1: Import games from {yesterday}")
    games = client.import_date(yesterday, save_to_db=True)

    if games:
        print(f"\n  Sample game:")
        sample = games[0]
        print(f"    {sample['away_team']} @ {sample['home_team']}")
        print(f"    Score: {sample['away_score']} - {sample['home_score']}")
        print(f"    Q1: {sample['q1_away']}-{sample['q1_home']}, Q2: {sample['q2_away']}-{sample['q2_home']}, Q3: {sample['q3_away']}-{sample['q3_home']}, Q4: {sample['q4_away']}-{sample['q4_home']}")
    else:
        print("  No completed games found (might be off-season)")

    # Verify database
    saved_games = client.db.get_games(sport='NBA', limit=5)
    if saved_games:
        print(f"\n  [OK] Database now has {len(saved_games)} games")
        for game in saved_games[:3]:
            print(f"       {game['date']}: {game['away_team']} @ {game['home_team']} ({game['away_score']}-{game['home_score']})")

    print("\n" + "="*60)
    print("TESTS COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    main()
