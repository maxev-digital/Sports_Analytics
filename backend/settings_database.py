"""
User Settings Database
Stores user preferences including enabled bookmakers, bankroll, and display settings
"""
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager
import json

DATABASE_PATH = "user_settings.db"

# Predefined bookmaker presets for quick selection
BOOKMAKER_PRESETS = {
    "sharp_books": {
        "name": "Sharp Books",
        "description": "Low-margin sportsbooks preferred by professional bettors",
        "bookmakers": ["pinnacle", "bookmaker", "betclic", "marathonbet", "betsson", "nordicbet"]
    },
    "us_major": {
        "name": "US Major Sportsbooks",
        "description": "Top-tier legal US sportsbooks",
        "bookmakers": ["draftkings", "fanduel", "betmgm", "caesars", "betrivers", "pointsbet", "fanatics", "espnbet"]
    },
    "us_all": {
        "name": "All US Books",
        "description": "All US-accessible sportsbooks (legal + offshore)",
        "bookmakers": [
            "draftkings", "fanduel", "betmgm", "caesars", "betrivers", "pointsbet",
            "williamhill_us", "fanatics", "espnbet", "ballybet", "betway", "unibet",
            "wynnbet", "superbook", "twinspires", "foxbet", "betonlineag", "bovada",
            "mybookieag", "lowvig", "betus"
        ]
    },
    "offshore": {
        "name": "Offshore Books",
        "description": "US-accessible offshore sportsbooks",
        "bookmakers": ["bovada", "betonlineag", "mybookieag", "lowvig", "betus", "bookmaker", "gtbets", "intertops"]
    },
    "uk_major": {
        "name": "UK Major Bookmakers",
        "description": "Top UK sportsbooks",
        "bookmakers": ["bet365", "williamhill", "ladbrokes", "coral", "paddypower", "skybet", "betfair", "betway"]
    },
    "uk_all": {
        "name": "All UK Books",
        "description": "All UK-accessible bookmakers",
        "bookmakers": [
            "bet365", "williamhill", "ladbrokes", "coral", "paddypower", "skybet",
            "virginbet", "betfair", "matchbook", "livescorebet", "mrgreen", "betway",
            "unibet", "betvictor", "sport888"
        ]
    },
    "australia": {
        "name": "Australian Bookmakers",
        "description": "Top Australian sportsbooks",
        "bookmakers": ["sportsbet", "tab", "neds", "bluebet", "picklebet", "playup", "topsport", "ladbrokes"]
    },
    "europe": {
        "name": "European Books",
        "description": "Major European sportsbooks",
        "bookmakers": [
            "bwin", "pinnacle", "marathonbet", "betsson", "nordicbet", "coolbet",
            "leovegas", "betclic", "unibet_eu", "sport888", "tipico", "betano"
        ]
    },
    "low_vig": {
        "name": "Low Vig/Reduced Juice",
        "description": "Bookmakers with lowest margins (best odds)",
        "bookmakers": ["pinnacle", "bookmaker", "lowvig", "betclic", "marathonbet", "betsson"]
    },
    "high_limits": {
        "name": "High Limit Books",
        "description": "Sportsbooks that accept large wagers",
        "bookmakers": ["pinnacle", "bookmaker", "bet365", "betsson", "marathonbet", "bwin"]
    },
    "exchanges": {
        "name": "Betting Exchanges",
        "description": "Peer-to-peer betting exchanges",
        "bookmakers": ["betfair", "matchbook", "smarkets"]
    },
    "popular_only": {
        "name": "Popular Bookmakers",
        "description": "Most commonly used bookmakers across all regions",
        "bookmakers": [
            "draftkings", "fanduel", "betmgm", "caesars", "betrivers", "pointsbet",
            "williamhill_us", "fanatics", "espnbet", "betonlineag", "bovada", "pinnacle",
            "bet365", "williamhill", "sportsbet", "tab", "bwin"
        ]
    },
    "arbitrage_focused": {
        "name": "Arbitrage Hunting",
        "description": "Books with frequent arbitrage opportunities",
        "bookmakers": [
            "pinnacle", "bookmaker", "draftkings", "fanduel", "betmgm", "bet365",
            "bovada", "betonlineag", "caesars", "betrivers"
        ]
    }
}

