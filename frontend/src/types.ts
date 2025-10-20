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
}

export interface GameProjection {
  current_total: number;
  projected_final: number;
  pregame_total: number;
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
  home_nhl_momentum: NHLMomentumStats | null;
  away_nhl_momentum: NHLMomentumStats | null;
  home_nhl_stats: NHLTeamStats | null;
  away_nhl_stats: NHLTeamStats | null;
  home_mlb_stats: MLBTeamStats | null;
  away_mlb_stats: MLBTeamStats | null;
}
