"""
Player Props Strategy Engine
Identifies value in player prop markets using usage rates, matchup analysis, and trends
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
import numpy as np


@dataclass
class PlayerStats:
    """Player statistics and trends"""
    player_name: str
    team: str
    position: str

    # Season averages
    ppg: float  # Points per game
    rpg: float  # Rebounds per game
    apg: float  # Assists per game
    minutes_per_game: float
    usage_rate: float  # Percentage of team possessions used

    # Recent form (last 5 games)
    last_5_ppg: float
    last_5_rpg: float
    last_5_apg: float
    last_5_minutes: float

    # Advanced metrics
    true_shooting_pct: float
    assist_rate: float
    rebound_rate: float

    # Injury/status
    injury_status: str = "Healthy"  # Healthy, Questionable, Probable
    minutes_restriction: bool = False


@dataclass
class OpponentDefense:
    """Opponent defensive metrics relevant to props"""
    team_name: str
    pace: float  # Possessions per game
    def_rating: float  # Defensive efficiency
    ppg_allowed: float

    # Position-specific defense
    ppg_allowed_to_position: Optional[float] = None
    rpg_allowed_to_position: Optional[float] = None
    apg_allowed_to_position: Optional[float] = None

    # Recent trends
    last_5_ppg_allowed: Optional[float] = None


@dataclass
class PropMarket:
    """Prop betting market"""
    prop_type: str  # points, rebounds, assists, threes, etc.
    line: float  # Over/under line
    over_odds: int  # American odds for over
    under_odds: int  # American odds for under
    bookmaker: str


@dataclass
class PropPrediction:
    """Prop prediction with value analysis"""
    player_name: str
    team: str
    opponent: str
    prop_type: str
    line: float
    predicted_value: float
    over_probability: float
    under_probability: float
    over_ev: float
    under_ev: float
    recommended_bet: Optional[str]  # "OVER", "UNDER", or None
    confidence: float
    edge_percentage: float
    key_factors: List[str]


class PlayerPropsStrategy:
    """
    Strategy for finding value in player prop markets

    Key Concepts:
    - Recent form matters more than season averages
    - Usage rate indicates opportunity
    - Matchup-specific defense (how opponent defends this position)
    - Pace impacts counting stats (more possessions = more opportunities)
    - Minutes played is THE most important factor
    - Injury status and load management
    """

    def __init__(
        self,
        recent_weight: float = 0.6,  # Weight recent form over season
        usage_weight: float = 0.3,  # Weight for usage rate impact
        matchup_weight: float = 0.25,  # Weight for matchup defense
        pace_boost_per_10: float = 2.0,  # Stat boost per 10 pace increase
        min_edge: float = 0.08,  # Minimum 8% edge for props
        min_minutes_threshold: float = 28.0,  # Minimum minutes for reliable props
    ):
        """
        Initialize Player Props Strategy

        Args:
            recent_weight: How much to weight recent form
            usage_weight: Importance of usage rate
            matchup_weight: Importance of matchup defense
            pace_boost_per_10: Stat increase per 10 pace
            min_edge: Minimum edge to recommend bet
            min_minutes_threshold: Minimum minutes for confidence
        """
        self.recent_weight = recent_weight
        self.usage_weight = usage_weight
        self.matchup_weight = matchup_weight
        self.pace_boost_per_10 = pace_boost_per_10
        self.min_edge = min_edge
        self.min_minutes_threshold = min_minutes_threshold

    def predict_stat(
        self,
        player: PlayerStats,
        opponent: OpponentDefense,
        stat_type: str  # 'points', 'rebounds', 'assists'
    ) -> tuple[float, float]:
        """
        Predict player's stat output for this game

        Args:
            player: PlayerStats object
            opponent: OpponentDefense object
            stat_type: Type of stat to predict

        Returns:
            (predicted_value, confidence)
        """
        # Get relevant stats
        if stat_type == 'points':
            season_avg = player.ppg
            recent_avg = player.last_5_ppg
            opponent_allowed = opponent.ppg_allowed_to_position or opponent.ppg_allowed / 5
            opponent_recent = opponent.last_5_ppg_allowed or opponent_allowed
        elif stat_type == 'rebounds':
            season_avg = player.rpg
            recent_avg = player.last_5_rpg
            opponent_allowed = opponent.rpg_allowed_to_position or 10.0  # Default
            opponent_recent = opponent_allowed
        elif stat_type == 'assists':
            season_avg = player.apg
            recent_avg = player.last_5_apg
            opponent_allowed = opponent.apg_allowed_to_position or 5.0
            opponent_recent = opponent_allowed
        else:
            return 0.0, 0.0

        # Weighted combination of season and recent
        base_prediction = (
            season_avg * (1 - self.recent_weight) +
            recent_avg * self.recent_weight
        )

        # Adjust for minutes
        minutes_factor = player.last_5_minutes / player.minutes_per_game
        minutes_factor = max(0.5, min(minutes_factor, 1.3))  # Cap adjustments
        base_prediction *= minutes_factor

        # Adjust for usage rate (high usage = more opportunity)
        if stat_type == 'points':
            usage_adjustment = (player.usage_rate - 20.0) / 100.0  # 20% is average
            base_prediction *= (1 + usage_adjustment * self.usage_weight)

        # Adjust for pace (faster pace = more possessions = more stats)
        avg_pace = 100.0
        pace_diff = opponent.pace - avg_pace
        pace_adjustment = (pace_diff / 10.0) * self.pace_boost_per_10
        base_prediction += pace_adjustment

        # Adjust for opponent defense
        league_avg_allowed = season_avg  # Rough approximation
        opponent_vs_avg = opponent_allowed - league_avg_allowed
        matchup_adjustment = opponent_vs_avg * self.matchup_weight
        base_prediction += matchup_adjustment

        # Check for injury impact
        if player.injury_status in ["Questionable", "Probable"]:
            base_prediction *= 0.90  # 10% reduction for injury concerns

        if player.minutes_restriction:
            base_prediction *= 0.85  # 15% reduction for minutes limit

        # Calculate confidence
        base_confidence = 0.5

        # More minutes = higher confidence
        if player.last_5_minutes >= self.min_minutes_threshold:
            base_confidence += 0.20

        # Consistent recent performance = higher confidence
        if stat_type == 'points':
            recent_std = np.std([player.last_5_ppg] * 5)  # Simplified
        elif stat_type == 'rebounds':
            recent_std = np.std([player.last_5_rpg] * 5)
        else:
            recent_std = np.std([player.last_5_apg] * 5)

        consistency = 1.0 / (1 + recent_std)
        base_confidence += consistency * 0.20

        # High usage = higher confidence
        if player.usage_rate > 25.0:
            base_confidence += 0.10

        confidence = min(base_confidence, 0.95)

        return base_prediction, confidence

    def american_to_probability(self, american_odds: int) -> float:
        """Convert American odds to implied probability"""
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)

    def calculate_prop_probabilities(
        self,
        predicted_value: float,
        line: float,
        confidence: float
    ) -> tuple[float, float]:
        """
        Calculate probability of going over/under the line

        Uses normal distribution assumption with confidence as std dev adjustment

        Args:
            predicted_value: Predicted stat value
            line: Prop line
            confidence: Model confidence

        Returns:
            (over_probability, under_probability)
        """
        # Standard deviation based on confidence
        # Lower confidence = higher variance
        std_dev = (1 - confidence) * predicted_value * 0.4

        if std_dev == 0:
            std_dev = predicted_value * 0.2  # Default 20% variance

        # Calculate z-score
        z_score = (line - predicted_value) / std_dev

        # Use normal CDF approximation
        # P(X > line) = 1 - CDF(z_score)
        from math import erf, sqrt
        cdf = 0.5 * (1 + erf(z_score / sqrt(2)))

        under_prob = cdf
        over_prob = 1 - cdf

        return over_prob, under_prob

    def analyze_prop(
        self,
        player: PlayerStats,
        opponent: OpponentDefense,
        prop_market: PropMarket
    ) -> PropPrediction:
        """
        Analyze a player prop market for value

        Args:
            player: PlayerStats object
            opponent: OpponentDefense object
            prop_market: PropMarket with line and odds

        Returns:
            PropPrediction with complete analysis
        """
        # Get prediction for this stat type
        predicted_value, confidence = self.predict_stat(
            player,
            opponent,
            prop_market.prop_type
        )

        # Calculate over/under probabilities
        over_prob, under_prob = self.calculate_prop_probabilities(
            predicted_value,
            prop_market.line,
            confidence
        )

        # Get implied probabilities from market odds
        over_implied = self.american_to_probability(prop_market.over_odds)
        under_implied = self.american_to_probability(prop_market.under_odds)

        # Calculate expected value
        # Over EV
        if prop_market.over_odds > 0:
            over_payout = prop_market.over_odds / 100
        else:
            over_payout = 100 / abs(prop_market.over_odds)
        over_ev = (over_prob * over_payout) - (under_prob * 1)

        # Under EV
        if prop_market.under_odds > 0:
            under_payout = prop_market.under_odds / 100
        else:
            under_payout = 100 / abs(prop_market.under_odds)
        under_ev = (under_prob * under_payout) - (over_prob * 1)

        # Calculate edges
        over_edge = over_prob - over_implied
        under_edge = under_prob - under_implied

        # Determine recommendation
        recommended_bet = None
        edge_percentage = 0.0

        if over_edge >= self.min_edge and over_ev > 0:
            recommended_bet = "OVER"
            edge_percentage = over_edge * 100
        elif under_edge >= self.min_edge and under_ev > 0:
            recommended_bet = "UNDER"
            edge_percentage = under_edge * 100

        # Generate key factors
        key_factors = []

        # Recent form
        if prop_market.prop_type == 'points':
            season_avg = player.ppg
            recent_avg = player.last_5_ppg
        elif prop_market.prop_type == 'rebounds':
            season_avg = player.rpg
            recent_avg = player.last_5_rpg
        else:
            season_avg = player.apg
            recent_avg = player.last_5_apg

        if recent_avg > season_avg * 1.15:
            key_factors.append(f"HOT: Averaging {recent_avg:.1f} last 5 vs {season_avg:.1f} season")
        elif recent_avg < season_avg * 0.85:
            key_factors.append(f"COLD: Averaging {recent_avg:.1f} last 5 vs {season_avg:.1f} season")

        # Usage
        if player.usage_rate > 28.0:
            key_factors.append(f"High usage rate: {player.usage_rate:.1f}%")

        # Minutes
        if player.last_5_minutes < self.min_minutes_threshold:
            key_factors.append(f"⚠️ Low minutes: {player.last_5_minutes:.1f} MPG")

        # Pace
        if opponent.pace > 102.0:
            key_factors.append(f"Fast pace matchup: {opponent.pace:.1f} possessions")
        elif opponent.pace < 97.0:
            key_factors.append(f"Slow pace matchup: {opponent.pace:.1f} possessions")

        # Injury
        if player.injury_status != "Healthy":
            key_factors.append(f"⚠️ Injury status: {player.injury_status}")

        # Prediction vs line
        diff = predicted_value - prop_market.line
        if abs(diff) >= 2.0:
            direction = "above" if diff > 0 else "below"
            key_factors.append(f"Model projects {abs(diff):.1f} {direction} line")

        return PropPrediction(
            player_name=player.player_name,
            team=player.team,
            opponent=opponent.team_name,
            prop_type=prop_market.prop_type,
            line=prop_market.line,
            predicted_value=predicted_value,
            over_probability=over_prob,
            under_probability=under_prob,
            over_ev=over_ev * 100,  # As percentage
            under_ev=under_ev * 100,
            recommended_bet=recommended_bet,
            confidence=confidence,
            edge_percentage=edge_percentage,
            key_factors=key_factors
        )

    def format_prediction(self, pred: PropPrediction) -> str:
        """Format prediction as readable string"""
        lines = [
            "="*70,
            f"PROP ANALYSIS: {pred.player_name} ({pred.team})",
            f"Opponent: {pred.opponent}",
            "="*70,
            f"\nProp: {pred.prop_type.upper()} {pred.line:+.1f}",
            f"Predicted: {pred.predicted_value:.1f}",
            f"\nProbabilities:",
            f"  Over {pred.line}: {pred.over_probability*100:.1f}%",
            f"  Under {pred.line}: {pred.under_probability*100:.1f}%",
            f"\nExpected Value:",
            f"  Over EV: {pred.over_ev:+.2f}%",
            f"  Under EV: {pred.under_ev:+.2f}%",
        ]

        if pred.recommended_bet:
            lines.extend([
                f"\nRECOMMENDATION: {pred.recommended_bet} {pred.line}",
                f"Edge: {pred.edge_percentage:+.1f}%",
                f"Confidence: {pred.confidence*100:.0f}%"
            ])
        else:
            lines.append("\nRECOMMENDATION: No bet (insufficient edge)")

        lines.append("\nKey Factors:")
        for factor in pred.key_factors:
            lines.append(f"  • {factor}")

        lines.append("="*70)

        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    # Initialize strategy
    strategy = PlayerPropsStrategy(min_edge=0.08)

    # Example: LeBron James points prop
    lebron = PlayerStats(
        player_name="LeBron James",
        team="Lakers",
        position="SF",
        ppg=25.5,
        rpg=7.5,
        apg=7.8,
        minutes_per_game=35.0,
        usage_rate=30.5,
        last_5_ppg=28.2,  # Hot streak
        last_5_rpg=8.0,
        last_5_apg=8.2,
        last_5_minutes=36.5,
        true_shooting_pct=0.588,
        assist_rate=35.0,
        rebound_rate=10.5,
        injury_status="Healthy"
    )

    opponent = OpponentDefense(
        team_name="Warriors",
        pace=101.5,  # Fast pace
        def_rating=112.0,
        ppg_allowed=115.0,
        ppg_allowed_to_position=26.5,  # Bad at defending SFs
        last_5_ppg_allowed=118.0
    )

    prop_market = PropMarket(
        prop_type="points",
        line=26.5,
        over_odds=-110,
        under_odds=-110,
        bookmaker="DraftKings"
    )

    # Analyze prop
    prediction = strategy.analyze_prop(lebron, opponent, prop_market)

    # Print results
    print(strategy.format_prediction(prediction))
