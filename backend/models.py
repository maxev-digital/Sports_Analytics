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
