"""NBA Stats API Client for team statistics"""
from nba_api.stats.endpoints import leaguedashteamstats, teamgamelog
from nba_api.stats.static import teams
import logging
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class NBAStatsClient:
    def __init__(self):
        self.cache_file = "team_stats_cache.json"
        self.cache_duration = timedelta(hours=12)  # Refresh twice per day
        self.team_id_map = self._build_team_id_map()

    def _build_team_id_map(self) -> Dict[str, str]:
        """Build mapping from team name to NBA team ID"""
        all_teams = teams.get_teams()
        team_map = {}
        for team in all_teams:
            # Map full name to team ID
            team_map[team['full_name']] = str(team['id'])
            # Also map nickname for easier lookup
            team_map[team['nickname']] = str(team['id'])
            # Add alternate abbreviations (e.g. "LA Clippers" for "Los Angeles Clippers")
            if team['full_name'].startswith('Los Angeles'):
                la_abbr = team['full_name'].replace('Los Angeles', 'LA')
                team_map[la_abbr] = str(team['id'])
        return team_map

    def _load_cache(self) -> Optional[Dict]:
        """Load cached team stats if available and fresh"""
        if not os.path.exists(self.cache_file):
            return None

        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)

            # Check if cache is still fresh
            cache_time = datetime.fromisoformat(cache['timestamp'])
            if datetime.now() - cache_time < self.cache_duration:
                logger.info("Using cached team stats")
                return cache['data']
            else:
                logger.info("Cache expired, will fetch fresh data")
                return None
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return None

    def _save_cache(self, data: Dict):
        """Save team stats to cache"""
        try:
            cache = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f)
            logger.info("Saved team stats to cache")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def get_team_id(self, team_name: str) -> Optional[str]:
        """Get NBA team ID from team name"""
        # Try exact match first
        if team_name in self.team_id_map:
            return self.team_id_map[team_name]

        # Try to find partial match
        for name, team_id in self.team_id_map.items():
            if team_name.lower() in name.lower():
                return team_id

        logger.warning(f"Could not find team ID for: {team_name}")
        return None

    def fetch_team_season_stats(self) -> Dict[str, Dict]:
        """Fetch season stats for all teams"""
        # Check cache first
        cached_data = self._load_cache()
        if cached_data:
            return cached_data

        logger.info("Fetching fresh team season stats from NBA API...")
        team_stats = {}

        try:
            # Fetch advanced team stats (includes OffRtg, DefRtg, Pace)
            time.sleep(0.6)  # Rate limiting
            advanced_stats = leaguedashteamstats.LeagueDashTeamStats(
                season='2024-25',
                season_type_all_star='Regular Season',
                measure_type_detailed_defense='Advanced',
                per_mode_detailed='PerGame'
            )
            advanced_df = advanced_stats.get_data_frames()[0]

            # Fetch base team stats (includes FG%, 3P%, etc.)
            time.sleep(0.6)  # Rate limiting
            base_stats = leaguedashteamstats.LeagueDashTeamStats(
                season='2024-25',
                season_type_all_star='Regular Season',
                measure_type_detailed_defense='Base',
                per_mode_detailed='PerGame'
            )
            base_df = base_stats.get_data_frames()[0]

            # Combine stats for each team
            for _, adv_row in advanced_df.iterrows():
                team_name = adv_row['TEAM_NAME']
                team_id = str(adv_row['TEAM_ID'])

                # Find matching base stats
                base_row = base_df[base_df['TEAM_ID'] == int(team_id)]
                if base_row.empty:
                    continue
                base_row = base_row.iloc[0]

                team_stats[team_name] = {
                    'team_id': team_id,
                    'team_name': team_name,
                    'games_played': int(adv_row.get('GP', 0)),
                    'wins': int(adv_row.get('W', 0)),
                    'losses': int(adv_row.get('L', 0)),
                    'win_pct': float(adv_row.get('W_PCT', 0)),
                    'off_rating': float(adv_row.get('OFF_RATING', 0)),
                    'def_rating': float(adv_row.get('DEF_RATING', 0)),
                    'net_rating': float(adv_row.get('NET_RATING', 0)),
                    'pace': float(adv_row.get('PACE', 0)),
                    'fg_pct': float(base_row.get('FG_PCT', 0)),
                    'fg3_pct': float(base_row.get('FG3_PCT', 0)),
                    'ft_pct': float(base_row.get('FT_PCT', 0)),
                    'pts_per_game': float(base_row.get('PTS', 0)),
                    'pts_allowed': float(adv_row.get('DEF_RATING', 0)) * float(adv_row.get('PACE', 0)) / 100,
                }

            # Calculate rankings by sorting teams
            teams_list = list(team_stats.values())

            # Rank by points per game (higher is better)
            sorted_by_ppg = sorted(teams_list, key=lambda x: x['pts_per_game'], reverse=True)
            for rank, team in enumerate(sorted_by_ppg, 1):
                team_stats[team['team_name']]['pts_per_game_rank'] = rank

            # Rank by offensive rating (higher is better)
            sorted_by_offrtg = sorted(teams_list, key=lambda x: x['off_rating'], reverse=True)
            for rank, team in enumerate(sorted_by_offrtg, 1):
                team_stats[team['team_name']]['off_rating_rank'] = rank

            # Rank by defensive rating (lower is better)
            sorted_by_defrtg = sorted(teams_list, key=lambda x: x['def_rating'])
            for rank, team in enumerate(sorted_by_defrtg, 1):
                team_stats[team['team_name']]['def_rating_rank'] = rank

            # Rank by net rating (higher is better)
            sorted_by_netrtg = sorted(teams_list, key=lambda x: x['net_rating'], reverse=True)
            for rank, team in enumerate(sorted_by_netrtg, 1):
                team_stats[team['team_name']]['net_rating_rank'] = rank

            # Rank by pace (higher is better)
            sorted_by_pace = sorted(teams_list, key=lambda x: x['pace'], reverse=True)
            for rank, team in enumerate(sorted_by_pace, 1):
                team_stats[team['team_name']]['pace_rank'] = rank

            # Rank by FG% (higher is better)
            sorted_by_fg = sorted(teams_list, key=lambda x: x['fg_pct'], reverse=True)
            for rank, team in enumerate(sorted_by_fg, 1):
                team_stats[team['team_name']]['fg_pct_rank'] = rank

            # Rank by 3P% (higher is better)
            sorted_by_fg3 = sorted(teams_list, key=lambda x: x['fg3_pct'], reverse=True)
            for rank, team in enumerate(sorted_by_fg3, 1):
                team_stats[team['team_name']]['fg3_pct_rank'] = rank

            # Rank by FT% (higher is better)
            sorted_by_ft = sorted(teams_list, key=lambda x: x['ft_pct'], reverse=True)
            for rank, team in enumerate(sorted_by_ft, 1):
                team_stats[team['team_name']]['ft_pct_rank'] = rank

            # Save to cache
            self._save_cache(team_stats)
            logger.info(f"Fetched stats for {len(team_stats)} teams")
            return team_stats

        except Exception as e:
            logger.error(f"Error fetching team stats: {e}", exc_info=True)
            return {}

    def fetch_last_n_games(self, team_name: str, n: int = 5) -> list:
        """Fetch last N games for a team"""
        team_id = self.get_team_id(team_name)
        if not team_id:
            return []

        try:
            time.sleep(0.6)  # Rate limiting
            game_log = teamgamelog.TeamGameLog(
                team_id=team_id,
                season='2024-25'
            )
            df = game_log.get_data_frames()[0]

            # Get last N games
            recent_games = []
            for _, row in df.head(n).iterrows():
                recent_games.append({
                    'game_date': row.get('GAME_DATE', ''),
                    'matchup': row.get('MATCHUP', ''),
                    'wl': row.get('WL', ''),
                    'pts': int(row.get('PTS', 0)),
                    'opp_pts': int(row.get('PTS', 0)) - int(row.get('PLUS_MINUS', 0)),
                    'plus_minus': int(row.get('PLUS_MINUS', 0)),
                    'fg_pct': float(row.get('FG_PCT', 0)),
                })

            return recent_games

        except Exception as e:
            logger.error(f"Error fetching game log for {team_name}: {e}")
            return []

    def get_team_stats(self, team_name: str) -> Optional[Dict]:
        """Get season stats for a specific team"""
        all_stats = self.fetch_team_season_stats()

        # Try exact match first
        if team_name in all_stats:
            return all_stats[team_name]

        # Try with "LA" converted to "Los Angeles"
        if team_name.startswith('LA '):
            la_full = team_name.replace('LA ', 'Los Angeles ')
            if la_full in all_stats:
                return all_stats[la_full]

        # Try fuzzy match
        team_name_lower = team_name.lower()
        for cached_name, stats in all_stats.items():
            if team_name_lower in cached_name.lower() or cached_name.lower() in team_name_lower:
                return stats

        return None
