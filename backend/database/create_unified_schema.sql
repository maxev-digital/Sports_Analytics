-- ==========================================
-- MAX EV SPORTS - UNIFIED DATABASE SCHEMA
-- ==========================================
-- Consolidates: users.json, sessions.json, activity_log.json,
--               user_settings.db, subscriptions.db, user_bets.db
-- Created: December 4, 2025
-- Database: maxev_sports.db
-- ==========================================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- ==========================================
-- USERS TABLE (replaces users.json)
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'user',
    stripe_customer_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    email_verified INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    trial_start TIMESTAMP,
    trial_days INTEGER,
    referral_code TEXT,
    has_referral_discount INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer ON users(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- ==========================================
-- SESSIONS TABLE (replaces sessions.json)
-- ==========================================
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP,
    activity_count INTEGER DEFAULT 0,
    user_agent TEXT,
    ip_address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

-- ==========================================
-- USER ACTIVITY LOG (replaces user_activity_log.json)
-- ==========================================
CREATE TABLE IF NOT EXISTS user_activity (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_action ON user_activity(action);
CREATE INDEX IF NOT EXISTS idx_activity_created ON user_activity(created_at);

-- ==========================================
-- SUBSCRIPTIONS (from subscriptions.db)
-- ==========================================
CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stripe_subscription_id TEXT UNIQUE,
    tier TEXT NOT NULL DEFAULT 'free',
    status TEXT NOT NULL DEFAULT 'active',
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end INTEGER DEFAULT 0,
    trial_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_subs_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subs_stripe ON subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_subs_status ON subscriptions(status);

-- ==========================================
-- SUBSCRIPTION HISTORY (from subscriptions.db)
-- ==========================================
CREATE TABLE IF NOT EXISTS subscription_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subscription_id INTEGER,
    event_type TEXT NOT NULL,
    tier TEXT,
    status TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id)
);

CREATE INDEX IF NOT EXISTS idx_history_user ON subscription_history(user_id);
CREATE INDEX IF NOT EXISTS idx_history_created ON subscription_history(created_at);

-- ==========================================
-- PAYMENT HISTORY (from subscriptions.db)
-- ==========================================
CREATE TABLE IF NOT EXISTS payment_history (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stripe_invoice_id TEXT UNIQUE,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'usd',
    status TEXT NOT NULL,
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_payments_user ON payment_history(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payment_history(stripe_invoice_id);

-- ==========================================
-- USER SETTINGS (from user_settings.db)
-- ==========================================
CREATE TABLE IF NOT EXISTS user_settings (
    settings_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    enabled_bookmakers TEXT NOT NULL DEFAULT '["draftkings", "fanduel", "pinnacle"]',
    total_bankroll REAL DEFAULT 10000.0,
    unit_size REAL DEFAULT 100.0,
    risk_level TEXT DEFAULT 'medium',
    min_arb_profit REAL DEFAULT 1.0,
    steam_move_threshold REAL DEFAULT 5.0,
    line_movement_threshold REAL DEFAULT 3.0,
    alert_sound_enabled INTEGER DEFAULT 1,
    show_latency INTEGER DEFAULT 1,
    highlight_pinnacle INTEGER DEFAULT 1,
    dark_mode INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_settings_user ON user_settings(user_id);

-- ==========================================
-- USER BETS (from user_bets.db)
-- ==========================================
CREATE TABLE IF NOT EXISTS user_bets (
    bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    bet_uuid TEXT UNIQUE NOT NULL,
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
    clicked_at TIMESTAMP NOT NULL,
    logged_at TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'pending',
    result TEXT,
    payout REAL,
    profit_loss REAL,
    settled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bets_user ON user_bets(user_id);
CREATE INDEX IF NOT EXISTS idx_bets_uuid ON user_bets(bet_uuid);
CREATE INDEX IF NOT EXISTS idx_bets_status ON user_bets(status);
CREATE INDEX IF NOT EXISTS idx_bets_sport ON user_bets(sport);
CREATE INDEX IF NOT EXISTS idx_bets_game ON user_bets(game_id);

-- ==========================================
-- REFERRALS (from influencer_system)
-- ==========================================
CREATE TABLE IF NOT EXISTS referrals (
    referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
    influencer_user_id INTEGER NOT NULL,
    referred_user_id INTEGER NOT NULL,
    referral_code TEXT NOT NULL,
    subscription_tier TEXT,
    referral_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (influencer_user_id) REFERENCES users(user_id),
    FOREIGN KEY (referred_user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_referrals_influencer ON referrals(influencer_user_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred ON referrals(referred_user_id);
CREATE INDEX IF NOT EXISTS idx_referrals_code ON referrals(referral_code);
