"""
Data Collection for Goalie Pull Timing Alpha

Collects:
1. Historical NHL game data from NHL Stats API
2. Coach information
3. Team strength metrics
4. Matches MoneyPuck pull events with full game context
"""

import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

from database_schema import GoaliePullDB


class NHLDataCollector:
    """Collects NHL game data from official NHL Stats API"""

    def __init__(self):
        self.db = GoaliePullDB()
        self.base_url = "https://statsapi.web.nhl.com/api/v1"
        self.session = requests.Session()

        # NHL team abbreviations mapping
        self.team_abbrev_map = {
            "Anaheim Ducks": "ANA",
            "Arizona Coyotes": "ARI",
            "Boston Bruins": "BOS",
            "Buffalo Sabres": "BUF",
            "Calgary Flames": "CGY",
            "Carolina Hurricanes": "CAR",
            "Chicago Blackhawks": "CHI",
            "Colorado Avalanche": "COL",
            "Columbus Blue Jackets": "CBJ",
            "Dallas Stars": "DAL",
            "Detroit Red Wings": "DET",
            "Edmonton Oilers": "EDM",
            "Florida Panthers": "FLA",
            "Los Angeles Kings": "LAK",
            "Minnesota Wild": "MIN",
            "Montréal Canadiens": "MTL",
            "Nashville Predators": "NSH",
            "New Jersey Devils": "NJD",
            "New York Islanders": "NYI",
            "New York Rangers": "NYR",
            "Ottawa Senators": "OTT",
            "Philadelphia Flyers": "PHI",
            "Pittsburgh Penguins": "PIT",
            "San Jose Sharks": "SJS",
            "Seattle Kraken": "SEA",
            "St. Louis Blues": "STL",
            "Tampa Bay Lightning": "TBL",
            "Toronto Maple Leafs": "TOR",
            "Vancouver Canucks": "VAN",
            "Vegas Golden Knights": "VGK",
            "Washington Capitals": "WSH",
            "Winnipeg Jets": "WPG"
        }

    def fetch_game_data(self, game_id: str, season: str = "20232024") -> Optional[Dict]:
        """
        Fetch full game data from NHL API

        Args:
            game_id: Game ID (e.g., "2023020001")
            season: Season year (e.g., "20232024")

        Returns:
            Dict with game data or None if error
        """
        # NHL game IDs are typically formatted as: SSSS0TGGGG
        # where SSSS = season (2023), T = game type (02=regular, 03=playoff), GGGG = game number

        # Construct full game ID if just number provided
        if len(game_id) <= 5:
            game_id = f"{season}02{game_id.zfill(4)}"

        url = f"{self.base_url}/game/{game_id}/feed/live"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching game {game_id}: {e}")
            return None

    def parse_game_coaches(self, game_data: Dict) -> Tuple[Optional[str], Optional[str]]:
        """Extract home and away coaches from game data"""
        try:
            home_coach = game_data['liveData']['boxscore']['teams']['home'].get('coaches', [{}])[0].get('person', {}).get('fullName')
            away_coach = game_data['liveData']['boxscore']['teams']['away'].get('coaches', [{}])[0].get('person', {}).get('fullName')
            return home_coach, away_coach
        except:
            return None, None

    def parse_game_teams(self, game_data: Dict) -> Tuple[str, str]:
        """Extract home and away team names"""
        try:
            home_team = game_data['gameData']['teams']['home']['triCode']
            away_team = game_data['gameData']['teams']['away']['triCode']
            return home_team, away_team
        except:
            return None, None

    def parse_game_date(self, game_data: Dict) -> str:
        """Extract game date"""
        try:
            return game_data['gameData']['datetime']['dateTime'].split('T')[0]
        except:
            return None

    def time_string_to_seconds(self, time_str: str) -> int:
        """Convert MM:SS to total seconds remaining"""
        try:
            parts = time_str.split(':')
            return int(parts[0]) * 60 + int(parts[1])
        except:
            return 0

    def load_moneypuck_data(self) -> pd.DataFrame:
        """Load MoneyPuck goalie pull data"""
        csv_path = Path(__file__).parent.parent.parent / "strategies" / "moneypuck_goalie_pulls_2023_2024_FINAL.csv"

        if not csv_path.exists():
            raise FileNotFoundError(f"MoneyPuck data not found at {csv_path}")

        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} pull events from MoneyPuck")
        return df

    def collect_historical_pulls(self, season: str = "20232024", start_game: int = 1, end_game: int = 1312):
        """
        Collect historical pull events and match with NHL game data

        Args:
            season: Season year (e.g., "20232024" for 2023-24)
            start_game: First game number to process
            end_game: Last game number to process (1312 = full regular season)
        """
        moneypuck_df = self.load_moneypuck_data()

        successful_matches = 0
        failed_matches = 0

        print(f"\nCollecting historical pull data for season {season}")
        print(f"Processing games {start_game} to {end_game}")
        print("=" * 80)

        for game_num in range(start_game, end_game + 1):
            # Format game ID
            game_id_short = str(game_num)
            game_id_full = f"{season}02{game_id_short.zfill(4)}"

            # Check if this game has a pull in MoneyPuck data
            pull_row = moneypuck_df[moneypuck_df['game_id'] == int(game_id_short)]

            if pull_row.empty:
                continue

            print(f"\nProcessing game {game_id_full} (#{game_num})...")

            # Fetch full game data from NHL API
            game_data = self.fetch_game_data(game_id_full, season)

            if not game_data:
                print(f"  [SKIP] Could not fetch NHL data for game {game_id_full}")
                failed_matches += 1
                continue

            # Parse game info
            home_team, away_team = self.parse_game_teams(game_data)
            home_coach, away_coach = self.parse_game_coaches(game_data)
            game_date = self.parse_game_date(game_data)

            if not home_team or not away_team:
                print(f"  [SKIP] Could not parse teams for game {game_id_full}")
                failed_matches += 1
                continue

            # Get pull info from MoneyPuck
            pulling_team = pull_row.iloc[0]['pulling_team']
            score_diff = pull_row.iloc[0]['score_differential']
            period = pull_row.iloc[0]['period']
            goals_by_pulling_team = pull_row.iloc[0]['goals_by_pulling_team']
            goals_by_opponent = pull_row.iloc[0]['goals_by_opponent']
            total_goals = pull_row.iloc[0]['total_goals_after_pull']
            pulling_team_tied = pull_row.iloc[0]['pulling_team_tied_game']

            # Determine opponent
            opponent_team = away_team if pulling_team == home_team else home_team

            # Determine coach
            if pulling_team == home_team:
                coach = home_coach
            else:
                coach = away_coach

            coach_id = coach.replace(' ', '_').upper() if coach else None

            # Estimate pull time (MoneyPuck doesn't have exact time)
            # For now, use average: down by 1 = 1:46, down by 2 = 2:15, down by 3+ = 2:45
            if score_diff == -1:
                pull_time_seconds = 106  # 1:46
            elif score_diff == -2:
                pull_time_seconds = 135  # 2:15
            else:
                pull_time_seconds = 165  # 2:45

            pull_time_remaining = f"{pull_time_seconds // 60}:{pull_time_seconds % 60:02d}"

            # Create pull record
            pull_data = {
                'game_id': game_id_full,
                'season': int(season[:4]),
                'game_date': game_date,
                'home_team': home_team,
                'away_team': away_team,
                'pulling_team': pulling_team,
                'opponent_team': opponent_team,
                'pull_time_remaining': pull_time_remaining,
                'pull_time_seconds': pull_time_seconds,
                'pull_period': period,
                'score_differential': score_diff,
                'coach_id': coach_id,
                'home_coach': home_coach,
                'away_coach': away_coach,
                'goals_by_pulling_team': goals_by_pulling_team,
                'goals_by_opponent': goals_by_opponent,
                'total_goals': total_goals,
                'pulling_team_tied': pulling_team_tied,
                'pulling_team_won': pulling_team_tied or goals_by_pulling_team > goals_by_opponent,
                'playoff_game': False,  # All MoneyPuck data is regular season
                'data_source': 'moneypuck'
            }

            # Insert into database
            try:
                pull_id = self.db.insert_historical_pull(pull_data)
                print(f"  [OK] Inserted pull #{pull_id}: {pulling_team} (coach: {coach})")
                successful_matches += 1
            except Exception as e:
                print(f"  [ERROR] Failed to insert: {e}")
                failed_matches += 1

            # Rate limiting - be nice to NHL API
            time.sleep(0.5)

            # Progress update every 50 games
            if game_num % 50 == 0:
                print(f"\n[PROGRESS] Processed {game_num}/{end_game} games")
                print(f"  Successful: {successful_matches}, Failed: {failed_matches}")

        print("\n" + "=" * 80)
        print(f"COLLECTION COMPLETE")
        print(f"Total pulls processed: {successful_matches + failed_matches}")
        print(f"Successfully matched: {successful_matches}")
        print(f"Failed to match: {failed_matches}")
        print("=" * 80)

        return successful_matches, failed_matches


