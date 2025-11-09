"""
NHL Goalie Pull Pattern Analyzer - Analyze team and coach tendencies
"""

from typing import Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data_collection.goalie_pull_database import GoaliePullDatabase


class GoaliePullAnalyzer:
    """
    Analyze goalie pull patterns and tendencies

    Provides insights on:
    - Team pulling tendencies
    - Coach aggression levels
    - Situational patterns (home/away, division games, etc.)
    - Success rates
    - Recent trends
    """

    def __init__(self):
        self.db = GoaliePullDatabase()

    def analyze_team(self, team: str, season: str = "20232024") -> Dict:
        """
        Complete analysis of team's goalie pull patterns

        Args:
            team: Team name
            season: Season to analyze

        Returns:
            Comprehensive team analysis
        """
        # Get base patterns
        patterns = self.db.get_team_pull_patterns(team, season)

        # Get recent trend
        recent_trend = self.db.get_recent_trend(team, games=10)

        # Calculate aggression score
        aggression_score = self._calculate_aggression_score(patterns)

        # Get situational breakdown
        situational = self._get_situational_breakdown(team, season)

        return {
            'team': team,
            'season': season,
            'patterns': patterns,
            'recent_trend': recent_trend,
            'aggression_score': aggression_score,
            'aggression_level': self._classify_aggression(aggression_score),
            'situational': situational,
            'insights': self._generate_insights(team, patterns, recent_trend, aggression_score)
        }

    def analyze_coach(self, coach: str, season: str = "20232024") -> Dict:
        """
        Analyze a coach's goalie pull tendencies

        Args:
            coach: Coach name
            season: Season to analyze

        Returns:
            Coach tendency analysis
        """
        tendencies = self.db.get_coach_tendencies(coach, season)

        # Calculate aggression
        aggression = self._calculate_coach_aggression(tendencies)

        return {
            'coach': coach,
            'season': season,
            'tendencies': tendencies,
            'aggression_score': aggression,
            'aggression_level': self._classify_aggression(aggression)
        }

    def predict_pull_time(
        self,
        team: str,
        score_diff: int,
        home_game: bool,
        opponent: str = None,
        season: str = "20232024"
    ) -> Dict:
        """
        Predict when team will pull goalie based on historical patterns

        Args:
            team: Team name
            score_diff: Current score differential (negative if down)
            home_game: Whether team is at home
            opponent: Opponent name (for division game detection)
            season: Season for historical data

        Returns:
            Prediction dictionary
        """
        # Get team patterns
        patterns = self.db.get_team_pull_patterns(team, season)
        recent_trend = self.db.get_recent_trend(team, games=10)

        # Get relevant pattern
        key = f"down_by_{abs(score_diff)}"
        location = 'home' if home_game else 'away'

        if key not in patterns['by_score_diff']:
            # No data for this score differential
            return {
                'team': team,
                'score_differential': score_diff,
                'prediction': 'INSUFFICIENT_DATA',
                'pull_probability': 0.0,
                'expected_pull_time': None,
                'confidence': 0.0
            }

        pattern_data = patterns['by_score_diff'][key].get(location, {})

        if not pattern_data:
            # Use other location as backup
            other_location = 'away' if home_game else 'home'
            pattern_data = patterns['by_score_diff'][key].get(other_location, {})

        if not pattern_data:
            return {
                'team': team,
                'score_differential': score_diff,
                'prediction': 'INSUFFICIENT_DATA',
                'pull_probability': 0.0,
                'expected_pull_time': None,
                'confidence': 0.0
            }

        # Base prediction from historical average
        avg_time_seconds = pattern_data.get('avg_time_remaining_seconds', 0)
        pull_count = pattern_data.get('pull_count', 0)

        # Adjust based on recent trend
        if recent_trend.get('recent_avg_seconds'):
            # Weight: 70% historical, 30% recent trend
            avg_time_seconds = (avg_time_seconds * 0.7) + (recent_trend['recent_avg_seconds'] * 0.3)

        # Convert to time format
        expected_pull_time = self._seconds_to_time(avg_time_seconds)

        # Calculate pull probability
        # Based on historical frequency
        pull_probability = min(1.0, pull_count / 20.0)  # Assume 20 games as baseline

        # Calculate confidence
        # Higher confidence with more data points
        confidence = min(0.95, 0.5 + (pull_count / 40.0))

        return {
            'team': team,
            'score_differential': score_diff,
            'home_game': home_game,
            'prediction': 'WILL_PULL' if pull_probability > 0.5 else 'UNLIKELY_PULL',
            'pull_probability': round(pull_probability, 2),
            'expected_pull_time': expected_pull_time,
            'expected_pull_time_seconds': int(avg_time_seconds),
            'confidence': round(confidence, 2),
            'historical_data': {
                'total_pulls_in_situation': pull_count,
                'earliest_pull': pattern_data.get('earliest_pull'),
                'latest_pull': pattern_data.get('latest_pull'),
                'location': location
            },
            'recent_trend': {
                'recent_avg_time': recent_trend.get('recent_avg_time'),
                'trend_direction': recent_trend.get('trend', 'stable')
            }
        }

    def get_live_prediction(
        self,
        team: str,
        score_diff: int,
        current_time_remaining_seconds: int,
        home_game: bool,
        season: str = "20232024"
    ) -> Dict:
        """
        Real-time prediction during live game

        Args:
            team: Team name
            score_diff: Current score differential
            current_time_remaining_seconds: Current time remaining in period
            home_game: Whether team is at home
            season: Season for historical data

        Returns:
            Live prediction with time until expected pull
        """
        # Get base prediction
        prediction = self.predict_pull_time(team, score_diff, home_game, season=season)

        if prediction['prediction'] == 'INSUFFICIENT_DATA':
            return prediction

        expected_pull_seconds = prediction['expected_pull_time_seconds']

        # Calculate time until pull
        time_until_pull = current_time_remaining_seconds - expected_pull_seconds

        # Determine alert status
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

        return {
            **prediction,
            'current_time_remaining': self._seconds_to_time(current_time_remaining_seconds),
            'current_time_remaining_seconds': current_time_remaining_seconds,
            'time_until_expected_pull': self._seconds_to_time(abs(time_until_pull)),
            'time_until_expected_pull_seconds': int(time_until_pull),
            'alert_status': alert_status,
            'alert_level': alert_level,
            'betting_recommendation': self._generate_betting_recommendation(
                alert_status, prediction['pull_probability'], score_diff
            )
        }

    def _calculate_aggression_score(self, patterns: Dict) -> float:
        """
        Calculate aggression score (0-100)
        Higher = more aggressive (pulls earlier)
        """
        score = 50.0  # Base score

        by_score = patterns.get('by_score_diff', {})

        # Down by 1: Earlier pull = more aggressive
        if 'down_by_1' in by_score:
            home_data = by_score['down_by_1'].get('home', {})
            if home_data.get('avg_time_remaining_seconds'):
                avg_time = home_data['avg_time_remaining_seconds']
                # 180 seconds (3:00) = neutral
                # Earlier than 3:00 = more aggressive
                # Later than 3:00 = less aggressive
                deviation = (avg_time - 180) / 60.0
                score += (deviation * 5)  # ±5 points per minute deviation

        # Down by 2: Willingness to pull
        if 'down_by_2' in by_score:
            home_data = by_score['down_by_2'].get('home', {})
            if home_data.get('pull_count', 0) > 5:
                score += 10  # Aggressive coaches pull down by 2

        # Down by 3: Very aggressive
        if 'down_by_3' in by_score:
            home_data = by_score['down_by_3'].get('home', {})
            if home_data.get('pull_count', 0) > 2:
                score += 15  # Extremely aggressive

        return max(0, min(100, score))

    def _calculate_coach_aggression(self, tendencies: Dict) -> float:
        """Calculate coach aggression score"""
        # Similar to team, but coach-specific
        return self._calculate_aggression_score({'by_score_diff': tendencies.get('by_score_diff', {})})

    def _classify_aggression(self, score: float) -> str:
        """Classify aggression level"""
        if score >= 75:
            return 'VERY_AGGRESSIVE'
        elif score >= 60:
            return 'AGGRESSIVE'
        elif score >= 40:
            return 'MODERATE'
        elif score >= 25:
            return 'CONSERVATIVE'
        else:
            return 'VERY_CONSERVATIVE'

    def _get_situational_breakdown(self, team: str, season: str) -> Dict:
        """Get breakdown of pulls by situation"""
        # TODO: Implement detailed situational queries
        return {
            'home_vs_away': 'Needs implementation',
            'division_games': 'Needs implementation',
            'vs_top_teams': 'Needs implementation'
        }

    def _generate_insights(self, team: str, patterns: Dict, trend: Dict, aggression: float) -> List[str]:
        """Generate human-readable insights"""
        insights = []

        # Aggression insight
        level = self._classify_aggression(aggression)
        insights.append(f"{team} is {level.lower().replace('_', ' ')} with goalie pulls (score: {aggression:.0f}/100)")

        # Trend insight
        if trend.get('trend') == 'earlier':
            recent_avg = trend.get('recent_avg_seconds') or 0
            season_avg = trend.get('season_avg_seconds') or 0
            if recent_avg and season_avg:
                diff = abs(recent_avg - season_avg)
                if diff > 30:
                    insights.append(f"Recent trend: Pulling goalie {int(diff)} seconds EARLIER than season average")

        elif trend.get('trend') == 'later':
            recent_avg = trend.get('recent_avg_seconds') or 0
            season_avg = trend.get('season_avg_seconds') or 0
            if recent_avg and season_avg:
                diff = abs(recent_avg - season_avg)
                if diff > 30:
                    insights.append(f"Recent trend: Pulling goalie {int(diff)} seconds LATER than season average")

        # Success rate insight
        success_rate = patterns.get('overall', {}).get('success_rate', 0)
        if success_rate > 0:
            insights.append(f"Success rate when pulling goalie: {success_rate*100:.1f}%")

        return insights

    def _generate_betting_recommendation(self, alert_status: str, pull_prob: float, score_diff: int) -> str:
        """Generate betting recommendation based on goalie pull prediction"""
        if alert_status == 'CRITICAL' or alert_status == 'IMMINENT':
            return f"BET NOW - Goalie pull imminent ({pull_prob*100:.0f}% probability). Consider live total OVER or empty net props."

        elif alert_status == 'LIKELY_SOON':
            return f"PREPARE TO BET - Goalie pull expected soon. Monitor closely for betting opportunity."

        elif alert_status == 'APPROACHING':
            return "WATCH CLOSELY - Approaching typical pull time. Be ready to bet."

        else:
            return "MONITOR - Not yet time for expected goalie pull."

    def _seconds_to_time(self, seconds: float) -> str:
        """Convert seconds to MM:SS format"""
        if seconds is None:
            return "00:00"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"


# Usage example
if __name__ == "__main__":
    analyzer = GoaliePullAnalyzer()

    # Analyze a team
    print("=" * 80)
    print("TEAM ANALYSIS: Boston Bruins")
    print("=" * 80)

    analysis = analyzer.analyze_team("Boston Bruins", "20232024")
    print(json.dumps(analysis, indent=2))

    # Live prediction example
    print("\n" + "=" * 80)
    print("LIVE PREDICTION EXAMPLE")
    print("=" * 80)
    print("Scenario: Bruins down by 1, 3:30 remaining")

    live_pred = analyzer.get_live_prediction(
        team="Boston Bruins",
        score_diff=-1,
        current_time_remaining_seconds=210,  # 3:30
        home_game=True,
        season="20232024"
    )

    print(json.dumps(live_pred, indent=2))
