"""
NBA Quarter Reversal Strategy - ML-Powered Detection System

Detects momentum reversal patterns when a team dominates consecutive quarters.
Alerts when opponent is likely to win the next quarter based on historical data.

Strategy ROI (2023-24 Season Backtest):
- Q1-Q2 → Q3: 55.3% hit rate, +12.1% ROI
- Q2-Q3 → Q4: 52.7% hit rate, +8.9% ROI
- Q3-Q4 → OT: 60.7% hit rate, +35.2% ROI

Features:
- Multi-option recommendations (3-5 bets per alert)
- Price limit enforcement for each bet type
- Kelly Criterion bet sizing with risk profiles
- Variance-adjusted scoring for optimal bet selection
"""

from typing import Dict, List, Optional, Literal
from datetime import datetime
import logging
from strategies.bet_recommender import (
    create_quarter_reversal_options,
    recommend_best_bets,
    validate_price_limits
)

logger = logging.getLogger(__name__)


class QuarterReversalDetector:
    """Detects NBA quarter reversal opportunities with ML-enhanced predictions"""

    # Historical reversal rates from 2023-24 season backtest
    REVERSAL_RATES = {
        'Q1-Q2_to_Q3': 0.553,  # 55.3%
        'Q2-Q3_to_Q4': 0.527,  # 52.7%
        'Q3-Q4_to_OT': 0.607,  # 60.7%
    }

    # Expected ROI at -110 odds
    ROI_RATES = {
        'Q1-Q2_to_Q3': 0.121,  # +12.1%
        'Q2-Q3_to_Q4': 0.089,  # +8.9%
        'Q3-Q4_to_OT': 0.352,  # +35.2%
    }

    # Teams with highest reversal rates (61%+)
    HIGH_REVERSAL_TEAMS = {
        'Lakers': 0.611,
        'Warriors': 0.594,
        'Knicks': 0.571,
        'Celtics': 0.533,
        'Nuggets': 0.538,
    }

    # Price limits by strategy type (from NBA Quarter Reversal.md)
    PRICE_LIMITS = {
        'Q1-Q2_to_Q3': {
            'max_ml_odds': '+160',      # Moneyline max
            'max_spread_line': '-115',  # Spread max
        },
        'Q2-Q3_to_Q4': {
            'max_ml_odds': '+170',
            'max_spread_line': '-115',
        },
        'Q3-Q4_to_OT': {
            'max_ml_odds': '+400',
            'max_spread_line': '-115',
        },
    }

    # Talent differential thresholds
    MIN_TALENT_GAP_FOR_FILTER = 12.0  # Skip alerts if talent gap > 12 PPG (blowout territory)

    def __init__(self):
        """Initialize the Quarter Reversal detector"""
        self.active_triggers = {}  # game_id -> trigger data

    def _calculate_talent_differential(
        self,
        hot_team: str,
        reversal_team: str,
        game_data: Dict
    ) -> Optional[float]:
        """
        Calculate talent differential between teams using PPG and net rating

        Returns positive value if hot_team is better, negative if reversal_team is better

        Uses multiple factors:
        - PPG differential (points per game)
        - Net rating differential (offensive - defensive rating)
        - Win percentage differential
        """
        home_team = game_data.get('home_team', {}).get('name', '')
        away_team = game_data.get('away_team', {}).get('name', '')

        home_stats = game_data.get('home_team_stats')
        away_stats = game_data.get('away_team_stats')

        if not home_stats or not away_stats:
            return None

        # Determine which team is hot vs reversal
        if hot_team == home_team:
            hot_stats = home_stats
            reversal_stats = away_stats
        else:
            hot_stats = away_stats
            reversal_stats = home_stats

        # Calculate PPG differential
        ppg_diff = hot_stats.get('pts_per_game', 110) - reversal_stats.get('pts_per_game', 110)

        # Calculate net rating differential (more reliable than just PPG)
        hot_net_rating = hot_stats.get('net_rating', 0)
        reversal_net_rating = reversal_stats.get('net_rating', 0)
        net_rating_diff = hot_net_rating - reversal_net_rating

        # Weight: 60% net rating, 40% PPG (net rating is more predictive)
        talent_differential = (0.6 * net_rating_diff) + (0.4 * ppg_diff)

        return talent_differential

    def analyze_game(
        self,
        game_data: Dict,
        bankroll: Optional[float] = None,
        risk_profile: Literal['conservative', 'balanced', 'aggressive'] = 'balanced'
    ) -> Optional[Dict]:
        """
        Analyze a live NBA game for quarter reversal opportunities

        Args:
            game_data: Live game data with quarter scores
            bankroll: Total bankroll for Kelly sizing (optional)
            risk_profile: Risk profile for bet sizing and scoring

        Returns:
            Alert dict with multiple bet options if opportunity found, None otherwise

        Response format:
            {
                'type': 'quarter_reversal',
                'strategy': 'Q1-Q2_to_Q3',
                'game_id': str,
                'matchup': str,
                'trigger': str,
                'reasoning': str,
                'alert_level': 'HIGH' | 'MEDIUM' | 'CRITICAL',
                'reversal_prob': float,
                'expected_roi': float,
                'recommendations': [
                    {
                        'rank': 1,
                        'label': 'Lakers Q3 Win (ML)',
                        'odds': '+140',
                        'probability': 0.553,
                        'expected_value': 0.327,
                        'score': 0.272,
                        'kelly_size': 150.0,  # if bankroll provided
                        'kelly_pct': 0.015,   # if bankroll provided
                        ...
                    },
                    ...
                ],
                'timestamp': str
            }
        """
        game_id = game_data.get('id')
        period = game_data.get('period', 1)
        home_team = game_data.get('home_team', {}).get('name', '')
        away_team = game_data.get('away_team', {}).get('name', '')

        # Get quarter scores
        quarters = game_data.get('quarters', {})

        # Only analyze games with quarter data
        if not quarters:
            return None

        # Check Q1-Q2 → Q3 trigger (STRONGEST)
        if period == 3:
            alert = self._check_q1q2_to_q3(
                game_id, quarters, home_team, away_team, game_data, bankroll, risk_profile
            )
            if alert:
                return alert

        # Check Q2-Q3 → Q4 trigger
        if period == 4:
            alert = self._check_q2q3_to_q4(
                game_id, quarters, home_team, away_team, game_data, bankroll, risk_profile
            )
            if alert:
                return alert

        # Check Q3-Q4 → OT trigger (HIGHEST ROI)
        if period == 5:  # OT
            alert = self._check_q3q4_to_ot(
                game_id, quarters, home_team, away_team, game_data, bankroll, risk_profile
            )
            if alert:
                return alert

        return None

    def _check_q1q2_to_q3(
        self,
        game_id: str,
        quarters: Dict,
        home_team: str,
        away_team: str,
        game_data: Dict,
        bankroll: Optional[float] = None,
        risk_profile: Literal['conservative', 'balanced', 'aggressive'] = 'balanced'
    ) -> Optional[Dict]:
        """Check for Q1-Q2 winner → Q3 reversal opportunity"""

        q1_home = quarters.get('Q1', {}).get('home', 0)
        q1_away = quarters.get('Q1', {}).get('away', 0)
        q2_home = quarters.get('Q2', {}).get('home', 0)
        q2_away = quarters.get('Q2', {}).get('away', 0)

        # Check if home won Q1 and Q2
        if q1_home > q1_away and q2_home > q2_away:
            hot_team = home_team
            reversal_team = away_team
            q1_margin = q1_home - q1_away
            q2_margin = q2_home - q2_away

        # Check if away won Q1 and Q2
        elif q1_away > q1_home and q2_away > q2_home:
            hot_team = away_team
            reversal_team = home_team
            q1_margin = q1_away - q1_home
            q2_margin = q2_away - q2_home
        else:
            return None

        # Calculate talent differential
        talent_diff = self._calculate_talent_differential(hot_team, reversal_team, game_data)

        # FILTER: Skip if talent gap is too large (dominant team crushing weak opponent)
        if talent_diff is not None and abs(talent_diff) > self.MIN_TALENT_GAP_FOR_FILTER:
            logger.info(f"Skipping Q3 reversal alert: talent gap too large ({talent_diff:.1f} > {self.MIN_TALENT_GAP_FOR_FILTER})")
            return None

        # Calculate confidence based on team, margins, and talent differential
        base_prob = self.REVERSAL_RATES['Q1-Q2_to_Q3']
        confidence = self._calculate_confidence(hot_team, reversal_team, q1_margin, q2_margin, base_prob, talent_diff)

        # Generate bet options with bookmaker odds
        bet_options = create_quarter_reversal_options(
            reversal_team=reversal_team,
            quarter='Q3',
            probability=confidence,
            strategy_type='Q1-Q2_to_Q3',
            bookmakers=game_data.get('bookmakers', [])
        )

        # Validate price limits
        price_limits = self.PRICE_LIMITS['Q1-Q2_to_Q3']
        valid_options = []
        for option in bet_options:
            validation = validate_price_limits(
                option,
                max_odds=price_limits['max_ml_odds'],
                max_spread_line=price_limits['max_spread_line']
            )
            if validation['valid']:
                valid_options.append(option)
            else:
                logger.info(f"Filtered out option: {validation['reason']}")

        # If no valid options after price filtering, skip this alert
        if not valid_options:
            logger.info(f"No valid bet options for Q3 reversal in game {game_id} after price limit filtering")
            return None

        # Get top recommendations
        recommendations = recommend_best_bets(
            valid_options,
            bankroll=bankroll,
            risk_profile=risk_profile,
            top_n=3,
            min_ev=0.0
        )

        return {
            'type': 'quarter_reversal',
            'strategy': 'Q1-Q2_to_Q3',
            'game_id': game_id,
            'home_team': home_team,
            'away_team': away_team,
            'matchup': f"{away_team} @ {home_team}",
            'hot_team': hot_team,
            'reversal_team': reversal_team,
            'quarter': 'Q3',
            'trigger': f"{hot_team} won Q1 ({q1_margin:+d}) and Q2 ({q2_margin:+d})",
            'reversal_prob': confidence,
            'expected_roi': self.ROI_RATES['Q1-Q2_to_Q3'],
            'alert_level': 'HIGH' if confidence > 0.57 else 'MEDIUM',
            'reasoning': self._generate_reasoning(hot_team, q1_margin, q2_margin, 'Q3', talent_diff),
            'talent_differential': talent_diff,
            'recommendations': recommendations,
            'total_options': len(recommendations),
            'timestamp': datetime.now().isoformat()
        }

    def _check_q2q3_to_q4(
        self,
        game_id: str,
        quarters: Dict,
        home_team: str,
        away_team: str,
        game_data: Dict,
        bankroll: Optional[float] = None,
        risk_profile: Literal['conservative', 'balanced', 'aggressive'] = 'balanced'
    ) -> Optional[Dict]:
        """Check for Q2-Q3 winner → Q4 reversal opportunity"""

        q2_home = quarters.get('Q2', {}).get('home', 0)
        q2_away = quarters.get('Q2', {}).get('away', 0)
        q3_home = quarters.get('Q3', {}).get('home', 0)
        q3_away = quarters.get('Q3', {}).get('away', 0)

        # Check if home won Q2 and Q3
        if q2_home > q2_away and q3_home > q3_away:
            hot_team = home_team
            reversal_team = away_team
            q2_margin = q2_home - q2_away
            q3_margin = q3_home - q3_away

        # Check if away won Q2 and Q3
        elif q2_away > q2_home and q3_away > q3_home:
            hot_team = away_team
            reversal_team = home_team
            q2_margin = q2_away - q2_home
            q3_margin = q3_away - q3_home
        else:
            return None

        # Calculate talent differential
        talent_diff = self._calculate_talent_differential(hot_team, reversal_team, game_data)

        # FILTER: Skip if talent gap is too large
        if talent_diff is not None and abs(talent_diff) > self.MIN_TALENT_GAP_FOR_FILTER:
            logger.info(f"Skipping Q4 reversal alert: talent gap too large ({talent_diff:.1f} > {self.MIN_TALENT_GAP_FOR_FILTER})")
            return None

        base_prob = self.REVERSAL_RATES['Q2-Q3_to_Q4']
        confidence = self._calculate_confidence(hot_team, reversal_team, q2_margin, q3_margin, base_prob, talent_diff)

        # Generate bet options with bookmaker odds
        bet_options = create_quarter_reversal_options(
            reversal_team=reversal_team,
            quarter='Q4',
            probability=confidence,
            strategy_type='Q2-Q3_to_Q4',
            bookmakers=game_data.get('bookmakers', [])
        )

        # Validate price limits
        price_limits = self.PRICE_LIMITS['Q2-Q3_to_Q4']
        valid_options = []
        for option in bet_options:
            validation = validate_price_limits(
                option,
                max_odds=price_limits['max_ml_odds'],
                max_spread_line=price_limits['max_spread_line']
            )
            if validation['valid']:
                valid_options.append(option)
            else:
                logger.info(f"Filtered out option: {validation['reason']}")

        if not valid_options:
            logger.info(f"No valid bet options for Q4 reversal in game {game_id} after price limit filtering")
            return None

        # Get top recommendations
        recommendations = recommend_best_bets(
            valid_options,
            bankroll=bankroll,
            risk_profile=risk_profile,
            top_n=3,
            min_ev=0.0
        )

        return {
            'type': 'quarter_reversal',
            'strategy': 'Q2-Q3_to_Q4',
            'game_id': game_id,
            'home_team': home_team,
            'away_team': away_team,
            'matchup': f"{away_team} @ {home_team}",
            'hot_team': hot_team,
            'reversal_team': reversal_team,
            'quarter': 'Q4',
            'trigger': f"{hot_team} won Q2 ({q2_margin:+d}) and Q3 ({q3_margin:+d})",
            'reversal_prob': confidence,
            'expected_roi': self.ROI_RATES['Q2-Q3_to_Q4'],
            'alert_level': 'MEDIUM' if confidence > 0.55 else 'LOW',
            'reasoning': self._generate_reasoning(hot_team, q2_margin, q3_margin, 'Q4', talent_diff),
            'talent_differential': talent_diff,
            'recommendations': recommendations,
            'total_options': len(recommendations),
            'timestamp': datetime.now().isoformat()
        }

    def _check_q3q4_to_ot(
        self,
        game_id: str,
        quarters: Dict,
        home_team: str,
        away_team: str,
        game_data: Dict,
        bankroll: Optional[float] = None,
        risk_profile: Literal['conservative', 'balanced', 'aggressive'] = 'balanced'
    ) -> Optional[Dict]:
        """Check for Q3-Q4 winner → OT reversal opportunity (HIGHEST ROI)"""

        q3_home = quarters.get('Q3', {}).get('home', 0)
        q3_away = quarters.get('Q3', {}).get('away', 0)
        q4_home = quarters.get('Q4', {}).get('home', 0)
        q4_away = quarters.get('Q4', {}).get('away', 0)

        # Check if home won Q3 and Q4
        if q3_home > q3_away and q4_home > q4_away:
            hot_team = home_team
            reversal_team = away_team
            q3_margin = q3_home - q3_away
            q4_margin = q4_home - q4_away

        # Check if away won Q3 and Q4
        elif q3_away > q3_home and q4_away > q4_home:
            hot_team = away_team
            reversal_team = home_team
            q3_margin = q3_away - q3_home
            q4_margin = q4_away - q4_home
        else:
            return None

        # Calculate talent differential
        talent_diff = self._calculate_talent_differential(hot_team, reversal_team, game_data)

        # FILTER: Skip if talent gap is too large
        if talent_diff is not None and abs(talent_diff) > self.MIN_TALENT_GAP_FOR_FILTER:
            logger.info(f"Skipping OT reversal alert: talent gap too large ({talent_diff:.1f} > {self.MIN_TALENT_GAP_FOR_FILTER})")
            return None

        base_prob = self.REVERSAL_RATES['Q3-Q4_to_OT']
        confidence = self._calculate_confidence(hot_team, reversal_team, q3_margin, q4_margin, base_prob, talent_diff)

        # Generate bet options with bookmaker odds
        bet_options = create_quarter_reversal_options(
            reversal_team=reversal_team,
            quarter='OT',
            probability=confidence,
            strategy_type='Q3-Q4_to_OT',
            bookmakers=game_data.get('bookmakers', [])
        )

        # Validate price limits
        price_limits = self.PRICE_LIMITS['Q3-Q4_to_OT']
        valid_options = []
        for option in bet_options:
            validation = validate_price_limits(
                option,
                max_odds=price_limits['max_ml_odds'],
                max_spread_line=price_limits['max_spread_line']
            )
            if validation['valid']:
                valid_options.append(option)
            else:
                logger.info(f"Filtered out option: {validation['reason']}")

        if not valid_options:
            logger.info(f"No valid bet options for OT reversal in game {game_id} after price limit filtering")
            return None

        # Get top recommendations
        recommendations = recommend_best_bets(
            valid_options,
            bankroll=bankroll,
            risk_profile=risk_profile,
            top_n=3,
            min_ev=0.0
        )

        return {
            'type': 'quarter_reversal',
            'strategy': 'Q3-Q4_to_OT',
            'game_id': game_id,
            'home_team': home_team,
            'away_team': away_team,
            'matchup': f"{away_team} @ {home_team}",
            'hot_team': hot_team,
            'reversal_team': reversal_team,
            'quarter': 'OT',
            'trigger': f"{hot_team} won Q3 ({q3_margin:+d}) and Q4 ({q4_margin:+d})",
            'reversal_prob': confidence,
            'expected_roi': self.ROI_RATES['Q3-Q4_to_OT'],
            'alert_level': 'CRITICAL',  # Highest ROI!
            'reasoning': self._generate_reasoning(hot_team, q3_margin, q4_margin, 'OT', talent_diff),
            'talent_differential': talent_diff,
            'recommendations': recommendations,
            'total_options': len(recommendations),
            'timestamp': datetime.now().isoformat()
        }

    def _calculate_confidence(self, hot_team: str, reversal_team: str,
                             margin1: int, margin2: int, base_prob: float,
                             talent_differential: Optional[float] = None) -> float:
        """
        Calculate ML-enhanced confidence for reversal

        Adjustments:
        - High-pace teams (Lakers, Warriors) have higher reversal rates
        - Larger margins (>10 pts) increase reversal probability
        - Smaller margins (<3 pts) decrease reversal probability
        - Talent differential (evenly matched teams have higher reversal rates)

        Args:
            hot_team: Team that dominated the recent quarters
            reversal_team: Team expected to reverse in next quarter
            margin1: Point margin in first quarter
            margin2: Point margin in second quarter
            base_prob: Base reversal probability from historical data
            talent_differential: PPG differential between teams (positive = hot_team is better)
        """
        confidence = base_prob

        # Team-specific adjustment
        if hot_team in self.HIGH_REVERSAL_TEAMS:
            confidence += 0.05  # +5% for high-reversal teams

        # Margin adjustments
        avg_margin = (margin1 + margin2) / 2
        if avg_margin > 10:
            confidence += 0.03  # Large leads more likely to reverse
        elif avg_margin < 3:
            confidence -= 0.02  # Close quarters less predictable

        # TALENT DIFFERENTIAL ADJUSTMENT (NEW)
        # When teams are evenly matched, reversals are more likely
        # When hot team is significantly better, reversals are less likely
        if talent_differential is not None:
            if abs(talent_differential) < 2.0:
                # Very evenly matched (< 2 PPG difference)
                confidence += 0.08  # +8% for even matchups
            elif abs(talent_differential) < 5.0:
                # Somewhat evenly matched (2-5 PPG difference)
                confidence += 0.04  # +4% for close matchups
            elif abs(talent_differential) > 10.0:
                # Large talent gap (> 10 PPG difference)
                confidence -= 0.10  # -10% when dominant team is rolling
                # If the dominant team is the hot team, reversal is very unlikely
                if talent_differential > 0:  # Hot team is significantly better
                    confidence -= 0.05  # Additional -5% penalty
            elif abs(talent_differential) > 7.0:
                # Moderate talent gap (7-10 PPG difference)
                confidence -= 0.05  # -5% for talent mismatch

        # Ensure within bounds
        return max(0.35, min(0.70, confidence))

    def _generate_reasoning(self, hot_team: str, margin1: int, margin2: int, next_quarter: str,
                           talent_diff: Optional[float] = None) -> str:
        """Generate human-readable reasoning for the alert"""
        avg_margin = (margin1 + margin2) / 2

        reasons = []
        reasons.append(f"{hot_team} dominated 2 consecutive quarters (avg +{avg_margin:.1f} margin)")

        if next_quarter == 'Q3':
            reasons.append("Halftime adjustments favor opponent")
        elif next_quarter == 'Q4':
            reasons.append("Star fatigue and garbage time factor")
        elif next_quarter == 'OT':
            reasons.append("Extreme fatigue after 48 minutes (60.7% reversal rate)")

        if hot_team in self.HIGH_REVERSAL_TEAMS:
            reasons.append(f"{hot_team} has {self.HIGH_REVERSAL_TEAMS[hot_team]:.1%} historical reversal rate")

        if avg_margin > 10:
            reasons.append("Large margins increase regression to mean")

        # Add talent differential context
        if talent_diff is not None:
            if abs(talent_diff) < 2.0:
                reasons.append("Evenly matched teams (reversal highly likely)")
            elif abs(talent_diff) < 5.0:
                reasons.append("Close talent levels increase reversal probability")
            elif abs(talent_diff) > 7.0:
                if talent_diff < 0:  # Reversal team is actually better
                    reasons.append("Better team expected to bounce back")
                else:  # Hot team is better, but still within acceptable range
                    reasons.append("Talent gap exists but reversal still viable")

        return " | ".join(reasons)
