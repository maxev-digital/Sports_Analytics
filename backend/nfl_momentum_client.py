"""NFL/NCAAF Live Momentum Calculator - Advanced drive and efficiency analysis"""
import requests
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class NFLMomentumClient:
    """
    Calculate NFL/NCAAF momentum using drive-by-drive analysis from ESPN API
    Similar to NBA/NHL momentum systems but adapted for football
    """

    BASE_NFL_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
    BASE_NCAAF_URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.cache = {}

    def fetch_game_data(self, game_id: str, is_college: bool = False) -> Optional[Dict]:
        """
        Fetch play-by-play and drive data for a live game

        Args:
            game_id: ESPN game ID
            is_college: True for NCAAF, False for NFL

        Returns:
            Dict with 'plays' and 'drives' keys
        """
        try:
            base_url = self.BASE_NCAAF_URL if is_college else self.BASE_NFL_URL

            # Fetch game summary with drives
            summary_url = f"{base_url}/summary?event={game_id}"
            response = self.session.get(summary_url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract drives from summary
            drives = data.get('drives', {})

            # Also try to get play-by-play
            pbp_url = f"{base_url}/playbyplay?event={game_id}"
            pbp_response = self.session.get(pbp_url, timeout=10)

            plays_data = {}
            if pbp_response.status_code == 200:
                plays_data = pbp_response.json()

            return {
                'drives': drives,
                'plays': plays_data,
                'boxscore': data.get('boxscore', {}),
                'header': data.get('header', {})
            }
        except Exception as e:
            logger.error(f"Error fetching NFL/NCAAF game data for {game_id}: {e}")
            return None

    def calculate_recent_momentum(self, game_data: Dict, lookback_drives: int = 6) -> Dict:
        """
        Calculate momentum based on recent drives (last ~10-15 minutes of game time)

        Multi-factor formula for football:
        - Yards per play (recent drives): 35% weight
        - Scoring efficiency (TD vs FG vs Punt): 30% weight
        - Turnover differential: 20% weight
        - Red zone efficiency: 15% weight

        Returns 0-100 scale for each team
        """
        if not game_data or 'drives' not in game_data:
            return self._empty_momentum()

        drives_data = game_data.get('drives', {})
        previous_drives = drives_data.get('previous', [])

        if not previous_drives:
            return self._empty_momentum()

        # Get team IDs from header
        header = game_data.get('header', {})
        competitions = header.get('competitions', [])

        if not competitions:
            return self._empty_momentum()

        comp = competitions[0]
        competitors = comp.get('competitors', [])

        home_team_id = None
        away_team_id = None

        for competitor in competitors:
            if competitor.get('homeAway') == 'home':
                home_team_id = competitor.get('id')
            else:
                away_team_id = competitor.get('id')

        if not home_team_id or not away_team_id:
            return self._empty_momentum()

        # Analyze recent drives (last N drives)
        recent_drives = previous_drives[-lookback_drives:] if len(previous_drives) > lookback_drives else previous_drives

        # Initialize stats tracking
        home_stats = {
            'yards': 0,
            'plays': 0,
            'touchdowns': 0,
            'field_goals': 0,
            'punts': 0,
            'turnovers': 0,
            'red_zone_trips': 0,
            'red_zone_scores': 0,
            'points': 0,
            'drives': 0
        }

        away_stats = {
            'yards': 0,
            'plays': 0,
            'touchdowns': 0,
            'field_goals': 0,
            'punts': 0,
            'turnovers': 0,
            'red_zone_trips': 0,
            'red_zone_scores': 0,
            'points': 0,
            'drives': 0
        }

        # Parse recent drives
        for drive in recent_drives:
            team_id = drive.get('team', {}).get('id')

            if not team_id:
                continue

            stats = home_stats if str(team_id) == str(home_team_id) else away_stats

            # Track drive stats
            yards = drive.get('yards', 0)
            plays = drive.get('plays', 0)
            result = drive.get('result', '')

            stats['yards'] += yards
            stats['plays'] += plays
            stats['drives'] += 1

            # Scoring result
            if 'TD' in result or 'Touchdown' in result:
                stats['touchdowns'] += 1
                stats['points'] += 7  # Approximate (could be 6+PAT or 6+2PT)
            elif 'FG' in result or 'Field Goal' in result:
                stats['field_goals'] += 1
                stats['points'] += 3
            elif 'Punt' in result:
                stats['punts'] += 1
            elif 'INT' in result or 'Fumble' in result or 'Turnover' in result:
                stats['turnovers'] += 1

            # Red zone tracking (if drive reached opponent's 20-yard line)
            start_yard_line = drive.get('start', {}).get('yardLine', 0)
            end_yard_line = drive.get('end', {}).get('yardLine', 0)

            # Check if entered red zone (within 20 yards of endzone)
            if end_yard_line <= 20 and end_yard_line > 0:
                stats['red_zone_trips'] += 1
                if 'TD' in result or 'FG' in result:
                    stats['red_zone_scores'] += 1

        # Calculate momentum components

        # 1. Yards per play (35% weight) - offensive efficiency
        home_ypp = (home_stats['yards'] / max(home_stats['plays'], 1))
        away_ypp = (away_stats['yards'] / max(away_stats['plays'], 1))
        total_ypp = home_ypp + away_ypp

        if total_ypp > 0:
            home_ypp_momentum = (home_ypp / total_ypp) * 100
            away_ypp_momentum = (away_ypp / total_ypp) * 100
        else:
            home_ypp_momentum = away_ypp_momentum = 50

        # 2. Scoring efficiency (30% weight) - TDs worth more than FGs
        home_scoring = (home_stats['touchdowns'] * 7 + home_stats['field_goals'] * 3)
        away_scoring = (away_stats['touchdowns'] * 7 + away_stats['field_goals'] * 3)
        total_scoring = home_scoring + away_scoring

        if total_scoring > 0:
            home_scoring_momentum = (home_scoring / total_scoring) * 100
            away_scoring_momentum = (away_scoring / total_scoring) * 100
        else:
            home_scoring_momentum = away_scoring_momentum = 50

        # 3. Turnover differential (20% weight) - fewer is better
        home_to_diff = away_stats['turnovers'] - home_stats['turnovers']
        away_to_diff = home_stats['turnovers'] - away_stats['turnovers']
        total_turnovers = home_stats['turnovers'] + away_stats['turnovers']

        if total_turnovers > 0:
            # Team with fewer turnovers gets momentum boost
            if home_stats['turnovers'] < away_stats['turnovers']:
                home_to_momentum = 70
                away_to_momentum = 30
            elif away_stats['turnovers'] < home_stats['turnovers']:
                home_to_momentum = 30
                away_to_momentum = 70
            else:
                home_to_momentum = away_to_momentum = 50
        else:
            home_to_momentum = away_to_momentum = 50

        # 4. Red zone efficiency (15% weight)
        home_rz_pct = (home_stats['red_zone_scores'] / max(home_stats['red_zone_trips'], 1)) if home_stats['red_zone_trips'] > 0 else 0
        away_rz_pct = (away_stats['red_zone_scores'] / max(away_stats['red_zone_trips'], 1)) if away_stats['red_zone_trips'] > 0 else 0
        total_rz = home_rz_pct + away_rz_pct

        if total_rz > 0:
            home_rz_momentum = (home_rz_pct / total_rz) * 100
            away_rz_momentum = (away_rz_pct / total_rz) * 100
        else:
            home_rz_momentum = away_rz_momentum = 50

        # Weighted momentum formula
        home_momentum = (
            home_ypp_momentum * 0.35 +
            home_scoring_momentum * 0.30 +
            home_to_momentum * 0.20 +
            home_rz_momentum * 0.15
        )

        away_momentum = (
            away_ypp_momentum * 0.35 +
            away_scoring_momentum * 0.30 +
            away_to_momentum * 0.20 +
            away_rz_momentum * 0.15
        )

        # Determine drive state indicator
        home_drive_state = 'NEUTRAL'
        away_drive_state = 'NEUTRAL'

        # Check current drive from boxscore or most recent drive
        if recent_drives:
            last_drive = recent_drives[-1]
            last_drive_team = str(last_drive.get('team', {}).get('id', ''))

            if last_drive_team == str(home_team_id):
                home_drive_state = 'ATTACKING'
                away_drive_state = 'DEFENDING'
            elif last_drive_team == str(away_team_id):
                away_drive_state = 'ATTACKING'
                home_drive_state = 'DEFENDING'

        return {
            'home': {
                'momentum_score': round(home_momentum, 1),
                'yards_per_play': round(home_ypp, 1),
                'recent_yards': home_stats['yards'],
                'recent_points': home_stats['points'],
                'touchdowns': home_stats['touchdowns'],
                'field_goals': home_stats['field_goals'],
                'turnovers': home_stats['turnovers'],
                'red_zone_efficiency': f"{home_stats['red_zone_scores']}/{home_stats['red_zone_trips']}" if home_stats['red_zone_trips'] > 0 else "0/0",
                'drive_state': home_drive_state
            },
            'away': {
                'momentum_score': round(away_momentum, 1),
                'yards_per_play': round(away_ypp, 1),
                'recent_yards': away_stats['yards'],
                'recent_points': away_stats['points'],
                'touchdowns': away_stats['touchdowns'],
                'field_goals': away_stats['field_goals'],
                'turnovers': away_stats['turnovers'],
                'red_zone_efficiency': f"{away_stats['red_zone_scores']}/{away_stats['red_zone_trips']}" if away_stats['red_zone_trips'] > 0 else "0/0",
                'drive_state': away_drive_state
            },
            'lookback_drives': len(recent_drives)
        }

    def _empty_momentum(self) -> Dict:
        """Return empty momentum data structure"""
        return {
            'home': {
                'momentum_score': 50.0,
                'yards_per_play': 0.0,
                'recent_yards': 0,
                'recent_points': 0,
                'touchdowns': 0,
                'field_goals': 0,
                'turnovers': 0,
                'red_zone_efficiency': '0/0',
                'drive_state': 'NEUTRAL'
            },
            'away': {
                'momentum_score': 50.0,
                'yards_per_play': 0.0,
                'recent_yards': 0,
                'recent_points': 0,
                'touchdowns': 0,
                'field_goals': 0,
                'turnovers': 0,
                'red_zone_efficiency': '0/0',
                'drive_state': 'NEUTRAL'
            },
            'lookback_drives': 0
        }

    def get_live_momentum(self, game_id: str, is_college: bool = False) -> Optional[Dict]:
        """
        Main method to get live momentum for a game

        Args:
            game_id: ESPN game ID
            is_college: True for NCAAF, False for NFL

        Returns:
            Dict with home/away momentum stats
        """
        game_data = self.fetch_game_data(game_id, is_college)
        if not game_data:
            return None

        momentum = self.calculate_recent_momentum(game_data)
        return momentum
