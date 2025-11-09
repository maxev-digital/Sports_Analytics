"""Player Props API Client - Fetch pregame player prop odds from The Odds API"""
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime
from config import ODDS_API_KEY, ODDS_API_BASE

logger = logging.getLogger(__name__)

class PlayerPropsClient:
    """
    Client for fetching player prop odds from The Odds API
    Designed for one-time pregame fetches (not continuous polling)
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = ODDS_API_BASE
        self.props_cache = {}  # Cache fetched props to avoid redundant API calls

    # Sport-specific prop market configurations
    SPORT_PROP_MARKETS = {
        'basketball_nba': [
            'player_points',
            'player_rebounds',
            'player_assists',
            'player_threes',
            'player_points_rebounds_assists',
            'player_blocks',
            'player_steals'
        ],
        'basketball_ncaab': [
            'player_points',
            'player_rebounds',
            'player_assists',
            'player_threes'
        ],
        'americanfootball_nfl': [
            'player_pass_yds',
            'player_pass_tds',
            'player_rush_yds',
            'player_rush_tds',
            'player_receptions',
            'player_reception_yds',
            'player_anytime_td'
        ],
        'americanfootball_ncaaf': [
            'player_pass_yds',
            'player_pass_tds',
            'player_rush_yds',
            'player_rush_tds',
            'player_receptions',
            'player_reception_yds'
        ],
        'icehockey_nhl': [
            'player_points',
            'player_assists',
            'player_goals',
            'player_shots_on_goal',
            'player_goal_scorer_anytime'
        ],
        'baseball_mlb': [
            'batter_home_runs',
            'batter_hits',
            'batter_total_bases',
            'batter_rbis',
            'pitcher_strikeouts',
            'pitcher_hits_allowed',
            'pitcher_earned_runs'
        ]
    }

    async def fetch_game_props(
        self,
        sport_key: str,
        event_id: str,
        prop_markets: Optional[List[str]] = None
    ) -> Dict:
        """
        Fetch player props for a specific game

        Args:
            sport_key: e.g., 'basketball_nba', 'americanfootball_nfl'
            event_id: The Odds API event ID
            prop_markets: List of prop markets to fetch (if None, uses sport defaults)

        Returns:
            Dict with props data organized by market type
        """
        # Check cache first
        cache_key = f"{sport_key}_{event_id}"
        if cache_key in self.props_cache:
            logger.info(f"Using cached props for {event_id}")
            return self.props_cache[cache_key]

        # Use sport-specific markets if not specified
        if prop_markets is None:
            prop_markets = self.SPORT_PROP_MARKETS.get(sport_key, [])

        if not prop_markets:
            logger.warning(f"No prop markets configured for sport: {sport_key}")
            return {}

        # Convert markets list to comma-separated string
        markets_param = ','.join(prop_markets)

        url = f"{self.base_url}/sports/{sport_key}/events/{event_id}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us,us2,us_dfs",  # US books + DFS sites (PrizePicks, Underdog, DraftKings Pick6)
            "markets": markets_param,
            "oddsFormat": "american"
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Log API usage
            remaining = response.headers.get('x-requests-remaining', 'unknown')
            logger.info(f"Props API call for {event_id} - Requests remaining: {remaining}")

            # Parse and structure the props data
            structured_props = self._parse_props_response(data, sport_key)

            # Cache the results
            self.props_cache[cache_key] = structured_props

            return structured_props

        except Exception as e:
            logger.error(f"Error fetching props for {sport_key} event {event_id}: {e}")
            return {}

    def _parse_props_response(self, data: Dict, sport_key: str) -> Dict:
        """
        Parse The Odds API response and structure props data

        Returns structured format:
        {
            'event_id': str,
            'home_team': str,
            'away_team': str,
            'commence_time': str,
            'props_by_market': {
                'player_points': [
                    {
                        'player_name': str,
                        'line': float,
                        'over_odds': int,
                        'under_odds': int,
                        'bookmakers': {
                            'draftkings': {'over': -110, 'under': -110},
                            'fanduel': {...}
                        }
                    }
                ]
            }
        }
        """
        if not data:
            return {}

        result = {
            'event_id': data.get('id'),
            'sport_key': sport_key,
            'home_team': data.get('home_team'),
            'away_team': data.get('away_team'),
            'commence_time': data.get('commence_time'),
            'props_by_market': {}
        }

        bookmakers = data.get('bookmakers', [])

        # Organize props by market type
        for bookmaker in bookmakers:
            bookmaker_name = bookmaker.get('key')
            markets = bookmaker.get('markets', [])

            for market in markets:
                market_key = market.get('key')
                outcomes = market.get('outcomes', [])

                if market_key not in result['props_by_market']:
                    result['props_by_market'][market_key] = {}

                # Group outcomes by player (description field)
                for outcome in outcomes:
                    player_name = outcome.get('description', 'Unknown')
                    point = outcome.get('point')  # The line (e.g., 25.5 points)
                    price = outcome.get('price')  # The odds
                    outcome_name = outcome.get('name')  # 'Over' or 'Under'

                    # Create player entry if doesn't exist
                    if player_name not in result['props_by_market'][market_key]:
                        result['props_by_market'][market_key][player_name] = {
                            'player_name': player_name,
                            'line': point,
                            'bookmakers': {}
                        }

                    # Add bookmaker odds
                    if bookmaker_name not in result['props_by_market'][market_key][player_name]['bookmakers']:
                        result['props_by_market'][market_key][player_name]['bookmakers'][bookmaker_name] = {}

                    if outcome_name == 'Over':
                        result['props_by_market'][market_key][player_name]['bookmakers'][bookmaker_name]['over'] = price
                        result['props_by_market'][market_key][player_name]['line'] = point
                    elif outcome_name == 'Under':
                        result['props_by_market'][market_key][player_name]['bookmakers'][bookmaker_name]['under'] = price

        # Convert nested dicts to lists for easier frontend consumption
        for market_key in result['props_by_market']:
            result['props_by_market'][market_key] = list(result['props_by_market'][market_key].values())

        return result

    async def fetch_all_game_props(self, games: List[Dict]) -> Dict[str, Dict]:
        """
        Fetch props for multiple games (batch operation)

        Args:
            games: List of game dicts with 'id' and 'sport_key'

        Returns:
            Dict keyed by event_id with props data
        """
        all_props = {}

        for game in games:
            event_id = game.get('id')
            sport_key = game.get('sport_key')

            if not event_id or not sport_key:
                continue

            props = await self.fetch_game_props(sport_key, event_id)
            if props:
                all_props[event_id] = props

        logger.info(f"Fetched props for {len(all_props)} games")
        return all_props

    def get_best_odds(self, prop_data: Dict) -> Dict:
        """
        Find best over/under odds across all bookmakers for a prop

        Args:
            prop_data: Single player prop data

        Returns:
            {'best_over': (bookmaker, odds), 'best_under': (bookmaker, odds)}
        """
        best_over = (None, float('-inf'))
        best_under = (None, float('-inf'))

        bookmakers = prop_data.get('bookmakers', {})

        for bookmaker_name, odds in bookmakers.items():
            over_odds = odds.get('over')
            under_odds = odds.get('under')

            if over_odds and over_odds > best_over[1]:
                best_over = (bookmaker_name, over_odds)

            if under_odds and under_odds > best_under[1]:
                best_under = (bookmaker_name, under_odds)

        return {
            'best_over': best_over,
            'best_under': best_under
        }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
