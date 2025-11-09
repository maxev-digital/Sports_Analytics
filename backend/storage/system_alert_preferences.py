"""
System Alert Preferences Storage
Manages which advanced systems users want to receive alerts for
"""
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Set
from contextlib import contextmanager
import json

# Use absolute path
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_settings.db")


class SystemAlertPreferences:
    """
    Manages user preferences for which advanced systems trigger alerts
    """

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_tables()

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

    def init_tables(self):
        """Initialize system alert preferences table"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # System Alert Preferences Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_alert_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    system_id INTEGER NOT NULL,

                    -- Alert Settings
                    alerts_enabled INTEGER DEFAULT 1,
                    notification_method TEXT DEFAULT 'in_app',  -- 'in_app', 'email', 'sms', 'all'
                    min_strength_threshold REAL DEFAULT 50.0,   -- Minimum strength to trigger alert

                    -- Metadata
                    enabled_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,

                    UNIQUE(user_id, system_id)
                )
            """)

            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_system
                ON system_alert_preferences(user_id, system_id)
            """)

    def enable_system_alerts(
        self,
        user_id: str,
        system_id: int,
        notification_method: str = 'in_app',
        min_strength: float = 50.0
    ) -> bool:
        """
        Enable alerts for a specific system

        Args:
            user_id: User identifier
            system_id: ID of the advanced system
            notification_method: 'in_app', 'email', 'sms', or 'all'
            min_strength: Minimum strength threshold (0-100)

        Returns:
            True if successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO system_alert_preferences
                (user_id, system_id, alerts_enabled, notification_method, min_strength_threshold, enabled_at, updated_at)
                VALUES (?, ?, 1, ?, ?, ?, ?)
                ON CONFLICT(user_id, system_id) DO UPDATE SET
                    alerts_enabled = 1,
                    notification_method = excluded.notification_method,
                    min_strength_threshold = excluded.min_strength_threshold,
                    updated_at = excluded.updated_at
            """, (user_id, system_id, notification_method, min_strength, now, now))

            return cursor.rowcount > 0

    def disable_system_alerts(self, user_id: str, system_id: int) -> bool:
        """Disable alerts for a specific system"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE system_alert_preferences
                SET alerts_enabled = 0, updated_at = ?
                WHERE user_id = ? AND system_id = ?
            """, (datetime.now().isoformat(), user_id, system_id))

            return cursor.rowcount > 0

    def toggle_system_alerts(self, user_id: str, system_id: int) -> tuple[bool, bool]:
        """
        Toggle alerts for a system

        Returns:
            (success, new_state) where new_state is True if now enabled
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check current state
            cursor.execute("""
                SELECT alerts_enabled FROM system_alert_preferences
                WHERE user_id = ? AND system_id = ?
            """, (user_id, system_id))

            row = cursor.fetchone()

            if row is None:
                # System not in preferences yet, enable it
                return self.enable_system_alerts(user_id, system_id), True
            else:
                # Toggle current state
                new_state = not bool(row['alerts_enabled'])
                cursor.execute("""
                    UPDATE system_alert_preferences
                    SET alerts_enabled = ?, updated_at = ?
                    WHERE user_id = ? AND system_id = ?
                """, (1 if new_state else 0, datetime.now().isoformat(), user_id, system_id))

                return cursor.rowcount > 0, new_state

    def get_enabled_systems(self, user_id: str) -> List[int]:
        """Get list of system IDs that have alerts enabled for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT system_id FROM system_alert_preferences
                WHERE user_id = ? AND alerts_enabled = 1
                ORDER BY system_id
            """, (user_id,))

            return [row['system_id'] for row in cursor.fetchall()]

    def get_system_preferences(self, user_id: str, system_id: int) -> Optional[Dict]:
        """Get preferences for a specific system"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM system_alert_preferences
                WHERE user_id = ? AND system_id = ?
            """, (user_id, system_id))

            row = cursor.fetchone()
            if not row:
                return None

            return {
                'system_id': row['system_id'],
                'alerts_enabled': bool(row['alerts_enabled']),
                'notification_method': row['notification_method'],
                'min_strength_threshold': row['min_strength_threshold'],
                'enabled_at': row['enabled_at'],
                'updated_at': row['updated_at']
            }

    def get_all_preferences(self, user_id: str) -> Dict[int, Dict]:
        """Get all system preferences for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM system_alert_preferences
                WHERE user_id = ?
                ORDER BY system_id
            """, (user_id,))

            preferences = {}
            for row in cursor.fetchall():
                system_id = row['system_id']
                preferences[system_id] = {
                    'alerts_enabled': bool(row['alerts_enabled']),
                    'notification_method': row['notification_method'],
                    'min_strength_threshold': row['min_strength_threshold'],
                    'enabled_at': row['enabled_at'],
                    'updated_at': row['updated_at']
                }

            return preferences

    def update_notification_method(
        self,
        user_id: str,
        system_id: int,
        method: str
    ) -> bool:
        """Update notification method for a system"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE system_alert_preferences
                SET notification_method = ?, updated_at = ?
                WHERE user_id = ? AND system_id = ?
            """, (method, datetime.now().isoformat(), user_id, system_id))

            return cursor.rowcount > 0

    def update_min_strength(
        self,
        user_id: str,
        system_id: int,
        min_strength: float
    ) -> bool:
        """Update minimum strength threshold for alerts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE system_alert_preferences
                SET min_strength_threshold = ?, updated_at = ?
                WHERE user_id = ? AND system_id = ?
            """, (min_strength, datetime.now().isoformat(), user_id, system_id))

            return cursor.rowcount > 0

    def should_send_alert(
        self,
        user_id: str,
        system_id: int,
        strength: float
    ) -> tuple[bool, Optional[str]]:
        """
        Check if an alert should be sent for this system

        Returns:
            (should_send, notification_method)
        """
        prefs = self.get_system_preferences(user_id, system_id)

        if not prefs or not prefs['alerts_enabled']:
            return False, None

        if strength < prefs['min_strength_threshold']:
            return False, None

        return True, prefs['notification_method']


# Global instance
system_alert_prefs = SystemAlertPreferences()
