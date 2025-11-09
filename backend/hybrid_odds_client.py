"""
Hybrid Odds Client - Merges data from The Odds API and Sports Data IO
Provides maximum sportsbook coverage with source tracking
"""
import asyncio
from typing import List, Dict
import logging
from odds_client import OddsAPIClient
from sportsdataio_odds_client import SportsDataIOOddsClient

logger = logging.getLogger(__name__)


class HybridOddsClient:
    """
    Combines The Odds API and Sports Data IO for maximum coverage

    Strategy:
    1. Fetch from both APIs concurrently
    2. Use Sports Data IO data where available (faster, includes weather/channel)
    3. Supplement with additional sportsbooks from The Odds API
    4. Track source for each sportsbook
    """

    def __init__(self):
        self.odds_api_client = OddsAPIClient()
        self.sportsdataio_client = SportsDataIOOddsClient()
        logger.info("Initialized Hybrid Odds Client (Odds API + Sports Data IO)")

    def _normalize_bookmaker_key(self, key: str) -> str:
        """Normalize bookmaker keys for comparison"""
        return key.lower().replace('_', '').replace(' ', '').replace('-', '')

    def _merge_game_data(self, sportsdataio_game: dict, oddsapi_game: dict) -> dict:
        """
        Merge game data from both sources

        Priority:
        1. Use Sports Data IO for channel, weather, and primary bookmakers
        2. Add unique bookmakers from Odds API
        3. Track source for each bookmaker
        """
        # Start with Sports Data IO data (includes channel, weather)
        merged_game = sportsdataio_game.copy()

        # Get existing bookmaker keys from Sports Data IO
        sdi_bookmakers = {
            self._normalize_bookmaker_key(book['key']): book
            for book in sportsdataio_game.get('bookmakers', [])
        }

        # Add source tag to Sports Data IO bookmakers
        for book in merged_game.get('bookmakers', []):
            book['source'] = 'SportsDataIO'
            book['source_speed'] = 'fast'

        # Add bookmakers from Odds API that aren't in Sports Data IO
        odds_api_bookmakers = oddsapi_game.get('bookmakers', [])
        added_count = 0

        for odds_book in odds_api_bookmakers:
            normalized_key = self._normalize_bookmaker_key(odds_book['key'])

            # If this bookmaker isn't in Sports Data IO data, add it
            if normalized_key not in sdi_bookmakers:
                odds_book_copy = odds_book.copy()
                odds_book_copy['source'] = 'OddsAPI'
                odds_book_copy['source_speed'] = 'standard'
                merged_game['bookmakers'].append(odds_book_copy)
                added_count += 1

        if added_count > 0:
            logger.info(f"[Hybrid] Added {added_count} additional sportsbooks from Odds API to game {merged_game['id']}")

        return merged_game

    def _match_games(self, sdi_games: List[dict], oddsapi_games: List[dict]) -> List[tuple]:
        """
        Match games from both sources by teams and time

        Returns list of tuples: (sdi_game, oddsapi_game or None)
        """
        matched_games = []
        used_oddsapi_indices = set()

        for sdi_game in sdi_games:
            sdi_home = sdi_game['home_team'].lower().replace(' ', '')
            sdi_away = sdi_game['away_team'].lower().replace(' ', '')

            # Try to find matching Odds API game
            match_found = False
            for i, oa_game in enumerate(oddsapi_games):
                if i in used_oddsapi_indices:
                    continue

                oa_home = oa_game['home_team'].lower().replace(' ', '')
                oa_away = oa_game['away_team'].lower().replace(' ', '')

                # Match by teams
                if (sdi_home in oa_home or oa_home in sdi_home) and \
                   (sdi_away in oa_away or oa_away in sdi_away):
                    matched_games.append((sdi_game, oa_game))
                    used_oddsapi_indices.add(i)
                    match_found = True
                    break

            if not match_found:
                # SDI game has no Odds API match, use SDI only
                matched_games.append((sdi_game, None))

        # Add any unmatched Odds API games
        for i, oa_game in enumerate(oddsapi_games):
            if i not in used_oddsapi_indices:
                # Tag all bookmakers as from Odds API
                for book in oa_game.get('bookmakers', []):
                    book['source'] = 'OddsAPI'
                    book['source_speed'] = 'standard'
                matched_games.append((None, oa_game))

        return matched_games

    async def get_live_games(self) -> List[dict]:
        """
        Fetch games from both APIs and merge

        Returns unified list with source tracking
        """
        try:
            # Fetch from both APIs concurrently
            logger.info("[Hybrid] Fetching from both Odds API and Sports Data IO...")

            sdi_task = self.sportsdataio_client.get_live_games()
            oddsapi_task = self.odds_api_client.get_live_games()

            sdi_games, oddsapi_games = await asyncio.gather(sdi_task, oddsapi_task)

            logger.info(f"[Hybrid] Sports Data IO returned {len(sdi_games)} games")
            logger.info(f"[Hybrid] Odds API returned {len(oddsapi_games)} games")

            # Match and merge games
            matched_games = self._match_games(sdi_games, oddsapi_games)

            merged_games = []
            for sdi_game, oa_game in matched_games:
                if sdi_game and oa_game:
                    # Merge data from both sources
                    merged_game = self._merge_game_data(sdi_game, oa_game)
                    merged_games.append(merged_game)
                elif sdi_game:
                    # SDI only - add source tags
                    for book in sdi_game.get('bookmakers', []):
                        book['source'] = 'SportsDataIO'
                        book['source_speed'] = 'fast'
                    merged_games.append(sdi_game)
                elif oa_game:
                    # Odds API only - already tagged
                    merged_games.append(oa_game)

            # Calculate statistics
            total_bookmakers = sum(len(game.get('bookmakers', [])) for game in merged_games)
            sdi_bookmakers = sum(
                len([b for b in game.get('bookmakers', []) if b.get('source') == 'SportsDataIO'])
                for game in merged_games
            )
            oa_bookmakers = total_bookmakers - sdi_bookmakers

            logger.info(f"[Hybrid] Merged result: {len(merged_games)} games, "
                       f"{total_bookmakers} total sportsbooks "
                       f"({sdi_bookmakers} from SDI, {oa_bookmakers} from Odds API)")

            return merged_games

        except Exception as e:
            logger.error(f"[Hybrid] Error fetching games: {e}", exc_info=True)
            # Fallback to Sports Data IO only
            logger.warning("[Hybrid] Falling back to Sports Data IO only")
            return await self.sportsdataio_client.get_live_games()

    async def get_game_scores(self) -> dict:
        """
        Get game scores - use Sports Data IO (faster for scores)
        """
        return await self.sportsdataio_client.get_game_scores()
