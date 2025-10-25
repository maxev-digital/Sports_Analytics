"""
Regression Strategy Engine
Detects EV opportunities based on mean reversion and statistical regression principles
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class PerformanceHistory:
    """Historical performance data for regression analysis"""
    team_name: str
    season_avg_points: float  # Season average points scored
    season_avg_allowed: float  # Season average points allowed
    last_5_avg_points: float  # Last 5 games average points
    last_5_avg_allowed: float  # Last 5 games average allowed
    last_10_avg_points: float  # Last 10 games average points
    last_10_avg_allowed: float  # Last 10 games average allowed
    shooting_pct_season: float  # FG% season average
    shooting_pct_last_5: float  # FG% last 5 games
    three_pt_pct_season: float  # 3PT% season average
    three_pt_pct_last_5: float  # 3PT% last 5 games
    opponent_shooting_pct_season: float  # Opp FG% season average
    opponent_shooting_pct_last_5: float  # Opp FG% last 5 games
    streak_type: Optional[str] = None  # 'winning', 'losing', or None
    streak_length: int = 0  # Length of current streak
    vs_opponent_last_3_avg: Optional[float] = None  # Avg vs this opponent last 3 games


@dataclass
class RegressionPrediction:
    """Prediction output from regression analysis"""
    expected_points: float  # Regression-adjusted expected points
    expected_allowed: float  # Regression-adjusted expected points allowed
    offensive_regression_factor: float  # How much offense should regress
    defensive_regression_factor: float  # How much defense should regress
    shooting_regression: float  # Expected shooting percentage correction
    confidence: float  # 0-1 scale
    regression_signals: list[str]  # Regression indicators
    over_performing: bool  # Is team currently over-performing expectations
    under_performing: bool  # Is team currently under-performing expectations


class RegressionStrategy:
    """
    Strategy that identifies EV opportunities based on mean reversion

    Key Concepts:
    - Teams shooting unsustainably hot/cold will regress to mean
    - Winning/losing streaks tend to reverse
    - Recent performance that deviates significantly from season average
    - Opponent-specific performance anomalies
    - Law of large numbers applies to shooting percentages
    """

    def __init__(
        self,
        regression_strength: float = 0.6,  # Weight toward season avg (0-1)
        recent_weight: float = 0.4,  # Weight toward recent performance
        shooting_regression_threshold: float = 0.04,  # 4% deviation triggers regression
        streak_regression_threshold: int = 4,  # Streaks of 4+ trigger regression
        confidence_multiplier: float = 1.0,
    ):
        """
        Initialize Regression Strategy

        Args:
            regression_strength: How strongly to regress toward season mean (higher = more regression)
            recent_weight: Weight given to recent performance vs season average
            shooting_regression_threshold: Shooting % deviation to trigger regression signal
            streak_regression_threshold: Streak length to trigger regression signal
            confidence_multiplier: Adjust overall confidence in predictions
        """
        self.regression_strength = regression_strength
        self.recent_weight = recent_weight
        self.shooting_regression_threshold = shooting_regression_threshold
        self.streak_regression_threshold = streak_regression_threshold
        self.confidence_multiplier = confidence_multiplier

    def calculate_regression_factor(
        self,
        recent_value: float,
        season_value: float,
        sample_size_weight: float = 1.0
    ) -> float:
        """
        Calculate how much a metric should regress toward the mean

        Args:
            recent_value: Recent performance metric
            season_value: Season average metric
            sample_size_weight: Adjustment for sample size (larger sample = less regression)

        Returns:
            Regression factor (higher = more regression needed)
        """
        deviation = abs(recent_value - season_value)
        relative_deviation = deviation / season_value if season_value > 0 else 0

        # More extreme deviations = stronger regression
        regression_factor = relative_deviation * self.regression_strength * sample_size_weight

        return min(regression_factor, 1.0)

    def calculate_expected_points(
        self,
        history: PerformanceHistory
    ) -> tuple[float, float, list[str]]:
        """
        Calculate expected points accounting for regression to mean

        Args:
            history: PerformanceHistory object

        Returns:
            (expected_points, offensive_regression_factor, regression_signals)
        """
        signals = []

        # Calculate how much recent differs from season
        points_deviation = history.last_5_avg_points - history.season_avg_points
        relative_deviation = (points_deviation / history.season_avg_points) if history.season_avg_points > 0 else 0

        # Determine regression factor
        if abs(relative_deviation) > 0.10:  # 10% deviation
            regression_factor = self.calculate_regression_factor(
                history.last_5_avg_points,
                history.season_avg_points,
                sample_size_weight=0.9  # Last 5 is small sample
            )

            if history.last_5_avg_points > history.season_avg_points:
                signals.append(f"OFFENSE_HOT (due for regression: {points_deviation:+.1f} PPG)")
            else:
                signals.append(f"OFFENSE_COLD (due for bounce-back: {points_deviation:+.1f} PPG)")
        else:
            regression_factor = 0.3  # Mild regression

        # Weighted combination: recent performance + season average
        expected_points = (
            history.last_5_avg_points * (1 - regression_factor) +
            history.season_avg_points * regression_factor
        )

        # Check shooting regression
        shooting_dev = history.shooting_pct_last_5 - history.shooting_pct_season
        if abs(shooting_dev) >= self.shooting_regression_threshold:
            if shooting_dev > 0:
                signals.append(f"SHOOTING_HOT ({history.shooting_pct_last_5:.1%} vs {history.shooting_pct_season:.1%})")
                # Adjust expected points down slightly
                expected_points *= 0.97
            else:
                signals.append(f"SHOOTING_COLD ({history.shooting_pct_last_5:.1%} vs {history.shooting_pct_season:.1%})")
                # Adjust expected points up slightly
                expected_points *= 1.03

        # Check three-point shooting regression
        three_dev = history.three_pt_pct_last_5 - history.three_pt_pct_season
        if abs(three_dev) >= self.shooting_regression_threshold:
            if three_dev > 0:
                signals.append(f"3PT_HOT ({history.three_pt_pct_last_5:.1%} vs {history.three_pt_pct_season:.1%})")
                expected_points *= 0.98
            else:
                signals.append(f"3PT_COLD ({history.three_pt_pct_last_5:.1%} vs {history.three_pt_pct_season:.1%})")
                expected_points *= 1.02

        return expected_points, regression_factor, signals

    def calculate_expected_defense(
        self,
        history: PerformanceHistory
    ) -> tuple[float, float, list[str]]:
        """
        Calculate expected points allowed accounting for regression

        Args:
            history: PerformanceHistory object

        Returns:
            (expected_allowed, defensive_regression_factor, regression_signals)
        """
        signals = []

        # Calculate defensive deviation
        defense_deviation = history.last_5_avg_allowed - history.season_avg_allowed
        relative_deviation = (defense_deviation / history.season_avg_allowed) if history.season_avg_allowed > 0 else 0

        # Determine regression factor
        if abs(relative_deviation) > 0.10:
            regression_factor = self.calculate_regression_factor(
                history.last_5_avg_allowed,
                history.season_avg_allowed,
                sample_size_weight=0.9
            )

            if history.last_5_avg_allowed < history.season_avg_allowed:
                signals.append(f"DEFENSE_HOT (due for regression: {defense_deviation:+.1f} PPG)")
            else:
                signals.append(f"DEFENSE_COLD (due for improvement: {defense_deviation:+.1f} PPG)")
        else:
            regression_factor = 0.3

        # Weighted combination
        expected_allowed = (
            history.last_5_avg_allowed * (1 - regression_factor) +
            history.season_avg_allowed * regression_factor
        )

        # Check opponent shooting regression
        opp_shooting_dev = history.opponent_shooting_pct_last_5 - history.opponent_shooting_pct_season
        if abs(opp_shooting_dev) >= self.shooting_regression_threshold:
            if opp_shooting_dev > 0:
                signals.append(f"OPP_SHOOTING_HOT (opponents due for regression)")
                # Opponents shooting hot, expect regression (fewer points allowed)
                expected_allowed *= 0.97
            else:
                signals.append(f"OPP_SHOOTING_COLD (opponents due for bounce-back)")
                # Opponents shooting cold, expect bounce-back (more points allowed)
                expected_allowed *= 1.03

        return expected_allowed, regression_factor, signals

    def analyze_streak(self, history: PerformanceHistory) -> tuple[float, list[str]]:
        """
        Analyze winning/losing streaks for regression signals

        Args:
            history: PerformanceHistory object

        Returns:
            (confidence_adjustment, signals)
        """
        signals = []
        confidence_adj = 0.0

        if history.streak_length >= self.streak_regression_threshold:
            if history.streak_type == 'winning':
                signals.append(f"LONG_WIN_STREAK ({history.streak_length} games - regression risk)")
                confidence_adj = 0.15  # Higher confidence in regression
            elif history.streak_type == 'losing':
                signals.append(f"LONG_LOSE_STREAK ({history.streak_length} games - bounce-back expected)")
                confidence_adj = 0.15

        return confidence_adj, signals

    def predict(self, history: PerformanceHistory) -> RegressionPrediction:
        """
        Generate regression-based prediction for a team

        Args:
            history: PerformanceHistory object

        Returns:
            RegressionPrediction with expected performance
        """
        # Calculate expected points (offensive)
        expected_points, off_regression, off_signals = self.calculate_expected_points(history)

        # Calculate expected defense
        expected_allowed, def_regression, def_signals = self.calculate_expected_defense(history)

        # Analyze streaks
        streak_confidence, streak_signals = self.analyze_streak(history)

        # Combine all signals
        all_signals = off_signals + def_signals + streak_signals

        # Calculate shooting regression
        shooting_regression = (
            (history.shooting_pct_season - history.shooting_pct_last_5) +
            (history.three_pt_pct_season - history.three_pt_pct_last_5)
        ) / 2

        # Determine over/under performing
        over_performing = (
            history.last_5_avg_points > history.season_avg_points * 1.08 or
            history.shooting_pct_last_5 > history.shooting_pct_season + self.shooting_regression_threshold
        )

        under_performing = (
            history.last_5_avg_points < history.season_avg_points * 0.92 or
            history.shooting_pct_last_5 < history.shooting_pct_season - self.shooting_regression_threshold
        )

        # Calculate confidence
        base_confidence = 0.4
        signal_confidence = min(len(all_signals) * 0.10, 0.4)
        confidence = (base_confidence + signal_confidence + streak_confidence) * self.confidence_multiplier
        confidence = min(confidence, 1.0)

        return RegressionPrediction(
            expected_points=expected_points,
            expected_allowed=expected_allowed,
            offensive_regression_factor=off_regression,
            defensive_regression_factor=def_regression,
            shooting_regression=shooting_regression,
            confidence=confidence,
            regression_signals=all_signals,
            over_performing=over_performing,
            under_performing=under_performing
        )

    def analyze_matchup(
        self,
        home_history: PerformanceHistory,
        away_history: PerformanceHistory,
        market_total: Optional[float] = None
    ) -> dict:
        """
        Analyze regression factors for a matchup

        Args:
            home_history: Performance history for home team
            away_history: Performance history for away team
            market_total: Current betting total (optional)

        Returns:
            Dictionary with complete regression analysis
        """
        home_pred = self.predict(home_history)
        away_pred = self.predict(away_history)

        # Calculate expected total
        expected_total = home_pred.expected_points + away_pred.expected_allowed / 2 + \
                        away_pred.expected_points + home_pred.expected_allowed / 2

        # Determine regression direction
        if home_pred.over_performing and away_pred.over_performing:
            regression_direction = "BOTH_OVER (expect lower total)"
            total_adjustment = -3.0
        elif home_pred.under_performing and away_pred.under_performing:
            regression_direction = "BOTH_UNDER (expect higher total)"
            total_adjustment = +3.0
        elif home_pred.over_performing or away_pred.over_performing:
            regression_direction = "ONE_OVER (slight downward pressure)"
            total_adjustment = -1.5
        elif home_pred.under_performing or away_pred.under_performing:
            regression_direction = "ONE_UNDER (slight upward pressure)"
            total_adjustment = +1.5
        else:
            regression_direction = "BALANCED"
            total_adjustment = 0.0

        # Calculate edge if market total provided
        edge = None
        recommendation = None
        if market_total:
            adjusted_expected = expected_total + total_adjustment
            edge = adjusted_expected - market_total

            if abs(edge) >= 4.0:
                recommendation = "OVER" if edge > 0 else "UNDER"
            elif abs(edge) >= 2.0:
                recommendation = "LEAN_OVER" if edge > 0 else "LEAN_UNDER"
            else:
                recommendation = "PASS"

        # Combined confidence
        combined_confidence = (home_pred.confidence + away_pred.confidence) / 2

        return {
            "home_prediction": home_pred,
            "away_prediction": away_pred,
            "expected_total": expected_total,
            "adjusted_expected_total": expected_total + total_adjustment,
            "regression_direction": regression_direction,
            "total_adjustment": total_adjustment,
            "market_total": market_total,
            "edge": edge,
            "recommendation": recommendation,
            "confidence": combined_confidence,
            "reasoning": self._generate_reasoning(
                home_history,
                away_history,
                home_pred,
                away_pred,
                regression_direction
            )
        }

    def _generate_reasoning(
        self,
        home_history: PerformanceHistory,
        away_history: PerformanceHistory,
        home_pred: RegressionPrediction,
        away_pred: RegressionPrediction,
        direction: str
    ) -> str:
        """Generate human-readable reasoning"""
        lines = []

        # Home signals
        if home_pred.regression_signals:
            lines.append(f"{home_history.team_name}: {', '.join(home_pred.regression_signals)}")

        # Away signals
        if away_pred.regression_signals:
            lines.append(f"{away_history.team_name}: {', '.join(away_pred.regression_signals)}")

        # Overall direction
        lines.append(f"Regression Direction: {direction}")

        return " | ".join(lines)


# Example usage
if __name__ == "__main__":
    # Initialize strategy
    strategy = RegressionStrategy(
        regression_strength=0.6,
        recent_weight=0.4
    )

    # Example: Home team shooting hot, away team in losing streak
    home_history = PerformanceHistory(
        team_name="Warriors",
        season_avg_points=115.0,
        season_avg_allowed=110.0,
        last_5_avg_points=125.0,  # Hot streak
        last_5_avg_allowed=108.0,
        last_10_avg_points=120.0,
        last_10_avg_allowed=109.0,
        shooting_pct_season=0.475,
        shooting_pct_last_5=0.520,  # Shooting hot
        three_pt_pct_season=0.365,
        three_pt_pct_last_5=0.420,  # 3PT hot
        opponent_shooting_pct_season=0.465,
        opponent_shooting_pct_last_5=0.450,
        streak_type='winning',
        streak_length=6
    )

    away_history = PerformanceHistory(
        team_name="Lakers",
        season_avg_points=112.0,
        season_avg_allowed=108.0,
        last_5_avg_points=105.0,  # Cold streak
        last_5_avg_allowed=115.0,  # Defense struggling
        last_10_avg_points=108.0,
        last_10_avg_allowed=112.0,
        shooting_pct_season=0.470,
        shooting_pct_last_5=0.430,  # Shooting cold
        three_pt_pct_season=0.360,
        three_pt_pct_last_5=0.310,  # 3PT cold
        opponent_shooting_pct_season=0.460,
        opponent_shooting_pct_last_5=0.490,  # Opponents hot
        streak_type='losing',
        streak_length=4
    )

    # Analyze matchup
    market_total = 230.5
    analysis = strategy.analyze_matchup(home_history, away_history, market_total)

    # Print results
    print("="*70)
    print(f"REGRESSION ANALYSIS: {home_history.team_name} vs {away_history.team_name}")
    print("="*70)

    print(f"\n{home_history.team_name}:")
    print(f"  Expected Points: {analysis['home_prediction'].expected_points:.1f}")
    print(f"  Expected Allowed: {analysis['home_prediction'].expected_allowed:.1f}")
    print(f"  Over-performing: {analysis['home_prediction'].over_performing}")
    print(f"  Signals: {', '.join(analysis['home_prediction'].regression_signals)}")

    print(f"\n{away_history.team_name}:")
    print(f"  Expected Points: {analysis['away_prediction'].expected_points:.1f}")
    print(f"  Expected Allowed: {analysis['away_prediction'].expected_allowed:.1f}")
    print(f"  Under-performing: {analysis['away_prediction'].under_performing}")
    print(f"  Signals: {', '.join(analysis['away_prediction'].regression_signals)}")

    print(f"\nExpected Total: {analysis['expected_total']:.1f}")
    print(f"Adjusted Expected: {analysis['adjusted_expected_total']:.1f}")
    print(f"Market Total: {market_total}")
    print(f"Edge: {analysis['edge']:+.1f}")
    print(f"Recommendation: {analysis['recommendation']}")
    print(f"Confidence: {analysis['confidence']:.2f}")
    print(f"\nReasoning: {analysis['reasoning']}")
    print("="*70)
