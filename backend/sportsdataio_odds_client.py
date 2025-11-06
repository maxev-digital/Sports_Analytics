"""
Sports Data IO Odds Client - Drop-in replacement for OddsAPIClient
Implements the same async interface but uses Sports Data IO instead
"""
import asyncio
from typing import List
from datetime import datetime
from scrapers.sportsdataio_client import SportsDataIOClient
import logging

logger = logging.getLogger(__name__)


class SportsDataIOOddsClient:
    """
    Adapter that implements OddsAPIClient interface using Sports Data IO
    """

    def __init__(self):
        self.client = SportsDataIOClient()
        logger.info("Initialized Sports Data IO Odds Client (with NHL/NCAAF/NCAAB fix)")

    def _parse_betting_markets(self, markets_data, home_team, away_team) -> List[dict]:
        """
        Parse betting markets data into bookmakers format

        Args:
            markets_data: List of betting markets from Sports Data IO
            home_team: Home team name
            away_team: Away team name

        Returns:
            List of bookmakers with their odds
        """
        # Group outcomes by sportsbook
        sportsbook_data = {}

        # Filter for Game Line markets for Full Game (handle both 'Full-Game' and 'Full Game')
        game_line_markets = [m for m in markets_data if
                            m.get('BettingMarketType') == 'Game Line' and
                            m.get('BettingPeriodType') in ['Full-Game', 'Full Game']]

        for market in game_line_markets:
            bet_type = market.get('BettingBetType')

            # Map sport-specific bet types to standard types
            # NHL uses 'Puck Line' and 'Total Goals'
            # NFL uses 'Spread' and 'Total Points'
            # NBA uses 'Spread' and 'Total Points'
            bet_type_mapping = {
                'Puck Line': 'Spread',
                'Total Goals': 'Total Points',
            }
            bet_type = bet_type_mapping.get(bet_type, bet_type)

            # Only process main markets
            if bet_type not in ['Spread', 'Moneyline', 'Total Points']:
                continue

            # Process each betting outcome
            for outcome in market.get('BettingOutcomes', []):
                if not outcome.get('IsAvailable'):
                    continue

                sportsbook = outcome.get('SportsBook', {})
                sportsbook_name = sportsbook.get('Name', 'Unknown')

                # Initialize sportsbook if not exists
                if sportsbook_name not in sportsbook_data:
                    sportsbook_data[sportsbook_name] = {
                        'key': sportsbook_name.lower().replace(' ', '_'),
                        'title': sportsbook_name,
                        'markets': {}
                    }

                # Parse outcome based on bet type
                if bet_type == 'Spread':
                    if 'spreads' not in sportsbook_data[sportsbook_name]['markets']:
                        sportsbook_data[sportsbook_name]['markets']['spreads'] = []

                    sportsbook_data[sportsbook_name]['markets']['spreads'].append({
                        'name': outcome.get('Participant', ''),
                        'price': outcome.get('PayoutAmerican', -110),
                        'point': outcome.get('Value')
                    })

                elif bet_type == 'Moneyline':
                    if 'h2h' not in sportsbook_data[sportsbook_name]['markets']:
                        sportsbook_data[sportsbook_name]['markets']['h2h'] = []

                    sportsbook_data[sportsbook_name]['markets']['h2h'].append({
                        'name': outcome.get('Participant', ''),
                        'price': outcome.get('PayoutAmerican', 100)
                    })

                elif bet_type == 'Total Points':
                    if 'totals' not in sportsbook_data[sportsbook_name]['markets']:
                        sportsbook_data[sportsbook_name]['markets']['totals'] = []

                    sportsbook_data[sportsbook_name]['markets']['totals'].append({
                        'name': outcome.get('BettingOutcomeType', ''),  # 'Over' or 'Under'
                        'price': outcome.get('PayoutAmerican', -110),
                        'point': outcome.get('Value')
                    })

        # Convert to list format
        bookmakers = []
        for sportsbook_name, data in sportsbook_data.items():
            bookmaker = {
                'key': data['key'],
                'title': data['title'],
                'markets': []
            }

            # Convert markets dict to list
            for market_key, outcomes in data['markets'].items():
                bookmaker['markets'].append({
                    'key': market_key,
                    'outcomes': outcomes
                })

            if bookmaker['markets']:
                bookmakers.append(bookmaker)

        return bookmakers

    async def get_live_games(self) -> List[dict]:
        """
        Fetch live games from Sports Data IO for all supported leagues with individual sportsbook odds
        Returns data in same format as OddsAPIClient for compatibility
        """
        loop = asyncio.get_event_loop()
        all_games = []

        # Define leagues to fetch with their sport keys
        leagues = [
            ('NBA', 'basketball_nba', 'NBA'),
            ('NHL', 'icehockey_nhl', 'NHL'),
            ('NFL', 'americanfootball_nfl', 'NFL'),
            ('CFB', 'americanfootball_ncaaf', 'NCAAF'),
            ('CBB', 'basketball_ncaab', 'NCAAB'),
        ]

        for sport, sport_key, sport_title in leagues:
            try:
                # Fetch games for this league
                games_data = await loop.run_in_executor(
                    None,
                    lambda s=sport: self.client.get_game_odds(s, date=datetime.now().strftime('%Y-%m-%d'))
                )

                logger.info(f"[Sports Data IO] Fetched {len(games_data)} {sport_title} games")

                # Convert Sports Data IO format to OddsAPI format
                for game in games_data:
                    # Get team names - handle different field names across leagues
                    home_team = game.get('HomeTeam', game.get('HomeTeamName', ''))
                    away_team = game.get('AwayTeam', game.get('AwayTeamName', ''))

                    # Generate game ID - handle different ID field names
                    game_id = game.get('GameId') or game.get('GameID') or game.get('GlobalGameID', '')

                    # Convert to OddsAPI format
                    game_dict = {
                        'id': f"sportsdataio_{sport.lower()}_{game_id}",
                        'sport_key': sport_key,
                        'sport_title': sport_title,
                        'commence_time': game.get('DateTime', ''),
                        'home_team': home_team,
                        'away_team': away_team,
                        'bookmakers': []
                    }

                    # Try to fetch individual sportsbook odds from betting markets
                    try:
                        betting_markets = await loop.run_in_executor(
                            None,
                            lambda gid=game_id, s=sport: self.client.get_betting_markets(s, gid)
                        )

                        if betting_markets:
                            # Parse betting markets to get individual sportsbook odds
                            bookmakers = self._parse_betting_markets(betting_markets, home_team, away_team)
                            game_dict['bookmakers'] = bookmakers
                            logger.info(f"[Sports Data IO] Got {len(bookmakers)} sportsbooks for {sport_title} game {game_id}")
                        else:
                            logger.warning(f"[Sports Data IO] No betting markets found for {sport_title} game {game_id}")
                    except Exception as e:
                        logger.warning(f"[Sports Data IO] Failed to fetch betting markets for {sport_title} game {game_id}: {e}")

                    # Fall back to consensus odds if no betting markets found
                    if not game_dict['bookmakers'] and (game.get('OverUnder') or game.get('PointSpread')):
                        logger.info(f"[Sports Data IO] Using consensus odds for {sport_title} game {game_id}")
                        bookmaker = {
                            'key': 'consensus',
                            'title': 'Consensus',
                            'markets': []
                        }

                        # Add totals market
                        if game.get('OverUnder'):
                            bookmaker['markets'].append({
                                'key': 'totals',
                                'outcomes': [
                                    {
                                        'name': 'Over',
                                        'price': game.get('OverPayout', -110),
                                        'point': game.get('OverUnder')
                                    },
                                    {
                                        'name': 'Under',
                                        'price': game.get('UnderPayout', -110),
                                        'point': game.get('OverUnder')
                                    }
                                ]
                            })

                        # Add spreads market
                        if game.get('PointSpread') is not None:
                            # Handle different spread field names
                            home_spread_price = game.get('PointSpreadHomeTeamMoneyLine') or game.get('HomePointSpreadPayout', -110)
                            away_spread_price = game.get('PointSpreadAwayTeamMoneyLine') or game.get('AwayPointSpreadPayout', -110)

                            bookmaker['markets'].append({
                                'key': 'spreads',
                                'outcomes': [
                                    {
                                        'name': home_team,
                                        'price': home_spread_price,
                                        'point': game.get('PointSpread')
                                    },
                                    {
                                        'name': away_team,
                                        'price': away_spread_price,
                                        'point': -game.get('PointSpread', 0)
                                    }
                                ]
                            })

                        # Add h2h (moneyline) market
                        home_ml = game.get('HomeTeamMoneyLine') or game.get('HomeMoneyLine')
                        away_ml = game.get('AwayTeamMoneyLine') or game.get('AwayMoneyLine')
                        if home_ml or away_ml:
                            bookmaker['markets'].append({
                                'key': 'h2h',
                                'outcomes': [
                                    {
                                        'name': home_team,
                                        'price': home_ml or 100
                                    },
                                    {
                                        'name': away_team,
                                        'price': away_ml or 100
                                    }
                                ]
                            })

                        if bookmaker['markets']:
                            game_dict['bookmakers'].append(bookmaker)

                    if game_dict['bookmakers']:
                        all_games.append(game_dict)

            except Exception as e:
                logger.error(f"[Sports Data IO] Error fetching {sport_title} games: {e}", exc_info=True)
                continue

        logger.info(f"[Sports Data IO] Total games fetched across all leagues: {len(all_games)}")
        return all_games

    async def get_game_scores(self) -> dict:
        """
        Fetch game scores from Sports Data IO for all supported leagues
        Returns dict mapping game_id to score info
        """
        loop = asyncio.get_event_loop()
        scores_dict = {}

        # Define leagues to fetch
        leagues = [
            ('NBA', 'nba'),
            ('NHL', 'nhl'),
            ('NFL', 'nfl'),
            ('CFB', 'cfb'),
            ('CBB', 'cbb'),
        ]

        for sport, sport_code in leagues:
            try:
                # Fetch games for this league
                games_data = await loop.run_in_executor(
                    None,
                    lambda s=sport: self.client.get_game_odds(s, date=datetime.now().strftime('%Y-%m-%d'))
                )

                logger.info(f"[Sports Data IO Scores] Fetched {len(games_data)} {sport} games for scores")

                # Build scores dict: {game_id: {completed: bool, scores: []}}
                for game in games_data:
                    # Generate game ID - handle different ID field names
                    game_id_raw = game.get('GameId') or game.get('GameID') or game.get('GlobalGameID', '')
                    game_id = f"sportsdataio_{sport_code}_{game_id_raw}"

                    # Check game status
                    status = game.get('Status', '')
                    is_completed = status in ['Final', 'F/OT', 'Completed']
                    is_live = status in ['InProgress', 'In Progress']

                    # Extract scores - handle different field names across leagues
                    # NFL uses AwayScore/HomeScore
                    # NBA, NHL, NCAAF, NCAAB use AwayTeamScore/HomeTeamScore
                    home_score = game.get('HomeScore') or game.get('HomeTeamScore')
                    away_score = game.get('AwayScore') or game.get('AwayTeamScore')

                    # Get team names - handle different field names
                    home_team = game.get('HomeTeam', game.get('HomeTeamName', ''))
                    away_team = game.get('AwayTeam', game.get('AwayTeamName', ''))

                    # Build scores array (only if scores exist, i.e., live or completed)
                    scores = None
                    if home_score is not None and away_score is not None:
                        scores = [
                            {'name': away_team, 'score': away_score},
                            {'name': home_team, 'score': home_score}
                        ]

                    scores_dict[game_id] = {
                        'completed': is_completed,
                        'scores': scores
                    }

                    logger.info(f"[Sports Data IO Scores] {game_id}: Status={status}, Completed={is_completed}, Scores={scores}")

            except Exception as e:
                logger.error(f"[Sports Data IO Scores] Error fetching {sport} scores: {e}", exc_info=True)
                continue

        return scores_dict
