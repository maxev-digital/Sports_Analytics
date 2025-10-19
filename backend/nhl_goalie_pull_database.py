"""
NHL Goalie Pull Database
Stores historical goalie pull events and team performance data
Used to predict pull timing and calculate betting edges
"""
import sqlite3
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "data" / "nhl_goalie_pulls.db"


class GoaliePullDatabase:
    """Database for storing and querying historical goalie pull data"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self.ensure_db_exists()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def ensure_db_exists(self):
        """Create database tables if they don't exist"""
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = self.get_connection()
        cursor = conn.cursor()

        # Table: goalie_pull_events
        # Stores every goalie pull event from NHL games
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goalie_pull_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                game_date TEXT NOT NULL,
                season TEXT NOT NULL,
                team TEXT NOT NULL,
                opponent TEXT NOT NULL,
                is_home BOOLEAN NOT NULL,
                score_differential INTEGER NOT NULL,
                time_remaining_seconds INTEGER NOT NULL,
                period INTEGER NOT NULL,
                coach TEXT,
                empty_net_goal_scored BOOLEAN NOT NULL DEFAULT 0,
                empty_net_goal_by TEXT,
                trailing_team_scored BOOLEAN NOT NULL DEFAULT 0,
                game_outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table: team_pull_profiles
        # Aggregated stats per team for quick lookups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_pull_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team TEXT NOT NULL UNIQUE,
                current_coach TEXT,
                season TEXT NOT NULL,
                total_pulls INTEGER DEFAULT 0,
                pulls_down_1 INTEGER DEFAULT 0,
                pulls_down_2 INTEGER DEFAULT 0,
                avg_pull_time_down_1 INTEGER,
                avg_pull_time_down_2 INTEGER,
                earliest_pull_down_1 INTEGER,
                latest_pull_down_1 INTEGER,
                earliest_pull_down_2 INTEGER,
                latest_pull_down_2 INTEGER,
                analytics_score REAL DEFAULT 5.0,
                en_goals_against INTEGER DEFAULT 0,
                en_goals_for INTEGER DEFAULT 0,
                trailing_team_scored_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table: coach_profiles
        # Track individual coach tendencies (coaches move between teams)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coach_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coach_name TEXT NOT NULL UNIQUE,
                current_team TEXT,
                total_pulls INTEGER DEFAULT 0,
                avg_pull_time_down_1 INTEGER,
                avg_pull_time_down_2 INTEGER,
                analytics_score REAL DEFAULT 5.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table: empty_net_stats
        # Track team performance with empty net (for/against)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empty_net_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team TEXT NOT NULL,
                season TEXT NOT NULL,
                en_goals_for INTEGER DEFAULT 0,
                en_goals_against INTEGER DEFAULT 0,
                en_opportunities INTEGER DEFAULT 0,
                en_success_rate REAL DEFAULT 0.0,
                en_defense_rate REAL DEFAULT 0.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team, season)
            )
        """)

        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pull_events_team
            ON goalie_pull_events(team, season)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pull_events_game
            ON goalie_pull_events(game_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pull_events_coach
            ON goalie_pull_events(coach)
        """)

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def insert_pull_event(self, event: Dict) -> int:
        """Insert a goalie pull event into database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO goalie_pull_events (
                game_id, game_date, season, team, opponent, is_home,
                score_differential, time_remaining_seconds, period, coach,
                empty_net_goal_scored, empty_net_goal_by, trailing_team_scored,
                game_outcome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event['game_id'],
            event['game_date'],
            event.get('season', '2024-25'),
            event['team'],
            event['opponent'],
            event['is_home'],
            event['score_differential'],
            event['time_remaining_seconds'],
            event['period'],
            event.get('coach'),
            event['empty_net_goal_scored'],
            event.get('empty_net_goal_by'),
            event['trailing_team_scored'],
            event.get('game_outcome')
        ))

        event_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Inserted pull event: {event['team']} at {event['time_remaining_seconds']}s")
        return event_id

    def get_team_profile(self, team: str, season: str = '2024-25') -> Optional[Dict]:
        """Get team pull profile with aggregated stats"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get profile from team_pull_profiles table
        cursor.execute("""
            SELECT * FROM team_pull_profiles
            WHERE team = ? AND season = ?
        """, (team, season))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

    def get_coach_profile(self, coach: str) -> Optional[Dict]:
        """Get coach profile with pull tendencies"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM coach_profiles
            WHERE coach_name = ?
        """, (coach,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

    def get_empty_net_stats(self, team: str, season: str = '2024-25') -> Optional[Dict]:
        """Get team's empty net performance stats"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM empty_net_stats
            WHERE team = ? AND season = ?
        """, (team, season))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

    def rebuild_team_profile(self, team: str, season: str = '2024-25'):
        """Rebuild team profile from historical pull events"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get all pull events for this team
        cursor.execute("""
            SELECT * FROM goalie_pull_events
            WHERE team = ? AND season = ?
        """, (team, season))

        events = cursor.fetchall()

        if not events:
            logger.warning(f"No pull events found for {team} in {season}")
            conn.close()
            return

        # Calculate aggregated stats
        pulls_down_1 = [e for e in events if e[6] == -1]  # score_differential
        pulls_down_2 = [e for e in events if e[6] == -2]

        def avg(values):
            return int(sum(values) / len(values)) if values else None

        avg_down_1 = avg([e[7] for e in pulls_down_1]) if pulls_down_1 else None  # time_remaining_seconds
        avg_down_2 = avg([e[7] for e in pulls_down_2]) if pulls_down_2 else None

        earliest_down_1 = max([e[7] for e in pulls_down_1]) if pulls_down_1 else None
        latest_down_1 = min([e[7] for e in pulls_down_1]) if pulls_down_1 else None
        earliest_down_2 = max([e[7] for e in pulls_down_2]) if pulls_down_2 else None
        latest_down_2 = min([e[7] for e in pulls_down_2]) if pulls_down_2 else None

        # Count outcomes
        en_goals_against = sum(1 for e in events if e[10] and e[11] != team)  # empty_net_goal_scored, empty_net_goal_by
        en_goals_for = sum(1 for e in events if e[12])  # trailing_team_scored
        trailing_scored = sum(1 for e in events if e[12])

        # Calculate analytics score (0-10 based on aggressiveness)
        analytics_score = self._calculate_analytics_score({
            'avg_pull_time_down_1': avg_down_1,
            'avg_pull_time_down_2': avg_down_2,
            'earliest_pull_down_1': earliest_down_1
        })

        # Get current coach (most recent event)
        current_coach = events[-1][9] if events else None  # coach

        # Insert or update team profile
        cursor.execute("""
            INSERT OR REPLACE INTO team_pull_profiles (
                team, current_coach, season, total_pulls,
                pulls_down_1, pulls_down_2,
                avg_pull_time_down_1, avg_pull_time_down_2,
                earliest_pull_down_1, latest_pull_down_1,
                earliest_pull_down_2, latest_pull_down_2,
                analytics_score, en_goals_against, en_goals_for,
                trailing_team_scored_count, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            team, current_coach, season, len(events),
            len(pulls_down_1), len(pulls_down_2),
            avg_down_1, avg_down_2,
            earliest_down_1, latest_down_1,
            earliest_down_2, latest_down_2,
            analytics_score, en_goals_against, en_goals_for,
            trailing_scored
        ))

        conn.commit()
        conn.close()

        logger.info(f"Rebuilt profile for {team}: {len(events)} pulls, analytics: {analytics_score:.1f}/10")

    def rebuild_coach_profile(self, coach: str):
        """Rebuild coach profile from all their historical events"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get all pull events for this coach
        cursor.execute("""
            SELECT * FROM goalie_pull_events
            WHERE coach = ?
        """, (coach,))

        events = cursor.fetchall()

        if not events:
            conn.close()
            return

        # Calculate coach-specific stats
        pulls_down_1 = [e for e in events if e[6] == -1]
        pulls_down_2 = [e for e in events if e[6] == -2]

        def avg(values):
            return int(sum(values) / len(values)) if values else None

        avg_down_1 = avg([e[7] for e in pulls_down_1]) if pulls_down_1 else None
        avg_down_2 = avg([e[7] for e in pulls_down_2]) if pulls_down_2 else None

        analytics_score = self._calculate_analytics_score({
            'avg_pull_time_down_1': avg_down_1,
            'avg_pull_time_down_2': avg_down_2,
            'earliest_pull_down_1': max([e[7] for e in pulls_down_1]) if pulls_down_1 else None
        })

        current_team = events[-1][3] if events else None  # team

        cursor.execute("""
            INSERT OR REPLACE INTO coach_profiles (
                coach_name, current_team, total_pulls,
                avg_pull_time_down_1, avg_pull_time_down_2,
                analytics_score, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            coach, current_team, len(events),
            avg_down_1, avg_down_2, analytics_score
        ))

        conn.commit()
        conn.close()

        logger.info(f"Rebuilt profile for coach {coach}: {len(events)} pulls")

    def update_empty_net_stats(self, team: str, season: str = '2024-25'):
        """Update empty net performance stats for a team"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Count empty net goals for/against
        cursor.execute("""
            SELECT
                SUM(CASE WHEN trailing_team_scored = 1 THEN 1 ELSE 0 END) as en_goals_for,
                SUM(CASE WHEN empty_net_goal_scored = 1 AND empty_net_goal_by != team THEN 1 ELSE 0 END) as en_goals_against,
                COUNT(*) as total_pulls
            FROM goalie_pull_events
            WHERE team = ? AND season = ?
        """, (team, season))

        row = cursor.fetchone()
        en_goals_for = row[0] or 0
        en_goals_against = row[1] or 0
        total_pulls = row[2] or 0

        if total_pulls == 0:
            conn.close()
            return

        # Calculate rates
        en_success_rate = (en_goals_for / total_pulls) * 100 if total_pulls > 0 else 0.0
        en_defense_rate = ((total_pulls - en_goals_against) / total_pulls) * 100 if total_pulls > 0 else 0.0

        cursor.execute("""
            INSERT OR REPLACE INTO empty_net_stats (
                team, season, en_goals_for, en_goals_against,
                en_opportunities, en_success_rate, en_defense_rate,
                last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            team, season, en_goals_for, en_goals_against,
            total_pulls, en_success_rate, en_defense_rate
        ))

        conn.commit()
        conn.close()

        logger.info(f"Updated EN stats for {team}: {en_goals_for}F / {en_goals_against}A ({en_success_rate:.1f}% success)")

    def _calculate_analytics_score(self, profile: Dict) -> float:
        """
        Score teams/coaches on aggressiveness (0-10)
        10 = Most aggressive (pulls early)
        5 = League average
        0 = Conservative
        """
        score = 5.0

        avg_down_1 = profile.get('avg_pull_time_down_1', 90)
        avg_down_2 = profile.get('avg_pull_time_down_2', 150)
        earliest = profile.get('earliest_pull_down_1', 120)

        if avg_down_1:
            # Bonus for pulling early when down 1
            if avg_down_1 >= 120:  # 2:00+
                score += 2.5
            elif avg_down_1 >= 100:  # 1:40+
                score += 1.5
            elif avg_down_1 >= 90:  # 1:30+
                score += 0.5

        if avg_down_2:
            # Bonus for pulling early when down 2
            if avg_down_2 >= 180:  # 3:00+
                score += 2.0
            elif avg_down_2 >= 150:  # 2:30+
                score += 1.0

        if earliest:
            # Bonus for ever pulling VERY early
            if earliest >= 240:  # 4:00+
                score += 0.5

        return min(score, 10.0)

    def get_all_teams_with_profiles(self, season: str = '2024-25') -> List[str]:
        """Get list of all teams that have pull profiles"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT team FROM team_pull_profiles
            WHERE season = ?
            ORDER BY team
        """, (season,))

        teams = [row[0] for row in cursor.fetchall()]
        conn.close()

        return teams

    def get_recent_pulls(self, team: str, days: int = 30) -> List[Dict]:
        """Get recent pull events for a team"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute("""
            SELECT * FROM goalie_pull_events
            WHERE team = ? AND game_date >= ?
            ORDER BY game_date DESC
        """, (team, cutoff_date))

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        events = [dict(zip(columns, row)) for row in rows]
        conn.close()

        return events


# Singleton instance
_db_instance = None


def get_database() -> GoaliePullDatabase:
    """Get singleton database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = GoaliePullDatabase()
    return _db_instance


if __name__ == "__main__":
    # Test database creation
    logging.basicConfig(level=logging.INFO)
    db = get_database()
    logger.info("Database ready!")
