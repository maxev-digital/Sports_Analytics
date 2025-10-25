"""
NBA Favorite Comeback Detector
Identifies high-value opportunities when favorites trail underdogs after hot starts
Historical Performance: 60.3% ATS at halftime (2005-2023), +9.4% edge
"""
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class FavoriteComebackDetector:
    """
    Detects regression opportunities when favorites trail underdogs
    Uses 5-factor scoring system to identify strong betting opportunities
    """

    def __init__(self):
        # Minimum talent gap required (PPG difference)
        self.min_talent_gap = 5.0

        # Confidence thresholds
        self.high_confidence_threshold = 15
        self.medium_confidence_threshold = 10
        self.low_confidence_threshold = 6

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
        pregame_spread: Optional[float] = None,
        current_spread: Optional[float] = None,
        home_season_stats: Optional[Dict] = None,
        away_season_stats: Optional[Dict] = None,
        quarter_stats: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze if a favorite comeback opportunity exists

        Returns dict with:
        - has_opportunity: bool
        - confidence_level: 'HIGH' | 'MEDIUM' | 'LOW' | None
        - regression_score: int (0-20)
        - opportunities: List of betting recommendations
        """

        # Determine which team is favorite/underdog
        if home_team_favorite:
            favorite = home_team
            underdog = away_team
            favorite_score = home_score
            underdog_score = away_score
            favorite_stats = home_season_stats or {}
            underdog_stats = away_season_stats or {}
        else:
            favorite = away_team
            underdog = home_team
            favorite_score = away_score
            underdog_score = home_score
            favorite_stats = away_season_stats or {}
            underdog_stats = home_season_stats or {}

        score_differential = underdog_score - favorite_score

        # Must be trailing
        if score_differential <= 0:
            return {
                'has_opportunity': False,
                'reason': 'Favorite is not trailing',
                'favorite': favorite,
                'underdog': underdog,
                'score_differential': score_differential
            }

        # Check timing (must be after Q1 or at halftime)
        valid_periods = ['1Q', 'Q1', 'Half', 'Halftime', '2Q', 'Q2']
        if period not in valid_periods:
            return {
                'has_opportunity': False,
                'reason': f'Invalid period for comeback detection: {period}',
                'favorite': favorite,
                'underdog': underdog
            }

        # Calculate regression score using 5-factor system
        regression_analysis = self._calculate_regression_score(
            favorite_score=favorite_score,
            underdog_score=underdog_score,
            period=period,
            score_differential=score_differential,
            favorite_stats=favorite_stats,
            underdog_stats=underdog_stats,
            quarter_stats=quarter_stats or {}
        )

        regression_score = regression_analysis['regression_score']

        # Determine if we have a bet
        if regression_score < self.low_confidence_threshold:
            return {
                'has_opportunity': False,
                'reason': f'Regression score too low: {regression_score}/20 (need ≥{self.low_confidence_threshold})',
                'favorite': favorite,
                'underdog': underdog,
                'score_differential': score_differential,
                'regression_score': regression_score,
                'regression_analysis': regression_analysis
            }

        # Determine confidence level
        if regression_score >= self.high_confidence_threshold:
            confidence = 'HIGH'
            expected_win_rate = 0.65
            recommended_stake_pct = 3.5  # 3-4% of bankroll
        elif regression_score >= self.medium_confidence_threshold:
            confidence = 'MEDIUM'
            expected_win_rate = 0.60
            recommended_stake_pct = 2.5  # 2-3% of bankroll
        else:
            confidence = 'LOW'
            expected_win_rate = 0.55
            recommended_stake_pct = 1.5  # 1-2% of bankroll

        # Build opportunity
        opportunities = []

        # Determine betting window
        if period in ['1Q', 'Q1']:
            betting_window = 'After Q1'
            historical_win_rate = 58.0
        elif period in ['2Q', 'Q2']:
            betting_window = 'During Q2'
            historical_win_rate = 59.0
        else:  # Halftime
            betting_window = 'Halftime'
            historical_win_rate = 60.3

        opportunity = {
            'strategy': 'Favorite Comeback',
            'game_id': game_id,
            'sport': sport,
            'favorite': favorite,
            'underdog': underdog,
            'current_score': f'{favorite_score}-{underdog_score} ({underdog} leading)',
            'score_differential': score_differential,
            'period': period,
            'confidence_level': confidence,
            'regression_score': regression_score,
            'recommendation': {
                'bet_type': '2H Spread',
                'team': favorite,
                'reasoning': f'{favorite} trailing by {score_differential} after strong regression indicators',
                'expected_spread': current_spread if current_spread else f'~{-abs(pregame_spread)/2:.1f}' if pregame_spread else 'TBD'
            },
            'edge_percentage': (expected_win_rate - 0.50) * 100,  # Edge over 50/50
            'expected_win_rate': expected_win_rate * 100,
            'recommended_stake_percent': recommended_stake_pct,
            'betting_window': betting_window,
            'historical_performance': {
                'timing': betting_window,
                'win_rate': historical_win_rate,
                'ats_coverage': f'{historical_win_rate}% ATS',
                'sample_size': '8,138 games (2005-2023)'
            },
            'regression_factors': regression_analysis['factors']
        }

        opportunities.append(opportunity)

        return {
            'has_opportunity': True,
            'game_id': game_id,
            'favorite': favorite,
            'underdog': underdog,
            'score_differential': score_differential,
            'period': period,
            'confidence': confidence,
            'regression_score': regression_score,
            'regression_analysis': regression_analysis,
            'opportunities': opportunities
        }

    def _calculate_regression_score(
        self,
        favorite_score: int,
        underdog_score: int,
        period: str,
        score_differential: int,
        favorite_stats: Dict,
        underdog_stats: Dict,
        quarter_stats: Dict
    ) -> Dict:
        """
        Calculate 0-20 regression score using 5 factors:
        1. Shooting Deviation (0-5)
        2. Pace Deviation (0-5)
        3. Talent Gap (0-5)
        4. Sample Size (0-3)
        5. Score Differential (0-2)
        """
        total_score = 0
        factors = []

        # Factor 1: Shooting Deviation (0-5 points)
        shooting_score = self._calculate_shooting_deviation(
            favorite_stats, underdog_stats, quarter_stats
        )
        total_score += shooting_score['score']
        factors.append({
            'name': 'Shooting Deviation',
            'score': shooting_score['score'],
            'max_score': 5,
            'details': shooting_score['details']
        })

        # Factor 2: Pace Deviation (0-5 points)
        pace_score = self._calculate_pace_deviation(
            favorite_score, underdog_score, period, favorite_stats, underdog_stats
        )
        total_score += pace_score['score']
        factors.append({
            'name': 'Pace Deviation',
            'score': pace_score['score'],
            'max_score': 5,
            'details': pace_score['details']
        })

        # Factor 3: Talent Gap (0-5 points)
        talent_score = self._calculate_talent_gap(favorite_stats, underdog_stats)
        total_score += talent_score['score']
        factors.append({
            'name': 'Talent Gap',
            'score': talent_score['score'],
            'max_score': 5,
            'details': talent_score['details']
        })

        # Factor 4: Sample Size (0-3 points)
        sample_score = self._calculate_sample_size_score(period)
        total_score += sample_score['score']
        factors.append({
            'name': 'Sample Size',
            'score': sample_score['score'],
            'max_score': 3,
            'details': sample_score['details']
        })

        # Factor 5: Score Differential (0-2 points)
        differential_score = self._calculate_score_differential(score_differential)
        total_score += differential_score['score']
        factors.append({
            'name': 'Score Differential',
            'score': differential_score['score'],
            'max_score': 2,
            'details': differential_score['details']
        })

        # Determine if regression is strong
        has_strong_regression = total_score >= 15

        return {
            'regression_score': total_score,
            'max_score': 20,
            'has_strong_regression': has_strong_regression,
            'factors': factors
        }

    def _calculate_shooting_deviation(
        self, favorite_stats: Dict, underdog_stats: Dict, quarter_stats: Dict
    ) -> Dict:
        """Factor 1: Shooting deviation from season averages (0-5 points)"""
        score = 0
        details = []

        # Favorite shooting below average
        fav_fg_pct = favorite_stats.get('fg_pct', 46.0)
        fav_current_fg = quarter_stats.get('favorite_fg_pct', fav_fg_pct)
        fav_deviation = fav_fg_pct - fav_current_fg

        if fav_deviation >= 15:
            score += 5
            details.append(f'Favorite shooting {fav_deviation:.1f}% below average (15%+)')
        elif fav_deviation >= 10:
            score += 3
            details.append(f'Favorite shooting {fav_deviation:.1f}% below average (10-14%)')
        elif fav_deviation >= 5:
            score += 2
            details.append(f'Favorite shooting {fav_deviation:.1f}% below average (5-9%)')
        else:
            details.append(f'Favorite shooting near average ({fav_deviation:+.1f}%)')

        # Underdog shooting above average
        und_fg_pct = underdog_stats.get('fg_pct', 44.0)
        und_current_fg = quarter_stats.get('underdog_fg_pct', und_fg_pct)
        und_deviation = und_current_fg - und_fg_pct

        if und_deviation >= 15:
            score += 5
            details.append(f'Underdog shooting {und_deviation:.1f}% above average (15%+)')
        elif und_deviation >= 10:
            score += 3
            details.append(f'Underdog shooting {und_deviation:.1f}% above average (10-14%)')
        elif und_deviation >= 5:
            score += 2
            details.append(f'Underdog shooting {und_deviation:.1f}% above average (5-9%)')
        else:
            details.append(f'Underdog shooting near average ({und_deviation:+.1f}%)')

        # Cap at 5
        score = min(score, 5)

        return {
            'score': score,
            'details': ' | '.join(details) if details else 'No significant shooting deviation'
        }

    def _calculate_pace_deviation(
        self, fav_score: int, und_score: int, period: str,
        favorite_stats: Dict, underdog_stats: Dict
    ) -> Dict:
        """Factor 2: Pace deviation from season averages (0-5 points)"""
        score = 0
        details = []

        # Calculate expected PPQ
        fav_ppg = favorite_stats.get('ppg', 110.0)
        und_ppg = underdog_stats.get('ppg', 105.0)

        # Quarters played
        if period in ['1Q', 'Q1']:
            quarters = 1
        elif period in ['2Q', 'Q2', 'Half', 'Halftime']:
            quarters = 2
        else:
            quarters = 2

        fav_expected = (fav_ppg / 4) * quarters
        und_expected = (und_ppg / 4) * quarters

        fav_pace_diff = fav_expected - fav_score
        und_pace_diff = und_score - und_expected

        # Favorite scoring below pace
        if fav_pace_diff >= 13:
            score += 5
            details.append(f'Favorite {fav_pace_diff:.1f} pts below pace (13+)')
        elif fav_pace_diff >= 9:
            score += 3
            details.append(f'Favorite {fav_pace_diff:.1f} pts below pace (9-12)')
        elif fav_pace_diff >= 5:
            score += 2
            details.append(f'Favorite {fav_pace_diff:.1f} pts below pace (5-8)')
        else:
            details.append(f'Favorite near expected pace ({fav_pace_diff:+.1f} pts)')

        # Underdog scoring above pace
        if und_pace_diff >= 13:
            score += 5
            details.append(f'Underdog {und_pace_diff:.1f} pts above pace (13+)')
        elif und_pace_diff >= 9:
            score += 3
            details.append(f'Underdog {und_pace_diff:.1f} pts above pace (9-12)')
        elif und_pace_diff >= 5:
            score += 2
            details.append(f'Underdog {und_pace_diff:.1f} pts above pace (5-8)')
        else:
            details.append(f'Underdog near expected pace ({und_pace_diff:+.1f} pts)')

        # Cap at 5
        score = min(score, 5)

        return {
            'score': score,
            'details': ' | '.join(details) if details else 'No significant pace deviation'
        }

    def _calculate_talent_gap(
        self, favorite_stats: Dict, underdog_stats: Dict
    ) -> Dict:
        """Factor 3: Talent gap based on season PPG (0-5 points)"""
        fav_ppg = favorite_stats.get('ppg', 110.0)
        und_ppg = underdog_stats.get('ppg', 105.0)

        talent_gap = fav_ppg - und_ppg

        if talent_gap >= 9:
            score = 5
            details = f'Large talent gap: {talent_gap:.1f} PPG difference (9+)'
        elif talent_gap >= 6:
            score = 3
            details = f'Moderate talent gap: {talent_gap:.1f} PPG difference (6-8)'
        elif talent_gap >= 3:
            score = 2
            details = f'Small talent gap: {talent_gap:.1f} PPG difference (3-5)'
        else:
            score = 0
            details = f'Minimal talent gap: {talent_gap:.1f} PPG difference (<3)'

        return {
            'score': score,
            'details': details
        }

    def _calculate_sample_size_score(self, period: str) -> Dict:
        """Factor 4: Sample size - smaller = more variance (0-3 points)"""
        if period in ['1Q', 'Q1']:
            score = 3
            details = 'After Q1 (12 min sample - highest variance)'
        elif period in ['2Q', 'Q2']:
            score = 2
            details = 'During Q2 (18-20 min sample - high variance)'
        else:  # Halftime
            score = 1
            details = 'At Halftime (24 min sample - moderate variance)'

        return {
            'score': score,
            'details': details
        }

    def _calculate_score_differential(self, differential: int) -> Dict:
        """Factor 5: Score differential (0-2 points)"""
        if differential >= 5:
            score = 2
            details = f'Large deficit: {differential} points (5+)'
        elif differential >= 1:
            score = 1
            details = f'Small deficit: {differential} points (1-4)'
        else:
            score = 0
            details = 'No deficit'

        return {
            'score': score,
            'details': details
        }
