"""
Subscription Database Module
Handles all database operations for user subscriptions
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from pathlib import Path


# Use absolute path relative to this file
BASE_DIR = Path(__file__).parent
DATABASE_PATH = str(BASE_DIR / "database" / "subscriptions.db")


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_subscription_tables():
    """Initialize subscription-related database tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Users table (extended with subscription info)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                stripe_customer_id TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                stripe_subscription_id TEXT UNIQUE,
                stripe_customer_id TEXT NOT NULL,
                tier TEXT NOT NULL DEFAULT 'free',
                status TEXT NOT NULL DEFAULT 'active',
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                cancel_at_period_end BOOLEAN DEFAULT 0,
                trial_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Subscription history table (audit trail)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscription_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                subscription_id INTEGER,
                event_type TEXT NOT NULL,
                tier TEXT,
                status TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
            )
        ''')
        
        # Payment history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                stripe_invoice_id TEXT UNIQUE,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'usd',
                status TEXT NOT NULL,
                paid_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_stripe_customer ON users(stripe_customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subs_user ON subscriptions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subs_stripe ON subscriptions(stripe_subscription_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_user ON subscription_history(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payments_user ON payment_history(user_id)')
        
        print("[OK] Subscription database tables initialized")


class SubscriptionDB:
    """Database operations for subscriptions"""
    
    @staticmethod
    def create_or_update_user(user_id: str, email: str, name: str = None, stripe_customer_id: str = None) -> bool:
        """Create or update user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (id, email, name, stripe_customer_id, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(id) DO UPDATE SET
                        email = excluded.email,
                        name = excluded.name,
                        stripe_customer_id = COALESCE(excluded.stripe_customer_id, stripe_customer_id),
                        updated_at = CURRENT_TIMESTAMP
                ''', (user_id, email, name, stripe_customer_id))
                return True
        except Exception as e:
            print(f"Error creating/updating user: {e}")
            return False
    
    @staticmethod
    def get_user(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                row = cursor.fetchone()
                if row:
                    return {key: row[key] for key in row.keys()}
                return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
                row = cursor.fetchone()
                if row:
                    return {key: row[key] for key in row.keys()}
                return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    @staticmethod
    def create_subscription(
        user_id: str,
        stripe_subscription_id: str,
        stripe_customer_id: str,
        tier: str,
        status: str = 'active',
        current_period_start: datetime = None,
        current_period_end: datetime = None,
        trial_end: datetime = None
    ) -> Optional[int]:
        """Create a new subscription"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO subscriptions (
                        user_id, stripe_subscription_id, stripe_customer_id,
                        tier, status, current_period_start, current_period_end,
                        trial_end, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    user_id, stripe_subscription_id, stripe_customer_id,
                    tier, status, current_period_start, current_period_end, trial_end
                ))
                
                subscription_id = cursor.lastrowid
                
                # Log to history
                SubscriptionDB.log_subscription_event(
                    user_id, subscription_id, 'subscription_created',
                    tier, status
                )
                
                return subscription_id
        except Exception as e:
            print(f"Error creating subscription: {e}")
            return None
    
    @staticmethod
    def update_subscription(
        stripe_subscription_id: str,
        tier: str = None,
        status: str = None,
        current_period_start: datetime = None,
        current_period_end: datetime = None,
        cancel_at_period_end: bool = None
    ) -> bool:
        """Update existing subscription"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Build update query dynamically
                updates = []
                params = []
                
                if tier is not None:
                    updates.append('tier = ?')
                    params.append(tier)
                if status is not None:
                    updates.append('status = ?')
                    params.append(status)
                if current_period_start is not None:
                    updates.append('current_period_start = ?')
                    params.append(current_period_start)
                if current_period_end is not None:
                    updates.append('current_period_end = ?')
                    params.append(current_period_end)
                if cancel_at_period_end is not None:
                    updates.append('cancel_at_period_end = ?')
                    params.append(1 if cancel_at_period_end else 0)
                
                if not updates:
                    return True
                
                updates.append('updated_at = CURRENT_TIMESTAMP')
                params.append(stripe_subscription_id)
                
                query = f"UPDATE subscriptions SET {', '.join(updates)} WHERE stripe_subscription_id = ?"
                cursor.execute(query, params)
                
                # Get subscription for logging
                cursor.execute('''
                    SELECT id, user_id FROM subscriptions 
                    WHERE stripe_subscription_id = ?
                ''', (stripe_subscription_id,))
                row = cursor.fetchone()
                
                if row:
                    SubscriptionDB.log_subscription_event(
                        row['user_id'], row['id'], 'subscription_updated',
                        tier, status
                    )
                
                return True
        except Exception as e:
            print(f"Error updating subscription: {e}")
            return False
    
    @staticmethod
    def get_subscription(user_id: str) -> Optional[Dict[str, Any]]:
        """Get active subscription for user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM subscriptions
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (user_id,))
                row = cursor.fetchone()
                if row:
                    return {key: row[key] for key in row.keys()}
                return None
        except Exception as e:
            print(f"Error getting subscription: {e}")
            return None
    
    @staticmethod
    def get_subscription_by_stripe_id(stripe_subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription by Stripe subscription ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM subscriptions
                    WHERE stripe_subscription_id = ?
                ''', (stripe_subscription_id,))
                row = cursor.fetchone()
                if row:
                    return {key: row[key] for key in row.keys()}
                return None
        except Exception as e:
            print(f"Error getting subscription by Stripe ID: {e}")
            return None
    
    @staticmethod
    def cancel_subscription(stripe_subscription_id: str) -> bool:
        """Mark subscription as cancelled"""
        return SubscriptionDB.update_subscription(
            stripe_subscription_id,
            status='canceled',
            tier='free'
        )
    
    @staticmethod
    def log_subscription_event(
        user_id: str,
        subscription_id: int,
        event_type: str,
        tier: str = None,
        status: str = None,
        metadata: str = None
    ) -> bool:
        """Log subscription event to history"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO subscription_history (
                        user_id, subscription_id, event_type, tier, status, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, subscription_id, event_type, tier, status, metadata))
                return True
        except Exception as e:
            print(f"Error logging subscription event: {e}")
            return False
    
    @staticmethod
    def add_payment(
        user_id: str,
        stripe_invoice_id: str,
        amount: float,
        currency: str,
        status: str,
        paid_at: datetime = None
    ) -> bool:
        """Record a payment"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO payment_history (
                        user_id, stripe_invoice_id, amount, currency, status, paid_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, stripe_invoice_id, amount, currency, status, paid_at))
                return True
        except Exception as e:
            print(f"Error adding payment: {e}")
            return False
    
    @staticmethod
    def get_user_payments(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get payment history for user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM payment_history
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (user_id, limit))
                rows = cursor.fetchall()
                return [{key: row[key] for key in row.keys()} for row in rows]
        except Exception as e:
            print(f"Error getting user payments: {e}")
            return []
    
    @staticmethod
    def get_subscription_tier(user_id: str) -> str:
        """Get current subscription tier for user"""
        subscription = SubscriptionDB.get_subscription(user_id)
        if not subscription:
            return 'free'
        
        # Check if subscription is active
        if subscription['status'] != 'active':
            return 'free'
        
        # Check if subscription has expired
        if subscription['current_period_end']:
            period_end = datetime.fromisoformat(subscription['current_period_end'])
            if period_end < datetime.now():
                return 'free'
        
        return subscription['tier']
    
    @staticmethod
    def has_feature_access(user_id: str, feature: str) -> bool:
        """Check if user has access to a specific feature"""
        tier = SubscriptionDB.get_subscription_tier(user_id)

        # Feature access matrix - each tier inherits from previous tiers
        features = {
            'trial': ['live_games_limited', 'basic_odds', 'basic_tracker'],
            'starter': [
                'live_games_limited', 'basic_odds', 'basic_tracker',
                'all_major_sports', 'email_notifications', 'ev_calculator',
                'no_vig_calculator', 'basic_line_tracker', 'advanced_tracker_100',
                'export_csv'
            ],
            'semipro': [
                'live_games_limited', 'basic_odds', 'basic_tracker',
                'all_major_sports', 'email_notifications', 'ev_calculator',
                'no_vig_calculator', 'basic_line_tracker', 'advanced_tracker_100',
                'export_csv',
                'advanced_analytics_dashboard', 'advanced_line_tracker',
                'steam_moves', 'market_consensus', 'arbitrage', 'middles',
                'advanced_tracker_unlimited', 'clv_tracker', 'roi_dashboard',
                'international_markets', 'sms_notifications', 'position_sizing'
            ],
            'professional': [
                'live_games_limited', 'basic_odds', 'basic_tracker',
                'all_major_sports', 'email_notifications', 'ev_calculator',
                'no_vig_calculator', 'basic_line_tracker', 'advanced_tracker_100',
                'export_csv',
                'advanced_analytics_dashboard', 'advanced_line_tracker',
                'steam_moves', 'market_consensus', 'arbitrage', 'middles',
                'advanced_tracker_unlimited', 'clv_tracker', 'roi_dashboard',
                'international_markets', 'sms_notifications', 'position_sizing',
                'browser_extension', 'player_props', 'sgp_builder',
                'prizepicks_comparison', 'ml_projections', 'weather_analysis',
                'injury_alerts', 'kelly_criterion', 'hedge_calculator',
                'clv_predictor', 'priority_support', 'custom_alerts',
                'multi_account_tracking'
            ],
            'elite': [
                'live_games_limited', 'basic_odds', 'basic_tracker',
                'all_major_sports', 'email_notifications', 'ev_calculator',
                'no_vig_calculator', 'basic_line_tracker', 'advanced_tracker_100',
                'export_csv',
                'advanced_analytics_dashboard', 'advanced_line_tracker',
                'steam_moves', 'market_consensus', 'arbitrage', 'middles',
                'advanced_tracker_unlimited', 'clv_tracker', 'roi_dashboard',
                'international_markets', 'sms_notifications', 'position_sizing',
                'browser_extension', 'player_props', 'sgp_builder',
                'prizepicks_comparison', 'ml_projections', 'weather_analysis',
                'injury_alerts', 'kelly_criterion', 'hedge_calculator',
                'clv_predictor', 'priority_support', 'custom_alerts',
                'multi_account_tracking',
                'desktop_client', 'api_access_unlimited', 'custom_models',
                'account_manager', 'custom_integrations', 'backtesting',
                'ml_models', 'automated_betting', 'custom_data_feeds',
                'white_glove_onboarding', 'priority_features', 'sla_guarantee',
                'custom_dashboards', 'offshore_books', 'private_channel'
            ],
            'elitepro': [
                'live_games_limited', 'basic_odds', 'basic_tracker',
                'all_major_sports', 'email_notifications', 'ev_calculator',
                'no_vig_calculator', 'basic_line_tracker', 'advanced_tracker_100',
                'export_csv',
                'advanced_analytics_dashboard', 'advanced_line_tracker',
                'steam_moves', 'market_consensus', 'arbitrage', 'middles',
                'advanced_tracker_unlimited', 'clv_tracker', 'roi_dashboard',
                'international_markets', 'sms_notifications', 'position_sizing',
                'browser_extension', 'player_props', 'sgp_builder',
                'prizepicks_comparison', 'ml_projections', 'weather_analysis',
                'injury_alerts', 'kelly_criterion', 'hedge_calculator',
                'clv_predictor', 'priority_support', 'custom_alerts',
                'multi_account_tracking',
                'desktop_client', 'api_access_unlimited', 'custom_models',
                'account_manager', 'custom_integrations', 'backtesting',
                'ml_models', 'automated_betting', 'custom_data_feeds',
                'white_glove_onboarding', 'priority_features', 'sla_guarantee',
                'custom_dashboards', 'offshore_books', 'private_channel',
                'enhanced_desktop_client', 'offshore_servers', 'direct_sportsbook_api',
                'fastest_ai', 'realtime_ml', 'distributed_servers',
                'sub_50ms_detection', 'dedicated_gpu', 'sharp_alerts',
                'syndicate_feeds', 'trading_desk', 'custom_algorithms',
                'institutional_infra', 'reserved_capacity', 'circa_vip_invite'
            ]
        }

        return feature in features.get(tier, [])


# Initialize database on module import
init_subscription_tables()
