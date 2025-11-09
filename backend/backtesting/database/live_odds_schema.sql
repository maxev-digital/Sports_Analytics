-- ============================================================================
-- LIVE ODDS COLLECTION DATABASE SCHEMA
-- For capturing in-game betting lines to enable regression analysis
-- ============================================================================

-- Main live odds table - captures all in-game lines
CREATE TABLE IF NOT EXISTS live_odds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Game identification
    game_id TEXT NOT NULL,
    sport TEXT NOT NULL,  -- 'basketball_nba', 'basketball_ncaab', etc.
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    game_date DATE NOT NULL,

    -- Timing information
    capture_timestamp TIMESTAMP NOT NULL,  -- When we captured this line
    game_status TEXT NOT NULL,  -- 'pregame', 'Q1', 'Q2', 'halftime', 'Q3', 'Q4', 'OT', 'final'
    clock_remaining TEXT,  -- e.g., "8:35" for 8:35 remaining in quarter
    period INTEGER,  -- 1, 2, 3, 4, 5 (OT)

    -- Current score
    home_score INTEGER,
    away_score INTEGER,

    -- Bookmaker info
    bookmaker TEXT NOT NULL,

    -- Odds data
    market_type TEXT NOT NULL,  -- 'totals', 'spreads', 'moneyline'
    line_value REAL,  -- Total line or spread value
    over_odds INTEGER,  -- e.g., -110
    under_odds INTEGER,  -- e.g., -110

    -- Metadata
    odds_movement TEXT,  -- 'up', 'down', 'stable'
    line_quality TEXT,  -- 'sharp', 'soft', 'consensus'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for fast queries
    UNIQUE(game_id, bookmaker, capture_timestamp, market_type, line_value)
);

CREATE INDEX IF NOT EXISTS idx_live_odds_game ON live_odds(game_id, game_status);
CREATE INDEX IF NOT EXISTS idx_live_odds_timestamp ON live_odds(capture_timestamp);
CREATE INDEX IF NOT EXISTS idx_live_odds_sport_date ON live_odds(sport, game_date);


-- Game state snapshots - captures complete game state at key moments
CREATE TABLE IF NOT EXISTS game_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Game identification
    game_id TEXT NOT NULL,
    sport TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    game_date DATE NOT NULL,

    -- Snapshot timing
    snapshot_timestamp TIMESTAMP NOT NULL,
    snapshot_type TEXT NOT NULL,  -- 'end_q1', 'halftime', 'end_q3', 'final'

    -- Score breakdown
    home_q1 INTEGER,
    home_q2 INTEGER,
    home_q3 INTEGER,
    home_q4 INTEGER,
    home_ot INTEGER,
    away_q1 INTEGER,
    away_q2 INTEGER,
    away_q3 INTEGER,
    away_q4 INTEGER,
    away_ot INTEGER,
    home_score INTEGER NOT NULL,
    away_score INTEGER NOT NULL,

    -- Consensus closing lines (from pregame)
    pregame_total REAL,
    pregame_spread REAL,

    -- Consensus live lines at this moment
    live_total REAL,  -- Consensus across bookmakers
    live_spread REAL,

    -- Calculated fields
    implied_final_total REAL,  -- Projected final based on pace
    deviation_from_pregame REAL,  -- Current pace vs pregame expectation

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(game_id, snapshot_type)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_game ON game_snapshots(game_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_sport_date ON game_snapshots(sport, game_date);


-- Betting opportunities - identified regression scenarios
CREATE TABLE IF NOT EXISTS regression_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Game identification
    game_id TEXT NOT NULL,
    sport TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    game_date DATE NOT NULL,

    -- Opportunity timing
    identified_at TIMESTAMP NOT NULL,
    game_status TEXT NOT NULL,  -- When we identified it

    -- Market conditions
    pregame_total REAL NOT NULL,
    live_total REAL NOT NULL,
    deviation REAL NOT NULL,  -- live_total - pregame_total
    deviation_sigma REAL NOT NULL,  -- deviation / std_deviation

    -- Bet recommendation
    bet_side TEXT NOT NULL,  -- 'over', 'under'
    confidence TEXT NOT NULL,  -- 'high', 'medium', 'low'
    expected_value REAL,  -- Estimated +EV

    -- Current game state
    current_score_home INTEGER,
    current_score_away INTEGER,
    current_total INTEGER,

    -- Best available odds
    best_bookmaker TEXT,
    best_line_value REAL,
    best_odds INTEGER,

    -- Outcome tracking
    bet_placed BOOLEAN DEFAULT 0,
    final_total INTEGER,
    result TEXT,  -- 'win', 'loss', 'push', 'pending'
    profit_loss REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_opportunities_game ON regression_opportunities(game_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_date ON regression_opportunities(game_date);
CREATE INDEX IF NOT EXISTS idx_opportunities_result ON regression_opportunities(result);


-- Odds movement tracking - for identifying sharp action
CREATE TABLE IF NOT EXISTS odds_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    game_id TEXT NOT NULL,
    bookmaker TEXT NOT NULL,
    market_type TEXT NOT NULL,

    -- Movement details
    old_line REAL NOT NULL,
    new_line REAL NOT NULL,
    movement_size REAL NOT NULL,
    movement_direction TEXT NOT NULL,  -- 'up', 'down'

    detected_at TIMESTAMP NOT NULL,
    game_status TEXT,

    -- Context
    public_bet_percentage INTEGER,  -- If available
    sharp_indicator BOOLEAN DEFAULT 0,  -- Reverse line movement

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_movements_game ON odds_movements(game_id, detected_at);


-- Performance tracking - strategy results
CREATE TABLE IF NOT EXISTS regression_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Time period
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    sport TEXT NOT NULL,

    -- Volume
    total_opportunities INTEGER NOT NULL,
    bets_placed INTEGER NOT NULL,

    -- Results
    wins INTEGER NOT NULL,
    losses INTEGER NOT NULL,
    pushes INTEGER NOT NULL,
    win_rate REAL NOT NULL,

    -- Financial
    total_wagered REAL NOT NULL,
    total_profit_loss REAL NOT NULL,
    roi REAL NOT NULL,

    -- By confidence level
    high_confidence_win_rate REAL,
    medium_confidence_win_rate REAL,
    low_confidence_win_rate REAL,

    -- By deviation size
    avg_deviation_wins REAL,
    avg_deviation_losses REAL,

    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================================
-- DATA COLLECTION STRATEGY
-- ============================================================================

/*
LIVE ODDS COLLECTION SCHEDULE:

1. PREGAME (captured in existing odds_history):
   - Closing lines ~30 minutes before tipoff

2. IN-GAME SNAPSHOTS:
   - End of Q1 (capture live totals, spreads)
   - Halftime (critical - highest liquidity)
   - End of Q3 (late-game opportunities)
   - Every 2 minutes during close games (within 5 points)

3. BOOKMAKERS TO TRACK:
   - Primary: FanDuel, DraftKings, BetMGM (highest limits)
   - Secondary: Caesars, Bet365, PointsBet (line comparison)

4. DATA POINTS PER SNAPSHOT:
   - Current score
   - Live total (all bookmakers)
   - Time remaining
   - Pace metrics (possessions/minute)

5. STORAGE EFFICIENCY:
   - Only store when lines move (not every capture)
   - Aggregate to consensus for snapshots
   - Archive old data after season

ESTIMATED STORAGE:
- ~10 NBA games per day x 180 days = 1,800 games
- ~5 bookmakers x 4 snapshots x 2 markets = 40 records per game
- 1,800 x 40 = 72,000 records per season (~10 MB)
*/
