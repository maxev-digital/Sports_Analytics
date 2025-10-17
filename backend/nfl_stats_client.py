"""NFL/NCAAF Team Stats Client for season statistics"""
import httpx
import logging
from typing import Dict, Optional
from datetime import datetime
from models import NFLTeamStats

logger = logging.getLogger(__name__)

class NFLStatsClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.nfl_base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        self.ncaaf_base_url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football"
        self.team_stats_cache = {}  # Cache team stats
        self.all_team_stats_cache = {}  # Cache all team stats for ranking calculation
        self.cache_timestamp = None

        # NCAAF Power 5 team mappings (using ESPN team IDs)
        self.ncaaf_teams = {
            # SEC
            'Alabama Crimson Tide': '333', 'Arkansas Razorbacks': '8', 'Auburn Tigers': '2',
            'Florida Gators': '57', 'Georgia Bulldogs': '61', 'Kentucky Wildcats': '96',
            'LSU Tigers': '99', 'Ole Miss Rebels': '145', 'Mississippi State Bulldogs': '344',
            'Missouri Tigers': '142', 'South Carolina Gamecocks': '2579', 'Tennessee Volunteers': '2633',
            'Texas A&M Aggies': '245', 'Vanderbilt Commodores': '238', 'Texas Longhorns': '251',
            'Oklahoma Sooners': '201',

            # Big Ten
            'Illinois Fighting Illini': '356', 'Indiana Hoosiers': '84', 'Iowa Hawkeyes': '2294',
            'Maryland Terrapins': '120', 'Michigan Wolverines': '130', 'Michigan State Spartans': '127',
            'Minnesota Golden Gophers': '135', 'Nebraska Cornhuskers': '158', 'Northwestern Wildcats': '77',
            'Ohio State Buckeyes': '194', 'Penn State Nittany Lions': '213', 'Purdue Boilermakers': '2509',
            'Rutgers Scarlet Knights': '164', 'Wisconsin Badgers': '275', 'UCLA Bruins': '26',
            'USC Trojans': '30', 'Oregon Ducks': '2483', 'Washington Huskies': '264',

            # Big 12
            'Baylor Bears': '239', 'BYU Cougars': '252', 'Cincinnati Bearcats': '2132',
            'Houston Cougars': '248', 'Iowa State Cyclones': '66', 'Kansas Jayhawks': '2305',
            'Kansas State Wildcats': '2306', 'Oklahoma State Cowboys': '197', 'TCU Horned Frogs': '2628',
            'Texas Tech Red Raiders': '2641', 'UCF Knights': '2116', 'West Virginia Mountaineers': '277',
            'Arizona Wildcats': '12', 'Arizona State Sun Devils': '9', 'Colorado Buffaloes': '38',
            'Utah Utes': '254',

            # ACC
            'Boston College Eagles': '103', 'Clemson Tigers': '228', 'Duke Blue Devils': '150',
            'Florida State Seminoles': '52', 'Georgia Tech Yellow Jackets': '59', 'Louisville Cardinals': '97',
            'Miami Hurricanes': '2390', 'NC State Wolfpack': '152', 'North Carolina Tar Heels': '153',
            'Pittsburgh Panthers': '221', 'Syracuse Orange': '183', 'Virginia Cavaliers': '258',
            'Virginia Tech Hokies': '259', 'Wake Forest Demon Deacons': '154', 'California Golden Bears': '25',
            'SMU Mustangs': '2567', 'Stanford Cardinal': '24',

            # Notable Independents & Others
            'Notre Dame Fighting Irish': '87', 'Army Black Knights': '349', 'Navy Midshipmen': '2426',
        }

    async def get_team_season_stats(self, team_abbr: str, is_ncaaf: bool = False) -> Optional[NFLTeamStats]:
        """
        Fetch team season statistics from ESPN API
        Returns comprehensive season stats for pregame analysis

        Args:
            team_abbr: For NFL, the team abbreviation (e.g., 'CIN'). For NCAAF, the full team name.
            is_ncaaf: True if this is a college football team, False for NFL
        """
        try:
            # Check cache first (refresh every 6 hours)
            cache_key = f"{'ncaaf' if is_ncaaf else 'nfl'}_{team_abbr}"
            if (self.cache_timestamp and
                (datetime.now() - self.cache_timestamp).total_seconds() < 21600 and
                cache_key in self.team_stats_cache):
                return self.team_stats_cache[cache_key]

            # Get current season year
            current_year = datetime.now().year
            current_month = datetime.now().month
            # Football season spans two years: Sep-Feb for NFL, Aug-Jan for NCAAF
            if current_month >= 8:  # August or later = new season
                season = current_year
            else:
                season = current_year - 1

            base_url = self.ncaaf_base_url if is_ncaaf else self.nfl_base_url

            if is_ncaaf:
                # For NCAAF, we have the team ID directly from the mapping
                team_id = self.ncaaf_teams.get(team_abbr)
                if not team_id:
                    logger.warning(f"Could not find NCAAF team: {team_abbr}")
                    return None
                team_name = team_abbr
            else:
                # For NFL, fetch team info to get team ID from abbreviation
                url = f"{base_url}/teams"
                response = await self.client.get(url)
                response.raise_for_status()
                teams_data = response.json()

                # Find team by abbreviation
                team_info = None
                for team in teams_data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
                    team_data = team.get('team', {})
                    if team_data.get('abbreviation', '').lower() == team_abbr.lower():
                        team_info = team_data
                        break

                if not team_info:
                    logger.warning(f"Could not find NFL team: {team_abbr}")
                    return None

                team_id = team_info.get('id')
                team_name = team_info.get('displayName', team_abbr.upper())

            # Fetch team statistics
            stats_url = f"{base_url}/teams/{team_id}/statistics"
            response = await self.client.get(stats_url)
            response.raise_for_status()
            stats_data = response.json()

            # Extract stats and rankings from categories
            stats_obj = {}
            ranks_obj = {}
            for category in stats_data.get('results', {}).get('stats', {}).get('categories', []):
                for stat in category.get('stats', []):
                    stat_name = stat.get('name', '')
                    stats_obj[stat_name] = stat.get('value', 0)
                    # Extract rank if available
                    if 'rank' in stat:
                        ranks_obj[stat_name] = stat.get('rank', None)

            # Get games played from stats (more reliable than record parsing)
            games_played = int(stats_obj.get('gamesPlayed', 0))

            # Parse record if available
            record = team_info.get('record', {}).get('items', [{}])[0].get('summary', '0-0')
            record_parts = record.split('-')
            wins = int(record_parts[0]) if len(record_parts) > 0 and record_parts[0].isdigit() else 0
            losses = int(record_parts[1]) if len(record_parts) > 1 and record_parts[1].isdigit() else 0
            ties = int(record_parts[2]) if len(record_parts) > 2 and record_parts[2].isdigit() else 0
            win_pct = round(wins / games_played, 3) if games_played > 0 else 0.000

            # Build stat values with defaults (using per-game values where available)
            points_per_game = float(stats_obj.get('totalPointsPerGame', 0))
            # Note: ESPN doesn't provide defensive stats directly - would need opponent data
            points_allowed = 0.0  # TODO: Calculate from opponent scoring or use different API
            point_differential = 0.0  # TODO: Calculate properly

            total_yards = float(stats_obj.get('totalYards', 0)) / games_played if games_played > 0 else 0.0
            yards_allowed = 0.0  # TODO: Would need defensive API endpoint
            passing_yards = float(stats_obj.get('passingYardsPerGame', 0))
            rushing_yards = float(stats_obj.get('rushingYardsPerGame', 0))

            turnovers = float(stats_obj.get('totalGiveaways', 0)) / games_played if games_played > 0 else 0.0
            takeaways = float(stats_obj.get('totalTakeaways', 0)) / games_played if games_played > 0 else 0.0
            turnover_diff = float(stats_obj.get('turnOverDifferential', 0)) / games_played if games_played > 0 else 0.0

            third_down_pct = float(stats_obj.get('thirdDownConvPct', 0)) / 100.0
            red_zone_pct = float(stats_obj.get('redzoneScoringPct', 0)) / 100.0
            sacks = float(stats_obj.get('sacks', 0)) / games_played if games_played > 0 else 0.0  # Defensive sacks

            # Calculate form trend (last 5 games approximation based on win%)
            if win_pct >= 0.6:
                form_trend = "HOT"
            elif win_pct <= 0.4:
                form_trend = "COLD"
            else:
                form_trend = "NEUTRAL"

            # Get last 5 record (simplified - would need game log API for accuracy)
            last_5_record = None  # TODO: Could fetch from game log

            # Create stats object (rankings will be added later)
            nfl_stats = NFLTeamStats(
                team_id=team_abbr,
                team_name=team_name,
                games_played=games_played,
                wins=wins,
                losses=losses,
                ties=ties,
                win_pct=win_pct,
                points_per_game=points_per_game,
                points_allowed_per_game=points_allowed,
                point_differential=point_differential,
                total_yards_per_game=total_yards,
                yards_allowed_per_game=yards_allowed,
                passing_yards_per_game=passing_yards,
                rushing_yards_per_game=rushing_yards,
                turnovers_per_game=turnovers,
                takeaways_per_game=takeaways,
                turnover_differential=turnover_diff,
                third_down_pct=third_down_pct,
                red_zone_pct=red_zone_pct,
                sacks_per_game=sacks,
                last_5_record=last_5_record,
                form_trend=form_trend,
                home_record=None,
                away_record=None,
                division_record=None,
                conference_record=None
            )

            # Cache the result
            self.team_stats_cache[cache_key] = nfl_stats
            self.cache_timestamp = datetime.now()

            return nfl_stats

        except Exception as e:
            logger.error(f"Error fetching NFL season stats for {team_abbr}: {e}")
            return None

    async def get_team_stats_with_rankings(self, team_abbr: str, is_ncaaf: bool = False) -> Optional[NFLTeamStats]:
        """Get team stats with calculated rankings"""
        # First ensure all teams are fetched and rankings are calculated
        if not is_ncaaf:  # Only for NFL, not NCAAF yet
            all_teams = await self.fetch_all_nfl_teams_and_calculate_rankings()
            if team_abbr in all_teams:
                # Return the team stats with rankings from the all teams cache
                return NFLTeamStats(**all_teams[team_abbr])

        # Fallback to regular method (without rankings)
        return await self.get_team_season_stats(team_abbr, is_ncaaf)

    async def fetch_all_nfl_teams_and_calculate_rankings(self) -> Dict[str, Dict]:
        """Fetch all 32 NFL teams and calculate rankings by sorting"""
        try:
            # Check if we have cached all team stats (refresh every 6 hours)
            if (self.cache_timestamp and
                (datetime.now() - self.cache_timestamp).total_seconds() < 21600 and
                self.all_team_stats_cache):
                logger.info("Using cached NFL team rankings")
                return self.all_team_stats_cache

            logger.info("Fetching all NFL teams to calculate rankings...")

            # Fetch list of all NFL teams
            url = f"{self.nfl_base_url}/teams"
            response = await self.client.get(url)
            response.raise_for_status()
            teams_data = response.json()

            all_teams_list = []

            # Get stats for each team
            for team in teams_data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
                team_data = team.get('team', {})
                team_abbr = team_data.get('abbreviation', '')

                if not team_abbr:
                    continue

                # Fetch this team's stats (without rankings yet)
                team_stat = await self.get_team_season_stats(team_abbr, is_ncaaf=False)
                if team_stat:
                    all_teams_list.append(team_stat.dict())

            # Now calculate rankings by sorting
            # Points per game (higher is better)
            sorted_by_ppg = sorted(all_teams_list, key=lambda x: x['points_per_game'], reverse=True)
            for rank, team in enumerate(sorted_by_ppg, 1):
                team['points_per_game_rank'] = rank

            # Total yards per game (higher is better)
            sorted_by_yards = sorted(all_teams_list, key=lambda x: x['total_yards_per_game'], reverse=True)
            for rank, team in enumerate(sorted_by_yards, 1):
                team['total_yards_per_game_rank'] = rank

            # Passing yards per game (higher is better)
            sorted_by_pass = sorted(all_teams_list, key=lambda x: x['passing_yards_per_game'], reverse=True)
            for rank, team in enumerate(sorted_by_pass, 1):
                team['passing_yards_per_game_rank'] = rank

            # Rushing yards per game (higher is better)
            sorted_by_rush = sorted(all_teams_list, key=lambda x: x['rushing_yards_per_game'], reverse=True)
            for rank, team in enumerate(sorted_by_rush, 1):
                team['rushing_yards_per_game_rank'] = rank

            # Third down % (higher is better)
            sorted_by_3rd = sorted(all_teams_list, key=lambda x: x['third_down_pct'], reverse=True)
            for rank, team in enumerate(sorted_by_3rd, 1):
                team['third_down_pct_rank'] = rank

            # Red zone % (higher is better)
            sorted_by_rz = sorted(all_teams_list, key=lambda x: x['red_zone_pct'], reverse=True)
            for rank, team in enumerate(sorted_by_rz, 1):
                team['red_zone_pct_rank'] = rank

            # Sacks (higher is better for defense)
            sorted_by_sacks = sorted(all_teams_list, key=lambda x: x['sacks_per_game'], reverse=True)
            for rank, team in enumerate(sorted_by_sacks, 1):
                team['sacks_rank'] = rank

            # Turnover differential (higher is better)
            sorted_by_to = sorted(all_teams_list, key=lambda x: x['turnover_differential'], reverse=True)
            for rank, team in enumerate(sorted_by_to, 1):
                team['turnover_differential_rank'] = rank

            # Convert list to dict keyed by team_id for easy lookup
            all_teams_dict = {team['team_id']: team for team in all_teams_list}

            # Cache the results
            self.all_team_stats_cache = all_teams_dict

            logger.info(f"Calculated rankings for {len(all_teams_dict)} NFL teams")
            return all_teams_dict

        except Exception as e:
            logger.error(f"Error fetching all NFL teams for rankings: {e}")
            return {}

    async def close(self):
        await self.client.aclose()
