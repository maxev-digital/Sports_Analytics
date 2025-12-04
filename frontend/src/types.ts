export interface Team {
  name: string;
  score: number | null;
  spread?: number | null;
  spread_price?: number | null;
  money_line?: number | null;
  momentum?: number | null;  // -100 to 100 scale, negative favors opponent
}

export interface GameState {
  id: string;
  sport_key: string;
  home_team: Team;
  away_team: Team;
  commence_time: string;
  status: 'upcoming' | 'live' | 'completed';
  is_live?: boolean;  // For NCAAB baseline comparison
  quarter: number | null;
  time_remaining: string | null;
  tournament?: string | null;  // For tennis: "Australian Open", "Wimbledon", etc.
}

export interface GameOdds {
  bookmaker: string;
  total: number;
  over_price: number;
  under_price: number;
  is_best_over: boolean;
  is_best_under: boolean;
  latency_ms: number | null;
  home_spread?: number | null;
  away_spread?: number | null;
  home_spread_price?: number | null;
  away_spread_price?: number | null;
  home_ml?: number | null;
  away_ml?: number | null;
  opening_total?: number | null;
  total_movement?: number | null;
  opening_spread?: number | null;
  spread_movement?: number | null;
}

export interface GameProjection {
  current_total: number;
  projected_final: number;
  pregame_total: number;
  pregame_spread?: number | null;  // Pregame spread (away team perspective)
  pregame_spread_price?: number | null;  // Pregame spread price
  pregame_moneyline_home?: number | null;  // Pregame moneyline for home team
  pregame_moneyline_away?: number | null;  // Pregame moneyline for away team
  current_live_total: number | null;
  line_movement: number | null;
  best_book_disparity: string | null;
  best_disparity_amount: number | null;
  edge: number | null;
  confidence: 'LOW' | 'MEDIUM' | 'HIGH';
  recommendation: 'OVER' | 'UNDER' | null;
  current_pace?: number | null;
  expected_pace?: number | null;
  pace_differential?: number | null;
  efficiency_factor?: number | null;
  regression_factor?: number | null;
  pace_indicator?: string | null;
  strength_factor?: number | null;
  unit_recommendation?: number | null;
  first_half_total?: number | null;  // Projected first half total
  first_half_current?: number | null;  // Current first half score
}

export interface TeamStats {
  team_id: string;
  team_name: string;
  games_played: number;
  wins: number;
  losses: number;
  win_pct: number;
  off_rating: number;
  def_rating: number;
  net_rating: number;
  pace: number;
  fg_pct: number;
  fg3_pct: number;
  ft_pct: number;
  pts_per_game: number;
  pts_allowed: number;
  last_5_record: string | null;
  last_5_avg_pts: number | null;
  last_5_avg_margin: number | null;
  form_trend: 'HOT' | 'COLD' | 'NEUTRAL' | null;
  // Rankings (1-30 for NBA)
  pts_per_game_rank?: number | null;
  off_rating_rank?: number | null;
  def_rating_rank?: number | null;
  net_rating_rank?: number | null;
  pace_rank?: number | null;
  fg_pct_rank?: number | null;
  fg3_pct_rank?: number | null;
  ft_pct_rank?: number | null;
}

export interface NFLLiveStats {
  first_downs: string | null;
  first_downs_passing: string | null;
  first_downs_rushing: string | null;
  first_downs_penalty: string | null;
  third_down_eff: string | null;
  fourth_down_eff: string | null;
  total_yards: string | null;
  yards_per_play: string | null;
  passing_yards: string | null;
  comp_att: string | null;
  yards_per_pass: string | null;
  interceptions_thrown: string | null;
  sacks_yards_lost: string | null;
  rushing_yards: string | null;
  rushing_attempts: string | null;
  yards_per_rush: string | null;
  red_zone: string | null;
  penalties: string | null;
  turnovers: string | null;
  fumbles_lost: string | null;
  defensive_td: string | null;
  possession: string | null;
  total_plays: string | null;
}

export interface NHLMomentumStats {
  momentum_score: number;  // 0-100 scale (higher = more momentum)
  recent_shots: number;  // Shots in last 5 minutes
  scoring_chances: number;  // High danger shots
  faceoff_wins: number;  // Faceoffs won in recent play
  offensive_zone_events: number;  // Events in offensive zone
  possession_indicator?: string | null;  // "ATTACKING", "DEFENDING", "NEUTRAL"
  power_play_opps?: string | null;  // "2/3" format (scored/total)
  penalty_minutes?: number | null;  // Total penalty minutes
  blocked_shots?: number | null;  // Shots blocked (defensive metric)
}

