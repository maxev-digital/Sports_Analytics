"""
NHL Goalie Pull Data Scraper
Collects historical goalie pull events from NHL API for strategy implementation
"""
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

NHL_API_BASE = "https://statsapi.web.nhl.com/api/v1"
NHL_API_V2 = "https://api-web.nhle.com/v1"

# Top aggressive coaches to prioritize (from strategy document)
AGGRESSIVE_COACHES = {
    'Tampa Bay Lightning': {'coach': 'Jon Cooper', 'analytics_score': 9.5},
    'Carolina Hurricanes': {'coach': 'Rod Brind\'Amour', 'analytics_score': 9.0},
    'Colorado Avalanche': {'coach': 'Jared Bednar', 'analytics_score': 8.8},
    'Toronto Maple Leafs': {'coach': 'Sheldon Keefe', 'analytics_score': 8.5},
    'Florida Panthers': {'coach': 'Paul Maurice', 'analytics_score': 8.5},
}

class NHLGoaliePullScraper:
    """Scrape goalie pull events from NHL games"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'NHL-Analytics-Bot/1.0'})

    async def get_games_on_date(self, date_str: str) -> List[Dict]:
        """Get all NHL games on a specific date"""
        url = f"{NHL_API_BASE}/schedule?date={date_str}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            games = []
            for date_entry in data.get('dates', []):
                for game in date_entry.get('games', []):
                    games.append({
                        'game_id': game['gamePk'],
                        'away_team': game['teams']['away']['team']['name'],
                        'home_team': game['teams']['home']['team']['name'],
                        'status': game['status']['detailedState'],
                        'date': date_entry['date']
                    })

            return games
        except Exception as e:
            logger.error(f"Error fetching games for {date_str}: {e}")
            return []

    async def extract_goalie_pulls_from_game(self, game_id: int) -> List[Dict]:
        """
        Parse play-by-play to find GOALIE PULLED events
        NHL API explicitly marks these events
        """
        url = f"{NHL_API_BASE}/game/{game_id}/feed/live"

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            plays = data.get('liveData', {}).get('plays', {}).get('allPlays', [])
            pulls = []

            for i, play in enumerate(plays):
                event_type = play.get('result', {}).get('event', '')

                # Look for goalie pull event
                if event_type in ['GOALIE PULLED', 'GOALIE_PULLED']:

                    team_data = play.get('team', {})
                    team = team_data.get('name', 'Unknown')

                    about = play.get('about', {})
                    period = about.get('period', 3)
                    time_remaining = about.get('periodTimeRemaining', '0:00')

                    # Convert time to seconds
                    try:
                        parts = time_remaining.split(':')
                        seconds = int(parts[0]) * 60 + int(parts[1])
                    except:
                        seconds = 0

                    # Get score differential at time of pull
                    try:
                        home_score = data['liveData']['linescore']['teams']['home']['goals']
                        away_score = data['liveData']['linescore']['teams']['away']['goals']

                        # Determine which team pulled and their score differential
                        game_data = data['gameData']
                        home_team = game_data['teams']['home']['name']

                        if team == home_team:
                            score_diff = home_score - away_score
                        else:
                            score_diff = away_score - home_score
                    except:
                        score_diff = -1  # Default to down by 1

                    # Analyze what happened after the pull
                    result = self._analyze_pull_outcome(i, plays, team)

                    pull_event = {
                        'game_id': str(game_id),
                        'date': about.get('dateTime', ''),
                        'team': team,
                        'score_differential': score_diff,
                        'time_remaining_seconds': seconds,
                        'time_remaining_display': time_remaining,
                        'period': period,
                        'empty_net_goal_scored': result['en_goal'],
                        'empty_net_goal_by': result['en_goal_by'],
                        'trailing_team_scored': result['trailing_scored'],
                    }

                    pulls.append(pull_event)

            return pulls

        except Exception as e:
            logger.error(f"Error extracting goalie pulls from game {game_id}: {e}")
            return []

    def _analyze_pull_outcome(self, pull_index: int, plays: List[Dict], pulling_team: str) -> Dict:
        """
        Analyze what happened after goalie was pulled
        Look at next 5-10 plays to see if EN goal was scored
        """
        result = {
            'en_goal': False,
            'en_goal_by': None,
            'trailing_scored': False
        }

        # Look at next 10 plays after the pull
        for play in plays[pull_index:pull_index+10]:
            event_type = play.get('result', {}).get('event', '')

            if event_type == 'GOAL':
                scoring_team = play.get('team', {}).get('name', '')

                # Check if it's an empty net goal
                if play.get('result', {}).get('emptyNet', False):
                    result['en_goal'] = True
                    result['en_goal_by'] = scoring_team

                # Check if trailing team scored
                if scoring_team == pulling_team:
                    result['trailing_scored'] = True

                break  # Only care about first goal after pull

        return result

    async def collect_historical_data(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Scrape past games to build initial database
        Collect data for the specified date range
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        all_pulls = []
        current_date = start

        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            logger.info(f"Collecting data for {date_str}")

            # Get games on this date
            games = await self.get_games_on_date(date_str)

            for game in games:
                # Skip if not final
                if 'Final' not in game['status']:
                    continue

                logger.info(f"  Processing: {game['away_team']} @ {game['home_team']}")

                # Extract goalie pull events
                pulls = await self.extract_goalie_pulls_from_game(game['game_id'])

                for pull in pulls:
                    logger.info(f"    Found pull: {pull['team']} at {pull['time_remaining_display']}")
                    all_pulls.append(pull)

                # Rate limit
                time.sleep(0.5)

            current_date += timedelta(days=1)

        logger.info(f"Historical collection complete: {len(all_pulls)} goalie pulls found")
        return all_pulls

    async def build_team_pull_profile(self, team: str, pulls: List[Dict]) -> Optional[Dict]:
        """
        Analyze all goalie pull events for a team
        Calculate average pull times and tendencies
        """
        # Filter pulls for this team
        team_pulls = [p for p in pulls if p['team'] == team]

        if len(team_pulls) < 3:
            logger.warning(f"Not enough data for {team}: {len(team_pulls)} pulls")
            return None

        # Separate by score differential
        down_1 = [p for p in team_pulls if p['score_differential'] == -1]
        down_2 = [p for p in team_pulls if p['score_differential'] == -2]
        down_3 = [p for p in team_pulls if p['score_differential'] <= -3]

        # Calculate averages
        def mean(values):
            return sum(values) / len(values) if values else 0

        profile = {
            'team': team,
            'total_pulls': len(team_pulls),
            'pulls_down_1': len(down_1),
            'pulls_down_2': len(down_2),
            'pulls_down_3': len(down_3),
        }

        if down_1:
            times = [p['time_remaining_seconds'] for p in down_1]
            profile['avg_pull_time_down_1'] = int(mean(times))
            profile['earliest_pull_down_1'] = max(times)
            profile['latest_pull_down_1'] = min(times)

        if down_2:
            times = [p['time_remaining_seconds'] for p in down_2]
            profile['avg_pull_time_down_2'] = int(mean(times))
            profile['earliest_pull_down_2'] = max(times)
            profile['latest_pull_down_2'] = min(times)

        # Calculate success rates
        profile['en_goals_against'] = sum(1 for p in team_pulls
                                          if p['empty_net_goal_scored'] and p['empty_net_goal_by'] != team)
        profile['trailing_team_scores'] = sum(1 for p in team_pulls if p['trailing_team_scored'])

        # Calculate analytics score
        profile['analytics_score'] = self._calculate_analytics_score(profile)

        return profile

    def _calculate_analytics_score(self, profile: Dict) -> float:
        """
        Score teams on aggressiveness (0-10)
        10 = Most aggressive (Tampa, Carolina)
        5 = League average
        0 = Conservative
        """
        score = 5.0  # Start at average

        avg_down_1 = profile.get('avg_pull_time_down_1', 90)
        avg_down_2 = profile.get('avg_pull_time_down_2', 150)
        earliest = profile.get('earliest_pull_down_1', 120)

        # Bonus for pulling early when down 1
        if avg_down_1 >= 120:  # 2:00+ minutes
            score += 2.5
        elif avg_down_1 >= 100:  # 1:40+ minutes
            score += 1.5
        elif avg_down_1 >= 90:  # 1:30+ minutes
            score += 0.5

        # Bonus for pulling early when down 2
        if avg_down_2 >= 180:  # 3:00+ minutes
            score += 2.0
        elif avg_down_2 >= 150:  # 2:30+ minutes
            score += 1.0

        # Bonus for ever pulling VERY early
        if earliest >= 240:  # 4:00+ minutes
            score += 0.5

        return min(score, 10.0)


# Quick test function
async def test_scraper():
    """Test the scraper with recent games"""
    scraper = NHLGoaliePullScraper()

    # Get games from last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    pulls = await scraper.collect_historical_data(
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )

    print(f"\nFound {len(pulls)} goalie pull events\n")

    # Build profiles for unique teams
    teams = list(set(p['team'] for p in pulls))

    for team in teams:
        profile = await scraper.build_team_pull_profile(team, pulls)
        if profile:
            print(f"{team}:")
            print(f"  Analytics Score: {profile['analytics_score']}/10")
            print(f"  Avg Pull Time (Down 1): {profile.get('avg_pull_time_down_1', 0)//60}:{profile.get('avg_pull_time_down_1', 0)%60:02d}")
            print(f"  Total Pulls: {profile['total_pulls']}")
            print()


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_scraper())
