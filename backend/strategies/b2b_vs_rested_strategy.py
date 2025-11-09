"""
Back-to-Back vs Rested Strategy
Fades teams on back-to-back games against fully rested opponents

Historical Edges:
- NBA: 58% ATS fade B2B vs 3+ days rest (2015-2024)
- NHL: 55% fade B2B vs 3+ days rest
- NFL: N/A (no back-to-backs)

Key Factors:
- Physical fatigue (2nd game in 24 hours)
- Travel fatigue (especially cross-country)
- Mental fatigue (focus and energy)
- Injury accumulation
- Rotation changes (stars get less minutes)
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class TeamSchedule:
    """Team schedule information"""
    team_name: str
    games_last_7_days: int
    rest_days: int  # Days since last game
    is_back_to_back: bool
    is_rested: bool  # 3+ days rest
    travel_distance: Optional[float] = None  # Miles traveled (if available)
    games_in_next_7_days: int = 0


@dataclass
class B2BOpportunity:
    """B2B vs Rested betting opportunity"""
    game_id: str
    sport: str
    fatigued_team: str
    rested_team: str
    home_team: str
    away_team: str
    fatigued_rest_days: int
    rested_rest_days: int
    rest_differential: int
    recommendation: str  # "FADE_HOME" or "FADE_AWAY" (bet against fatigued team)
    confidence: float  # 0-1
    confidence_level: str  # HIGH/MEDIUM/LOW
    edge_estimate: float  # Expected edge in points/goals
    key_factors: List[str]
    reasoning: str
    spread: Optional[float] = None
    market_line: Optional[float] = None


class B2BVsRestedStrategy:
    """
    Strategy for identifying value when fatigued teams face rested opponents

    Core Logic:
    - B2B teams (0 days rest) face significant fatigue
    - Opponents with 3+ days rest have physical & mental advantage
    - Edge increases with:
      1. Greater rest differential (B2B vs 4+ days)
      2. Travel distance
      3. Star player minutes restrictions
      4. Division games (more intense)
    """

    # Historical win rates (B2B team)
    B2B_WIN_RATE_NBA = 0.42  # 42% straight up
    B2B_ATS_RATE_NBA = 0.42  # 42% ATS
    B2B_WIN_RATE_NHL = 0.45  # 45% straight up

    # Edge estimates (how much to adjust spread/ML)
    NBA_EDGE_PER_REST_DAY = 1.5  # Points per day of rest advantage
    NHL_EDGE_PER_REST_DAY = 0.35  # Goals per day of rest advantage

    def __init__(
        self,
        min_rest_differential: int = 2,  # Minimum 2 day difference
        nba_max_edge: float = 6.0,  # Cap NBA edge at 6 points
        nhl_max_edge: float = 1.5,  # Cap NHL edge at 1.5 goals
    ):
        self.min_rest_differential = min_rest_differential
        self.nba_max_edge = nba_max_edge
        self.nhl_max_edge = nhl_max_edge

    def analyze_matchup(
        self,
        game_id: str,
        sport: str,
        home_schedule: TeamSchedule,
        away_schedule: TeamSchedule,
        spread: Optional[float] = None,
        home_team: str = None,
        away_team: str = None
    ) -> Optional[B2BOpportunity]:
        """
        Analyze a game for B2B vs Rested opportunity

        Args:
            game_id: Unique game identifier
            sport: 'NBA' or 'NHL'
            home_schedule: Home team schedule info
            away_schedule: Away team schedule info
            spread: Current market spread
            home_team: Home team name
            away_team: Away team name

        Returns:
            B2BOpportunity if conditions met, None otherwise
        """
        # Check if one team is B2B and other is rested
        home_b2b = home_schedule.is_back_to_back
        away_b2b = away_schedule.is_back_to_back
        home_rested = home_schedule.is_rested
        away_rested = away_schedule.is_rested

        # Must have B2B vs Rested matchup
        if not ((home_b2b and away_rested) or (away_b2b and home_rested)):
            return None

        # Determine fatigued and rested teams
        if home_b2b:
            fatigued_team = home_team or "Home"
            rested_team = away_team or "Away"
            fatigued_rest = home_schedule.rest_days
            rested_rest = away_schedule.rest_days
            recommendation = "FADE_HOME"  # Bet against home (fade home spread, take away ML)
        else:
            fatigued_team = away_team or "Away"
            rested_team = home_team or "Home"
            fatigued_rest = away_schedule.rest_days
            rested_rest = home_schedule.rest_days
            recommendation = "FADE_AWAY"  # Bet against away

        # Calculate rest differential
        rest_diff = rested_rest - fatigued_rest

        # Must meet minimum rest differential
        if rest_diff < self.min_rest_differential:
            return None

        # Calculate edge and confidence
        edge_estimate, confidence, confidence_level = self._calculate_edge_and_confidence(
            sport=sport,
            rest_diff=rest_diff,
            fatigued_schedule=home_schedule if home_b2b else away_schedule,
            rested_schedule=away_schedule if home_b2b else home_schedule
        )

        # Generate key factors
        key_factors = self._generate_key_factors(
            sport,
            rest_diff,
            fatigued_team,
            rested_team,
            fatigued_schedule=home_schedule if home_b2b else away_schedule
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            sport,
            fatigued_team,
            rested_team,
            rest_diff,
            edge_estimate,
            key_factors
        )

        return B2BOpportunity(
            game_id=game_id,
            sport=sport,
            fatigued_team=fatigued_team,
            rested_team=rested_team,
            home_team=home_team or "Home",
            away_team=away_team or "Away",
            fatigued_rest_days=fatigued_rest,
            rested_rest_days=rested_rest,
            rest_differential=rest_diff,
            recommendation=recommendation,
            confidence=confidence,
            confidence_level=confidence_level,
            edge_estimate=edge_estimate,
            key_factors=key_factors,
            reasoning=reasoning,
            spread=spread,
            market_line=spread
        )

    def _calculate_edge_and_confidence(
        self,
        sport: str,
        rest_diff: int,
        fatigued_schedule: TeamSchedule,
        rested_schedule: TeamSchedule
    ) -> tuple[float, float, str]:
        """Calculate edge estimate and confidence"""

        # Base edge from rest differential
        if sport == 'NBA':
            base_edge = rest_diff * self.NBA_EDGE_PER_REST_DAY
            base_edge = min(base_edge, self.nba_max_edge)
        elif sport == 'NHL':
            base_edge = rest_diff * self.NHL_EDGE_PER_REST_DAY
            base_edge = min(base_edge, self.nhl_max_edge)
        else:
            base_edge = 0.0

        # Adjust for additional factors
        edge_multiplier = 1.0

        # Heavy game load increases fatigue
        if fatigued_schedule.games_last_7_days >= 4:
            edge_multiplier += 0.15  # +15% edge

        # Upcoming heavy schedule for fatigued team
        if fatigued_schedule.games_in_next_7_days >= 4:
            edge_multiplier += 0.10  # +10% edge (may rest stars)

        final_edge = base_edge * edge_multiplier

        # Calculate confidence
        base_confidence = 0.60  # Base confidence

        # Higher rest differential = more confidence
        if rest_diff >= 4:
            base_confidence += 0.20
        elif rest_diff >= 3:
            base_confidence += 0.15
        elif rest_diff >= 2:
            base_confidence += 0.10

        # Rested team has even more rest
        if rested_schedule.rest_days >= 5:
            base_confidence += 0.10

        confidence = min(base_confidence, 0.95)

        # Determine confidence level
        if confidence >= 0.80:
            confidence_level = 'HIGH'
        elif confidence >= 0.65:
            confidence_level = 'MEDIUM'
        else:
            confidence_level = 'LOW'

        return final_edge, confidence, confidence_level

    def _generate_key_factors(
        self,
        sport: str,
        rest_diff: int,
        fatigued_team: str,
        rested_team: str,
        fatigued_schedule: TeamSchedule
    ) -> List[str]:
        """Generate key factors for the opportunity"""
        factors = []

        # Rest differential
        factors.append(f"{rested_team} has {rest_diff} day rest advantage")

        # Back-to-back
        factors.append(f"{fatigued_team} on back-to-back (0 days rest)")

        # Heavy schedule
        if fatigued_schedule.games_last_7_days >= 4:
            factors.append(f"{fatigued_team} playing {fatigued_schedule.games_last_7_days} games in 7 days")

        # Historical edge
        if sport == 'NBA':
            factors.append(f"B2B teams are 42% ATS vs rested opponents (historical)")
        elif sport == 'NHL':
            factors.append(f"B2B teams are 45% win rate vs rested opponents")

        # Physical factors
        if rest_diff >= 3:
            factors.append("Significant physical and mental fatigue differential")

        return factors

    def _generate_reasoning(
        self,
        sport: str,
        fatigued_team: str,
        rested_team: str,
        rest_diff: int,
        edge: float,
        factors: List[str]
    ) -> str:
        """Generate human-readable reasoning"""
        reasoning_parts = []

        reasoning_parts.append(
            f"{fatigued_team} faces significant fatigue disadvantage against {rested_team}"
        )

        reasoning_parts.append(
            f"{rest_diff} day rest differential creates estimated {edge:.1f} "
            f"{'point' if sport == 'NBA' else 'goal'} edge"
        )

        reasoning_parts.append(
            f"Fade {fatigued_team} (bet against them on spread/ML)"
        )

        return " | ".join(reasoning_parts)


# Example usage
if __name__ == "__main__":
    strategy = B2BVsRestedStrategy()

    # Example NBA matchup: Lakers on B2B vs rested Warriors
    lakers_schedule = TeamSchedule(
        team_name="Lakers",
        games_last_7_days=4,
        rest_days=0,  # B2B
        is_back_to_back=True,
        is_rested=False,
        games_in_next_7_days=4
    )

    warriors_schedule = TeamSchedule(
        team_name="Warriors",
        games_last_7_days=3,
        rest_days=3,  # 3 days rest
        is_back_to_back=False,
        is_rested=True,
        games_in_next_7_days=3
    )

    opportunity = strategy.analyze_matchup(
        game_id="test_123",
        sport="NBA",
        home_schedule=lakers_schedule,
        away_schedule=warriors_schedule,
        spread=-3.5,
        home_team="Lakers",
        away_team="Warriors"
    )

    if opportunity:
        print("="*70)
        print("B2B VS RESTED OPPORTUNITY")
        print("="*70)
        print(f"Fatigued Team: {opportunity.fatigued_team}")
        print(f"Rested Team: {opportunity.rested_team}")
        print(f"Rest Differential: {opportunity.rest_differential} days")
        print(f"Recommendation: {opportunity.recommendation}")
        print(f"Edge Estimate: {opportunity.edge_estimate:.1f} points")
        print(f"Confidence: {opportunity.confidence_level} ({opportunity.confidence:.0%})")
        print(f"\nKey Factors:")
        for factor in opportunity.key_factors:
            print(f"  • {factor}")
        print(f"\nReasoning: {opportunity.reasoning}")
        print("="*70)
