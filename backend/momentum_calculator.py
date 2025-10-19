"""Calculate live momentum scores for all sports based on recent play"""
import logging
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class MomentumCalculator:
    """Calculate momentum scores (-100 to 100 scale) for live games"""

    @staticmethod
    def calculate_momentum(
        home_score: int,
        away_score: int,
        sport_key: str,
        period: Optional[int] = None,
        time_remaining: Optional[str] = None,
        recent_plays: Optional[list] = None,
        home_stats: Optional[dict] = None,
        away_stats: Optional[dict] = None
    ) -> Tuple[float, float]:
        """
        Calculate momentum for both teams

        Returns: (home_momentum, away_momentum)
        Each value is on a -100 to 100 scale where:
        - Positive = team has momentum
        - Negative = team is losing momentum
        - 0 = neutral
        """

        # Base momentum from score differential
        score_diff = home_score - away_score

        # Different sports weight momentum differently
        if sport_key.startswith('basketball'):
            return MomentumCalculator._calculate_basketball_momentum(
                score_diff, period, home_score, away_score, home_stats, away_stats
            )
        elif sport_key.startswith('icehockey'):
            return MomentumCalculator._calculate_hockey_momentum(
                score_diff, period, home_stats, away_stats
            )
        elif sport_key.startswith('americanfootball'):
            return MomentumCalculator._calculate_football_momentum(
                score_diff, period, home_score, away_score
            )
        elif sport_key.startswith('baseball'):
            return MomentumCalculator._calculate_baseball_momentum(
                score_diff, period, home_stats, away_stats
            )
        else:
            # Generic momentum based on score
            return MomentumCalculator._calculate_generic_momentum(score_diff)

    @staticmethod
    def _calculate_basketball_momentum(
        score_diff: int,
        period: Optional[int],
        home_score: int,
        away_score: int,
        home_stats: Optional[dict],
        away_stats: Optional[dict]
    ) -> Tuple[float, float]:
        """Calculate NBA momentum based on scoring runs and pace"""

        # Score differential component (-50 to 50)
        score_momentum = max(-50, min(50, score_diff * 3))

        # Game situation modifier (late game close games = higher momentum swings)
        situation_multiplier = 1.0
        if period and period >= 4:
            if abs(score_diff) <= 5:
                situation_multiplier = 1.5  # Close game in 4th = more dramatic

        # Calculate final momentum
        home_momentum = score_momentum * situation_multiplier
        away_momentum = -home_momentum

        # Clamp to -100 to 100
        home_momentum = max(-100, min(100, home_momentum))
        away_momentum = max(-100, min(100, away_momentum))

        return (home_momentum, away_momentum)

    @staticmethod
    def _calculate_hockey_momentum(
        score_diff: int,
        period: Optional[int],
        home_stats: Optional[dict],
        away_stats: Optional[dict]
    ) -> Tuple[float, float]:
        """Calculate NHL momentum based on shots, goals, and possession indicators"""

        # Score differential is important but not overwhelming in hockey
        score_momentum = max(-40, min(40, score_diff * 15))

        # Shot differential is a KEY indicator in hockey
        shot_momentum = 0
        if home_stats and away_stats:
            home_shots = home_stats.get('shots', 0)
            away_shots = away_stats.get('shots', 0)
            shot_diff = home_shots - away_shots
            # Each shot differential = 3 momentum points
            shot_momentum = max(-30, min(30, shot_diff * 3))

        # Save percentage can indicate goalie momentum
        save_momentum = 0
        if home_stats and away_stats:
            home_save_pct = home_stats.get('save_pct', 0.0)
            away_save_pct = away_stats.get('save_pct', 0.0)
            # Higher save % = defense holding strong
            save_diff = (home_save_pct - away_save_pct) * 100
            save_momentum = max(-20, min(20, save_diff * 2))

        # Goals component (recent scoring)
        goal_momentum = 0
        if home_stats and away_stats:
            home_goals = home_stats.get('goals', 0)
            away_goals = away_stats.get('goals', 0)
            goal_diff = home_goals - away_goals
            goal_momentum = max(-30, min(30, goal_diff * 10))

        # Combine all factors
        home_momentum = score_momentum + shot_momentum + save_momentum + goal_momentum
        away_momentum = -home_momentum

        # Clamp to -100 to 100
        home_momentum = max(-100, min(100, home_momentum))
        away_momentum = max(-100, min(100, away_momentum))

        return (home_momentum, away_momentum)

    @staticmethod
    def _calculate_football_momentum(
        score_diff: int,
        period: Optional[int],
        home_score: int,
        away_score: int
    ) -> Tuple[float, float]:
        """Calculate NFL/NCAAF momentum based on scoring drives"""

        # Score differential (more impactful in football)
        score_momentum = max(-60, min(60, score_diff * 5))

        # Quarter situation (late game = more dramatic)
        situation_multiplier = 1.0
        if period and period >= 4:
            if abs(score_diff) <= 7:  # One score game
                situation_multiplier = 1.5

        # Calculate final momentum
        home_momentum = score_momentum * situation_multiplier
        away_momentum = -home_momentum

        # Clamp to -100 to 100
        home_momentum = max(-100, min(100, home_momentum))
        away_momentum = max(-100, min(100, away_momentum))

        return (home_momentum, away_momentum)

    @staticmethod
    def _calculate_baseball_momentum(
        score_diff: int,
        inning: Optional[int],
        home_stats: Optional[dict],
        away_stats: Optional[dict]
    ) -> Tuple[float, float]:
        """Calculate MLB momentum based on runs and hits"""

        # Score differential
        score_momentum = max(-50, min(50, score_diff * 8))

        # Hits can indicate offensive momentum
        hit_momentum = 0
        if home_stats and away_stats:
            home_hits = home_stats.get('hits', 0)
            away_hits = away_stats.get('hits', 0)
            hit_diff = home_hits - away_hits
            hit_momentum = max(-25, min(25, hit_diff * 5))

        # Late inning closer = more dramatic
        situation_multiplier = 1.0
        if inning and inning >= 7:
            if abs(score_diff) <= 2:
                situation_multiplier = 1.3

        # Combine
        home_momentum = (score_momentum + hit_momentum) * situation_multiplier
        away_momentum = -home_momentum

        # Clamp to -100 to 100
        home_momentum = max(-100, min(100, home_momentum))
        away_momentum = max(-100, min(100, away_momentum))

        return (home_momentum, away_momentum)

    @staticmethod
    def _calculate_generic_momentum(score_diff: int) -> Tuple[float, float]:
        """Generic momentum calculation based on score differential only"""

        # Simple score-based momentum
        momentum = max(-100, min(100, score_diff * 10))

        return (momentum, -momentum)
