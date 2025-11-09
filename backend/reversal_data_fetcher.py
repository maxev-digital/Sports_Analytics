"""
Basketball Reversal Strategy - Historical Data Fetcher
Fetches quarter-by-quarter scores for 2023-2024 season across all leagues
"""

import httpx
import asyncio
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path(__file__).parent / "data" / "reversal_backtesting"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class BasketballDataFetcher:
    """Fetch quarter-by-quarter data from multiple basketball leagues"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_nba_games(self, season="2023-24") -> List[Dict]:
        """
        Fetch NBA games with quarter scores using ESPN API
        Season: 2023-24 (1,230 games)
        """
        logger.info(f"Fetching NBA games for {season}...")

        all_games = []

        # NBA season runs Oct 2023 - June 2024
        start_date = datetime(2023, 10, 1)
        end_date = datetime(2024, 6, 30)

        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime("%Y%m%d")

            try:
                # ESPN scoreboard API
                url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str}"
                response = await self.client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    events = data.get('events', [])

                    for event in events:
                        game = await self._parse_nba_game(event)
                        if game and game.get('quarters'):
                            all_games.append(game)

                    if events:
                        logger.info(f"  {date_str}: Found {len(events)} games")

            except Exception as e:
                logger.error(f"  Error fetching {date_str}: {e}")

            current_date += timedelta(days=1)

            # Rate limiting
            await asyncio.sleep(0.1)

        logger.info(f"Fetched {len(all_games)} NBA games with quarter scores")
        return all_games

    async def _parse_nba_game(self, event: Dict) -> Optional[Dict]:
        """Parse NBA game event into quarter scores"""
        try:
            game_id = event.get('id')
            competitions = event.get('competitions', [{}])[0]

            # Check if game is final
            status = competitions.get('status', {}).get('type', {}).get('name', '')
            if status != 'STATUS_FINAL':
                return None

            competitors = competitions.get('competitors', [])
            if len(competitors) != 2:
                return None

            home_team = next((c for c in competitors if c.get('homeAway') == 'home'), None)
            away_team = next((c for c in competitors if c.get('homeAway') == 'away'), None)

            if not home_team or not away_team:
                return None

            # Fetch detailed game data for quarter scores
            summary_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}"
            summary_response = await self.client.get(summary_url)

            if summary_response.status_code != 200:
                return None

            summary_data = summary_response.json()
            boxscore = summary_data.get('boxscore', {})
            teams = boxscore.get('teams', [])

            if len(teams) != 2:
                return None

            # Extract quarter scores
            away_box = next((t for t in teams if t.get('homeAway') == 'away'), None)
            home_box = next((t for t in teams if t.get('homeAway') == 'home'), None)

            if not away_box or not home_box:
                return None

            away_linescore = away_box.get('statistics', [{}])[0].get('linescores', [])
            home_linescore = home_box.get('statistics', [{}])[0].get('linescores', [])

            if not away_linescore or not home_linescore:
                return None

            quarters = {}
            for i in range(min(len(away_linescore), len(home_linescore))):
                q_num = i + 1
                q_key = f'Q{q_num}' if q_num <= 4 else f'OT{q_num - 4}'
                quarters[q_key] = {
                    'home': int(home_linescore[i].get('value', 0)),
                    'away': int(away_linescore[i].get('value', 0))
                }

            game_date = event.get('date', '')

            return {
                'game_id': game_id,
                'date': game_date,
                'league': 'NBA',
                'home_team': home_team.get('team', {}).get('displayName', ''),
                'away_team': away_team.get('team', {}).get('displayName', ''),
                'home_score': int(home_team.get('score', 0)),
                'away_score': int(away_team.get('score', 0)),
                'quarters': quarters
            }

        except Exception as e:
            logger.error(f"Error parsing NBA game: {e}")
            return None

    async def fetch_ncaa_games(self, season="2023-24") -> List[Dict]:
        """
        Fetch NCAA Men's Basketball games with quarter scores
        Season: 2023-24 (~5,437 games)
        """
        logger.info(f"Fetching NCAA Men's games for {season}...")

        all_games = []

        # NCAA season runs Nov 2023 - Apr 2024
        start_date = datetime(2023, 11, 1)
        end_date = datetime(2024, 4, 30)

        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime("%Y%m%d")

            try:
                # ESPN NCAA scoreboard
                url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={date_str}"
                response = await self.client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    events = data.get('events', [])

                    for event in events:
                        game = await self._parse_ncaa_game(event)
                        if game and game.get('quarters'):
                            all_games.append(game)

                    if events:
                        logger.info(f"  {date_str}: Found {len(events)} NCAA games")

            except Exception as e:
                logger.error(f"  Error fetching NCAA {date_str}: {e}")

            current_date += timedelta(days=1)
            await asyncio.sleep(0.1)

        logger.info(f"Fetched {len(all_games)} NCAA games")
        return all_games

    async def _parse_ncaa_game(self, event: Dict) -> Optional[Dict]:
        """Parse NCAA game (similar to NBA but adapted for college basketball)"""
        try:
            game_id = event.get('id')
            competitions = event.get('competitions', [{}])[0]

            status = competitions.get('status', {}).get('type', {}).get('name', '')
            if status != 'STATUS_FINAL':
                return None

            competitors = competitions.get('competitors', [])
            if len(competitors) != 2:
                return None

            home_team = next((c for c in competitors if c.get('homeAway') == 'home'), None)
            away_team = next((c for c in competitors if c.get('homeAway') == 'away'), None)

            # Get quarter scores from linescore
            home_linescore = home_team.get('linescores', [])
            away_linescore = away_team.get('linescores', [])

            if not home_linescore or not away_linescore:
                return None

            quarters = {}
            for i in range(min(len(home_linescore), len(away_linescore))):
                # NCAA uses halves typically, but some data has quarters
                q_num = i + 1
                q_key = f'Q{q_num}' if q_num <= 4 else f'OT{q_num - 4}'
                quarters[q_key] = {
                    'home': int(home_linescore[i].get('value', 0)),
                    'away': int(away_linescore[i].get('value', 0))
                }

            return {
                'game_id': game_id,
                'date': event.get('date', ''),
                'league': 'NCAA',
                'home_team': home_team.get('team', {}).get('displayName', ''),
                'away_team': away_team.get('team', {}).get('displayName', ''),
                'home_score': int(home_team.get('score', 0)),
                'away_score': int(away_team.get('score', 0)),
                'quarters': quarters
            }

        except Exception as e:
            logger.error(f"Error parsing NCAA game: {e}")
            return None

    async def fetch_euroleague_games(self, season="2023-24") -> List[Dict]:
        """
        Fetch Euroleague games (306 games)
        Note: Euroleague API access is limited - using ESPN as fallback
        """
        logger.info(f"Fetching Euroleague games for {season}...")

        # Euroleague runs Oct 2023 - May 2024
        # ESPN may have limited coverage - this is a placeholder
        logger.warning("Euroleague data fetching is limited - ESPN coverage varies")

        return []  # TODO: Implement Euroleague API when available

    async def save_to_csv(self, games: List[Dict], filename: str):
        """Save games to CSV"""
        if not games:
            logger.warning(f"No games to save for {filename}")
            return

        # Flatten quarters into columns
        rows = []
        for game in games:
            row = {
                'game_id': game['game_id'],
                'date': game['date'],
                'league': game['league'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'home_score': game['home_score'],
                'away_score': game['away_score']
            }

            # Add quarter scores
            quarters = game.get('quarters', {})
            for q in ['Q1', 'Q2', 'Q3', 'Q4', 'OT']:
                if q in quarters:
                    row[f'{q}_home'] = quarters[q]['home']
                    row[f'{q}_away'] = quarters[q]['away']
                else:
                    row[f'{q}_home'] = None
                    row[f'{q}_away'] = None

            rows.append(row)

        df = pd.DataFrame(rows)
        filepath = DATA_DIR / filename
        df.to_csv(filepath, index=False)
        logger.info(f"Saved {len(df)} games to {filepath}")


async def main():
    """Main execution"""
    fetcher = BasketballDataFetcher()

    # Fetch NBA games
    nba_games = await fetcher.fetch_nba_games("2023-24")
    await fetcher.save_to_csv(nba_games, "nba_2023_24.csv")

    # Fetch NCAA games
    ncaa_games = await fetcher.fetch_ncaa_games("2023-24")
    await fetcher.save_to_csv(ncaa_games, "ncaa_2023_24.csv")

    # Summary
    logger.info("\n=== DATA COLLECTION COMPLETE ===")
    logger.info(f"NBA games: {len(nba_games)}")
    logger.info(f"NCAA games: {len(ncaa_games)}")
    logger.info(f"Total: {len(nba_games) + len(ncaa_games)}")


if __name__ == "__main__":
    asyncio.run(main())
