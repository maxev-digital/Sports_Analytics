"""Advanced game projection algorithm with pace analysis"""
from live_models import GameState, GameProjection, TeamStats
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class GameProjector:
    """Advanced projection algorithm with pace and efficiency analysis"""

    # Efficiency weight constants
    FG_PCT_WEIGHT = 0.50
    FG3_PCT_WEIGHT = 0.30
    FT_PCT_WEIGHT = 0.20

    @staticmethod
    def calculate_time_elapsed_seconds(quarter: int, time_remaining: str, sport_key: str = "basketball_nba") -> int:
        """Calculate seconds elapsed in game

        Args:
            quarter: Current quarter/period
            time_remaining: Time remaining in format "5:23"
            sport_key: Sport identifier (basketball_nba or americanfootball_*)
        """
        # Determine quarter length based on sport
        if sport_key.startswith('americanfootball'):
            QUARTER_LENGTH = 900  # 15 minutes for NFL/NCAA Football
        else:
            QUARTER_LENGTH = 720  # 12 minutes for NBA/NHL

        # Parse time_remaining "5:23" -> 323 seconds
        try:
            parts = time_remaining.split(":")
            minutes = int(parts[0])
            seconds = int(parts[1])
            remaining_in_quarter = (minutes * 60) + seconds
        except:
            remaining_in_quarter = QUARTER_LENGTH / 2

        # Calculate elapsed
        if quarter <= 4:
            elapsed = ((quarter - 1) * QUARTER_LENGTH) + (QUARTER_LENGTH - remaining_in_quarter)
        else:
            # Overtime
            regular_time = 4 * QUARTER_LENGTH
            ot_time = (quarter - 4) * 300
            elapsed = regular_time + ot_time + (300 - remaining_in_quarter)

        return elapsed

    @staticmethod
    def calculate_time_weights(minutes_played: float) -> Tuple[float, float]:
        """
        Calculate weighting between season data and current game data

        Returns: (season_weight, current_weight)
        """
        if minutes_played < 12:
            return (0.60, 0.40)
        elif minutes_played < 24:
            return (0.40, 0.60)
        else:
            return (0.25, 0.75)

    @staticmethod
    def estimate_possessions(
        score: int,
        minutes_played: float,
        team_pace: float
    ) -> float:
        """
        Estimate possessions for a team based on current score and pace

        In a real implementation with play-by-play data, we'd use:
        Possessions = FGA - OREB + TO + (0.4 × FTA)

        For now, we estimate based on pace and time
        """
        # Possessions per 48 minutes = pace
        # Possessions in current time = (pace / 48) * minutes_played
        estimated_possessions = (team_pace / 48.0) * minutes_played
        return estimated_possessions

    @staticmethod
    def calculate_current_pace(
        total_score: int,
        home_stats: TeamStats,
        away_stats: TeamStats,
        minutes_played: float
    ) -> float:
        """
        Calculate current game pace (possessions per 48 minutes)

        Estimates total possessions and projects to 48 minutes
        """
        if minutes_played <= 0:
            return (home_stats.pace + away_stats.pace) / 2.0

        # Estimate possessions for each team
        home_poss = GameProjector.estimate_possessions(
            total_score // 2,  # Rough estimate of home score
            minutes_played,
            home_stats.pace
        )
        away_poss = GameProjector.estimate_possessions(
            total_score // 2,  # Rough estimate of away score
            minutes_played,
            away_stats.pace
        )

        # Average possessions
        avg_possessions = (home_poss + away_poss) / 2.0

        # Project to 48 minutes
        if minutes_played > 0:
            current_pace = (avg_possessions / minutes_played) * 48.0
        else:
            current_pace = (home_stats.pace + away_stats.pace) / 2.0

        return current_pace

    @staticmethod
    def calculate_efficiency_factor(
        current_score: int,
        minutes_played: float,
        home_stats: TeamStats,
        away_stats: TeamStats
    ) -> float:
        """
        Calculate shooting efficiency factor vs season averages

        Returns value between 0.0 and 2.0:
        - 1.0 = shooting at season averages
        - < 1.0 = shooting below averages (cold)
        - > 1.0 = shooting above averages (hot)
        """
        if minutes_played <= 0:
            return 1.0

        # Average season shooting percentages
        avg_fg_pct = (home_stats.fg_pct + away_stats.fg_pct) / 2.0
        avg_fg3_pct = (home_stats.fg3_pct + away_stats.fg3_pct) / 2.0
        avg_ft_pct = (home_stats.ft_pct + away_stats.ft_pct) / 2.0

        # Expected points based on season averages
        avg_ppg = (home_stats.pts_per_game + away_stats.pts_per_game) / 2.0
        expected_points = (avg_ppg / 48.0) * minutes_played

        if expected_points <= 0:
            return 1.0

        # Current scoring rate vs expected
        scoring_rate = current_score / expected_points

        # Clamp between 0.5 and 1.5 to avoid extreme values
        scoring_rate = max(0.5, min(1.5, scoring_rate))

        return scoring_rate

    @staticmethod
    def calculate_regression_factor(efficiency_factor: float) -> float:
        """
        Calculate regression to mean factor
        Hot/cold shooting tends to regress toward season averages

        Formula: 0.85 + (0.15 × efficiency_factor)
        More conservative - assumes stronger regression to mean
        """
        return 0.85 + (0.15 * efficiency_factor)

    @staticmethod
    def project_final_total(
        current_score: int,
        time_elapsed_seconds: int,
        pregame_total: float,
        quarter: int,
        home_stats: Optional[TeamStats] = None,
        away_stats: Optional[TeamStats] = None
    ) -> GameProjection:
        """
        Project final total using advanced pace and efficiency analysis

        If team stats are provided, uses sophisticated pace-based projection.
        Falls back to simple time-weighted projection if stats unavailable.
        """
        TOTAL_GAME_TIME = 2880  # 48 minutes in seconds
        minutes_played = time_elapsed_seconds / 60.0

        # Use advanced projection if we have team stats
        if home_stats and away_stats:
            return GameProjector._project_with_pace_analysis(
                current_score,
                minutes_played,
                pregame_total,
                quarter,
                home_stats,
                away_stats
            )

        # Fallback to simple projection
        return GameProjector._simple_projection(
            current_score,
            time_elapsed_seconds,
            pregame_total,
            quarter
        )

    @staticmethod
    def _project_with_pace_analysis(
        current_score: int,
        minutes_played: float,
        pregame_total: float,
        quarter: int,
        home_stats: TeamStats,
        away_stats: TeamStats
    ) -> GameProjection:
        """Advanced projection using pace and efficiency analysis"""

        # Calculate expected pace (average of both teams)
        expected_pace = (home_stats.pace + away_stats.pace) / 2.0

        # Calculate current game pace
        current_pace = GameProjector.calculate_current_pace(
            current_score,
            home_stats,
            away_stats,
            minutes_played
        )

        pace_differential = current_pace - expected_pace

        # Calculate efficiency factor
        efficiency_factor = GameProjector.calculate_efficiency_factor(
            current_score,
            minutes_played,
            home_stats,
            away_stats
        )

        # Calculate regression factor
        regression_factor = GameProjector.calculate_regression_factor(efficiency_factor)

        # Get time weights based on minutes played
        season_weight, current_weight = GameProjector.calculate_time_weights(minutes_played)

        # Calculate season-based projection
        avg_ppg = (home_stats.pts_per_game + away_stats.pts_per_game)
        season_projection = avg_ppg

        # Calculate current pace-based projection with regression
        if minutes_played > 0:
            current_pace_projection = (current_score / minutes_played) * 48.0 * regression_factor
        else:
            current_pace_projection = avg_ppg

        # Weighted projection
        projected_final = (season_projection * season_weight) + (current_pace_projection * current_weight)

        # Determine confidence based on time played
        if minutes_played < 12:
            confidence = "LOW"
        elif minutes_played < 30:
            confidence = "MEDIUM"
        else:
            confidence = "HIGH"

        # Generate pace indicator for display
        pace_indicator = GameProjector._generate_pace_indicator(
            pace_differential, efficiency_factor
        )

        logger.info(
            f"Pace Analysis: Expected={expected_pace:.1f}, Current={current_pace:.1f}, "
            f"Diff={pace_differential:.1f}, Efficiency={efficiency_factor:.2f}, "
            f"Regression={regression_factor:.2f}, Projected={projected_final:.1f}, "
            f"Indicator={pace_indicator}"
        )

        return GameProjection(
            current_total=current_score,
            projected_final=round(projected_final, 1),
            pregame_total=pregame_total,
            confidence=confidence,
            current_pace=round(current_pace, 1),
            expected_pace=round(expected_pace, 1),
            pace_differential=round(pace_differential, 1),
            efficiency_factor=round(efficiency_factor, 2),
            regression_factor=round(regression_factor, 2),
            pace_indicator=pace_indicator
        )

    @staticmethod
    def _generate_pace_indicator(pace_differential: float, efficiency_factor: float) -> str:
        """
        Generate human-readable pace indicator

        Combines pace and efficiency information into one concise indicator
        """
        # Determine pace status
        if abs(pace_differential) < 3:
            pace_status = "Normal Pace"
        elif pace_differential > 5:
            pace_status = "Fast Pace"
        elif pace_differential > 3:
            pace_status = "Up-Tempo"
        elif pace_differential < -5:
            pace_status = "Slow Pace"
        else:
            pace_status = "Grinding"

        # Determine shooting status
        if efficiency_factor > 1.15:
            shooting_status = " | Hot Shooting"
        elif efficiency_factor < 0.85:
            shooting_status = " | Cold Shooting"
        else:
            shooting_status = ""

        return pace_status + shooting_status

    @staticmethod
    def _simple_projection(
        current_score: int,
        time_elapsed_seconds: int,
        pregame_total: float,
        quarter: int
    ) -> GameProjection:
        """Simple time-weighted projection (fallback)"""
        TOTAL_GAME_TIME = 2880  # 48 minutes

        # Calculate current pace
        if time_elapsed_seconds > 0:
            current_pace_total = (current_score / time_elapsed_seconds) * TOTAL_GAME_TIME
        else:
            current_pace_total = pregame_total

        # Weight based on quarter
        if quarter == 1:
            projected = (0.7 * pregame_total) + (0.3 * current_pace_total)
            confidence = "LOW"
        elif quarter == 2:
            projected = (0.5 * pregame_total) + (0.5 * current_pace_total)
            confidence = "MEDIUM"
        elif quarter == 3:
            projected = (0.3 * pregame_total) + (0.7 * current_pace_total)
            confidence = "MEDIUM"
        else:
            projected = (0.2 * pregame_total) + (0.8 * current_pace_total)
            confidence = "HIGH"

        return GameProjection(
            current_total=current_score,
            projected_final=round(projected, 1),
            pregame_total=pregame_total,
            confidence=confidence
        )

    @staticmethod
    def calculate_edge(
        projected_total: float,
        live_total: Optional[float],
        pregame_total: float
    ) -> tuple[Optional[float], Optional[str]]:
        """Calculate edge and recommendation"""
        if live_total is None:
            live_total = pregame_total

        edge = abs(projected_total - live_total)

        # Require 5+ point edge for recommendation
        if edge >= 5.0:
            if projected_total > live_total:
                recommendation = "OVER"
            else:
                recommendation = "UNDER"
            return round(edge, 1), recommendation

        return None, None

    @staticmethod
    def calculate_strength_factor(
        edge: Optional[float],
        confidence: str,
        pace_differential: Optional[float],
        efficiency_factor: Optional[float],
        minutes_played: float
    ) -> float:
        """
        Calculate overall strength factor (0-100 scale)

        Factors considered:
        - Edge size (bigger edge = stronger)
        - Time confidence (more time played = more confidence)
        - Pace differential (extreme pace = more confidence)
        - Efficiency factor (hot/cold shooting = more confidence in direction)
        """
        if edge is None or edge < 5.0:
            return 0.0

        strength = 0.0

        # 1. Edge component (0-40 points) - Edge size matters
        # 5 pts = 10, 10 pts = 20, 15 pts = 30, 20+ pts = 40
        edge_score = min(40, (edge / 0.5))  # 0.5 points = 1 strength point, cap at 40
        strength += edge_score

        # 2. Time confidence (0-25 points)
        if confidence == "HIGH":  # 30+ mins
            strength += 25
        elif confidence == "MEDIUM":  # 12-30 mins
            strength += 15
        else:  # <12 mins
            strength += 5

        # 3. Pace factor (0-20 points) - Extreme pace gives more confidence
        if pace_differential is not None:
            pace_strength = min(20, abs(pace_differential) * 2)  # Each point of pace diff = 2 strength
            strength += pace_strength

        # 4. Efficiency factor (0-15 points) - Hot/cold shooting
        if efficiency_factor is not None:
            # If shooting hot (>1.1) or cold (<0.9), adds confidence
            efficiency_deviation = abs(efficiency_factor - 1.0)
            if efficiency_deviation > 0.1:
                efficiency_strength = min(15, efficiency_deviation * 75)  # 0.2 deviation = 15 points
                strength += efficiency_strength

        return round(min(100, strength), 1)

    @staticmethod
    def calculate_unit_recommendation(
        strength_factor: float,
        best_odds: int
    ) -> float:
        """
        Calculate recommended unit size based on strength and odds

        Strength tiers:
        - 0-30: No play (returns 0)
        - 30-50: 0.5-1.0 units
        - 50-70: 1.0-2.0 units
        - 70-85: 2.0-3.5 units
        - 85+: 3.5-5.0 units

        Adjusted by odds value:
        - Better odds (closer to -110) increase unit size slightly
        - Worse odds decrease unit size
        """
        if strength_factor < 30:
            return 0.0

        # Base units from strength
        if strength_factor < 50:
            base_units = 0.5 + ((strength_factor - 30) / 20) * 0.5  # 0.5-1.0
        elif strength_factor < 70:
            base_units = 1.0 + ((strength_factor - 50) / 20) * 1.0  # 1.0-2.0
        elif strength_factor < 85:
            base_units = 2.0 + ((strength_factor - 70) / 15) * 1.5  # 2.0-3.5
        else:
            base_units = 3.5 + ((strength_factor - 85) / 15) * 1.5  # 3.5-5.0

        # Adjust for odds value (prefer better odds)
        # -110 is standard, better than -110 increases slightly, worse decreases
        if best_odds >= -110:  # Good value
            odds_multiplier = 1.1
        elif best_odds >= -120:  # Fair value
            odds_multiplier = 1.0
        elif best_odds >= -130:  # Slight juice
            odds_multiplier = 0.9
        else:  # Heavy juice
            odds_multiplier = 0.8

        final_units = base_units * odds_multiplier

        # Cap at 5 units max, min at 0.5 if we're playing
        return round(min(5.0, max(0.5, final_units)), 1)
