"""
MLB Stats Client - Fetches team statistics from ESPN API
Similar to NHL stats client, provides comprehensive batting and pitching statistics
with rankings across all 30 MLB teams.
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from live_models import MLBTeamStats

class MLBStatsClient:
    """Client for fetching MLB team statistics from ESPN API"""

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb"

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._stats_cache = {}
        self._cache_expiry = {}
        self.cache_duration = timedelta(hours=6)  # Cache stats for 6 hours

    async def ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_team_info(self) -> Dict[str, Dict]:
        """
        Fetch all MLB team information including team IDs and abbreviations.
        Returns a mapping of team abbreviations to team data.
        """
        await self.ensure_session()

        try:
            url = f"{self.BASE_URL}/teams"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    print(f"Error fetching team info: {response.status}")
                    return {}

                data = await response.json()
                teams = {}

                # Extract team data from sports array
                if 'sports' in data and len(data['sports']) > 0:
                    leagues = data['sports'][0].get('leagues', [])
                    if leagues:
                        team_list = leagues[0].get('teams', [])
                        for team_obj in team_list:
                            team = team_obj.get('team', {})
                            abbr = team.get('abbreviation', '')
                            if abbr:
                                teams[abbr] = {
                                    'id': team.get('id', ''),
                                    'name': team.get('displayName', ''),
                                    'abbreviation': abbr,
                                    'location': team.get('location', ''),
                                    'nickname': team.get('name', '')
                                }

                return teams
        except Exception as e:
            print(f"Exception fetching team info: {e}")
            return {}

    async def get_team_season_stats(self, team_abbr: str) -> Optional[Dict]:
        """
        Fetch comprehensive season statistics for a specific MLB team.
        Uses ESPN's team stats endpoint.
        """
        # Check cache first
        cache_key = f"stats_{team_abbr}"
        if cache_key in self._stats_cache:
            if datetime.now() < self._cache_expiry.get(cache_key, datetime.min):
                print(f"Using cached stats for {team_abbr}")
                return self._stats_cache[cache_key]

        await self.ensure_session()

        try:
            # First get team info to get team ID
            teams = await self.get_team_info()
            if team_abbr not in teams:
                print(f"Team abbreviation {team_abbr} not found")
                return None

            team_id = teams[team_abbr]['id']

            # Fetch team statistics
            url = f"{self.BASE_URL}/teams/{team_id}/statistics"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    print(f"Error fetching stats for {team_abbr}: {response.status}")
                    return None

                data = await response.json()

                # Extract stats from the response
                stats = self._parse_team_stats(data, teams[team_abbr])

                # Cache the results
                self._stats_cache[cache_key] = stats
                self._cache_expiry[cache_key] = datetime.now() + self.cache_duration

                return stats

        except Exception as e:
            print(f"Exception fetching stats for {team_abbr}: {e}")
            return None

    def _parse_team_stats(self, data: Dict, team_info: Dict) -> Dict:
        """Parse ESPN team statistics response into our format"""
        stats = {
            'team_id': team_info['id'],
            'team_name': team_info['name'],
            'abbreviation': team_info['abbreviation'],
            'games_played': 0,
            'wins': 0,
            'losses': 0,
            'win_pct': 0.0,
            # Batting stats
            'runs_per_game': 0.0,
            'batting_avg': 0.0,
            'on_base_pct': 0.0,
            'slugging_pct': 0.0,
            'ops': 0.0,
            'home_runs': 0,
            'hits_per_game': 0.0,
            'stolen_bases': 0,
            # Pitching stats
            'era': 0.0,
            'whip': 0.0,
            'strikeouts_per_9': 0.0,
            'walks_per_9': 0.0,
            'hits_allowed_per_9': 0.0,
            'saves': 0,
            'blown_saves': 0,
            'quality_starts': 0,
        }

        # Parse splits and statistics
        if 'splits' in data:
            categories = data['splits'].get('categories', [])

            for category in categories:
                cat_name = category.get('name', '')
                cat_stats = category.get('stats', [])

                for stat in cat_stats:
                    stat_name = stat.get('name', '')
                    stat_value = stat.get('value', 0)

                    # Map ESPN stat names to our fields
                    if stat_name == 'gamesPlayed':
                        stats['games_played'] = int(stat_value)
                    elif stat_name == 'wins':
                        stats['wins'] = int(stat_value)
                    elif stat_name == 'losses':
                        stats['losses'] = int(stat_value)
                    elif stat_name == 'winPercent':
                        stats['win_pct'] = float(stat_value)
                    elif stat_name == 'runsPerGame':
                        stats['runs_per_game'] = float(stat_value)
                    elif stat_name == 'avg':
                        stats['batting_avg'] = float(stat_value)
                    elif stat_name == 'onBasePct' or stat_name == 'OBP':
                        stats['on_base_pct'] = float(stat_value)
                    elif stat_name == 'slugPct' or stat_name == 'SLG':
                        stats['slugging_pct'] = float(stat_value)
                    elif stat_name == 'OPS':
                        stats['ops'] = float(stat_value)
                    elif stat_name == 'homeRuns':
                        stats['home_runs'] = int(stat_value)
                    elif stat_name == 'stolenBases':
                        stats['stolen_bases'] = int(stat_value)
                    elif stat_name == 'ERA':
                        stats['era'] = float(stat_value)
                    elif stat_name == 'WHIP':
                        stats['whip'] = float(stat_value)
                    elif stat_name == 'strikeoutsPer9':
                        stats['strikeouts_per_9'] = float(stat_value)
                    elif stat_name == 'walksPer9':
                        stats['walks_per_9'] = float(stat_value)
                    elif stat_name == 'saves':
                        stats['saves'] = int(stat_value)
                    elif stat_name == 'blownSaves':
                        stats['blown_saves'] = int(stat_value)

        # Calculate derived stats
        if stats['games_played'] > 0:
            stats['hits_per_game'] = stats.get('hits', 0) / stats['games_played']
            stats['home_runs_per_game'] = stats['home_runs'] / stats['games_played']

        if stats['on_base_pct'] > 0 and stats['slugging_pct'] > 0:
            stats['ops'] = stats['on_base_pct'] + stats['slugging_pct']

        return stats

    async def get_all_teams_stats(self) -> List[Dict]:
        """
        Fetch statistics for all 30 MLB teams.
        Used for calculating rankings.
        """
        teams = await self.get_team_info()
        all_stats = []

        # Fetch stats for all teams concurrently
        tasks = [self.get_team_season_stats(abbr) for abbr in teams.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for stats in results:
            if stats and not isinstance(stats, Exception):
                all_stats.append(stats)

        return all_stats

    def calculate_rankings(self, all_stats: List[Dict]) -> Dict[str, Dict]:
        """
        Calculate rankings for all teams across all statistics.
        Returns a dictionary mapping team abbreviations to their stats with rankings.
        """
        if not all_stats:
            return {}

        # Sort teams for each stat (higher is better except for ERA, WHIP, walks)

        # Offensive stats (higher is better)
        sorted_by_rpg = sorted(all_stats, key=lambda x: x.get('runs_per_game', 0), reverse=True)
        sorted_by_avg = sorted(all_stats, key=lambda x: x.get('batting_avg', 0), reverse=True)
        sorted_by_ops = sorted(all_stats, key=lambda x: x.get('ops', 0), reverse=True)
        sorted_by_hr = sorted(all_stats, key=lambda x: x.get('home_runs', 0), reverse=True)

        # Pitching stats (lower is better for ERA, WHIP, walks; higher for K/9, saves)
        sorted_by_era = sorted(all_stats, key=lambda x: x.get('era', 999))
        sorted_by_whip = sorted(all_stats, key=lambda x: x.get('whip', 999))
        sorted_by_k9 = sorted(all_stats, key=lambda x: x.get('strikeouts_per_9', 0), reverse=True)
        sorted_by_saves = sorted(all_stats, key=lambda x: x.get('saves', 0), reverse=True)

        # Create ranking maps
        rankings = {}

        for idx, team in enumerate(sorted_by_rpg):
            abbr = team['abbreviation']
            if abbr not in rankings:
                rankings[abbr] = team.copy()
            rankings[abbr]['runs_per_game_rank'] = idx + 1

        for idx, team in enumerate(sorted_by_avg):
            abbr = team['abbreviation']
            rankings[abbr]['batting_avg_rank'] = idx + 1

        for idx, team in enumerate(sorted_by_ops):
            abbr = team['abbreviation']
            rankings[abbr]['ops_rank'] = idx + 1

        for idx, team in enumerate(sorted_by_hr):
            abbr = team['abbreviation']
            rankings[abbr]['home_runs_rank'] = idx + 1

        for idx, team in enumerate(sorted_by_era):
            abbr = team['abbreviation']
            rankings[abbr]['era_rank'] = idx + 1

        for idx, team in enumerate(sorted_by_whip):
            abbr = team['abbreviation']
            rankings[abbr]['whip_rank'] = idx + 1

        for idx, team in enumerate(sorted_by_k9):
            abbr = team['abbreviation']
            rankings[abbr]['strikeouts_per_9_rank'] = idx + 1

        for idx, team in enumerate(sorted_by_saves):
            abbr = team['abbreviation']
            rankings[abbr]['saves_rank'] = idx + 1

        return rankings

    async def get_team_stats_with_rankings(self, team_abbr: str) -> Optional[MLBTeamStats]:
        """
        Get comprehensive team statistics with rankings for a specific team.
        This is the main method to use for getting full team data.
        """
        # Fetch all teams to calculate rankings
        all_stats = await self.get_all_teams_stats()

        if not all_stats:
            return None

        # Calculate rankings
        rankings = self.calculate_rankings(all_stats)

        if team_abbr not in rankings:
            return None

        team_data = rankings[team_abbr]

        # Determine form trend based on recent win percentage
        form_trend = "NEUTRAL"
        if team_data.get('win_pct', 0) >= 0.600:
            form_trend = "HOT"
        elif team_data.get('win_pct', 0) <= 0.400:
            form_trend = "COLD"

        # Create MLBTeamStats object
        return MLBTeamStats(
            team_id=team_data['team_id'],
            team_name=team_data['team_name'],
            games_played=team_data['games_played'],
            wins=team_data['wins'],
            losses=team_data['losses'],
            win_pct=team_data['win_pct'],
            runs_per_game=team_data['runs_per_game'],
            batting_avg=team_data['batting_avg'],
            on_base_pct=team_data['on_base_pct'],
            slugging_pct=team_data['slugging_pct'],
            ops=team_data['ops'],
            home_runs_per_game=team_data.get('home_runs_per_game', 0),
            hits_per_game=team_data['hits_per_game'],
            stolen_bases=team_data['stolen_bases'],
            era=team_data['era'],
            whip=team_data['whip'],
            strikeouts_per_9=team_data['strikeouts_per_9'],
            walks_per_9=team_data['walks_per_9'],
            hits_allowed_per_9=team_data.get('hits_allowed_per_9', 0),
            saves=team_data['saves'],
            blown_saves=team_data['blown_saves'],
            quality_starts=team_data['quality_starts'],
            form_trend=form_trend,
            runs_per_game_rank=team_data.get('runs_per_game_rank'),
            batting_avg_rank=team_data.get('batting_avg_rank'),
            ops_rank=team_data.get('ops_rank'),
            home_runs_rank=team_data.get('home_runs_rank'),
            era_rank=team_data.get('era_rank'),
            whip_rank=team_data.get('whip_rank'),
            strikeouts_per_9_rank=team_data.get('strikeouts_per_9_rank'),
            saves_rank=team_data.get('saves_rank')
        )

    async def get_recent_form(self, team_abbr: str, num_games: int = 10) -> Optional[str]:
        """
        Get team's record in their last N games (e.g., "7-3" for last 10 games).
        This requires fetching recent game results.
        """
        await self.ensure_session()

        try:
            teams = await self.get_team_info()
            if team_abbr not in teams:
                return None

            team_id = teams[team_abbr]['id']

            # Fetch recent games/schedule
            url = f"{self.BASE_URL}/teams/{team_id}/schedule"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return None

                data = await response.json()

                # Parse recent completed games
                events = data.get('events', [])
                recent_wins = 0
                recent_losses = 0
                games_counted = 0

                for event in reversed(events):  # Most recent first
                    if games_counted >= num_games:
                        break

                    competition = event.get('competitions', [{}])[0]
                    status = competition.get('status', {})

                    # Only count completed games
                    if status.get('type', {}).get('completed', False):
                        competitors = competition.get('competitors', [])
                        for competitor in competitors:
                            if competitor.get('id') == team_id:
                                if competitor.get('winner', False):
                                    recent_wins += 1
                                else:
                                    recent_losses += 1
                                games_counted += 1
                                break

                if games_counted > 0:
                    return f"{recent_wins}-{recent_losses}"

        except Exception as e:
            print(f"Exception fetching recent form for {team_abbr}: {e}")

        return None


# Test the client
async def test_mlb_client():
    """Test function to verify MLB stats client works"""
    client = MLBStatsClient()

    try:
        print("Testing MLB Stats Client...")

        # Test fetching team info
        print("\n1. Fetching all team info...")
        teams = await client.get_team_info()
        print(f"Found {len(teams)} MLB teams")

        # Test fetching stats for a specific team (Yankees)
        if 'NYY' in teams:
            print("\n2. Fetching stats for New York Yankees...")
            stats = await client.get_team_stats_with_rankings('NYY')
            if stats:
                print(f"Team: {stats.team_name}")
                print(f"Record: {stats.wins}-{stats.losses} ({stats.win_pct:.3f})")
                print(f"Runs/Game: {stats.runs_per_game:.2f} (Rank: {stats.runs_per_game_rank})")
                print(f"Batting Avg: {stats.batting_avg:.3f} (Rank: {stats.batting_avg_rank})")
                print(f"OPS: {stats.ops:.3f} (Rank: {stats.ops_rank})")
                print(f"ERA: {stats.era:.2f} (Rank: {stats.era_rank})")
                print(f"WHIP: {stats.whip:.3f} (Rank: {stats.whip_rank})")
                print(f"Form: {stats.form_trend}")

        # Test fetching recent form
        if 'NYY' in teams:
            print("\n3. Fetching recent form for Yankees...")
            form = await client.get_recent_form('NYY', 10)
            if form:
                print(f"Last 10 games: {form}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_mlb_client())
