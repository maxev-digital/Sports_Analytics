"""NBA Player Stats Client for Player Props Projections"""
from nba_api.stats.endpoints import playergamelog, commonplayerinfo, leaguedashplayerstats, leaguedashteamstats, playerdashptshots, leaguedashteamstats
from nba_api.stats.static import players, teams
import logging
from typing import Dict, List, Optional
import time
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class NBAPlayerPropsStats:
    """
    Fetch and process NBA player stats for props projections
    Uses NBA.com official API via nba_api library
    """

    def __init__(self):
        self.players_cache = {}
        self.team_defense_cache = {}
        self.current_season = "2024-25"

    def get_player_by_name(self, player_name: str) -> Optional[Dict]:
        """
        Find player by name (fuzzy matching)

        Args:
            player_name: Player name (e.g., "LeBron James")

        Returns:
            Dict with player info or None
        """
        try:
            all_players = players.get_players()

            # Try exact match first
            for player in all_players:
                if player['full_name'].lower() == player_name.lower():
                    return player

            # Try partial match
            for player in all_players:
                if player_name.lower() in player['full_name'].lower():
                    return player

            logger.warning(f"Player not found: {player_name}")
            return None

        except Exception as e:
            logger.error(f"Error finding player {player_name}: {e}")
            return None

    def get_player_season_stats(self, player_id: int) -> Optional[Dict]:
        """
        Get player's season averages

        Returns:
            Dict with stats like PTS, REB, AST, 3PM, etc.
        """
        try:
            time.sleep(0.6)  # Rate limiting

            stats = leaguedashplayerstats.LeagueDashPlayerStats(
                season=self.current_season,
                season_type_all_star='Regular Season',
                per_mode_detailed='PerGame'
            )

            df = stats.get_data_frames()[0]

            # Filter for the specific player
            if df.empty:
                return None

            player_data = df[df['PLAYER_ID'] == player_id]

            if player_data.empty:
                return None

            player_data = player_data.iloc[0]

            return {
                'player_id': player_id,
                'player_name': player_data['PLAYER_NAME'],
                'team_abbr': player_data['TEAM_ABBREVIATION'],
                'games_played': player_data['GP'],
                'minutes_per_game': player_data['MIN'],
                'points': player_data['PTS'],
                'rebounds': player_data['REB'],
                'assists': player_data['AST'],
                'threes_made': player_data['FG3M'],
                'steals': player_data['STL'],
                'blocks': player_data['BLK'],
                'turnovers': player_data['TOV'],
                'fg_pct': player_data['FG_PCT'],
                'fg3_pct': player_data['FG3_PCT'],
                'usage_pct': player_data.get('USG_PCT', 0) if 'USG_PCT' in player_data else None
            }

        except Exception as e:
            logger.error(f"Error fetching season stats for player {player_id}: {e}")
            return None

    def get_player_recent_games(self, player_id: int, num_games: int = 10) -> List[Dict]:
        """
        Get player's recent game logs

        Args:
            player_id: NBA player ID
            num_games: Number of recent games to fetch

        Returns:
            List of game dicts with stats
        """
        try:
            time.sleep(0.6)  # Rate limiting

            game_log = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=self.current_season,
                season_type_all_star='Regular Season'
            )

            df = game_log.get_data_frames()[0]

            if df.empty:
                return []

            # Get most recent games
            recent_games = df.head(num_games)

            games_list = []
            for _, game in recent_games.iterrows():
                games_list.append({
                    'game_date': game['GAME_DATE'],
                    'matchup': game['MATCHUP'],
                    'minutes': game['MIN'],
                    'points': game['PTS'],
                    'rebounds': game['REB'],
                    'assists': game['AST'],
                    'threes_made': game['FG3M'],
                    'steals': game['STL'],
                    'blocks': game['BLK'],
                    'turnovers': game['TOV'],
                    'fg_pct': game['FG_PCT'],
                    'plus_minus': game['PLUS_MINUS']
                })

            return games_list

        except Exception as e:
            logger.error(f"Error fetching recent games for player {player_id}: {e}")
            return []

    def get_team_defensive_stats(self, team_abbr: str) -> Optional[Dict]:
        """
        Get team's defensive stats (opponent averages)

        Returns:
            Dict with defensive ratings, opponent stats allowed
        """
        # Check cache
        if team_abbr in self.team_defense_cache:
            return self.team_defense_cache[team_abbr]

        try:
            time.sleep(0.6)  # Rate limiting

            # Get team defensive stats
            team_stats = leaguedashteamstats.LeagueDashTeamStats(
                season=self.current_season,
                season_type_all_star='Regular Season',
                measure_type_detailed_defense='Defense',
                per_mode_detailed='PerGame'
            )

            df = team_stats.get_data_frames()[0]

            # Find the specific team
            team_data = df[df['TEAM_ABBREVIATION'] == team_abbr]

            if team_data.empty:
                return None

            team_row = team_data.iloc[0]

            defense_stats = {
                'team_abbr': team_abbr,
                'def_rating': team_row.get('DEF_RATING', 0),
                'opp_pts_per_game': team_row.get('OPP_PTS', 0),
                'opp_fg_pct': team_row.get('OPP_FG_PCT', 0),
                'opp_fg3_pct': team_row.get('OPP_FG3_PCT', 0),
                'def_reb_per_game': team_row.get('DREB', 0),
                'steals_per_game': team_row.get('STL', 0),
                'blocks_per_game': team_row.get('BLK', 0),
                'pace': team_row.get('PACE', 100.0)  # Possessions per 48 min
            }

            # Cache it
            self.team_defense_cache[team_abbr] = defense_stats

            return defense_stats

        except Exception as e:
            logger.error(f"Error fetching defensive stats for {team_abbr}: {e}")
            return None

    def calculate_recent_trend(self, recent_games: List[Dict], stat_type: str) -> Dict:
        """
        Calculate trend from recent games

        Args:
            recent_games: List of recent game dicts
            stat_type: 'points', 'rebounds', 'assists', etc.

        Returns:
            Dict with average, trend (increasing/decreasing/stable)
        """
        if not recent_games:
            return {'average': 0, 'trend': 'stable', 'std_dev': 0}

        # Extract stat values
        values = [game.get(stat_type, 0) for game in recent_games]

        if not values:
            return {'average': 0, 'trend': 'stable', 'std_dev': 0}

        # Calculate average
        avg = sum(values) / len(values)

        # Calculate standard deviation
        if len(values) > 1:
            variance = sum((x - avg) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
        else:
            std_dev = 0

        # Determine trend (compare first half vs second half)
        if len(values) >= 4:
            first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
            second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)

            diff_pct = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0

            if diff_pct > 10:
                trend = 'increasing'
            elif diff_pct < -10:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'stable'

        return {
            'average': round(avg, 1),
            'trend': trend,
            'std_dev': round(std_dev, 1),
            'recent_values': values
        }

    def get_player_complete_profile(self, player_name: str, opponent_team: str = None) -> Optional[Dict]:
        """
        Get complete player profile for props projection

        Args:
            player_name: Player name
            opponent_team: Opponent team abbreviation (optional)

        Returns:
            Comprehensive dict with all needed stats
        """
        # Find player
        player = self.get_player_by_name(player_name)
        if not player:
            return None

        player_id = player['id']

        # Get season stats
        season_stats = self.get_player_season_stats(player_id)
        if not season_stats:
            return None

        # Get recent games
        recent_games = self.get_player_recent_games(player_id, num_games=10)

        # Calculate trends for each stat type
        points_trend = self.calculate_recent_trend(recent_games, 'points')
        rebounds_trend = self.calculate_recent_trend(recent_games, 'rebounds')
        assists_trend = self.calculate_recent_trend(recent_games, 'assists')
        threes_trend = self.calculate_recent_trend(recent_games, 'threes_made')

        # Get opponent defensive stats if provided
        opponent_defense = None
        if opponent_team:
            opponent_defense = self.get_team_defensive_stats(opponent_team)

        return {
            'player_info': {
                'id': player_id,
                'name': player_name,
                'team': season_stats.get('team_abbr')
            },
            'season_stats': season_stats,
            'recent_games': recent_games,
            'trends': {
                'points': points_trend,
                'rebounds': rebounds_trend,
                'assists': assists_trend,
                'threes': threes_trend
            },
            'opponent_defense': opponent_defense
        }
