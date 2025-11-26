"""
ESPN NCAAB API Client - Free live game data and box scores

Provides:
- Live game scoreboard (all games for a date)
- Detailed game summary with full box scores
- Live statistics (FG, 3PT, FT, rebounds, turnovers, etc.)

Based on ESPN's public basketball API endpoints
"""

import httpx
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ESPNNCAABClient:
    """Client for ESPN NCAAB live game data"""

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"

    def __init__(self):
        self.timeout = 10.0

    async def get_scoreboard(self, date: str = None) -> Optional[Dict]:
        """
        Get live scoreboard for all NCAAB games

        Args:
            date: Date string in YYYYMMDD format (e.g., '20251121')
                  If None, uses today's date

        Returns:
            Dict with all games including live status, scores, and event IDs
        """
        try:
            if not date:
                date = datetime.now().strftime("%Y%m%d")

            url = f"{self.BASE_URL}/scoreboard?dates={date}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                logger.info(f"Fetched NCAAB scoreboard: {len(data.get('events', []))} games on {date}")
                return data

        except Exception as e:
            logger.error(f"Error fetching NCAAB scoreboard: {e}")
            return None

    async def get_game_summary(self, event_id: str) -> Optional[Dict]:
        """
        Get detailed game summary including full box scores

        Args:
            event_id: ESPN event ID from scoreboard

        Returns:
            Dict with complete game data including box scores
        """
        try:
            url = f"{self.BASE_URL}/summary?event={event_id}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                logger.info(f"Fetched game summary for event {event_id}")
                return data

        except Exception as e:
            logger.error(f"Error fetching game summary for {event_id}: {e}")
            return None

    def parse_live_box_score(self, summary_data: Dict) -> Optional[Dict]:
        """
        Extract clean live statistics from ESPN summary response

        Returns:
            Dict with parsed stats for both teams
        """
        try:
            if 'boxscore' not in summary_data:
                logger.warning("No boxscore in summary data")
                return None

            boxscore = summary_data['boxscore']
            teams = boxscore.get('teams', [])

            if len(teams) < 2:
                logger.warning("Incomplete team data in boxscore")
                return None

            # Parse game status from header
            header = summary_data.get('header', {})
            competitions = header.get('competitions', [{}])
            status = competitions[0].get('status', {})

            period = status.get('period', 0)
            clock = status.get('displayClock', '0:00')
            status_detail = status.get('type', {}).get('detail', 'Unknown')
            is_live = status.get('type', {}).get('state') == 'in'

            def extract_team_stats(team_data: Dict) -> Dict:
                """Extract stats from single team's data"""
                team_info = team_data.get('team', {})
                # Extract school name from displayName (e.g., 'Cincinnati Bearcats' -> 'Cincinnati')
                display_name = team_info.get('displayName', '')
                if display_name and ' ' in display_name:
                    team_name = ' '.join(display_name.split()[:-1])  # Remove last word (mascot)
                else:
                    team_name = team_info.get('location') or team_info.get('name', 'Unknown')
                team_abv = team_info.get('abbreviation', 'UNK')
                points = int(team_data.get('score', 0))

                # Build stats dict
                stats_raw = {s['name']: s.get('displayValue', '0')
                           for s in team_data.get('statistics', [])}

                # Parse made-attempted strings
                def parse_made_att(stat_str: str) -> tuple:
                    try:
                        parts = stat_str.split('-')
                        return int(parts[0]), int(parts[1])
                    except:
                        return 0, 0

                fg_made, fg_att = parse_made_att(stats_raw.get('fieldGoalsMade-fieldGoalsAttempted', '0-0'))
                three_made, three_att = parse_made_att(stats_raw.get('threePointFieldGoalsMade-threePointFieldGoalsAttempted', '0-0'))
                ft_made, ft_att = parse_made_att(stats_raw.get('freeThrowsMade-freeThrowsAttempted', '0-0'))

                return {
                    'team_name': team_name,
                    'team_abv': team_abv,
                    'points': points,
                    'fg_made': fg_made,
                    'fg_att': fg_att,
                    'three_made': three_made,
                    'three_att': three_att,
                    'ft_made': ft_made,
                    'ft_att': ft_att,
                    'turnovers': int(stats_raw.get('turnovers', 0)),
                    'off_rebounds': int(stats_raw.get('offensiveRebounds', 0)),
                    'def_rebounds': int(stats_raw.get('defensiveRebounds', 0)),
                    'total_rebounds': int(stats_raw.get('totalRebounds', 0))
                }

            home_team = extract_team_stats(teams[0])
            away_team = extract_team_stats(teams[1])

            result = {
                'home': home_team,
                'away': away_team,
                'period': period,
                'clock': clock,
                'status': status_detail,
                'is_live': is_live
            }

            logger.info(f"Parsed box score: {home_team['team_name']} {home_team['points']} - {away_team['team_name']} {away_team['points']}")
            return result

        except Exception as e:
            logger.error(f"Error parsing box score: {e}")
            return None

    async def get_live_box_score(self, event_id: str) -> Optional[Dict]:
        """
        Convenience method: Get and parse live box score in one call
        """
        summary = await self.get_game_summary(event_id)
        if not summary:
            return None

        return self.parse_live_box_score(summary)
