"""
Odds Archive Database Manager
Unified storage for game odds and player prop odds (pregame and live)

Architecture:
- Single SQLite database for all odds data
- Separate tables for game odds vs props, pregame vs live
- Automatic grading for player props
- Smart data retention and archiving
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

# Database location
DB_PATH = Path(__file__).parent / "odds_history.db"


class OddsArchiveDB:
    """Unified odds archive database manager"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Create all tables with proper schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # ==========================================
            # GAME ODDS - PREGAME
            # ==========================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_odds_pregame (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    game_id TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    game_date TEXT NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    bookmaker TEXT NOT NULL,
                    market_type TEXT NOT NULL,  -- spreads, totals, h2h

                    -- Line data
                    home_line REAL,
                    away_line REAL,
                    total_line REAL,
                    over_under TEXT,

                    -- Odds data
                    home_odds INTEGER,
                    away_odds INTEGER,
                    over_odds INTEGER,
                    under_odds INTEGER,

                    -- Metadata
                    snapshot_type TEXT DEFAULT 'pregame',  -- opening, morning, closing
                    hours_before_game REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    UNIQUE(game_id, bookmaker, market_type, timestamp)
                )
            """)

            # ==========================================
            # GAME ODDS - LIVE
            # ==========================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_odds_live (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    game_id TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    game_date TEXT NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    bookmaker TEXT NOT NULL,
                    market_type TEXT NOT NULL,

                    -- Current game state
                    period TEXT,  -- Q1, Q2, H1, H2, etc.
                    time_remaining TEXT,
                    home_score INTEGER,
                    away_score INTEGER,

                    -- Line data
                    home_line REAL,
                    away_line REAL,
                    total_line REAL,

                    -- Odds data
                    home_odds INTEGER,
                    away_odds INTEGER,
                    over_odds INTEGER,
                    under_odds INTEGER,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    UNIQUE(game_id, bookmaker, market_type, period, timestamp)
                )
            """)

            # ==========================================
            # PLAYER PROP ODDS - PREGAME
            # ==========================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prop_odds_pregame (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    game_id TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    game_date TEXT NOT NULL,
                    player_name TEXT NOT NULL,
                    team TEXT NOT NULL,
                    opponent TEXT NOT NULL,
                    bookmaker TEXT NOT NULL,

                    -- Prop details
                    prop_type TEXT NOT NULL,  -- points, rebounds, assists, etc.
                    line_value REAL NOT NULL,
                    over_odds INTEGER,
                    under_odds INTEGER,

                    -- Metadata
                    snapshot_type TEXT DEFAULT 'pregame',
                    hours_before_game REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    UNIQUE(game_id, player_name, prop_type, bookmaker, timestamp)
                )
            """)

            # ==========================================
            # PLAYER PROP ODDS - LIVE
            # ==========================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prop_odds_live (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    game_id TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    game_date TEXT NOT NULL,
                    player_name TEXT NOT NULL,
                    team TEXT NOT NULL,
                    bookmaker TEXT NOT NULL,

                    -- Prop details
                    prop_type TEXT NOT NULL,
                    line_value REAL NOT NULL,
                    over_odds INTEGER,
                    under_odds INTEGER,

                    -- Current stats
                    current_value REAL,  -- Player's current stat in game
                    period TEXT,
                    time_remaining TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    UNIQUE(game_id, player_name, prop_type, bookmaker, timestamp)
                )
            """)

            # ==========================================
            # PLAYER PROP RESULTS (GRADED)
            # ==========================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prop_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    game_date TEXT NOT NULL,
                    player_name TEXT NOT NULL,
                    team TEXT NOT NULL,

                    -- Prop details
                    prop_type TEXT NOT NULL,
                    opening_line REAL,
                    closing_line REAL,

                    -- Result
                    actual_value REAL NOT NULL,
                    over_result TEXT,  -- WIN, LOSS, PUSH
                    under_result TEXT, -- WIN, LOSS, PUSH

                    -- Odds at close
                    closing_over_odds INTEGER,
                    closing_under_odds INTEGER,

                    -- Grading metadata
                    graded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_source TEXT,  -- nba_api, espn, etc.

                    UNIQUE(game_id, player_name, prop_type)
                )
            """)

            # ==========================================
            # GAME RESULTS (for reference)
            # ==========================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT NOT NULL UNIQUE,
                    sport TEXT NOT NULL,
                    game_date TEXT NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,

                    -- Final score
                    home_score INTEGER NOT NULL,
                    away_score INTEGER NOT NULL,
                    total_score INTEGER NOT NULL,

                    -- Quarters/Periods
                    q1_home INTEGER,
                    q1_away INTEGER,
                    q2_home INTEGER,
                    q2_away INTEGER,
                    q3_home INTEGER,
                    q3_away INTEGER,
                    q4_home INTEGER,
                    q4_away INTEGER,

                    -- Metadata
                    status TEXT DEFAULT 'final',
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # ==========================================
            # INDEXES FOR PERFORMANCE
            # ==========================================

            # Game odds indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_pregame_date ON game_odds_pregame(game_date, sport)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_pregame_id ON game_odds_pregame(game_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_live_id ON game_odds_live(game_id, period)")

            # Prop odds indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_prop_pregame_player ON prop_odds_pregame(player_name, game_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_prop_pregame_game ON prop_odds_pregame(game_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_prop_live_player ON prop_odds_live(player_name, game_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_prop_results_player ON prop_results(player_name, game_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_prop_results_game ON prop_results(game_id)")

            # Game results index
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_results_date ON game_results(game_date, sport)")

            conn.commit()
            logger.info(f"Odds archive database initialized: {self.db_path}")

    # ==========================================
    # GAME ODDS - PREGAME STORAGE
    # ==========================================

    def save_pregame_odds(self, odds_data: List[Dict]) -> int:
        """
        Save pregame game odds (spreads, totals, moneyline)

        Args:
            odds_data: List of odds dictionaries from Odds API

        Returns:
            Count of records saved
        """
        saved = 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for odds in odds_data:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO game_odds_pregame (
                            timestamp, game_id, sport, game_date,
                            home_team, away_team, bookmaker, market_type,
                            home_line, away_line, total_line, over_under,
                            home_odds, away_odds, over_odds, under_odds,
                            snapshot_type, hours_before_game
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        odds.get('timestamp', datetime.now().isoformat()),
                        odds['game_id'],
                        odds['sport'],
                        odds['game_date'],
                        odds['home_team'],
                        odds['away_team'],
                        odds['bookmaker'],
                        odds['market_type'],
                        odds.get('home_line'),
                        odds.get('away_line'),
                        odds.get('total_line'),
                        odds.get('over_under'),
                        odds.get('home_odds'),
                        odds.get('away_odds'),
                        odds.get('over_odds'),
                        odds.get('under_odds'),
                        odds.get('snapshot_type', 'pregame'),
                        odds.get('hours_before_game')
                    ))
                    saved += 1
                except sqlite3.IntegrityError:
                    pass  # Duplicate, skip

            conn.commit()

        return saved

    # ==========================================
    # PLAYER PROP ODDS - PREGAME STORAGE
    # ==========================================

    def save_pregame_props(self, props_data: List[Dict]) -> int:
        """
        Save pregame player prop odds

        Args:
            props_data: List of prop dictionaries

        Returns:
            Count of records saved
        """
        saved = 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for prop in props_data:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO prop_odds_pregame (
                            timestamp, game_id, sport, game_date,
                            player_name, team, opponent, bookmaker,
                            prop_type, line_value, over_odds, under_odds,
                            snapshot_type, hours_before_game
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        prop.get('timestamp', datetime.now().isoformat()),
                        prop['game_id'],
                        prop['sport'],
                        prop['game_date'],
                        prop['player_name'],
                        prop['team'],
                        prop['opponent'],
                        prop['bookmaker'],
                        prop['prop_type'],
                        prop['line_value'],
                        prop.get('over_odds'),
                        prop.get('under_odds'),
                        prop.get('snapshot_type', 'pregame'),
                        prop.get('hours_before_game')
                    ))
                    saved += 1
                except sqlite3.IntegrityError:
                    pass

            conn.commit()

        return saved

    # ==========================================
    # PLAYER PROP GRADING
    # ==========================================

    def grade_props(self, game_id: str, player_stats: Dict[str, Dict]) -> int:
        """
        Grade player props for a completed game

        Args:
            game_id: Game identifier
            player_stats: Dict mapping player_name to their stats
                Example: {
                    "LeBron James": {"points": 28, "rebounds": 7, "assists": 11},
                    "Anthony Davis": {"points": 22, "rebounds": 14, "assists": 3}
                }

        Returns:
            Count of props graded
        """
        graded = 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get all pregame props for this game
            cursor.execute("""
                SELECT DISTINCT player_name, prop_type, game_date, sport, team
                FROM prop_odds_pregame
                WHERE game_id = ?
            """, (game_id,))

            props_to_grade = cursor.fetchall()

            for player_name, prop_type, game_date, sport, team in props_to_grade:
                if player_name not in player_stats:
                    continue

                stats = player_stats[player_name]
                actual_value = stats.get(prop_type.lower())

                if actual_value is None:
                    continue

                # Get opening and closing lines
                cursor.execute("""
                    SELECT line_value, over_odds, under_odds
                    FROM prop_odds_pregame
                    WHERE game_id = ? AND player_name = ? AND prop_type = ?
                    ORDER BY timestamp ASC
                    LIMIT 1
                """, (game_id, player_name, prop_type))

                opening = cursor.fetchone()

                cursor.execute("""
                    SELECT line_value, over_odds, under_odds
                    FROM prop_odds_pregame
                    WHERE game_id = ? AND player_name = ? AND prop_type = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (game_id, player_name, prop_type))

                closing = cursor.fetchone()

                if not closing:
                    continue

                opening_line = opening[0] if opening else closing[0]
                closing_line = closing[0]
                closing_over_odds = closing[1]
                closing_under_odds = closing[2]

                # Determine results
                if actual_value > closing_line:
                    over_result = 'WIN'
                    under_result = 'LOSS'
                elif actual_value < closing_line:
                    over_result = 'LOSS'
                    under_result = 'WIN'
                else:
                    over_result = 'PUSH'
                    under_result = 'PUSH'

                # Save result
                cursor.execute("""
                    INSERT OR REPLACE INTO prop_results (
                        game_id, sport, game_date, player_name, team,
                        prop_type, opening_line, closing_line,
                        actual_value, over_result, under_result,
                        closing_over_odds, closing_under_odds,
                        data_source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    game_id, sport, game_date, player_name, team,
                    prop_type, opening_line, closing_line,
                    actual_value, over_result, under_result,
                    closing_over_odds, closing_under_odds,
                    'nba_api'
                ))

                graded += 1

            conn.commit()

        return graded

    # ==========================================
    # DATA RETENTION & CLEANUP
    # ==========================================

    def archive_old_data(self, days_to_keep: int = 365) -> Dict[str, int]:
        """
        Archive data older than specified days to reduce database size

        Args:
            days_to_keep: Number of days to keep in active database

        Returns:
            Dict with counts of archived records by table
        """
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
        archived = {}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Count and delete old pregame odds
            cursor.execute("SELECT COUNT(*) FROM game_odds_pregame WHERE game_date < ?", (cutoff_date,))
            archived['game_odds_pregame'] = cursor.fetchone()[0]
            cursor.execute("DELETE FROM game_odds_pregame WHERE game_date < ?", (cutoff_date,))

            # Count and delete old live odds
            cursor.execute("SELECT COUNT(*) FROM game_odds_live WHERE game_date < ?", (cutoff_date,))
            archived['game_odds_live'] = cursor.fetchone()[0]
            cursor.execute("DELETE FROM game_odds_live WHERE game_date < ?", (cutoff_date,))

            # Keep prop results forever (small size, valuable)
            archived['prop_results'] = 0

            conn.commit()

            # Vacuum to reclaim space
            cursor.execute("VACUUM")

        return archived

    # ==========================================
    # STATISTICS & REPORTING
    # ==========================================

    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the database"""
        stats = {}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Table sizes
            for table in ['game_odds_pregame', 'game_odds_live', 'prop_odds_pregame', 'prop_odds_live', 'prop_results', 'game_results']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]

            # Database file size
            stats['database_size_mb'] = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0

            # Date range
            cursor.execute("SELECT MIN(game_date), MAX(game_date) FROM game_odds_pregame")
            result = cursor.fetchone()
            stats['odds_date_range'] = {'min': result[0], 'max': result[1]} if result[0] else None

        return stats


if __name__ == "__main__":
    # Initialize database
    db = OddsArchiveDB()

    # Print stats
    stats = db.get_database_stats()
    print("\n" + "="*60)
    print("ODDS ARCHIVE DATABASE STATISTICS")
    print("="*60)
    for key, value in stats.items():
        print(f"{key}: {value}")
    print("="*60 + "\n")
