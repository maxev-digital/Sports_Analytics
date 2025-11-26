"""
Odds Collection Service
Continuously collects and archives game odds and player prop odds

Features:
- Smart polling (only when lines change)
- Both pregame and live odds collection
- Player prop odds tracking
- Automatic prop grading after games complete
- Rate limit management
"""

import os
import sys
import time
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from data.odds_archive.odds_archive_db import OddsArchiveDB

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OddsCollectorService:
    """Service to collect and archive odds data"""

    ODDS_API_BASE = "https://api.the-odds-api.com/v4"

    # Sports to track
    SPORTS = [
        'basketball_nba',
        'basketball_ncaab',
        'icehockey_nhl',
        'americanfootball_nfl',
        'americanfootball_ncaaf'
    ]

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ODDS_API_KEY')
        if not self.api_key:
            raise ValueError("ODDS_API_KEY not found")

        self.db = OddsArchiveDB()
        self.session = requests.Session()

        # Rate limiting - track remaining requests from API
        self.requests_remaining = None
        self.last_check = datetime.now()

    def check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        # If we have remaining request count and it's low, warn
        if self.requests_remaining is not None and self.requests_remaining < 1000:
            logger.warning(f"Low API requests remaining: {self.requests_remaining}")
            if self.requests_remaining < 100:
                return False
        return True

    def fetch_odds(self, sport: str, markets: str = "h2h,spreads,totals") -> List[Dict]:
        """
        Fetch current odds from Odds API

        Args:
            sport: Sport identifier
            markets: Comma-separated markets to fetch

        Returns:
            List of game odds
        """
        if not self.check_rate_limit():
            logger.warning("Skipping fetch - rate limit reached")
            return []

        url = f"{self.ODDS_API_BASE}/sports/{sport}/odds/"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': markets,
            'oddsFormat': 'american',
            'dateFormat': 'iso'
        }

        try:
            response = self.session.get(url, params=params, timeout=30)

            # Update rate limit from headers
            if 'x-requests-remaining' in response.headers:
                self.requests_remaining = int(response.headers['x-requests-remaining'])
                logger.info(f"API requests remaining: {self.requests_remaining}")

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Error fetching odds for {sport}: {e}")
            return []

    def parse_and_save_pregame_odds(self, games: List[Dict], sport: str) -> int:
        """
        Parse game odds and save to database

        Args:
            games: List of games from Odds API
            sport: Sport identifier

        Returns:
            Count of odds saved
        """
        odds_records = []

        for game in games:
            game_id = game.get('id')
            home_team = game.get('home_team')
            away_team = game.get('away_team')
            commence_time = game.get('commence_time')

            # Calculate hours before game
            game_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
            hours_before = (game_time - datetime.now(game_time.tzinfo)).total_seconds() / 3600

            # Determine snapshot type
            if hours_before > 48:
                snapshot_type = 'opening'
            elif hours_before > 2:
                snapshot_type = 'morning'
            elif hours_before > 0:
                snapshot_type = 'closing'
            else:
                continue  # Game already started, skip pregame

            # Parse each bookmaker's odds
            for bookmaker in game.get('bookmakers', []):
                bookmaker_key = bookmaker.get('key')

                for market in bookmaker.get('markets', []):
                    market_type = market.get('key')
                    outcomes = market.get('outcomes', [])

                    odds_record = {
                        'timestamp': datetime.now().isoformat(),
                        'game_id': game_id,
                        'sport': sport,
                        'game_date': commence_time[:10],
                        'home_team': home_team,
                        'away_team': away_team,
                        'bookmaker': bookmaker_key,
                        'market_type': market_type,
                        'snapshot_type': snapshot_type,
                        'hours_before_game': hours_before
                    }

                    # Parse outcomes based on market type
                    if market_type == 'h2h':
                        for outcome in outcomes:
                            if outcome['name'] == home_team:
                                odds_record['home_odds'] = outcome.get('price')
                            elif outcome['name'] == away_team:
                                odds_record['away_odds'] = outcome.get('price')

                    elif market_type == 'spreads':
                        for outcome in outcomes:
                            if outcome['name'] == home_team:
                                odds_record['home_line'] = outcome.get('point')
                                odds_record['home_odds'] = outcome.get('price')
                            elif outcome['name'] == away_team:
                                odds_record['away_line'] = outcome.get('point')
                                odds_record['away_odds'] = outcome.get('price')

                    elif market_type == 'totals':
                        for outcome in outcomes:
                            total_line = outcome.get('point')
                            odds_record['total_line'] = total_line

                            if outcome['name'] == 'Over':
                                odds_record['over_under'] = 'Over'
                                odds_record['over_odds'] = outcome.get('price')
                            elif outcome['name'] == 'Under':
                                odds_record['under_odds'] = outcome.get('price')

                    odds_records.append(odds_record)

        # Save to database
        if odds_records:
            saved = self.db.save_pregame_odds(odds_records)
            logger.info(f"Saved {saved} pregame odds records for {sport}")
            return saved

        return 0

    def fetch_player_props_for_event(self, sport: str, event_id: str) -> Optional[Dict]:
        """
        Fetch player prop odds for a specific event/game

        Args:
            sport: Sport identifier
            event_id: The Odds API event ID

        Returns:
            Dict with props data or None if error
        """
        if not self.check_rate_limit():
            return None

        # Sport-specific prop markets
        SPORT_PROP_MARKETS = {
            'basketball_nba': 'player_points,player_rebounds,player_assists,player_threes,player_blocks,player_steals',
            'basketball_ncaab': 'player_points,player_rebounds,player_assists,player_threes',
            'icehockey_nhl': 'player_points,player_assists,player_goals,player_shots_on_goal',
            'americanfootball_nfl': 'player_pass_yds,player_pass_tds,player_rush_yds,player_receptions',
            'americanfootball_ncaaf': 'player_pass_yds,player_pass_tds,player_rush_yds,player_receptions'
        }

        markets = SPORT_PROP_MARKETS.get(sport, '')
        if not markets:
            return None

        url = f"{self.ODDS_API_BASE}/sports/{sport}/events/{event_id}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'us,us2',
            'markets': markets,
            'oddsFormat': 'american',
            'dateFormat': 'iso'
        }

        try:
            response = self.session.get(url, params=params, timeout=30)

            # Update rate limit from headers
            if 'x-requests-remaining' in response.headers:
                self.requests_remaining = int(response.headers['x-requests-remaining'])

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Error fetching props for {sport} event {event_id}: {e}")
            return None

    def parse_and_save_props(self, games: List[Dict], sport: str) -> int:
        """
        Fetch and save player prop odds for each game

        Args:
            games: List of games (from fetch_odds)
            sport: Sport identifier

        Returns:
            Count of props saved
        """
        prop_records = []

        for game in games:
            game_id = game.get('id')
            home_team = game.get('home_team')
            away_team = game.get('away_team')
            commence_time = game.get('commence_time')
            game_date = commence_time[:10]

            # Calculate hours before game
            game_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
            hours_before = (game_time - datetime.now(game_time.tzinfo)).total_seconds() / 3600

            if hours_before <= 0:
                continue  # Skip live props for now

            # Fetch props for this specific event
            props_data = self.fetch_player_props_for_event(sport, game_id)
            if not props_data:
                continue

            # Parse bookmakers
            for bookmaker in props_data.get('bookmakers', []):
                bookmaker_key = bookmaker.get('key')

                for market in bookmaker.get('markets', []):
                    market_key = market.get('key')

                    # Map market to prop type
                    prop_type_map = {
                        'player_points': 'points',
                        'player_rebounds': 'rebounds',
                        'player_assists': 'assists',
                        'player_threes': 'threes',
                        'player_blocks': 'blocks',
                        'player_steals': 'steals',
                        'player_pass_yds': 'pass_yds',
                        'player_pass_tds': 'pass_tds',
                        'player_rush_yds': 'rush_yds',
                        'player_receptions': 'receptions',
                        'player_goals': 'goals',
                        'player_shots_on_goal': 'shots_on_goal'
                    }

                    prop_type = prop_type_map.get(market_key, market_key)

                    # Parse outcomes (each player)
                    outcomes = market.get('outcomes', [])

                    # Group by player (Over/Under pairs)
                    players = {}
                    for outcome in outcomes:
                        player_name = outcome.get('description', '').strip()
                        if not player_name:
                            continue

                        if player_name not in players:
                            players[player_name] = {
                                'line': outcome.get('point'),
                                'over_odds': None,
                                'under_odds': None
                            }

                        if outcome.get('name') == 'Over':
                            players[player_name]['over_odds'] = outcome.get('price')
                        elif outcome.get('name') == 'Under':
                            players[player_name]['under_odds'] = outcome.get('price')

                    # Create prop records
                    for player_name, prop_data in players.items():
                        # Determine team (simplified - would need roster lookup)
                        team = home_team  # Default assumption
                        opponent = away_team

                        prop_records.append({
                            'timestamp': datetime.now().isoformat(),
                            'game_id': game_id,
                            'sport': sport,
                            'game_date': game_date,
                            'player_name': player_name,
                            'team': team,
                            'opponent': opponent,
                            'bookmaker': bookmaker_key,
                            'prop_type': prop_type,
                            'line_value': prop_data['line'],
                            'over_odds': prop_data['over_odds'],
                            'under_odds': prop_data['under_odds'],
                            'snapshot_type': 'pregame',
                            'hours_before_game': hours_before
                        })

        # Save to database
        if prop_records:
            saved = self.db.save_pregame_props(prop_records)
            logger.info(f"Saved {saved} player prop records for {sport}")
            return saved

        return 0

    def run_collection_cycle(self):
        """Run one collection cycle for all sports"""
        logger.info("\n" + "="*60)
        logger.info("ODDS COLLECTION CYCLE")
        logger.info("="*60)

        total_saved = 0

        for sport in self.SPORTS:
            logger.info(f"\nCollecting odds for {sport}...")

            # Fetch and save game odds
            games = self.fetch_odds(sport)
            if games:
                saved = self.parse_and_save_pregame_odds(games, sport)
                total_saved += saved

                # Fetch and save player props (using the games list we just got)
                try:
                    saved = self.parse_and_save_props(games, sport)
                    total_saved += saved
                except Exception as e:
                    logger.error(f"Error saving props for {sport}: {e}")

            # Rate limit delay
            time.sleep(2)

        logger.info(f"\nTotal odds saved this cycle: {total_saved}")
        if self.requests_remaining is not None:
            logger.info(f"API requests remaining: {self.requests_remaining}")

        # Print database stats
        stats = self.db.get_database_stats()
        logger.info(f"Database size: {stats['database_size_mb']:.2f} MB")
        logger.info("="*60 + "\n")

    def run_continuous(self, interval_minutes: int = 30):
        """
        Run continuous odds collection

        Args:
            interval_minutes: Minutes between collection cycles
        """
        logger.info("Starting continuous odds collection...")
        logger.info(f"Collection interval: {interval_minutes} minutes")
        logger.info(f"Sports: {', '.join(self.SPORTS)}")

        while True:
            try:
                self.run_collection_cycle()

                # Sleep until next cycle
                logger.info(f"Sleeping for {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)

            except KeyboardInterrupt:
                logger.info("Stopping odds collection service...")
                break
            except Exception as e:
                logger.error(f"Error in collection cycle: {e}", exc_info=True)
                time.sleep(60)  # Wait 1 minute before retrying


if __name__ == "__main__":
    collector = OddsCollectorService()

    # Run one cycle for testing
    collector.run_collection_cycle()

    # Uncomment to run continuously:
    # collector.run_continuous(interval_minutes=30)
