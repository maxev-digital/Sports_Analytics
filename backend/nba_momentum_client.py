"""NBA Live Momentum Calculator - Advanced play-by-play analysis"""
from nba_api.live.nba.endpoints import playbyplay, boxscore
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class NBAMomentumClient:
    """
    Calculate NBA momentum using play-by-play data
    Similar to NHL momentum system but adapted for basketball
    """

    def __init__(self):
        self.cache = {}
        self.cache_timestamp = None

    def fetch_game_data(self, game_id: str) -> Optional[Dict]:
        """
        Fetch play-by-play and boxscore data for a live game

        Args:
            game_id: NBA game ID (e.g., "0022400123")

        Returns:
            Dict with 'play_by_play' and 'boxscore' keys
        """
        try:
            # Fetch play-by-play
            pbp = playbyplay.PlayByPlay(game_id)
            pbp_data = pbp.get_dict()

            # Fetch boxscore for additional stats
            box = boxscore.BoxScore(game_id)
            box_data = box.get_dict()

            return {
                'play_by_play': pbp_data,
                'boxscore': box_data
            }
        except Exception as e:
            logger.error(f"Error fetching NBA game data for {game_id}: {e}")
            return None

    def calculate_recent_momentum(self, pbp_data: Dict, lookback_minutes: int = 5) -> Dict:
        """
        Calculate momentum based on recent plays (last N minutes)

        Multi-factor formula:
        - Field Goal % (recent possessions): 40% weight
        - Scoring Run (points in last N min): 30% weight
        - Rebounds (offensive boards): 15% weight
        - Turnovers (forced vs committed): 15% weight

        Returns 0-100 scale for each team
        """
        if not pbp_data or 'game' not in pbp_data:
            return self._empty_momentum()

        game = pbp_data.get('game', {})
        actions = game.get('actions', [])

        if not actions:
            return self._empty_momentum()

        # Get current period and clock to determine recent plays
        current_period = game.get('period', 1)

        # Take last 50 actions as proxy for last ~5 minutes
        recent_plays = actions[-50:] if len(actions) > 50 else actions

        # Initialize stats tracking
        home_stats = {
            'points': 0,
            'fgm': 0,  # Field goals made
            'fga': 0,  # Field goals attempted
            'offensive_rebounds': 0,
            'defensive_rebounds': 0,
            'turnovers': 0,
            'steals': 0,
            'assists': 0
        }

        away_stats = {
            'points': 0,
            'fgm': 0,
            'fga': 0,
            'offensive_rebounds': 0,
            'defensive_rebounds': 0,
            'turnovers': 0,
            'steals': 0,
            'assists': 0
        }

        home_team_id = game.get('homeTeam', {}).get('teamId')
        away_team_id = game.get('awayTeam', {}).get('teamId')

        # Parse recent plays
        for action in recent_plays:
            action_type = action.get('actionType', '')
            team_id = action.get('teamId')
            sub_type = action.get('subType', '')
            points = action.get('pointsTotal', 0)

            stats = home_stats if team_id == home_team_id else away_stats
            opp_stats = away_stats if team_id == home_team_id else home_stats

            # Track field goals
            if action_type == 'SHOT':
                if action.get('shotResult') == 'Made':
                    stats['fgm'] += 1
                    stats['fga'] += 1
                    stats['points'] += action.get('pointsTotal', 0)
                else:
                    stats['fga'] += 1

            # Track rebounds
            elif action_type == 'REBOUND':
                if sub_type == 'offensive':
                    stats['offensive_rebounds'] += 1
                else:
                    stats['defensive_rebounds'] += 1

            # Track turnovers
            elif action_type == 'TURNOVER':
                stats['turnovers'] += 1

            # Track steals
            elif action_type == 'STEAL':
                stats['steals'] += 1
                # Also count as opponent turnover
                opp_stats['turnovers'] += 1

            # Track assists
            elif action_type == 'ASSIST':
                stats['assists'] += 1

        # Calculate momentum components

        # 1. Field Goal % (40% weight)
        home_fg_pct = (home_stats['fgm'] / max(home_stats['fga'], 1)) * 100
        away_fg_pct = (away_stats['fgm'] / max(away_stats['fga'], 1)) * 100
        total_fg = home_fg_pct + away_fg_pct
        if total_fg > 0:
            home_fg_momentum = (home_fg_pct / total_fg) * 100
            away_fg_momentum = (away_fg_pct / total_fg) * 100
        else:
            home_fg_momentum = away_fg_momentum = 50

        # 2. Scoring Run (30% weight)
        total_points = home_stats['points'] + away_stats['points']
        if total_points > 0:
            home_scoring_momentum = (home_stats['points'] / total_points) * 100
            away_scoring_momentum = (away_stats['points'] / total_points) * 100
        else:
            home_scoring_momentum = away_scoring_momentum = 50

        # 3. Rebounding (15% weight) - offensive rebounds are key
        total_off_reb = home_stats['offensive_rebounds'] + away_stats['offensive_rebounds']
        if total_off_reb > 0:
            home_reb_momentum = (home_stats['offensive_rebounds'] / total_off_reb) * 100
            away_reb_momentum = (away_stats['offensive_rebounds'] / total_off_reb) * 100
        else:
            # Fall back to defensive rebounds
            total_def_reb = home_stats['defensive_rebounds'] + away_stats['defensive_rebounds']
            if total_def_reb > 0:
                home_reb_momentum = (home_stats['defensive_rebounds'] / total_def_reb) * 100
                away_reb_momentum = (away_stats['defensive_rebounds'] / total_def_reb) * 100
            else:
                home_reb_momentum = away_reb_momentum = 50

        # 4. Turnover Differential (15% weight) - lower is better
        home_turnover_diff = away_stats['turnovers'] - home_stats['turnovers']
        away_turnover_diff = home_stats['turnovers'] - away_stats['turnovers']
        total_turnovers = home_stats['turnovers'] + away_stats['turnovers']
        if total_turnovers > 0:
            # Team with fewer turnovers gets higher momentum
            if home_stats['turnovers'] < away_stats['turnovers']:
                home_to_momentum = 60
                away_to_momentum = 40
            elif away_stats['turnovers'] < home_stats['turnovers']:
                home_to_momentum = 40
                away_to_momentum = 60
            else:
                home_to_momentum = away_to_momentum = 50
        else:
            home_to_momentum = away_to_momentum = 50

        # Weighted momentum formula
        home_momentum = (
            home_fg_momentum * 0.40 +
            home_scoring_momentum * 0.30 +
            home_reb_momentum * 0.15 +
            home_to_momentum * 0.15
        )

        away_momentum = (
            away_fg_momentum * 0.40 +
            away_scoring_momentum * 0.30 +
            away_reb_momentum * 0.15 +
            away_to_momentum * 0.15
        )

        # Calculate possession indicator
        home_possession = 'NEUTRAL'
        away_possession = 'NEUTRAL'

        # Last action determines possession
        if recent_plays:
            last_action = recent_plays[-1]
            last_team_id = last_action.get('teamId')
            last_action_type = last_action.get('actionType', '')

            if last_action_type in ['SHOT', 'TURNOVER']:
                # Possession likely changed
                if last_team_id == home_team_id:
                    away_possession = 'ATTACKING'
                    home_possession = 'DEFENDING'
                else:
                    home_possession = 'ATTACKING'
                    away_possession = 'DEFENDING'

        return {
            'home': {
                'momentum_score': round(home_momentum, 1),
                'points_last_5min': home_stats['points'],
                'fg_pct_recent': round(home_fg_pct, 1),
                'offensive_rebounds': home_stats['offensive_rebounds'],
                'turnovers': home_stats['turnovers'],
                'steals': home_stats['steals'],
                'assists': home_stats['assists'],
                'possession_indicator': home_possession
            },
            'away': {
                'momentum_score': round(away_momentum, 1),
                'points_last_5min': away_stats['points'],
                'fg_pct_recent': round(away_fg_pct, 1),
                'offensive_rebounds': away_stats['offensive_rebounds'],
                'turnovers': away_stats['turnovers'],
                'steals': away_stats['steals'],
                'assists': away_stats['assists'],
                'possession_indicator': away_possession
            },
            'period': current_period,
            'lookback_events': len(recent_plays)
        }

    def _empty_momentum(self) -> Dict:
        """Return empty momentum data structure"""
        return {
            'home': {
                'momentum_score': 50.0,
                'points_last_5min': 0,
                'fg_pct_recent': 0.0,
                'offensive_rebounds': 0,
                'turnovers': 0,
                'steals': 0,
                'assists': 0,
                'possession_indicator': 'NEUTRAL'
            },
            'away': {
                'momentum_score': 50.0,
                'points_last_5min': 0,
                'fg_pct_recent': 0.0,
                'offensive_rebounds': 0,
                'turnovers': 0,
                'steals': 0,
                'assists': 0,
                'possession_indicator': 'NEUTRAL'
            },
            'period': 0,
            'lookback_events': 0
        }

    def get_live_momentum(self, game_id: str) -> Optional[Dict]:
        """
        Main method to get live momentum for a game

        Args:
            game_id: NBA game ID

        Returns:
            Dict with home/away momentum stats
        """
        game_data = self.fetch_game_data(game_id)
        if not game_data:
            return None

        pbp_data = game_data.get('play_by_play', {})
        momentum = self.calculate_recent_momentum(pbp_data)

        return momentum
