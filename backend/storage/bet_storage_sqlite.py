"""Storage layer for user bets using SQLite database"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import uuid
from contextlib import contextmanager

from models.user_bet import UserBet, CreateBetRequest, calculate_profit_loss
from storage.alert_storage import alert_storage


class BetStorageSQLite:
    """Manages storage of user bets in SQLite database"""

    def __init__(self, data_dir: str = "data/bets"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "user_bets.db"
        self.json_backup = self.data_dir / "user_bets.json"

        # Initialize database
        self._init_db()

        # Migrate JSON data if exists and DB is empty
        self._migrate_from_json()

    def _init_db(self):
        """Initialize SQLite database with schema"""
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_bets (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    commence_time TEXT NOT NULL,
                    bet_type TEXT NOT NULL,
                    bet_side TEXT NOT NULL,
                    stake REAL,
                    odds REAL NOT NULL,
                    bookmaker TEXT NOT NULL,
                    alert_id TEXT,
                    confidence TEXT,
                    edge_percent REAL,
                    strategy TEXT,
                    clicked_at TEXT NOT NULL,
                    logged_at TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    result TEXT,
                    payout REAL,
                    profit_loss REAL,
                    settled_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes for common queries
            conn.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON user_bets(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_status ON user_bets(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_user_status ON user_bets(user_id, status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_sport ON user_bets(sport)')
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper handling"""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        """Convert SQLite row to dictionary"""
        return {key: row[key] for key in row.keys()}

    def _row_to_bet(self, row: sqlite3.Row) -> UserBet:
        """Convert SQLite row to UserBet model"""
        data = self._row_to_dict(row)
        # Remove created_at as it's not in the model
        data.pop('created_at', None)
        return UserBet(**data)

    def _migrate_from_json(self):
        """Migrate existing JSON data to SQLite"""
        if not self.json_backup.exists():
            return

        # Check if DB is empty
        with self._get_connection() as conn:
            count = conn.execute('SELECT COUNT(*) FROM user_bets').fetchone()[0]
            if count > 0:
                return  # Already have data

        # Load JSON data
        try:
            with open(self.json_backup, 'r') as f:
                bets = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return

        if not bets:
            return

        # Insert into SQLite
        with self._get_connection() as conn:
            for bet in bets:
                self._insert_bet_dict(conn, bet)
            conn.commit()

        print(f"Migrated {len(bets)} bets from JSON to SQLite")

    def _insert_bet_dict(self, conn, bet: dict):
        """Insert a bet dictionary into the database"""
        columns = [
            'id', 'user_id', 'game_id', 'sport', 'home_team', 'away_team',
            'commence_time', 'bet_type', 'bet_side', 'stake', 'odds', 'bookmaker',
            'alert_id', 'confidence', 'edge_percent', 'strategy', 'clicked_at',
            'logged_at', 'status', 'result', 'payout', 'profit_loss', 'settled_at'
        ]

        values = [bet.get(col) for col in columns]
        placeholders = ','.join(['?' for _ in columns])
        columns_str = ','.join(columns)

        conn.execute(
            f'INSERT OR REPLACE INTO user_bets ({columns_str}) VALUES ({placeholders})',
            values
        )

    def create_bet(self, request: CreateBetRequest) -> UserBet:
        """Create a new pending bet from a click event"""
        bet = UserBet(
            id=str(uuid.uuid4()),
            user_id=request.user_id,
            game_id=request.game_id,
            sport=request.sport,
            home_team=request.home_team,
            away_team=request.away_team,
            commence_time=request.commence_time,
            bet_type=request.bet_type,
            bet_side=request.bet_side,
            odds=request.odds,
            bookmaker=request.bookmaker,
            alert_id=request.alert_id,
            confidence=request.confidence,
            edge_percent=request.edge_percent,
            strategy=request.strategy,
            clicked_at=datetime.utcnow().isoformat(),
            status='pending'
        )

        with self._get_connection() as conn:
            self._insert_bet_dict(conn, bet.dict())
            conn.commit()

        return bet

    def get_bet(self, bet_id: str) -> Optional[UserBet]:
        """Get a specific bet by ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM user_bets WHERE id = ?',
                (bet_id,)
            ).fetchone()

            if row:
                return self._row_to_bet(row)
        return None

    def get_user_bets(
        self,
        user_id: str,
        status: Optional[str] = None,
        sport: Optional[str] = None
    ) -> List[UserBet]:
        """Get all bets for a user with optional filters"""
        query = 'SELECT * FROM user_bets WHERE user_id = ?'
        params = [user_id]

        if status:
            query += ' AND status = ?'
            params.append(status)
        if sport:
            query += ' AND sport = ?'
            params.append(sport)

        query += ' ORDER BY clicked_at DESC'

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_bet(row) for row in rows]

    def get_pending_bets(self, user_id: str) -> List[UserBet]:
        """Get all pending bets for a user"""
        return self.get_user_bets(user_id, status='pending')

    def add_stake(self, bet_id: str, stake: float) -> Optional[UserBet]:
        """Add stake to a pending bet and change status to active"""
        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM user_bets WHERE id = ?',
                (bet_id,)
            ).fetchone()

            if not row:
                return None

            if row['status'] != 'pending':
                raise ValueError(f"Cannot add stake to bet with status {row['status']}")

            logged_at = datetime.utcnow().isoformat()
            conn.execute(
                'UPDATE user_bets SET stake = ?, status = ?, logged_at = ? WHERE id = ?',
                (stake, 'active', logged_at, bet_id)
            )
            conn.commit()

            return self.get_bet(bet_id)

    def settle_bet(self, bet_id: str, result: str) -> Optional[UserBet]:
        """Settle a bet with win/loss/push result"""
        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM user_bets WHERE id = ?',
                (bet_id,)
            ).fetchone()

            if not row:
                return None

            if row['status'] != 'active':
                raise ValueError(f"Cannot settle bet with status {row['status']}")

            if not row['stake']:
                raise ValueError("Cannot settle bet without stake")

            # Calculate payout and profit/loss
            payout, profit_loss = calculate_profit_loss(
                row['stake'],
                row['odds'],
                result
            )

            # Map result to status (win->won, loss->lost, push->push)
            status_map = {'win': 'won', 'loss': 'lost', 'push': 'push'}
            new_status = status_map.get(result, result)
            settled_at = datetime.utcnow().isoformat()

            conn.execute('''
                UPDATE user_bets
                SET result = ?, payout = ?, profit_loss = ?, settled_at = ?, status = ?
                WHERE id = ?
            ''', (result, payout, profit_loss, settled_at, new_status, bet_id))
            conn.commit()

            # If bet was from an alert, settle the alert too
            alert_id = row['alert_id']
            if alert_id:
                try:
                    alert_storage.settle_alert(
                        alert_id=alert_id,
                        outcome=result,
                        actual_result=f"Bet settled: {result}"
                    )
                except Exception as e:
                    import logging
                    logging.error(f"Failed to settle alert {alert_id}: {e}")

            return self.get_bet(bet_id)

    def update_bet(self, bet_id: str, updates: dict) -> Optional[UserBet]:
        """Update bet details"""
        allowed_fields = ['bet_side', 'odds', 'stake', 'bookmaker', 'confidence', 'edge_percent']

        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM user_bets WHERE id = ?',
                (bet_id,)
            ).fetchone()

            if not row:
                return None

            # Build update query
            set_clauses = []
            params = []

            for key, value in updates.items():
                if key in allowed_fields and value is not None:
                    set_clauses.append(f'{key} = ?')
                    params.append(value)

            # If stake was added and bet was pending, change status to active
            if 'stake' in updates and updates['stake'] is not None and row['status'] == 'pending':
                set_clauses.append('status = ?')
                params.append('active')
                set_clauses.append('logged_at = ?')
                params.append(datetime.utcnow().isoformat())

            if set_clauses:
                params.append(bet_id)
                query = f'UPDATE user_bets SET {", ".join(set_clauses)} WHERE id = ?'
                conn.execute(query, params)
                conn.commit()

            # Recalculate profit/loss if needed for settled bets
            updated_bet = self.get_bet(bet_id)
            if updated_bet and updated_bet.status in ['won', 'lost', 'push']:
                if ('odds' in updates or 'stake' in updates) and updated_bet.stake and updated_bet.result:
                    payout, profit_loss = calculate_profit_loss(
                        updated_bet.stake,
                        updated_bet.odds,
                        updated_bet.result
                    )
                    conn.execute(
                        'UPDATE user_bets SET payout = ?, profit_loss = ? WHERE id = ?',
                        (payout, profit_loss, bet_id)
                    )
                    conn.commit()
                    return self.get_bet(bet_id)

            return updated_bet

    def delete_bet(self, bet_id: str) -> bool:
        """Delete a bet"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                'DELETE FROM user_bets WHERE id = ?',
                (bet_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def check_for_duplicate(
        self,
        user_id: str,
        game_id: str,
        bet_type: str,
        bet_side: str,
        bookmaker: str
    ) -> Optional[UserBet]:
        """Check if user already has a pending or active bet on this exact play"""
        with self._get_connection() as conn:
            row = conn.execute('''
                SELECT * FROM user_bets
                WHERE user_id = ? AND game_id = ? AND bet_type = ?
                AND bet_side = ? AND bookmaker = ? AND status IN ('pending', 'active')
            ''', (user_id, game_id, bet_type, bet_side, bookmaker)).fetchone()

            if row:
                return self._row_to_bet(row)
        return None

    def get_user_stats(self, user_id: str) -> dict:
        """Get betting statistics for a user"""
        with self._get_connection() as conn:
            # Get counts by status
            status_counts = conn.execute('''
                SELECT status, COUNT(*) as count
                FROM user_bets WHERE user_id = ?
                GROUP BY status
            ''', (user_id,)).fetchall()

            # Get profit/loss summary
            profit_summary = conn.execute('''
                SELECT
                    COUNT(*) as total_settled,
                    SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN status = 'push' THEN 1 ELSE 0 END) as pushes,
                    COALESCE(SUM(stake), 0) as total_staked,
                    COALESCE(SUM(profit_loss), 0) as total_profit_loss
                FROM user_bets
                WHERE user_id = ? AND status IN ('won', 'lost', 'push')
            ''', (user_id,)).fetchone()

            # Get by sport
            sport_breakdown = conn.execute('''
                SELECT sport, COUNT(*) as count, COALESCE(SUM(profit_loss), 0) as profit_loss
                FROM user_bets WHERE user_id = ? AND status IN ('won', 'lost', 'push')
                GROUP BY sport
            ''', (user_id,)).fetchall()

            return {
                'status_counts': {row['status']: row['count'] for row in status_counts},
                'total_settled': profit_summary['total_settled'],
                'wins': profit_summary['wins'],
                'losses': profit_summary['losses'],
                'pushes': profit_summary['pushes'],
                'total_staked': profit_summary['total_staked'],
                'total_profit_loss': profit_summary['total_profit_loss'],
                'win_rate': (profit_summary['wins'] / profit_summary['total_settled'] * 100) if profit_summary['total_settled'] > 0 else 0,
                'roi': (profit_summary['total_profit_loss'] / profit_summary['total_staked'] * 100) if profit_summary['total_staked'] > 0 else 0,
                'sport_breakdown': [
                    {'sport': row['sport'], 'count': row['count'], 'profit_loss': row['profit_loss']}
                    for row in sport_breakdown
                ]
            }

    def export_to_json(self) -> str:
        """Export all bets to JSON (for backup)"""
        with self._get_connection() as conn:
            rows = conn.execute('SELECT * FROM user_bets ORDER BY clicked_at DESC').fetchall()
            bets = [self._row_to_dict(row) for row in rows]

            backup_path = self.data_dir / f"user_bets_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_path, 'w') as f:
                json.dump(bets, f, indent=2)

            return str(backup_path)


# Global storage instance
bet_storage = BetStorageSQLite()
