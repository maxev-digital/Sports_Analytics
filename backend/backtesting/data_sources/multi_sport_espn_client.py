"""
Multi-Sport ESPN API Client
Supports: NBA, NCAA Basketball, NFL, NHL, MLB, College Football
For machine learning training data collection
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from database.backtest_db import BacktestDB


class MultiSportESPNClient:
    """Unified client for multiple sports via ESPN API"""

    # Sport configurations: (espn_path, default_season_start, default_season_end, sport_code)
    SPORTS_CONFIG = {
        'nba': {
            'path': 'basketball/nba',
            'season_start_month': 10,
            'season_start_day': 15,
            'season_end_month': 4,
            'season_end_day': 30,
            'sport_code': 'NBA',
            'has_halves': False,
            'periods': 4
        },
        'ncaab': {
            'path': 'basketball/mens-college-basketball',
            'season_start_month': 11,
            'season_start_day': 1,
            'season_end_month': 4,
            'season_end_day': 10,
            'sport_code': 'NCAAB',
            'has_halves': True,  # NCAA uses halves
            'periods': 2
        },
        'nfl': {
            'path': 'football/nfl',
            'season_start_month': 9,
            'season_start_day': 1,
            'season_end_month': 2,
            'season_end_day': 15,
            'sport_code': 'NFL',
            'has_halves': True,
            'periods': 4
        },
        'nhl': {
            'path': 'hockey/nhl',
            'season_start_month': 10,
            'season_start_day': 1,
            'season_end_month': 4,
            'season_end_day': 30,
            'sport_code': 'NHL',
            'has_halves': False,
            'periods': 3
        },
        'cfb': {
            'path': 'football/college-football',
            'season_start_month': 8,
            'season_start_day': 25,
            'season_end_month': 1,
            'season_end_day': 15,
            'sport_code': 'CFB',
            'has_halves': True,
            'periods': 4
        }
    }

    def __init__(self, sport: str = 'nba'):
        """
        Initialize client for specific sport

        Args:
            sport: One of 'nba', 'ncaab', 'nfl', 'nhl', 'cfb'
        """
        if sport not in self.SPORTS_CONFIG:
            raise ValueError(f"Unsupported sport: {sport}. Choose from {list(self.SPORTS_CONFIG.keys())}")

        self.sport = sport
        self.config = self.SPORTS_CONFIG[sport]
        self.session = requests.Session()
        self.db = BacktestDB()

        # Build URLs
        base_url = f"https://site.api.espn.com/apis/site/v2/sports/{self.config['path']}"
        self.scoreboard_url = f"{base_url}/scoreboard"
        self.summary_url = f"{base_url}/summary"

    def _get(self, url: str, params: Dict = None) -> Dict:
        """Make GET request with error handling"""
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            time.sleep(0.5)  # Rate limiting
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
            Scoreboard data
        """
        params = {'dates': date}
        return self._get(self.scoreboard_url, params)

    def parse_game(self, event: Dict, date_str: str) -> Optional[Dict]:
        """
        Parse ESPN game event to database format

        Args:
            event: Game event from ESPN
            date_str: Date in YYYY-MM-DD format

        Returns:
            Game dict or None if incomplete
        """
        try:
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])

            if len(competitors) != 2:
                return None

            # Identify home/away
            home = next((c for c in competitors if c.get('homeAway') == 'home'), {})
            away = next((c for c in competitors if c.get('homeAway') == 'away'), {})

            # Check if game is completed
            status = competition.get('status', {})
            if status.get('type', {}).get('state') != 'post':
                return None

            # Get final scores
            home_score = int(home.get('score', 0))
            away_score = int(away.get('score', 0))

            # Extract period scores
            home_linescore = home.get('linescores', [])
            away_linescore = away.get('linescores', [])

            # Parse based on sport
            if self.config['has_halves'] and self.sport == 'ncaab':
                # NCAA Basketball: 2 halves
                q1_home = home_linescore[0].get('value', 0) if len(home_linescore) > 0 else 0
                q1_away = away_linescore[0].get('value', 0) if len(away_linescore) > 0 else 0
                q2_home = home_linescore[1].get('value', 0) if len(home_linescore) > 1 else 0
                q2_away = away_linescore[1].get('value', 0) if len(away_linescore) > 1 else 0
                q3_home = q3_away = q4_home = q4_away = 0
            else:
                # NBA, NFL, NHL: 4 periods (or 3 for NHL)
                q1_home = home_linescore[0].get('value', 0) if len(home_linescore) > 0 else 0
                q1_away = away_linescore[0].get('value', 0) if len(away_linescore) > 0 else 0
                q2_home = home_linescore[1].get('value', 0) if len(home_linescore) > 1 else 0
                q2_away = away_linescore[1].get('value', 0) if len(away_linescore) > 1 else 0
                q3_home = home_linescore[2].get('value', 0) if len(home_linescore) > 2 else 0
                q3_away = away_linescore[2].get('value', 0) if len(away_linescore) > 2 else 0
                q4_home = home_linescore[3].get('value', 0) if len(home_linescore) > 3 else 0
                q4_away = away_linescore[3].get('value', 0) if len(away_linescore) > 3 else 0

            # Handle overtime
            ot_home = sum(h.get('value', 0) for h in home_linescore[self.config['periods']:])
            ot_away = sum(a.get('value', 0) for a in away_linescore[self.config['periods']:])

            # Get season year
            season_year = event.get('season', {}).get('year', 0)

            return {
                'game_id': event.get('id'),
                'sport': self.config['sport_code'],
                'date': date_str,
                'season': season_year,
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
        """Import all games from specific date"""
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        espn_date = date_obj.strftime('%Y%m%d')

        print(f"Fetching {self.config['sport_code']} games for {date}...")
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

        if save_to_db and saved_count > 0:
            print(f"  [OK] Saved {saved_count}/{len(imported_games)} completed games")

        return imported_games

    def import_season(self, season: int, save_to_db: bool = True) -> List[Dict]:
        """
        Import entire season

        Args:
            season: Starting year (e.g., 2023 for 2023-24 season)
            save_to_db: Save to database

        Returns:
            List of imported games
        """
        start_date = f"{season}-{self.config['season_start_month']:02d}-{self.config['season_start_day']:02d}"
        end_date = f"{season+1}-{self.config['season_end_month']:02d}-{self.config['season_end_day']:02d}"

        print(f"\n{'='*60}")
        print(f"Importing {self.config['sport_code']} {season}-{season+1} season")
        print(f"From {start_date} to {end_date}")
        print(f"{'='*60}\n")

        all_games = []
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        current_date = start

        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            games = self.import_date(date_str, save_to_db=save_to_db)
            all_games.extend(games)

            current_date += timedelta(days=1)
            time.sleep(1)  # Rate limiting

        print(f"\n{'='*60}")
        print(f"{self.config['sport_code']} IMPORT COMPLETE")
        print(f"Total games imported: {len(all_games)}")
        print(f"{'='*60}\n")

        return all_games


def import_all_sports_2024_season():
    """Import 2023-24 season for all major sports"""

    sports = ['nba', 'ncaab', 'nfl', 'nhl']

    for sport in sports:
        print(f"\n{'#'*60}")
        print(f"STARTING {sport.upper()} IMPORT")
        print(f"{'#'*60}\n")

        try:
            client = MultiSportESPNClient(sport=sport)
            games = client.import_season(2023, save_to_db=True)
            print(f"\n[SUCCESS] {sport.upper()}: {len(games)} games imported")
        except Exception as e:
            print(f"\n[ERROR] {sport.upper()} import failed: {e}")

    print(f"\n{'#'*60}")
    print("ALL SPORTS IMPORT COMPLETE")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    # Example: Import NCAA Basketball 2023-24
    client = MultiSportESPNClient(sport='ncaab')
    games = client.import_season(2023, save_to_db=True)
