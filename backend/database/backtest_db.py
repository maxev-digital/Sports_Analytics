"""
Database schema for backtesting results
Completely separate from live strategies/alerts database
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Database location - separate from live strategies
DB_PATH = Path(__file__).parent / "backtests.db"


class BacktestDB:
    """Database handler for backtest results"""

    def __init__(self):
        self.db_path = DB_PATH
        self.init_database()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Historical games table (from BALLDONTLIE)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_games (
                game_id TEXT PRIMARY KEY,
                sport TEXT NOT NULL,
                date TEXT NOT NULL,
                season INTEGER,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_score INTEGER NOT NULL,
                away_score INTEGER NOT NULL,
                q1_home INTEGER,
                q1_away INTEGER,
                q2_home INTEGER,
                q2_away INTEGER,
                q3_home INTEGER,
                q3_away INTEGER,
                q4_home INTEGER,
                q4_away INTEGER,
                ot_home INTEGER DEFAULT 0,
                ot_away INTEGER DEFAULT 0,
                data_source TEXT DEFAULT 'balldontlie',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Prospective odds history (start collecting NOW)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS odds_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                game_id TEXT,
                sport TEXT NOT NULL,
                home_team TEXT,
                away_team TEXT,
                bookmaker TEXT NOT NULL,
                market_type TEXT NOT NULL,
                line_value REAL,
                odds INTEGER,
                period TEXT DEFAULT 'full_game',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for odds_history
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_timestamp ON odds_history(game_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sport_date ON odds_history(sport, timestamp)")

        # Strategy metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                strategy_id INTEGER PRIMARY KEY,
                angle_number INTEGER,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                why_it_works TEXT,
                example TEXT,
                typical_ev_min REAL,
                typical_ev_max REAL,
                sports TEXT,
                difficulty TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Backtest results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER NOT NULL,
                sport TEXT NOT NULL,
                date_range_start TEXT NOT NULL,
                date_range_end TEXT NOT NULL,
                total_opportunities INTEGER DEFAULT 0,
                bets_placed INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                pushes INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.0,
                roi REAL DEFAULT 0.0,
                avg_edge REAL DEFAULT 0.0,
                profit_loss REAL DEFAULT 0.0,
                confidence_interval TEXT,
                best_situations TEXT,
                data_source TEXT DEFAULT 'balldontlie',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
            )
        """)

        # Individual backtest bets (for detailed analysis)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id INTEGER NOT NULL,
                game_id TEXT NOT NULL,
                game_date TEXT NOT NULL,
                strategy_id INTEGER NOT NULL,
                bet_type TEXT,
                bet_line REAL,
                bet_odds INTEGER,
                actual_result REAL,
                outcome TEXT,
                profit_loss REAL,
                edge REAL,
                confidence TEXT,
                notes TEXT,
                FOREIGN KEY (backtest_id) REFERENCES backtest_results(id),
                FOREIGN KEY (game_id) REFERENCES historical_games(game_id)
            )
        """)

        conn.commit()
        conn.close()
        print(f"[OK] Backtest database initialized: {self.db_path}")

    # ==================== HISTORICAL GAMES ====================

    def insert_game(self, game_data: Dict) -> bool:
        """Insert historical game data"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO historical_games
                (game_id, sport, date, season, home_team, away_team,
                 home_score, away_score, q1_home, q1_away, q2_home, q2_away,
                 q3_home, q3_away, q4_home, q4_away, ot_home, ot_away, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_data['game_id'],
                game_data['sport'],
                game_data['date'],
                game_data.get('season'),
                game_data['home_team'],
                game_data['away_team'],
                game_data['home_score'],
                game_data['away_score'],
                game_data.get('q1_home', 0),
                game_data.get('q1_away', 0),
                game_data.get('q2_home', 0),
                game_data.get('q2_away', 0),
                game_data.get('q3_home', 0),
                game_data.get('q3_away', 0),
                game_data.get('q4_home', 0),
                game_data.get('q4_away', 0),
                game_data.get('ot_home', 0),
                game_data.get('ot_away', 0),
                game_data.get('data_source', 'balldontlie')
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error inserting game: {e}")
            return False

    def get_games(self, sport: str = None, season: int = None, limit: int = 1000) -> List[Dict]:
        """Get historical games"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM historical_games WHERE 1=1"
        params = []

        if sport:
            query += " AND sport = ?"
            params.append(sport)

        if season:
            query += " AND season = ?"
            params.append(season)

        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    # ==================== BACKTEST RESULTS ====================

    def save_backtest_result(self, result: Dict) -> int:
        """Save backtest result and return backtest_id"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO backtest_results
            (strategy_id, sport, date_range_start, date_range_end,
             total_opportunities, bets_placed, wins, losses, pushes,
             win_rate, roi, avg_edge, profit_loss, confidence_interval,
             best_situations, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result['strategy_id'],
            result['sport'],
            result['date_range_start'],
            result['date_range_end'],
            result['total_opportunities'],
            result['bets_placed'],
            result['wins'],
            result['losses'],
            result['pushes'],
            result['win_rate'],
            result['roi'],
            result['avg_edge'],
            result['profit_loss'],
            result.get('confidence_interval', ''),
            result.get('best_situations', ''),
            result.get('data_source', 'balldontlie')
        ))

        backtest_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return backtest_id

    def get_backtest_results(self, strategy_id: int = None, sport: str = None) -> List[Dict]:
        """Get backtest results"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM backtest_results WHERE 1=1"
        params = []

        if strategy_id:
            query += " AND strategy_id = ?"
            params.append(strategy_id)

        if sport:
            query += " AND sport = ?"
            params.append(sport)

        query += " ORDER BY last_updated DESC"

        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    def save_backtest_bet(self, bet_data: Dict) -> bool:
        """Save individual bet from backtest"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO backtest_bets
                (backtest_id, game_id, game_date, strategy_id, bet_type,
                 bet_line, bet_odds, actual_result, outcome, profit_loss,
                 edge, confidence, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bet_data['backtest_id'],
                bet_data['game_id'],
                bet_data['game_date'],
                bet_data['strategy_id'],
                bet_data.get('bet_type'),
                bet_data.get('bet_line'),
                bet_data.get('bet_odds'),
                bet_data.get('actual_result'),
                bet_data['outcome'],
                bet_data['profit_loss'],
                bet_data.get('edge'),
                bet_data.get('confidence'),
                bet_data.get('notes')
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving bet: {e}")
            return False


# Initialize database on import
if __name__ == "__main__":
    db = BacktestDB()
    print("Database initialized successfully!")