export interface NBAMomentumStats {
  momentum_score: number;  // 0-100 scale (higher = more momentum)
  points_last_5min: number;  // Points scored in last ~5 minutes
  fg_pct_recent: number;  // Field goal % in recent possessions
  offensive_rebounds: number;  // Offensive rebounds (second chance points)
  turnovers: number;  // Turnovers in recent play
  steals: number;  // Steals forced
  assists: number;  // Assists in recent play
  possession_indicator?: string | null;  // "ATTACKING", "DEFENDING", "NEUTRAL"
}

export interface NFLMomentumStats {
  momentum_score: number;  // 0-100 scale (higher = more momentum)
  yards_per_play: number;  // Average yards per play on recent drives
  recent_yards: number;  // Total yards gained on recent drives
  recent_points: number;  // Points scored on recent drives
  touchdowns: number;  // TDs on recent drives
  field_goals: number;  // Field goals on recent drives
  turnovers: number;  // Turnovers on recent drives
  red_zone_efficiency: string;  // "2/3" format (scores/trips)
  drive_state?: string | null;  // "ATTACKING", "DEFENDING", "NEUTRAL"
}

export interface NHLTeamStats {
  team_id: string;
  team_name: string;
  games_played: number;
  wins: number;
  losses: number;
  ot_losses: number;  // Overtime/Shootout losses
  points: number;  // NHL points (2 for W, 1 for OTL)
  win_pct: number;
  goals_per_game: number;  // GF/GP
  goals_against_per_game: number;  // GA/GP
  shots_per_game: number;
  shots_against_per_game: number;
  power_play_pct: number;  // PP%
  penalty_kill_pct: number;  // PK%
  faceoff_win_pct: number;
  shooting_pct: number;  // Team shooting %
  save_pct: number;  // Team save %
  pdo: number;  // Shooting % + Save % (luck indicator)
  last_10_record?: string | null;  // "7-2-1" format
  form_trend?: string | null;  // "HOT", "COLD", "NEUTRAL"
  home_record?: string | null;  // "15-5-2"
  away_record?: string | null;  // "12-8-2"
  // Rankings (1-32 for NHL)
  goals_per_game_rank?: number | null;
  goals_against_per_game_rank?: number | null;
  shots_per_game_rank?: number | null;
  shots_against_per_game_rank?: number | null;
  power_play_pct_rank?: number | null;
  penalty_kill_pct_rank?: number | null;
  faceoff_win_pct_rank?: number | null;
  shooting_pct_rank?: number | null;
  save_pct_rank?: number | null;
  pdo_rank?: number | null;
  // Empty Net Statistics (courtesy of MoreHockeyStats.com)
  en_goals_for?: number | null;  // Empty net goals scored
  en_goals_against?: number | null;  // Empty net goals allowed
  en_differential?: number | null;  // EN goals for - against
  en_situations?: number | null;  // Count of EN situations
  en_success_rate?: number | null;  // Success rate when pulling goalie
  // Empty Net Offensive (WITH Empty Net - we pulled goalie)
  en_goals_for_offensive?: number | null;  // Goals scored when we pulled goalie
  en_goals_against_offensive?: number | null;  // Goals allowed when we pulled goalie
  en_situations_offensive?: number | null;  // Situations when we pulled goalie
  // Empty Net Defensive (AGAINST Empty Net - opponent pulled goalie)
  en_goals_for_defensive?: number | null;  // Goals scored when opponent pulled goalie
  en_goals_against_defensive?: number | null;  // Goals allowed when opponent pulled goalie
  en_situations_defensive?: number | null;  // Situations when opponent pulled goalie
  // Empty Net Rankings (1-32)
  en_goals_for_rank?: number | null;
  en_goals_against_rank?: number | null;
  en_differential_rank?: number | null;
  // Empty Net Offensive Rankings
  goals_for_offensive_rank?: number | null;
  goals_against_offensive_rank?: number | null;
  situations_offensive_rank?: number | null;
  // Empty Net Defensive Rankings
  goals_for_defensive_rank?: number | null;
  goals_against_defensive_rank?: number | null;
  situations_defensive_rank?: number | null;
}

