-- ============================================================================
-- MACHINE LEARNING SPORTS BETTING DATABASE SCHEMA
-- Comprehensive schema for all sports with scikit-learn feature engineering
-- ============================================================================

-- =========================
-- CORE GAME DATA (Enhanced)
-- =========================

-- Already have historical_games, but add indexes and views for ML
CREATE INDEX IF NOT EXISTS idx_games_sport_season ON historical_games(sport, season);
CREATE INDEX IF NOT EXISTS idx_games_date_sport ON historical_games(date, sport);
CREATE INDEX IF NOT EXISTS idx_games_teams ON historical_games(home_team, away_team);


-- =========================
-- TEAM STATISTICS (Time-Series)
-- =========================

CREATE TABLE IF NOT EXISTS team_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name TEXT NOT NULL,
    sport TEXT NOT NULL,
    season INTEGER NOT NULL,
    date DATE NOT NULL,  -- Stats up to this date (rolling)

    -- Offense
    points_per_game REAL,
    offensive_rating REAL,  -- Points per 100 possessions
    pace REAL,  -- Possessions per game
    field_goal_pct REAL,
    three_point_pct REAL,
    free_throw_pct REAL,
    assists_per_game REAL,
    turnovers_per_game REAL,

    -- Defense
    points_allowed_per_game REAL,
    defensive_rating REAL,  -- Opponent points per 100 possessions
    opponent_fg_pct REAL,
    opponent_three_pct REAL,
    steals_per_game REAL,
    blocks_per_game REAL,

    -- Rebounds
    rebounds_per_game REAL,
    offensive_rebounds_per_game REAL,
    defensive_rebounds_per_game REAL,

    -- Team Context
    wins INTEGER,
    losses INTEGER,
    win_pct REAL,
    home_record TEXT,  -- "10-5" format
    away_record TEXT,
    vs_ranked_record TEXT,  -- For college
    conference TEXT,  -- For college

    -- Rest & Travel
    avg_rest_days REAL,
    back_to_back_games INTEGER,
    games_in_last_7_days INTEGER,

    -- Advanced Metrics
    net_rating REAL,  -- Off Rating - Def Rating
    true_shooting_pct REAL,
    effective_fg_pct REAL,
    assist_to_turnover_ratio REAL,

    -- Trends (Last 5/10 games)
    last_5_record TEXT,
    last_10_record TEXT,
    points_trend_5g REAL,  -- Avg change in scoring
    defense_trend_5g REAL,

    -- ML Features (calculated)
    form_score REAL,  -- Weighted recent performance
    strength_of_schedule REAL,
    pythagorean_wins REAL,  -- Expected wins based on point differential

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_team_stats_lookup ON team_stats(team_name, sport, date);
CREATE INDEX IF NOT EXISTS idx_team_stats_season ON team_stats(sport, season);


-- =========================
-- PLAYER STATISTICS (For Injuries/Lineup Impact)
-- =========================

CREATE TABLE IF NOT EXISTS player_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    team_name TEXT NOT NULL,
    sport TEXT NOT NULL,
    season INTEGER NOT NULL,
    date DATE NOT NULL,

    -- Core Stats
    games_played INTEGER,
    minutes_per_game REAL,
    points_per_game REAL,
    rebounds_per_game REAL,
    assists_per_game REAL,

    -- Shooting
    field_goal_pct REAL,
    three_point_pct REAL,
    free_throw_pct REAL,

    -- Advanced
    player_efficiency_rating REAL,
    true_shooting_pct REAL,
    usage_rate REAL,
    plus_minus REAL,

    -- Injury Status
    injury_status TEXT,  -- 'healthy', 'questionable', 'out', 'injured_reserve'
    games_missed_last_10 INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_player_stats ON player_stats(player_name, team_name, date);
CREATE INDEX IF NOT EXISTS idx_player_team_date ON player_stats(team_name, date);


-- =========================
-- BETTING LINES (Historical + Live)
-- =========================

CREATE TABLE IF NOT EXISTS betting_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    sport TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    -- Line Type
    line_type TEXT NOT NULL,  -- 'opening', 'closing', 'live'
    game_time_remaining TEXT,  -- For live lines: "Q2 8:45"

    -- Bookmaker
    bookmaker TEXT NOT NULL,

    -- Lines
    home_spread REAL,
    home_spread_odds INTEGER,
    away_spread_odds INTEGER,

    total_line REAL,
    over_odds INTEGER,
    under_odds INTEGER,

    home_moneyline INTEGER,
    away_moneyline INTEGER,

    -- Line Movement
    spread_movement REAL,  -- Change since opening
    total_movement REAL,

    -- Market Indicators
    public_bet_percentage_spread INTEGER,  -- % on home spread
    public_bet_percentage_total INTEGER,  -- % on over
    sharp_money_indicator BOOLEAN DEFAULT 0,  -- Reverse line movement

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_betting_lines_game ON betting_lines(game_id, line_type);
CREATE INDEX IF NOT EXISTS idx_betting_lines_timestamp ON betting_lines(timestamp);


