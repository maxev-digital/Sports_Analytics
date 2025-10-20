"""
Live Betting Strategy Engine
Identifies value opportunities during live games by analyzing momentum, scoring runs, and odds movements
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime
import numpy as np


@dataclass
class LiveGameState:
    """Current state of a live game"""
    game_id: str
    sport: str
    home_team: str
    away_team: str

    # Score
    home_score: int
    away_score: int

    # Time
    period: int  # Quarter/Period/Inning
    time_remaining: float  # Minutes remaining in period
    total_time_remaining: float  # Minutes remaining in game

    # Pregame context
    pregame_total: float
    pregame_spread: float
    pregame_home_ml: int
    pregame_away_ml: int

    # Live odds
    live_total: Optional[float] = None
    live_spread: Optional[float] = None
    live_home_ml: Optional[int] = None
    live_away_ml: Optional[int] = None

    # Recent momentum (last 5 minutes)
    home_recent_scoring: int = 0
    away_recent_scoring: int = 0

    # Pace metrics
    current_pace: Optional[float] = None  # Possessions per 48 min (NBA/NHL adjusted)
    pregame_expected_pace: Optional[float] = None


@dataclass
class ScoringRun:
    """Detected scoring run in the game"""
    team: str
    run_size: int  # Points scored in run
    opponent_points: int  # Opponent points during run
    time_elapsed: float  # Minutes the run took
    current_period: int
    significant: bool  # Is this a 10-0+ run or similar?


@dataclass
class LiveBettingOpportunity:
    """Live betting opportunity with analysis"""
    game_id: str
    sport: str
    home_team: str
    away_team: str
    opportunity_type: str  # "LIVE_TOTAL", "LIVE_SPREAD", "LIVE_ML"

    # Recommendation
    recommended_bet: str  # "OVER", "UNDER", "HOME +X", "AWAY +X", "HOME ML", "AWAY ML"
    bet_value: float  # Line or odds value

    # Edge analysis
    fair_value: float
    edge: float
    edge_percentage: float
    confidence: float

    # Live context
    current_score: str
    time_remaining: str

    # Key factors
    key_factors: List[str]
    momentum_indicator: str  # "HOME_HOT", "AWAY_HOT", "BALANCED"

    # EV
    expected_value: float


class LiveBettingStrategy:
    """
    Strategy for finding value in live betting markets

    Key Concepts:
    - Overreactions to scoring runs create value
    - Momentum shifts are often temporary (regression to mean)
    - Live totals overreact to pace in early periods
    - Public overvalues recent performance (recency bias)
    - Oddsmakers slow to adjust after big runs
    """

    def __init__(
        self,
        scoring_run_threshold: int = 10,  # 10-0 run is significant
        momentum_lookback_minutes: float = 5.0,  # Look at last 5 minutes
        pace_sample_size_periods: int = 1,  # Need 1 full period for pace
        min_edge: float = 0.05,  # Minimum 5% edge
        overreaction_factor: float = 0.6,  # How much to fade overreactions
    ):
        """
        Initialize Live Betting Strategy

        Args:
            scoring_run_threshold: Minimum point differential to be a "run"
            momentum_lookback_minutes: How far back to analyze momentum
            pace_sample_size_periods: Periods needed for reliable pace
            min_edge: Minimum edge to recommend bet
            overreaction_factor: Adjustment factor for market overreactions
        """
        self.scoring_run_threshold = scoring_run_threshold
        self.momentum_lookback_minutes = momentum_lookback_minutes
        self.pace_sample_size_periods = pace_sample_size_periods
        self.min_edge = min_edge
        self.overreaction_factor = overreaction_factor

    def detect_scoring_run(
        self,
        game_state: LiveGameState
    ) -> Optional[ScoringRun]:
        """
        Detect if there's a significant scoring run happening

        Args:
            game_state: Current live game state

        Returns:
            ScoringRun if detected, None otherwise
        """
        home_recent = game_state.home_recent_scoring
        away_recent = game_state.away_recent_scoring

        point_differential = abs(home_recent - away_recent)

        if point_differential >= self.scoring_run_threshold:
            # Significant run detected
            if home_recent > away_recent:
                team = game_state.home_team
                run_size = home_recent
                opponent_points = away_recent
            else:
                team = game_state.away_team
                run_size = away_recent
                opponent_points = home_recent

            return ScoringRun(
                team=team,
                run_size=run_size,
                opponent_points=opponent_points,
                time_elapsed=self.momentum_lookback_minutes,
                current_period=game_state.period,
                significant=True
            )

        return None

    def calculate_fair_total(
        self,
        game_state: LiveGameState
    ) -> tuple[float, float]:
        """
        Calculate fair total for the remainder of the game

        Args:
            game_state: Current live game state

        Returns:
            (fair_total, confidence)
        """
        # Points scored so far
        current_total = game_state.home_score + game_state.away_score

        # Time elapsed percentage
        if game_state.sport == "basketball_nba":
            total_time = 48.0
        elif game_state.sport == "icehockey_nhl":
            total_time = 60.0
        elif game_state.sport == "americanfootball_nfl":
            total_time = 60.0
        else:
            total_time = 48.0

        time_elapsed = total_time - game_state.total_time_remaining
        time_elapsed_pct = time_elapsed / total_time

        # Early game: Use more of pregame expectation
        # Late game: Use more of current pace
        if time_elapsed_pct < 0.25:
            # Less than 25% complete - trust pregame more
            weight_current = 0.3
            weight_pregame = 0.7
            confidence = 0.6
        elif time_elapsed_pct < 0.5:
            # 25-50% complete - balanced
            weight_current = 0.5
            weight_pregame = 0.5
            confidence = 0.75
        elif time_elapsed_pct < 0.75:
            # 50-75% complete - trust current pace more
            weight_current = 0.7
            weight_pregame = 0.3
            confidence = 0.85
        else:
            # 75%+ complete - heavily trust current pace
            weight_current = 0.85
            weight_pregame = 0.15
            confidence = 0.90

        # Project based on current pace
        projected_final_current = current_total / time_elapsed_pct if time_elapsed_pct > 0 else game_state.pregame_total

        # Weighted projection
        fair_total = (
            projected_final_current * weight_current +
            game_state.pregame_total * weight_pregame
        )

        return fair_total, confidence

    def calculate_fair_spread(
        self,
        game_state: LiveGameState
    ) -> tuple[float, float]:
        """
        Calculate fair spread for remainder of game

        Args:
            game_state: Current live game state

        Returns:
            (fair_spread, confidence) - positive means home favored
        """
        # Current point differential
        current_diff = game_state.home_score - game_state.away_score

        # Time remaining percentage
        if game_state.sport == "basketball_nba":
            total_time = 48.0
        elif game_state.sport == "icehockey_nhl":
            total_time = 60.0
        elif game_state.sport == "americanfootball_nfl":
            total_time = 60.0
        else:
            total_time = 48.0

        time_remaining_pct = game_state.total_time_remaining / total_time

        # Expected points remaining based on pregame spread
        # If home was -5.5 pregame, expect them to win by ~5.5
        pregame_expected_final_diff = game_state.pregame_spread

        # Current pace suggests different final margin
        current_pace_final_diff = current_diff / (1 - time_remaining_pct) if time_remaining_pct < 1.0 else current_diff

        # Weight based on time remaining
        if time_remaining_pct > 0.75:
            # Lots of time left - trust pregame more
            weight_pregame = 0.6
            confidence = 0.65
        elif time_remaining_pct > 0.5:
            weight_pregame = 0.4
            confidence = 0.75
        elif time_remaining_pct > 0.25:
            weight_pregame = 0.2
            confidence = 0.85
        else:
            # Very little time - current score matters most
            weight_pregame = 0.05
            confidence = 0.95

        fair_final_diff = (
            current_pace_final_diff * (1 - weight_pregame) +
            pregame_expected_final_diff * weight_pregame
        )

        # Fair live spread is: fair_final_diff - current_diff
        fair_spread = fair_final_diff - current_diff

        return fair_spread, confidence

    def analyze_total_opportunity(
        self,
        game_state: LiveGameState
    ) -> Optional[LiveBettingOpportunity]:
        """
        Analyze live total for betting opportunity

        Args:
            game_state: Current live game state

        Returns:
            LiveBettingOpportunity if found, None otherwise
        """
        if game_state.live_total is None:
            return None

        # Calculate fair total
        fair_total, confidence = self.calculate_fair_total(game_state)

        # Check for scoring run (overreaction indicator)
        scoring_run = self.detect_scoring_run(game_state)

        # If scoring run detected, adjust for overreaction
        if scoring_run:
            # Market likely overreacted to the run
            # Adjust our fair value to fade the overreaction
            if game_state.live_total > fair_total:
                # Total went up, likely overreacting to high scoring
                fair_total = fair_total + (game_state.live_total - fair_total) * self.overreaction_factor
            elif game_state.live_total < fair_total:
                # Total went down, overreacting to slow pace
                fair_total = fair_total - (fair_total - game_state.live_total) * self.overreaction_factor

            confidence *= 1.1  # More confident when we detect overreaction

        # Calculate edge
        edge = abs(fair_total - game_state.live_total)
        edge_percentage = (edge / game_state.live_total) * 100

        # Determine recommendation
        if fair_total > game_state.live_total + (game_state.live_total * self.min_edge):
            recommended_bet = "OVER"
            bet_value = game_state.live_total
            ev = ((confidence * 1.91) - (1 - confidence)) * 100  # -110 odds
        elif fair_total < game_state.live_total - (game_state.live_total * self.min_edge):
            recommended_bet = "UNDER"
            bet_value = game_state.live_total
            ev = ((confidence * 1.91) - (1 - confidence)) * 100
        else:
            return None  # No edge

        # Generate key factors
        key_factors = []

        current_total = game_state.home_score + game_state.away_score
        if current_total > game_state.pregame_total * 0.6:
            key_factors.append(f"Scoring {((current_total / game_state.pregame_total) - 1) * 100:+.1f}% vs pregame pace")

        if scoring_run:
            key_factors.append(f"{scoring_run.team} on {scoring_run.run_size}-{scoring_run.opponent_points} run")
            key_factors.append(f"Market likely overreacting to recent scoring")

        time_remaining_str = f"{int(game_state.total_time_remaining)}min remaining"
        key_factors.append(time_remaining_str)

        # Momentum indicator
        if game_state.home_recent_scoring > game_state.away_recent_scoring * 1.5:
            momentum = "HOME_HOT"
        elif game_state.away_recent_scoring > game_state.home_recent_scoring * 1.5:
            momentum = "AWAY_HOT"
        else:
            momentum = "BALANCED"

        return LiveBettingOpportunity(
            game_id=game_state.game_id,
            sport=game_state.sport,
            home_team=game_state.home_team,
            away_team=game_state.away_team,
            opportunity_type="LIVE_TOTAL",
            recommended_bet=recommended_bet,
            bet_value=bet_value,
            fair_value=fair_total,
            edge=edge,
            edge_percentage=edge_percentage,
            confidence=min(confidence, 0.95),
            current_score=f"{game_state.home_team} {game_state.home_score}, {game_state.away_team} {game_state.away_score}",
            time_remaining=time_remaining_str,
            key_factors=key_factors,
            momentum_indicator=momentum,
            expected_value=ev
        )

    def analyze_spread_opportunity(
        self,
        game_state: LiveGameState
    ) -> Optional[LiveBettingOpportunity]:
        """
        Analyze live spread for betting opportunity

        Args:
            game_state: Current live game state

        Returns:
            LiveBettingOpportunity if found, None otherwise
        """
        if game_state.live_spread is None:
            return None

        # Calculate fair spread
        fair_spread, confidence = self.calculate_fair_spread(game_state)

        # Calculate edge
        edge = abs(fair_spread - game_state.live_spread)

        # Check minimum edge (0.5 points for spread)
        if edge < 0.5:
            return None

        edge_percentage = (edge / abs(game_state.live_spread)) * 100 if game_state.live_spread != 0 else 0

        # Determine recommendation
        if fair_spread > game_state.live_spread + 0.5:
            # Home team better value than market thinks
            recommended_bet = f"{game_state.home_team} {game_state.live_spread:+.1f}"
            ev = ((confidence * 1.91) - (1 - confidence)) * 100
        elif fair_spread < game_state.live_spread - 0.5:
            # Away team better value
            recommended_bet = f"{game_state.away_team} {-game_state.live_spread:+.1f}"
            ev = ((confidence * 1.91) - (1 - confidence)) * 100
        else:
            return None

        # Key factors
        key_factors = []

        current_diff = game_state.home_score - game_state.away_score
        key_factors.append(f"Current margin: {game_state.home_team if current_diff > 0 else game_state.away_team} by {abs(current_diff)}")

        if abs(fair_spread - game_state.live_spread) > 2.0:
            key_factors.append(f"Market off by {abs(fair_spread - game_state.live_spread):.1f} points")

        # Momentum
        scoring_run = self.detect_scoring_run(game_state)
        if scoring_run:
            key_factors.append(f"{scoring_run.team} on {scoring_run.run_size}-{scoring_run.opponent_points} scoring run")
            key_factors.append("Fading recency bias")

        momentum = "BALANCED"
        if game_state.home_recent_scoring > game_state.away_recent_scoring * 1.5:
            momentum = "HOME_HOT"
        elif game_state.away_recent_scoring > game_state.home_recent_scoring * 1.5:
            momentum = "AWAY_HOT"

        return LiveBettingOpportunity(
            game_id=game_state.game_id,
            sport=game_state.sport,
            home_team=game_state.home_team,
            away_team=game_state.away_team,
            opportunity_type="LIVE_SPREAD",
            recommended_bet=recommended_bet,
            bet_value=game_state.live_spread,
            fair_value=fair_spread,
            edge=edge,
            edge_percentage=edge_percentage,
            confidence=min(confidence, 0.95),
            current_score=f"{game_state.home_team} {game_state.home_score}, {game_state.away_team} {game_state.away_score}",
            time_remaining=f"{int(game_state.total_time_remaining)}min remaining",
            key_factors=key_factors,
            momentum_indicator=momentum,
            expected_value=ev
        )

    def analyze_game(
        self,
        game_state: LiveGameState
    ) -> List[LiveBettingOpportunity]:
        """
        Analyze all live betting opportunities for a game

        Args:
            game_state: Current live game state

        Returns:
            List of LiveBettingOpportunity
        """
        opportunities = []

        # Check total
        total_opp = self.analyze_total_opportunity(game_state)
        if total_opp:
            opportunities.append(total_opp)

        # Check spread
        spread_opp = self.analyze_spread_opportunity(game_state)
        if spread_opp:
            opportunities.append(spread_opp)

        return opportunities

    def format_opportunity(self, opp: LiveBettingOpportunity) -> str:
        """Format opportunity as readable string"""
        lines = [
            "="*70,
            f"LIVE BETTING OPPORTUNITY: {opp.home_team} vs {opp.away_team}",
            "="*70,
            f"\nCurrent Score: {opp.current_score}",
            f"Time Remaining: {opp.time_remaining}",
            f"Momentum: {opp.momentum_indicator}",
            f"\nOpportunity Type: {opp.opportunity_type}",
            f"\nRECOMMENDATION: {opp.recommended_bet}",
            f"Market Line: {opp.bet_value}",
            f"Fair Value: {opp.fair_value:.1f}",
            f"Edge: {opp.edge:.1f} ({opp.edge_percentage:+.1f}%)",
            f"Confidence: {opp.confidence*100:.0f}%",
            f"Expected Value: {opp.expected_value:+.1f}%",
            "\nKey Factors:"
        ]

        for factor in opp.key_factors:
            lines.append(f"  • {factor}")

        lines.append("="*70)

        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    strategy = LiveBettingStrategy(min_edge=0.05)

    # Example: NBA game at halftime with home team on scoring run
    game = LiveGameState(
        game_id="LAL_BOS_LIVE",
        sport="basketball_nba",
        home_team="Lakers",
        away_team="Celtics",
        home_score=58,
        away_score=52,
        period=2,  # Halftime
        time_remaining=0.0,  # End of 2nd quarter
        total_time_remaining=24.0,  # Half a game left
        pregame_total=220.5,
        pregame_spread=-3.5,  # Lakers favored by 3.5
        pregame_home_ml=-150,
        pregame_away_ml=+130,
        # Live odds have overreacted to fast pace
        live_total=230.5,  # Market raised total by 10 points
        live_spread=-5.5,  # Lakers now favored by more
        live_home_ml=-200,
        live_away_ml=+170,
        # Lakers just went on 12-2 run in last 5 minutes
        home_recent_scoring=12,
        away_recent_scoring=2,
        current_pace=105.0,  # Fast pace
        pregame_expected_pace=98.0
    )

    # Analyze opportunities
    opportunities = strategy.analyze_game(game)

    print(f"\nFound {len(opportunities)} live betting opportunities:\n")

    for opp in opportunities:
        print(strategy.format_opportunity(opp))
        print()