class SettingsDatabase:
    """
    Database for storing user settings and preferences
    - Enabled bookmakers (for filtering odds/alerts)
    - Bankroll management settings
    - Alert preferences
    - Display preferences
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

            # User Settings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,

                    -- Bookmaker Filtering
                    enabled_bookmakers TEXT NOT NULL,  -- JSON array of bookmaker keys

                    -- Bankroll Settings
                    total_bankroll REAL DEFAULT 10000.0,
                    unit_size REAL DEFAULT 100.0,
                    risk_level TEXT DEFAULT 'medium',

                    -- Alert Settings
                    min_arb_profit REAL DEFAULT 1.0,
                    steam_move_threshold REAL DEFAULT 5.0,
                    line_movement_threshold REAL DEFAULT 3.0,
                    alert_sound_enabled INTEGER DEFAULT 1,

                    -- Display Settings
                    show_latency INTEGER DEFAULT 1,
                    highlight_pinnacle INTEGER DEFAULT 1,
                    dark_mode INTEGER DEFAULT 1,

                    -- Metadata
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Create default settings for 'default' user if not exists
            cursor.execute("SELECT COUNT(*) FROM user_settings WHERE user_id = 'default'")
            if cursor.fetchone()[0] == 0:
                self._create_default_settings(cursor)

    def _create_default_settings(self, cursor):
        """Create default settings for the default user"""
        # Enable popular US bookmakers by default
        default_bookmakers = [
            'draftkings', 'fanduel', 'betmgm', 'caesars', 'betrivers',
            'pointsbet', 'williamhill_us', 'fanatics', 'espnbet',
            'betonlineag', 'bovada', 'pinnacle'
        ]

        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO user_settings (
                user_id, enabled_bookmakers, total_bankroll, unit_size,
                risk_level, min_arb_profit, steam_move_threshold,
                line_movement_threshold, alert_sound_enabled,
                show_latency, highlight_pinnacle, dark_mode,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'default',
            json.dumps(default_bookmakers),
            10000.0,
            100.0,
            'medium',
            1.0,
            5.0,
            3.0,
            1,
            1,
            1,
            1,
            now,
            now
        ))

    def get_settings(self, user_id: str = 'default') -> Optional[Dict]:
        """Get all settings for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM user_settings WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            if not row:
                return None

            # Convert row to dict and parse JSON fields
            settings = dict(row)
            settings['enabled_bookmakers'] = json.loads(settings['enabled_bookmakers'])

            # Convert integer booleans to actual booleans
            settings['alert_sound_enabled'] = bool(settings['alert_sound_enabled'])
            settings['show_latency'] = bool(settings['show_latency'])
            settings['highlight_pinnacle'] = bool(settings['highlight_pinnacle'])
            settings['dark_mode'] = bool(settings['dark_mode'])

            return settings

    def update_enabled_bookmakers(self, bookmakers: List[str], user_id: str = 'default') -> bool:
        """Update the list of enabled bookmakers"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_settings
                SET enabled_bookmakers = ?, updated_at = ?
                WHERE user_id = ?
            """, (json.dumps(bookmakers), datetime.now().isoformat(), user_id))

            return cursor.rowcount > 0

    def update_bankroll_settings(
        self,
        total_bankroll: float,
        unit_size: float,
        risk_level: str,
        user_id: str = 'default'
    ) -> bool:
        """Update bankroll management settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_settings
                SET total_bankroll = ?, unit_size = ?, risk_level = ?, updated_at = ?
                WHERE user_id = ?
            """, (total_bankroll, unit_size, risk_level, datetime.now().isoformat(), user_id))

            return cursor.rowcount > 0

    def update_alert_settings(
        self,
        min_arb_profit: float,
        steam_move_threshold: float,
        line_movement_threshold: float,
        alert_sound_enabled: bool,
        user_id: str = 'default'
    ) -> bool:
        """Update alert threshold settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_settings
                SET min_arb_profit = ?, steam_move_threshold = ?,
                    line_movement_threshold = ?, alert_sound_enabled = ?, updated_at = ?
                WHERE user_id = ?
            """, (
                min_arb_profit,
                steam_move_threshold,
                line_movement_threshold,
                1 if alert_sound_enabled else 0,
                datetime.now().isoformat(),
                user_id
            ))

            return cursor.rowcount > 0

    def update_display_settings(
        self,
        show_latency: bool,
        highlight_pinnacle: bool,
        dark_mode: bool,
        user_id: str = 'default'
    ) -> bool:
        """Update display preferences"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_settings
                SET show_latency = ?, highlight_pinnacle = ?, dark_mode = ?, updated_at = ?
                WHERE user_id = ?
            """, (
                1 if show_latency else 0,
                1 if highlight_pinnacle else 0,
                1 if dark_mode else 0,
                datetime.now().isoformat(),
                user_id
            ))

            return cursor.rowcount > 0

    def update_all_settings(self, settings: Dict, user_id: str = 'default') -> bool:
        """Update all settings at once"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Prepare bookmakers JSON
            bookmakers_json = json.dumps(settings.get('enabled_bookmakers', []))

            cursor.execute("""
                UPDATE user_settings
                SET enabled_bookmakers = ?,
                    total_bankroll = ?,
                    unit_size = ?,
                    risk_level = ?,
                    min_arb_profit = ?,
                    steam_move_threshold = ?,
                    line_movement_threshold = ?,
                    alert_sound_enabled = ?,
                    show_latency = ?,
                    highlight_pinnacle = ?,
                    dark_mode = ?,
                    updated_at = ?
                WHERE user_id = ?
            """, (
                bookmakers_json,
                settings.get('total_bankroll', 10000.0),
                settings.get('unit_size', 100.0),
                settings.get('risk_level', 'medium'),
                settings.get('min_arb_profit', 1.0),
                settings.get('steam_move_threshold', 5.0),
                settings.get('line_movement_threshold', 3.0),
                1 if settings.get('alert_sound_enabled', True) else 0,
                1 if settings.get('show_latency', True) else 0,
                1 if settings.get('highlight_pinnacle', True) else 0,
                1 if settings.get('dark_mode', True) else 0,
                datetime.now().isoformat(),
                user_id
            ))

            return cursor.rowcount > 0

    def reset_to_defaults(self, user_id: str = 'default') -> bool:
        """Reset user settings to defaults"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
            if user_id == 'default':
                self._create_default_settings(cursor)
            return True

# Global instance
settings_db = SettingsDatabase()