-- =========================
-- BETTING MARKET CONSENSUS
-- =========================

CREATE TABLE IF NOT EXISTS market_consensus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    -- Consensus Lines (Average across books)
    consensus_spread REAL,
    consensus_total REAL,

    -- Spread Variance
    spread_std_dev REAL,  -- How much books disagree
    spread_range REAL,  -- Max - Min

    -- Total Variance
    total_std_dev REAL,
    total_range REAL,

    -- Steam Moves (Sudden line movements)
    steam_detected BOOLEAN DEFAULT 0,
    steam_direction TEXT,  -- 'spread_home', 'spread_away', 'over', 'under'

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_consensus_game ON market_consensus(game_id, timestamp);


-- =========================
-- ML TRAINING FEATURES (Pre-computed)
-- =========================

CREATE TABLE IF NOT EXISTS ml_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL UNIQUE,
    sport TEXT NOT NULL,
    date DATE NOT NULL,

    -- Teams
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,

    -- ==================
    -- TEAM FEATURES
    -- ==================

    -- Team Ratings (at game time)
    home_off_rating REAL,
    home_def_rating REAL,
    home_net_rating REAL,
    away_off_rating REAL,
    away_def_rating REAL,
    away_net_rating REAL,

    -- Form
    home_last_5_wins INTEGER,
    home_last_10_wins INTEGER,
    away_last_5_wins INTEGER,
    away_last_10_wins INTEGER,

    -- Rest
    home_rest_days INTEGER,
    away_rest_days INTEGER,
    home_is_back_to_back BOOLEAN,
    away_is_back_to_back BOOLEAN,

    -- Home/Away Splits
    home_home_record_pct REAL,
    away_away_record_pct REAL,

    -- Head-to-Head
    h2h_games_last_2_years INTEGER,
    h2h_home_wins INTEGER,
    h2h_avg_total REAL,

    -- ==================
    -- PACE & TEMPO
    -- ==================
    home_pace REAL,
    away_pace REAL,
    expected_pace REAL,  -- Geometric mean

    -- ==================
    -- BETTING FEATURES
    -- ==================
    opening_spread REAL,
    closing_spread REAL,
    spread_movement REAL,

    opening_total REAL,
    closing_total REAL,
    total_movement REAL,

    public_on_home_pct REAL,
    public_on_over_pct REAL,

    -- Sharp Action
    reverse_line_movement BOOLEAN,
    steam_move_detected BOOLEAN,

    -- ==================
    -- SITUATIONAL
    -- ==================
    is_rivalry BOOLEAN,
    is_playoff BOOLEAN,
    is_conference_game BOOLEAN,
    days_since_last_game_home INTEGER,
    days_since_last_game_away INTEGER,

    -- ==================
    -- WEATHER (NFL/CFB)
    -- ==================
    temperature REAL,
    wind_speed REAL,
    precipitation BOOLEAN,
    dome BOOLEAN,

    -- ==================
    -- INJURIES
    -- ==================
    home_key_players_out INTEGER,
    away_key_players_out INTEGER,
    home_total_minutes_lost REAL,  -- Minutes from injured players
    away_total_minutes_lost REAL,

    -- ==================
    -- ADVANCED METRICS
    -- ==================
    talent_gap REAL,  -- Home rating - Away rating
    pace_differential REAL,  -- |Home pace - Away pace|
    style_mismatch_score REAL,  -- Fast vs slow team indicator

    -- ==================
    -- ACTUAL RESULTS (for training)
    -- ==================
    actual_home_score INTEGER,
    actual_away_score INTEGER,
    actual_total INTEGER,
    actual_spread REAL,  -- home_score - away_score

    spread_covered TEXT,  -- 'home', 'away', 'push'
    total_result TEXT,  -- 'over', 'under', 'push'

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ml_features_game ON ml_features(game_id);
CREATE INDEX IF NOT EXISTS idx_ml_features_sport_date ON ml_features(sport, date);


-- =========================
-- ML MODEL PREDICTIONS
-- =========================

CREATE TABLE IF NOT EXISTS ml_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    model_name TEXT NOT NULL,  -- 'random_forest_totals', 'xgboost_spread', etc.
    model_version TEXT NOT NULL,

    -- Predictions
    predicted_home_score REAL,
    predicted_away_score REAL,
    predicted_total REAL,
    predicted_spread REAL,

    -- Probabilities
    prob_home_cover REAL,  -- Probability home covers spread
    prob_over REAL,  -- Probability game goes over

    -- Confidence
    confidence_score REAL,  -- 0-1, model's confidence
    prediction_interval_lower REAL,  -- For total
    prediction_interval_upper REAL,

    -- Edge Detection
    edge_vs_market REAL,  -- Predicted vs closing line
    bet_recommendation TEXT,  -- 'home', 'away', 'over', 'under', 'pass'
    kelly_bet_size REAL,  -- Optimal bet size as % of bankroll

    -- Actual Results
    actual_total INTEGER,
    actual_spread REAL,
    prediction_error REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ml_predictions ON ml_predictions(game_id, model_name);
