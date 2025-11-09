"""
NHL Live Game Monitor - Real-time goalie pull detection
"""

import requests
import time
from datetime import datetime
from typing import List, Dict, Optional
import json
from goalie_pull_database import GoaliePullDatabase


class NHLLiveMonitor:
    """Monitor live NHL games for goalie pull events"""

    BASE_URL = "https://statsapi.web.nhl.com/api/v1"

    def __init__(self):
        self.db = GoaliePullDatabase()
        self.active_games = {}
        self.tracked_pulls = set()  # Track which pulls we've already logged

    def get_todays_games(self) -> List[Dict]:
        """Get all NHL games for today"""
        url = f"{self.BASE_URL}/schedule"

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            games = []
            for date_entry in data.get('dates', []):
                for game in date_entry.get('games', []):
                    games.append({
                        'game_id': str(game['gamePk']),
                        'home_team': game['teams']['home']['team']['name'],
                        'away_team': game['teams']['away']['team']['name'],
                        'status': game['status']['abstractGameState'],  # Live, Final, Preview
                        'start_time': game['gameDate']
                    })

            return games

        except Exception as e:
            print(f"❌ Error fetching schedule: {e}")
            return []

    def get_live_game_data(self, game_id: str) -> Optional[Dict]:
        """Get live play-by-play data for a game"""
        url = f"{self.BASE_URL}/game/{game_id}/feed/live"

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"  ❌ Error fetching game {game_id}: {e}")
            return None

    def detect_goalie_pull(self, game_data: Dict) -> Optional[Dict]:
        """
        Detect if goalie was pulled in game

        Returns:
            Goalie pull event dict or None
        """
        if not game_data:
            return None

        try:
            game_id = str(game_data['gamePk'])
            plays = game_data.get('liveData', {}).get('plays', {}).get('allPlays', [])

            # Look through recent plays (last 20) for goalie pull
            for play in reversed(plays[-20:]):
                event_type = play.get('result', {}).get('eventTypeId', '')
                description = play.get('result', {}).get('description', '').lower()

                # Detect goalie pull
                is_pull = (
                    'goalie' in description and ('pulled' in description or 'extra attacker' in description) or
                    play.get('result', {}).get('emptyNet', False)
                )

                if is_pull:
                    about = play.get('about', {})
                    team_data = play.get('team', {})

                    if not team_data:
                        continue

                    team_name = team_data.get('name', '')
                    pull_id = f"{game_id}_{team_name}_{about.get('eventId', '')}"

                    # Skip if already tracked
                    if pull_id in self.tracked_pulls:
                        continue

                    # Extract details
                    period = about.get('period', 3)
                    period_time_remaining = about.get('periodTimeRemaining', '00:00')

                    # Convert to seconds
                    time_parts = period_time_remaining.split(':')
                    if len(time_parts) == 2:
                        time_remaining_seconds = int(time_parts[0]) * 60 + int(time_parts[1])
                    else:
                        time_remaining_seconds = 0

                    # Get score
                    goals = about.get('goals', {})
                    home_score = goals.get('home', 0)
                    away_score = goals.get('away', 0)

                    home_team = game_data['gameData']['teams']['home']['name']
                    away_team = game_data['gameData']['teams']['away']['name']

                    # Determine score differential
                    is_home = (team_name == home_team)
                    if is_home:
                        score_diff = home_score - away_score
                        opponent = away_team
                    else:
                        score_diff = away_score - home_score
                        opponent = home_team

                    # Only track if team is down
                    if score_diff >= 0:
                        continue

                    return {
                        'pull_id': pull_id,
                        'game_id': game_id,
                        'team': team_name,
                        'period': period,
                        'time_remaining': period_time_remaining,
                        'time_remaining_seconds': time_remaining_seconds,
                        'score_differential': score_diff,
                        'home_score': home_score,
                        'away_score': away_score,
                        'opponent': opponent,
                        'home_game': is_home,
                        'timestamp': about.get('dateTime', ''),
                        'description': description
                    }

        except Exception as e:
            print(f"  ❌ Error detecting pull: {e}")

        return None

    def monitor_live_games(self, interval: int = 10):
        """
        Monitor all live NHL games continuously

        Args:
            interval: Check interval in seconds (default 10)
        """
        print("🏒 NHL Live Game Monitor Started")
        print("=" * 80)
        print(f"Checking every {interval} seconds for goalie pulls...")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                # Get today's games
                games = self.get_todays_games()
                live_games = [g for g in games if g['status'] == 'Live']

                if not live_games:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] No live games currently")
                else:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Monitoring {len(live_games)} live game(s)...")

                    for game in live_games:
                        game_id = game['game_id']
                        matchup = f"{game['away_team']} @ {game['home_team']}"

                        # Get live data
                        game_data = self.get_live_game_data(game_id)

                        if not game_data:
                            continue

                        # Check for goalie pull
                        pull_event = self.detect_goalie_pull(game_data)

                        if pull_event:
                            pull_id = pull_event['pull_id']

                            # Mark as tracked
                            self.tracked_pulls.add(pull_id)

                            # Log the event
                            print("\n" + "=" * 80)
                            print("🚨 GOALIE PULL DETECTED!")
                            print("=" * 80)
                            print(f"Game: {matchup}")
                            print(f"Team: {pull_event['team']}")
                            print(f"Time: {pull_event['time_remaining']} remaining in Period {pull_event['period']}")
                            print(f"Score: {pull_event['home_score']} - {pull_event['away_score']}")
                            print(f"Down by: {abs(pull_event['score_differential'])}")
                            print(f"Description: {pull_event['description']}")
                            print("=" * 80)

                            # TODO: Send betting alert here
                            # self.send_betting_alert(pull_event)

                # Sleep before next check
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n⏹️  Monitor stopped by user")
            print(f"Total pulls tracked this session: {len(self.tracked_pulls)}")

    def get_current_game_status(self) -> Dict:
        """Get status of all current games"""
        games = self.get_todays_games()

        status = {
            'total_games': len(games),
            'live': [],
            'final': [],
            'scheduled': []
        }

        for game in games:
            game_info = {
                'game_id': game['game_id'],
                'matchup': f"{game['away_team']} @ {game['home_team']}",
                'time': game['start_time']
            }

            if game['status'] == 'Live':
                status['live'].append(game_info)
            elif game['status'] == 'Final':
                status['final'].append(game_info)
            else:
                status['scheduled'].append(game_info)

        return status


# Usage
if __name__ == "__main__":
    monitor = NHLLiveMonitor()

    # Option 1: Monitor continuously
    monitor.monitor_live_games(interval=10)

    # Option 2: Check current status once
    # status = monitor.get_current_game_status()
    # print(json.dumps(status, indent=2))
