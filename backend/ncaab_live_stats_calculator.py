"""
NCAAB Live vs Baseline Stats Calculator

Calculates variance between live game performance and season baseline averages
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class NCAABLiveStatsCalculator:
    def __init__(self):
        pass

    def calculate_possessions(self, live_stats: Dict) -> float:
        try:
            possessions = (
                live_stats.get('fg_att', 0) +
                0.4 * live_stats.get('ft_att', 0) +
                live_stats.get('turnovers', 0) -
                live_stats.get('off_rebounds', 0)
            )
            return max(possessions, 0.0)
        except Exception as e:
            logger.error(f'Error calculating possessions: {e}')
            return 0.0

    def calculate_shooting_variance(self, live_stats: Dict, baseline: Dict) -> Dict:
        try:
            live_fg_pct = (live_stats['fg_made'] / live_stats['fg_att'] * 100) if live_stats['fg_att'] > 0 else 0
            live_three_pct = (live_stats['three_made'] / live_stats['three_att'] * 100) if live_stats['three_att'] > 0 else 0
            live_ft_pct = (live_stats['ft_made'] / live_stats['ft_att'] * 100) if live_stats['ft_att'] > 0 else 0

            # TeamRankings stores percentages as whole numbers (e.g., 29.9 not 0.299)
            season_fg_pct = baseline.get('field_goal_pct', 0) if baseline.get('field_goal_pct') else 0
            season_three_pct = baseline.get('three_point_pct', 0) if baseline.get('three_point_pct') else 0
            season_ft_pct = baseline.get('free_throw_pct', 0) if baseline.get('free_throw_pct') else 0

            fg_variance = live_fg_pct - season_fg_pct
            three_variance = live_three_pct - season_three_pct
            ft_variance = live_ft_pct - season_ft_pct

            return {
                'fg_pct': round(live_fg_pct, 1),
                'fg_variance': round(fg_variance, 1),
                'three_pct': round(live_three_pct, 1),
                'three_variance': round(three_variance, 1),
                'ft_pct': round(live_ft_pct, 1),
                'ft_variance': round(ft_variance, 1),
                'is_hot_fg': fg_variance >= 6.0,
                'is_cold_fg': fg_variance <= -6.0,
                'is_hot_three': three_variance >= 10.0,
                'is_cold_three': three_variance <= -10.0
            }
        except Exception as e:
            logger.error(f'Error calculating shooting variance: {e}')
            return {}

    def calculate_pace_variance(self, live_possessions: float, baseline: Dict, period: int, clock: str) -> Dict:
        try:
            season_tempo = baseline.get('possessions_per_game') or baseline.get('adj_tempo', 70.0)
            
            if period == 1:
                minutes_elapsed = 20 - self._parse_clock_to_minutes(clock)
                game_progress = minutes_elapsed / 40.0
            else:
                minutes_elapsed = 20 + (20 - self._parse_clock_to_minutes(clock))
                game_progress = minutes_elapsed / 40.0
            
            game_progress = max(0.0, min(1.0, game_progress))
            expected_possessions = season_tempo * game_progress
            pace_variance = live_possessions - expected_possessions
            projected_total = live_possessions / game_progress if game_progress > 0 else season_tempo
            
            return {
                'live_possessions': round(live_possessions, 1),
                'expected_possessions': round(expected_possessions, 1),
                'pace_variance': round(pace_variance, 1),
                'is_faster': pace_variance >= 3.0,
                'is_slower': pace_variance <= -3.0,
                'projected_total_possessions': round(projected_total, 1)
            }
        except Exception as e:
            logger.error(f'Error calculating pace variance: {e}')
            return {}

    def calculate_efficiency_variance(self, live_stats: Dict, live_possessions: float, baseline: Dict) -> Dict:
        try:
            points = live_stats.get('points', 0)
            live_efficiency = (points / live_possessions * 100) if live_possessions > 0 else 0
            # TeamRankings stores efficiency as whole numbers
            season_efficiency = baseline.get('offensive_efficiency', 1.0) if baseline.get('offensive_efficiency') else 0
            efficiency_variance = live_efficiency - season_efficiency
            
            return {
                'live_efficiency': round(live_efficiency, 1),
                'season_efficiency': round(season_efficiency, 1),
                'efficiency_variance': round(efficiency_variance, 1),
                'is_underperforming': efficiency_variance <= -8.0,
                'is_overperforming': efficiency_variance >= 8.0
            }
        except Exception as e:
            logger.error(f'Error calculating efficiency variance: {e}')
            return {}

    def _parse_clock_to_minutes(self, clock: str) -> float:
        try:
            if ':' in clock:
                parts = clock.split(':')
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes + seconds / 60.0
            else:
                return float(clock)
        except:
            return 0.0

    def calculate_regression_probability(self, shooting_variance: Dict, efficiency_variance: Dict) -> Dict:
        try:
            three_var = shooting_variance.get('three_variance', 0)
            fg_var = shooting_variance.get('fg_variance', 0)
            eff_var = efficiency_variance.get('efficiency_variance', 0)
            
            if three_var <= -15.0 or (fg_var <= -10.0 and eff_var <= -12.0):
                confidence = 'HIGH' if three_var <= -20.0 else 'MEDIUM'
                expected_regression = abs(eff_var) * 0.4
                
                return {
                    'has_regression_opportunity': True,
                    'confidence': confidence,
                    'reason': f'Team shooting {abs(three_var):.1f}% below season 3PT average',
                    'expected_regression_points': round(expected_regression, 1)
                }
            elif three_var >= 15.0 or (fg_var >= 10.0 and eff_var >= 12.0):
                return {
                    'has_regression_opportunity': True,
                    'confidence': 'MEDIUM',
                    'reason': f'Team shooting {three_var:.1f}% above season avg (likely unsustainable)',
                    'expected_regression_points': round(abs(eff_var) * 0.3, 1)
                }
            
            return {
                'has_regression_opportunity': False,
                'confidence': 'NONE',
                'reason': 'Shooting within normal range',
                'expected_regression_points': 0.0
            }
        except Exception as e:
            logger.error(f'Error calculating regression probability: {e}')
            return {}

    def analyze_team_performance(self, live_box_score: Dict, baseline_stats: Dict, team_side: str) -> Dict:
        try:
            team_stats = live_box_score.get(team_side, {})
            period = live_box_score.get('period', 1)
            clock = live_box_score.get('clock', '20:00')
            
            possessions = self.calculate_possessions(team_stats)
            shooting = self.calculate_shooting_variance(team_stats, baseline_stats)
            pace = self.calculate_pace_variance(possessions, baseline_stats, period, clock)
            efficiency = self.calculate_efficiency_variance(team_stats, possessions, baseline_stats)
            regression = self.calculate_regression_probability(shooting, efficiency)
            
            # Get emoji indicators
            shooting_emoji = self.get_shooting_emoji(shooting.get("three_variance", 0))
            pace_emoji = self.get_pace_emoji(pace.get("pace_variance", 0))
            
            return {
                'team_name': team_stats.get('team_name', 'Unknown'),
                'team_abv': team_stats.get('team_abv', 'UNK'),
                'possessions': possessions,
                'shooting': shooting,
                'pace': pace,
                "shooting_emoji": shooting_emoji,
                "pace_emoji": pace_emoji,
                'efficiency': efficiency,
                'regression': regression,
                'period': period,
                'clock': clock
            }
        except Exception as e:
            logger.error(f'Error analyzing team performance: {e}')
            return {}

    def get_shooting_emoji(self, variance: float) -> Dict:
        """
        Get shooting emoji indicator based on variance intensity
        
        Args:
            variance: Shooting percentage variance (e.g., -25.2 for 25.2% below avg)
            
        Returns:
            {'emoji': '❄️❄️❄️', 'level': 'ICE COLD', 'count': 3}
        """
        if variance >= 15:
            return {'emoji': '🔥🔥🔥', 'level': 'SCORCHING', 'count': 3}
        elif variance >= 10:
            return {'emoji': '🔥🔥', 'level': 'HOT', 'count': 2}
        elif variance >= 6:
            return {'emoji': '🔥', 'level': 'WARM', 'count': 1}
        elif variance <= -15:
            return {'emoji': '❄️❄️❄️', 'level': 'ICE COLD', 'count': 3}
        elif variance <= -10:
            return {'emoji': '❄️❄️', 'level': 'COLD', 'count': 2}
        elif variance <= -6:
            return {'emoji': '❄️', 'level': 'COOL', 'count': 1}
        else:
            return {'emoji': '✅', 'level': 'NORMAL', 'count': 0}
    
    def get_pace_emoji(self, variance: float) -> Dict:
        """
        Get pace emoji indicator based on variance intensity
        
        Args:
            variance: Pace variance in possessions (e.g., +3.2)
            
        Returns:
            {'emoji': '⚡⚡', 'level': 'VERY FAST', 'count': 2}
        """
        if variance >= 6:
            return {'emoji': '⚡⚡⚡', 'level': 'BLAZING', 'count': 3}
        elif variance >= 4:
            return {'emoji': '⚡⚡', 'level': 'VERY FAST', 'count': 2}
        elif variance >= 3:
            return {'emoji': '⚡', 'level': 'FAST', 'count': 1}
        elif variance <= -6:
            return {'emoji': '🐢🐢🐢', 'level': 'CRAWLING', 'count': 3}
        elif variance <= -4:
            return {'emoji': '🐢🐢', 'level': 'VERY SLOW', 'count': 2}
        elif variance <= -3:
            return {'emoji': '🐢', 'level': 'SLOW', 'count': 1}
        else:
            return {'emoji': '✅', 'level': 'NORMAL', 'count': 0}
