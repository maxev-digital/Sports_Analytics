"""
Moneyline Strategy Engine
Identifies value in moneyline markets by comparing true win probability to implied odds
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
import numpy as np


@dataclass
class TeamStrength:
    """Team strength metrics"""
    team_name: str
    elo_rating: float  # Elo rating (1500 = average)
    win_pct: float  # Season win percentage
    recent_form: float  # Last 10 games win %
    strength_of_schedule: float  # Opponent quality (higher = tougher)
    home_record: Optional[str] = None
    away_record: Optional[str] = None
    vs_winning_teams: Optional[float] = None  # Win % vs teams >.500


@dataclass
class GameContext:
    """Contextual factors affecting the game"""
    home_team: TeamStrength
    away_team: TeamStrength
    is_neutral_site: bool = False
    playoff_game: bool = False
    must_win_situation: bool = False  # Playoff race implications
    rivalry_game: bool = False
    home_team_rest_advantage: int = 0  # Days of rest differential
    key_injuries_home: int = 0
    key_injuries_away: int = 0


@dataclass
class MoneylinePrediction:
    """Moneyline prediction with value analysis"""
    home_team: str
    away_team: str
    home_win_prob: float  # True probability (0-1)
    away_win_prob: float
    home_ml_value: float  # Expected value percentage
    away_ml_value: float
    recommended_bet: Optional[str]  # Team name or None
    confidence: float
    edge_percentage: float
    reasoning: List[str]


class MoneylineStrategy:
    """
    Strategy for finding value in moneyline markets

    Key Concepts:
    - Convert team ratings to win probabilities
    - Account for home court advantage
    - Adjust for situational factors (rest, injuries, motivation)
    - Compare true probability to implied probability from odds
    - Only bet when edge exceeds threshold
    """

    def __init__(
        self,
        home_court_advantage: float = 65.0,  # Elo points for home court
        min_edge: float = 0.05,  # Minimum 5% edge to recommend bet
        injury_impact_per_player: float = 20.0,  # Elo adjustment per key injury
        must_win_boost: float = 30.0,  # Elo boost for must-win games
        rivalry_variance: float = 0.95,  # Rivalry games are less predictable
    ):
        """
        Initialize Moneyline Strategy

        Args:
            home_court_advantage: Elo rating boost for home team
            min_edge: Minimum edge required to recommend bet
            injury_impact_per_player: Elo adjustment per key injury
            must_win_boost: Elo boost when team has playoff implications
            rivalry_variance: Multiplier for rivalry games (closer to 1 = less predictable)
        """
        self.home_court_advantage = home_court_advantage
        self.min_edge = min_edge
        self.injury_impact_per_player = injury_impact_per_player
        self.must_win_boost = must_win_boost
        self.rivalry_variance = rivalry_variance

    def calculate_win_probability_elo(
        self,
        team_a_elo: float,
        team_b_elo: float
    ) -> float:
        """
        Calculate team A's win probability using Elo formula

        Formula: 1 / (1 + 10^((Elo_B - Elo_A) / 400))

        Args:
            team_a_elo: Team A's Elo rating
            team_b_elo: Team B's Elo rating

        Returns:
            Probability of team A winning (0-1)
        """
        elo_diff = team_a_elo - team_b_elo
        win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        return win_prob

    def adjust_for_context(
        self,
        base_elo: float,
        context: GameContext,
        is_home_team: bool
    ) -> float:
        """
        Adjust Elo rating based on game context

        Args:
            base_elo: Team's base Elo rating
            context: GameContext with situational factors
            is_home_team: Whether this is the home team

        Returns:
            Adjusted Elo rating
        """
        adjusted_elo = base_elo

        # Home court advantage
        if is_home_team and not context.is_neutral_site:
            adjusted_elo += self.home_court_advantage

        # Rest advantage
        if is_home_team:
            rest_diff = context.home_team_rest_advantage
        else:
            rest_diff = -context.home_team_rest_advantage

        # Each day of rest advantage worth ~10 Elo points
        adjusted_elo += rest_diff * 10.0

        # Injuries
        if is_home_team:
            adjusted_elo -= context.key_injuries_home * self.injury_impact_per_player
        else:
            adjusted_elo -= context.key_injuries_away * self.injury_impact_per_player

        # Must-win situation
        if context.must_win_situation:
            # Home team typically has more pressure in must-win
            if is_home_team:
                adjusted_elo += self.must_win_boost * 0.7
            else:
                adjusted_elo += self.must_win_boost

        return adjusted_elo

    def american_to_probability(self, american_odds: float) -> float:
        """Convert American odds to implied probability"""
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)

    def calculate_expected_value(
        self,
        true_prob: float,
        implied_prob: float,
        american_odds: float
    ) -> float:
        """
        Calculate expected value percentage

        Args:
            true_prob: True win probability (model)
            implied_prob: Implied probability from odds
            american_odds: American odds

        Returns:
            Expected value as percentage
        """
        # Convert odds to decimal
        if american_odds > 0:
            decimal_odds = (american_odds / 100) + 1
        else:
            decimal_odds = (100 / abs(american_odds)) + 1

        # EV = (true_prob * (decimal_odds - 1)) - (1 - true_prob)
        ev = (true_prob * (decimal_odds - 1)) - (1 - true_prob)
        ev_percentage = ev * 100

        return ev_percentage

    def predict(
        self,
        context: GameContext,
        home_ml_odds: float,
        away_ml_odds: float
    ) -> MoneylinePrediction:
        """
        Generate moneyline prediction with value analysis

        Args:
            context: GameContext with team strength and situational factors
            home_ml_odds: Home team moneyline odds (American)
            away_ml_odds: Away team moneyline odds (American)

        Returns:
            MoneylinePrediction with complete analysis
        """
        # Get base Elo ratings
        home_base_elo = context.home_team.elo_rating
        away_base_elo = context.away_team.elo_rating

        # Adjust for context
        home_adjusted_elo = self.adjust_for_context(home_base_elo, context, is_home_team=True)
        away_adjusted_elo = self.adjust_for_context(away_base_elo, context, is_home_team=False)

        # Calculate true win probabilities
        home_win_prob = self.calculate_win_probability_elo(home_adjusted_elo, away_adjusted_elo)
        away_win_prob = 1 - home_win_prob

        # Adjust for rivalry (more variance, less predictable)
        if context.rivalry_game:
            # Move probabilities closer to 50-50
            home_win_prob = 0.5 + (home_win_prob - 0.5) * self.rivalry_variance
            away_win_prob = 1 - home_win_prob

        # Get implied probabilities from market odds
        home_implied_prob = self.american_to_probability(home_ml_odds)
        away_implied_prob = self.american_to_probability(away_ml_odds)

        # Calculate expected value
        home_ml_value = self.calculate_expected_value(home_win_prob, home_implied_prob, home_ml_odds)
        away_ml_value = self.calculate_expected_value(away_win_prob, away_implied_prob, away_ml_odds)

        # Calculate edge (true prob - implied prob)
        home_edge = home_win_prob - home_implied_prob
        away_edge = away_win_prob - away_implied_prob

        # Determine recommendation
        recommended_bet = None
        confidence = 0.5
        edge_percentage = 0.0

        if home_edge >= self.min_edge and home_ml_value > 0:
            recommended_bet = context.home_team.team_name
            confidence = min(0.5 + (home_edge * 2), 0.95)
            edge_percentage = home_edge * 100
        elif away_edge >= self.min_edge and away_ml_value > 0:
            recommended_bet = context.away_team.team_name
            confidence = min(0.5 + (away_edge * 2), 0.95)
            edge_percentage = away_edge * 100

        # Generate reasoning
        reasoning = []

        # Elo differential
        elo_diff = home_adjusted_elo - away_adjusted_elo
        if abs(elo_diff) > 100:
            stronger_team = context.home_team.team_name if elo_diff > 0 else context.away_team.team_name
            reasoning.append(f"{stronger_team} has {abs(elo_diff):.0f} Elo advantage")

        # Recent form
        if context.home_team.recent_form > 0.7:
            reasoning.append(f"{context.home_team.team_name} hot (70%+ last 10)")
        if context.away_team.recent_form > 0.7:
            reasoning.append(f"{context.away_team.team_name} hot (70%+ last 10)")

        # Rest advantage
        if abs(context.home_team_rest_advantage) >= 2:
            rested_team = context.home_team.team_name if context.home_team_rest_advantage > 0 else context.away_team.team_name
            reasoning.append(f"{rested_team} has {abs(context.home_team_rest_advantage)} day rest advantage")

        # Injuries
        if context.key_injuries_home > 0:
            reasoning.append(f"{context.home_team.team_name} missing {context.key_injuries_home} key players")
        if context.key_injuries_away > 0:
            reasoning.append(f"{context.away_team.team_name} missing {context.key_injuries_away} key players")

        # Must-win situation
        if context.must_win_situation:
            reasoning.append("Must-win game (playoff implications)")

        # Value analysis
        if home_ml_value > 0:
            reasoning.append(f"{context.home_team.team_name} ML: {home_ml_value:+.1f}% EV")
        if away_ml_value > 0:
            reasoning.append(f"{context.away_team.team_name} ML: {away_ml_value:+.1f}% EV")

        return MoneylinePrediction(
            home_team=context.home_team.team_name,
            away_team=context.away_team.team_name,
            home_win_prob=home_win_prob,
            away_win_prob=away_win_prob,
            home_ml_value=home_ml_value,
            away_ml_value=away_ml_value,
            recommended_bet=recommended_bet,
            confidence=confidence,
            edge_percentage=edge_percentage,
            reasoning=reasoning
        )

    def format_prediction(self, pred: MoneylinePrediction) -> str:
        """Format prediction as readable string"""
        lines = [
            "="*70,
            f"MONEYLINE ANALYSIS: {pred.home_team} vs {pred.away_team}",
            "="*70,
            f"\nWin Probabilities:",
            f"  {pred.home_team}: {pred.home_win_prob*100:.1f}%",
            f"  {pred.away_team}: {pred.away_win_prob*100:.1f}%",
            f"\nExpected Value:",
            f"  {pred.home_team} ML: {pred.home_ml_value:+.2f}%",
            f"  {pred.away_team} ML: {pred.away_ml_value:+.2f}%",
        ]

        if pred.recommended_bet:
            lines.extend([
                f"\nRECOMMENDATION: Bet {pred.recommended_bet} ML",
                f"Edge: {pred.edge_percentage:+.1f}%",
                f"Confidence: {pred.confidence*100:.0f}%"
            ])
        else:
            lines.append("\nRECOMMENDATION: No bet (insufficient edge)")

        lines.append("\nKey Factors:")
        for reason in pred.reasoning:
            lines.append(f"  • {reason}")

        lines.append("="*70)

        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    # Initialize strategy
    strategy = MoneylineStrategy(min_edge=0.05)

    # Example: NBA underdog scenario - Spurs at home vs Warriors
    home_team = TeamStrength(
        team_name="San Antonio Spurs",
        elo_rating=1520,  # Slightly above average
        win_pct=0.48,
        recent_form=0.60,  # 6-4 last 10
        strength_of_schedule=0.52,
        home_record="18-15",
        vs_winning_teams=0.35
    )

    away_team = TeamStrength(
        team_name="Golden State Warriors",
        elo_rating=1580,  # Strong team
        win_pct=0.58,
        recent_form=0.50,  # 5-5 last 10 (slumping)
        strength_of_schedule=0.48,
        away_record="15-18",
        vs_winning_teams=0.62
    )

    context = GameContext(
        home_team=home_team,
        away_team=away_team,
        home_team_rest_advantage=2,  # Spurs rested, Warriors B2B
        key_injuries_away=1,  # Warriors missing key player
        must_win_situation=False
    )

    # Market odds (Warriors favored despite rest disadvantage)
    home_ml_odds = +140  # Spurs underdogs
    away_ml_odds = -165  # Warriors favorites

    # Generate prediction
    prediction = strategy.predict(context, home_ml_odds, away_ml_odds)

    # Print results
    print(strategy.format_prediction(prediction))
