"""NBA Live Scoreboard Client for real-time game clock data"""
from nba_api.live.nba.endpoints import scoreboard
import logging
from typing import Optional, Dict, List
import re

logger = logging.getLogger(__name__)

class NBALiveClient:
    """Client for fetching live NBA game data including quarter and time"""

    def __init__(self):
        self.scoreboard_cache = {}

    def fetch_live_scoreboard(self) -> Dict:
        """Fetch current live scoreboard data"""
        try:
            sb = scoreboard.ScoreBoard()
            data = sb.get_dict()

            # Build lookup by team names
            scoreboard_lookup = {}
            for game in data.get('scoreboard', {}).get('games', []):
                home_team = game.get('homeTeam', {})
                away_team = game.get('awayTeam', {})

                home_city = home_team.get('teamCity', '')
                home_name = home_team.get('teamName', '')
                away_city = away_team.get('teamCity', '')
                away_name = away_team.get('teamName', '')

                # Create full team names
                home_full = f"{home_city} {home_name}".strip()
                away_full = f"{away_city} {away_name}".strip()

                game_info = {
                    'game_id': game.get('gameId'),
                    'period': game.get('period', 0),
                    'game_clock': game.get('gameClock', ''),
                    'game_status': game.get('gameStatus', 0),  # 1=not started, 2=live, 3=final
                    'game_status_text': game.get('gameStatusText', ''),
                    'home_score': home_team.get('score', 0),
                    'away_score': away_team.get('score', 0),
                    'home_team': home_full,
                    'away_team': away_full
                }

                # Store by both team names for easier lookup
                scoreboard_lookup[home_full] = game_info
                scoreboard_lookup[away_full] = game_info

                # Also store shortened versions
                scoreboard_lookup[home_name] = game_info
                scoreboard_lookup[away_name] = game_info

            self.scoreboard_cache = scoreboard_lookup
            logger.info(f"Fetched live scoreboard with {len(data.get('scoreboard', {}).get('games', []))} games")
            return scoreboard_lookup

        except Exception as e:
            logger.error(f"Error fetching live scoreboard: {e}", exc_info=True)
            return {}

    def fetch_schedule(self) -> List[Dict]:
        """
        Fetch NBA schedule for upcoming and live games
        
        Returns list of games with:
        - home_team: str
        - away_team: str
        - commence_time: str (ISO format)
        - status: str ('upcoming' or 'live')
        - game_id: str
        """
        try:
            sb = scoreboard.ScoreBoard()
            data = sb.get_dict()
            
            games = []
            for game in data.get('scoreboard', {}).get('games', []):
                try:
                    home_team = game.get('homeTeam', {})
                    away_team = game.get('awayTeam', {})
                    
                    home_city = home_team.get('teamCity', '')
                    home_name = home_team.get('teamName', '')
                    away_city = away_team.get('teamCity', '')
                    away_name = away_team.get('teamName', '')
                    
                    # Create full team names
                    home_full = f"{home_city} {home_name}".strip()
                    away_full = f"{away_city} {away_name}".strip()
                    
                    # Get game status
                    game_status = game.get('gameStatus', 0)  # 1=not started, 2=live, 3=final
                    
                    # Skip completed games
                    if game_status == 3:
                        continue
                    
                    # Get commence time
                    commence_time = game.get('gameTimeUTC', '')
                    
                    games.append({
                        'home_team': home_full,
                        'away_team': away_full,
                        'commence_time': commence_time,
                        'status': 'live' if game_status == 2 else 'upcoming',
                        'game_id': game.get('gameId'),
                        'sport_key': 'basketball_nba'
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing NBA game: {e}")
                    continue
            
            logger.info(f"Fetched {len(games)} NBA games from schedule")
            return games
            
        except Exception as e:
            logger.error(f"Error fetching NBA schedule: {e}", exc_info=True)
            return []

    def parse_game_clock(self, clock_string: str) -> str:
        """
        Convert ISO 8601 duration format to MM:SS format

        Examples:
        - "PT12M34.56S" -> "12:34"
        - "PT00M00.00S" -> "0:00"
        - "PT05M23.40S" -> "5:23"
        """
        if not clock_string or clock_string == "":
            return "0:00"

        try:
            # Parse ISO 8601 duration: PT12M34.56S
            # Pattern: PT(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?
            match = re.match(r'PT(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?', clock_string)
            if not match:
                return "0:00"

            minutes = int(match.group(1)) if match.group(1) else 0
            seconds = int(float(match.group(2))) if match.group(2) else 0

            return f"{minutes}:{seconds:02d}"

        except Exception as e:
            logger.warning(f"Error parsing game clock '{clock_string}': {e}")
            return "0:00"

    def get_game_info(self, team_name: str) -> Optional[Dict]:
        """
        Get live game info for a team

        Returns dict with:
        - period: Current quarter (1-4+)
        - time_remaining: Time in "MM:SS" format
        - is_live: Boolean if game is currently live
        - home_score: Home team score
        - away_score: Away team score
        """
        if team_name not in self.scoreboard_cache:
            return None

        game = self.scoreboard_cache[team_name]

        return {
            'period': game['period'],
            'time_remaining': self.parse_game_clock(game['game_clock']),
            'is_live': game['game_status'] == 2,
            'is_final': game['game_status'] == 3,
            'home_score': game['home_score'],
            'away_score': game['away_score'],
            'home_team': game['home_team'],
            'away_team': game['away_team']
        }
