"""Pydantic models for type safety"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Team(BaseModel):
    name: str
    score: Optional[int] = None
    spread: Optional[float] = None
    spread_price: Optional[int] = None
    money_line: Optional[int] = None
    momentum: Optional[float] = None  # -100 to 100 scale, represents recent play trends

class GameState(BaseModel):
    id: str
    sport_key: str  # 'basketball_nba_preseason', 'icehockey_nhl', 'americanfootball_ncaaf'
    home_team: Team
    away_team: Team
    commence_time: datetime
    status: str  # 'upcoming', 'live', 'final'
    quarter: Optional[int] = None
    time_remaining: Optional[str] = None  # "5:23" format
    
class GameOdds(BaseModel):
    bookmaker: str
    total: float
    over_price: int
    under_price: int
    is_best_over: bool = False  # True if this book has best over line
    is_best_under: bool = False  # True if this book has best under line
    latency_ms: Optional[float] = None  # Milliseconds delay from fastest book (0 = fastest)
    # Spread and ML data per book
    home_spread: Optional[float] = None
    away_spread: Optional[float] = None
    home_spread_price: Optional[int] = None
    away_spread_price: Optional[int] = None
    home_ml: Optional[int] = None
    away_ml: Optional[int] = None
    
class GameProjection(BaseModel):
    current_total: int
    projected_final: float
    pregame_total: float  # Opening/closing total from one book
    current_live_total: Optional[float] = None  # Current live average
    line_movement: Optional[float] = None  # Difference between pregame and current
    best_book_disparity: Optional[str] = None  # Book with largest disparity
    best_disparity_amount: Optional[float] = None  # Amount of largest disparity
    edge: Optional[float] = None
    confidence: str  # 'LOW', 'MEDIUM', 'HIGH'
    recommendation: Optional[str] = None  # 'OVER', 'UNDER', None
    # Advanced pace analysis fields
    current_pace: Optional[float] = None  # Current game pace (possessions per 48)
    expected_pace: Optional[float] = None  # Expected pace based on team averages
    pace_differential: Optional[float] = None  # Current vs expected pace
    efficiency_factor: Optional[float] = None  # Combined shooting efficiency vs season
    regression_factor: Optional[float] = None  # Hot/cold shooting regression factor
    pace_indicator: Optional[str] = None  # Human-readable pace/shooting indicator
    strength_factor: Optional[float] = None  # Overall strength of the bet (0-100 scale)
    unit_recommendation: Optional[float] = None  # Recommended unit size (0.5-5.0 units)
    first_half_total: Optional[float] = None  # Projected first half total
    first_half_current: Optional[int] = None  # Current first half score

class TeamStats(BaseModel):
    team_id: str
    team_name: str
    games_played: int
    wins: int
    losses: int
    win_pct: float
    off_rating: float  # Offensive rating per 100 possessions
    def_rating: float  # Defensive rating per 100 possessions
    net_rating: float  # Net rating (off - def)
    pace: float  # Possessions per game
    fg_pct: float  # Field goal percentage
    fg3_pct: float  # 3-point percentage
    ft_pct: float  # Free throw percentage
    pts_per_game: float  # Points per game
    pts_allowed: float  # Points allowed per game
    last_5_record: Optional[str] = None  # e.g., "4-1"
    last_5_avg_pts: Optional[float] = None  # Avg points in last 5
    last_5_avg_margin: Optional[float] = None  # Avg +/- in last 5
    form_trend: Optional[str] = None  # "HOT", "COLD", "NEUTRAL"
    # Rankings (1-30 for NBA)
    pts_per_game_rank: Optional[int] = None  # Points per game rank
    off_rating_rank: Optional[int] = None  # Offensive rating rank
    def_rating_rank: Optional[int] = None  # Defensive rating rank
    net_rating_rank: Optional[int] = None  # Net rating rank
    pace_rank: Optional[int] = None  # Pace rank
    fg_pct_rank: Optional[int] = None  # Field goal % rank
    fg3_pct_rank: Optional[int] = None  # 3-point % rank
    ft_pct_rank: Optional[int] = None  # Free throw % rank

class NFLLiveStats(BaseModel):
    """Live in-game statistics for NFL games"""
    first_downs: Optional[str] = None
    first_downs_passing: Optional[str] = None
    first_downs_rushing: Optional[str] = None
    first_downs_penalty: Optional[str] = None
    third_down_eff: Optional[str] = None
    fourth_down_eff: Optional[str] = None
    total_yards: Optional[str] = None
    yards_per_play: Optional[str] = None
    passing_yards: Optional[str] = None
    comp_att: Optional[str] = None
    yards_per_pass: Optional[str] = None
    interceptions_thrown: Optional[str] = None
    sacks_yards_lost: Optional[str] = None
    rushing_yards: Optional[str] = None
    rushing_attempts: Optional[str] = None
    yards_per_rush: Optional[str] = None
    red_zone: Optional[str] = None
    penalties: Optional[str] = None
    turnovers: Optional[str] = None
    fumbles_lost: Optional[str] = None
    defensive_td: Optional[str] = None
    possession: Optional[str] = None
    total_plays: Optional[str] = None

class NHLMomentumStats(BaseModel):
    """Live momentum statistics for NHL games"""
    momentum_score: float  # 0-100 scale (higher = more momentum)
    recent_shots: int  # Shots in last 5 minutes
    scoring_chances: int  # High danger shots
    faceoff_wins: int  # Faceoffs won in recent play
    offensive_zone_events: int  # Events in offensive zone
    possession_indicator: Optional[str] = None  # "ATTACKING", "DEFENDING", "NEUTRAL"
    power_play_opps: Optional[str] = None  # "2/3" format (scored/total)
    penalty_minutes: Optional[int] = None  # Total penalty minutes
    blocked_shots: Optional[int] = None  # Shots blocked (defensive metric)

class NBAMomentumStats(BaseModel):
    """Live momentum statistics for NBA games"""
    momentum_score: float  # 0-100 scale (higher = more momentum)
    points_last_5min: int  # Points scored in last ~5 minutes
    fg_pct_recent: float  # Field goal % in recent possessions
    offensive_rebounds: int  # Offensive rebounds (second chance points)
    turnovers: int  # Turnovers in recent play
    steals: int  # Steals forced
    assists: int  # Assists in recent play
    possession_indicator: Optional[str] = None  # "ATTACKING", "DEFENDING", "NEUTRAL"

class NFLMomentumStats(BaseModel):
    """Live momentum statistics for NFL/NCAAF games"""
    momentum_score: float  # 0-100 scale (higher = more momentum)
    yards_per_play: float  # Average yards per play on recent drives
    recent_yards: int  # Total yards gained on recent drives
    recent_points: int  # Points scored on recent drives
    touchdowns: int  # TDs on recent drives
    field_goals: int  # Field goals on recent drives
    turnovers: int  # Turnovers on recent drives
    red_zone_efficiency: str  # "2/3" format (scores/trips)
    drive_state: Optional[str] = None  # "ATTACKING", "DEFENDING", "NEUTRAL"

class NHLTeamStats(BaseModel):
    """Season statistics for NHL teams"""
    team_id: str
    team_name: str
    games_played: int
    wins: int
    losses: int
    ot_losses: int  # Overtime/Shootout losses
    points: int  # NHL points (2 for W, 1 for OTL)
    win_pct: float
    goals_per_game: float  # GF/GP
    goals_against_per_game: float  # GA/GP
    shots_per_game: float
    shots_against_per_game: float
    power_play_pct: float  # PP%
    penalty_kill_pct: float  # PK%
    faceoff_win_pct: float
    shooting_pct: float  # Team shooting %
    save_pct: float  # Team save %
    pdo: float  # Shooting % + Save % (luck indicator)
    last_10_record: Optional[str] = None  # "7-2-1" format
    form_trend: Optional[str] = None  # "HOT", "COLD", "NEUTRAL"
    home_record: Optional[str] = None  # "15-5-2"
    away_record: Optional[str] = None  # "12-8-2"
    # Rankings (1-32 for NHL)
    goals_per_game_rank: Optional[int] = None  # Goals per game rank
    goals_against_per_game_rank: Optional[int] = None  # Goals against rank (defensive)
    shots_per_game_rank: Optional[int] = None  # Shots per game rank
    shots_against_per_game_rank: Optional[int] = None  # Shots against rank (defensive)
    power_play_pct_rank: Optional[int] = None  # Power play % rank
    penalty_kill_pct_rank: Optional[int] = None  # Penalty kill % rank
    faceoff_win_pct_rank: Optional[int] = None  # Faceoff win % rank
    shooting_pct_rank: Optional[int] = None  # Shooting % rank
    save_pct_rank: Optional[int] = None  # Save % rank
    pdo_rank: Optional[int] = None  # PDO rank

class NFLTeamStats(BaseModel):
    """Season statistics for NFL teams"""
    team_id: str
    team_name: str
    games_played: int
    wins: int
    losses: int
    ties: int
    win_pct: float
    points_per_game: float  # Offensive points per game
    points_allowed_per_game: float  # Defensive points allowed per game
    point_differential: float  # Net points per game
    total_yards_per_game: float  # Total offense
    yards_allowed_per_game: float  # Total defense
    passing_yards_per_game: float
    rushing_yards_per_game: float
    turnovers_per_game: float  # Giveaways
    takeaways_per_game: float  # Defensive takeaways
    turnover_differential: float  # +/- turnovers
    third_down_pct: float  # 3rd down conversion %
    red_zone_pct: float  # Red zone scoring %
    sacks_per_game: float  # Defensive sacks
    last_5_record: Optional[str] = None  # "4-1"
    form_trend: Optional[str] = None  # "HOT", "COLD", "NEUTRAL"
    home_record: Optional[str] = None  # "8-1"
    away_record: Optional[str] = None  # "5-3"
    division_record: Optional[str] = None  # "3-1"
    conference_record: Optional[str] = None  # "8-3"
    # Rankings (1-32 for NFL, 1-134 for NCAAF)
    points_per_game_rank: Optional[int] = None  # Offensive rank
    points_allowed_per_game_rank: Optional[int] = None  # Defensive rank
    total_yards_per_game_rank: Optional[int] = None  # Total offense rank
    yards_allowed_per_game_rank: Optional[int] = None  # Total defense rank
    passing_yards_per_game_rank: Optional[int] = None  # Pass offense rank
    rushing_yards_per_game_rank: Optional[int] = None  # Rush offense rank
    passing_yards_allowed_rank: Optional[int] = None  # Pass defense rank
    rushing_yards_allowed_rank: Optional[int] = None  # Rush defense rank
    third_down_pct_rank: Optional[int] = None  # 3rd down conversion rank
    red_zone_pct_rank: Optional[int] = None  # Red zone efficiency rank
    sacks_rank: Optional[int] = None  # Defensive sacks rank
    turnover_differential_rank: Optional[int] = None  # Turnover margin rank

class MLBTeamStats(BaseModel):
    """Season statistics for MLB teams"""
    team_id: str
    team_name: str
    games_played: int
    wins: int
    losses: int
    win_pct: float
    # Batting statistics
    runs_per_game: float  # Runs scored per game
    batting_avg: float  # Team batting average
    on_base_pct: float  # OBP
    slugging_pct: float  # SLG
    ops: float  # On-base + slugging
    home_runs_per_game: float
    hits_per_game: float
    stolen_bases: int
    # Pitching statistics
    era: float  # Earned run average
    whip: float  # Walks + hits per inning
    strikeouts_per_9: float  # K/9
    walks_per_9: float  # BB/9
    hits_allowed_per_9: float
    saves: int
    blown_saves: int
    quality_starts: int
    # Recent form
    last_10_record: Optional[str] = None  # "7-3" format
    form_trend: Optional[str] = None  # "HOT", "COLD", "NEUTRAL"
    home_record: Optional[str] = None  # "45-36"
    away_record: Optional[str] = None  # "40-41"
    # Rankings (1-30 for MLB)
    runs_per_game_rank: Optional[int] = None
    batting_avg_rank: Optional[int] = None
    ops_rank: Optional[int] = None
    home_runs_rank: Optional[int] = None
    era_rank: Optional[int] = None
    whip_rank: Optional[int] = None
    strikeouts_per_9_rank: Optional[int] = None
    saves_rank: Optional[int] = None

class LiveGame(BaseModel):
    state: GameState
    odds: list[GameOdds]
    projection: GameProjection
    home_team_stats: Optional[TeamStats] = None  # NBA team stats
    away_team_stats: Optional[TeamStats] = None  # NBA team stats
    home_nfl_live_stats: Optional[NFLLiveStats] = None  # NFL-specific live stats
    away_nfl_live_stats: Optional[NFLLiveStats] = None  # NFL-specific live stats
    home_nfl_stats: Optional[NFLTeamStats] = None  # NFL-specific season stats
    away_nfl_stats: Optional[NFLTeamStats] = None  # NFL-specific season stats
    home_nhl_momentum: Optional[NHLMomentumStats] = None  # NHL-specific momentum
    away_nhl_momentum: Optional[NHLMomentumStats] = None  # NHL-specific momentum
    home_nhl_stats: Optional[NHLTeamStats] = None  # NHL-specific season stats
    away_nhl_stats: Optional[NHLTeamStats] = None  # NHL-specific season stats
    home_nba_momentum: Optional[NBAMomentumStats] = None  # NBA-specific momentum
    away_nba_momentum: Optional[NBAMomentumStats] = None  # NBA-specific momentum
    home_nfl_momentum: Optional[NFLMomentumStats] = None  # NFL-specific momentum
    away_nfl_momentum: Optional[NFLMomentumStats] = None  # NFL-specific momentum
    home_ncaaf_momentum: Optional[NFLMomentumStats] = None  # NCAAF-specific momentum (uses same model as NFL)
    away_ncaaf_momentum: Optional[NFLMomentumStats] = None  # NCAAF-specific momentum (uses same model as NFL)
    home_mlb_stats: Optional[MLBTeamStats] = None  # MLB-specific season stats
    away_mlb_stats: Optional[MLBTeamStats] = None  # MLB-specific season stats
    quarters: Optional[dict] = None  # NBA quarter-by-quarter scores: {'Q1': {'home': 25, 'away': 22}, ...}


# ============================================================================
# PLAYER PROPS MODELS
# ============================================================================

class BookmakerOdds(BaseModel):
    """Odds from a single bookmaker for a player prop"""
    bookmaker: str
    over_odds: Optional[int] = None  # American odds (e.g., -110)
    under_odds: Optional[int] = None  # American odds (e.g., -110)

class PlayerPropOdds(BaseModel):
    """Market odds for a single player prop"""
    player_name: str
    prop_type: str  # 'points', 'rebounds', 'assists', 'threes', etc.
    line: float  # The over/under line (e.g., 25.5)
    bookmakers: list[BookmakerOdds]  # All available bookmaker odds
    best_over_odds: Optional[int] = None  # Best available over odds
    best_under_odds: Optional[int] = None  # Best available under odds
    best_over_book: Optional[str] = None  # Bookmaker with best over
    best_under_book: Optional[str] = None  # Bookmaker with best under

class ProjectionFactors(BaseModel):
    """Detailed breakdown of projection factors"""
    baseline: float  # Season average
    recent_avg: float  # Recent games average
    trend: str  # 'increasing', 'decreasing', 'stable'
    matchup_adjustment: float  # Adjustment for opponent defense
    pace_adjustment: float  # Adjustment for game pace
    total_adjustment: float  # Total adjustment applied

class PlayerPropProjection(BaseModel):
    """Our projection for a player prop"""
    prop_type: str  # 'points', 'rebounds', 'assists', 'threes'
    projection: float  # Our projected value
    confidence: str  # 'HIGH', 'MEDIUM', 'LOW'
    confidence_score: float  # Numerical confidence (0.0-1.0)
    factors: ProjectionFactors  # Detailed breakdown
    reasoning: str  # Human-readable explanation

class PlayerPropEdge(BaseModel):
    """Edge analysis comparing projection to market line"""
    edge: float  # Difference (projection - line)
    edge_pct: float  # Percentage edge
    recommendation: Optional[str] = None  # 'OVER', 'UNDER', or None
    bet_strength: Optional[str] = None  # 'STRONG', 'MODERATE', 'WEAK', or None

class PlayerProp(BaseModel):
    """Complete player prop with odds, projection, and edge"""
    player_name: str
    team: str
    opponent: Optional[str] = None
    game_time: Optional[datetime] = None
    prop_type: str
    market_odds: PlayerPropOdds  # Market odds from bookmakers
    projection: PlayerPropProjection  # Our projection
    edge: PlayerPropEdge  # Edge analysis

class PlayerPropsGame(BaseModel):
    """All player props for a single game"""
    event_id: str
    sport_key: str
    home_team: str
    away_team: str
    commence_time: datetime
    props: list[PlayerProp]  # All player props for this game

class PlayerPropsResponse(BaseModel):
    """API response for player props"""
    games: list[PlayerPropsGame]  # Props organized by game
    total_props: int  # Total number of props with edges
    total_strong_bets: int  # Number of strong bet recommendations
    total_moderate_bets: int  # Number of moderate bet recommendations
    last_updated: datetime  # When props were last fetched/updated

