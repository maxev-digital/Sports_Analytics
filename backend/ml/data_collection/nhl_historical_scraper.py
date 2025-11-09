"""
NHL Historical Data Scraper - Get goalie pull data from 2023-24 season
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from goalie_pull_database import GoaliePullDatabase


class NHLHistoricalScraper:
    """Scrape historical NHL game data for goalie pulls"""

    # Use new NHL API
    BASE_URL = "https://api-web.nhle.com/v1"
    OLD_API_URL = "https://statsapi.web.nhl.com/api/v1"

    # NHL divisions for detecting division games
    DIVISIONS = {
        'Atlantic': ['Boston Bruins', 'Buffalo Sabres', 'Detroit Red Wings', 'Florida Panthers',
                     'Montreal Canadiens', 'Ottawa Senators', 'Tampa Bay Lightning', 'Toronto Maple Leafs'],
        'Metropolitan': ['Carolina Hurricanes', 'Columbus Blue Jackets', 'New Jersey Devils', 'New York Islanders',
                        'New York Rangers', 'Philadelphia Flyers', 'Pittsburgh Penguins', 'Washington Capitals'],
        'Central': ['Arizona Coyotes', 'Chicago Blackhawks', 'Colorado Avalanche', 'Dallas Stars',
                   'Minnesota Wild', 'Nashville Predators', 'St. Louis Blues', 'Winnipeg Jets'],
        'Pacific': ['Anaheim Ducks', 'Calgary Flames', 'Edmonton Oilers', 'Los Angeles Kings',
                   'San Jose Sharks', 'Seattle Kraken', 'Vancouver Canucks', 'Vegas Golden Knights']
    }

    def __init__(self):
        self.db = GoaliePullDatabase()
        self.team_to_division = {}
        for division, teams in self.DIVISIONS.items():
            for team in teams:
                self.team_to_division[team] = division

    def get_season_schedule(self, season: str = "20232024") -> List[Dict]:
        """
        Get all games for a season using new NHL API

        Args:
            season: Season in format '20232024' for 2023-24 season

        Returns:
            List of game dictionaries
        """
        print(f"\n[*] Fetching schedule for {season} season...")

        games = []

        # For 2023-24 season: Oct 10, 2023 to Apr 18, 2024
        start_date = datetime(2023, 10, 10)
        end_date = datetime(2024, 4, 19)  # Inclusive

        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            url = f"{self.BASE_URL}/schedule/{date_str}"

            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()

                # New API returns gameWeek array with dates
                for week_data in data.get('gameWeek', []):
                    for game_data in week_data.get('games', []):
                        games.append({
                            'game_id': str(game_data['id']),
                            'date': game_data['startTimeUTC'],
                            'home_team': game_data['homeTeam']['placeName']['default'] + ' ' + game_data['homeTeam']['commonName']['default'],
                            'away_team': game_data['awayTeam']['placeName']['default'] + ' ' + game_data['awayTeam']['commonName']['default'],
                            'status': game_data['gameState']
                        })

                time.sleep(0.1)  # Rate limit

            except Exception as e:
                # Continue on error, some dates may not have games
                pass

            current_date += timedelta(days=1)

        print(f"[OK] Found {len(games)} games")
        return games

    def get_game_play_by_play(self, game_id: str) -> Optional[Dict]:
        """
        Get detailed play-by-play data for a game using new NHL API

        Args:
            game_id: NHL game ID

        Returns:
            Game data dictionary or None if error
        """
        url = f"{self.BASE_URL}/gamecenter/{game_id}/play-by-play"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"  [ERROR] Error fetching game {game_id}: {e}")
            return None

    def extract_goalie_pulls(self, game_data: Dict) -> List[Dict]:
        """
        Extract all goalie pull events from game data (NEW NHL API FORMAT)

        Args:
            game_data: Full game data from new NHL API

        Returns:
            List of goalie pull event dictionaries
        """
        if not game_data:
            return []

        pulls = []

        try:
            # New API structure
            game_id = str(game_data['id'])
            season = game_data.get('season', '20232024')
            game_date = game_data.get('gameDate', '')

            home_team = game_data['homeTeam']['placeName']['default'] + ' ' + game_data['homeTeam']['commonName']['default']
            away_team = game_data['awayTeam']['placeName']['default'] + ' ' + game_data['awayTeam']['commonName']['default']

            # Coaches not available in new API, use "Unknown"
            home_coach = "Unknown"
            away_coach = "Unknown"

            # Check if division game
            is_division_game = self.team_to_division.get(home_team) == self.team_to_division.get(away_team)

            # Get final score
            final_home = game_data['liveData']['linescore']['teams']['home']['goals']
            final_away = game_data['liveData']['linescore']['teams']['away']['goals']

            # Track goalie pulls
            goalie_pulled = {}  # team -> pull event
            empty_net_goals = []

            # Parse all plays
            plays = game_data.get('liveData', {}).get('plays', {}).get('allPlays', [])

            for play in plays:
                event_type = play.get('result', {}).get('eventTypeId', '')
                description = play.get('result', {}).get('description', '').lower()

                # Detect goalie pull
                if 'goalie' in description and ('pulled' in description or 'empty net' in description):
                    about = play.get('about', {})
                    team_data = play.get('team', {})

                    if not team_data:
                        continue

                    team_name = team_data.get('name', '')
                    period = about.get('period', 3)
                    period_time = about.get('periodTime', '00:00')
                    period_time_remaining = about.get('periodTimeRemaining', '00:00')

                    # Convert time remaining to seconds
                    time_parts = period_time_remaining.split(':')
                    if len(time_parts) == 2:
                        time_remaining_seconds = int(time_parts[0]) * 60 + int(time_parts[1])
                    else:
                        time_remaining_seconds = 0

                    # Get score at time of pull
                    goals = about.get('goals', {})
                    home_score = goals.get('home', 0)
                    away_score = goals.get('away', 0)

                    # Determine which team pulled and score differential
                    is_home = (team_name == home_team)
                    if is_home:
                        score_diff = home_score - away_score
                        opponent = away_team
                        coach = home_coach
                    else:
                        score_diff = away_score - home_score
                        opponent = home_team
                        coach = away_coach

                    # Only track if down (score_diff < 0)
                    if score_diff < 0:
                        goalie_pulled[team_name] = {
                            'game_id': game_id,
                            'team': team_name,
                            'coach': coach,
                            'period': period,
                            'time_remaining': period_time_remaining,
                            'time_remaining_seconds': time_remaining_seconds,
                            'score_differential': score_diff,
                            'home_score': home_score,
                            'away_score': away_score,
                            'opponent': opponent,
                            'home_game': is_home,
                            'division_game': is_division_game,
                            'playoff_game': game_id.startswith('2023030'),  # Playoff games start with 030
                            'season': season,
                            'game_date': game_date,
                            'pull_timestamp': about.get('dateTime', ''),
                            'goalie_name': None,  # Will try to extract
                            'result': None,  # Will update if goal scored
                            'goal_scored_by': None,
                            'time_to_goal_seconds': None,
                            'final_outcome': None
                        }

                        # Try to extract goalie name from description
                        if 'goalie' in description:
                            words = description.split()
                            for i, word in enumerate(words):
                                if word == 'goalie' and i > 0:
                                    goalie_pulled[team_name]['goalie_name'] = words[i-1].title()

                # Detect empty net goals
                elif event_type == 'GOAL' and play.get('result', {}).get('emptyNet', False):
                    about = play.get('about', {})
                    team_scored = play.get('team', {}).get('name', '')
                    scorer = play.get('players', [{}])[0].get('player', {}).get('fullName', 'Unknown')

                    empty_net_goals.append({
                        'team_scored': team_scored,
                        'scorer': scorer,
                        'time': about.get('periodTime', ''),
                        'timestamp': about.get('dateTime', '')
                    })

            # Match empty net goals to pulls
            for team, pull_event in goalie_pulled.items():
                pull_time = datetime.fromisoformat(pull_event['pull_timestamp'].replace('Z', '+00:00'))

                # Find next empty net goal
                for en_goal in empty_net_goals:
                    goal_time = datetime.fromisoformat(en_goal['timestamp'].replace('Z', '+00:00'))

                    if goal_time > pull_time:
                        time_diff = (goal_time - pull_time).total_seconds()

                        # Goal by team that pulled (success)
                        if en_goal['team_scored'] == team:
                            pull_event['result'] = 'goal_for'
                            pull_event['goal_scored_by'] = en_goal['scorer']
                            pull_event['time_to_goal_seconds'] = int(time_diff)
                        # Goal against (failed)
                        else:
                            pull_event['result'] = 'goal_against'
                            pull_event['goal_scored_by'] = en_goal['scorer']
                            pull_event['time_to_goal_seconds'] = int(time_diff)
                        break

                # Determine final outcome
                if pull_event['home_game']:
                    if final_home > final_away:
                        pull_event['final_outcome'] = 'win'
                    elif final_home < final_away:
                        pull_event['final_outcome'] = 'loss'
                    else:
                        pull_event['final_outcome'] = 'tie'
                else:
                    if final_away > final_home:
                        pull_event['final_outcome'] = 'win'
                    elif final_away < final_home:
                        pull_event['final_outcome'] = 'loss'
                    else:
                        pull_event['final_outcome'] = 'tie'

                pulls.append(pull_event)

        except Exception as e:
            print(f"  [ERROR] Error parsing game data: {e}")

        return pulls

    def scrape_season(self, season: str = "20232024", max_games: int = None):
        """
        Scrape entire season for goalie pull data

        Args:
            season: Season to scrape
            max_games: Maximum games to scrape (for testing)
        """
        print(f"\n[*] Starting NHL Historical Scraper for {season} season")
        print("=" * 80)

        # Get schedule
        games = self.get_season_schedule(season)

        if max_games:
            games = games[:max_games]
            print(f"[!] Limited to {max_games} games for testing")

        total_games = len(games)
        total_pulls = 0
        errors = 0

        print(f"\n[*] Processing {total_games} games...")

        for i, game in enumerate(games, 1):
            game_id = game['game_id']
            matchup = f"{game['away_team']} @ {game['home_team']}"

            if i % 50 == 0:
                print(f"\nProgress: {i}/{total_games} games ({i/total_games*100:.1f}%)")
                print(f"Pulls found so far: {total_pulls}")

            # Get game data
            game_data = self.get_game_play_by_play(game_id)

            if not game_data:
                errors += 1
                continue

            # Extract goalie pulls
            pulls = self.extract_goalie_pulls(game_data)

            # Save to database
            for pull in pulls:
                row_id = self.db.insert_pull_event(pull)
                if row_id > 0:
                    total_pulls += 1
                    print(f"  [OK] {matchup}: {pull['team']} pulled goalie at {pull['time_remaining']} (down {abs(pull['score_differential'])})")

            # Rate limit: 1 request per 0.5 seconds
            time.sleep(0.5)

        # Final summary
        print("\n" + "=" * 80)
        print("[OK] SCRAPING COMPLETE!")
        print("=" * 80)
        print(f"Games processed: {total_games}")
        print(f"Goalie pulls found: {total_pulls}")
        print(f"Errors: {errors}")

        # Update team stats
        print("\n[*] Updating team statistics...")
        teams = self.db.get_all_teams()
        for team in teams:
            self.db.update_team_stats(team, season)
            print(f"  [OK] Updated stats for {team}")

        # Print summary
        summary = self.db.get_stats_summary()
        print("\n[*] Database Summary:")
        print(f"  Total pull events: {summary['total_pull_events']}")
        print(f"  Teams tracked: {summary['total_teams']}")
        print(f"  Games with pulls: {summary['total_games']}")
        print(f"  Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")


# Usage
if __name__ == "__main__":
    scraper = NHLHistoricalScraper()

    # Scrape full 2023-24 season (will take ~45 minutes)
    print("[*] Starting FULL season scrape...")
    print("[*] This will take approximately 45 minutes")
    print("[*] Progress will be shown every 50 games")
    print("=" * 80)
    scraper.scrape_season(season="20232024")
