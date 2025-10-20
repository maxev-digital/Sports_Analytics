"""
Fatigue Strategy Engine
Detects EV opportunities based on team fatigue, travel, and schedule factors
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
import numpy as np


@dataclass
class ScheduleContext:
    """Schedule and travel context for a team"""
    team_name: str
    rest_days: int  # Days since last game
    back_to_back: bool  # Playing on consecutive days
    three_in_four: bool  # 3 games in 4 nights
    four_in_five: bool  # 4 games in 5 nights
    miles_traveled: float  # Miles traveled since last game
    time_zone_changes: int  # Time zones crossed
    home_game: bool  # Is this a home game
    games_last_7_days: int  # Games played in last 7 days
    games_last_14_days: int  # Games played in last 14 days
    avg_minutes_starters: Optional[float] = None  # Avg minutes for starters last 5 games
    injury_count: int = 0  # Number of key players injured/questionable


@dataclass
class FatiguePrediction:
    """Prediction output from fatigue analysis"""
    fatigue_score: float  # 0-100, higher = more fatigued
    pace_adjustment: float  # Expected pace change due to fatigue
    scoring_adjustment: float  # Expected scoring change due to fatigue
    defensive_impact: float  # Impact on defensive rating
    confidence: float  # 0-1 scale
    risk_factors: list[str]  # List of fatigue risk factors
    advantages: list[str]  # List of advantages if opponent is more fatigued


class FatigueStrategy:
    """
    Strategy that identifies EV opportunities based on fatigue analysis

    Key Concepts:
    - Back-to-backs significantly reduce performance
    - Travel fatigue compounds with schedule density
    - West-to-East travel is harder than East-to-West
    - Road trips of 3+ games create cumulative fatigue
    - High minutes for starters indicates fatigue risk
    """

    def __init__(
        self,
        b2b_pace_penalty: float = -3.0,  # Pace decrease on back-to-back
        b2b_scoring_penalty: float = -2.5,  # Points decrease on back-to-back
        travel_fatigue_threshold: float = 2000.0,  # Miles to trigger fatigue
        time_zone_penalty: float = -1.0,  # Per time zone crossed
        dense_schedule_threshold: int = 4,  # Games in 7 days for "dense"
        high_minutes_threshold: float = 36.0,  # Minutes per game for starters
    ):
        """
        Initialize Fatigue Strategy

        Args:
            b2b_pace_penalty: Pace decrease for back-to-back games
            b2b_scoring_penalty: Scoring decrease for back-to-back games
            travel_fatigue_threshold: Miles traveled to trigger fatigue penalty
            time_zone_penalty: Penalty per time zone crossed
            dense_schedule_threshold: Games in 7 days to be considered dense
            high_minutes_threshold: Minutes per game indicating fatigue risk
        """
        self.b2b_pace_penalty = b2b_pace_penalty
        self.b2b_scoring_penalty = b2b_scoring_penalty
        self.travel_fatigue_threshold = travel_fatigue_threshold
        self.time_zone_penalty = time_zone_penalty
        self.dense_schedule_threshold = dense_schedule_threshold
        self.high_minutes_threshold = high_minutes_threshold

    def calculate_fatigue_score(self, schedule: ScheduleContext) -> float:
        """
        Calculate overall fatigue score (0-100)

        Args:
            schedule: ScheduleContext for the team

        Returns:
            Fatigue score where 0 = fully rested, 100 = extremely fatigued
        """
        fatigue = 0.0

        # Rest days factor (most important)
        if schedule.back_to_back:
            fatigue += 30.0
        elif schedule.rest_days == 1:
            fatigue += 15.0
        elif schedule.rest_days >= 3:
            fatigue -= 10.0  # Well rested

        # Schedule density
        if schedule.four_in_five:
            fatigue += 25.0
        elif schedule.three_in_four:
            fatigue += 15.0

        if schedule.games_last_7_days >= self.dense_schedule_threshold:
            fatigue += 10.0

        # Travel fatigue
        if schedule.miles_traveled >= self.travel_fatigue_threshold:
            travel_factor = min((schedule.miles_traveled / 1000.0), 5.0)
            fatigue += travel_factor * 3.0  # Up to 15 points

        # Time zone changes (especially West to East)
        if schedule.time_zone_changes > 0:
            fatigue += abs(schedule.time_zone_changes) * 5.0

        # Home vs away
        if not schedule.home_game:
            fatigue += 5.0  # Road games are inherently more tiring

        # Minutes played by starters
        if schedule.avg_minutes_starters and schedule.avg_minutes_starters >= self.high_minutes_threshold:
            minutes_factor = (schedule.avg_minutes_starters - 35.0) / 5.0
            fatigue += minutes_factor * 8.0

        # Injury situation
        fatigue += schedule.injury_count * 3.0

        return min(fatigue, 100.0)

    def calculate_pace_impact(self, fatigue_score: float) -> float:
        """
        Calculate expected pace adjustment based on fatigue

        Args:
            fatigue_score: Fatigue score (0-100)

        Returns:
            Pace adjustment (negative for slower)
        """
        # Fatigue slows down pace
        # Linear relationship: 50 fatigue = -2.5 pace, 100 fatigue = -5 pace
        pace_impact = -(fatigue_score / 20.0)
        return pace_impact

    def calculate_scoring_impact(self, fatigue_score: float) -> float:
        """
        Calculate expected scoring adjustment based on fatigue

        Args:
            fatigue_score: Fatigue score (0-100)

        Returns:
            Scoring adjustment (negative for lower scoring)
        """
        # Fatigue reduces offensive efficiency
        # Non-linear: fatigue compounds
        base_impact = -(fatigue_score / 25.0)

        # Extreme fatigue has exponential impact
        if fatigue_score > 70:
            base_impact *= 1.3

        return base_impact

    def calculate_defensive_impact(self, fatigue_score: float) -> float:
        """
        Calculate expected defensive rating impact based on fatigue

        Args:
            fatigue_score: Fatigue score (0-100)

        Returns:
            Defensive rating adjustment (positive = worse defense)
        """
        # Fatigue hurts defense more than offense
        # Tired teams give up more points
        defensive_impact = (fatigue_score / 15.0)

        # Extreme fatigue has larger defensive breakdown
        if fatigue_score > 70:
            defensive_impact *= 1.5

        return defensive_impact

    def identify_risk_factors(self, schedule: ScheduleContext) -> list[str]:
        """Identify key fatigue risk factors"""
        risks = []

        if schedule.back_to_back:
            risks.append("BACK-TO-BACK")

        if schedule.three_in_four:
            risks.append("3-IN-4 NIGHTS")

        if schedule.four_in_five:
            risks.append("4-IN-5 NIGHTS")

        if schedule.miles_traveled >= self.travel_fatigue_threshold:
            risks.append(f"LONG TRAVEL ({schedule.miles_traveled:.0f} miles)")

        if schedule.time_zone_changes >= 2:
            risks.append(f"TIME ZONES ({schedule.time_zone_changes} zones)")

        if schedule.games_last_7_days >= self.dense_schedule_threshold:
            risks.append(f"DENSE SCHEDULE ({schedule.games_last_7_days} in 7 days)")

        if schedule.avg_minutes_starters and schedule.avg_minutes_starters >= self.high_minutes_threshold:
            risks.append(f"HIGH MINUTES ({schedule.avg_minutes_starters:.1f} MPG)")

        if schedule.injury_count > 0:
            risks.append(f"INJURIES ({schedule.injury_count} players)")

        return risks

    def identify_advantages(self, schedule: ScheduleContext) -> list[str]:
        """Identify advantages (well-rested situations)"""
        advantages = []

        if schedule.rest_days >= 3:
            advantages.append(f"WELL RESTED ({schedule.rest_days} days)")

        if schedule.home_game:
            advantages.append("HOME GAME")

        if schedule.games_last_7_days <= 2:
            advantages.append("LIGHT SCHEDULE")

        if schedule.miles_traveled < 500:
            advantages.append("MINIMAL TRAVEL")

        return advantages

    def predict(self, schedule: ScheduleContext) -> FatiguePrediction:
        """
        Generate fatigue prediction for a team

        Args:
            schedule: ScheduleContext for the team

        Returns:
            FatiguePrediction with all fatigue impacts
        """
        # Calculate fatigue score
        fatigue_score = self.calculate_fatigue_score(schedule)

        # Calculate impacts
        pace_adjustment = self.calculate_pace_impact(fatigue_score)
        scoring_adjustment = self.calculate_scoring_impact(fatigue_score)
        defensive_impact = self.calculate_defensive_impact(fatigue_score)

        # Identify factors
        risk_factors = self.identify_risk_factors(schedule)
        advantages = self.identify_advantages(schedule)

        # Calculate confidence
        # Higher confidence when there are clear risk factors
        confidence = min(0.3 + (len(risk_factors) * 0.15), 1.0)

        return FatiguePrediction(
            fatigue_score=fatigue_score,
            pace_adjustment=pace_adjustment,
            scoring_adjustment=scoring_adjustment,
            defensive_impact=defensive_impact,
            confidence=confidence,
            risk_factors=risk_factors,
            advantages=advantages
        )

    def analyze_matchup(
        self,
        home_schedule: ScheduleContext,
        away_schedule: ScheduleContext
    ) -> dict:
        """
        Analyze fatigue matchup between two teams

        Args:
            home_schedule: Schedule context for home team
            away_schedule: Schedule context for away team

        Returns:
            Dictionary with comparative analysis
        """
        home_pred = self.predict(home_schedule)
        away_pred = self.predict(away_schedule)

        # Calculate fatigue differential
        fatigue_differential = away_pred.fatigue_score - home_pred.fatigue_score

        # Determine if there's an exploitable edge
        if abs(fatigue_differential) < 20:
            edge_type = "MINIMAL"
            recommended_bet = None
        elif fatigue_differential > 20:
            edge_type = "AWAY_FATIGUED"
            recommended_bet = "home_team"  # Bet on home team
        else:
            edge_type = "HOME_FATIGUED"
            recommended_bet = "away_team"  # Bet on away team

        # Calculate expected total impact
        total_pace_impact = home_pred.pace_adjustment + away_pred.pace_adjustment
        total_scoring_impact = home_pred.scoring_adjustment + away_pred.scoring_adjustment

        # Estimate total adjustment
        # More fatigued teams = lower total
        total_adjustment = (total_pace_impact * 0.5) + total_scoring_impact

        return {
            "home_prediction": home_pred,
            "away_prediction": away_pred,
            "fatigue_differential": fatigue_differential,
            "edge_type": edge_type,
            "recommended_bet": recommended_bet,
            "total_adjustment": total_adjustment,
            "pace_impact": total_pace_impact,
            "reasoning": self._generate_reasoning(
                home_schedule,
                away_schedule,
                home_pred,
                away_pred,
                fatigue_differential
            )
        }

    def _generate_reasoning(
        self,
        home_schedule: ScheduleContext,
        away_schedule: ScheduleContext,
        home_pred: FatiguePrediction,
        away_pred: FatiguePrediction,
        differential: float
    ) -> str:
        """Generate human-readable reasoning"""
        lines = []

        # Home team analysis
        if home_pred.risk_factors:
            lines.append(f"{home_schedule.team_name} risks: {', '.join(home_pred.risk_factors)}")
        if home_pred.advantages:
            lines.append(f"{home_schedule.team_name} advantages: {', '.join(home_pred.advantages)}")

        # Away team analysis
        if away_pred.risk_factors:
            lines.append(f"{away_schedule.team_name} risks: {', '.join(away_pred.risk_factors)}")
        if away_pred.advantages:
            lines.append(f"{away_schedule.team_name} advantages: {', '.join(away_pred.advantages)}")

        # Differential analysis
        if abs(differential) >= 20:
            more_fatigued = away_schedule.team_name if differential > 0 else home_schedule.team_name
            lines.append(f"SIGNIFICANT FATIGUE EDGE: {more_fatigued} at {abs(differential):.0f} fatigue differential")

        return " | ".join(lines)


# Example usage
if __name__ == "__main__":
    # Initialize strategy
    strategy = FatigueStrategy()

    # Example: Home team well-rested, away team on brutal road trip
    home_schedule = ScheduleContext(
        team_name="Lakers",
        rest_days=2,
        back_to_back=False,
        three_in_four=False,
        four_in_five=False,
        miles_traveled=0,  # Home game, no travel
        time_zone_changes=0,
        home_game=True,
        games_last_7_days=3,
        games_last_14_days=5,
        avg_minutes_starters=34.5,
        injury_count=0
    )

    away_schedule = ScheduleContext(
        team_name="Celtics",
        rest_days=0,  # Back-to-back
        back_to_back=True,
        three_in_four=True,
        four_in_five=False,
        miles_traveled=2800,  # Boston to LA
        time_zone_changes=3,  # EST to PST
        home_game=False,
        games_last_7_days=5,
        games_last_14_days=8,
        avg_minutes_starters=37.2,
        injury_count=1
    )

    # Analyze matchup
    analysis = strategy.analyze_matchup(home_schedule, away_schedule)

    # Print results
    print("="*70)
    print(f"FATIGUE ANALYSIS: {home_schedule.team_name} vs {away_schedule.team_name}")
    print("="*70)

    print(f"\n{home_schedule.team_name} (Home):")
    print(f"  Fatigue Score: {analysis['home_prediction'].fatigue_score:.1f}/100")
    print(f"  Pace Impact: {analysis['home_prediction'].pace_adjustment:+.1f}")
    print(f"  Scoring Impact: {analysis['home_prediction'].scoring_adjustment:+.1f}")
    print(f"  Risk Factors: {', '.join(analysis['home_prediction'].risk_factors) if analysis['home_prediction'].risk_factors else 'None'}")
    print(f"  Advantages: {', '.join(analysis['home_prediction'].advantages) if analysis['home_prediction'].advantages else 'None'}")

    print(f"\n{away_schedule.team_name} (Away):")
    print(f"  Fatigue Score: {analysis['away_prediction'].fatigue_score:.1f}/100")
    print(f"  Pace Impact: {analysis['away_prediction'].pace_adjustment:+.1f}")
    print(f"  Scoring Impact: {analysis['away_prediction'].scoring_adjustment:+.1f}")
    print(f"  Risk Factors: {', '.join(analysis['away_prediction'].risk_factors) if analysis['away_prediction'].risk_factors else 'None'}")
    print(f"  Advantages: {', '.join(analysis['away_prediction'].advantages) if analysis['away_prediction'].advantages else 'None'}")

    print(f"\nFatigue Differential: {analysis['fatigue_differential']:+.1f}")
    print(f"Edge Type: {analysis['edge_type']}")
    print(f"Recommended Bet: {analysis['recommended_bet']}")
    print(f"Expected Total Adjustment: {analysis['total_adjustment']:+.1f} points")
    print(f"\nReasoning: {analysis['reasoning']}")
    print("="*70)
