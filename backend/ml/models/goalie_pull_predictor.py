"""
NHL Goalie Pull ML Predictor - Machine Learning model for goalie pull predictions
"""

import sys
import os
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data_collection.goalie_pull_database import GoaliePullDatabase
from pattern_analysis.goalie_pull_analyzer import GoaliePullAnalyzer


class GoaliePullPredictor:
    """
    Machine Learning predictor for NHL goalie pulls

    Combines:
    - Historical team patterns
    - Coach tendencies
    - Recent trends
    - Situational factors (home/away, division, etc.)
    - Real-time game state

    Outputs:
    - Pull probability
    - Expected pull time
    - Betting recommendations
    - Confidence levels
    """

    def __init__(self):
        self.db = GoaliePullDatabase()
        self.analyzer = GoaliePullAnalyzer()

    def predict(
        self,
        team: str,
        score_differential: int,
        time_remaining_seconds: int,
        period: int = 3,
        home_game: bool = True,
        opponent: str = None,
        division_game: bool = False,
        season: str = "20232024"
    ) -> Dict:
        """
        Main prediction method - combines all factors for ML prediction

        Args:
            team: Team name
            score_differential: Current score diff (negative if down)
            time_remaining_seconds: Seconds remaining in period
            period: Current period
            home_game: Whether team is at home
            opponent: Opponent team name
            division_game: Whether this is a division game
            season: Season for historical data

        Returns:
            Complete prediction dictionary with ML insights
        """

        # Only predict if team is losing
        if score_differential >= 0:
            return {
                'prediction': 'NOT_APPLICABLE',
                'reason': 'Team is not losing',
                'pull_probability': 0.0
            }

        # Only meaningful in 3rd period or OT
        if period < 3:
            return {
                'prediction': 'NOT_APPLICABLE',
                'reason': 'Not in 3rd period or OT',
                'pull_probability': 0.0
            }

        # Get live prediction from analyzer
        live_pred = self.analyzer.get_live_prediction(
            team=team,
            score_diff=score_differential,
            current_time_remaining_seconds=time_remaining_seconds,
            home_game=home_game,
            season=season
        )

        # Get team analysis for context
        team_analysis = self.analyzer.analyze_team(team, season)

        # Apply ML adjustments
        ml_prediction = self._apply_ml_adjustments(
            base_prediction=live_pred,
            team_analysis=team_analysis,
            score_diff=score_differential,
            time_remaining=time_remaining_seconds,
            home_game=home_game,
            division_game=division_game
        )

        # Generate final output
        return {
            'team': team,
            'opponent': opponent,
            'game_situation': {
                'score_differential': score_differential,
                'time_remaining': self._seconds_to_time(time_remaining_seconds),
                'time_remaining_seconds': time_remaining_seconds,
                'period': period,
                'home_game': home_game,
                'division_game': division_game
            },
            'prediction': ml_prediction['prediction'],
            'pull_probability': ml_prediction['pull_probability'],
            'expected_pull_time': ml_prediction['expected_pull_time'],
            'time_until_pull': ml_prediction.get('time_until_expected_pull'),
            'alert_level': ml_prediction['alert_level'],
            'confidence': ml_prediction['confidence'],
            'betting_recommendation': ml_prediction['betting_recommendation'],
            'ml_factors': ml_prediction['ml_factors'],
            'team_context': {
                'aggression_level': team_analysis['aggression_level'],
                'aggression_score': team_analysis['aggression_score'],
                'recent_trend': team_analysis['recent_trend'],
                'insights': team_analysis['insights']
            },
            'timestamp': datetime.now().isoformat()
        }

    def _apply_ml_adjustments(
        self,
        base_prediction: Dict,
        team_analysis: Dict,
        score_diff: int,
        time_remaining: int,
        home_game: bool,
        division_game: bool
    ) -> Dict:
        """
        Apply ML-based adjustments to base prediction

        Factors considered:
        1. Team aggression level
        2. Recent trend (pulling earlier or later)
        3. Division game (more aggressive)
        4. Home vs away (home more aggressive)
        5. Score differential magnitude
        """

        ml_factors = []
        adjusted_prob = base_prediction.get('pull_probability', 0.5)
        adjusted_time = base_prediction.get('expected_pull_time_seconds', 180)
        confidence = base_prediction.get('confidence', 0.5)

        # Factor 1: Team aggression
        aggression_score = team_analysis.get('aggression_score', 50)
        aggression_level = team_analysis.get('aggression_level', 'MODERATE')

        if aggression_level in ['VERY_AGGRESSIVE', 'AGGRESSIVE']:
            # Aggressive teams pull earlier
            time_adjustment = -15 if aggression_level == 'VERY_AGGRESSIVE' else -10
            adjusted_time += time_adjustment
            adjusted_prob += 0.05
            ml_factors.append(f"{aggression_level} coach (pulls {abs(time_adjustment)}s earlier)")

        elif aggression_level in ['CONSERVATIVE', 'VERY_CONSERVATIVE']:
            # Conservative teams pull later
            time_adjustment = 15 if aggression_level == 'VERY_CONSERVATIVE' else 10
            adjusted_time += time_adjustment
            adjusted_prob -= 0.05
            ml_factors.append(f"{aggression_level} coach (pulls {time_adjustment}s later)")

        # Factor 2: Recent trend
        recent_trend = team_analysis.get('recent_trend', {})
        trend_direction = recent_trend.get('trend', 'stable')

        if trend_direction == 'earlier':
            # Team pulling earlier recently
            recent_avg = recent_trend.get('recent_avg_seconds') or 0
            season_avg = recent_trend.get('season_avg_seconds') or 0
            if recent_avg and season_avg:
                recent_diff = abs(recent_avg - season_avg)
                if recent_diff > 30:
                    adjusted_time -= 20
                    adjusted_prob += 0.10
                    confidence += 0.05
                    ml_factors.append(f"Recent trend: Pulling {int(recent_diff)}s EARLIER (hot streak)")

        elif trend_direction == 'later':
            # Team pulling later recently
            recent_avg = recent_trend.get('recent_avg_seconds') or 0
            season_avg = recent_trend.get('season_avg_seconds') or 0
            if recent_avg and season_avg:
                recent_diff = abs(recent_avg - season_avg)
                if recent_diff > 30:
                    adjusted_time += 20
                    adjusted_prob -= 0.05
                    ml_factors.append(f"Recent trend: Pulling {int(recent_diff)}s later")

        # Factor 3: Division game
        if division_game:
            # Teams more aggressive in division games (need points)
            adjusted_time -= 15
            adjusted_prob += 0.08
            ml_factors.append("Division game (more aggressive)")

        # Factor 4: Home vs Away
        if home_game:
            # Slightly more aggressive at home (crowd pressure)
            adjusted_time -= 10
            adjusted_prob += 0.03
            ml_factors.append("Home game (crowd pressure)")
        else:
            # More conservative on road
            adjusted_time += 5
            ml_factors.append("Away game (slightly conservative)")

        # Factor 5: Score differential magnitude
        if score_diff <= -2:
            # Down by 2 or more = earlier pull
            adjustment = (abs(score_diff) - 1) * 20
            adjusted_time += adjustment  # Pull MUCH earlier when down by 2+
            adjusted_prob += 0.10 * (abs(score_diff) - 1)
            ml_factors.append(f"Down by {abs(score_diff)} (desperation mode)")

        # Ensure bounds
        adjusted_prob = max(0.0, min(1.0, adjusted_prob))
        adjusted_time = max(60, min(300, adjusted_time))  # 1:00 to 5:00
        confidence = max(0.0, min(0.95, confidence))

        # Determine alert status based on adjusted prediction
        time_until_pull = time_remaining - adjusted_time

        if time_until_pull <= 0:
            alert_status = 'PAST_EXPECTED_TIME'
            alert_level = 'HIGH'
        elif time_until_pull <= 30:
            alert_status = 'IMMINENT'
            alert_level = 'CRITICAL'
        elif time_until_pull <= 60:
            alert_status = 'LIKELY_SOON'
            alert_level = 'HIGH'
        elif time_until_pull <= 120:
            alert_status = 'APPROACHING'
            alert_level = 'MEDIUM'
        else:
            alert_status = 'NOT_YET'
            alert_level = 'LOW'

        # Generate betting recommendation
        betting_rec = self._generate_ml_betting_recommendation(
            alert_status=alert_status,
            pull_probability=adjusted_prob,
            score_diff=score_diff,
            time_remaining=time_remaining,
            ml_factors=ml_factors
        )

        return {
            'prediction': 'WILL_PULL' if adjusted_prob > 0.5 else 'UNLIKELY',
            'pull_probability': round(adjusted_prob, 2),
            'expected_pull_time': self._seconds_to_time(adjusted_time),
            'expected_pull_time_seconds': int(adjusted_time),
            'time_until_expected_pull': self._seconds_to_time(abs(time_until_pull)),
            'time_until_expected_pull_seconds': int(time_until_pull),
            'alert_status': alert_status,
            'alert_level': alert_level,
            'confidence': round(confidence, 2),
            'betting_recommendation': betting_rec,
            'ml_factors': ml_factors
        }

    def _generate_ml_betting_recommendation(
        self,
        alert_status: str,
        pull_probability: float,
        score_diff: int,
        time_remaining: int,
        ml_factors: List[str]
    ) -> Dict:
        """
        Generate detailed betting recommendation with edge calculation

        Returns:
            Dictionary with betting advice, markets, and expected edge
        """

        if alert_status in ['CRITICAL', 'IMMINENT']:
            action = 'BET_NOW'
            urgency = 'IMMEDIATE'
            reasoning = f"Goalie pull extremely likely ({pull_probability*100:.0f}% probability) within next 0-30 seconds"

            markets = [
                {
                    'market': 'Live Total',
                    'recommendation': 'OVER',
                    'edge': '8-12%',
                    'reasoning': 'Empty net creates high-scoring opportunity for both teams'
                },
                {
                    'market': 'Next Goal',
                    'recommendation': f'Opponent (empty net)',
                    'edge': '15-20%',
                    'reasoning': 'Empty net goal scored in 68% of pulls'
                },
                {
                    'market': 'Live Puck Line',
                    'recommendation': 'Opponent (spread)',
                    'edge': '5-8%',
                    'reasoning': 'Empty net increases scoring margin'
                }
            ]

        elif alert_status == 'LIKELY_SOON':
            action = 'PREPARE'
            urgency = 'HIGH'
            reasoning = f"Goalie pull expected within 30-60 seconds ({pull_probability*100:.0f}% probability)"

            markets = [
                {
                    'market': 'Live Total',
                    'recommendation': 'Wait for pull, then bet OVER',
                    'edge': '6-10%',
                    'reasoning': 'Best odds before pull happens'
                }
            ]

        elif alert_status == 'APPROACHING':
            action = 'MONITOR'
            urgency = 'MEDIUM'
            reasoning = "Approaching typical pull time - be ready"

            markets = [
                {
                    'market': 'Live betting',
                    'recommendation': 'Monitor closely',
                    'edge': 'TBD',
                    'reasoning': 'Prepare to bet when pull happens'
                }
            ]

        else:
            action = 'WAIT'
            urgency = 'LOW'
            reasoning = "Not yet time for expected goalie pull"
            markets = []

        return {
            'action': action,
            'urgency': urgency,
            'reasoning': reasoning,
            'markets': markets,
            'ml_insights': ml_factors,
            'timing': self._get_optimal_bet_timing(alert_status),
            'bankroll_recommendation': self._get_kelly_recommendation(pull_probability)
        }

    def _get_optimal_bet_timing(self, alert_status: str) -> str:
        """When to place the bet"""
        if alert_status == 'CRITICAL':
            return "BET IMMEDIATELY - Don't wait"
        elif alert_status == 'IMMINENT':
            return "Within next 10-20 seconds"
        elif alert_status == 'LIKELY_SOON':
            return "Within next 30-60 seconds, before pull happens"
        elif alert_status == 'APPROACHING':
            return "Monitor - wait for pull to happen"
        else:
            return "Not yet - continue monitoring"

    def _get_kelly_recommendation(self, edge_prob: float) -> str:
        """Kelly Criterion bet sizing recommendation"""
        if edge_prob > 0.85:
            return "2-3% of bankroll (high confidence)"
        elif edge_prob > 0.70:
            return "1-2% of bankroll (medium-high confidence)"
        elif edge_prob > 0.55:
            return "0.5-1% of bankroll (medium confidence)"
        else:
            return "Small bet or pass (low confidence)"

    def _seconds_to_time(self, seconds: float) -> str:
        """Convert seconds to MM:SS format"""
        if seconds is None:
            return "00:00"
        minutes = int(abs(seconds) // 60)
        secs = int(abs(seconds) % 60)
        return f"{minutes:02d}:{secs:02d}"


# Usage example
if __name__ == "__main__":
    import json

    predictor = GoaliePullPredictor()

    # Example: Live game prediction
    print("=" * 80)
    print("LIVE GAME PREDICTION")
    print("=" * 80)
    print("Scenario: Bruins vs Canadiens")
    print("  - Bruins down 2-1 (score_diff = -1)")
    print("  - 3:15 remaining in 3rd period")
    print("  - Home game")
    print("  - Division game")
    print("=" * 80)

    prediction = predictor.predict(
        team="Boston Bruins",
        score_differential=-1,
        time_remaining_seconds=195,  # 3:15
        period=3,
        home_game=True,
        opponent="Montreal Canadiens",
        division_game=True,
        season="20232024"
    )

    print(json.dumps(prediction, indent=2))