CREATE INDEX IF NOT EXISTS idx_ml_model_performance ON ml_predictions(model_name, created_at);


-- =========================
-- MODEL PERFORMANCE TRACKING
-- =========================

CREATE TABLE IF NOT EXISTS model_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    sport TEXT NOT NULL,

    -- Time Period
    evaluation_date DATE NOT NULL,
    games_evaluated INTEGER NOT NULL,

    -- Accuracy Metrics
    mae REAL,  -- Mean Absolute Error
    rmse REAL,  -- Root Mean Squared Error
    r_squared REAL,

    -- Betting Performance
    roi REAL,
    win_rate REAL,
    profit_loss REAL,
    units_won REAL,

    -- By Market
    spread_accuracy REAL,
    total_accuracy REAL,
    moneyline_accuracy REAL,

    -- By Confidence Level
    high_confidence_win_rate REAL,
    medium_confidence_win_rate REAL,
    low_confidence_win_rate REAL,

    -- Feature Importance (JSON)
    top_features TEXT,  -- JSON array of top 10 features

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_model_performance ON model_performance(model_name, evaluation_date);


-- =========================
-- TRAINING SETS (for reproducibility)
-- =========================

CREATE TABLE IF NOT EXISTS training_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_name TEXT NOT NULL UNIQUE,
    description TEXT,
    sport TEXT NOT NULL,

    -- Date Range
    train_start_date DATE NOT NULL,
    train_end_date DATE NOT NULL,
    test_start_date DATE,
    test_end_date DATE,

    -- Size
    train_games INTEGER,
    test_games INTEGER,

    -- Features Used (JSON array)
    features_list TEXT,

    -- Target Variable
    target_variable TEXT,  -- 'total', 'spread', 'home_score', etc.

    -- Created
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================
-- LIVE ALERTS (for 2025 season)
-- =========================

CREATE TABLE IF NOT EXISTS live_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,  -- 'regression', 'steam_move', 'model_edge', 'injury'

    -- Alert Details
    message TEXT NOT NULL,
    severity TEXT NOT NULL,  -- 'high', 'medium', 'low'

    -- Recommendation
    action TEXT,  -- 'bet_home', 'bet_away', 'bet_over', 'bet_under', 'monitor'
    stake_recommendation REAL,

    -- Sent Status
    sent_discord BOOLEAN DEFAULT 0,
    sent_sms BOOLEAN DEFAULT 0,
    sent_email BOOLEAN DEFAULT 0,

    -- User Response
    user_action_taken TEXT,
    user_bet_placed BOOLEAN DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_game ON live_alerts(game_id, created_at);


-- =========================
-- VIEWS FOR ML (Quick Access)
-- =========================

-- Recent team performance view
CREATE VIEW IF NOT EXISTS vw_recent_team_stats AS
SELECT
    team_name,
    sport,
    AVG(points_per_game) as avg_ppg_last_10,
    AVG(points_allowed_per_game) as avg_papg_last_10,
    AVG(net_rating) as avg_net_rating,
    MAX(date) as last_update
FROM team_stats
WHERE date >= date('now', '-30 days')
GROUP BY team_name, sport;


-- Betting line consensus view
CREATE VIEW IF NOT EXISTS vw_closing_lines AS
SELECT
    game_id,
    AVG(home_spread) as consensus_spread,
    AVG(total_line) as consensus_total,
    COUNT(DISTINCT bookmaker) as num_books
FROM betting_lines
WHERE line_type = 'closing'
GROUP BY game_id;


-- ============================================================================
-- EXAMPLE ML PIPELINE QUERIES
-- ============================================================================

/*
-- 1. Get training data for totals prediction model
SELECT
    f.*,
    g.date,
    g.home_team,
    g.away_team
FROM ml_features f
JOIN historical_games g ON f.game_id = g.game_id
WHERE f.sport = 'NBA'
  AND f.date BETWEEN '2021-10-01' AND '2024-04-30'
  AND f.actual_total IS NOT NULL
ORDER BY f.date;


-- 2. Feature engineering: Calculate team form score
UPDATE team_stats
SET form_score = (
    last_5_wins * 2.0 +  -- Recent games weighted more
    (win_pct * 10) +     -- Overall record
    (net_rating / 10)    -- Point differential
) / 3;


-- 3. Get games with high model edge
SELECT
    p.game_id,
    p.predicted_total,
    c.consensus_total,
    p.edge_vs_market,
    p.bet_recommendation,
    p.confidence_score,
    g.date,
    g.home_team,
    g.away_team
FROM ml_predictions p
JOIN vw_closing_lines c ON p.game_id = c.game_id
JOIN historical_games g ON p.game_id = g.game_id
WHERE p.confidence_score > 0.7
  AND ABS(p.edge_vs_market) > 5.0
  AND p.bet_recommendation != 'pass'
ORDER BY p.confidence_score DESC;

*/
