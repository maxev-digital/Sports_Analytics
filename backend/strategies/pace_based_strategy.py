"""
Pace-Based Strategy Engine
Detects EV opportunities based on pace tempo mismatches and projections
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class TeamStats:
    """Team statistics for pace analysis"""
    team_name: str
    pace: float  # Possessions per 48 minutes
    off_rating: float  # Points per 100 possessions
    def_rating: float  # Points allowed per 100 possessions
    rest_days: int  # Days since last game
    home_pace: Optional[float] = None  # Home-specific pace
    away_pace: Optional[float] = None  # Away-specific pace
    back_to_back: bool = False  # Playing on back-to-back
    recent_pace_trend: Optional[float] = None  # Last 5 games pace avg


@dataclass
class MatchupContext:
    """Context for the matchup"""
    home_team: TeamStats
    away_team: TeamStats
    is_neutral_site: bool = False
    league_avg_pace: float = 100.0
    league_avg_rating: float = 110.0
    home_court_advantage: float = 2.5


@dataclass
class PacePrediction:
    """Prediction output from pace analysis"""
    predicted_pace: float
    predicted_total: float
    home_expected_points: float
    away_expected_points: float
    confidence: float  # 0-1 scale
    pace_boost_factor: float  # Multiplier showing pace impact
    scenario: str  # Description of pace scenario


class PaceBasedStrategy:
    """
    Strategy that identifies EV opportunities by analyzing pace mismatches

    Key Concepts:
    - Fast teams vs slow teams create exploitable totals
    - Rest advantages increase pace
    - Back-to-backs decrease pace
    - Home teams control tempo more than away teams
    """

    def __init__(
        self,
        rest_day_boost: float = 1.5,  # Pace boost per extra rest day
        back_to_back_penalty: float = -3.0,  # Pace penalty for B2B
        home_tempo_control: float = 0.6,  # Weight for home team's pace
        pace_mismatch_threshold: float = 5.0,  # Significant pace difference
    ):
        """
        Initialize Pace-Based Strategy

        Args:
            rest_day_boost: Pace increase per day of rest advantage
            back_to_back_penalty: Pace decrease for back-to-back games
            home_tempo_control: How much home team controls pace (0.5-0.7 typical)
            pace_mismatch_threshold: Pace difference that signals opportunity
        """
        self.rest_day_boost = rest_day_boost
        self.back_to_back_penalty = back_to_back_penalty
        self.home_tempo_control = home_tempo_control
        self.pace_mismatch_threshold = pace_mismatch_threshold

    def calculate_expected_pace(self, matchup: MatchupContext) -> tuple[float, str]:
        """
        Calculate expected pace for the matchup

        Uses weighted average favoring home team's pace preference
        Adjusts for rest and fatigue factors

        Returns:
            (expected_pace, scenario_description)
        """
        home = matchup.home_team
        away = matchup.away_team

        # Base pace calculation - weighted toward home team
        if matchup.is_neutral_site:
            base_pace = (home.pace + away.pace) / 2
        else:
            # Home team has more control over tempo
            base_pace = (
                home.pace * self.home_tempo_control +
                away.pace * (1 - self.home_tempo_control)
            )

        # Adjust for rest days
        rest_adjustment = 0
        rest_diff = home.rest_days - away.rest_days

        if rest_diff > 0:
            # Home team more rested, likely faster pace
            rest_adjustment = min(rest_diff * self.rest_day_boost, 4.0)
            scenario = f"HOME_RESTED (+{rest_diff}d)"
        elif rest_diff < 0:
            # Away team more rested
            rest_adjustment = max(rest_diff * self.rest_day_boost, -4.0)
            scenario = f"AWAY_RESTED ({rest_diff}d)"
        else:
            scenario = "EQUAL_REST"

        # Back-to-back penalties
        if home.back_to_back and away.back_to_back:
            rest_adjustment += self.back_to_back_penalty * 1.5  # Both tired, very slow
            scenario = "BOTH_B2B"
        elif home.back_to_back:
            rest_adjustment += self.back_to_back_penalty
            scenario = "HOME_B2B"
        elif away.back_to_back:
            rest_adjustment += self.back_to_back_penalty * 0.7  # Less impact on road
            scenario = "AWAY_B2B"

        # Consider recent pace trends if available
        trend_adjustment = 0
        if home.recent_pace_trend and away.recent_pace_trend:
            # If both teams trending faster/slower, amplify
            avg_trend = (home.recent_pace_trend + away.recent_pace_trend) / 2
            trend_deviation = avg_trend - base_pace
            if abs(trend_deviation) > 2.0:
                trend_adjustment = trend_deviation * 0.3  # 30% weight to recent trend
                scenario += f"_TRENDING({'UP' if trend_deviation > 0 else 'DOWN'})"

        expected_pace = base_pace + rest_adjustment + trend_adjustment

        # Identify pace mismatch scenarios
        pace_diff = abs(home.pace - away.pace)
        if pace_diff >= self.pace_mismatch_threshold:
            if home.pace > away.pace:
                scenario += "_FAST_HOME"
            else:
                scenario += "_FAST_AWAY"

        return expected_pace, scenario

    def calculate_expected_points(
        self,
        team: TeamStats,
        opponent: TeamStats,
        expected_pace: float,
        is_home: bool,
        league_avg: float = 110.0,
        hca: float = 2.5
    ) -> float:
        """
        Calculate expected points for a team

        Args:
            team: TeamStats for the team
            opponent: TeamStats for opponent
            expected_pace: Expected possessions
            is_home: Whether team is home
            league_avg: League average offensive rating
            hca: Home court advantage in points

        Returns:
            Expected points scored
        """
        # Adjust offensive rating vs opponent's defense
        # Formula: ORtg - (Opp_DRtg - League_Avg)
        adjusted_off_rating = team.off_rating - (opponent.def_rating - league_avg)

        # Apply home court advantage
        if is_home:
            adjusted_off_rating += hca

        # Convert to points: (Rating / 100) * Pace
        expected_points = (adjusted_off_rating / 100) * expected_pace

        return expected_points

    def calculate_confidence(
        self,
        pace_diff: float,
        rest_advantage: int,
        sample_size_factor: float = 1.0
    ) -> float:
        """
        Calculate confidence in prediction based on various factors

        Args:
            pace_diff: Absolute difference in team pace ratings
            rest_advantage: Rest day differential
            sample_size_factor: Quality of underlying data (0-1)

        Returns:
            Confidence score (0-1)
        """
        confidence = 0.5  # Base confidence

        # Larger pace mismatches increase confidence
        if pace_diff >= self.pace_mismatch_threshold:
            confidence += min((pace_diff / 20.0), 0.25)

        # Significant rest advantages increase confidence
        if abs(rest_advantage) >= 2:
            confidence += 0.15

        # Sample size factor
        confidence *= sample_size_factor

        return min(confidence, 1.0)

    def predict(self, matchup: MatchupContext) -> PacePrediction:
        """
        Generate prediction for a matchup based on pace analysis

        Args:
            matchup: MatchupContext with both teams' stats

        Returns:
            PacePrediction with expected total and confidence
        """
        # Calculate expected pace
        expected_pace, scenario = self.calculate_expected_pace(matchup)

        # Calculate expected points for each team
        home_points = self.calculate_expected_points(
            team=matchup.home_team,
            opponent=matchup.away_team,
            expected_pace=expected_pace,
            is_home=True,
            league_avg=matchup.league_avg_rating,
            hca=matchup.home_court_advantage
        )

        away_points = self.calculate_expected_points(
            team=matchup.away_team,
            opponent=matchup.home_team,
            expected_pace=expected_pace,
            is_home=False,
            league_avg=matchup.league_avg_rating,
            hca=matchup.home_court_advantage
        )

        predicted_total = home_points + away_points

        # Calculate pace boost factor
        avg_team_pace = (matchup.home_team.pace + matchup.away_team.pace) / 2
        pace_boost_factor = expected_pace / avg_team_pace if avg_team_pace > 0 else 1.0

        # Calculate confidence
        pace_diff = abs(matchup.home_team.pace - matchup.away_team.pace)
        rest_diff = matchup.home_team.rest_days - matchup.away_team.rest_days
        confidence = self.calculate_confidence(pace_diff, rest_diff)

        return PacePrediction(
            predicted_pace=expected_pace,
            predicted_total=predicted_total,
            home_expected_points=home_points,
            away_expected_points=away_points,
            confidence=confidence,
            pace_boost_factor=pace_boost_factor,
            scenario=scenario
        )

    def analyze_total_opportunity(
        self,
        matchup: MatchupContext,
        market_total: float
    ) -> dict:
        """
        Analyze if there's an EV opportunity on the total

        Args:
            matchup: MatchupContext
            market_total: Current betting line

        Returns:
            Dictionary with analysis results
        """
        prediction = self.predict(matchup)

        edge = prediction.predicted_total - market_total
        edge_percentage = (edge / market_total) * 100

        # Determine recommendation
        if abs(edge) < 3.0:
            recommendation = "PASS"
            bet_type = None
        elif edge > 0:
            recommendation = "OVER"
            bet_type = "total_over"
        else:
            recommendation = "UNDER"
            bet_type = "total_under"

        # Adjust confidence for edge size
        confidence_multiplier = min(abs(edge) / 5.0, 1.5)
        adjusted_confidence = prediction.confidence * confidence_multiplier

        return {
            "prediction": prediction,
            "market_total": market_total,
            "predicted_total": prediction.predicted_total,
            "edge": edge,
            "edge_percentage": edge_percentage,
            "recommendation": recommendation,
            "bet_type": bet_type,
            "confidence": adjusted_confidence,
            "reasoning": self._generate_reasoning(matchup, prediction, edge)
        }

    def _generate_reasoning(
        self,
        matchup: MatchupContext,
        prediction: PacePrediction,
        edge: float
    ) -> str:
        """Generate human-readable reasoning for the prediction"""
        lines = []

        # Pace analysis
        home_pace = matchup.home_team.pace
        away_pace = matchup.away_team.pace
        pace_diff = abs(home_pace - away_pace)

        if pace_diff >= self.pace_mismatch_threshold:
            faster_team = matchup.home_team.team_name if home_pace > away_pace else matchup.away_team.team_name
            lines.append(f"Significant pace mismatch: {faster_team} plays {pace_diff:.1f} possessions faster")

        # Rest situation
        if matchup.home_team.back_to_back or matchup.away_team.back_to_back:
            teams = []
            if matchup.home_team.back_to_back:
                teams.append(matchup.home_team.team_name)
            if matchup.away_team.back_to_back:
                teams.append(matchup.away_team.team_name)
            lines.append(f"Back-to-back situation: {', '.join(teams)} on B2B (expect slower pace)")

        rest_diff = matchup.home_team.rest_days - matchup.away_team.rest_days
        if abs(rest_diff) >= 2:
            rested_team = matchup.home_team.team_name if rest_diff > 0 else matchup.away_team.team_name
            lines.append(f"{rested_team} has {abs(rest_diff)} day rest advantage")

        # Pace prediction
        lines.append(f"Expected pace: {prediction.predicted_pace:.1f} possessions")
        lines.append(f"Pace scenario: {prediction.scenario}")

        # Edge explanation
        if abs(edge) >= 5.0:
            lines.append(f"STRONG edge: {edge:+.1f} points from market")
        elif abs(edge) >= 3.0:
            lines.append(f"Moderate edge: {edge:+.1f} points from market")

        return " | ".join(lines)


# Example usage
if __name__ == "__main__":
    # Initialize strategy
    strategy = PaceBasedStrategy(
        rest_day_boost=1.5,
        back_to_back_penalty=-3.0,
        home_tempo_control=0.6
    )

    # Example matchup: Fast pace team vs slow pace team
    matchup = MatchupContext(
        home_team=TeamStats(
            team_name="Warriors",
            pace=102.5,  # Fast pace
            off_rating=118.0,
            def_rating=112.0,
            rest_days=2,
            back_to_back=False
        ),
        away_team=TeamStats(
            team_name="Grizzlies",
            pace=95.0,  # Slow pace
            off_rating=115.0,
            def_rating=110.0,
            rest_days=0,  # No rest
            back_to_back=True  # On back-to-back
        ),
        league_avg_pace=100.0,
        league_avg_rating=112.0,
        home_court_advantage=2.5
    )

    # Analyze
    market_total = 225.5
    analysis = strategy.analyze_total_opportunity(matchup, market_total)

    # Print results
    print("="*70)
    print(f"PACE-BASED ANALYSIS: {matchup.home_team.team_name} vs {matchup.away_team.team_name}")
    print("="*70)
    print(f"\nMarket Total: {market_total}")
    print(f"Predicted Total: {analysis['predicted_total']:.1f}")
    print(f"Edge: {analysis['edge']:+.1f} ({analysis['edge_percentage']:+.1f}%)")
    print(f"\nRecommendation: {analysis['recommendation']}")
    print(f"Confidence: {analysis['confidence']:.2f}")
    print(f"\nPredicted Score: {matchup.home_team.team_name} {analysis['prediction'].home_expected_points:.1f}, "
          f"{matchup.away_team.team_name} {analysis['prediction'].away_expected_points:.1f}")
    print(f"Expected Pace: {analysis['prediction'].predicted_pace:.1f}")
    print(f"Scenario: {analysis['prediction'].scenario}")
    print(f"\nReasoning: {analysis['reasoning']}")
    print("="*70)
