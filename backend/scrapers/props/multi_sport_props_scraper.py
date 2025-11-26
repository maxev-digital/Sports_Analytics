"""
Multi-Sport Player Props Scraper - One-Time Use
Fetches player props from The Odds API for all supported sports

API Cost Estimate:
- NBA: ~9 calls (1 events + 8 games)
- NCAAB: ~16 calls (1 events + 15 games)
- NFL: ~4 calls (1 events + 3 games)
- NCAAF: ~11 calls (1 events + 10 games)
- NHL: ~7 calls (1 events + 6 games)
Total: ~47 API calls for full scrape

Usage:
    python backend/scrapers/props/multi_sport_props_scraper.py --sports nba
    python backend/scrapers/props/multi_sport_props_scraper.py --sports all
    python backend/scrapers/props/multi_sport_props_scraper.py --sports nba,nhl,nfl
"""

import sys
import sqlite3
import asyncio
import argparse
import os
from pathlib import Path
from datetime import datetime, date
from dotenv import load_dotenv

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx

# Load environment
load_dotenv(Path(__file__).parent.parent.parent / '.env')

ODDS_API_KEY = os.getenv('ODDS_API_KEY')
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# Sport configurations
SPORT_CONFIG = {
    'nba': {
        'sport_key': 'basketball_nba',
        'name': 'NBA',
        'markets': [
            'player_points',
            'player_rebounds',
            'player_assists',
            'player_threes',
            'player_points_rebounds_assists',
            'player_blocks',
            'player_steals'
        ]
    },
    'ncaab': {
        'sport_key': 'basketball_ncaab',
        'name': 'NCAAB',
        'markets': [
            'player_points',
            'player_rebounds',
            'player_assists',
            'player_threes'
        ]
    },
    'nfl': {
        'sport_key': 'americanfootball_nfl',
        'name': 'NFL',
        'markets': [
            'player_pass_yds',
            'player_pass_tds',
            'player_rush_yds',
            'player_rush_tds',
            'player_receptions',
            'player_reception_yds',
            'player_anytime_td'
        ]
    },
    'ncaaf': {
        'sport_key': 'americanfootball_ncaaf',
        'name': 'NCAAF',
        'markets': [
            'player_pass_yds',
            'player_pass_tds',
            'player_rush_yds',
            'player_rush_tds',
            'player_receptions',
            'player_reception_yds'
        ]
    },
    'nhl': {
        'sport_key': 'icehockey_nhl',
        'name': 'NHL',
        'markets': [
            'player_points',
            'player_assists',
            'player_goals',
            'player_shots_on_goal',
            'player_goal_scorer_anytime'
        ]
    }
}

# Market key to prop type mapping
MARKET_TO_PROP = {
    # Basketball
    'player_points': 'points',
    'player_rebounds': 'rebounds',
    'player_assists': 'assists',
    'player_threes': 'threes',
    'player_points_rebounds_assists': 'PRA',
    'player_blocks': 'blocks',
    'player_steals': 'steals',
    # Football
    'player_pass_yds': 'pass_yards',
    'player_pass_tds': 'pass_tds',
    'player_rush_yds': 'rush_yards',
    'player_rush_tds': 'rush_tds',
    'player_receptions': 'receptions',
    'player_reception_yds': 'receiving_yards',
    'player_anytime_td': 'anytime_td',
    # Hockey
    'player_goals': 'goals',
    'player_shots_on_goal': 'shots_on_goal',
    'player_goal_scorer_anytime': 'anytime_goal'
}


