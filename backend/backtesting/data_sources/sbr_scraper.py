"""
SBR (Sports Book Review) Odds Archive Scraper
Scrapes historical betting odds from sportsbookreview.com

SBR provides historical odds for multiple bookmakers going back years.
This complements The Odds API for comprehensive historical coverage.
"""

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import sys
import re

# Add parent directory to path for database imports
sys.path.append(str(Path(__file__).parent.parent))
from database.backtest_db import BacktestDB


class SBRScraper:
    """Scraper for SBR Odds Archive"""

    BASE_URL = "https://www.sportsbookreview.com"

    # Team name mapping (SBR abbreviations -> Our standard names)
    TEAM_MAPPING = {
        'ATL': 'Atlanta Hawks',
        'BOS': 'Boston Celtics',
        'BKN': 'Brooklyn Nets',
        'CHA': 'Charlotte Hornets',
        'CHI': 'Chicago Bulls',
        'CLE': 'Cleveland Cavaliers',
        'DAL': 'Dallas Mavericks',
        'DEN': 'Denver Nuggets',
        'DET': 'Detroit Pistons',
        'GSW': 'Golden State Warriors',
        'HOU': 'Houston Rockets',
        'IND': 'Indiana Pacers',
        'LAC': 'LA Clippers',
        'LAL': 'Los Angeles Lakers',
        'MEM': 'Memphis Grizzlies',
        'MIA': 'Miami Heat',
        'MIL': 'Milwaukee Bucks',
        'MIN': 'Minnesota Timberwolves',
        'NOP': 'New Orleans Pelicans',
        'NYK': 'New York Knicks',
        'OKC': 'Oklahoma City Thunder',
        'ORL': 'Orlando Magic',
        'PHI': 'Philadelphia 76ers',
        'PHX': 'Phoenix Suns',
        'POR': 'Portland Trail Blazers',
        'SAC': 'Sacramento Kings',
        'SAS': 'San Antonio Spurs',
        'TOR': 'Toronto Raptors',
        'UTA': 'Utah Jazz',
        'WAS': 'Washington Wizards'
    }

    def __init__(self):
        """Initialize scraper"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.db = BacktestDB()

    def scrape_nba_odds(
        self,
        start_date: str,
        end_date: str
    ) -> int:
        """
        Scrape NBA odds for a date range

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Count of odds records saved
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        print("\n" + "="*60)
        print("SCRAPING SBR ODDS ARCHIVE: NBA")
        print(f"Date Range: {start_date} to {end_date}")
        print("="*60 + "\n")

        saved_count = 0
        current_date = start

        while current_date <= end:
            date_str = current_date.strftime('%Y%m%d')  # SBR uses YYYYMMDD format

            try:
                games = self._scrape_date(date_str)

                for game in games:
                    saved = self._save_game_odds(game)
                    if saved:
                        saved_count += 1

                print(f"  ✓ Saved {len(games)} games for {current_date.strftime('%Y-%m-%d')}")

            except Exception as e:
                print(f"  ✗ Error scraping {current_date.strftime('%Y-%m-%d')}: {e}")

            current_date += timedelta(days=1)
            time.sleep(2)  # Respectful rate limiting

        print("\n" + "="*60)
        print(f"TOTAL ODDS RECORDS SAVED: {saved_count}")
        print("="*60 + "\n")

        return saved_count

    def _scrape_date(self, date_str: str) -> List[Dict]:
        """
        Scrape odds for a specific date

        Args:
            date_str: Date in YYYYMMDD format

        Returns:
            List of game odds dictionaries
        """
        url = f"{self.BASE_URL}/betting-odds/nba-basketball/{date_str}/"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Parse games from HTML
            games = self._parse_games(soup, date_str)

            return games

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to fetch {url}: {e}")
            return []

    def _parse_games(self, soup: BeautifulSoup, date_str: str) -> List[Dict]:
        """
        Parse game odds from SBR HTML

        This is a template - SBR's HTML structure may require adjustment
        based on their current layout.

        Args:
            soup: BeautifulSoup object
            date_str: Date string (YYYYMMDD)

        Returns:
            List of game dictionaries
        """
        games = []

        # NOTE: SBR's HTML structure changes frequently
        # This is a basic implementation that may need updates

        # Look for game containers (adjust selector as needed)
        game_rows = soup.find_all('div', class_=re.compile(r'game|event|matchup'))

        for row in game_rows:
            try:
                game = self._parse_game_row(row, date_str)
                if game:
                    games.append(game)
            except Exception as e:
                print(f"  [WARN] Failed to parse game row: {e}")
                continue

        return games

    def _parse_game_row(self, row, date_str: str) -> Optional[Dict]:
        """
        Parse a single game row

        Args:
            row: BeautifulSoup element for game row
            date_str: Date string (YYYYMMDD)

        Returns:
            Game dictionary or None
        """
        # This is a template - needs to be customized based on SBR's HTML

        try:
            # Extract team names (adjust selectors)
            teams = row.find_all('div', class_=re.compile(r'team'))
            if len(teams) < 2:
                return None

            away_team_abbr = teams[0].get_text(strip=True)
            home_team_abbr = teams[1].get_text(strip=True)

            # Map abbreviations to full names
            away_team = self.TEAM_MAPPING.get(away_team_abbr, away_team_abbr)
            home_team = self.TEAM_MAPPING.get(home_team_abbr, home_team_abbr)

            # Extract odds (adjust selectors)
            odds_cells = row.find_all('div', class_=re.compile(r'odds|line'))

            # Parse spread, total, moneyline from cells
            # This is highly dependent on SBR's current layout

            game_data = {
                'date': date_str,
                'away_team': away_team,
                'home_team': home_team,
                'bookmaker': 'Consensus',  # SBR shows consensus lines
                'odds': {}
            }

            # Add parsed odds to game_data
            # (Implementation depends on SBR's HTML structure)

            return game_data

        except Exception as e:
            return None

    def _save_game_odds(self, game_data: Dict) -> bool:
        """
        Save game odds to database

        Args:
            game_data: Game odds dictionary

        Returns:
            True if saved successfully
        """
        try:
            date_str = game_data['date']
            timestamp = datetime.strptime(date_str, '%Y%m%d').isoformat()

            game_id = f"nba_{date_str}_{game_data['away_team']}_{game_data['home_team']}"

            # Save each type of odds (spread, total, moneyline)
            for market_type, odds_value in game_data.get('odds', {}).items():
                conn = self.db.get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO odds_history
                    (timestamp, game_id, sport, home_team, away_team,
                     bookmaker, market_type, line_value, odds, period)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    game_id,
                    'basketball_nba',
                    game_data['home_team'],
                    game_data['away_team'],
                    game_data['bookmaker'],
                    market_type,
                    odds_value.get('line'),
                    odds_value.get('price'),
                    'full_game'
                ))

                conn.commit()
                conn.close()

            return True

        except Exception as e:
            print(f"[ERROR] Failed to save odds: {e}")
            return False

    def test_scraper(self):
        """Test the scraper with a recent date"""
        print("Testing SBR Scraper...")

        # Test with yesterday's date
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')

        print(f"\nFetching odds for {yesterday}...\n")

        games = self._scrape_date(yesterday)

        if games:
            print(f"\n[OK] Found {len(games)} games")
            print(f"\nSample game:")
            print(games[0])
        else:
            print("\n[WARNING] No games found")
            print("Note: SBR's HTML structure may have changed")
            print("You may need to update the parsing logic in _parse_games()")


def main():
    """Test the SBR scraper"""
    scraper = SBRScraper()
    scraper.test_scraper()


if __name__ == "__main__":
    main()
