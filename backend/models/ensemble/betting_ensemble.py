"""
Ensemble Model for Betting Strategy
Combines multiple betting strategies using weighted voting and confidence scoring
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import numpy as np
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from strategies.pace_based_strategy import PaceBasedStrategy, MatchupContext as PaceMatchup
from strategies.fatigue_strategy import FatigueStrategy, ScheduleContext
from strategies.regression_strategy import RegressionStrategy, PerformanceHistory
from utils.ev_calculator import EVCalculator, BettingOpportunity, BettingRecommendation


@dataclass
class GameData:
    """Complete game data for ensemble analysis"""
    game_id: str
    home_team: str
    away_team: str
    game_time: str

    # Market data
    market_total: float
    market_total_odds: float  # Odds for over/under
    market_spread: Optional[float] = None
    market_spread_odds: Optional[float] = None

    # Pace data
    home_pace: float = 100.0
    away_pace: float = 100.0
    home_off_rating: float = 110.0
    away_off_rating: float = 110.0
    home_def_rating: float = 110.0
    away_def_rating: float = 110.0

    # Schedule/Fatigue data
    home_rest_days: int = 1
    away_rest_days: int = 1
    home_back_to_back: bool = False
    away_back_to_back: bool = False
    home_miles_traveled: float = 0.0
    away_miles_traveled: float = 0.0
    home_time_zones: int = 0
    away_time_zones: int = 0
    home_games_last_7: int = 3
    away_games_last_7: int = 3

    # Performance history data
    home_season_ppg: float = 110.0
    away_season_ppg: float = 110.0
    home_last_5_ppg: float = 110.0
    away_last_5_ppg: float = 110.0
    home_season_papg: float = 110.0  # Points allowed per game
    away_season_papg: float = 110.0
    home_last_5_papg: float = 110.0
    away_last_5_papg: float = 110.0
    home_fg_pct_season: float = 0.46
    away_fg_pct_season: float = 0.46
    home_fg_pct_last_5: float = 0.46
    away_fg_pct_last_5: float = 0.46
    home_3pt_pct_season: float = 0.36
    away_3pt_pct_season: float = 0.36
    home_3pt_pct_last_5: float = 0.36
    away_3pt_pct_last_5: float = 0.36


@dataclass
class EnsemblePrediction:
    """Final ensemble prediction combining all strategies"""
    game_id: str
    home_team: str
    away_team: str

    # Predictions
    predicted_total: float
    market_total: float
    edge: float
    edge_percentage: float

    # Individual strategy predictions
    pace_prediction: float
    fatigue_prediction: float
    regression_prediction: float

    # Strategy weights used
    pace_weight: float
    fatigue_weight: float
    regression_weight: float

    # Overall confidence
    confidence: float
    confidence_tier: str  # HIGH, MEDIUM, LOW

    # Recommendation
    recommendation: str  # OVER, UNDER, PASS
    bet_decision: str  # BET, PASS, AVOID

    # EV Analysis
    expected_value: float
    recommended_bet_size: float

    # Reasoning
    key_factors: list[str]
    strategy_insights: Dict[str, Any]


class BettingEnsemble:
    """
    Ensemble model combining multiple betting strategies

    Uses weighted voting based on confidence and historical performance
    """

    def __init__(
        self,
        pace_weight: float = 0.40,
        fatigue_weight: float = 0.30,
        regression_weight: float = 0.30,
        min_edge: float = 3.0,  # Minimum edge to recommend bet
        min_confidence: float = 0.50,  # Minimum confidence to recommend
        confidence_boost_agreement: float = 0.15,  # Boost when strategies agree
    ):
        """
        Initialize Betting Ensemble

        Args:
            pace_weight: Weight for pace-based strategy
            fatigue_weight: Weight for fatigue strategy
            regression_weight: Weight for regression strategy
            min_edge: Minimum edge required to recommend bet
            min_confidence: Minimum confidence required
            confidence_boost_agreement: Confidence boost when all strategies agree
        """
        self.pace_weight = pace_weight
        self.fatigue_weight = fatigue_weight
        self.regression_weight = regression_weight
        self.min_edge = min_edge
        self.min_confidence = min_confidence
        self.confidence_boost_agreement = confidence_boost_agreement

        # Initialize individual strategies
        self.pace_strategy = PaceBasedStrategy()
        self.fatigue_strategy = FatigueStrategy()
        self.regression_strategy = RegressionStrategy()
        self.ev_calculator = EVCalculator(min_edge=0.02, min_ev=2.0)

    def _prepare_pace_data(self, game: GameData) -> PaceMatchup:
        """Convert GameData to PaceMatchup format"""
        from strategies.pace_based_strategy import TeamStats

        home_team = TeamStats(
            team_name=game.home_team,
            pace=game.home_pace,
            off_rating=game.home_off_rating,
            def_rating=game.home_def_rating,
            rest_days=game.home_rest_days,
            back_to_back=game.home_back_to_back
        )

        away_team = TeamStats(
            team_name=game.away_team,
            pace=game.away_pace,
            off_rating=game.away_off_rating,
            def_rating=game.away_def_rating,
            rest_days=game.away_rest_days,
            back_to_back=game.away_back_to_back
        )

        return PaceMatchup(
            home_team=home_team,
            away_team=away_team,
            league_avg_pace=100.0,
            league_avg_rating=112.0,
            home_court_advantage=2.5
        )

    def _prepare_fatigue_data(self, game: GameData) -> tuple[ScheduleContext, ScheduleContext]:
        """Convert GameData to ScheduleContext format"""
        home_schedule = ScheduleContext(
            team_name=game.home_team,
            rest_days=game.home_rest_days,
            back_to_back=game.home_back_to_back,
            three_in_four=game.home_games_last_7 >= 3,
            four_in_five=game.home_games_last_7 >= 4,
            miles_traveled=game.home_miles_traveled,
            time_zone_changes=game.home_time_zones,
            home_game=True,
            games_last_7_days=game.home_games_last_7,
            games_last_14_days=game.home_games_last_7 * 2  # Estimate
        )

        away_schedule = ScheduleContext(
            team_name=game.away_team,
            rest_days=game.away_rest_days,
            back_to_back=game.away_back_to_back,
            three_in_four=game.away_games_last_7 >= 3,
            four_in_five=game.away_games_last_7 >= 4,
            miles_traveled=game.away_miles_traveled,
            time_zone_changes=game.away_time_zones,
            home_game=False,
            games_last_7_days=game.away_games_last_7,
            games_last_14_days=game.away_games_last_7 * 2
        )

        return home_schedule, away_schedule

    def _prepare_regression_data(self, game: GameData) -> tuple[PerformanceHistory, PerformanceHistory]:
        """Convert GameData to PerformanceHistory format"""
        home_history = PerformanceHistory(
            team_name=game.home_team,
            season_avg_points=game.home_season_ppg,
            season_avg_allowed=game.home_season_papg,
            last_5_avg_points=game.home_last_5_ppg,
            last_5_avg_allowed=game.home_last_5_papg,
            last_10_avg_points=(game.home_season_ppg + game.home_last_5_ppg) / 2,
            last_10_avg_allowed=(game.home_season_papg + game.home_last_5_papg) / 2,
            shooting_pct_season=game.home_fg_pct_season,
            shooting_pct_last_5=game.home_fg_pct_last_5,
            three_pt_pct_season=game.home_3pt_pct_season,
            three_pt_pct_last_5=game.home_3pt_pct_last_5,
            opponent_shooting_pct_season=0.46,  # League average
            opponent_shooting_pct_last_5=game.away_fg_pct_last_5
        )

        away_history = PerformanceHistory(
            team_name=game.away_team,
            season_avg_points=game.away_season_ppg,
            season_avg_allowed=game.away_season_papg,
            last_5_avg_points=game.away_last_5_ppg,
            last_5_avg_allowed=game.away_last_5_papg,
            last_10_avg_points=(game.away_season_ppg + game.away_last_5_ppg) / 2,
            last_10_avg_allowed=(game.away_season_papg + game.away_last_5_papg) / 2,
            shooting_pct_season=game.away_fg_pct_season,
            shooting_pct_last_5=game.away_fg_pct_last_5,
            three_pt_pct_season=game.away_3pt_pct_season,
            three_pt_pct_last_5=game.away_3pt_pct_last_5,
            opponent_shooting_pct_season=0.46,
            opponent_shooting_pct_last_5=game.home_fg_pct_last_5
        )

        return home_history, away_history

    def predict(self, game: GameData, bankroll: float = 10000) -> EnsemblePrediction:
        """
        Generate ensemble prediction for a game

        Args:
            game: GameData object with all game information
            bankroll: Current bankroll for bet sizing

        Returns:
            EnsemblePrediction with complete analysis
        """
        # Get predictions from each strategy
        pace_matchup = self._prepare_pace_data(game)
        pace_analysis = self.pace_strategy.analyze_total_opportunity(
            pace_matchup,
            game.market_total
        )

        home_fatigue, away_fatigue = self._prepare_fatigue_data(game)
        fatigue_analysis = self.fatigue_strategy.analyze_matchup(home_fatigue, away_fatigue)

        home_regression, away_regression = self._prepare_regression_data(game)
        regression_analysis = self.regression_strategy.analyze_matchup(
            home_regression,
            away_regression,
            game.market_total
        )

        # Extract predictions
        pace_pred = pace_analysis['predicted_total']
        fatigue_pred = game.market_total + fatigue_analysis['total_adjustment']
        regression_pred = regression_analysis['adjusted_expected_total']

        # Calculate weighted ensemble prediction
        ensemble_total = (
            pace_pred * self.pace_weight +
            fatigue_pred * self.fatigue_weight +
            regression_pred * self.regression_weight
        )

        # Calculate edge
        edge = ensemble_total - game.market_total
        edge_percentage = (edge / game.market_total) * 100

        # Aggregate confidence scores
        pace_conf = pace_analysis['confidence']
        fatigue_conf = (fatigue_analysis['home_prediction'].confidence +
                       fatigue_analysis['away_prediction'].confidence) / 2
        regression_conf = regression_analysis['confidence']

        # Weighted average confidence
        base_confidence = (
            pace_conf * self.pace_weight +
            fatigue_conf * self.fatigue_weight +
            regression_conf * self.regression_weight
        )

        # Check if all strategies agree on direction
        pace_direction = "OVER" if pace_pred > game.market_total else "UNDER"
        fatigue_direction = "OVER" if fatigue_pred > game.market_total else "UNDER"
        regression_direction = "OVER" if regression_pred > game.market_total else "UNDER"

        all_agree = (pace_direction == fatigue_direction == regression_direction)

        if all_agree:
            confidence = min(base_confidence + self.confidence_boost_agreement, 1.0)
        else:
            confidence = base_confidence * 0.85  # Reduce confidence when disagreement

        # Determine recommendation
        if abs(edge) >= self.min_edge and confidence >= self.min_confidence:
            recommendation = "OVER" if edge > 0 else "UNDER"
            bet_decision = "BET"
        elif abs(edge) >= self.min_edge * 0.6:
            recommendation = "LEAN_OVER" if edge > 0 else "LEAN_UNDER"
            bet_decision = "PASS"
        else:
            recommendation = "PASS"
            bet_decision = "PASS"

        # Confidence tier
        if confidence >= 0.75:
            confidence_tier = "HIGH"
        elif confidence >= 0.60:
            confidence_tier = "MEDIUM"
        else:
            confidence_tier = "LOW"

        # Calculate EV and bet sizing
        if bet_decision == "BET":
            # Estimate probability from ensemble prediction
            # Simple approach: use edge to infer probability advantage
            prob_adjustment = abs(edge) / game.market_total * 0.5
            implied_prob = 0.5  # Baseline for over/under

            if edge > 0:
                true_prob = min(implied_prob + prob_adjustment, 0.70)
            else:
                true_prob = min(implied_prob + prob_adjustment, 0.70)

            opportunity = BettingOpportunity(
                game_id=game.game_id,
                team_name=f"{game.home_team} vs {game.away_team}",
                bet_type="total_over" if edge > 0 else "total_under",
                market_odds=game.market_total_odds,
                true_probability=true_prob,
                market_line=game.market_total,
                predicted_line=ensemble_total,
                confidence=confidence
            )

            ev_rec = self.ev_calculator.analyze_opportunity(opportunity, bankroll)
            expected_value = ev_rec.expected_value
            recommended_bet_size = ev_rec.recommended_bet_size
        else:
            expected_value = 0.0
            recommended_bet_size = 0.0

        # Compile key factors
        key_factors = []

        if all_agree:
            key_factors.append(f"ALL STRATEGIES AGREE: {pace_direction}")

        # Add top factors from each strategy
        if pace_analysis.get('reasoning'):
            key_factors.append(f"Pace: {pace_analysis['reasoning'][:80]}")

        if fatigue_analysis.get('reasoning'):
            key_factors.append(f"Fatigue: {fatigue_analysis['reasoning'][:80]}")

        if regression_analysis.get('reasoning'):
            key_factors.append(f"Regression: {regression_analysis['reasoning'][:80]}")

        # Strategy insights
        strategy_insights = {
            "pace": {
                "predicted_total": pace_pred,
                "confidence": pace_conf,
                "scenario": pace_analysis['prediction'].scenario
            },
            "fatigue": {
                "predicted_total": fatigue_pred,
                "confidence": fatigue_conf,
                "edge_type": fatigue_analysis['edge_type']
            },
            "regression": {
                "predicted_total": regression_pred,
                "confidence": regression_conf,
                "direction": regression_analysis['regression_direction']
            }
        }

        return EnsemblePrediction(
            game_id=game.game_id,
            home_team=game.home_team,
            away_team=game.away_team,
            predicted_total=ensemble_total,
            market_total=game.market_total,
            edge=edge,
            edge_percentage=edge_percentage,
            pace_prediction=pace_pred,
            fatigue_prediction=fatigue_pred,
            regression_prediction=regression_pred,
            pace_weight=self.pace_weight,
            fatigue_weight=self.fatigue_weight,
            regression_weight=self.regression_weight,
            confidence=confidence,
            confidence_tier=confidence_tier,
            recommendation=recommendation,
            bet_decision=bet_decision,
            expected_value=expected_value,
            recommended_bet_size=recommended_bet_size,
            key_factors=key_factors,
            strategy_insights=strategy_insights
        )

    def format_prediction(self, pred: EnsemblePrediction) -> str:
        """Format prediction as readable string"""
        lines = [
            "=" * 80,
            f"ENSEMBLE PREDICTION: {pred.home_team} vs {pred.away_team}",
            "=" * 80,
            f"\nMarket Total: {pred.market_total}",
            f"Predicted Total: {pred.predicted_total:.1f}",
            f"Edge: {pred.edge:+.1f} ({pred.edge_percentage:+.1f}%)",
            f"\nRecommendation: {pred.recommendation}",
            f"Bet Decision: {pred.bet_decision}",
            f"Confidence: {pred.confidence:.2f} ({pred.confidence_tier})",
            f"\nExpected Value: {pred.expected_value:+.2f}%",
            f"Recommended Bet Size: ${pred.recommended_bet_size:.2f}",
            f"\nSTRATEGY BREAKDOWN:",
            f"  Pace Strategy: {pred.pace_prediction:.1f} (weight: {pred.pace_weight:.0%}, conf: {pred.strategy_insights['pace']['confidence']:.2f})",
            f"  Fatigue Strategy: {pred.fatigue_prediction:.1f} (weight: {pred.fatigue_weight:.0%}, conf: {pred.strategy_insights['fatigue']['confidence']:.2f})",
            f"  Regression Strategy: {pred.regression_prediction:.1f} (weight: {pred.regression_weight:.0%}, conf: {pred.strategy_insights['regression']['confidence']:.2f})",
            f"\nKEY FACTORS:",
        ]

        for factor in pred.key_factors:
            lines.append(f"  • {factor}")

        lines.append("=" * 80)

        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    # Initialize ensemble
    ensemble = BettingEnsemble(
        pace_weight=0.40,
        fatigue_weight=0.30,
        regression_weight=0.30
    )

    # Example game data
    game = GameData(
        game_id="LAL_BOS_2025_01_15",
        home_team="Lakers",
        away_team="Celtics",
        game_time="2025-01-15 19:00",
        market_total=225.5,
        market_total_odds=-110,
        # Pace data
        home_pace=102.0,
        away_pace=98.0,
        home_off_rating=116.0,
        away_off_rating=118.0,
        home_def_rating=112.0,
        away_def_rating=110.0,
        # Schedule data
        home_rest_days=2,
        away_rest_days=0,
        home_back_to_back=False,
        away_back_to_back=True,
        away_miles_traveled=2800,
        away_time_zones=3,
        # Performance data
        home_season_ppg=115.0,
        away_season_ppg=117.0,
        home_last_5_ppg=120.0,
        away_last_5_ppg=112.0,
        home_fg_pct_last_5=0.490,
        away_fg_pct_last_5=0.430
    )

    # Generate prediction
    prediction = ensemble.predict(game, bankroll=10000)

    # Print results
    print(ensemble.format_prediction(prediction))
