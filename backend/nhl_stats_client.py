"""NHL Live Stats Client for momentum tracking and season stats"""
import httpx
import logging
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path
import pandas as pd
from live_models import NHLTeamStats

logger = logging.getLogger(__name__)

class NHLStatsClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = "https://api-web.nhle.com/v1"
        self.season_stats_cache = {}  # Cache season stats
        self.all_team_stats_cache = {}  # Cache all team stats for ranking calculation
        self.cache_timestamp = None
        self.en_stats_cache = None  # Cache empty net stats

    def load_empty_net_stats(self) -> Dict[str, Dict]:
        """
        Load empty net statistics from CSV file
        Returns dict keyed by team_abbr with EN stats
        """
        try:
            # Look for latest empty net CSV
            data_dir = Path(__file__).parent / "data" / "raw" / "nhl"
            en_file = data_dir / "empty_net_stats_latest.csv"

            if not en_file.exists():
                logger.warning(f"Empty net stats file not found: {en_file}")
                return {}

            df = pd.read_csv(en_file)
            logger.info(f"Loaded empty net stats for {len(df)} teams")

            # Convert to dict keyed by team_abbr
            en_dict = {}
            for _, row in df.iterrows():
                team_abbr = row['team_abbr']
                en_dict[team_abbr] = {
                    'en_goals_for': float(row['en_goals_for']) if pd.notna(row['en_goals_for']) else 0.0,
                    'en_goals_against': float(row['en_goals_against']) if pd.notna(row['en_goals_against']) else 0.0,
                    'en_differential': float(row['en_differential']) if pd.notna(row['en_differential']) else 0.0,
                    'en_situations': float(row['en_situations']) if pd.notna(row['en_situations']) else 0.0,
                    'en_success_rate': float(row['en_success_rate']) if pd.notna(row['en_success_rate']) else 0.0,
                }

            self.en_stats_cache = en_dict
            return en_dict

        except Exception as e:
            logger.error(f"Error loading empty net stats: {e}")
            return {}

    async def get_live_game_stats(self, game_id: str) -> Optional[Dict]:
        """Fetch live game statistics including shots, possession, zone time"""
        try:
            # Get play-by-play data which includes all shots and events
            url = f"{self.base_url}/gamecenter/{game_id}/play-by-play"
            response = await self.client.get(url)
            response.raise_for_status()
            pbp_data = response.json()

            # Get boxscore data for summary stats
            url = f"{self.base_url}/gamecenter/{game_id}/boxscore"
            response = await self.client.get(url)
            response.raise_for_status()
            boxscore = response.json()

            return {
                'play_by_play': pbp_data,
                'boxscore': boxscore
            }
        except Exception as e:
            logger.error(f"Error fetching NHL stats for game {game_id}: {e}")
            return None

    def calculate_recent_momentum(self, pbp_data: Dict, lookback_minutes: int = 5) -> Dict:
        """
        Calculate momentum score based on recent events
        Analyzes last N minutes of play for:
        - Shot attempts
        - Shot quality (scoring chances)
        - Zone entries
        - Faceoff wins
        - Time on attack
        """
        if not pbp_data or 'plays' not in pbp_data:
            return self._empty_momentum()

        plays = pbp_data.get('plays', [])
        if not plays:
            return self._empty_momentum()

        # Get current game time
        current_period = pbp_data.get('periodDescriptor', {}).get('number', 1)

        # Filter for recent plays (last N events as proxy for last N minutes)
        recent_plays = plays[-50:]  # Last 50 events as approximation

        home_stats = {
            'shots': 0,
            'scoring_chances': 0,
            'zone_entries': 0,
            'faceoff_wins': 0,
            'offensive_zone_time': 0
        }

        away_stats = {
            'shots': 0,
            'scoring_chances': 0,
            'zone_entries': 0,
            'faceoff_wins': 0,
            'offensive_zone_time': 0
        }

        for play in recent_plays:
            event_type = play.get('typeDescKey', '')
            details = play.get('details', {})

            # Track shots
            if event_type in ['shot-on-goal', 'missed-shot', 'blocked-shot', 'goal']:
                if play.get('eventOwnerTeamId') == pbp_data.get('homeTeam', {}).get('id'):
                    home_stats['shots'] += 1
                    # Scoring chances are shots from slot/high danger areas
                    if details.get('shotType') in ['Wrist Shot', 'Snap Shot', 'Tip-In', 'Deflection']:
                        home_stats['scoring_chances'] += 1
                else:
                    away_stats['shots'] += 1
                    if details.get('shotType') in ['Wrist Shot', 'Snap Shot', 'Tip-In', 'Deflection']:
                        away_stats['scoring_chances'] += 1

            # Track faceoffs
            elif event_type == 'faceoff':
                winning_team_id = details.get('winningTeamId')
                if winning_team_id == pbp_data.get('homeTeam', {}).get('id'):
                    home_stats['faceoff_wins'] += 1
                else:
                    away_stats['faceoff_wins'] += 1

            # Track zone entries (approximated by dump-in, zone-entry events)
            elif event_type in ['hit', 'takeaway']:
                zone_code = details.get('zoneCode', '')
                if zone_code == 'O':  # Offensive zone
                    if play.get('eventOwnerTeamId') == pbp_data.get('homeTeam', {}).get('id'):
                        home_stats['offensive_zone_time'] += 1
                    else:
                        away_stats['offensive_zone_time'] += 1

        # Calculate momentum scores (0-100 scale)
        total_shots = home_stats['shots'] + away_stats['shots']
        total_faceoffs = home_stats['faceoff_wins'] + away_stats['faceoff_wins']

        if total_shots > 0:
            home_shot_pct = (home_stats['shots'] / total_shots) * 100
            away_shot_pct = (away_stats['shots'] / total_shots) * 100
        else:
            home_shot_pct = away_shot_pct = 50

        if total_faceoffs > 0:
            home_fo_pct = (home_stats['faceoff_wins'] / total_faceoffs) * 100
            away_fo_pct = (away_stats['faceoff_wins'] / total_faceoffs) * 100
        else:
            home_fo_pct = away_fo_pct = 50

        # Weighted momentum formula
        # Shots: 50%, Scoring Chances: 30%, Faceoffs: 10%, Zone Time: 10%
        home_momentum = (
            home_shot_pct * 0.5 +
            (home_stats['scoring_chances'] / max(total_shots, 1) * 100) * 0.3 +
            home_fo_pct * 0.1 +
            (home_stats['offensive_zone_time'] / max(len(recent_plays), 1) * 100) * 0.1
        )

        away_momentum = (
            away_shot_pct * 0.5 +
            (away_stats['scoring_chances'] / max(total_shots, 1) * 100) * 0.3 +
            away_fo_pct * 0.1 +
            (away_stats['offensive_zone_time'] / max(len(recent_plays), 1) * 100) * 0.1
        )

        return {
            'home': {
                'momentum_score': round(home_momentum, 1),
                'recent_shots': home_stats['shots'],
                'scoring_chances': home_stats['scoring_chances'],
                'faceoff_wins': home_stats['faceoff_wins'],
                'offensive_zone_events': home_stats['offensive_zone_time']
            },
            'away': {
                'momentum_score': round(away_momentum, 1),
                'recent_shots': away_stats['shots'],
                'scoring_chances': away_stats['scoring_chances'],
                'faceoff_wins': away_stats['faceoff_wins'],
                'offensive_zone_events': away_stats['offensive_zone_time']
            },
            'period': current_period,
            'lookback_events': len(recent_plays)
        }

    def _empty_momentum(self) -> Dict:
        """Return empty momentum data structure"""
        return {
            'home': {
                'momentum_score': 50.0,
                'recent_shots': 0,
                'scoring_chances': 0,
                'faceoff_wins': 0,
                'offensive_zone_events': 0,
                'power_play_opps': "0/0",
                'penalty_minutes': 0,
                'blocked_shots': 0
            },
            'away': {
                'momentum_score': 50.0,
                'recent_shots': 0,
                'scoring_chances': 0,
                'faceoff_wins': 0,
                'offensive_zone_events': 0,
                'power_play_opps': "0/0",
                'penalty_minutes': 0,
                'blocked_shots': 0
            },
            'period': 1,
            'lookback_events': 0
        }

    async def get_team_season_stats(self, team_abbr: str) -> Optional[Dict]:
        """
        Fetch team season statistics from NHL API
        Returns comprehensive season stats for pregame analysis
        """
        try:
            # Check cache first (refresh every 6 hours)
            if (self.cache_timestamp and
                (datetime.now() - self.cache_timestamp).total_seconds() < 21600 and
                team_abbr in self.season_stats_cache):
                return self.season_stats_cache[team_abbr]

            # Get current season (e.g., 20242025)
            # NOTE: System date may be incorrect, so hardcoding current NHL season
            # TODO: Fix when system date is corrected
            season = "20242025"  # 2024-2025 NHL season

            # Fetch team stats
            url = f"{self.base_url}/club-stats/{team_abbr}/{season}/2"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            # Cache the result
            self.season_stats_cache[team_abbr] = data
            self.cache_timestamp = datetime.now()

            return data

        except Exception as e:
            logger.error(f"Error fetching NHL season stats for {team_abbr}: {e}")
            return None

    def extract_enhanced_momentum_from_pbp(self, pbp_data: Dict, boxscore: Dict) -> Dict:
        """
        Enhanced momentum calculation including PP opportunities and penalties
        """
        if not pbp_data or 'plays' not in pbp_data:
            return self._empty_momentum()

        plays = pbp_data.get('plays', [])
        if not plays:
            return self._empty_momentum()

        # Get team IDs
        home_team_id = pbp_data.get('homeTeam', {}).get('id')
        away_team_id = pbp_data.get('awayTeam', {}).get('id')

        # Filter for recent plays (last 50 events as proxy for last 5 minutes)
        recent_plays = plays[-50:]

        home_stats = {
            'shots': 0,
            'scoring_chances': 0,
            'zone_entries': 0,
            'faceoff_wins': 0,
            'offensive_zone_time': 0,
            'power_plays': 0,
            'pp_goals': 0,
            'penalty_minutes': 0,
            'blocked_shots': 0
        }

        away_stats = {
            'shots': 0,
            'scoring_chances': 0,
            'zone_entries': 0,
            'faceoff_wins': 0,
            'offensive_zone_time': 0,
            'power_plays': 0,
            'pp_goals': 0,
            'penalty_minutes': 0,
            'blocked_shots': 0
        }

        for play in recent_plays:
            event_type = play.get('typeDescKey', '')
            details = play.get('details', {})
            event_owner = play.get('eventOwnerTeamId')

            # Track shots
            if event_type in ['shot-on-goal', 'missed-shot', 'blocked-shot', 'goal']:
                if event_owner == home_team_id:
                    home_stats['shots'] += 1
                    # Scoring chances are shots from slot/high danger areas
                    if details.get('shotType') in ['Wrist Shot', 'Snap Shot', 'Tip-In', 'Deflection']:
                        home_stats['scoring_chances'] += 1
                else:
                    away_stats['shots'] += 1
                    if details.get('shotType') in ['Wrist Shot', 'Snap Shot', 'Tip-In', 'Deflection']:
                        away_stats['scoring_chances'] += 1

            # Track blocked shots (defensive metric)
            if event_type == 'blocked-shot':
                # Blocking team gets credit
                blocking_team = play.get('eventOwnerTeamId')  # This might need adjustment
                if blocking_team == home_team_id:
                    away_stats['blocked_shots'] += 1  # Away blocked home's shot
                else:
                    home_stats['blocked_shots'] += 1

            # Track faceoffs
            elif event_type == 'faceoff':
                winning_team_id = details.get('winningTeamId')
                if winning_team_id == home_team_id:
                    home_stats['faceoff_wins'] += 1
                else:
                    away_stats['faceoff_wins'] += 1

            # Track penalties
            elif event_type == 'penalty':
                penalty_team = event_owner
                duration = details.get('duration', 2)  # Default 2 min minor
                if penalty_team == home_team_id:
                    home_stats['penalty_minutes'] += duration
                    away_stats['power_plays'] += 1  # Opposing team gets PP
                else:
                    away_stats['penalty_minutes'] += duration
                    home_stats['power_plays'] += 1

            # Track PP goals
            elif event_type == 'goal':
                if details.get('strength') == 'PPG':  # Power play goal
                    if event_owner == home_team_id:
                        home_stats['pp_goals'] += 1
                    else:
                        away_stats['pp_goals'] += 1

            # Track zone entries (approximated by dump-in, zone-entry events)
            elif event_type in ['hit', 'takeaway']:
                zone_code = details.get('zoneCode', '')
                if zone_code == 'O':  # Offensive zone
                    if event_owner == home_team_id:
                        home_stats['offensive_zone_time'] += 1
                    else:
                        away_stats['offensive_zone_time'] += 1

        # Calculate momentum scores (0-100 scale)
        total_shots = home_stats['shots'] + away_stats['shots']
        total_faceoffs = home_stats['faceoff_wins'] + away_stats['faceoff_wins']

        if total_shots > 0:
            home_shot_pct = (home_stats['shots'] / total_shots) * 100
            away_shot_pct = (away_stats['shots'] / total_shots) * 100
        else:
            home_shot_pct = away_shot_pct = 50

        if total_faceoffs > 0:
            home_fo_pct = (home_stats['faceoff_wins'] / total_faceoffs) * 100
            away_fo_pct = (away_stats['faceoff_wins'] / total_faceoffs) * 100
        else:
            home_fo_pct = away_fo_pct = 50

        # Weighted momentum formula
        # Shots: 50%, Scoring Chances: 30%, Faceoffs: 10%, Zone Time: 10%
        home_momentum = (
            home_shot_pct * 0.5 +
            (home_stats['scoring_chances'] / max(total_shots, 1) * 100) * 0.3 +
            home_fo_pct * 0.1 +
            (home_stats['offensive_zone_time'] / max(len(recent_plays), 1) * 100) * 0.1
        )

        away_momentum = (
            away_shot_pct * 0.5 +
            (away_stats['scoring_chances'] / max(total_shots, 1) * 100) * 0.3 +
            away_fo_pct * 0.1 +
            (away_stats['offensive_zone_time'] / max(len(recent_plays), 1) * 100) * 0.1
        )

        return {
            'home': {
                'momentum_score': round(home_momentum, 1),
                'recent_shots': home_stats['shots'],
                'scoring_chances': home_stats['scoring_chances'],
                'faceoff_wins': home_stats['faceoff_wins'],
                'offensive_zone_events': home_stats['offensive_zone_time'],
                'power_play_opps': f"{home_stats['pp_goals']}/{home_stats['power_plays']}" if home_stats['power_plays'] > 0 else "0/0",
                'penalty_minutes': home_stats['penalty_minutes'],
                'blocked_shots': home_stats['blocked_shots']
            },
            'away': {
                'momentum_score': round(away_momentum, 1),
                'recent_shots': away_stats['shots'],
                'scoring_chances': away_stats['scoring_chances'],
                'faceoff_wins': away_stats['faceoff_wins'],
                'offensive_zone_events': away_stats['offensive_zone_time'],
                'power_play_opps': f"{away_stats['pp_goals']}/{away_stats['power_plays']}" if away_stats['power_plays'] > 0 else "0/0",
                'penalty_minutes': away_stats['penalty_minutes'],
                'blocked_shots': away_stats['blocked_shots']
            },
            'period': pbp_data.get('periodDescriptor', {}).get('number', 1),
            'lookback_events': len(recent_plays)
        }

    async def get_team_stats_with_rankings(self, team_abbr: str) -> Optional[NHLTeamStats]:
        """Get team stats with calculated rankings"""
        # Fetch all 32 NHL teams and calculate rankings
        all_teams = await self.fetch_all_nhl_teams_and_calculate_rankings()
        logger.info(f"[NHL RANKINGS] Got {len(all_teams)} teams, looking for '{team_abbr}'")
        if team_abbr in all_teams:
            # Return the team stats with rankings included
            team_stats = all_teams[team_abbr]
            logger.info(f"[NHL RANKINGS] Found {team_abbr}: GPG rank = {team_stats.goals_per_game_rank}")
            return team_stats

        # Fallback to regular method (without rankings)
        logger.warning(f"[NHL RANKINGS] Team '{team_abbr}' not found in all_teams dict. Available: {list(all_teams.keys())[:5]}...")
        return None

    async def fetch_all_nhl_teams_and_calculate_rankings(self) -> Dict[str, NHLTeamStats]:
        """Fetch all 32 NHL teams and calculate rankings by sorting"""
        try:
            # Check if we have cached all team stats (refresh every 6 hours)
            if (self.cache_timestamp and
                (datetime.now() - self.cache_timestamp).total_seconds() < 21600 and
                self.all_team_stats_cache):
                logger.info("Using cached NHL team rankings")
                return self.all_team_stats_cache

            logger.info("Fetching all NHL teams to calculate rankings...")

            # Load empty net statistics
            en_stats = self.load_empty_net_stats()

            all_teams_list = []

            # Fetch current standings from the correct endpoint
            url = f"{self.base_url}/standings/now"
            response = await self.client.get(url, follow_redirects=True)
            response.raise_for_status()
            standings_data = response.json()

            # Get all teams from standings
            standings_list = standings_data.get('standings', [])

            # Process each team
            for team_standing in standings_list:
                try:
                    # Extract team info
                    team_abbr = team_standing.get('teamAbbrev', {}).get('default', '').lower()
                    team_name = team_standing.get('teamName', {}).get('default', team_abbr.upper())

                    # Extract record and stats
                    games_played = team_standing.get('gamesPlayed', 0)
                    wins = team_standing.get('wins', 0)
                    losses = team_standing.get('losses', 0)
                    ot_losses = team_standing.get('otLosses', 0)
                    points = team_standing.get('points', 0)

                    # Extract goals
                    goals_for = team_standing.get('goalFor', 0)
                    goals_against = team_standing.get('goalAgainst', 0)
                    goal_differential = team_standing.get('goalDifferential', 0)

                    # Calculate per-game averages
                    goals_per_game = goals_for / games_played if games_played > 0 else 0.0
                    goals_against_per_game = goals_against / games_played if games_played > 0 else 0.0

                    # Calculate win percentage
                    win_pct = wins / games_played if games_played > 0 else 0.0

                    # Form trend based on recent record
                    streak_code = team_standing.get('streakCode', '')
                    streak_count = team_standing.get('streakCount', 0)

                    if streak_code == 'W' and streak_count >= 3:
                        form_trend = "HOT"
                    elif streak_code == 'L' and streak_count >= 3:
                        form_trend = "COLD"
                    else:
                        form_trend = "NEUTRAL"

                    # Get last 10 record
                    l10_wins = team_standing.get('l10Wins', 0)
                    l10_losses = team_standing.get('l10Losses', 0)
                    l10_ot_losses = team_standing.get('l10OtLosses', 0)
                    last_10_record = f"{l10_wins}-{l10_losses}-{l10_ot_losses}"

                    # NOTE: The /standings endpoint doesn't include advanced stats like shots, PP%, PK%, etc.
                    # For now, we'll use placeholder values. Could fetch from /club-stats if needed.
                    shots_per_game = 0.0  # TODO: Fetch from club-stats if needed
                    shots_against_per_game = 0.0
                    power_play_pct = 0.0
                    penalty_kill_pct = 0.0
                    faceoff_win_pct = 0.0
                    shooting_pct = 0.0
                    save_pct = 0.0
                    pdo = 100.0  # Neutral PDO

                    # Get empty net stats for this team
                    team_en_stats = en_stats.get(team_abbr, {})

                    # Add to list as dict (rankings will be added later)
                    team_dict = {
                        'team_id': team_abbr,
                        'team_name': team_name,
                        'games_played': games_played,
                        'wins': wins,
                        'losses': losses,
                        'ot_losses': ot_losses,
                        'points': points,
                        'win_pct': win_pct,
                        'goals_per_game': goals_per_game,
                        'goals_against_per_game': goals_against_per_game,
                        'shots_per_game': shots_per_game,
                        'shots_against_per_game': shots_against_per_game,
                        'power_play_pct': power_play_pct,
                        'penalty_kill_pct': penalty_kill_pct,
                        'faceoff_win_pct': faceoff_win_pct,
                        'shooting_pct': shooting_pct,
                        'save_pct': save_pct,
                        'pdo': pdo,
                        'last_10_record': last_10_record,
                        'form_trend': form_trend,
                        'home_record': None,
                        'away_record': None,
                        # Empty net statistics
                        'en_goals_for': team_en_stats.get('en_goals_for', 0.0),
                        'en_goals_against': team_en_stats.get('en_goals_against', 0.0),
                        'en_differential': team_en_stats.get('en_differential', 0.0),
                        'en_situations': team_en_stats.get('en_situations', 0.0),
                        'en_success_rate': team_en_stats.get('en_success_rate', 0.0),
                    }
                    all_teams_list.append(team_dict)

                except Exception as e:
                    team_name = team_standing.get('teamAbbrev', {}).get('default', 'Unknown')
                    logger.warning(f"Error processing NHL stats for {team_name}: {e}")
                    continue

            # Now calculate rankings by sorting
            # Goals per game (higher is better)
            sorted_by_gpg = sorted(all_teams_list, key=lambda x: x['goals_per_game'], reverse=True)
            for rank, team in enumerate(sorted_by_gpg, 1):
                team['goals_per_game_rank'] = rank

            # Goals against per game (lower is better for defense)
            sorted_by_gapg = sorted(all_teams_list, key=lambda x: x['goals_against_per_game'])
            for rank, team in enumerate(sorted_by_gapg, 1):
                team['goals_against_per_game_rank'] = rank

            # Shots per game (higher is better)
            sorted_by_spg = sorted(all_teams_list, key=lambda x: x['shots_per_game'], reverse=True)
            for rank, team in enumerate(sorted_by_spg, 1):
                team['shots_per_game_rank'] = rank

            # Shots against per game (lower is better for defense)
            sorted_by_sapg = sorted(all_teams_list, key=lambda x: x['shots_against_per_game'])
            for rank, team in enumerate(sorted_by_sapg, 1):
                team['shots_against_per_game_rank'] = rank

            # Power play % (higher is better)
            sorted_by_pp = sorted(all_teams_list, key=lambda x: x['power_play_pct'], reverse=True)
            for rank, team in enumerate(sorted_by_pp, 1):
                team['power_play_pct_rank'] = rank

            # Penalty kill % (higher is better)
            sorted_by_pk = sorted(all_teams_list, key=lambda x: x['penalty_kill_pct'], reverse=True)
            for rank, team in enumerate(sorted_by_pk, 1):
                team['penalty_kill_pct_rank'] = rank

            # Faceoff win % (higher is better)
            sorted_by_fo = sorted(all_teams_list, key=lambda x: x['faceoff_win_pct'], reverse=True)
            for rank, team in enumerate(sorted_by_fo, 1):
                team['faceoff_win_pct_rank'] = rank

            # Shooting % (higher is better)
            sorted_by_sh = sorted(all_teams_list, key=lambda x: x['shooting_pct'], reverse=True)
            for rank, team in enumerate(sorted_by_sh, 1):
                team['shooting_pct_rank'] = rank

            # Save % (higher is better)
            sorted_by_sv = sorted(all_teams_list, key=lambda x: x['save_pct'], reverse=True)
            for rank, team in enumerate(sorted_by_sv, 1):
                team['save_pct_rank'] = rank

            # PDO (closer to 100 is normal, but higher is generally better)
            sorted_by_pdo = sorted(all_teams_list, key=lambda x: x['pdo'], reverse=True)
            for rank, team in enumerate(sorted_by_pdo, 1):
                team['pdo_rank'] = rank

            # Empty Net Goals For (higher is better)
            sorted_by_engf = sorted(all_teams_list, key=lambda x: x['en_goals_for'], reverse=True)
            for rank, team in enumerate(sorted_by_engf, 1):
                team['en_goals_for_rank'] = rank

            # Empty Net Goals Against (lower is better)
            sorted_by_enga = sorted(all_teams_list, key=lambda x: x['en_goals_against'])
            for rank, team in enumerate(sorted_by_enga, 1):
                team['en_goals_against_rank'] = rank

            # Empty Net Differential (higher is better)
            sorted_by_endiff = sorted(all_teams_list, key=lambda x: x['en_differential'], reverse=True)
            for rank, team in enumerate(sorted_by_endiff, 1):
                team['en_differential_rank'] = rank

            # Convert list to NHLTeamStats objects keyed by team_id for easy lookup
            all_teams_dict = {}
            for team_dict in all_teams_list:
                team_stats = NHLTeamStats(**team_dict)
                all_teams_dict[team_dict['team_id']] = team_stats

            # Cache the results
            self.all_team_stats_cache = all_teams_dict
            self.cache_timestamp = datetime.now()

            logger.info(f"Calculated rankings for {len(all_teams_dict)} NHL teams")
            return all_teams_dict

        except Exception as e:
            logger.error(f"Error fetching all NHL teams for rankings: {e}")
            return {}

    async def close(self):
        await self.client.aclose()

