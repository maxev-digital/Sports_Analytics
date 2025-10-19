"""Odds API Client"""
import httpx
from typing import List
from live_models import GameState, GameOdds, Team
from config import ODDS_API_KEY, ODDS_API_BASE, SPORTS, REGION, MARKETS
import logging

logger = logging.getLogger(__name__)

class OddsAPIClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = ODDS_API_BASE

    async def get_live_games(self) -> List[dict]:
        """Fetch games from all configured sports"""
        all_games = []

        for sport in SPORTS:
            url = f"{self.base_url}/sports/{sport}/odds"
            params = {
                "apiKey": ODDS_API_KEY,
                "regions": REGION,
                "markets": MARKETS,
                "oddsFormat": "american"
            }

            try:
                response = await self.client.get(url, params=params)
                response.raise_for_status()

                # Log API usage (only once)
                if sport == SPORTS[0]:
                    remaining = response.headers.get('x-requests-remaining', 'unknown')
                    logger.info(f"API requests remaining: {remaining}")

                games = response.json()
                # Add sport key to each game
                for game in games:
                    game['sport_key'] = sport
                all_games.extend(games)

            except Exception as e:
                logger.error(f"Error fetching odds for {sport}: {e}")

        return all_games

    async def get_game_scores(self) -> dict:
        """Fetch live scores from all configured sports"""
        all_scores = {}

        for sport in SPORTS:
            url = f"{self.base_url}/sports/{sport}/scores"
            params = {
                "apiKey": ODDS_API_KEY,
                "daysFrom": 1
            }

            try:
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                scores_list = response.json()
                # Convert list to dict, keyed by game ID
                for game in scores_list:
                    if game and 'id' in game:
                        all_scores[game['id']] = game
            except Exception as e:
                logger.error(f"Error fetching scores for {sport}: {e}")

        return all_scores
    
    async def close(self):
        await self.client.aclose()