export interface NFLTeamStats {
  team_id: string;
  team_name: string;
  games_played: number;
  wins: number;
  losses: number;
  ties: number;
  win_pct: number;
  points_per_game: number;  // Offensive points per game
  points_allowed_per_game: number;  // Defensive points allowed per game
  point_differential: number;  // Net points per game
  total_yards_per_game: number;  // Total offense
  yards_allowed_per_game: number;  // Total defense
  passing_yards_per_game: number;
  rushing_yards_per_game: number;
  turnovers_per_game: number;  // Giveaways
  takeaways_per_game: number;  // Defensive takeaways
  turnover_differential: number;  // +/- turnovers
  third_down_pct: number;  // 3rd down conversion %
  red_zone_pct: number;  // Red zone scoring %
  sacks_per_game: number;  // Defensive sacks
  yards_per_play?: number | null;  // Offensive efficiency
  completion_pct?: number | null;  // Passing completion percentage
  fourth_down_conversion_pct?: number | null;  // 4th down conversion %
  interceptions_thrown_per_game?: number | null;  // INTs thrown per game
  fumbles_lost_per_game?: number | null;  // Fumbles lost per game
  offensive_touchdowns_per_game?: number | null;  // Offensive TDs per game
  defensive_touchdowns_per_game?: number | null;  // Defensive TDs per game
  // Additional volume stats (Phase 3, 4, 5)
  passing_touchdowns_per_game?: number | null;  // Passing TDs per game
  rushing_touchdowns_per_game?: number | null;  // Rushing TDs per game
  touchdowns_per_game?: number | null;  // Total TDs per game
  pass_attempts_per_game?: number | null;  // Pass attempts per game
  rushing_attempts_per_game?: number | null;  // Rush attempts per game
  qb_sacked_per_game?: number | null;  // Times QB sacked per game
  penalty_yards_per_game?: number | null;  // Penalty yards per game
  two_point_conversion_pct?: number | null;  // 2-point conversion %
  plays_per_game?: number | null;  // Total plays per game
  opponent_passing_touchdowns_per_game?: number | null;  // Opponent pass TDs allowed
  opponent_rushing_touchdowns_per_game?: number | null;  // Opponent rush TDs allowed
  opponent_plays_per_game?: number | null;  // Opponent plays per game
  opponent_first_downs_per_game?: number | null;  // Opponent first downs
  last_5_record?: string | null;  // "4-1"
  form_trend?: string | null;  // "HOT", "COLD", "NEUTRAL"
  home_record?: string | null;  // "8-1"
  away_record?: string | null;  // "5-3"
  division_record?: string | null;  // "3-1"
  conference_record?: string | null;  // "8-3"
  // Rankings (1-32 for NFL, 1-134 for NCAAF)
  points_per_game_rank?: number | null;  // Offensive rank
  points_allowed_per_game_rank?: number | null;  // Defensive rank
  total_yards_per_game_rank?: number | null;  // Total offense rank
  yards_allowed_per_game_rank?: number | null;  // Total defense rank
  passing_yards_per_game_rank?: number | null;  // Pass offense rank
  rushing_yards_per_game_rank?: number | null;  // Rush offense rank
  passing_yards_allowed_rank?: number | null;  // Pass defense rank
  rushing_yards_allowed_rank?: number | null;  // Rush defense rank
  third_down_pct_rank?: number | null;  // 3rd down conversion rank
  red_zone_pct_rank?: number | null;  // Red zone efficiency rank
  sacks_rank?: number | null;  // Defensive sacks rank
  turnover_differential_rank?: number | null;  // Turnover margin rank
  // Betting Trends (ATS - Against The Spread)
  ats_wins?: number | null;  // ATS wins
  ats_losses?: number | null;  // ATS losses
  ats_pushes?: number | null;  // ATS pushes
  home_ats_wins?: number | null;  // Home ATS wins
  home_ats_losses?: number | null;  // Home ATS losses
  home_ats_pushes?: number | null;  // Home ATS pushes
  away_ats_wins?: number | null;  // Away ATS wins
  away_ats_losses?: number | null;  // Away ATS losses
  away_ats_pushes?: number | null;  // Away ATS pushes
  ats_last_5?: number[] | null;  // Last 5 games: [1, 0, 1, 1, 0] (1=win, 0=loss, -1=push)
  ats_last_10?: number[] | null;  // Last 10 games
  // Betting Trends (O/U - Over/Under)
  ou_overs?: number | null;  // Overs hit
  ou_unders?: number | null;  // Unders hit
  ou_pushes?: number | null;  // O/U pushes
  home_ou_overs?: number | null;  // Home overs
  home_ou_unders?: number | null;  // Home unders
  home_ou_pushes?: number | null;  // Home pushes
  away_ou_overs?: number | null;  // Away overs
  away_ou_unders?: number | null;  // Away unders
  away_ou_pushes?: number | null;  // Away pushes
  ou_last_5?: number[] | null;  // Last 5 games: [1, 0, 1, 1, 0] (1=over, 0=under, -1=push)
  ou_last_10?: number[] | null;  // Last 10 games
}

