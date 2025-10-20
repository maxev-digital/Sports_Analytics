"""
Halftime/Period Betting Tracker
Implements halftime adjustments and period-specific betting strategies

Based on Live_Betting_Strategies.md:
- NFL/NCAA Football: Halftime adjustments
- NBA/NCAA Basketball: Quarter-specific wagers
- NHL: Period-specific betting
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HalftimeTracker:
    """
    Track halftime/period betting opportunities across multiple sports
    """

    def __init__(self):
        self.game_states: Dict[str, Dict] = {}
        self.period_history: Dict[str, List[Dict]] = {}

    def update_game_state(
        self,
        game_id: str,
        sport: str,
        period: str,
        time_remaining: str,
        home_score: int,
        away_score: int,
        home_team: str,
        away_team: str
    ) -> Dict[str, Any]:
        """
        Update game state and detect halftime/period transitions

        Args:
            game_id: Unique game identifier
            sport: Sport type (NBA, NFL, NHL, NCAAF, NCAAB)
            period: Current period (1Q, 2Q, 3Q, 4Q, 1P, 2P, 3P, etc.)
            time_remaining: Time left in period
            home_score: Home team score
            away_score: Away team score
            home_team: Home team name
            away_team: Away team name

        Returns:
            Dict with period analysis and betting opportunities
        """
        current_state = {
            'sport': sport,
            'period': period,
            'time_remaining': time_remaining,
            'home_score': home_score,
            'away_score': away_score,
            'home_team': home_team,
            'away_team': away_team,
            'timestamp': datetime.now().isoformat()
        }

        # Check for period transitions
        previous_state = self.game_states.get(game_id)
        is_halftime = self._is_halftime_transition(sport, period, previous_state)
        is_period_end = self._is_period_end(sport, period, time_remaining)

        # Store current state
        self.game_states[game_id] = current_state

        # Track period history
        if game_id not in self.period_history:
            self.period_history[game_id] = []
        self.period_history[game_id].append(current_state.copy())

        # Generate analysis
        analysis = self._analyze_period_opportunity(
            game_id, sport, period, home_score, away_score,
            is_halftime, is_period_end, previous_state
        )

        return analysis

    def _is_halftime_transition(
        self,
        sport: str,
        current_period: str,
        previous_state: Optional[Dict]
    ) -> bool:
        """Check if we're transitioning to halftime"""
        if not previous_state:
            return False

        previous_period = previous_state.get('period', '')

        if sport in ['NBA', 'NCAAB']:
            # End of 2Q
            return current_period == 'Half' or (previous_period == '2Q' and current_period in ['Half', '3Q'])
        elif sport in ['NFL', 'NCAAF']:
            # End of 2Q
            return current_period == 'Half' or (previous_period == '2' and current_period in ['Half', '3'])
        elif sport == 'NHL':
            # End of 1st or 2nd period
            return current_period in ['1P_END', '2P_END'] or (
                previous_period in ['1', '2'] and current_period in ['2', '3']
            )

        return False

    def _is_period_end(self, sport: str, period: str, time_remaining: str) -> bool:
        """Check if period is ending soon (last minute)"""
        try:
            # Parse time_remaining (format: "MM:SS" or "M:SS")
            if ':' in time_remaining:
                parts = time_remaining.split(':')
                minutes = int(parts[0])
                seconds = int(parts[1])
                total_seconds = minutes * 60 + seconds
                return total_seconds <= 60  # Last minute
        except (ValueError, IndexError):
            pass

        return False

    def _analyze_period_opportunity(
        self,
        game_id: str,
        sport: str,
        period: str,
        home_score: int,
        away_score: int,
        is_halftime: bool,
        is_period_end: bool,
        previous_state: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Analyze betting opportunities based on period situation

        Returns analysis with:
        - Opportunity type
        - Confidence level
        - Recommended bet
        - Edge calculation
        - Historical context
        """
        score_diff = home_score - away_score
        total_score = home_score + away_score

        opportunities = []

        # Halftime adjustment opportunities (NFL/NCAAF/NBA/NCAAB)
        if is_halftime:
            halftime_opp = self._analyze_halftime_adjustment(
                sport, score_diff, total_score, home_score, away_score
            )
            if halftime_opp:
                opportunities.append(halftime_opp)

        # Period-specific opportunities
        if sport in ['NBA', 'NCAAB']:
            period_opp = self._analyze_basketball_period(
                period, total_score, score_diff
            )
            if period_opp:
                opportunities.append(period_opp)
        elif sport == 'NHL':
            period_opp = self._analyze_hockey_period(
                period, total_score, score_diff
            )
            if period_opp:
                opportunities.append(period_opp)

        # Period end opportunities
        if is_period_end:
            end_opp = self._analyze_period_end_opportunity(
                sport, period, score_diff
            )
            if end_opp:
                opportunities.append(end_opp)

        return {
            'game_id': game_id,
            'sport': sport,
            'period': period,
            'is_halftime': is_halftime,
            'is_period_end': is_period_end,
            'score_diff': score_diff,
            'total_score': total_score,
            'opportunities': opportunities,
            'period_count': len(self.period_history.get(game_id, [])),
            'timestamp': datetime.now().isoformat()
        }

    def _analyze_halftime_adjustment(
        self,
        sport: str,
        score_diff: int,
        total_score: int,
        home_score: int,
        away_score: int
    ) -> Optional[Dict]:
        """
        Analyze halftime betting opportunities

        Strategy (from Live_Betting_Strategies.md):
        - Pre-game favorites trailing at halftime: 60.3% ATS (2005-2023)
        - Coaching adjustments favor better teams
        - College blowouts common in 2nd half
        """
        if sport not in ['NFL', 'NCAAF', 'NBA', 'NCAAB']:
            return None

        # Check if this looks like a favorite trailing scenario
        # (We'd need pre-game odds to be certain, but large deficit suggests underdog leading)
        if abs(score_diff) >= 7 and sport in ['NFL', 'NCAAF']:
            trailing_team = 'away' if score_diff > 0 else 'home'
            leading_team = 'home' if score_diff > 0 else 'away'

            return {
                'type': 'halftime_adjustment',
                'strategy': 'Halftime Adjustments (Second-Half Edges)',
                'trigger': f'Halftime score differential: {abs(score_diff)} points',
                'confidence_level': 'LOW' if abs(score_diff) >= 14 else 'MEDIUM',
                'recommendation': {
                    'bet_type': 'second_half_spread',
                    'side': f'{trailing_team}_spread',
                    'reasoning': 'Pre-game favorites trailing at halftime cover 60.3% ATS historically'
                },
                'historical_performance': {
                    'win_rate': 60.3,
                    'sample': '2005-2023 NFL/NCAAF',
                    'roi': 'LOW - Low volatility; once per game; high reliability'
                },
                'edge_percentage': 5.0,  # Estimated edge based on historical
                'risk_level': 'LOW',
                'stake_recommendation': '3-5% bankroll'
            }

        elif abs(score_diff) >= 10 and sport in ['NBA', 'NCAAB']:
            return {
                'type': 'halftime_adjustment',
                'strategy': 'Halftime Adjustments (Second-Half Edges)',
                'trigger': f'Halftime score differential: {abs(score_diff)} points',
                'confidence_level': 'MEDIUM',
                'recommendation': {
                    'bet_type': 'second_half_spread',
                    'side': 'trailing_team',
                    'reasoning': 'Halftime adjustments and regression to mean'
                },
                'historical_performance': {
                    'win_rate': 56.0,
                    'sample': '2024-25 NBA/NCAAB 1H ATS',
                    'roi': 'LOW - Low volatility; once per game; high reliability'
                },
                'edge_percentage': 3.0,
                'risk_level': 'LOW',
                'stake_recommendation': '3-5% bankroll'
            }

        return None

    def _analyze_basketball_period(
        self,
        period: str,
        total_score: int,
        score_diff: int
    ) -> Optional[Dict]:
        """
        Analyze NBA/NCAAB quarter-specific opportunities

        Strategy (from Live_Betting_Strategies.md):
        - 1Q under hits 64-67% (2024-25, ROI 10-27%)
        - 4Q pace typically slower
        - Quarter variance creates edges
        """
        if period == '1Q' or period == '1':
            # First quarter analysis
            return {
                'type': 'quarter_specific',
                'strategy': 'Quarter-Specific Wagers (Pace Changes)',
                'trigger': '1st Quarter in progress',
                'confidence_level': 'MEDIUM',
                'recommendation': {
                    'bet_type': 'quarter_total',
                    'side': 'under',
                    'quarter': '1Q',
                    'reasoning': '1Q under hits 64-67% historically with ROI 10-27%'
                },
                'historical_performance': {
                    'win_rate': 65.5,
                    'roi': 18.5,
                    'sample': '2024-25 NBA/NCAAB',
                    'variance': 'LOW - Low volatility; frequent; pacing reliable'
                },
                'edge_percentage': 8.0,
                'risk_level': 'LOW',
                'stake_recommendation': '3-5% bankroll'
            }

        elif period == '4Q' or period == '4':
            # Fourth quarter typically slower
            return {
                'type': 'quarter_specific',
                'strategy': 'Quarter-Specific Wagers (Pace Changes)',
                'trigger': '4th Quarter in progress',
                'confidence_level': 'LOW',
                'recommendation': {
                    'bet_type': 'quarter_total',
                    'side': 'under',
                    'quarter': '4Q',
                    'reasoning': '4th quarter pace typically slows; clock management'
                },
                'historical_performance': {
                    'win_rate': 55.0,
                    'sample': '2024-25 NBA/NCAAB',
                    'variance': 'LOW - Low volatility; frequent; pacing reliable'
                },
                'edge_percentage': 3.0,
                'risk_level': 'LOW',
                'stake_recommendation': '3-5% bankroll'
            }

        return None

    def _analyze_hockey_period(
        self,
        period: str,
        total_score: int,
        score_diff: int
    ) -> Optional[Dict]:
        """
        Analyze NHL period-specific opportunities

        Strategy (from Live_Betting_Strategies.md):
        - 1st period under hits 64-67% (2022-23, ROI 10-27%)
        - Period variance creates betting edges
        - 1st period typically higher scoring
        """
        if period in ['1', '1P', 'first']:
            return {
                'type': 'period_specific',
                'strategy': 'Period-Specific Betting (Pace Adjustments)',
                'trigger': '1st Period in progress',
                'confidence_level': 'MEDIUM',
                'recommendation': {
                    'bet_type': 'period_total',
                    'side': 'under',
                    'period': '1P',
                    'line': 1.5,
                    'reasoning': '1st period under hits 64-67% with ROI 10-27%'
                },
                'historical_performance': {
                    'win_rate': 65.5,
                    'roi': 18.5,
                    'sample': '2022-23 NHL',
                    'variance': 'LOW - Low volatility per period; frequent'
                },
                'edge_percentage': 8.0,
                'risk_level': 'LOW',
                'stake_recommendation': '2-5% bankroll'
            }

        return None

    def _analyze_period_end_opportunity(
        self,
        sport: str,
        period: str,
        score_diff: int
    ) -> Optional[Dict]:
        """
        Analyze opportunities at period end (last minute)

        - Late period chaos
        - Fouling situations (NBA)
        - Empty net opportunities (NHL)
        """
        if sport == 'NHL' and abs(score_diff) >= 2:
            return {
                'type': 'period_end',
                'strategy': 'Late-Game Scenarios (Empty Net and Lead Protection)',
                'trigger': 'Last minute of period with 2+ goal lead',
                'confidence_level': 'MEDIUM',
                'recommendation': {
                    'bet_type': 'next_goal',
                    'side': 'yes' if score_diff > 2 else 'no',
                    'reasoning': 'Empty net situations create high-percentage opportunities'
                },
                'historical_performance': {
                    'win_rate': 50.0,
                    'sample': 'NHL empty-net scenarios',
                    'variance': 'HIGH - Extreme volatility in final minutes'
                },
                'edge_percentage': 5.0,
                'risk_level': 'HIGH',
                'stake_recommendation': '1-2% bankroll'
            }

        return None

    def get_period_history(self, game_id: str) -> List[Dict]:
        """Get full period history for a game"""
        return self.period_history.get(game_id, [])

    def clear_game_data(self, game_id: str):
        """Clear tracking data for a completed game"""
        if game_id in self.game_states:
            del self.game_states[game_id]
        if game_id in self.period_history:
            del self.period_history[game_id]
