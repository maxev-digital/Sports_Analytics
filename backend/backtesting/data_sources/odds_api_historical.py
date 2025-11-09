"""
The Odds API Historical Data Client
Fetches historical betting odds for backtesting strategies

API Docs: https://the-odds-api.com/liveapi/guides/v4/
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import sys
import os

# Add parent directory to path for database imports
sys.path.append(str(Path(__file__).parent.parent))
from database.backtest_db import BacktestDB


class OddsAPIHistoricalClient:
    """Client for The Odds API historical data"""

    BASE_URL = "https://api.the-odds-api.com/v4"

    def __init__(self, api_key: str = None):
        """
        Initialize client

        Args:
            api_key: The Odds API key (or load from env)
        """
        self.api_key = api_key or os.getenv('ODDS_API_KEY')
        if not self.api_key:
            raise ValueError("ODDS_API_KEY not found in environment or provided")

        self.session = requests.Session()
        self.db = BacktestDB()

    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make GET request to The Odds API"""
        if params is None:
            params = {}

        params['apiKey'] = self.api_key

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            # Check API usage from headers
            if 'x-requests-remaining' in response.headers:
                remaining = response.headers['x-requests-remaining']
                print(f"  [API] Requests remaining: {remaining}")

            time.sleep(0.5)  # Rate limiting
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] API request failed: {e}")
            return {}

    def get_historical_odds(
        self,
        sport: str = 'basketball_nba',
        date: str = None,
        regions: str = 'us',
        markets: str = 'totals,h2h,spreads',
        odds_format: str = 'american'
    ) -> List[Dict]:
        """
        Get historical odds for a specific date

        Args:
            sport: Sport key (basketball_nba, americanfootball_nfl, etc.)
            date: Date in ISO format (YYYY-MM-DDTHH:MM:SSZ) or YYYY-MM-DD
            regions: Comma-separated regions (us, uk, eu, au)
            markets: Comma-separated markets (h2h, spreads, totals)
            odds_format: american, decimal, or fractional

        Returns:
            List of games with odds
        """
        if not date:
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # Convert to ISO format if just date
        if 'T' not in date:
            date = f"{date}T12:00:00Z"

        endpoint = f"sports/{sport}/odds-history"

        params = {
            'date': date,
            'regions': regions,
            'markets': markets,
            'oddsFormat': odds_format
        }

        print(f"Fetching historical odds for {sport} on {date}...")
        data = self._get(endpoint, params)

        if isinstance(data, dict) and 'data' in data:
            return data['data']
        elif isinstance(data, list):
            return data
        else:
            return []

    def save_historical_odds(
        self,
        sport: str,
        start_date: str,
        end_date: str
    ) -> int:
        """
        Fetch and save historical odds for a date range

        Args:
            sport: Sport key
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Count of odds records saved
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        print("\n" + "="*60)
        print(f"FETCHING HISTORICAL ODDS: {sport}")
        print(f"Date Range: {start_date} to {end_date}")
        print("="*60 + "\n")

        saved_count = 0
        current_date = start

        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')

            odds_data = self.get_historical_odds(
                sport=sport,
                date=date_str
            )

            # Save each game's odds to database
            for game in odds_data:
                saved = self._save_game_odds(game, sport)
                if saved:
                    saved_count += 1

            print(f"  Saved {len(odds_data)} games for {date_str}")

            current_date += timedelta(days=1)
            time.sleep(1)  # Rate limiting between days

        print("\n" + "="*60)
        print(f"TOTAL ODDS RECORDS SAVED: {saved_count}")
        print("="*60 + "\n")

        return saved_count

    def _save_game_odds(self, game_data: Dict, sport: str) -> bool:
        """
        Save odds for a single game to database

        Args:
            game_data: Game data from Odds API
            sport: Sport identifier

        Returns:
            True if saved successfully
        """
        try:
            game_id = game_data.get('id')
            commence_time = game_data.get('commence_time')
            home_team = game_data.get('home_team')
            away_team = game_data.get('away_team')

            # Extract bookmaker odds
            bookmakers = game_data.get('bookmakers', [])

            for bookmaker in bookmakers:
                bookmaker_name = bookmaker.get('key')
                markets = bookmaker.get('markets', [])

                for market in markets:
                    market_type = market.get('key')  # h2h, spreads, totals
                    outcomes = market.get('outcomes', [])

                    for outcome in outcomes:
                        # Save each outcome as an odds record
                        odds_record = {
                            'timestamp': commence_time,
                            'game_id': f"{sport}_{game_id}",
                            'sport': sport,
                            'home_team': home_team,
                            'away_team': away_team,
                            'bookmaker': bookmaker_name,
                            'market_type': market_type,
                            'line_value': outcome.get('point'),  # For spreads/totals
                            'odds': outcome.get('price'),
                            'period': 'full_game'
                        }

                        # Insert into database
                        conn = self.db.get_connection()
                        cursor = conn.cursor()

                        cursor.execute("""
                            INSERT INTO odds_history
                            (timestamp, game_id, sport, home_team, away_team,
                             bookmaker, market_type, line_value, odds, period)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            odds_record['timestamp'],
                            odds_record['game_id'],
                            odds_record['sport'],
                            odds_record['home_team'],
                            odds_record['away_team'],
                            odds_record['bookmaker'],
                            odds_record['market_type'],
                            odds_record['line_value'],
                            odds_record['odds'],
                            odds_record['period']
                        ))

                        conn.commit()
                        conn.close()

            return True

        except Exception as e:
            print(f"[ERROR] Failed to save odds: {e}")
            return False


def main():
    """Test the historical odds client"""
    client = OddsAPIHistoricalClient()

    # Test: Fetch yesterday's NBA odds
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    print("Testing Odds API Historical Client...")
    print(f"Fetching odds for {yesterday}\n")

    odds = client.get_historical_odds(
        sport='basketball_nba',
        date=yesterday
    )

    if odds:
        print(f"\n[OK] Found {len(odds)} games with odds data")
        print(f"\nSample game:")
        game = odds[0]
        print(f"  {game.get('away_team')} @ {game.get('home_team')}")
        print(f"  Commence: {game.get('commence_time')}")
        print(f"  Bookmakers: {len(game.get('bookmakers', []))}")
    else:
        print("[WARNING] No odds data returned")
        print("Note: Historical data may only be available for recent dates")


if __name__ == "__main__":
    main()
