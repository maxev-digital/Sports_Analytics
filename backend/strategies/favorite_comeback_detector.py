"""
Favorite Comeback Detector
Identifies opportunities when favorites trail underdogs after hot starts
and are likely to regress to their true talent level

Based on historical data:
- Favorites trailing after Q1: Cover 2H spread 58% of the time
- Favorites trailing at halftime: 60.3% ATS in 2H (2005-2023)
- Public overreacts to underdog hot starts, creating value on favorite
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FavoriteComeb ackDetector:
    """
    Detect when favorites are due for comebacks after trailing underdogs
    """

    def __init__(self):
        self.game_states: Dict[str, Dict] = {}
        self.alert_history: Dict[str, List[Dict]] = {}

    def analyze_comeback_opportunity(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        period: str,
        time_remaining: str,
        home_team_favorite: bool,
        pregame_spread: float,  # Positive if home favored, negative if away favored
        current_spread: Optional[float] = None,
        home_season_stats: Optional[Dict] = None,
        away_season_stats: Optional[Dict] = None,
        quarter_stats: Optional[Dict] = None  # Stats for current quarter/period
    ) -> Dict[str, Any]:
        """
        Analyze if a favorite comeback opportunity exists

        Args:
            game_id: Unique game identifier
            sport: Sport type (NBA, NCAAB, etc.)
            home_team: Home team name
            away_team: Away team name
            home_score: Current home team score
            away_score: Current away team score
            period: Current period/quarter
            time_remaining: Time remaining in period
            home_team_favorite: True if home team was pregame favorite
            pregame_spread: Pregame spread (positive = home favored)
            current_spread: Current live spread
            home_season_stats: Season averages for home team (FG%, PPG, etc.)
            away_season_stats: Season averages for away team
            quarter_stats: Current period shooting percentages

        Returns:
            Dict with comeback opportunity analysis and alerts
        """
        # Determine favorite and underdog
        if home_team_favorite:
            favorite = home_team
            favorite_score = home_score
            underdog = away_team
            underdog_score = away_score
            favorite_is_home = True
        else:
            favorite = away_team
            favorite_score = away_score
            underdog = home_team
            underdog_score = home_score
            favorite_is_home = False

        score_diff = favorite_score - underdog_score
        is_favorite_trailing = score_diff < 0

        # Only analyze if favorite is trailing
        if not is_favorite_trailing:
            return {
                'game_id': game_id,
                'has_opportunity': False,
                'reason': 'Favorite is not trailing'
            }

        # Check if we're in the right time window (Q1 end, Q2, or halftime)
        is_right_timing = self._is_right_timing(sport, period, time_remaining)

        if not is_right_timing:
            return {
                'game_id': game_id,
                'has_opportunity': False,
                'reason': f'Wrong timing: {period}'
            }

        # Calculate regression indicators
        regression_analysis = self._analyze_regression_potential(
            favorite=favorite,
            underdog=underdog,
            favorite_score=favorite_score,
            underdog_score=underdog_score,
            period=period,
            home_season_stats=home_season_stats,
            away_season_stats=away_season_stats,
            quarter_stats=quarter_stats,
            favorite_is_home=favorite_is_home
        )

        # Determine if this is a strong comeback opportunity
        opportunities = []

        if regression_analysis['has_strong_regression']:
            opportunity = self._generate_comeback_alert(
                game_id=game_id,
                sport=sport,
                favorite=favorite,
                underdog=underdog,
                score_diff=abs(score_diff),
                period=period,
                pregame_spread=pregame_spread,
                current_spread=current_spread,
                regression_analysis=regression_analysis,
                home_team=home_team,
                away_team=away_team,
                home_score=home_score,
                away_score=away_score
            )
            opportunities.append(opportunity)

        # Store state
        self.game_states[game_id] = {
            'favorite': favorite,
            'underdog': underdog,
            'score_diff': score_diff,
            'period': period,
            'regression_analysis': regression_analysis,
            'timestamp': datetime.now().isoformat()
        }

        return {
            'game_id': game_id,
            'sport': sport,
            'favorite': favorite,
            'underdog': underdog,
            'score_differential': score_diff,
            'period': period,
            'has_opportunity': len(opportunities) > 0,
            'regression_analysis': regression_analysis,
            'opportunities': opportunities,
            'timestamp': datetime.now().isoformat()
        }

    def _is_right_timing(self, sport: str, period: str, time_remaining: str) -> bool:
        """
        Check if we're in the right timing window for comeback bets

        Best timing:
        - End of Q1 (last 2 minutes)
        - During Q2 (entire quarter)
        - Halftime
        """
        if sport in ['NBA', 'NCAAB']:
            # Q1 end (last 2 min), Q2 anytime, Halftime
            if period in ['1Q', '1', 'first']:
                # Check if < 2 min remaining in Q1
                try:
                    if ':' in time_remaining:
                        parts = time_remaining.split(':')
                        minutes = int(parts[0])
                        return minutes < 2
                except:
                    pass
                return False
            elif period in ['2Q', '2', 'second', 'Half', 'halftime']:
                return True
            else:
                return False

        return False

    def _analyze_regression_potential(
        self,
        favorite: str,
        underdog: str,
        favorite_score: int,
        underdog_score: int,
        period: str,
        home_season_stats: Optional[Dict],
        away_season_stats: Optional[Dict],
        quarter_stats: Optional[Dict],
        favorite_is_home: bool
    ) -> Dict[str, Any]:
        """
        Analyze how much regression is expected

        Strong regression indicators:
        1. Underdog shooting WAY above season average (65% vs 45%)
        2. Favorite shooting WAY below season average (38% vs 48%)
        3. Large talent gap (favorite expected to win by 8+)
        4. Small sample size (Q1 only)
        """
        regression_score = 0.0
        regression_details = {}

        # Get season stats if available
        if home_season_stats and away_season_stats:
            fav_season = home_season_stats if favorite_is_home else away_season_stats
            und_season = away_season_stats if favorite_is_home else home_season_stats

            # Check shooting percentages if quarter stats available
            if quarter_stats:
                fav_current_fg = quarter_stats.get('favorite_fg_pct', 0)
                und_current_fg = quarter_stats.get('underdog_fg_pct', 0)
                fav_season_fg = fav_season.get('fg_pct', 47.0)
                und_season_fg = und_season.get('fg_pct', 45.0)

                # Calculate deviation from season average
                fav_deviation = fav_current_fg - fav_season_fg
                und_deviation = und_current_fg - und_season_fg

                regression_details['favorite_fg_deviation'] = fav_deviation
                regression_details['underdog_fg_deviation'] = und_deviation

                # Favorite shooting below average (good for regression)
                if fav_deviation < -5.0:  # Shooting 5%+ below average
                    regression_score += abs(fav_deviation) * 0.5

                # Underdog shooting above average (good for regression)
                if und_deviation > 5.0:  # Shooting 5%+ above average
                    regression_score += und_deviation * 0.5

            # Check scoring pace
            fav_season_ppg = fav_season.get('ppg', 110.0)
            und_season_ppg = und_season.get('ppg', 105.0)

            # Calculate current pace (extrapolate to full game)
            if period in ['1Q', '1', 'first']:
                minutes_played = 12
            elif period in ['2Q', '2', 'second']:
                minutes_played = 24
            else:
                minutes_played = 24  # Halftime

            fav_current_pace = (favorite_score / minutes_played) * 48
            und_current_pace = (underdog_score / minutes_played) * 48

            fav_pace_deviation = fav_current_pace - fav_season_ppg
            und_pace_deviation = und_current_pace - und_season_ppg

            regression_details['favorite_pace_deviation'] = round(fav_pace_deviation, 1)
            regression_details['underdog_pace_deviation'] = round(und_pace_deviation, 1)

            # Favorite scoring below average
            if fav_pace_deviation < -8.0:  # Scoring 8+ PPG below average
                regression_score += abs(fav_pace_deviation) * 0.3

            # Underdog scoring above average
            if und_pace_deviation > 8.0:  # Scoring 8+ PPG above average
                regression_score += und_pace_deviation * 0.3

            # Talent gap (PPG difference)
            talent_gap = fav_season_ppg - und_season_ppg
            regression_details['talent_gap'] = round(talent_gap, 1)

            if talent_gap > 5.0:  # Favorite averages 5+ more PPG
                regression_score += talent_gap * 0.4

        # Small sample size bonus
        if period in ['1Q', '1', 'first']:
            regression_score += 5.0  # Q1 = small sample, high regression potential

        # Determine strength
        has_strong_regression = regression_score >= 10.0
        has_moderate_regression = regression_score >= 6.0

        regression_details['regression_score'] = round(regression_score, 2)
        regression_details['has_strong_regression'] = has_strong_regression
        regression_details['has_moderate_regression'] = has_moderate_regression

        return regression_details

    def _generate_comeback_alert(
        self,
        game_id: str,
        sport: str,
        favorite: str,
        underdog: str,
        score_diff: int,
        period: str,
        pregame_spread: float,
        current_spread: Optional[float],
        regression_analysis: Dict,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int
    ) -> Dict[str, Any]:
        """
        Generate comeback betting alert

        Historical data:
        - Favorites trailing after Q1: 58% cover 2H spread
        - Favorites trailing at halftime: 60.3% ATS 2H (2005-2023)
        """
        # Determine timing-specific win rate
        if period in ['1Q', '1', 'first']:
            historical_win_rate = 58.0
            timing_desc = "after Q1"
            bet_window = "2nd Half"
        elif period in ['2Q', '2', 'second', 'Half', 'halftime']:
            historical_win_rate = 60.3
            timing_desc = "at halftime"
            bet_window = "2nd Half"
        else:
            historical_win_rate = 55.0
            timing_desc = "mid-game"
            bet_window = "Game"

        # Calculate confidence based on regression score
        regression_score = regression_analysis.get('regression_score', 0)

        if regression_score >= 15.0:
            confidence = 'HIGH'
            edge_pct = 8.0
        elif regression_score >= 10.0:
            confidence = 'MEDIUM'
            edge_pct = 5.0
        else:
            confidence = 'LOW'
            edge_pct = 3.0

        # Determine recommended bet
        if current_spread:
            bet_recommendation = f"{favorite} {current_spread:+.1f} (2H spread)"
        else:
            bet_recommendation = f"{favorite} 2H spread (wait for line)"

        return {
            'type': 'favorite_comeback',
            'strategy': 'Fading Underdog Hot Starts (Regression to Mean)',
            'trigger': f'{favorite} trailing {underdog} by {score_diff} {timing_desc}',
            'confidence_level': confidence,
            'recommendation': {
                'bet_type': '2h_spread',
                'side': favorite,
                'bet_window': bet_window,
                'current_spread': current_spread,
                'reasoning': f'{underdog} playing above true talent level; {favorite} due for regression to mean'
            },
            'regression_indicators': {
                'favorite_shooting': regression_analysis.get('favorite_fg_deviation', 'N/A'),
                'underdog_shooting': regression_analysis.get('underdog_fg_deviation', 'N/A'),
                'favorite_pace': regression_analysis.get('favorite_pace_deviation', 'N/A'),
                'underdog_pace': regression_analysis.get('underdog_pace_deviation', 'N/A'),
                'talent_gap': regression_analysis.get('talent_gap', 'N/A'),
                'regression_score': regression_analysis.get('regression_score', 0)
            },
            'historical_performance': {
                'win_rate': historical_win_rate,
                'sample': f'{sport} favorites trailing {timing_desc} (2005-2023)',
                'ats_coverage': f'{historical_win_rate}% ATS in {bet_window}',
                'variance': 'MEDIUM - Moderate volatility; reliable historical data'
            },
            'edge_percentage': edge_pct,
            'risk_level': 'MEDIUM',
            'stake_recommendation': '2-4% bankroll',
            'game_details': {
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'favorite': favorite,
                'underdog': underdog,
                'score_differential': score_diff,
                'pregame_spread': pregame_spread
            },
            'timing': {
                'period': period,
                'alert_time': datetime.now().isoformat(),
                'bet_window': bet_window
            }
        }

    def get_game_state(self, game_id: str) -> Optional[Dict]:
        """Get current game state"""
        return self.game_states.get(game_id)

    def get_alert_history(self, game_id: str) -> List[Dict]:
        """Get alert history for a game"""
        return self.alert_history.get(game_id, [])

    def clear_game_data(self, game_id: str):
        """Clear tracking data for a completed game"""
        if game_id in self.game_states:
            del self.game_states[game_id]
        if game_id in self.alert_history:
            del self.alert_history[game_id]