export interface MLBTeamStats {
  team_id: string;
  team_name: string;
  games_played: number;
  wins: number;
  losses: number;
  win_pct: number;
  // Batting statistics
  runs_per_game: number;  // Runs scored per game
  batting_avg: number;  // Team batting average
  on_base_pct: number;  // OBP
  slugging_pct: number;  // SLG
  ops: number;  // On-base + slugging
  home_runs_per_game: number;
  hits_per_game: number;
  stolen_bases: number;
  // Pitching statistics
  era: number;  // Earned run average
  whip: number;  // Walks + hits per inning
  strikeouts_per_9: number;  // K/9
  walks_per_9: number;  // BB/9
  hits_allowed_per_9: number;
  saves: number;
  blown_saves: number;
  quality_starts: number;
  // Recent form
  last_10_record?: string | null;  // "7-3" format
  form_trend?: string | null;  // "HOT", "COLD", "NEUTRAL"
  home_record?: string | null;  // "45-36"
  away_record?: string | null;  // "40-41"
  // Rankings (1-30 for MLB)
  runs_per_game_rank?: number | null;
  batting_avg_rank?: number | null;
  ops_rank?: number | null;
  home_runs_rank?: number | null;
  era_rank?: number | null;
  whip_rank?: number | null;
  strikeouts_per_9_rank?: number | null;
  saves_rank?: number | null;
}

export interface StrategyAlert {
  strategy_id: string;  // 'quarter_reversal', 'favorite_comeback', 'halftime_tracker', etc.
  strategy_name: string;  // 'NBA Quarter Reversal', 'Favorite Comeback', etc.
  game_id?: string;  // Game identifier
  home_team?: string;  // Home team name
  away_team?: string;  // Away team name
  sport?: string;  // Sport key (e.g., 'basketball_nba', 'icehockey_nhl')
  confidence: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  trigger: string;  // Why the alert fired: "Q2 hot start reversal detected"
  recommendation: string;  // "Bet UNDER 2H total", "Fade favorite", etc.
  edge_percentage: number;  // Expected edge: 8.5%
  expected_roi: number;  // Expected ROI: 12.1%
  win_probability: number;  // Historical win rate: 58.3%
  stake_recommendation: number;  // Kelly-sized units: 1.5 units
  bet_options?: BetOption[];  // Multiple bet options with odds
  reasoning?: string;  // Detailed explanation
  urgency?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';  // How urgent
  expires_in?: number;  // Seconds until alert expires
  sound_alert?: boolean;  // Play audio alert?
  custom_audio_url?: string;  // Custom audio file URL (overrides default alert sounds)
  timestamp: string;  // When alert was generated
}

export interface BetOption {
  label: string;  // "Under 2H 110.5"
  market_type: string;  // "totals", "spread", "moneyline"
  bet_side: string;  // "UNDER", "OVER", "HOME", "AWAY"
  line?: number;  // 110.5
  odds: number;  // -110
  bookmaker: string;  // "draftkings"
  bookmaker_title?: string;  // "DraftKings"
  bookmaker_logo?: string;  // URL to bookmaker favicon/logo
  probability: number;  // 0.583
  expected_value: number;  // 0.089 (8.9%)
  kelly_size?: number;  // 1.5 units
  alt_bookmakers?: Array<{
    bookmaker: string;
    bookmaker_title?: string;
    bookmaker_logo?: string;
    odds: number;
  }>;
}

