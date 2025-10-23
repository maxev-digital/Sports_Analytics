"""ESPN NFL API client for comprehensive live game and team statistics data"""
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ESPNNFLClient:
    """Client for fetching NFL live data from ESPN's unofficial API"""

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_scoreboard(self) -> Dict:
        """Fetch NFL scoreboard with all live games"""
        try:
            url = f"{self.BASE_URL}/scoreboard"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching ESPN scoreboard: {e}")
            return {}

    def fetch_schedule(self, limit: int = 50) -> List[Dict]:
        """
        Fetch NFL schedule for upcoming and live games
        
        Returns list of games with:
        - home_team: str
        - away_team: str
        - commence_time: str (ISO format)
        - status: str ('upcoming' or 'live')
        - game_id: str (ESPN event ID)
        """
        try:
            url = f"{self.BASE_URL}/scoreboard"
            params = {'limit': limit}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            games = []
            events = data.get('events', [])
            
            for event in events:
                try:
                    competitions = event.get('competitions', [])
                    if not competitions:
                        continue
                    
                    comp = competitions[0]
                    competitors = comp.get('competitors', [])
                    
                    if len(competitors) < 2:
                        continue
                    
                    # Extract teams
                    home_team = None
                    away_team = None
                    
                    for competitor in competitors:
                        team = competitor.get('team', {})
                        team_name = team.get('displayName', '')
                        home_away = competitor.get('homeAway', '')
                        
                        if home_away == 'home':
                            home_team = team_name
                        elif home_away == 'away':
                            away_team = team_name
                    
                    if not home_team or not away_team:
                        continue
                    
                    # Extract status
                    status = comp.get('status', {})
                    status_type = status.get('type', {}).get('name', '')
                    is_live = status_type in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD']
                    is_completed = status_type in ['STATUS_FINAL', 'STATUS_FINAL_OT']
                    
                    # Skip completed games
                    if is_completed:
                        continue
                    
                    # Get commence time
                    commence_time = event.get('date', '')
                    
                    games.append({
                        'home_team': home_team,
                        'away_team': away_team,
                        'commence_time': commence_time,
                        'status': 'live' if is_live else 'upcoming',
                        'game_id': event.get('id'),
                        'sport_key': 'americanfootball_nfl'
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing game event: {e}")
                    continue
            
            logger.info(f"Fetched {len(games)} NFL games from ESPN schedule")
            return games
            
        except Exception as e:
            logger.error(f"Error fetching ESPN NFL schedule: {e}")
            return []

    def fetch_game_summary(self, game_id: str) -> Dict:
        """Fetch detailed game summary including boxscore stats"""
        try:
            url = f"{self.BASE_URL}/summary?event={game_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching ESPN game summary for {game_id}: {e}")
            return {}

    def get_live_game_info(self, team_name: str, scoreboard_data: Dict) -> Optional[Dict]:
        """
        Extract live game info for a specific team from scoreboard data

        Returns dict with:
        - is_live: bool
        - period: int (quarter)
        - clock: str (time remaining)
        - game_id: str (ESPN event ID)
        """
        events = scoreboard_data.get('events', [])

        for event in events:
            competitions = event.get('competitions', [])
            if not competitions:
                continue

            comp = competitions[0]
            competitors = comp.get('competitors', [])

            # Check if this game involves the team
            team_found = False
            for competitor in competitors:
                team = competitor.get('team', {})
                team_display = team.get('displayName', '')
                if team_name.lower() in team_display.lower() or team_display.lower() in team_name.lower():
                    team_found = True
                    break

            if not team_found:
                continue

            # Extract game status
            status = comp.get('status', {})
            status_type = status.get('type', {}).get('name', '')

            is_live = status_type in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME', 'STATUS_END_PERIOD']

            if is_live:
                return {
                    'is_live': True,
                    'period': status.get('period', 1),
                    'clock': status.get('displayClock', '15:00'),
                    'game_id': event.get('id'),
                    'status_detail': status.get('type', {}).get('detail', '')
                }

        return None

    def parse_game_stats(self, summary_data: Dict) -> Dict[str, Dict]:
        """
        Parse boxscore statistics from game summary

        Returns dict with team names as keys and stats dict as values
        """
        result = {}

        boxscore = summary_data.get('boxscore', {})
        teams = boxscore.get('teams', [])

        for team_data in teams:
            team_info = team_data.get('team', {})
            team_name = team_info.get('displayName', '')

            stats_dict = {}
            statistics = team_data.get('statistics', [])

            for stat in statistics:
                stat_name = stat.get('name', '')
                stat_value = stat.get('displayValue', '')
                stats_dict[stat_name] = stat_value

            result[team_name] = stats_dict

        return result

    def fetch_team_season_stats(self, team_abbr: str) -> Optional[Dict]:
        """
        Fetch comprehensive season statistics for a specific NFL team from ESPN
        Returns dict with season totals, averages, and rankings
        """
        try:
            team_url = f"{self.TEAMS_URL}"
            response = self.session.get(team_url, timeout=15)
            response.raise_for_status()
            teams_data = response.json()

            # Find the specific team
            for team_info in teams_data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
                team_data = team_info.get('team', {})
                team_slug = team_data.get('slug', '')

                if team_slug and team_abbr.lower() in team_slug.lower():
                    # Get detailed team stats
                    team_id = team_data.get('id')

                    # Fetch team-specific stats
                    stats_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}"
                    stats_response = self.session.get(stats_url, timeout=15)

                    if stats_response.status_code == 200:
                        team_stats_data = stats_response.json()
                        stats = team_stats_data.get('team', {}).get('record', {}).get('stats', [])

                        # Parse season statistics
                        season_stats = {}
                        for stat in stats:
                            key = stat.get('name', '').lower().replace(' ', '_').replace('/', '_')
                            value = stat.get('value', 0)
                            season_stats[key] = value

                        # Get rankings if available
                        rankings = team_stats_data.get('team', {}).get('rankings', {}).get('stats', [])
                        ranking_stats = {}
                        for rank in rankings:
                            key = f"{rank.get('name', '').lower().replace(' ', '_')}_rank"
                            value = rank.get('value', 0)
                            ranking_stats[key] = value

                        # Calculate derived stats
                        games_played = season_stats.get('games_played', 0)

                        if games_played > 0:
                            # Points per game
                            points = season_stats.get('points', 0)
                            points_allowed = season_stats.get('points_allowed', 0)

                            season_stats['points_per_game'] = round(points / games_played, 1)
                            season_stats['points_allowed_per_game'] = round(points_allowed / games_played, 1)
                            season_stats['point_differential'] = points - points_allowed
                            season_stats['point_differential_per_game'] = round((points - points_allowed) / games_played, 1)

                            # Yardage stats
                            total_yards = season_stats.get('net_yards', 0)
                            pass_yards = season_stats.get('passing_yards', 0)
                            rush_yards = season_stats.get('rushing_yards', 0)

                            season_stats['total_yards_per_game'] = round(total_yards / games_played, 1)
                            season_stats['passing_yards_per_game'] = round(pass_yards / games_played, 1)
                            season_stats['rushing_yards_per_game'] = round(rush_yards / games_played, 1)

                            # Efficiency stats
                            completions = season_stats.get('completions', 0)
                            attempts = season_stats.get('passing_attempts', 0)
                            if attempts > 0:
                                season_stats['completion_pct'] = round((completions / attempts) * 100, 1)

                            fg_made = season_stats.get('field_goals_made', 0)
                            fg_attempts = season_stats.get('field_goals_attempted', 0)
                            if fg_attempts > 0:
                                season_stats['field_goal_pct'] = round((fg_made / fg_attempts) * 100, 1)

                            # Defense stats
                            sacks_allowed = season_stats.get('sacks_allowed', 0)
                            ints_thrown = season_stats.get('interceptions_thrown', 0)
                            fumbles_lost = season_stats.get('fumbles_lost', 0)

                            season_stats['turnovers_per_game'] = round((ints_thrown + fumbles_lost) / games_played, 2)

                            sacks = season_stats.get('sacks', 0)
                            season_stats['sacks_per_game'] = round(sacks / games_played, 2)

                        # Determine winning/losing trend
                        wins = season_stats.get('wins', 0)
                        losses = season_stats.get('losses', 0)
                        ties = season_stats.get('ties', 0)

                        if wins > losses:
                            trend = 'HOT' if wins > 8 else 'NEUTRAL'
                        elif losses > wins:
                            trend = 'COLD' if losses > 8 else 'NEUTRAL'
                        else:
                            trend = 'NEUTRAL'

                        return {
                            'team_id': team_id,
                            'team_name': team_data.get('displayName', ''),
                            'team_abbr': team_data.get('abbreviation', ''),
                            'games_played': games_played,
                            'wins': wins,
                            'losses': losses,
                            'ties': ties,
                            'win_pct': round(wins / (wins + losses + ties) if (wins + losses + ties) > 0 else 0, 3),
                            'season_stats': season_stats,
                            'rankings': ranking_stats,
                            'form_trend': trend,
                            'last_5_record': self._calculate_last_5_performance(team_slug)
                        }

            logger.warning(f"Team {team_abbr} not found in ESPN data")
            return None

        except Exception as e:
            logger.error(f"Error fetching season stats for {team_abbr}: {e}")
            return None

    def _calculate_last_5_performance(self, team_slug: str) -> Optional[str]:
        """Calculate last 5 game performance for a team"""
        try:
            # Get recent games for this team
            recent_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={(datetime.now() - timedelta(days=90)).strftime('%Y%m%d')}-{(datetime.now() + timedelta(days=1)).strftime('%Y%m%d')}&limit=50"
            response = self.session.get(recent_url, timeout=15)

            if response.status_code == 200:
                data = response.json()
                team_games = []

                for event in data.get('events', []):
                    competitions = event.get('competitions', [])
                    if competitions:
                        comp = competitions[0]
                        competitors = comp.get('competitors', [])

                        team_found = False
                        for comp_team in competitors:
                            team_info = comp_team.get('team', {})
                            if team_slug in team_info.get('slug', '').lower():
                                team_found = True
                                break

                        if team_found:
                            status = comp.get('status', {})
                            status_type = status.get('type', {}).get('name', '')

                            if status_type in ['STATUS_FINAL', 'STATUS_SCHEDULED_past']:
                                competitors = comp.get('competitors', [])
                                team_score = None
                                opponent_score = None

                                for team_comp in competitors:
                                    team_info = team_comp.get('team', {})
                                    if team_slug in team_info.get('slug', '').lower():
                                        team_score = team_comp.get('score', 0)
                                    elif team_comp.get('homeAway') != competitors[0].get('homeAway'):
                                        opponent_score = team_comp.get('score', 0)

                                if team_score is not None and opponent_score is not None:
                                    result = 'W' if team_score > opponent_score else ('L' if team_score < opponent_score else 'T')
                                    team_games.append(result)

                # Get last 5 games
                last_5 = team_games[-5:] if len(team_games) >= 5 else team_games

                if last_5:
                    wins = last_5.count('W')
                    losses = last_5.count('L')
                    return f"{wins}-{losses}"
                else:
                    return "0-0"

        except Exception as e:
            logger.error(f"Error calculating last 5 performance for {team_slug}: {e}")
            return None

    def fetch_live_game_stats(self, game_id: str) -> Optional[Dict]:
        """
        Fetch detailed live game statistics for a specific NFL game
        Returns live boxscore data for both teams
        """
        try:
            summary_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={game_id}"
            response = self.session.get(summary_url, timeout=15)

            if response.status_code != 200:
                logger.warning(f"Game summary not available for game {game_id}")
                return self._get_basic_game_stats(game_id)

            summary_data = response.json()

            # Extract boxscore statistics
            boxscore = summary_data.get('boxscore', {})

            if not boxscore:
                return self._get_basic_game_stats(game_id)

            teams_data = boxscore.get('teams', [])

            if len(teams_data) < 2:
                return self._get_basic_game_stats(game_id)

            home_team = None
            away_team = None

            # Determine home/away teams
            for team_data in teams_data:
                team_info = team_data.get('team', {})
                home_away = team_info.get('homeAway', '')

                if home_away == 'home':
                    home_team = team_data
                elif home_away == 'away':
                    away_team = team_data

            if not home_team or not away_team:
                return self._get_basic_game_stats(game_id)

            # Extract live statistics for both teams
            home_stats = self._parse_live_team_stats(home_team)
            away_stats = self._parse_live_team_stats(away_team)

            return {
                'home_team_stats': home_stats,
                'away_team_stats': away_stats,
                'game_status': summary_data.get('header', {}).get('competitions', [{}])[0].get('status', {})
            }

        except Exception as e:
            logger.error(f"Error fetching live game stats for game {game_id}: {e}")
            return self._get_basic_game_stats(game_id)

    def _parse_live_team_stats(self, team_data: Dict) -> Dict:
        """Parse live statistics for a single team from boxscore data"""
        team_info = team_data.get('team', {})
        team_name = team_info.get('displayName', '')
        team_abbr = team_info.get('abbreviation', '')

        # Initialize stats
        stats = {
            'team_name': team_name,
            'team_abbr': team_abbr,
            'points': 0,
            'first_downs': None,
            'total_yards': None,
            'passing_yards': None,
            'rushing_yards': None,
            'turnovers': None,
            'penalties': None,
            'possessions': None,
            'time_of_possession': None
        }

        # Get score from team data
        score = team_data.get('score', 0)
        stats['points'] = score

        # Parse detailed statistics
        statistics = team_data.get('statistics', [])

        for stat in statistics:
            stat_name = stat.get('name', '').lower().replace(' ', '_').replace('/', '_').replace('-', '_')
            stat_value = stat.get('displayValue', '')

            # Map ESPN stat names to our format
            if stat_name in ['first_downs', 'total_yards', 'passing_yards', 'rushing_yards', 'turnovers', 'penalties']:
                stats[stat_name] = stat_value
            elif 'time_of_possession' in stat_name:
                stats['time_of_possession'] = stat_value
            elif 'possessions' in stat_name:
                stats['possessions'] = stat_value
            elif 'third_down_eff' in stat_name or 'third_down_efficiency' in stat_name:
                stats['third_down_pct'] = stat_value
            elif 'fourth_down_eff' in stat_name or 'fourth_down_efficiency' in stat_name:
                stats['fourth_down_pct'] = stat_value
            elif 'completions' in stat_name:
                stats['pass_completions'] = stat_value
            elif 'rushing_attempts' in stat_name:
                stats['rush_attempts'] = stat_value
            elif 'sacks_yards_lost' in stat_name:
                stats['sacks_yards'] = stat_value

        # Calculate additional metrics
        if stats.get('total_yards'):
            try:
                yards = float(stats['total_yards'])
                # Rough yards per play calculation (total yards / estimated plays)
                # This is approximate since we don't have the exact number of plays
                stats['yards_per_play'] = round(yards / 10, 1) if yards > 0 else 0
            except (ValueError, TypeError):
                pass

        return stats

    def _get_basic_game_stats(self, game_id: str) -> Optional[Dict]:
        """Fallback method to get basic game stats when detailed summary isn't available"""
        try:
            # Get basic scoreboard data
            scoreboard = self.fetch_scoreboard()
            events = scoreboard.get('events', [])

            for event in events:
                if str(event.get('id')) == str(game_id):
                    competitions = event.get('competitions', [])
                    if competitions:
                        comp = competitions[0]
                        competitors = comp.get('competitors', [])

                        if len(competitors) >= 2:
                            home_team = None
                            away_team = None

                            for comp_team in competitors:
                                home_away = comp_team.get('homeAway', '')
                                team_info = comp_team.get('team', {})
                                score = comp_team.get('score', 0)

                                team_stats = {
                                    'team_name': team_info.get('displayName', ''),
                                    'team_abbr': team_info.get('abbreviation', ''),
                                    'points': score,
                                    'first_downs': None,
                                    'total_yards': None,
                                    'passing_yards': None,
                                    'rushing_yards': None,
                                    'turnovers': None,
                                    'penalties': None,
                                    'possessions': None,
                                    'time_of_possession': None
                                }

                                if home_away == 'home':
                                    home_team = team_stats
                                elif home_away == 'away':
                                    away_team = team_stats

                            if home_team and away_team:
                                return {
                                    'home_team_stats': home_team,
                                    'away_team_stats': away_team,
                                    'game_status': comp.get('status', {})
                                }

            return None

        except Exception as e:
            logger.error(f"Error getting basic game stats for {game_id}: {e}")
            return None

    def get_team_recent_form(self, team_abbr: str, num_games: int = 5) -> List[Dict]:
        """Get recent game results for a team"""
        try:
            team_slug = team_abbr.lower().replace(' ', '-')
            history_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_slug}/schedule"
            response = self.session.get(history_url, timeout=15)

            if response.status_code != 200:
                return []

            data = response.json()
            events = data.get('events', [])

            recent_games = []
            completed_count = 0

            # Get most recent completed games
            for event in reversed(events):
                if completed_count >= num_games:
                    break

                competitions = event.get('competitions', [])
                if competitions:
                    comp = competitions[0]
                    status = comp.get('status', {}).get('type', {}).get('state', '')

                    if status == 'post':
                        competitors = comp.get('competitors', [])
                        if len(competitors) >= 2:

                            team_info = None
                            opponent_info = None
                            team_score = 0
                            opponent_score = 0

                            for comp_team in competitors:
                                team_data = comp_team.get('team', {})
                                score = comp_team.get('score', 0)
                                if team_slug in team_data.get('slug', '').lower():
                                    team_info = team_data
                                    team_score = score
                                else:
                                    opponent_info = team_data
                                    opponent_score = score

                            if team_info:
                                result = 'win' if team_score > opponent_score else ('loss' if team_score < opponent_score else 'tie')
                                recent_games.append({
                                    'opponent': opponent_info.get('displayName', '') if opponent_info else '',
                                    'score': f"{team_score}-{opponent_score}",
                                    'result': result,
                                    'margin': team_score - opponent_score
                                })
                                completed_count += 1

            return recent_games[:num_games]

        except Exception as e:
            logger.error(f"Error getting recent form for {team_abbr}: {e}")
            return []