class MultiSportPropsScraper:
    """Scrapes player props from multiple sports"""

    def __init__(self, db_path: str = "data/player_props.db"):
        self.db_path = db_path
        self.api_calls = 0

    async def fetch_events(self, sport_key: str) -> list:
        """Fetch upcoming events for a sport"""
        url = f"{ODDS_API_BASE}/sports/{sport_key}/events"
        params = {
            'apiKey': ODDS_API_KEY,
            'dateFormat': 'iso'
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            self.api_calls += 1

            remaining = response.headers.get('x-requests-remaining', 'unknown')
            print(f"    API call #{self.api_calls} - Remaining: {remaining}")

            response.raise_for_status()
            return response.json()

    async def fetch_event_props(self, sport_key: str, event_id: str, markets: list) -> dict:
        """Fetch props for a specific event"""
        url = f"{ODDS_API_BASE}/sports/{sport_key}/events/{event_id}/odds"
        markets_str = ','.join(markets)

        params = {
            'apiKey': ODDS_API_KEY,
            'regions': 'us,us2',
            'markets': markets_str,
            'oddsFormat': 'american'
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            self.api_calls += 1

            remaining = response.headers.get('x-requests-remaining', 'unknown')
            print(f"    API call #{self.api_calls} - Remaining: {remaining}")

            response.raise_for_status()
            return response.json()

    def parse_props(self, event_data: dict, sport: str) -> list:
        """Parse props from event data into database format"""
        props = []

        home_team = event_data.get('home_team', '')
        away_team = event_data.get('away_team', '')
        event_id = event_data.get('id', '')

        bookmakers = event_data.get('bookmakers', [])

        # Collect all props across bookmakers
        props_by_player = {}

        for bookmaker in bookmakers:
            bookmaker_name = bookmaker.get('key', 'unknown')
            markets = bookmaker.get('markets', [])

            for market in markets:
                market_key = market.get('key', '')
                prop_type = MARKET_TO_PROP.get(market_key, market_key)
                outcomes = market.get('outcomes', [])

                for outcome in outcomes:
                    player_name = outcome.get('description', '')
                    if not player_name:
                        continue

                    line = outcome.get('point')
                    price = outcome.get('price')
                    name = outcome.get('name', '')  # Over or Under

                    key = f"{player_name}_{prop_type}"

                    if key not in props_by_player:
                        props_by_player[key] = {
                            'player_name': player_name,
                            'prop_type': prop_type,
                            'line': line,
                            'over_odds': -110,
                            'under_odds': -110,
                            'bookmaker': bookmaker_name,
                            'home_team': home_team,
                            'away_team': away_team,
                            'event_id': event_id,
                            'sport': sport
                        }

                    if name == 'Over':
                        props_by_player[key]['over_odds'] = price
                        props_by_player[key]['line'] = line
                    elif name == 'Under':
                        props_by_player[key]['under_odds'] = price

        return list(props_by_player.values())

    async def scrape_sport(self, sport: str) -> dict:
        """Scrape all props for a single sport"""
        config = SPORT_CONFIG.get(sport)
        if not config:
            print(f"  [ERROR] Unknown sport: {sport}")
            return {'sport': sport, 'props': 0, 'games': 0, 'errors': 0}

        sport_key = config['sport_key']
        sport_name = config['name']
        markets = config['markets']

        print(f"\n  [{sport_name}] Fetching events...")

        try:
            events = await self.fetch_events(sport_key)
            print(f"  [{sport_name}] Found {len(events)} events")
        except Exception as e:
            print(f"  [{sport_name}] ERROR fetching events: {e}")
            return {'sport': sport, 'props': 0, 'games': 0, 'errors': 1}

        all_props = []
        errors = 0

        for event in events:
            event_id = event.get('id')
            home_team = event.get('home_team', 'Unknown')
            away_team = event.get('away_team', 'Unknown')

            print(f"    Fetching props: {away_team} @ {home_team}")

            try:
                event_data = await self.fetch_event_props(sport_key, event_id, markets)
                props = self.parse_props(event_data, sport)
                all_props.extend(props)
                print(f"      -> {len(props)} props")
            except Exception as e:
                print(f"      -> ERROR: {e}")
                errors += 1

        return {
            'sport': sport,
            'props': all_props,
            'games': len(events),
            'errors': errors
        }

    def store_props(self, props: list, sport: str) -> int:
        """Store props in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today = date.today()
        stored = 0

        for prop in props:
            try:
                player_id = f"{prop['player_name'].replace(' ', '_')}_{sport}"

                # Determine team assignment (simplified)
                team = prop['home_team']
                opponent = prop['away_team']
                home_away = 'HOME'

                cursor.execute("""
                    INSERT OR REPLACE INTO player_props_lines
                    (date, game_id, player_id, player_name, team, opponent,
                     home_away, prop_type, market_line, over_odds, under_odds, bookmaker, sport)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    today,
                    prop['event_id'],
                    player_id,
                    prop['player_name'],
                    team,
                    opponent,
                    home_away,
                    prop['prop_type'],
                    prop['line'],
                    prop['over_odds'],
                    prop['under_odds'],
                    prop['bookmaker'],
                    sport
                ))
                stored += 1
            except Exception as e:
                print(f"      Store error for {prop['player_name']}: {e}")

        conn.commit()
        conn.close()

        return stored

    async def run(self, sports: list = None):
        """Run full multi-sport scrape"""
        if sports is None:
            sports = ['nba']

        if 'all' in sports:
            sports = list(SPORT_CONFIG.keys())

        print("=" * 70)
        print("MULTI-SPORT PLAYER PROPS SCRAPER")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Sports: {', '.join(sports)}")
        print(f"Database: {self.db_path}")
        print()

        total_props = 0
        total_games = 0
        total_errors = 0

        for sport in sports:
            result = await self.scrape_sport(sport)

            if result['props']:
                stored = self.store_props(result['props'], sport)
                print(f"  [{sport.upper()}] Stored {stored} props")
                total_props += stored

            total_games += result['games']
            total_errors += result.get('errors', 0)

        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"  Total sports: {len(sports)}")
        print(f"  Total games: {total_games}")
        print(f"  Total props stored: {total_props}")
        print(f"  Total API calls: {self.api_calls}")
        print(f"  Errors: {total_errors}")
        print()

        return {
            'sports': sports,
            'games': total_games,
            'props': total_props,
            'api_calls': self.api_calls,
            'errors': total_errors
        }


async def main():
    parser = argparse.ArgumentParser(description='Scrape player props from multiple sports')
    parser.add_argument('--sports', type=str, default='nba',
                       help='Sports to scrape (comma-separated: nba,nhl,nfl,ncaab,ncaaf or "all")')
    parser.add_argument('--db', type=str, default='data/player_props.db',
                       help='Database path')

    args = parser.parse_args()

    sports = [s.strip().lower() for s in args.sports.split(',')]

    scraper = MultiSportPropsScraper(db_path=args.db)
    result = await scraper.run(sports)

    print(f"\n[DONE] Scraped {result['props']} props using {result['api_calls']} API calls")


if __name__ == "__main__":
    asyncio.run(main())