class CoachProfileBuilder:
    """Builds coach pull profiles from historical data"""

    def __init__(self):
        self.db = GoaliePullDB()

    def build_coach_profiles(self):
        """Calculate coach pull profiles from historical pulls"""
        print("\nBuilding coach profiles from historical pulls...")
        print("=" * 80)

        # Get all historical pulls
        all_pulls = self.db.get_historical_pulls()

        if not all_pulls:
            print("No historical pulls found. Run data collection first.")
            return

        # Group by coach
        coaches = {}
        for pull in all_pulls:
            coach_id = pull['coach_id']
            if not coach_id:
                continue

            if coach_id not in coaches:
                coaches[coach_id] = {
                    'coach_name': pull['home_coach'] if pull['pulling_team'] == pull['home_team'] else pull['away_coach'],
                    'pulls_down_1': [],
                    'pulls_down_2': [],
                    'pulls_down_3_plus': [],
                    'pulls_shorthanded': 0,
                    'pulls_playoff': 0,
                    'pulls_regular': 0,
                    'pulls_before_2min': 0,
                    'pulls_after_1min': 0,
                    'teams': set()
                }

            # Categorize pull
            score_diff = pull['score_differential']
            pull_time = pull['pull_time_seconds']

            if score_diff == -1:
                coaches[coach_id]['pulls_down_1'].append(pull_time)
            elif score_diff == -2:
                coaches[coach_id]['pulls_down_2'].append(pull_time)
            else:
                coaches[coach_id]['pulls_down_3_plus'].append(pull_time)

            # Track timing
            if pull_time > 120:
                coaches[coach_id]['pulls_before_2min'] += 1
            if pull_time < 60:
                coaches[coach_id]['pulls_after_1min'] += 1

            # Track playoff vs regular
            if pull.get('playoff_game'):
                coaches[coach_id]['pulls_playoff'] += 1
            else:
                coaches[coach_id]['pulls_regular'] += 1

            # Track teams
            coaches[coach_id]['teams'].add(pull['pulling_team'])

        # Calculate statistics and create profiles
        profiles_created = 0

        for coach_id, data in coaches.items():
            # Calculate median pull times
            pulls_down_1 = sorted(data['pulls_down_1'])
            pulls_down_2 = sorted(data['pulls_down_2'])
            pulls_down_3_plus = sorted(data['pulls_down_3_plus'])

            def median(values):
                if not values:
                    return None
                n = len(values)
                if n % 2 == 0:
                    return (values[n//2-1] + values[n//2]) / 2
                return values[n//2]

            def percentile(values, p):
                if not values:
                    return None
                k = (len(values) - 1) * (p / 100)
                f = int(k)
                c = int(k) + 1
                if c >= len(values):
                    return values[f]
                return values[f] + (k - f) * (values[c] - values[f])

            # Calculate aggressive rating (1-10)
            # Based on median pull time when down 1
            # Earlier pulls = more aggressive
            median_down_1 = median(pulls_down_1)
            if median_down_1:
                if median_down_1 > 120:  # > 2:00
                    aggressive_rating = 9  # Very aggressive
                elif median_down_1 > 100:  # > 1:40
                    aggressive_rating = 7  # Aggressive
                elif median_down_1 > 80:  # > 1:20
                    aggressive_rating = 5  # Moderate
                elif median_down_1 > 60:  # > 1:00
                    aggressive_rating = 3  # Conservative
                else:
                    aggressive_rating = 1  # Very conservative
            else:
                aggressive_rating = 5  # Default

            # Calculate predictability (based on variance)
            variability = percentile(pulls_down_1, 75) - percentile(pulls_down_1, 25) if pulls_down_1 else 0
            if variability:
                if variability < 20:
                    predictability_rating = 9  # Very predictable
                elif variability < 40:
                    predictability_rating = 7  # Predictable
                elif variability < 60:
                    predictability_rating = 5  # Moderate
                else:
                    predictability_rating = 3  # Unpredictable
            else:
                predictability_rating = 5

            # Playoff vs regular ratio
            total_pulls = data['pulls_playoff'] + data['pulls_regular']
            playoff_ratio = data['pulls_playoff'] / total_pulls if total_pulls > 0 else 1.0

            # Create coach profile
            coach_profile = {
                'coach_id': coach_id,
                'coach_name': data['coach_name'],
                'current_team': list(data['teams'])[0] if data['teams'] else None,
                'seasons_active': "2023-2024",
                'pulls_down_1': len(pulls_down_1),
                'median_pull_time_down_1_seconds': int(median_down_1) if median_down_1 else None,
                'p25_pull_time_down_1_seconds': int(percentile(pulls_down_1, 25)) if pulls_down_1 else None,
                'p75_pull_time_down_1_seconds': int(percentile(pulls_down_1, 75)) if pulls_down_1 else None,
                'pulls_down_2': len(pulls_down_2),
                'median_pull_time_down_2_seconds': int(median_down_2) if median_down_2 else None,
                'p25_pull_time_down_2_seconds': int(percentile(pulls_down_2, 25)) if pulls_down_2 else None,
                'p75_pull_time_down_2_seconds': int(percentile(pulls_down_2, 75)) if pulls_down_2 else None,
                'pulls_down_3_plus': len(pulls_down_3_plus),
                'median_pull_time_down_3_plus_seconds': int(median(pulls_down_3_plus)) if pulls_down_3_plus else None,
                'pull_rate_when_shorthanded': 0.0,  # TODO: need strength state data
                'pull_rate_playoff_vs_regular': playoff_ratio,
                'pulls_before_2min': data['pulls_before_2min'],
                'pulls_after_1min': data['pulls_after_1min'],
                'aggressive_rating': aggressive_rating,
                'predictability_rating': predictability_rating
            }

            # Insert into database
            try:
                self.db.insert_coach_profile(coach_profile)
                print(f"[OK] Created profile for {data['coach_name']} ({coach_id})")
                print(f"     Aggressive: {aggressive_rating}/10, Predictable: {predictability_rating}/10")
                print(f"     Down 1: {len(pulls_down_1)} pulls, median {median_down_1:.0f}s")
                profiles_created += 1
            except Exception as e:
                print(f"[ERROR] Failed to create profile for {coach_id}: {e}")

        print("\n" + "=" * 80)
        print(f"COACH PROFILES COMPLETE")
        print(f"Total profiles created: {profiles_created}")
        print("=" * 80)

        return profiles_created


if __name__ == "__main__":
    print("=" * 80)
    print("NHL GOALIE PULL DATA COLLECTION")
    print("=" * 80)

    # Step 1: Collect historical pulls
    collector = NHLDataCollector()
    collector.collect_historical_pulls(
        season="20232024",
        start_game=1,
        end_game=1312  # Full regular season
    )

    # Step 2: Build coach profiles
    print("\n")
    builder = CoachProfileBuilder()
    builder.build_coach_profiles()

    print("\n[OK] Data collection complete!")
