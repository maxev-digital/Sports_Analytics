"""
Persistent Storage for Recommended Plays and Results
Tracks all strategy recommendations with bookmaker details, prices, and outcomes
"""
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager
import json

DATABASE_PATH = "plays_tracking.db"

class PlaysDatabase:
    """
    Database for tracking recommended plays and their results
    Provides full transparency with historical performance across server restarts
    """

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Recommended Plays Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recommended_plays (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    play_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    game_time TEXT NOT NULL,

                    -- Strategy Information
                    strategy_name TEXT NOT NULL,
                    strategy_category TEXT NOT NULL,
                    confidence_level TEXT NOT NULL,

                    -- Recommendation Details
                    play_type TEXT NOT NULL,
                    recommended_side TEXT NOT NULL,
                    recommended_line REAL,
                    recommended_price INTEGER NOT NULL,

                    -- Bookmaker Information
                    best_book TEXT NOT NULL,
                    alternate_books TEXT,

                    -- Edge Calculation
                    our_probability REAL NOT NULL,
                    market_probability REAL NOT NULL,
                    edge_percentage REAL NOT NULL,
                    expected_value REAL NOT NULL,

                    -- Additional Context
                    momentum_indicator TEXT,
                    trend_data TEXT,
                    notes TEXT,

                    -- Status
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL
                )
            """)

            # Play Results Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS play_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    play_id TEXT NOT NULL,

                    -- Result Information
                    result TEXT NOT NULL,
                    actual_total REAL,
                    final_score_home INTEGER,
                    final_score_away INTEGER,

                    -- Pricing at Close
                    closing_line REAL,
                    closing_price INTEGER,
                    line_movement REAL,

                    -- Profitability
                    profit_loss REAL NOT NULL,
                    roi REAL NOT NULL,

                    -- Verification
                    settled_at TEXT NOT NULL,
                    verified BOOLEAN DEFAULT 1,

                    FOREIGN KEY (play_id) REFERENCES recommended_plays (play_id)
                )
            """)

            # Strategy Performance Summary Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT UNIQUE NOT NULL,
                    strategy_category TEXT NOT NULL,

                    -- Performance Metrics
                    total_plays INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    pushes INTEGER DEFAULT 0,
                    pending INTEGER DEFAULT 0,

                    -- Financial Metrics
                    total_profit REAL DEFAULT 0.0,
                    avg_edge REAL DEFAULT 0.0,
                    avg_roi REAL DEFAULT 0.0,
                    win_rate REAL DEFAULT 0.0,

                    -- Confidence Breakdown
                    high_conf_wins INTEGER DEFAULT 0,
                    high_conf_total INTEGER DEFAULT 0,
                    medium_conf_wins INTEGER DEFAULT 0,
                    medium_conf_total INTEGER DEFAULT 0,
                    low_conf_wins INTEGER DEFAULT 0,
                    low_conf_total INTEGER DEFAULT 0,

                    -- Updated Timestamp
                    last_updated TEXT NOT NULL
                )
            """)

            # Alert Categories Table (Beyond arbitrage/steam/line movements)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    description TEXT,
                    color_code TEXT,
                    icon TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    sort_order INTEGER DEFAULT 0
                )
            """)

            # Insert default alert categories
            default_categories = [
                ('arbitrage', 'Arbitrage', 'Risk-free betting opportunities', 'green', 'shield', 1, 1),
                ('steam_move', 'Steam Move', 'Sharp money line movements', 'blue', 'trending-up', 1, 2),
                ('line_movement', 'Line Movement', 'Significant odds shifts', 'purple', 'activity', 1, 3),
                ('pace_based', 'Pace Analysis', 'Game pace and tempo predictions', 'orange', 'zap', 1, 4),
                ('fatigue', 'Fatigue Model', 'Rest days and back-to-back analysis', 'red', 'battery', 1, 5),
                ('regression', 'Regression Analysis', 'Statistical mean reversion plays', 'cyan', 'trending-down', 1, 6),
                ('moneyline', 'Moneyline Value', 'Undervalued moneyline opportunities', 'yellow', 'dollar-sign', 1, 7),
                ('multi_sport_ensemble', 'Multi-Sport Ensemble', 'Combined strategy recommendations', 'indigo', 'layers', 1, 8),
                ('live_betting', 'Live Betting', 'In-game betting opportunities', 'pink', 'radio', 1, 9),
                ('sharp_action', 'Sharp Action', 'Professional bettor movements', 'teal', 'users', 1, 10),
                ('public_fade', 'Public Fade', 'Contrarian plays against public', 'amber', 'users-x', 1, 11),
                ('weather_impact', 'Weather Edge', 'Weather-adjusted predictions', 'gray', 'cloud-rain', 1, 12)
            ]

            cursor.executemany("""
                INSERT OR IGNORE INTO alert_categories
                (category_name, display_name, description, color_code, icon, is_active, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, default_categories)

    def log_recommended_play(self, play_data: Dict) -> str:
        """
        Log a new recommended play
        Returns the play_id
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            play_id = f"{play_data['game_id']}_{play_data['strategy_name']}_{datetime.now().timestamp()}"

            cursor.execute("""
                INSERT INTO recommended_plays (
                    play_id, timestamp, game_id, sport, home_team, away_team, game_time,
                    strategy_name, strategy_category, confidence_level,
                    play_type, recommended_side, recommended_line, recommended_price,
                    best_book, alternate_books,
                    our_probability, market_probability, edge_percentage, expected_value,
                    momentum_indicator, trend_data, notes, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                play_id,
                play_data['timestamp'],
                play_data['game_id'],
                play_data.get('sport', 'NBA'),
                play_data['home_team'],
                play_data['away_team'],
                play_data['game_time'],
                play_data['strategy_name'],
                play_data.get('strategy_category', play_data['strategy_name']),
                play_data['confidence_level'],
                play_data['play_type'],
                play_data['recommended_side'],
                play_data.get('recommended_line'),
                play_data['recommended_price'],
                play_data['best_book'],
                json.dumps(play_data.get('alternate_books', [])),
                play_data['our_probability'],
                play_data['market_probability'],
                play_data['edge_percentage'],
                play_data['expected_value'],
                play_data.get('momentum_indicator'),
                json.dumps(play_data.get('trend_data', {})),
                play_data.get('notes', ''),
                'pending',
                datetime.now().isoformat()
            ))

            # Update strategy performance
            self._update_strategy_stats(play_data['strategy_name'], play_data.get('strategy_category', play_data['strategy_name']))

            return play_id

    def record_play_result(self, play_id: str, result_data: Dict) -> bool:
        """
        Record the result of a play
        Returns True if successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Insert result
            cursor.execute("""
                INSERT INTO play_results (
                    play_id, result, actual_total, final_score_home, final_score_away,
                    closing_line, closing_price, line_movement,
                    profit_loss, roi, settled_at, verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                play_id,
                result_data['result'],
                result_data.get('actual_total'),
                result_data.get('final_score_home'),
                result_data.get('final_score_away'),
                result_data.get('closing_line'),
                result_data.get('closing_price'),
                result_data.get('line_movement', 0.0),
                result_data['profit_loss'],
                result_data['roi'],
                datetime.now().isoformat(),
                result_data.get('verified', True)
            ))

            # Update play status
            cursor.execute("""
                UPDATE recommended_plays
                SET status = ?
                WHERE play_id = ?
            """, (result_data['result'], play_id))

            # Get strategy name for this play
            cursor.execute("SELECT strategy_name, confidence_level FROM recommended_plays WHERE play_id = ?", (play_id,))
            play_info = cursor.fetchone()

            if play_info:
                self._update_strategy_performance(
                    play_info['strategy_name'],
                    result_data['result'],
                    play_info['confidence_level'],
                    result_data['profit_loss'],
                    result_data['roi']
                )

            return True

    def _update_strategy_stats(self, strategy_name: str, strategy_category: str):
        """Update strategy performance table when new play is logged"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO strategy_performance (strategy_name, strategy_category, pending, last_updated)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(strategy_name) DO UPDATE SET
                    pending = pending + 1,
                    total_plays = total_plays + 1,
                    last_updated = ?
            """, (strategy_name, strategy_category, datetime.now().isoformat(), datetime.now().isoformat()))

    def _update_strategy_performance(self, strategy_name: str, result: str, confidence: str, profit_loss: float, roi: float):
        """Update strategy performance metrics after result is recorded"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get current stats
            cursor.execute("SELECT * FROM strategy_performance WHERE strategy_name = ?", (strategy_name,))
            current = cursor.fetchone()

            if not current:
                return

            # Calculate new metrics
            wins = current['wins'] + (1 if result == 'won' else 0)
            losses = current['losses'] + (1 if result == 'lost' else 0)
            pushes = current['pushes'] + (1 if result == 'push' else 0)
            pending = max(0, current['pending'] - 1)

            total_profit = current['total_profit'] + profit_loss

            completed = wins + losses + pushes
            win_rate = (wins / completed * 100) if completed > 0 else 0.0

            # Update confidence breakdown
            conf_updates = {}
            if confidence == 'HIGH':
                conf_updates['high_conf_total'] = current['high_conf_total'] + 1
                conf_updates['high_conf_wins'] = current['high_conf_wins'] + (1 if result == 'won' else 0)
            elif confidence == 'MEDIUM':
                conf_updates['medium_conf_total'] = current['medium_conf_total'] + 1
                conf_updates['medium_conf_wins'] = current['medium_conf_wins'] + (1 if result == 'won' else 0)
            else:
                conf_updates['low_conf_total'] = current['low_conf_total'] + 1
                conf_updates['low_conf_wins'] = current['low_conf_wins'] + (1 if result == 'won' else 0)

            # Update database
            cursor.execute("""
                UPDATE strategy_performance SET
                    wins = ?, losses = ?, pushes = ?, pending = ?,
                    total_profit = ?, win_rate = ?,
                    avg_roi = (avg_roi * ? + ?) / ?,
                    high_conf_wins = ?, high_conf_total = ?,
                    medium_conf_wins = ?, medium_conf_total = ?,
                    low_conf_wins = ?, low_conf_total = ?,
                    last_updated = ?
                WHERE strategy_name = ?
            """, (
                wins, losses, pushes, pending,
                total_profit, win_rate,
                completed - 1, roi, completed,
                conf_updates.get('high_conf_wins', current['high_conf_wins']),
                conf_updates.get('high_conf_total', current['high_conf_total']),
                conf_updates.get('medium_conf_wins', current['medium_conf_wins']),
                conf_updates.get('medium_conf_total', current['medium_conf_total']),
                conf_updates.get('low_conf_wins', current['low_conf_wins']),
                conf_updates.get('low_conf_total', current['low_conf_total']),
                datetime.now().isoformat(),
                strategy_name
            ))

    def get_all_plays(self, limit: int = 100, status: Optional[str] = None) -> List[Dict]:
        """Get all recommended plays with optional status filter"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT p.*, r.result, r.profit_loss, r.roi, r.closing_line, r.settled_at
                FROM recommended_plays p
                LEFT JOIN play_results r ON p.play_id = r.play_id
            """

            if status:
                query += " WHERE p.status = ?"
                cursor.execute(query + " ORDER BY p.created_at DESC LIMIT ?", (status, limit))
            else:
                cursor.execute(query + " ORDER BY p.created_at DESC LIMIT ?", (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_strategy_performance(self, strategy_name: Optional[str] = None) -> List[Dict]:
        """Get performance metrics for strategies"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if strategy_name:
                cursor.execute("SELECT * FROM strategy_performance WHERE strategy_name = ?", (strategy_name,))
            else:
                cursor.execute("SELECT * FROM strategy_performance ORDER BY win_rate DESC")

            return [dict(row) for row in cursor.fetchall()]

    def get_plays_by_strategy(self, strategy_name: str, limit: int = 50) -> List[Dict]:
        """Get all plays for a specific strategy"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT p.*, r.result, r.profit_loss, r.roi
                FROM recommended_plays p
                LEFT JOIN play_results r ON p.play_id = r.play_id
                WHERE p.strategy_name = ?
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (strategy_name, limit))

            return [dict(row) for row in cursor.fetchall()]

    def get_plays_by_category(self, category: str, limit: int = 50) -> List[Dict]:
        """Get all plays for a specific category"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT p.*, r.result, r.profit_loss, r.roi
                FROM recommended_plays p
                LEFT JOIN play_results r ON p.play_id = r.play_id
                WHERE p.strategy_category = ?
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (category, limit))

            return [dict(row) for row in cursor.fetchall()]

    def get_alert_categories(self) -> List[Dict]:
        """Get all alert categories"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alert_categories WHERE is_active = 1 ORDER BY sort_order")
            return [dict(row) for row in cursor.fetchall()]

    def get_pending_plays(self) -> List[Dict]:
        """Get all pending plays waiting for results"""
        return self.get_all_plays(status='pending')

    def get_recent_results(self, days: int = 7) -> List[Dict]:
        """Get recent settled plays"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT p.*, r.result, r.profit_loss, r.roi, r.settled_at
                FROM recommended_plays p
                INNER JOIN play_results r ON p.play_id = r.play_id
                WHERE r.settled_at >= datetime('now', '-' || ? || ' days')
                ORDER BY r.settled_at DESC
            """, (days,))

            return [dict(row) for row in cursor.fetchall()]

    def get_performance_by_sport(self, sport: Optional[str] = None) -> Dict:
        """Get performance metrics grouped by sport"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if sport:
                # Get stats for specific sport
                cursor.execute("""
                    SELECT
                        p.sport,
                        COUNT(DISTINCT p.play_id) as total_plays,
                        SUM(CASE WHEN r.result = 'won' THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN r.result = 'lost' THEN 1 ELSE 0 END) as losses,
                        SUM(CASE WHEN r.result = 'push' THEN 1 ELSE 0 END) as pushes,
                        SUM(CASE WHEN p.status = 'pending' THEN 1 ELSE 0 END) as pending,
                        COALESCE(SUM(r.profit_loss), 0) as total_profit,
                        COALESCE(AVG(p.edge_percentage), 0) as avg_edge,
                        COALESCE(AVG(r.roi), 0) as avg_roi
                    FROM recommended_plays p
                    LEFT JOIN play_results r ON p.play_id = r.play_id
                    WHERE p.sport = ?
                    GROUP BY p.sport
                """, (sport,))
            else:
                # Get stats for all sports
                cursor.execute("""
                    SELECT
                        p.sport,
                        COUNT(DISTINCT p.play_id) as total_plays,
                        SUM(CASE WHEN r.result = 'won' THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN r.result = 'lost' THEN 1 ELSE 0 END) as losses,
                        SUM(CASE WHEN r.result = 'push' THEN 1 ELSE 0 END) as pushes,
                        SUM(CASE WHEN p.status = 'pending' THEN 1 ELSE 0 END) as pending,
                        COALESCE(SUM(r.profit_loss), 0) as total_profit,
                        COALESCE(AVG(p.edge_percentage), 0) as avg_edge,
                        COALESCE(AVG(r.roi), 0) as avg_roi
                    FROM recommended_plays p
                    LEFT JOIN play_results r ON p.play_id = r.play_id
                    GROUP BY p.sport
                    ORDER BY total_plays DESC
                """)

            results = {}
            for row in cursor.fetchall():
                sport_name = row['sport']
                completed = row['wins'] + row['losses'] + row['pushes']
                win_rate = (row['wins'] / completed * 100) if completed > 0 else 0.0

                results[sport_name] = {
                    'sport': sport_name,
                    'total_plays': row['total_plays'],
                    'wins': row['wins'] or 0,
                    'losses': row['losses'] or 0,
                    'pushes': row['pushes'] or 0,
                    'pending': row['pending'] or 0,
                    'completed': completed,
                    'win_rate': round(win_rate, 2),
                    'total_profit': round(row['total_profit'], 2),
                    'avg_edge': round(row['avg_edge'], 2),
                    'avg_roi': round(row['avg_roi'], 2)
                }

            return results

    def get_plays_by_sport(self, sport: str, limit: int = 50) -> List[Dict]:
        """Get all plays for a specific sport"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT p.*, r.result, r.profit_loss, r.roi
                FROM recommended_plays p
                LEFT JOIN play_results r ON p.play_id = r.play_id
                WHERE p.sport = ?
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (sport, limit))

            return [dict(row) for row in cursor.fetchall()]

# Global instance
plays_db = PlaysDatabase()
