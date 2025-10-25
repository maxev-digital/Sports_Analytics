"""
Multi-Sport Betting Strategy Ensemble
Adapts betting strategies across NBA, NHL, NFL, and MLB
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Literal
from datetime import datetime
import numpy as np


SportType = Literal['nba', 'nhl', 'nfl', 'mlb']


@dataclass
class SportConfig:
    """Configuration for sport-specific parameters"""
    name: str
    periods: int  # Number of periods/quarters/innings
    period_length: float  # Minutes per period (for pacing)
    typical_scoring_rate: float  # Points per period
    home_advantage: float  # Home court/field/ice advantage
    pace_variance: float  # How much pace varies (higher = more variance)

    # Sport-specific factors
    overtime_enabled: bool = True
    shootout_enabled: bool = False  # NHL specific
    innings_variable: bool = False  # MLB specific (can end in 9th)


# Sport configurations
SPORT_CONFIGS: Dict[SportType, SportConfig] = {
    'nba': SportConfig(
        name='NBA',
        periods=4,
        period_length=12.0,
        typical_scoring_rate=27.5,  # ~110 points / 4 quarters
        home_advantage=2.5,
        pace_variance=0.15,
        overtime_enabled=True
    ),
    'nhl': SportConfig(
        name='NHL',
        periods=3,
        period_length=20.0,
        typical_scoring_rate=2.0,  # ~6 goals / 3 periods
        home_advantage=0.3,
        pace_variance=0.25,
        overtime_enabled=True,
        shootout_enabled=True
    ),
    'nfl': SportConfig(
        name='NFL',
        periods=4,
        period_length=15.0,
        typical_scoring_rate=5.5,  # ~22 points / 4 quarters
        home_advantage=2.8,
        pace_variance=0.20,
        overtime_enabled=True
    ),
    'mlb': SportConfig(
        name='MLB',
        periods=9,
        period_length=20.0,  # Approximate minutes per inning
        typical_scoring_rate=0.5,  # ~4.5 runs / 9 innings
        home_advantage=0.15,
        pace_variance=0.30,
        overtime_enabled=True,
        innings_variable=True
    )
}


@dataclass
class TeamStats:
    """Universal team statistics across sports"""
    team_name: str
    sport: SportType

    # Offensive metrics
    offensive_rating: float  # Points/goals/runs per game
    pace: float  # Possessions/shots/plate appearances per game
    efficiency: float  # Scoring efficiency (points per possession)

    # Defensive metrics
    defensive_rating: float  # Points allowed per game
    defensive_efficiency: float  # Opponent scoring efficiency

    # Situational metrics
    home_record: tuple[int, int]  # (wins, losses)
    away_record: tuple[int, int]
    rest_days: int = 1
    injuries_impact: float = 0.0  # -1.0 to 1.0 (negative = hurt by injuries)

    # Recent form
    last_5_games: List[bool] = None  # True = Win, False = Loss
    scoring_trend: float = 0.0  # +/- from season average


@dataclass
class UniversalPrediction:
    """Prediction format that works across all sports"""
    sport: SportType
    game_id: str
    game_date: datetime

    home_team: str
    away_team: str

    # Total predictions
    predicted_total: float
    market_total: Optional[float] = None
    total_edge: Optional[float] = None
    total_recommendation: Optional[str] = None  # OVER/UNDER
    total_confidence: str = 'LOW'  # LOW/MEDIUM/HIGH

    # Spread predictions
    predicted_spread: float  # Positive = home favored
    market_spread: Optional[float] = None
    spread_edge: Optional[float] = None
    spread_recommendation: Optional[str] = None  # HOME/AWAY
    spread_confidence: str = 'LOW'

    # Moneyline predictions
    home_win_prob: float  # 0.0 to 1.0
    away_win_prob: float
    market_home_odds: Optional[int] = None  # American odds
    market_away_odds: Optional[int] = None
    ml_edge: Optional[float] = None
    ml_recommendation: Optional[str] = None  # HOME/AWAY
    ml_confidence: str = 'LOW'

    # Breakdown
    prediction_factors: Dict[str, float] = None



class MultiSportEnsemble:
    """
    Ensemble betting strategy system that works across NBA, NHL, NFL, and MLB

    Adapts prediction models to sport-specific characteristics while maintaining
    consistent betting logic and edge detection.
    """

    def __init__(
        self,
        min_total_edge: float = 3.0,
        min_spread_edge: float = 2.0,
        min_ml_edge: float = 0.05,
        confidence_thresholds: Dict[str, float] = None
    ):
        """
        Initialize multi-sport ensemble

        Args:
            min_total_edge: Minimum edge to recommend total bets
            min_spread_edge: Minimum edge to recommend spread bets
            min_ml_edge: Minimum edge (as probability) for moneyline bets
            confidence_thresholds: Custom confidence levels by metric
        """
        self.min_total_edge = min_total_edge
        self.min_spread_edge = min_spread_edge
        self.min_ml_edge = min_ml_edge

        self.confidence_thresholds = confidence_thresholds or {
            'total_high': 5.0,
            'total_medium': 3.0,
            'spread_high': 3.0,
            'spread_medium': 2.0,
            'ml_high': 0.10,
            'ml_medium': 0.05
        }

    def predict_game(
        self,
        sport: SportType,
        home_team: TeamStats,
        away_team: TeamStats,
        game_id: str,
        game_date: datetime,
        market_total: Optional[float] = None,
        market_spread: Optional[float] = None,
        market_home_odds: Optional[int] = None,
        market_away_odds: Optional[int] = None
    ) -> UniversalPrediction:
        """
        Generate predictions for any sport

        Args:
            sport: Sport type (nba, nhl, nfl, mlb)
            home_team: Home team statistics
            away_team: Away team statistics
            game_id: Unique game identifier
            game_date: Game date/time
            market_total: Current betting line for total
            market_spread: Current spread (positive = home favored)
            market_home_odds: American odds for home team
            market_away_odds: American odds for away team

        Returns:
            UniversalPrediction with all betting recommendations
        """
        config = SPORT_CONFIGS[sport]

        # Calculate predicted total
        predicted_total = self._calculate_total(sport, home_team, away_team, config)

        # Calculate predicted spread
        predicted_spread = self._calculate_spread(sport, home_team, away_team, config)

        # Calculate win probabilities
        home_win_prob, away_win_prob = self._calculate_win_probabilities(
            predicted_spread, config
        )

        # Analyze edges
        total_edge = None
        total_rec = None
        total_conf = 'LOW'
        if market_total:
            total_edge = abs(predicted_total - market_total)
            if total_edge >= self.min_total_edge:
                total_rec = 'OVER' if predicted_total > market_total else 'UNDER'
                if total_edge >= self.confidence_thresholds['total_high']:
                    total_conf = 'HIGH'
                elif total_edge >= self.confidence_thresholds['total_medium']:
                    total_conf = 'MEDIUM'

        spread_edge = None
        spread_rec = None
        spread_conf = 'LOW'
        if market_spread:
            spread_edge = abs(predicted_spread - market_spread)
            if spread_edge >= self.min_spread_edge:
                # If predicted spread is more favorable to home than market
                spread_rec = 'HOME' if predicted_spread > market_spread else 'AWAY'
                if spread_edge >= self.confidence_thresholds['spread_high']:
                    spread_conf = 'HIGH'
                elif spread_edge >= self.confidence_thresholds['spread_medium']:
                    spread_conf = 'MEDIUM'

        ml_edge = None
        ml_rec = None
        ml_conf = 'LOW'
        if market_home_odds and market_away_odds:
            # Convert American odds to implied probabilities
            home_implied = self._odds_to_prob(market_home_odds)
            away_implied = self._odds_to_prob(market_away_odds)

            # Calculate edge (our prob vs implied prob)
            home_edge = home_win_prob - home_implied
            away_edge = away_win_prob - away_implied

            ml_edge = max(abs(home_edge), abs(away_edge))
            if ml_edge >= self.min_ml_edge:
                ml_rec = 'HOME' if home_edge > away_edge else 'AWAY'
                if ml_edge >= self.confidence_thresholds['ml_high']:
                    ml_conf = 'HIGH'
                elif ml_edge >= self.confidence_thresholds['ml_medium']:
                    ml_conf = 'MEDIUM'

        # Build prediction factors
        factors = {
            'home_offensive_rating': home_team.offensive_rating,
            'away_offensive_rating': away_team.offensive_rating,
            'home_defensive_rating': home_team.defensive_rating,
            'away_defensive_rating': away_team.defensive_rating,
            'home_advantage': config.home_advantage,
            'pace_factor': (home_team.pace + away_team.pace) / 2,
            'rest_differential': home_team.rest_days - away_team.rest_days,
            'injury_impact': home_team.injuries_impact - away_team.injuries_impact
        }

        return UniversalPrediction(
            sport=sport,
            game_id=game_id,
            game_date=game_date,
            home_team=home_team.team_name,
            away_team=away_team.team_name,
            predicted_total=predicted_total,
            market_total=market_total,
            total_edge=total_edge,
            total_recommendation=total_rec,
            total_confidence=total_conf,
            predicted_spread=predicted_spread,
            market_spread=market_spread,
            spread_edge=spread_edge,
            spread_recommendation=spread_rec,
            spread_confidence=spread_conf,
            home_win_prob=home_win_prob,
            away_win_prob=away_win_prob,
            market_home_odds=market_home_odds,
            market_away_odds=market_away_odds,
            ml_edge=ml_edge,
            ml_recommendation=ml_rec,
            ml_confidence=ml_conf,
            prediction_factors=factors
        )

    def _calculate_total(
        self,
        sport: SportType,
        home_team: TeamStats,
        away_team: TeamStats,
        config: SportConfig
    ) -> float:
        """Calculate predicted total score/goals/runs"""

        # Calculate expected pace (geometric mean)
        expected_pace = np.sqrt(home_team.pace * away_team.pace)

        # Adjust for rest days
        rest_adjustment = self._calculate_rest_adjustment(
            home_team.rest_days,
            away_team.rest_days,
            config.pace_variance
        )
        expected_pace *= (1 + rest_adjustment)

        # Calculate home team expected points
        # Home offensive rating vs away defensive rating
        league_avg = config.typical_scoring_rate * config.periods

        home_expected = (
            home_team.offensive_rating +  # Team's offensive strength
            (league_avg - away_team.defensive_rating) +  # Opponent's defensive weakness
            config.home_advantage +  # Home advantage
            home_team.scoring_trend +  # Recent form
            (home_team.injuries_impact * -2.0)  # Injury impact
        )

        # Calculate away team expected points
        away_expected = (
            away_team.offensive_rating +
            (league_avg - home_team.defensive_rating) +
            away_team.scoring_trend +
            (away_team.injuries_impact * -2.0)
        )

        # Pace adjustment (higher pace = more scoring)
        pace_factor = expected_pace / (league_avg / config.typical_scoring_rate)

        predicted_total = (home_expected + away_expected) * pace_factor

        # Sport-specific adjustments
        if sport == 'nhl':
            # Hockey is lower scoring, more variance
            predicted_total *= 0.95  # Slight deflation for NHL
        elif sport == 'mlb':
            # Baseball totals are very pitcher-dependent
            # This would ideally incorporate pitcher stats
            predicted_total *= 1.0  # Placeholder for pitcher adjustments
        elif sport == 'nfl':
            # Football is very matchup dependent
            # Weather would be a factor here
            predicted_total *= 1.0  # Placeholder for weather/conditions

        return round(predicted_total, 1)

    def _calculate_spread(
        self,
        sport: SportType,
        home_team: TeamStats,
        away_team: TeamStats,
        config: SportConfig
    ) -> float:
        """Calculate predicted point spread (positive = home favored)"""

        league_avg = config.typical_scoring_rate * config.periods

        # Home team strength
        home_strength = (
            home_team.offensive_rating -
            (away_team.defensive_rating - league_avg) +
            config.home_advantage +
            home_team.scoring_trend +
            (home_team.injuries_impact * -2.0)
        )

        # Away team strength
        away_strength = (
            away_team.offensive_rating -
            (home_team.defensive_rating - league_avg) +
            away_team.scoring_trend +
            (away_team.injuries_impact * -2.0)
        )

        predicted_spread = home_strength - away_strength

        # Rest advantage
        rest_diff = home_team.rest_days - away_team.rest_days
        if rest_diff > 0:
            predicted_spread += (rest_diff * 0.5)
        elif rest_diff < 0:
            predicted_spread += (rest_diff * 0.5)

        # Recent form adjustment
        if home_team.last_5_games and away_team.last_5_games:
            home_form = sum(home_team.last_5_games) / len(home_team.last_5_games)
            away_form = sum(away_team.last_5_games) / len(away_team.last_5_games)
            form_diff = (home_form - away_form) * 2.0  # Scale form difference
            predicted_spread += form_diff

        return round(predicted_spread, 1)

    def _calculate_win_probabilities(
        self,
        predicted_spread: float,
        config: SportConfig
    ) -> tuple[float, float]:
        """
        Convert predicted spread to win probabilities

        Uses logistic function to convert point spread to win probability
        """
        # Standard deviation of point differential varies by sport
        std_dev_map = {
            'nba': 12.0,
            'nhl': 1.8,
            'nfl': 13.5,
            'mlb': 2.0
        }

        std_dev = std_dev_map.get(config.name.lower(), 12.0)

        # Logistic function: P(home wins) = 1 / (1 + exp(-spread/std_dev))
        home_prob = 1 / (1 + np.exp(-predicted_spread / std_dev))
        away_prob = 1 - home_prob

        return round(home_prob, 3), round(away_prob, 3)

    def _calculate_rest_adjustment(
        self,
        home_rest: int,
        away_rest: int,
        pace_variance: float
    ) -> float:
        """Calculate pace adjustment based on rest days"""

        # Both teams well-rested: slightly faster pace
        if home_rest >= 2 and away_rest >= 2:
            return 0.02 * pace_variance

        # Both teams tired: slightly slower
        if home_rest == 0 and away_rest == 0:
            return -0.03 * pace_variance

        # One team rested, one tired: neutral
        return 0.0

    def _odds_to_prob(self, american_odds: int) -> float:
        """Convert American odds to implied probability"""
        if american_odds > 0:
            # Underdog: 100 / (odds + 100)
            return 100 / (american_odds + 100)
        else:
            # Favorite: abs(odds) / (abs(odds) + 100)
            return abs(american_odds) / (abs(american_odds) + 100)

    def batch_predict(
        self,
        games: List[Dict]
    ) -> List[UniversalPrediction]:
        """
        Generate predictions for multiple games across sports

        Args:
            games: List of game dictionaries containing:
                - sport: SportType
                - home_team: TeamStats
                - away_team: TeamStats
                - game_id: str
                - game_date: datetime
                - market_total: Optional[float]
                - market_spread: Optional[float]
                - market_home_odds: Optional[int]
                - market_away_odds: Optional[int]

        Returns:
            List of UniversalPrediction objects
        """
        predictions = []

        for game in games:
            pred = self.predict_game(
                sport=game['sport'],
                home_team=game['home_team'],
                away_team=game['away_team'],
                game_id=game['game_id'],
                game_date=game['game_date'],
                market_total=game.get('market_total'),
                market_spread=game.get('market_spread'),
                market_home_odds=game.get('market_home_odds'),
                market_away_odds=game.get('market_away_odds')
            )
            predictions.append(pred)

        return predictions

    def filter_best_bets(
        self,
        predictions: List[UniversalPrediction],
        min_confidence: str = 'MEDIUM',
        max_bets: int = 10
    ) -> List[UniversalPrediction]:
        """
        Filter predictions to only high-value bets

        Args:
            predictions: List of predictions
            min_confidence: Minimum confidence level (LOW/MEDIUM/HIGH)
            max_bets: Maximum number of bets to return

        Returns:
            Filtered and sorted list of best bets
        """
        confidence_order = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        min_conf_level = confidence_order[min_confidence]

        # Collect all potential bets
        bets = []

        for pred in predictions:
            # Total bets
            if pred.total_recommendation:
                if confidence_order[pred.total_confidence] >= min_conf_level:
                    bets.append({
                        'prediction': pred,
                        'bet_type': 'TOTAL',
                        'confidence': pred.total_confidence,
                        'edge': pred.total_edge
                    })

            # Spread bets
            if pred.spread_recommendation:
                if confidence_order[pred.spread_confidence] >= min_conf_level:
                    bets.append({
                        'prediction': pred,
                        'bet_type': 'SPREAD',
                        'confidence': pred.spread_confidence,
                        'edge': pred.spread_edge
                    })

            # Moneyline bets
            if pred.ml_recommendation:
                if confidence_order[pred.ml_confidence] >= min_conf_level:
                    bets.append({
                        'prediction': pred,
                        'bet_type': 'MONEYLINE',
                        'confidence': pred.ml_confidence,
                        'edge': pred.ml_edge * 100  # Convert to percentage for sorting
                    })

        # Sort by confidence (HIGH first) then by edge
        bets.sort(
            key=lambda x: (confidence_order[x['confidence']], x['edge']),
            reverse=True
        )

        # Return top bets
        return [bet['prediction'] for bet in bets[:max_bets]]


# Example usage and testing
if __name__ == "__main__":
    ensemble = MultiSportEnsemble()

    # Example NBA game
    print("=" * 80)
    print("NBA Example: Lakers vs Celtics")
    print("=" * 80)

    lakers = TeamStats(
        team_name='Lakers',
        sport='nba',
        offensive_rating=115.2,
        pace=101.5,
        efficiency=1.13,
        defensive_rating=110.8,
        defensive_efficiency=1.09,
        home_record=(20, 5),
        away_record=(15, 10),
        rest_days=2,
        injuries_impact=-0.2,
        last_5_games=[True, True, False, True, True],
        scoring_trend=2.1
    )

    celtics = TeamStats(
        team_name='Celtics',
        sport='nba',
        offensive_rating=118.5,
        pace=98.2,
        efficiency=1.21,
        defensive_rating=108.2,
        defensive_efficiency=1.10,
        home_record=(22, 3),
        away_record=(18, 7),
        rest_days=1,
        injuries_impact=0.0,
        last_5_games=[True, True, True, False, True],
        scoring_trend=3.5
    )

    nba_pred = ensemble.predict_game(
        sport='nba',
        home_team=lakers,
        away_team=celtics,
        game_id='nba_20250117_bos_lal',
        game_date=datetime(2025, 1, 17, 19, 30),
        market_total=225.5,
        market_spread=-2.5,  # Lakers favored by 2.5
        market_home_odds=-130,
        market_away_odds=+110
    )

    print(f"\nPredicted Total: {nba_pred.predicted_total} (Market: {nba_pred.market_total})")
    print(f"Total Edge: {nba_pred.total_edge} points")
    print(f"Recommendation: {nba_pred.total_recommendation} ({nba_pred.total_confidence} confidence)")
    print(f"\nPredicted Spread: {nba_pred.predicted_spread} (Market: {nba_pred.market_spread})")
    print(f"Spread Edge: {nba_pred.spread_edge} points")
    print(f"Recommendation: {nba_pred.spread_recommendation} ({nba_pred.spread_confidence} confidence)")
    print(f"\nWin Probabilities: Lakers {nba_pred.home_win_prob:.1%} | Celtics {nba_pred.away_win_prob:.1%}")
    print(f"ML Recommendation: {nba_pred.ml_recommendation} ({nba_pred.ml_confidence} confidence)")

    # Example NHL game
    print("\n" + "=" * 80)
    print("NHL Example: Maple Leafs vs Bruins")
    print("=" * 80)

    leafs = TeamStats(
        team_name='Maple Leafs',
        sport='nhl',
        offensive_rating=3.2,  # Goals per game
        pace=62.0,  # Shots per game
        efficiency=0.052,  # Shooting percentage
        defensive_rating=2.8,
        defensive_efficiency=0.045,
        home_record=(18, 7, 2),
        away_record=(12, 10, 5),
        rest_days=1,
        injuries_impact=-0.1,
        last_5_games=[True, False, True, True, True],
        scoring_trend=0.3
    )

    bruins = TeamStats(
        team_name='Bruins',
        sport='nhl',
        offensive_rating=3.4,
        pace=58.5,
        efficiency=0.058,
        defensive_rating=2.5,
        defensive_efficiency=0.043,
        home_record=(20, 5, 2),
        away_record=(15, 8, 4),
        rest_days=2,
        injuries_impact=0.0,
        last_5_games=[True, True, False, True, True],
        scoring_trend=0.5
    )

    nhl_pred = ensemble.predict_game(
        sport='nhl',
        home_team=leafs,
        away_team=bruins,
        game_id='nhl_20250117_bos_tor',
        game_date=datetime(2025, 1, 17, 19, 0),
        market_total=6.5,
        market_spread=-0.5,  # Leafs slight favorite
        market_home_odds=-115,
        market_away_odds=-105
    )

    print(f"\nPredicted Total: {nhl_pred.predicted_total} (Market: {nhl_pred.market_total})")
    print(f"Total Edge: {nhl_pred.total_edge} goals")
    print(f"Recommendation: {nhl_pred.total_recommendation} ({nhl_pred.total_confidence} confidence)")
    print(f"\nPredicted Spread: {nhl_pred.predicted_spread} (Market: {nhl_pred.market_spread})")
    print(f"Win Probabilities: Leafs {nhl_pred.home_win_prob:.1%} | Bruins {nhl_pred.away_win_prob:.1%}")

    print("\n" + "=" * 80)
    print("Multi-Sport Ensemble System Created Successfully!")
    print("=" * 80)
    print("\nSupported Sports:")
    for sport, config in SPORT_CONFIGS.items():
        print(f"  • {config.name}: {config.periods} periods, {config.typical_scoring_rate} pts/period")
    print("\nFeatures:")
    print("  ✓ Universal prediction format across all sports")
    print("  ✓ Sport-specific pace and efficiency adjustments")
    print("  ✓ Total, spread, and moneyline analysis")
    print("  ✓ Confidence-based bet filtering")
    print("  ✓ Rest day and injury impact modeling")
    print("  ✓ Recent form tracking")
    print("  ✓ Home advantage adjustments")
