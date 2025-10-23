"""
Test script to verify database connection and display account information
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from subscription_db import SubscriptionDB, get_db_connection, init_subscription_tables

def test_connection():
    """Test database connection and display information"""
    print("=" * 60)
    print("NBA Sports Betting Platform - Database Connection Test")
    print("=" * 60)
    
    try:
        # Initialize database tables
        print("\n📊 Initializing database tables...")
        init_subscription_tables()
        
        # Test connection
        print("\n🔌 Testing database connection...")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get database info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            print("✅ Database connection successful!")
            print(f"\n📋 Available tables:")
            for table in tables:
                print(f"  - {table[0]}")
            
            # Get user count
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            # Get subscription count
            cursor.execute("SELECT COUNT(*) FROM subscriptions")
            sub_count = cursor.fetchone()[0]
            
            # Get active subscription count
            cursor.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'")
            active_sub_count = cursor.fetchone()[0]
            
            print(f"\n📈 Database Statistics:")
            print(f"  - Total Users: {user_count}")
            print(f"  - Total Subscriptions: {sub_count}")
            print(f"  - Active Subscriptions: {active_sub_count}")
            
            # Get subscription tiers breakdown
            cursor.execute("""
                SELECT tier, COUNT(*) as count 
                FROM subscriptions 
                WHERE status = 'active' 
                GROUP BY tier
            """)
            tiers = cursor.fetchall()
            
            if tiers:
                print(f"\n🎯 Active Subscriptions by Tier:")
                for tier, count in tiers:
                    print(f"  - {tier}: {count}")
            
            # Get recent users (last 5)
            cursor.execute("""
                SELECT email, created_at 
                FROM users 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            recent_users = cursor.fetchall()
            
            if recent_users:
                print(f"\n👥 Recent Users:")
                for email, created_at in recent_users:
                    print(f"  - {email} (joined: {created_at})")
            else:
                print(f"\n👥 No users found in database")
        
        print("\n" + "=" * 60)
        print("✅ Database connection test completed successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error connecting to database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_connection()
