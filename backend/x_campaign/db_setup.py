"""
Database setup for X Campaign
Creates SQLite database for tracking partners, DM status, and campaign metrics
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'referrals.db'

def setup_database():
    """Create all required tables for campaign tracking"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Partners table - tracks influencer status and engagement
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS partners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        handle TEXT UNIQUE NOT NULL,
        code TEXT UNIQUE,
        tier TEXT DEFAULT 'beta',
        status TEXT DEFAULT 'pending',

        -- DM tracking
        dm_sent INTEGER DEFAULT 0,
        dm_sent_date TEXT,
        dm_id TEXT,

        -- Reply tracking
        replied INTEGER DEFAULT 0,
        reply_date TEXT,
        reply_text TEXT,

        -- Onboarding tracking
        onboarded INTEGER DEFAULT 0,
        onboard_date TEXT,

        -- Influencer metrics
        followers INTEGER,
        engagement_rate REAL,
        niche TEXT,
        why_target TEXT,

        -- Timestamps
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # DM Log table - detailed log of every DM sent
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dm_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partner_id INTEGER,
        dm_id TEXT,
        message_text TEXT,
        sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'sent',
        error TEXT,
        FOREIGN KEY (partner_id) REFERENCES partners(id)
    )
    ''')

    # Referrals table - tracks signups from each partner
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partner_id INTEGER,
        referral_code TEXT,
        referred_username TEXT,
        signup_date TEXT DEFAULT CURRENT_TIMESTAMP,
        subscription_tier TEXT,
        monthly_revenue REAL,
        commission_earned REAL,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (partner_id) REFERENCES partners(id)
    )
    ''')

    # Campaign Stats table - daily performance metrics
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS campaign_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE,
        dms_sent INTEGER DEFAULT 0,
        replies_received INTEGER DEFAULT 0,
        partners_onboarded INTEGER DEFAULT 0,
        referrals_generated INTEGER DEFAULT 0,
        revenue_generated REAL DEFAULT 0,
        commission_paid REAL DEFAULT 0,
        response_rate REAL,
        conversion_rate REAL
    )
    ''')

    # Create indexes for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_partner_handle ON partners(handle)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_partner_code ON partners(code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_partner_status ON partners(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_dm_log_partner ON dm_log(partner_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_referrals_partner ON referrals(partner_id)')

    conn.commit()
    conn.close()

    print(f"[OK] Database created successfully: {DB_PATH}")
    print("Tables created:")
    print("  - partners - Influencer tracking")
    print("  - dm_log - DM history")
    print("  - referrals - Signup tracking")
    print("  - campaign_stats - Daily metrics")

def add_partner(handle, followers, niche, why_target, engagement_rate=None):
    """Add a new partner to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO partners (handle, followers, niche, why_target, engagement_rate)
        VALUES (?, ?, ?, ?, ?)
        ''', (handle, followers, niche, why_target, engagement_rate))

        conn.commit()
        partner_id = cursor.lastrowid
        print(f"[OK] Added partner: @{handle} (ID: {partner_id})")
        return partner_id
    except sqlite3.IntegrityError:
        print(f"[WARN] Partner @{handle} already exists")
        return None
    finally:
        conn.close()

def get_pending_partners(limit=50):
    """Get partners who haven't been DMed yet"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT id, handle, followers, niche, why_target
    FROM partners
    WHERE dm_sent = 0
    ORDER BY followers DESC
    LIMIT ?
    ''', (limit,))

    partners = cursor.fetchall()
    conn.close()

    return partners

def mark_dm_sent(partner_id, dm_id=None):
    """Mark that a DM was sent to a partner"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()
    cursor.execute('''
    UPDATE partners
    SET dm_sent = 1, dm_sent_date = ?, dm_id = ?, updated_at = ?
    WHERE id = ?
    ''', (now, dm_id, now, partner_id))

    conn.commit()
    conn.close()

def mark_reply_received(partner_id, reply_text):
    """Mark that a partner replied"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()
    cursor.execute('''
    UPDATE partners
    SET replied = 1, reply_date = ?, reply_text = ?, updated_at = ?
    WHERE id = ?
    ''', (now, reply_text, now, partner_id))

    conn.commit()
    conn.close()

def mark_onboarded(partner_id, referral_code):
    """Mark that a partner has been onboarded"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()
    cursor.execute('''
    UPDATE partners
    SET onboarded = 1, onboard_date = ?, code = ?, status = 'active', updated_at = ?
    WHERE id = ?
    ''', (now, referral_code, now, partner_id))

    conn.commit()
    conn.close()

def get_campaign_stats():
    """Get overall campaign statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT
        COUNT(*) as total_partners,
        SUM(dm_sent) as dms_sent,
        SUM(replied) as replies_received,
        SUM(onboarded) as partners_onboarded,
        ROUND(CAST(SUM(replied) AS FLOAT) / NULLIF(SUM(dm_sent), 0) * 100, 2) as response_rate,
        ROUND(CAST(SUM(onboarded) AS FLOAT) / NULLIF(SUM(replied), 0) * 100, 2) as conversion_rate
    FROM partners
    ''')

    stats = cursor.fetchone()
    conn.close()

    return {
        'total_partners': stats[0],
        'dms_sent': stats[1] or 0,
        'replies_received': stats[2] or 0,
        'partners_onboarded': stats[3] or 0,
        'response_rate': stats[4] or 0,
        'conversion_rate': stats[5] or 0
    }

def print_stats():
    """Print campaign statistics"""
    stats = get_campaign_stats()

    print("\n[STATS] Campaign Statistics")
    print("=" * 50)
    print(f"Total Partners in DB: {stats['total_partners']}")
    print(f"DMs Sent: {stats['dms_sent']}")
    print(f"Replies Received: {stats['replies_received']}")
    print(f"Partners Onboarded: {stats['partners_onboarded']}")
    print(f"Response Rate: {stats['response_rate']}%")
    print(f"Conversion Rate: {stats['conversion_rate']}%")

if __name__ == "__main__":
    print("X Campaign Database Setup")
    print("=" * 50)
    setup_database()
    print()

    # Add a test partner
    print("\nAdding test partner...")
    add_partner(
        handle="testinfluencer",
        followers=50000,
        niche="sports_betting",
        why_target="High engagement on NBA content, verified account",
        engagement_rate=4.5
    )

    print()
    print_stats()
