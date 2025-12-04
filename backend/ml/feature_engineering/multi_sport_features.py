"""
Multi-Sport Player Props Feature Engineering
=============================================
Base classes and sport-specific feature engineering for all major sports

Supported Sports:
- NBA: Points, Rebounds, Assists, Threes, PRA, Blocks, Steals
- NFL: Pass Yards/TDs, Rush Yards/TDs, Receptions, Receiving Yards
- NHL: Goals, Assists, Points, Shots on Goal
- NCAAB: Points, Rebounds, Assists, Threes
- NCAAF: Pass Yards/TDs, Rush Yards/TDs, Receptions, Receiving Yards
- MLB: Hits, Home Runs, RBIs, Strikeouts (future)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class BaseSportFeatures(ABC):
    """Base class for sport-specific feature engineering"""

    def __init__(self, sport_key: str, prop_types: List[str]):
        self.sport_key = sport_key
        self.prop_types = prop_types
        self.feature_columns = []

    @abstractmethod
    def get_player_stats(self, player_name: str, team: str) -> Dict:
        """Get player statistics from database or API"""
        pass

    @abstractmethod
    def get_team_stats(self, team: str) -> Dict:
        """Get team statistics"""
        pass

    @abstractmethod
    def get_matchup_stats(self, team: str, opponent: str) -> Dict:
        """Get matchup-specific statistics"""
        pass

    @abstractmethod
    def engineer_features(self, player_name: str, team: str, opponent: str,
                         prop_type: str, market_line: float) -> Dict:
        """Engineer all features for a prediction"""
        pass

    def get_feature_names(self) -> List[str]:
        """Return list of feature names in correct order"""
        return self.feature_columns


class NBAFeatures(BaseSportFeatures):
    """NBA-specific feature engineering"""

    # Feature columns (22 features matching trainer)
    FEATURE_COLUMNS = [
        # Player stats (8 features)
        'season_avg', 'last_10_avg', 'usage_rate', 'minutes_per_game',
        'home_avg', 'away_avg', 'vs_opponent_avg', 'fg_pct',
        # Opponent matchup (8 features)
        'opp_defensive_rating', 'opp_pace', 'opp_assists', 'opp_turnovers',
        'opp_steals', 'opp_blocks', 'opp_rebounds', 'opp_points_allowed',
        # Market context (6 features)
        'market_line', 'line_vs_avg_diff', 'line_vs_l10_diff',
        'prop_weight', 'is_home', 'matchup_factor'
    ]

    def __init__(self, db_connection):
        super().__init__('nba', ['points', 'rebounds', 'assists', 'threes', 'PRA', 'blocks', 'steals'])
        self.db = db_connection
        self.feature_columns = self.FEATURE_COLUMNS

    def get_player_stats(self, player_name: str, team: str) -> Dict:
        """Get NBA player statistics"""
        cursor = self.db.cursor()

        # Try to get from player_stats_cache
        cursor.execute("""
            SELECT
                points_per_game,
                rebounds_per_game,
                assists_per_game,
                fg3_per_game,
                blocks_per_game,
                steals_per_game,
                field_goal_pct,
                minutes_per_game,
                usage_rate,
                last_10_ppg,
                last_10_rpg,
                last_10_apg,
                home_ppg,
                away_ppg
            FROM player_stats_cache
            WHERE player_name = ? AND team = ?
            ORDER BY last_updated DESC
            LIMIT 1
        """, (player_name, team))

        row = cursor.fetchone()

        if row:
            return {
                'points_per_game': row[0] or 0,
                'rebounds_per_game': row[1] or 0,
                'assists_per_game': row[2] or 0,
                'fg3_per_game': row[3] or 0,
                'blocks_per_game': row[4] or 0,
                'steals_per_game': row[5] or 0,
                'field_goal_pct': row[6] or 0.45,
                'minutes_per_game': row[7] or 25,
                'usage_rate': row[8] or 20,
                'last_10_ppg': row[9] or row[0] or 0,
                'last_10_rpg': row[10] or row[1] or 0,
                'last_10_apg': row[11] or row[2] or 0,
                'home_ppg': row[12] or row[0] or 0,
                'away_ppg': row[13] or row[0] or 0
            }

        # Return defaults if not found
        return {
            'points_per_game': 10,
            'rebounds_per_game': 4,
            'assists_per_game': 2,
            'fg3_per_game': 1,
            'blocks_per_game': 0.5,
            'steals_per_game': 0.7,
            'field_goal_pct': 0.45,
            'minutes_per_game': 25,
            'usage_rate': 20,
            'last_10_ppg': 10,
            'last_10_rpg': 4,
            'last_10_apg': 2,
            'home_ppg': 10,
            'away_ppg': 10
        }

    def get_team_stats(self, team: str) -> Dict:
        """Get NBA team statistics"""
        cursor = self.db.cursor()

        cursor.execute("""
            SELECT
                offensive_rating,
                defensive_rating,
                pace,
                assists_per_game,
                turnovers_per_game,
                steals_per_game,
                blocks_per_game,
                rebounds_per_game,
                points_allowed
            FROM team_stats_cache
            WHERE team = ? AND sport = 'nba'
            ORDER BY last_updated DESC
            LIMIT 1
        """, (team,))

        row = cursor.fetchone()

        if row:
            return {
                'offensive_rating': row[0] or 110,
                'defensive_rating': row[1] or 110,
                'pace': row[2] or 100,
                'assists': row[3] or 25,
                'turnovers': row[4] or 14,
                'steals': row[5] or 7.5,
                'blocks': row[6] or 5,
                'rebounds': row[7] or 45,
                'points_allowed': row[8] or 110
            }

        # Return league averages
        return {
            'offensive_rating': 110,
            'defensive_rating': 110,
            'pace': 100,
            'assists': 25,
            'turnovers': 14,
            'steals': 7.5,
            'blocks': 5,
            'rebounds': 45,
            'points_allowed': 110
        }

    def get_matchup_stats(self, team: str, opponent: str) -> Dict:
        """Get NBA matchup statistics"""
        return self.get_team_stats(opponent)

    def engineer_features(self, player_name: str, team: str, opponent: str,
                         prop_type: str, market_line: float, is_home: bool = True) -> Dict:
        """Engineer all 22 NBA features"""
        player_stats = self.get_player_stats(player_name, team)
        opp_stats = self.get_matchup_stats(team, opponent)

        # Map prop type to stat
        stat_map = {
            'points': 'points_per_game',
            'rebounds': 'rebounds_per_game',
            'assists': 'assists_per_game',
            'threes': 'fg3_per_game',
            'blocks': 'blocks_per_game',
            'steals': 'steals_per_game',
            'PRA': None  # Calculated
        }

        last10_map = {
            'points': 'last_10_ppg',
            'rebounds': 'last_10_rpg',
            'assists': 'last_10_apg'
        }

        # Get season average
        if prop_type == 'PRA':
            season_avg = (player_stats['points_per_game'] +
                         player_stats['rebounds_per_game'] +
                         player_stats['assists_per_game'])
            last_10_avg = (player_stats['last_10_ppg'] +
                          player_stats['last_10_rpg'] +
                          player_stats['last_10_apg'])
        else:
            stat_key = stat_map.get(prop_type, 'points_per_game')
            season_avg = player_stats.get(stat_key, 0)
            last_10_avg = player_stats.get(last10_map.get(prop_type, stat_key), season_avg)

        # Home/Away split
        home_avg = player_stats.get('home_ppg', season_avg) if prop_type == 'points' else season_avg
        away_avg = player_stats.get('away_ppg', season_avg) if prop_type == 'points' else season_avg

        # Calculate features
        features = {
            # Player stats
            'season_avg': season_avg,
            'last_10_avg': last_10_avg,
            'usage_rate': player_stats.get('usage_rate', 20),
            'minutes_per_game': player_stats.get('minutes_per_game', 25),
            'home_avg': home_avg,
            'away_avg': away_avg,
            'vs_opponent_avg': season_avg,  # TODO: Get actual vs opponent avg
            'fg_pct': player_stats.get('field_goal_pct', 0.45),

            # Opponent matchup
            'opp_defensive_rating': opp_stats['defensive_rating'],
            'opp_pace': opp_stats['pace'],
            'opp_assists': opp_stats['assists'],
            'opp_turnovers': opp_stats['turnovers'],
            'opp_steals': opp_stats['steals'],
            'opp_blocks': opp_stats['blocks'],
            'opp_rebounds': opp_stats['rebounds'],
            'opp_points_allowed': opp_stats['points_allowed'],

            # Market context
            'market_line': market_line,
            'line_vs_avg_diff': market_line - season_avg,
            'line_vs_l10_diff': market_line - last_10_avg,
            'prop_weight': 1.0,  # TODO: Calculate based on prop type importance
            'is_home': 1 if is_home else 0,
            'matchup_factor': opp_stats['pace'] / 100  # Pace adjustment
        }

        return features


class NFLFeatures(BaseSportFeatures):
    """NFL-specific feature engineering"""

    FEATURE_COLUMNS = [
        # Player stats (8 features)
        'season_avg', 'last_4_avg', 'usage_rate', 'team_pass_rate',
        'home_avg', 'away_avg', 'vs_opponent_avg', 'completion_pct',
        # Opponent matchup (6 features)
        'opp_yards_allowed', 'opp_tds_allowed', 'opp_pass_def_rank',
        'opp_rush_def_rank', 'opp_sacks', 'opp_interceptions',
        # Game context (6 features)
        'market_line', 'line_vs_avg_diff', 'vegas_total',
        'weather_factor', 'is_home', 'divisional_game'
    ]

    def __init__(self, db_connection):
        super().__init__('nfl', ['pass_yards', 'pass_tds', 'rush_yards', 'rush_tds',
                                  'receptions', 'receiving_yards', 'anytime_td'])
        self.db = db_connection
        self.feature_columns = self.FEATURE_COLUMNS

    def get_player_stats(self, player_name: str, team: str) -> Dict:
        """Get NFL player statistics - placeholder for now"""
        return {
            'season_avg': 250,  # Passing yards example
            'last_4_avg': 260,
            'usage_rate': 100,
            'team_pass_rate': 60,
            'home_avg': 265,
            'away_avg': 235,
            'vs_opponent_avg': 250,
            'completion_pct': 0.65
        }

    def get_team_stats(self, team: str) -> Dict:
        """Get NFL team statistics"""
        return {
            'yards_allowed': 350,
            'tds_allowed': 2.5,
            'pass_def_rank': 15,
            'rush_def_rank': 15,
            'sacks': 2.5,
            'interceptions': 1.0
        }

    def get_matchup_stats(self, team: str, opponent: str) -> Dict:
        return self.get_team_stats(opponent)

    def engineer_features(self, player_name: str, team: str, opponent: str,
                         prop_type: str, market_line: float, is_home: bool = True) -> Dict:
        """Engineer all NFL features"""
        player_stats = self.get_player_stats(player_name, team)
        opp_stats = self.get_matchup_stats(team, opponent)

        features = {
            # Player stats
            'season_avg': player_stats['season_avg'],
            'last_4_avg': player_stats['last_4_avg'],
            'usage_rate': player_stats['usage_rate'],
            'team_pass_rate': player_stats['team_pass_rate'],
            'home_avg': player_stats['home_avg'],
            'away_avg': player_stats['away_avg'],
            'vs_opponent_avg': player_stats['vs_opponent_avg'],
            'completion_pct': player_stats['completion_pct'],

            # Opponent matchup
            'opp_yards_allowed': opp_stats['yards_allowed'],
            'opp_tds_allowed': opp_stats['tds_allowed'],
            'opp_pass_def_rank': opp_stats['pass_def_rank'],
            'opp_rush_def_rank': opp_stats['rush_def_rank'],
            'opp_sacks': opp_stats['sacks'],
            'opp_interceptions': opp_stats['interceptions'],

            # Game context
            'market_line': market_line,
            'line_vs_avg_diff': market_line - player_stats['season_avg'],
            'vegas_total': 47.5,  # TODO: Get actual total
            'weather_factor': 1.0,  # TODO: Get weather data
            'is_home': 1 if is_home else 0,
            'divisional_game': 0  # TODO: Determine if divisional
        }

        return features


class NHLFeatures(BaseSportFeatures):
    """NHL-specific feature engineering"""

    FEATURE_COLUMNS = [
        # Player stats (8 features)
        'season_avg', 'last_10_avg', 'ice_time', 'shooting_pct',
        'home_avg', 'away_avg', 'power_play_time', 'linemates_quality',
        # Opponent matchup (6 features)
        'opp_goals_allowed', 'opp_save_pct', 'opp_penalty_kill',
        'opp_def_rank', 'goalie_rating', 'back_to_back',
        # Game context (6 features)
        'market_line', 'line_vs_avg_diff', 'vegas_total',
        'is_home', 'rest_days', 'matchup_factor'
    ]

    def __init__(self, db_connection):
        super().__init__('nhl', ['goals', 'assists', 'points', 'shots_on_goal', 'anytime_goal'])
        self.db = db_connection
        self.feature_columns = self.FEATURE_COLUMNS

    def get_player_stats(self, player_name: str, team: str) -> Dict:
        """Get NHL player statistics"""
        return {
            'season_avg': 0.8,  # Goals per game example
            'last_10_avg': 0.9,
            'ice_time': 18.5,
            'shooting_pct': 0.12,
            'home_avg': 0.85,
            'away_avg': 0.75,
            'power_play_time': 3.5,
            'linemates_quality': 80
        }

    def get_team_stats(self, team: str) -> Dict:
        return {
            'goals_allowed': 3.0,
            'save_pct': 0.910,
            'penalty_kill': 0.80,
            'def_rank': 15,
            'goalie_rating': 75,
            'back_to_back': 0
        }

    def get_matchup_stats(self, team: str, opponent: str) -> Dict:
        return self.get_team_stats(opponent)

    def engineer_features(self, player_name: str, team: str, opponent: str,
                         prop_type: str, market_line: float, is_home: bool = True) -> Dict:
        player_stats = self.get_player_stats(player_name, team)
        opp_stats = self.get_matchup_stats(team, opponent)

        features = {
            # Player stats
            'season_avg': player_stats['season_avg'],
            'last_10_avg': player_stats['last_10_avg'],
            'ice_time': player_stats['ice_time'],
            'shooting_pct': player_stats['shooting_pct'],
            'home_avg': player_stats['home_avg'],
            'away_avg': player_stats['away_avg'],
            'power_play_time': player_stats['power_play_time'],
            'linemates_quality': player_stats['linemates_quality'],

            # Opponent matchup
            'opp_goals_allowed': opp_stats['goals_allowed'],
            'opp_save_pct': opp_stats['save_pct'],
            'opp_penalty_kill': opp_stats['penalty_kill'],
            'opp_def_rank': opp_stats['def_rank'],
            'goalie_rating': opp_stats['goalie_rating'],
            'back_to_back': opp_stats['back_to_back'],

            # Game context
            'market_line': market_line,
            'line_vs_avg_diff': market_line - player_stats['season_avg'],
            'vegas_total': 6.5,
            'is_home': 1 if is_home else 0,
            'rest_days': 1,
            'matchup_factor': 1.0
        }

        return features


# Factory function
def get_feature_engineer(sport: str, db_connection):
    """Factory function to get the right feature engineer for each sport"""
    feature_map = {
        'nba': NBAFeatures,
        'nfl': NFLFeatures,
        'nhl': NHLFeatures,
        'ncaab': NBAFeatures,  # Use NBA features for college basketball
        'ncaaf': NFLFeatures   # Use NFL features for college football
    }

    feature_class = feature_map.get(sport.lower())
    if not feature_class:
        raise ValueError(f"Unsupported sport: {sport}")

    return feature_class(db_connection)
