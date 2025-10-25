"""
Expected Value (EV) Calculator for Sports Betting
Implements Kelly Criterion for optimal bet sizing
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class BettingOpportunity:
    """Represents a betting opportunity with odds and probability"""
    game_id: str
    team_name: str
    bet_type: str  # 'spread', 'total_over', 'total_under', 'moneyline'
    market_odds: float  # American odds (e.g., -110, +150)
    true_probability: float  # Model's estimated probability (0-1)
    market_line: Optional[float] = None  # Point spread or total line
    predicted_line: Optional[float] = None  # Model's predicted line
    confidence: float = 1.0  # Confidence multiplier (0-1)


@dataclass
class BettingRecommendation:
    """Output recommendation with EV and sizing"""
    game_id: str
    team_name: str
    bet_type: str
    market_odds: float
    market_line: Optional[float]
    predicted_line: Optional[float]
    true_probability: float
    implied_probability: float
    expected_value: float  # As percentage
    ev_dollars: float  # Expected value in dollars per $100 bet
    kelly_fraction: float  # Full Kelly percentage
    recommended_bet_size: float  # Conservative Kelly (typically 0.25x)
    edge_percentage: float  # Difference between true and implied probability
    bet_decision: str  # 'BET', 'PASS', 'AVOID'
    confidence_tier: str  # 'HIGH', 'MEDIUM', 'LOW'


class EVCalculator:
    """
    Calculate Expected Value and optimal bet sizing using Kelly Criterion
    """

    def __init__(
        self,
        kelly_fraction: float = 0.25,
        min_edge: float = 0.02,  # Minimum 2% edge to consider
        min_ev: float = 2.0,  # Minimum 2% EV to recommend
        high_confidence_threshold: float = 5.0,  # 5%+ EV = HIGH
        medium_confidence_threshold: float = 3.0,  # 3%+ EV = MEDIUM
    ):
        """
        Initialize EV Calculator

        Args:
            kelly_fraction: Fraction of Kelly to use (0.25 = quarter Kelly, conservative)
            min_edge: Minimum edge required to consider betting
            min_ev: Minimum EV% required to recommend a bet
            high_confidence_threshold: EV% threshold for HIGH confidence
            medium_confidence_threshold: EV% threshold for MEDIUM confidence
        """
        self.kelly_fraction = kelly_fraction
        self.min_edge = min_edge
        self.min_ev = min_ev
        self.high_confidence_threshold = high_confidence_threshold
        self.medium_confidence_threshold = medium_confidence_threshold

    @staticmethod
    def american_to_decimal(american_odds: float) -> float:
        """Convert American odds to decimal odds"""
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1

    @staticmethod
    def decimal_to_implied_probability(decimal_odds: float) -> float:
        """Convert decimal odds to implied probability"""
        return 1 / decimal_odds

    @staticmethod
    def american_to_implied_probability(american_odds: float) -> float:
        """Convert American odds directly to implied probability"""
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)

    def calculate_expected_value(
        self,
        true_probability: float,
        decimal_odds: float
    ) -> tuple[float, float]:
        """
        Calculate expected value

        Args:
            true_probability: Model's estimated probability (0-1)
            decimal_odds: Decimal odds from sportsbook

        Returns:
            (ev_percentage, ev_dollars) - EV as percentage and dollars per $100 bet
        """
        # Expected value formula: (probability × profit) - (1 - probability × stake)
        # For a $1 bet:
        win_amount = decimal_odds - 1  # Profit from winning
        loss_amount = 1  # Amount lost if bet loses

        ev = (true_probability * win_amount) - ((1 - true_probability) * loss_amount)
        ev_percentage = ev * 100  # Convert to percentage
        ev_dollars = ev * 100  # EV in dollars for a $100 bet

        return ev_percentage, ev_dollars

    def calculate_kelly_criterion(
        self,
        true_probability: float,
        decimal_odds: float
    ) -> float:
        """
        Calculate Kelly Criterion bet sizing

        Formula: f* = (bp - q) / b
        Where:
            f* = fraction of bankroll to bet
            b = decimal odds - 1 (net profit per unit bet)
            p = true probability of winning
            q = 1 - p (probability of losing)

        Returns:
            Kelly fraction (0-1, multiply by bankroll for bet size)
        """
        b = decimal_odds - 1  # Net odds
        p = true_probability
        q = 1 - p

        kelly = (b * p - q) / b

        # Never bet more than 100% of bankroll, never negative
        kelly = max(0, min(kelly, 1.0))

        return kelly

    def analyze_opportunity(
        self,
        opportunity: BettingOpportunity,
        bankroll: float = 10000
    ) -> BettingRecommendation:
        """
        Analyze a betting opportunity and return recommendation

        Args:
            opportunity: BettingOpportunity object
            bankroll: Current bankroll size (default $10,000)

        Returns:
            BettingRecommendation with complete analysis
        """
        # Convert odds
        decimal_odds = self.american_to_decimal(opportunity.market_odds)
        implied_prob = self.decimal_to_implied_probability(decimal_odds)

        # Adjust true probability by confidence
        adjusted_prob = opportunity.true_probability * opportunity.confidence

        # Calculate edge
        edge = adjusted_prob - implied_prob
        edge_percentage = edge * 100

        # Calculate EV
        ev_percentage, ev_dollars = self.calculate_expected_value(
            adjusted_prob,
            decimal_odds
        )

        # Calculate Kelly
        full_kelly = self.calculate_kelly_criterion(adjusted_prob, decimal_odds)
        conservative_kelly = full_kelly * self.kelly_fraction
        recommended_bet_size = conservative_kelly * bankroll

        # Determine bet decision
        if ev_percentage >= self.min_ev and edge >= self.min_edge:
            bet_decision = 'BET'
        elif ev_percentage > 0:
            bet_decision = 'PASS'  # Positive EV but below threshold
        else:
            bet_decision = 'AVOID'  # Negative EV

        # Determine confidence tier
        if ev_percentage >= self.high_confidence_threshold:
            confidence_tier = 'HIGH'
        elif ev_percentage >= self.medium_confidence_threshold:
            confidence_tier = 'MEDIUM'
        elif ev_percentage >= self.min_ev:
            confidence_tier = 'LOW'
        else:
            confidence_tier = 'NONE'

        return BettingRecommendation(
            game_id=opportunity.game_id,
            team_name=opportunity.team_name,
            bet_type=opportunity.bet_type,
            market_odds=opportunity.market_odds,
            market_line=opportunity.market_line,
            predicted_line=opportunity.predicted_line,
            true_probability=opportunity.true_probability,
            implied_probability=implied_prob,
            expected_value=ev_percentage,
            ev_dollars=ev_dollars,
            kelly_fraction=full_kelly,
            recommended_bet_size=recommended_bet_size,
            edge_percentage=edge_percentage,
            bet_decision=bet_decision,
            confidence_tier=confidence_tier
        )

    def analyze_multiple_opportunities(
        self,
        opportunities: list[BettingOpportunity],
        bankroll: float = 10000,
        max_total_exposure: float = 0.10  # Max 10% of bankroll across all bets
    ) -> list[BettingRecommendation]:
        """
        Analyze multiple betting opportunities and adjust for total exposure

        Args:
            opportunities: List of BettingOpportunity objects
            bankroll: Current bankroll size
            max_total_exposure: Maximum fraction of bankroll to risk across all bets

        Returns:
            List of BettingRecommendation objects, sorted by EV descending
        """
        recommendations = []

        # Analyze each opportunity
        for opp in opportunities:
            rec = self.analyze_opportunity(opp, bankroll)
            if rec.bet_decision == 'BET':
                recommendations.append(rec)

        # Sort by EV descending
        recommendations.sort(key=lambda x: x.expected_value, reverse=True)

        # Adjust bet sizes if total exposure exceeds maximum
        total_exposure = sum(rec.recommended_bet_size for rec in recommendations)
        max_exposure_dollars = bankroll * max_total_exposure

        if total_exposure > max_exposure_dollars:
            # Scale down all bets proportionally
            scale_factor = max_exposure_dollars / total_exposure
            for rec in recommendations:
                rec.recommended_bet_size *= scale_factor

        return recommendations

    def format_recommendation(self, rec: BettingRecommendation) -> str:
        """Format a recommendation as a readable string"""
        lines = [
            f"{'='*60}",
            f"GAME: {rec.game_id}",
            f"TEAM: {rec.team_name}",
            f"BET TYPE: {rec.bet_type}",
            f"{'='*60}",
            f"Market Odds: {rec.market_odds:+.0f}",
        ]

        if rec.market_line is not None:
            lines.append(f"Market Line: {rec.market_line:+.1f}")
        if rec.predicted_line is not None:
            lines.append(f"Predicted Line: {rec.predicted_line:+.1f}")

        lines.extend([
            f"",
            f"PROBABILITIES:",
            f"  True Probability: {rec.true_probability*100:.1f}%",
            f"  Implied Probability: {rec.implied_probability*100:.1f}%",
            f"  Edge: {rec.edge_percentage:+.2f}%",
            f"",
            f"EXPECTED VALUE:",
            f"  EV: {rec.expected_value:+.2f}%",
            f"  EV per $100: ${rec.ev_dollars:+.2f}",
            f"",
            f"BET SIZING:",
            f"  Full Kelly: {rec.kelly_fraction*100:.2f}%",
            f"  Recommended Bet: ${rec.recommended_bet_size:.2f}",
            f"",
            f"DECISION: {rec.bet_decision} ({rec.confidence_tier} CONFIDENCE)",
            f"{'='*60}",
        ])

        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    # Initialize calculator
    calc = EVCalculator(
        kelly_fraction=0.25,  # Quarter Kelly (conservative)
        min_edge=0.02,  # 2% minimum edge
        min_ev=2.0  # 2% minimum EV
    )

    # Example opportunity: Model predicts 55% chance of covering, odds are -110
    opportunity = BettingOpportunity(
        game_id="LAL_vs_BOS_2025_01_15",
        team_name="Lakers",
        bet_type="spread",
        market_odds=-110,
        true_probability=0.55,  # 55% chance to cover
        market_line=-5.5,
        predicted_line=-3.5,
        confidence=0.9
    )

    # Analyze
    recommendation = calc.analyze_opportunity(opportunity, bankroll=10000)

    # Print formatted result
    print(calc.format_recommendation(recommendation))

    # Example with multiple opportunities
    print("\n\n" + "="*60)
    print("ANALYZING MULTIPLE OPPORTUNITIES")
    print("="*60 + "\n")

    opportunities = [
        BettingOpportunity(
            game_id="LAL_vs_BOS",
            team_name="Lakers",
            bet_type="spread",
            market_odds=-110,
            true_probability=0.58,
            market_line=-5.5,
            predicted_line=-3.0
        ),
        BettingOpportunity(
            game_id="GSW_vs_DEN",
            team_name="Warriors",
            bet_type="total_over",
            market_odds=-105,
            true_probability=0.56,
            market_line=225.5,
            predicted_line=228.0
        ),
        BettingOpportunity(
            game_id="MIA_vs_PHX",
            team_name="Heat",
            bet_type="moneyline",
            market_odds=+150,
            true_probability=0.45,
            market_line=None,
            predicted_line=None
        ),
    ]

    recommendations = calc.analyze_multiple_opportunities(
        opportunities,
        bankroll=10000,
        max_total_exposure=0.10
    )

    for rec in recommendations:
        print(calc.format_recommendation(rec))
        print("\n")
