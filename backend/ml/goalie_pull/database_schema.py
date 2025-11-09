"""
Database Schema for Goalie Pull Timing Alpha System

Stores:
1. Historical pull events with full game state
2. State snapshots before pulls (for training)
3. Coach pull profiles
4. Live alerts and outcomes (for tracking CLV and ROI)
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

DB_PATH = Path(__file__).parent.parent.parent / "database" / "goalie_pull.db"


class GoaliePullDB:
    """Database handler for goalie pull timing alpha system"""

    def __init__(self):
        self.db_path = DB_PATH
        self.init_database()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize all tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Historical pull events with full context
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_pulls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                season INTEGER NOT NULL,
                game_date TEXT NOT NULL,

                -- Teams
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                pulling_team TEXT NOT NULL,
                opponent_team TEXT NOT NULL,

                -- Pull Event Details
                pull_time_remaining TEXT NOT NULL,
                pull_time_seconds INTEGER NOT NULL,
                pull_period INTEGER NOT NULL,
                score_differential INTEGER NOT NULL,

                -- Game State at Pull
                strength_state TEXT,
                zone TEXT,
                possession TEXT,
                faceoff_zone TEXT,

                -- Coach
                coach_id TEXT,
                home_coach TEXT,
                away_coach TEXT,

                -- Context
                timeout_available BOOLEAN,
                timeout_just_used BOOLEAN,
                playoff_game BOOLEAN,

                -- Outcome
                goals_by_pulling_team INTEGER DEFAULT 0,
                goals_by_opponent INTEGER DEFAULT 0,
                total_goals INTEGER DEFAULT 0,
                pulling_team_tied BOOLEAN DEFAULT FALSE,
                pulling_team_won BOOLEAN DEFAULT FALSE,

                -- Metadata
                data_source TEXT DEFAULT 'moneypuck',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(game_id, pulling_team)
            )
        """)

        # State snapshots before pulls (for training)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pull_state_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pull_id INTEGER NOT NULL,
                game_id TEXT NOT NULL,

                -- Time before actual pull
                seconds_before_pull INTEGER NOT NULL,
                time_remaining TEXT NOT NULL,
                time_remaining_seconds INTEGER NOT NULL,

                -- Game State
                score_differential INTEGER NOT NULL,
                period INTEGER NOT NULL,
                strength_state TEXT,
                zone TEXT,
                possession TEXT,
                faceoff_zone TEXT,

                -- Momentum features
                xg_for_last_5min REAL,
                xg_against_last_5min REAL,
                shots_for_last_5min INTEGER,
                shots_against_last_5min INTEGER,
                recent_goal BOOLEAN,

                -- Coach profile at this point
                coach_id TEXT,
                coach_aggressive_rating INTEGER,

                -- Context
                timeout_available BOOLEAN,
                playoff_game BOOLEAN,
                home_game BOOLEAN,

                -- Target (did pull happen in next N seconds?)
                pull_in_next_15s BOOLEAN DEFAULT FALSE,
                pull_in_next_30s BOOLEAN DEFAULT FALSE,
                pull_in_next_60s BOOLEAN DEFAULT FALSE,

                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (pull_id) REFERENCES historical_pulls(id)
            )
        """)

        # No-pull examples (negative training data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS no_pull_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                season INTEGER NOT NULL,
                game_date TEXT NOT NULL,

                -- Teams
                trailing_team TEXT NOT NULL,
                leading_team TEXT NOT NULL,

                -- Game State
                time_remaining TEXT NOT NULL,
                time_remaining_seconds INTEGER NOT NULL,
                score_differential INTEGER NOT NULL,
                period INTEGER NOT NULL,
                strength_state TEXT,

                -- Coach
                coach_id TEXT,
                coach_aggressive_rating INTEGER,

                -- Why no pull?
                reason TEXT,  -- 'too_early', 'conservative_coach', 'shorthanded', etc.

                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Coach pull profiles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coach_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coach_id TEXT NOT NULL UNIQUE,
                coach_name TEXT NOT NULL,

                -- Current assignment
                current_team TEXT,
                seasons_active TEXT,  -- e.g., "2022-2025"

                -- Pull statistics (trailing by 1)
                pulls_down_1 INTEGER DEFAULT 0,
                median_pull_time_down_1_seconds INTEGER,
                p25_pull_time_down_1_seconds INTEGER,
                p75_pull_time_down_1_seconds INTEGER,

                -- Pull statistics (trailing by 2)
                pulls_down_2 INTEGER DEFAULT 0,
                median_pull_time_down_2_seconds INTEGER,
                p25_pull_time_down_2_seconds INTEGER,
                p75_pull_time_down_2_seconds INTEGER,

                -- Pull statistics (trailing by 3+)
                pulls_down_3_plus INTEGER DEFAULT 0,
                median_pull_time_down_3_plus_seconds INTEGER,

                -- Behavior patterns
                pull_rate_when_shorthanded REAL DEFAULT 0.0,
                pull_rate_playoff_vs_regular REAL DEFAULT 1.0,
                pulls_before_2min INTEGER DEFAULT 0,
                pulls_after_1min INTEGER DEFAULT 0,

                -- Ratings
                aggressive_rating INTEGER,  -- 1 (conservative) to 10 (aggressive)
                predictability_rating INTEGER,  -- 1 (chaotic) to 10 (predictable)

                -- Metadata
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Live alerts (for tracking and CLV analysis)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goalie_pull_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_timestamp TEXT NOT NULL,
                game_id TEXT NOT NULL,

                -- Game Info
                home_team TEXT,
                away_team TEXT,
                trailing_team TEXT,

                -- State Snapshot
                time_remaining TEXT,
                time_remaining_seconds INTEGER,
                score_diff INTEGER,
                zone TEXT,
                possession TEXT,
                strength TEXT,
                coach_id TEXT,

                -- Model Outputs
                pull_propensity REAL,
                p_at_least_1_goal REAL,
                fair_price_decimal REAL,
                fair_price_american TEXT,
                required_cushion REAL,

                -- Offered Price
                bookmaker TEXT,
                offered_price_american TEXT,
                offered_price_decimal REAL,
                cushion_captured REAL,
                ev_at_entry REAL,
                quote_age_seconds REAL,

                -- Bet Details (if placed)
                bet_placed BOOLEAN DEFAULT FALSE,
                bet_size REAL,
                kelly_fraction REAL,
                fill_latency_ms REAL,

                -- Post-Pull Market (CLV Benchmark)
                price_when_pull_obvious TEXT,
                price_when_pull_obvious_decimal REAL,
                clv_vs_post_pull REAL,
                seconds_between_alert_and_pull REAL,

                -- Outcome
                pull_occurred BOOLEAN,
                pull_time TEXT,
                goals_scored INTEGER,
                bet_result TEXT,  -- 'win', 'loss', 'push', 'no_bet'
                profit_loss REAL,
                roi REAL,

                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Regime-specific goal rates (for probability model)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regime_goal_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season INTEGER NOT NULL,
                team TEXT NOT NULL,

                -- 5v5 rates (normal play)
                lambda_5v5_for REAL,
                lambda_5v5_against REAL,

                -- 6v5 rates (extra attacker)
                lambda_6v5_for REAL,
                lambda_6v5_against REAL,

                -- Empty net rates
                lambda_en_for REAL,
                lambda_en_against REAL,

                -- Team strength
                xg_rate_for REAL,
                xg_rate_against REAL,

                -- Metadata
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(season, team)
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pulls_game ON historical_pulls(game_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pulls_team ON historical_pulls(pulling_team)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pulls_coach ON historical_pulls(coach_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_pull ON pull_state_snapshots(pull_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_game ON goalie_pull_alerts(game_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON goalie_pull_alerts(alert_timestamp)")

        conn.commit()
        conn.close()
        print(f"[OK] Goalie Pull database initialized: {self.db_path}")

    # ==================== HISTORICAL PULLS ====================

    def insert_historical_pull(self, pull_data: Dict) -> int:
        """Insert historical pull event, return pull_id"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO historical_pulls
            (game_id, season, game_date, home_team, away_team, pulling_team, opponent_team,
             pull_time_remaining, pull_time_seconds, pull_period, score_differential,
             strength_state, zone, possession, faceoff_zone, coach_id, home_coach, away_coach,
             timeout_available, timeout_just_used, playoff_game,
             goals_by_pulling_team, goals_by_opponent, total_goals,
             pulling_team_tied, pulling_team_won, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pull_data['game_id'],
            pull_data['season'],
            pull_data['game_date'],
            pull_data['home_team'],
            pull_data['away_team'],
            pull_data['pulling_team'],
            pull_data['opponent_team'],
            pull_data['pull_time_remaining'],
            pull_data['pull_time_seconds'],
            pull_data['pull_period'],
            pull_data['score_differential'],
            pull_data.get('strength_state'),
            pull_data.get('zone'),
            pull_data.get('possession'),
            pull_data.get('faceoff_zone'),
            pull_data.get('coach_id'),
            pull_data.get('home_coach'),
            pull_data.get('away_coach'),
            pull_data.get('timeout_available'),
            pull_data.get('timeout_just_used'),
            pull_data.get('playoff_game', False),
            pull_data.get('goals_by_pulling_team', 0),
            pull_data.get('goals_by_opponent', 0),
            pull_data.get('total_goals', 0),
            pull_data.get('pulling_team_tied', False),
            pull_data.get('pulling_team_won', False),
            pull_data.get('data_source', 'moneypuck')
        ))

        pull_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return pull_id

    def get_historical_pulls(self, season: int = None, team: str = None, coach: str = None) -> List[Dict]:
        """Get historical pull events"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM historical_pulls WHERE 1=1"
        params = []

        if season:
            query += " AND season = ?"
            params.append(season)
        if team:
            query += " AND pulling_team = ?"
            params.append(team)
        if coach:
            query += " AND coach_id = ?"
            params.append(coach)

        query += " ORDER BY game_date DESC"

        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    # ==================== COACH PROFILES ====================

    def insert_coach_profile(self, coach_data: Dict) -> int:
        """Insert or update coach profile"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO coach_profiles
            (coach_id, coach_name, current_team, seasons_active,
             pulls_down_1, median_pull_time_down_1_seconds, p25_pull_time_down_1_seconds, p75_pull_time_down_1_seconds,
             pulls_down_2, median_pull_time_down_2_seconds, p25_pull_time_down_2_seconds, p75_pull_time_down_2_seconds,
             pulls_down_3_plus, median_pull_time_down_3_plus_seconds,
             pull_rate_when_shorthanded, pull_rate_playoff_vs_regular,
             pulls_before_2min, pulls_after_1min,
             aggressive_rating, predictability_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            coach_data['coach_id'],
            coach_data['coach_name'],
            coach_data.get('current_team'),
            coach_data.get('seasons_active'),
            coach_data.get('pulls_down_1', 0),
            coach_data.get('median_pull_time_down_1_seconds'),
            coach_data.get('p25_pull_time_down_1_seconds'),
            coach_data.get('p75_pull_time_down_1_seconds'),
            coach_data.get('pulls_down_2', 0),
            coach_data.get('median_pull_time_down_2_seconds'),
            coach_data.get('p25_pull_time_down_2_seconds'),
            coach_data.get('p75_pull_time_down_2_seconds'),
            coach_data.get('pulls_down_3_plus', 0),
            coach_data.get('median_pull_time_down_3_plus_seconds'),
            coach_data.get('pull_rate_when_shorthanded', 0.0),
            coach_data.get('pull_rate_playoff_vs_regular', 1.0),
            coach_data.get('pulls_before_2min', 0),
            coach_data.get('pulls_after_1min', 0),
            coach_data.get('aggressive_rating'),
            coach_data.get('predictability_rating')
        ))

        coach_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return coach_id

    def get_coach_profile(self, coach_id: str) -> Optional[Dict]:
        """Get coach profile by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM coach_profiles WHERE coach_id = ?", (coach_id,))
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()

        conn.close()

        if row:
            return dict(zip(columns, row))
        return None

    def get_all_coach_profiles(self) -> List[Dict]:
        """Get all coach profiles"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM coach_profiles ORDER BY coach_name")
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    # ==================== LIVE ALERTS ====================

    def insert_alert(self, alert_data: Dict) -> int:
        """Insert live alert, return alert_id"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO goalie_pull_alerts
            (alert_timestamp, game_id, home_team, away_team, trailing_team,
             time_remaining, time_remaining_seconds, score_diff, zone, possession, strength, coach_id,
             pull_propensity, p_at_least_1_goal, fair_price_decimal, fair_price_american, required_cushion,
             bookmaker, offered_price_american, offered_price_decimal, cushion_captured, ev_at_entry, quote_age_seconds,
             bet_placed, bet_size, kelly_fraction, fill_latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_data['alert_timestamp'],
            alert_data['game_id'],
            alert_data.get('home_team'),
            alert_data.get('away_team'),
            alert_data.get('trailing_team'),
            alert_data.get('time_remaining'),
            alert_data.get('time_remaining_seconds'),
            alert_data.get('score_diff'),
            alert_data.get('zone'),
            alert_data.get('possession'),
            alert_data.get('strength'),
            alert_data.get('coach_id'),
            alert_data.get('pull_propensity'),
            alert_data.get('p_at_least_1_goal'),
            alert_data.get('fair_price_decimal'),
            alert_data.get('fair_price_american'),
            alert_data.get('required_cushion'),
            alert_data.get('bookmaker'),
            alert_data.get('offered_price_american'),
            alert_data.get('offered_price_decimal'),
            alert_data.get('cushion_captured'),
            alert_data.get('ev_at_entry'),
            alert_data.get('quote_age_seconds'),
            alert_data.get('bet_placed', False),
            alert_data.get('bet_size'),
            alert_data.get('kelly_fraction'),
            alert_data.get('fill_latency_ms')
        ))

        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return alert_id

    def update_alert_outcome(self, alert_id: int, outcome_data: Dict):
        """Update alert with outcome and CLV data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE goalie_pull_alerts
            SET price_when_pull_obvious = ?,
                price_when_pull_obvious_decimal = ?,
                clv_vs_post_pull = ?,
                seconds_between_alert_and_pull = ?,
                pull_occurred = ?,
                pull_time = ?,
                goals_scored = ?,
                bet_result = ?,
                profit_loss = ?,
                roi = ?
            WHERE id = ?
        """, (
            outcome_data.get('price_when_pull_obvious'),
            outcome_data.get('price_when_pull_obvious_decimal'),
            outcome_data.get('clv_vs_post_pull'),
            outcome_data.get('seconds_between_alert_and_pull'),
            outcome_data.get('pull_occurred'),
            outcome_data.get('pull_time'),
            outcome_data.get('goals_scored'),
            outcome_data.get('bet_result'),
            outcome_data.get('profit_loss'),
            outcome_data.get('roi'),
            alert_id
        ))

        conn.commit()
        conn.close()


# Initialize database on import
if __name__ == "__main__":
    db = GoaliePullDB()
    print("Database initialized successfully!")