// Generic Advanced Analytics (from custom models) - Used for all sports
export interface AdvancedAnalytics {
  // Top 5 Must-Have Metrics (Always Visible)
  direction: 'OVER' | 'UNDER';  // Bet direction
  line: number;  // Current total line (e.g., 164.5)
  z_score: number;  // Statistical deviation (e.g., 2.2)
  edge_points: number;  // Edge in points (e.g., 8.3)
  model_prediction: number;  // Model's predicted total (e.g., 156.2)
  live_total: number;  // Current live total (e.g., 164.5)
  kelly_percentage: number;  // Kelly criterion bankroll % (e.g., 3.2)
  confidence: number;  // Confidence percentage (e.g., 78)

  // Secondary Metrics (Below fold or on hover)
  pregame_total?: number;  // Opening line
  line_movement?: number;  // Change from open to current
  standard_deviation?: number;  // Uncertainty metric
  home_tempo?: number;  // Possessions per game (basketball) or pace (other sports)
  away_tempo?: number;  // Possessions per game (basketball) or pace (other sports)
  home_offensive_efficiency?: number;  // Points per 100 possessions
  away_offensive_efficiency?: number;  // Points per 100 possessions
  home_defensive_efficiency?: number;  // Points allowed per 100 possessions
  away_defensive_efficiency?: number;  // Points allowed per 100 possessions
  time_remaining?: string;  // "12:34" format
  deviation_description?: string;  // Human-readable explanation
}

// NCAAB Advanced Analytics (alias for backwards compatibility)
export type NCAABAnalytics = AdvancedAnalytics;

export interface LiveGame {
  state: GameState;
  odds: GameOdds[];
  projection: GameProjection;
  home_team_stats: TeamStats | null;
  away_team_stats: TeamStats | null;
  home_nfl_live_stats: NFLLiveStats | null;
  away_nfl_live_stats: NFLLiveStats | null;
  home_nfl_stats: NFLTeamStats | null;
  away_nfl_stats: NFLTeamStats | null;
  home_ncaaf_stats: NFLTeamStats | null;
  away_ncaaf_stats: NFLTeamStats | null;
  home_nhl_momentum: NHLMomentumStats | null;
  away_nhl_momentum: NHLMomentumStats | null;
  home_nhl_stats: NHLTeamStats | null;
  away_nhl_stats: NHLTeamStats | null;
  home_nba_momentum: NBAMomentumStats | null;
  away_nba_momentum: NBAMomentumStats | null;
  home_nfl_momentum: NFLMomentumStats | null;
  away_nfl_momentum: NFLMomentumStats | null;
  home_ncaaf_momentum: NFLMomentumStats | null;
  alternate_lines?: AlternateMarketLine[] | null;
  away_ncaaf_momentum: NFLMomentumStats | null;
  home_mlb_stats: MLBTeamStats | null;
  away_mlb_stats: MLBTeamStats | null;
  player_props_count?: number | null;
  strategy_alerts?: StrategyAlert[];  // NEW: Strategy alerts for this game
  ncaab_analytics?: NCAABAnalytics | null;  // NCAAB custom analytics from our models
  nba_analytics?: AdvancedAnalytics | null;  // NBA custom analytics
  nfl_analytics?: AdvancedAnalytics | null;  // NFL custom analytics
  ncaaf_analytics?: AdvancedAnalytics | null;  // NCAAF custom analytics
  mlb_analytics?: AdvancedAnalytics | null;  // MLB custom analytics
  nhl_analytics?: AdvancedAnalytics | null;  // NHL custom analytics
  // B2B / Rest day fatigue fields
  away_rest_days?: number | null;
  home_rest_days?: number | null;
  fatigue_edge?: number | null;
  fatigue_edge_points?: number | null;
  rest_differential?: number | null;
}

export interface AlternateMarketLine {
  market_type: string; // '1H', '2H', 'Q1', 'Q2', 'Q3', 'Q4'
  bookmaker: string;
  total?: number | null;
  over_price?: number | null;
  under_price?: number | null;
  home_spread?: number | null;
  away_spread?: number | null;
  home_spread_price?: number | null;
  away_spread_price?: number | null;
}

export interface AdvancedSystem {
  id: number;
  name: string;
  status: 'live' | 'active' | 'proven' | 'pending';
  description: string;
  sports: string[];  // ['basketball_nba', 'icehockey_nhl'] or ['multi-sport']
  difficulty: 'EASY' | 'MEDIUM' | 'HARD';
  evRange: {
    min: number;
    max: number;
  };
  performance?: {
    winRate?: number;
    roi?: number;
    alerts?: number;
    games?: number;
  };
  backend?: string;
  apiEndpoint?: string;
  strategyId?: number;
}
