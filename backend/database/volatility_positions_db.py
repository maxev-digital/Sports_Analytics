"""
Volatility Arbitrage Positions Database

SQLite database for tracking volatility arbitrage positions
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VolatilityPositionsDB:
    """Database for volatility arbitrage positions"""

    def __init__(self, db_path: str = "data/volatility_positions.db"):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn = None
        self._create_tables()

    def _get_connection(self):
        """Get database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def _create_tables(self):
        """Create database tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Positions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                game_id TEXT NOT NULL,
                sport TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,

                -- First leg
                first_team TEXT NOT NULL,
                first_side TEXT NOT NULL,
                first_odds INTEGER NOT NULL,
                first_stake REAL NOT NULL,
                first_timestamp TEXT NOT NULL,
                first_bookmaker TEXT NOT NULL,

                -- Trigger conditions
                trigger_price INTEGER NOT NULL,
                trigger_min_profit REAL NOT NULL,

                -- Second leg (nullable)
                second_team TEXT,
                second_odds INTEGER,
                second_stake REAL,
                second_timestamp TEXT,
                second_bookmaker TEXT,

                -- Status
                status TEXT NOT NULL DEFAULT 'open',
                locked_profit REAL,
                actual_profit REAL,

                -- Game state
                entry_quarter TEXT,
                entry_score TEXT,

                -- Metadata
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                closed_at TEXT
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON positions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_id ON positions(game_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON positions(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON positions(created_at)")

        # Hedge alerts history (for analytics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hedge_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                game_id TEXT NOT NULL,

                hedge_team TEXT NOT NULL,
                hedge_odds INTEGER NOT NULL,
                hedge_bookmaker TEXT NOT NULL,
                recommended_stake REAL NOT NULL,
                locked_profit REAL NOT NULL,

                was_executed BOOLEAN DEFAULT 0,

                created_at TEXT NOT NULL,

                FOREIGN KEY (position_id) REFERENCES positions(id)
            )
        """)

        # Create indexes for hedge_alerts
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hedge_position_id ON hedge_alerts(position_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hedge_created_at ON hedge_alerts(created_at)")

        # Performance stats (aggregated daily)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_performance (
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,

                total_positions INTEGER DEFAULT 0,
                hedged_positions INTEGER DEFAULT 0,
                held_won INTEGER DEFAULT 0,
                held_lost INTEGER DEFAULT 0,
                expired INTEGER DEFAULT 0,

                total_wagered REAL DEFAULT 0,
                total_profit REAL DEFAULT 0,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                PRIMARY KEY (user_id, date)
            )
        """)

        # Create indexes for daily_performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_perf_date ON daily_performance(date)")

        conn.commit()

    def create_position(self, position_data: Dict) -> str:
        """
        Create new position in database

        Args:
            position_data: Dictionary with position fields

        Returns:
            Position ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO positions (
                id, user_id, game_id, sport, home_team, away_team,
                first_team, first_side, first_odds, first_stake, first_timestamp, first_bookmaker,
                trigger_price, trigger_min_profit,
                entry_quarter, entry_score,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            position_data['id'],
            position_data['user_id'],
            position_data['game_id'],
            position_data['sport'],
            position_data['home_team'],
            position_data['away_team'],
            position_data['first_team'],
            position_data['first_side'],
            position_data['first_odds'],
            position_data['first_stake'],
            position_data['first_timestamp'],
            position_data['first_bookmaker'],
            position_data['trigger_price'],
            position_data['trigger_min_profit'],
            position_data.get('entry_quarter', ''),
            position_data.get('entry_score', ''),
            'open',
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        conn.commit()
        logger.info(f"Created position {position_data['id']} in database")

        return position_data['id']

    def update_position(self, position_id: str, updates: Dict) -> bool:
        """
        Update position fields

        Args:
            position_id: Position ID
            updates: Dictionary of fields to update

        Returns:
            True if successful
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build UPDATE statement dynamically
        updates['updated_at'] = datetime.now().isoformat()

        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [position_id]

        cursor.execute(f"""
            UPDATE positions
            SET {set_clause}
            WHERE id = ?
        """, values)

        conn.commit()
        return cursor.rowcount > 0

    def execute_hedge(self, position_id: str, hedge_data: Dict) -> bool:
        """
        Record hedge execution on position

        Args:
            position_id: Position ID
            hedge_data: Dictionary with second leg details

        Returns:
            True if successful
        """
        updates = {
            'second_team': hedge_data['second_team'],
            'second_odds': hedge_data['second_odds'],
            'second_stake': hedge_data['second_stake'],
            'second_timestamp': hedge_data['second_timestamp'],
            'second_bookmaker': hedge_data['second_bookmaker'],
            'locked_profit': hedge_data['locked_profit'],
            'status': 'hedged'
        }

        return self.update_position(position_id, updates)

    def close_position(self, position_id: str, actual_profit: float, status: str = 'closed_won') -> bool:
        """
        Close position with final profit

        Args:
            position_id: Position ID
            actual_profit: Final profit/loss
            status: 'closed_won' or 'closed_lost'

        Returns:
            True if successful
        """
        updates = {
            'actual_profit': actual_profit,
            'status': status,
            'closed_at': datetime.now().isoformat()
        }

        return self.update_position(position_id, updates)

    def get_position(self, position_id: str) -> Optional[Dict]:
        """Get single position by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM positions WHERE id = ?", (position_id,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def get_open_positions(self, user_id: Optional[str] = None) -> List[Dict]:
        """
        Get all open positions

        Args:
            user_id: Filter by user ID (optional)

        Returns:
            List of position dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if user_id:
            cursor.execute(
                "SELECT * FROM positions WHERE status = 'open' AND user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
        else:
            cursor.execute("SELECT * FROM positions WHERE status = 'open' ORDER BY created_at DESC")

        return [dict(row) for row in cursor.fetchall()]

    def get_user_positions(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get positions for specific user

        Args:
            user_id: User ID
            status: Filter by status (optional)
            limit: Maximum number of results

        Returns:
            List of position dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if status:
            cursor.execute("""
                SELECT * FROM positions
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, status, limit))
        else:
            cursor.execute("""
                SELECT * FROM positions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))

        return [dict(row) for row in cursor.fetchall()]

    def log_hedge_alert(self, alert_data: Dict) -> int:
        """
        Log hedge alert to history

        Args:
            alert_data: Dictionary with alert details

        Returns:
            Alert ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO hedge_alerts (
                position_id, user_id, game_id,
                hedge_team, hedge_odds, hedge_bookmaker,
                recommended_stake, locked_profit,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_data['position_id'],
            alert_data['user_id'],
            alert_data['game_id'],
            alert_data['hedge_team'],
            alert_data['hedge_odds'],
            alert_data['hedge_bookmaker'],
            alert_data['recommended_stake'],
            alert_data['locked_profit'],
            datetime.now().isoformat()
        ))

        conn.commit()
        return cursor.lastrowid

    def mark_alert_executed(self, alert_id: int) -> bool:
        """Mark hedge alert as executed"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE hedge_alerts
            SET was_executed = 1
            WHERE id = ?
        """, (alert_id,))

        conn.commit()
        return cursor.rowcount > 0

    def get_performance_stats(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Get performance statistics for user

        Args:
            user_id: User ID
            start_date: Start date (ISO format, optional)
            end_date: End date (ISO format, optional)

        Returns:
            Dictionary with performance stats
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build WHERE clause
        where_clauses = ["user_id = ?"]
        params = [user_id]

        if start_date:
            where_clauses.append("created_at >= ?")
            params.append(start_date)

        if end_date:
            where_clauses.append("created_at <= ?")
            params.append(end_date)

        where_clause = " AND ".join(where_clauses)

        # Count by status
        cursor.execute(f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'hedged' THEN 1 ELSE 0 END) as hedged,
                SUM(CASE WHEN status = 'closed_won' AND second_team IS NULL THEN 1 ELSE 0 END) as held_won,
                SUM(CASE WHEN status = 'closed_lost' AND second_team IS NULL THEN 1 ELSE 0 END) as held_lost,
                SUM(CASE WHEN status = 'expired' THEN 1 ELSE 0 END) as expired,
                SUM(first_stake + COALESCE(second_stake, 0)) as total_wagered,
                SUM(COALESCE(actual_profit, 0)) as total_profit
            FROM positions
            WHERE {where_clause}
        """, params)

        row = cursor.fetchone()

        return {
            'total_positions': row['total'] or 0,
            'hedged_positions': row['hedged'] or 0,
            'held_and_won': row['held_won'] or 0,
            'held_and_lost': row['held_lost'] or 0,
            'expired': row['expired'] or 0,
            'total_wagered': row['total_wagered'] or 0,
            'total_profit': row['total_profit'] or 0,
            'roi_percent': (row['total_profit'] / row['total_wagered'] * 100) if row['total_wagered'] > 0 else 0
        }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None


# Global instance
volatility_db = VolatilityPositionsDB()
