"""NBA Player Props Projection Engine

Generates advanced stat projections using:
- Season baseline stats
- Recent form trends (last 10 games)
- Matchup quality (opponent defense)
- Pace adjustments
- Usage rate and minutes
"""
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class NBAPropsProjector:
    """
    Advanced projection engine for NBA player props
    Uses multi-factor analysis to generate projections
    """

    # League average baseline (2024-25 season)
    LEAGUE_AVG_PACE = 99.5
    LEAGUE_AVG_DEF_RATING = 114.0
    LEAGUE_AVG_OFF_RATING = 114.0

    # Confidence thresholds
    CONFIDENCE_THRESHOLDS = {
        'HIGH': 0.75,      # 75%+ confidence
        'MEDIUM': 0.60,    # 60-75% confidence
        'LOW': 0.50        # 50-60% confidence
    }

    # Stat type weights for different factors
    FACTOR_WEIGHTS = {
        'baseline': 0.40,           # Season average (40%)
        'recent_form': 0.25,        # Last 10 games trend (25%)
        'matchup': 0.20,            # Opponent defensive quality (15%)
        'pace': 0.10,               # Pace differential (10%)
        'situational': 0.05         # Home/away, rest, etc. (10%)
    }

    def __init__(self):
        pass

    def project_player_stats(
        self,
        player_profile: Dict,
        opponent_team: Optional[str] = None
    ) -> Dict:
        """
        Generate comprehensive player stat projections

        Args:
            player_profile: Complete player profile from NBAPlayerPropsStats
            opponent_team: Optional opponent team abbreviation

        Returns:
            Dict with projections for each stat type:
            {
                'points': {'projection': 25.5, 'confidence': 'HIGH', 'factors': {...}},
                'rebounds': {...},
                'assists': {...},
                'threes': {...}
            }
        """
        if not player_profile:
            return {}

        season_stats = player_profile.get('season_stats', {})
        trends = player_profile.get('trends', {})
        opponent_defense = player_profile.get('opponent_defense')

        # Calculate pace adjustment factor
        pace_factor = self._calculate_pace_factor(
            season_stats,
            opponent_defense
        )

        # Calculate matchup adjustment
        matchup_factor = self._calculate_matchup_factor(
            season_stats,
            opponent_defense
        )

        # Project each stat type
        projections = {}

        # Points projection
        projections['points'] = self._project_stat(
            stat_type='points',
            baseline=season_stats.get('points', 0),
            trend=trends.get('points', {}),
            pace_factor=pace_factor,
            matchup_factor=matchup_factor,
            season_stats=season_stats,
            opponent_defense=opponent_defense
        )

        # Rebounds projection
        projections['rebounds'] = self._project_stat(
            stat_type='rebounds',
            baseline=season_stats.get('rebounds', 0),
            trend=trends.get('rebounds', {}),
            pace_factor=pace_factor,
            matchup_factor=matchup_factor,
            season_stats=season_stats,
            opponent_defense=opponent_defense
        )

        # Assists projection
        projections['assists'] = self._project_stat(
            stat_type='assists',
            baseline=season_stats.get('assists', 0),
            trend=trends.get('assists', {}),
            pace_factor=pace_factor,
            matchup_factor=matchup_factor,
            season_stats=season_stats,
            opponent_defense=opponent_defense
        )

        # Three-pointers projection
        projections['threes'] = self._project_stat(
            stat_type='threes',
            baseline=season_stats.get('threes_made', 0),
            trend=trends.get('threes', {}),
            pace_factor=pace_factor,
            matchup_factor=matchup_factor,
            season_stats=season_stats,
            opponent_defense=opponent_defense
        )

        return projections

    def _project_stat(
        self,
        stat_type: str,
        baseline: float,
        trend: Dict,
        pace_factor: float,
        matchup_factor: float,
        season_stats: Dict,
        opponent_defense: Optional[Dict]
    ) -> Dict:
        """
        Project a single stat using multi-factor analysis

        Returns:
            {
                'projection': float,
                'confidence': str ('HIGH', 'MEDIUM', 'LOW'),
                'factors': {
                    'baseline': float,
                    'recent_form': float,
                    'matchup': float,
                    'pace': float,
                    'total_adjustment': float
                },
                'reasoning': str
            }
        """
        if baseline == 0:
            return {
                'projection': 0,
                'confidence': 'LOW',
                'factors': {},
                'reasoning': 'Insufficient data'
            }

        # 1. Baseline (40% weight)
        baseline_component = baseline * self.FACTOR_WEIGHTS['baseline']

        # 2. Recent form adjustment (25% weight)
        recent_avg = trend.get('average', baseline)
        trend_direction = trend.get('trend', 'stable')
        std_dev = trend.get('std_dev', 0)

        # Apply trend adjustment
        if trend_direction == 'increasing':
            recent_form_adj = (recent_avg - baseline) * 0.6  # 60% of the increase
        elif trend_direction == 'decreasing':
            recent_form_adj = (recent_avg - baseline) * 0.6  # 60% of the decrease
        else:
            recent_form_adj = (recent_avg - baseline) * 0.3  # 30% for stable

        recent_form_component = recent_form_adj * self.FACTOR_WEIGHTS['recent_form']

        # 3. Matchup adjustment (20% weight)
        matchup_component = baseline * (matchup_factor - 1.0) * self.FACTOR_WEIGHTS['matchup']

        # 4. Pace adjustment (10% weight)
        pace_component = baseline * (pace_factor - 1.0) * self.FACTOR_WEIGHTS['pace']

        # 5. Situational adjustment (5% weight) - placeholder for future enhancements
        situational_component = 0

        # Total projection
        total_adjustment = (
            recent_form_component +
            matchup_component +
            pace_component +
            situational_component
        )

        projection = baseline + total_adjustment

        # Calculate confidence based on data quality
        confidence_score = self._calculate_confidence(
            baseline=baseline,
            std_dev=std_dev,
            games_played=season_stats.get('games_played', 0),
            recent_games_count=len(trend.get('recent_values', [])),
            has_opponent_data=opponent_defense is not None
        )

        if confidence_score >= self.CONFIDENCE_THRESHOLDS['HIGH']:
            confidence = 'HIGH'
        elif confidence_score >= self.CONFIDENCE_THRESHOLDS['MEDIUM']:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'

        # Generate reasoning
        reasoning = self._generate_reasoning(
            stat_type=stat_type,
            baseline=baseline,
            projection=projection,
            trend_direction=trend_direction,
            matchup_factor=matchup_factor,
            pace_factor=pace_factor
        )

        return {
            'projection': round(projection, 1),
            'confidence': confidence,
            'confidence_score': round(confidence_score, 3),
            'factors': {
                'baseline': round(baseline, 1),
                'recent_avg': round(recent_avg, 1),
                'trend': trend_direction,
                'matchup_adjustment': round(matchup_component, 2),
                'pace_adjustment': round(pace_component, 2),
                'total_adjustment': round(total_adjustment, 2)
            },
            'reasoning': reasoning
        }

    def _calculate_pace_factor(
        self,
        season_stats: Dict,
        opponent_defense: Optional[Dict]
    ) -> float:
        """
        Calculate pace adjustment factor

        Returns:
            Multiplier (1.0 = neutral, >1.0 = faster, <1.0 = slower)
        """
        if not opponent_defense:
            return 1.0

        opponent_pace = opponent_defense.get('pace', self.LEAGUE_AVG_PACE)

        # Compare to league average
        pace_diff = (opponent_pace - self.LEAGUE_AVG_PACE) / self.LEAGUE_AVG_PACE

        # Cap pace adjustment at +/- 10%
        pace_factor = 1.0 + max(-0.10, min(0.10, pace_diff))

        return pace_factor

    def _calculate_matchup_factor(
        self,
        season_stats: Dict,
        opponent_defense: Optional[Dict]
    ) -> float:
        """
        Calculate matchup quality adjustment

        Returns:
            Multiplier (1.0 = neutral, >1.0 = favorable, <1.0 = unfavorable)
        """
        if not opponent_defense:
            return 1.0

        opp_def_rating = opponent_defense.get('def_rating', self.LEAGUE_AVG_DEF_RATING)

        # Better defensive rating (lower) = harder matchup for offense
        # Worse defensive rating (higher) = easier matchup for offense
        def_diff = (opp_def_rating - self.LEAGUE_AVG_DEF_RATING) / self.LEAGUE_AVG_DEF_RATING

        # Cap matchup adjustment at +/- 15%
        matchup_factor = 1.0 + max(-0.15, min(0.15, def_diff))

        return matchup_factor

    def _calculate_confidence(
        self,
        baseline: float,
        std_dev: float,
        games_played: int,
        recent_games_count: int,
        has_opponent_data: bool
    ) -> float:
        """
        Calculate confidence score (0.0 to 1.0)

        Factors:
        - Sample size (games played)
        - Consistency (standard deviation)
        - Recent data availability
        - Opponent data availability
        """
        confidence = 0.0

        # Sample size component (0-0.3)
        if games_played >= 20:
            confidence += 0.3
        elif games_played >= 10:
            confidence += 0.2
        elif games_played >= 5:
            confidence += 0.1

        # Consistency component (0-0.3)
        if baseline > 0:
            coefficient_of_variation = std_dev / baseline
            if coefficient_of_variation < 0.20:  # Very consistent
                confidence += 0.3
            elif coefficient_of_variation < 0.35:  # Moderately consistent
                confidence += 0.2
            elif coefficient_of_variation < 0.50:  # Somewhat consistent
                confidence += 0.1

        # Recent data component (0-0.2)
        if recent_games_count >= 10:
            confidence += 0.2
        elif recent_games_count >= 5:
            confidence += 0.1

        # Opponent data component (0-0.2)
        if has_opponent_data:
            confidence += 0.2

        return min(1.0, confidence)

    def _generate_reasoning(
        self,
        stat_type: str,
        baseline: float,
        projection: float,
        trend_direction: str,
        matchup_factor: float,
        pace_factor: float
    ) -> str:
        """
        Generate human-readable reasoning for the projection
        """
        diff = projection - baseline
        diff_pct = (diff / baseline * 100) if baseline > 0 else 0

        reasoning_parts = []

        # Baseline
        reasoning_parts.append(f"Season avg: {baseline:.1f}")

        # Trend
        if trend_direction == 'increasing':
            reasoning_parts.append(f"Recent form trending UP")
        elif trend_direction == 'decreasing':
            reasoning_parts.append(f"Recent form trending DOWN")
        else:
            reasoning_parts.append(f"Consistent recent performance")

        # Matchup
        if matchup_factor > 1.05:
            reasoning_parts.append(f"Favorable matchup (+{(matchup_factor-1)*100:.1f}%)")
        elif matchup_factor < 0.95:
            reasoning_parts.append(f"Tough matchup ({(matchup_factor-1)*100:.1f}%)")

        # Pace
        if pace_factor > 1.03:
            reasoning_parts.append(f"Fast-paced game (+{(pace_factor-1)*100:.1f}%)")
        elif pace_factor < 0.97:
            reasoning_parts.append(f"Slower pace ({(pace_factor-1)*100:.1f}%)")

        # Final projection
        if abs(diff_pct) > 5:
            direction = "up" if diff > 0 else "down"
            reasoning_parts.append(f"Projecting {direction} {abs(diff_pct):.1f}%")

        return " | ".join(reasoning_parts)

    def compare_to_line(
        self,
        projection: Dict,
        market_line: float
    ) -> Dict:
        """
        Compare projection to market line and calculate edge

        Args:
            projection: Projection dict from _project_stat
            market_line: The over/under line from sportsbooks

        Returns:
            {
                'edge': float,  # Difference (projection - line)
                'edge_pct': float,  # Percentage edge
                'recommendation': str,  # 'OVER', 'UNDER', or None
                'bet_strength': str,  # 'STRONG', 'MODERATE', 'WEAK', or None
            }
        """
        projected_value = projection.get('projection', 0)
        confidence = projection.get('confidence', 'LOW')

        edge = projected_value - market_line
        edge_pct = (edge / market_line * 100) if market_line > 0 else 0

        # Determine recommendation based on edge and confidence
        recommendation = None
        bet_strength = None

        # Require minimum edge thresholds based on confidence
        edge_thresholds = {
            'HIGH': 0.05,      # 5% edge for high confidence
            'MEDIUM': 0.08,    # 8% edge for medium confidence
            'LOW': 0.12        # 12% edge for low confidence
        }

        min_edge = edge_thresholds.get(confidence, 0.12)

        if abs(edge_pct / 100) >= min_edge:
            recommendation = 'OVER' if edge > 0 else 'UNDER'

            # Bet strength based on edge size and confidence
            if abs(edge_pct / 100) >= min_edge * 2 and confidence == 'HIGH':
                bet_strength = 'STRONG'
            elif abs(edge_pct / 100) >= min_edge * 1.5:
                bet_strength = 'MODERATE'
            else:
                bet_strength = 'WEAK'

        return {
            'edge': round(edge, 2),
            'edge_pct': round(edge_pct, 2),
            'recommendation': recommendation,
            'bet_strength': bet_strength
        }

    def batch_project(
        self,
        player_profiles: List[Dict]
    ) -> List[Dict]:
        """
        Generate projections for multiple players

        Args:
            player_profiles: List of player profile dicts

        Returns:
            List of projection results
        """
        results = []

        for profile in player_profiles:
            player_info = profile.get('player_info', {})
            projections = self.project_player_stats(profile)

            results.append({
                'player': player_info.get('name'),
                'team': player_info.get('team'),
                'projections': projections
            })

        return results
