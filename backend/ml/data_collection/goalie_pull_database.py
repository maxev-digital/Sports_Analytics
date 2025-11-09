"""
NHL Goalie Pull Database - Store and retrieve goalie pull patterns
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import os


class GoaliePullDatabase:
    """SQLite database for tracking NHL goalie pull events"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to backend/ml/data/goalie_pulls.db
            base_dir = os.path.dirname(os.path.dirname(__file__))
            data_dir = os.path.join(base_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'goalie_pulls.db')

        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Main goalie pull events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goalie_pulls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id VARCHAR(50) NOT NULL,
                team VARCHAR(100) NOT NULL,
                coach VARCHAR(100),
                period INTEGER,
                time_remaining VARCHAR(10),
                time_remaining_seconds INTEGER,
                score_differential INTEGER,
                home_score INTEGER,
                away_score INTEGER,
                opponent VARCHAR(100),
                home_game BOOLEAN,
                division_game BOOLEAN,
                playoff_game BOOLEAN,
                season VARCHAR(10),
                game_date DATE,
                pull_timestamp DATETIME,
                goalie_name VARCHAR(100),
                result VARCHAR(50),
                goal_scored_by VARCHAR(50),
                time_to_goal_seconds INTEGER,
                final_outcome VARCHAR(20),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game_id, team, pull_timestamp)
            )
        ''')

        # Team statistics view
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_pull_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team VARCHAR(100) NOT NULL,
                season VARCHAR(10),
                total_pulls INTEGER DEFAULT 0,
                avg_pull_time_down_1 REAL,
                avg_pull_time_down_2 REAL,
                avg_pull_time_down_3 REAL,
                pull_success_rate REAL,
                home_pull_avg_time REAL,
                away_pull_avg_time REAL,
                division_pull_avg_time REAL,
                coach_aggression_score REAL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team, season)
            )
        ''')

        # Create indexes for fast queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_team_season
            ON goalie_pulls(team, season)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_score_diff
            ON goalie_pulls(score_differential)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_game_date
            ON goalie_pulls(game_date)
        ''')

        conn.commit()
        conn.close()

        print(f"[OK] Database initialized at {self.db_path}")

    def insert_pull_event(self, event: Dict) -> int:
        """
        Insert a goalie pull event into the database

        Args:
            event: Dictionary with goalie pull data

        Returns:
            Row ID of inserted event
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR IGNORE INTO goalie_pulls (
                    game_id, team, coach, period, time_remaining, time_remaining_seconds,
                    score_differential, home_score, away_score, opponent, home_game,
                    division_game, playoff_game, season, game_date, pull_timestamp,
                    goalie_name, result, goal_scored_by, time_to_goal_seconds, final_outcome
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.get('game_id'),
                event.get('team'),
                event.get('coach'),
                event.get('period'),
                event.get('time_remaining'),
                event.get('time_remaining_seconds'),
                event.get('score_differential'),
                event.get('home_score'),
                event.get('away_score'),
                event.get('opponent'),
                event.get('home_game', False),
                event.get('division_game', False),
                event.get('playoff_game', False),
                event.get('season'),
                event.get('game_date'),
                event.get('pull_timestamp'),
                event.get('goalie_name'),
                event.get('result'),
                event.get('goal_scored_by'),
                event.get('time_to_goal_seconds'),
                event.get('final_outcome')
            ))

            row_id = cursor.lastrowid
            conn.commit()
            return row_id

        except sqlite3.IntegrityError:
            # Event already exists
            return -1
        finally:
            conn.close()

    def get_team_pull_patterns(self, team: str, season: str = None) -> Dict:
        """
        Get historical goalie pull patterns for a team

        Args:
            team: Team name
            season: Season (e.g., '20232024') or None for all seasons

        Returns:
            Dictionary with pull patterns
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Base query
        where_clause = "WHERE team = ?"
        params = [team]

        if season:
            where_clause += " AND season = ?"
            params.append(season)

        # Get pull patterns by score differential
        query = f'''
            SELECT
                score_differential,
                COUNT(*) as pull_count,
                AVG(time_remaining_seconds) as avg_time_seconds,
                MIN(time_remaining_seconds) as earliest_pull,
                MAX(time_remaining_seconds) as latest_pull,
                home_game
            FROM goalie_pulls
            {where_clause}
            GROUP BY score_differential, home_game
            ORDER BY score_differential
        '''

        cursor.execute(query, params)
        results = cursor.fetchall()

        patterns = {
            'team': team,
            'season': season or 'all',
            'by_score_diff': {}
        }

        for row in results:
            score_diff, count, avg_sec, earliest, latest, home = row

            key = f"down_by_{abs(score_diff)}"
            location = 'home' if home else 'away'

            if key not in patterns['by_score_diff']:
                patterns['by_score_diff'][key] = {}

            patterns['by_score_diff'][key][location] = {
                'pull_count': count,
                'avg_time_remaining_seconds': avg_sec,
                'avg_time_remaining': self._seconds_to_time(avg_sec),
                'earliest_pull': self._seconds_to_time(earliest),
                'latest_pull': self._seconds_to_time(latest),
                'pull_frequency': count  # Will calculate vs total games later
            }

        # Get overall stats
        cursor.execute(f'''
            SELECT
                COUNT(*) as total_pulls,
                AVG(time_remaining_seconds) as overall_avg_time,
                COUNT(CASE WHEN result = 'goal_for' THEN 1 END) * 1.0 / COUNT(*) as success_rate
            FROM goalie_pulls
            {where_clause}
        ''', params)

        total_pulls, overall_avg, success_rate = cursor.fetchone()

        patterns['overall'] = {
            'total_pulls': total_pulls,
            'avg_pull_time': self._seconds_to_time(overall_avg) if overall_avg else None,
            'success_rate': success_rate if success_rate else 0.0
        }

        conn.close()
        return patterns

    def get_coach_tendencies(self, coach: str, season: str = None) -> Dict:
        """Get coaching tendencies for goalie pulls"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        where_clause = "WHERE coach = ?"
        params = [coach]

        if season:
            where_clause += " AND season = ?"
            params.append(season)

        cursor.execute(f'''
            SELECT
                score_differential,
                AVG(time_remaining_seconds) as avg_pull_time,
                COUNT(*) as frequency
            FROM goalie_pulls
            {where_clause}
            GROUP BY score_differential
        ''', params)

        tendencies = {
            'coach': coach,
            'by_score_diff': {}
        }

        for row in cursor.fetchall():
            score_diff, avg_time, freq = row
            tendencies['by_score_diff'][f"down_{abs(score_diff)}"] = {
                'avg_pull_time_seconds': avg_time,
                'avg_pull_time': self._seconds_to_time(avg_time),
                'frequency': freq
            }

        conn.close()
        return tendencies

    def get_recent_trend(self, team: str, games: int = 10) -> Dict:
        """
        Get recent goalie pull trend for a team (last N games)

        Args:
            team: Team name
            games: Number of recent games to analyze

        Returns:
            Recent trend data
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                AVG(time_remaining_seconds) as recent_avg_time,
                COUNT(*) as recent_pulls
            FROM (
                SELECT time_remaining_seconds
                FROM goalie_pulls
                WHERE team = ?
                ORDER BY game_date DESC, pull_timestamp DESC
                LIMIT ?
            )
        ''', (team, games))

        recent_avg, recent_count = cursor.fetchone()

        # Compare to season average
        cursor.execute('''
            SELECT AVG(time_remaining_seconds) as season_avg
            FROM goalie_pulls
            WHERE team = ?
        ''', (team,))

        season_avg = cursor.fetchone()[0]

        conn.close()

        return {
            'team': team,
            'recent_games': games,
            'recent_pulls': recent_count or 0,
            'recent_avg_time': self._seconds_to_time(recent_avg) if recent_avg else None,
            'recent_avg_seconds': recent_avg,
            'season_avg_time': self._seconds_to_time(season_avg) if season_avg else None,
            'season_avg_seconds': season_avg,
            'trend': 'earlier' if recent_avg and season_avg and recent_avg > season_avg else 'later'
        }

    def update_team_stats(self, team: str, season: str):
        """Update aggregated team statistics"""
        patterns = self.get_team_pull_patterns(team, season)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate stats
        total_pulls = patterns['overall']['total_pulls']
        success_rate = patterns['overall']['success_rate']

        # Get avg times by score diff
        avg_down_1 = patterns['by_score_diff'].get('down_by_1', {}).get('home', {}).get('avg_time_remaining_seconds')
        avg_down_2 = patterns['by_score_diff'].get('down_by_2', {}).get('home', {}).get('avg_time_remaining_seconds')
        avg_down_3 = patterns['by_score_diff'].get('down_by_3', {}).get('home', {}).get('avg_time_remaining_seconds')

        cursor.execute('''
            INSERT OR REPLACE INTO team_pull_stats (
                team, season, total_pulls, avg_pull_time_down_1, avg_pull_time_down_2,
                avg_pull_time_down_3, pull_success_rate, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (team, season, total_pulls, avg_down_1, avg_down_2, avg_down_3, success_rate))

        conn.commit()
        conn.close()

    def _seconds_to_time(self, seconds: float) -> str:
        """Convert seconds to MM:SS format"""
        if seconds is None:
            return "00:00"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def get_all_teams(self) -> List[str]:
        """Get list of all teams in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT DISTINCT team FROM goalie_pulls ORDER BY team')
        teams = [row[0] for row in cursor.fetchall()]

        conn.close()
        return teams

    def get_stats_summary(self) -> Dict:
        """Get summary statistics of database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM goalie_pulls')
        total_events = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT team) FROM goalie_pulls')
        total_teams = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT game_id) FROM goalie_pulls')
        total_games = cursor.fetchone()[0]

        cursor.execute('SELECT MIN(game_date), MAX(game_date) FROM goalie_pulls')
        date_range = cursor.fetchone()

        conn.close()

        return {
            'total_pull_events': total_events,
            'total_teams': total_teams,
            'total_games': total_games,
            'date_range': {
                'earliest': date_range[0],
                'latest': date_range[1]
            }
        }


# Testing
if __name__ == "__main__":
    db = GoaliePullDatabase()

    # Test insert
    test_event = {
        'game_id': '2023020001',
        'team': 'Boston Bruins',
        'coach': 'Jim Montgomery',
        'period': 3,
        'time_remaining': '02:37',
        'time_remaining_seconds': 157,
        'score_differential': -1,
        'home_score': 1,
        'away_score': 2,
        'opponent': 'Montreal Canadiens',
        'home_game': True,
        'season': '20232024',
        'game_date': '2023-10-10',
        'pull_timestamp': '2023-10-10T22:45:30Z',
        'goalie_name': 'Linus Ullmark'
    }

    row_id = db.insert_pull_event(test_event)
    print(f"Inserted event with ID: {row_id}")

    # Test query
    patterns = db.get_team_pull_patterns('Boston Bruins', '20232024')
    print("\nBoston Bruins patterns:")
    print(patterns)

    # Get summary
    summary = db.get_stats_summary()
    print("\nDatabase summary:")
    print(summary)
