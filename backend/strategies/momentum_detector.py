"""
Momentum Detection for Live Betting
Implements momentum-based betting strategies across multiple sports

Based on Live_Betting_Strategies.md:
- NHL: Live Corsi >60% over last 5 min; xG differential +0.5
- NFL/NCAAF: Turnovers; EPA >+2; comeback prob >40%
- NBA/NCAAB: 8-0 runs; momentum teams cover 57-63% ATS in 1Q
- MLB: Hot/cold streaks (wRC+ >150)
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)


class MomentumDetector:
    """
    Detect momentum shifts and generate betting opportunities
    """

    def __init__(self, window_size_minutes: int = 5):
        """
        Initialize momentum detector

        Args:
            window_size_minutes: Time window for momentum calculation (default: 5 minutes)
        """
        self.window_size_minutes = window_size_minutes
        self.game_events: Dict[str, deque] = {}  # Sliding window of events
        self.momentum_history: Dict[str, List[Dict]] = {}
        self.current_momentum: Dict[str, Dict] = {}

    def add_event(
        self,
        game_id: str,
        event_type: str,
        team: str,  # 'home' or 'away'
        value: float = 1.0,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Add a game event for momentum tracking

        Event types:
        - score (points, goals, runs)
        - shot (shots, shot attempts)
        - turnover (turnovers, giveaways)
        - possession (possession time)
        - penalty (penalties, fouls)
        - hit (hits, tackles)
        - save (saves, defensive stops)

        Args:
            game_id: Game identifier
            event_type: Type of event
            team: Team ('home' or 'away')
            value: Event value/weight
            timestamp: Event timestamp (defaults to now)
            metadata: Additional event data
        """
        if game_id not in self.game_events:
            self.game_events[game_id] = deque()

        event = {
            'type': event_type,
            'team': team,
            'value': value,
            'timestamp': timestamp or datetime.now(),
            'metadata': metadata or {}
        }

        self.game_events[game_id].append(event)

        # Trim old events (outside time window)
        self._trim_old_events(game_id)

    def calculate_momentum(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int
    ) -> Dict[str, Any]:
        """
        Calculate current momentum for a game

        Returns:
            Dict with momentum analysis and betting opportunities
        """
        if game_id not in self.game_events:
            return {
                'game_id': game_id,
                'sport': sport,
                'has_momentum_data': False,
                'message': 'No event data available'
            }

        # Get events in time window
        events = list(self.game_events[game_id])

        if not events:
            return {
                'game_id': game_id,
                'sport': sport,
                'has_momentum_data': False,
                'message': 'No recent events'
            }

        # Calculate momentum scores
        home_momentum, away_momentum = self._calculate_momentum_scores(events, sport)

        # Determine momentum shift
        momentum_diff = home_momentum - away_momentum
        momentum_team = 'home' if momentum_diff > 0 else 'away'
        momentum_strength = abs(momentum_diff)

        # Calculate run/streak information
        current_run = self._calculate_current_run(events)

        # Store current momentum
        momentum_data = {
            'game_id': game_id,
            'sport': sport,
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'home_momentum': round(home_momentum, 2),
            'away_momentum': round(away_momentum, 2),
            'momentum_differential': round(momentum_diff, 2),
            'momentum_team': momentum_team,
            'momentum_strength': round(momentum_strength, 2),
            'current_run': current_run,
            'event_count': len(events),
            'timestamp': datetime.now().isoformat()
        }

        self.current_momentum[game_id] = momentum_data

        # Track history
        if game_id not in self.momentum_history:
            self.momentum_history[game_id] = []
        self.momentum_history[game_id].append(momentum_data.copy())

        # Generate betting opportunities
        opportunities = self._generate_momentum_opportunities(
            sport, home_team, away_team, home_score, away_score,
            home_momentum, away_momentum, momentum_diff, current_run
        )

        momentum_data['opportunities'] = opportunities

        return momentum_data

    def _trim_old_events(self, game_id: str):
        """Remove events outside the time window"""
        if game_id not in self.game_events:
            return

        cutoff_time = datetime.now() - timedelta(minutes=self.window_size_minutes)
        events = self.game_events[game_id]

        # Remove old events from front of deque
        while events and events[0]['timestamp'] < cutoff_time:
            events.popleft()

    def _calculate_momentum_scores(
        self,
        events: List[Dict],
        sport: str
    ) -> Tuple[float, float]:
        """
        Calculate momentum scores for both teams

        Different sports weight events differently
        """
        home_score = 0.0
        away_score = 0.0

        # Sport-specific event weights
        weights = self._get_event_weights(sport)

        for event in events:
            event_type = event['type']
            team = event['team']
            value = event['value']

            # Get weight for this event type
            weight = weights.get(event_type, 1.0)

            # Add to team's momentum score
            if team == 'home':
                home_score += value * weight
            else:
                away_score += value * weight

        return home_score, away_score

    def _get_event_weights(self, sport: str) -> Dict[str, float]:
        """Get event weights for sport"""
        if sport == 'NHL':
            return {
                'goal': 10.0,
                'shot': 1.0,
                'hit': 0.5,
                'penalty': -2.0,
                'save': 0.3,
                'turnover': -1.5,
                'possession': 0.2
            }
        elif sport in ['NBA', 'NCAAB']:
            return {
                'score': 5.0,
                'shot_made': 2.0,
                'shot_missed': -0.5,
                'turnover': -2.0,
                'steal': 1.5,
                'rebound': 1.0,
                'assist': 1.2,
                'foul': -0.5
            }
        elif sport in ['NFL', 'NCAAF']:
            return {
                'touchdown': 15.0,
                'field_goal': 5.0,
                'first_down': 2.0,
                'turnover': -10.0,
                'sack': 3.0,
                'penalty': -1.5,
                'big_play': 5.0  # 20+ yards
            }
        elif sport == 'MLB':
            return {
                'run': 10.0,
                'hit': 2.0,
                'walk': 1.5,
                'strikeout': -1.0,
                'error': -3.0,
                'stolen_base': 2.0
            }
        else:
            # Default weights
            return {
                'score': 5.0,
                'positive_event': 1.0,
                'negative_event': -1.0
            }

    def _calculate_current_run(self, events: List[Dict]) -> Optional[Dict]:
        """
        Calculate current scoring run (e.g., 8-0 run in NBA)

        Returns run info if significant run detected
        """
        if not events:
            return None

        # Only look at recent scoring events
        scoring_events = [e for e in events if e['type'] in ['score', 'goal', 'run', 'touchdown', 'field_goal']]

        if not scoring_events:
            return None

        # Find consecutive scores by same team
        current_team = scoring_events[-1]['team']
        run_points = 0
        run_count = 0

        for event in reversed(scoring_events):
            if event['team'] != current_team:
                break
            run_points += event['value']
            run_count += 1

        # Determine if this is a significant run
        is_significant = False
        if run_points >= 8:  # Basketball: 8-0 run
            is_significant = True
        elif run_count >= 3:  # Any sport: 3+ consecutive scores
            is_significant = True

        if is_significant:
            return {
                'team': current_team,
                'points': run_points,
                'count': run_count,
                'duration_minutes': (scoring_events[-1]['timestamp'] - scoring_events[-run_count]['timestamp']).total_seconds() / 60
            }

        return None

    def _generate_momentum_opportunities(
        self,
        sport: str,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        home_momentum: float,
        away_momentum: float,
        momentum_diff: float,
        current_run: Optional[Dict]
    ) -> List[Dict]:
        """
        Generate betting opportunities based on momentum

        Strategy varies by sport
        """
        opportunities = []
        momentum_team = home_team if momentum_diff > 0 else away_team
        trailing_team = away_team if home_score > away_score else home_team

        # Strong momentum shift (momentum differential > 10)
        if abs(momentum_diff) >= 10.0:
            if sport in ['NBA', 'NCAAB']:
                # NBA momentum strategy
                opportunities.append({
                    'type': 'momentum_shift',
                    'strategy': 'Run Exploitation (Momentum Swings)',
                    'trigger': f'Strong momentum: {abs(momentum_diff):.1f} differential',
                    'confidence_level': 'HIGH' if abs(momentum_diff) >= 15.0 else 'MEDIUM',
                    'recommendation': {
                        'bet_type': 'quarter_winner',
                        'side': momentum_team,
                        'reasoning': f'{momentum_team} has overwhelming momentum; teams with momentum cover 57-63% ATS'
                    },
                    'historical_performance': {
                        'win_rate': 60.0,
                        'ats_coverage': 60.0,
                        'sample': 'NBA momentum teams 1Q ATS',
                        'variance': 'HIGH - High volatility; frequent'
                    },
                    'edge_percentage': 5.0 + (abs(momentum_diff) * 0.2),
                    'risk_level': 'HIGH',
                    'stake_recommendation': '1-2% bankroll',
                    'momentum_details': {
                        'home_momentum': round(home_momentum, 2),
                        'away_momentum': round(away_momentum, 2),
                        'differential': round(momentum_diff, 2)
                    }
                })

            elif sport == 'NHL':
                # NHL momentum (Corsi/xG based)
                opportunities.append({
                    'type': 'momentum_shift',
                    'strategy': 'Momentum Shift Betting (Mid-Game Dominance)',
                    'trigger': f'High momentum: {abs(momentum_diff):.1f} (Corsi/xG equivalent)',
                    'confidence_level': 'MEDIUM',
                    'recommendation': {
                        'bet_type': 'next_goal',
                        'side': momentum_team,
                        'reasoning': f'{momentum_team} dominating possession and shots; high xG differential'
                    },
                    'historical_performance': {
                        'win_rate': 58.6,
                        'expected_vs_actual': '+0.4%',
                        'roi': 8.5,
                        'sample': 'NHL multivariate models 2016-2021',
                        'variance': 'MEDIUM - Moderate volatility'
                    },
                    'edge_percentage': 4.5,
                    'risk_level': 'MEDIUM',
                    'stake_recommendation': '1-3% bankroll'
                })

        # Significant run detected
        if current_run and current_run['points'] >= 8:
            if sport in ['NBA', 'NCAAB']:
                opportunities.append({
                    'type': 'scoring_run',
                    'strategy': 'Run Exploitation (Momentum Swings)',
                    'trigger': f'{current_run["points"]}-0 run by {current_run["team"]}',
                    'confidence_level': 'MEDIUM',
                    'recommendation': {
                        'bet_type': 'next_basket' if current_run['points'] < 12 else 'quarter_winner',
                        'side': 'opposite' if current_run['points'] >= 14 else current_run['team'],
                        'reasoning': f'{"Regression expected after " + str(current_run["points"]) + "-0 run" if current_run["points"] >= 14 else "Momentum continues; ride the run"}'
                    },
                    'historical_performance': {
                        'win_rate': 58.0 if current_run['points'] < 14 else 53.0,
                        'sample': 'NBA/NCAAB scoring runs',
                        'variance': 'HIGH - High volatility; frequent'
                    },
                    'edge_percentage': 3.0,
                    'risk_level': 'HIGH',
                    'stake_recommendation': '1-2% bankroll',
                    'run_details': current_run
                })

        # Comeback opportunity (trailing but gaining momentum)
        score_diff = home_score - away_score
        if abs(score_diff) >= 7 and momentum_team == trailing_team:
            if sport in ['NFL', 'NCAAF']:
                opportunities.append({
                    'type': 'comeback_momentum',
                    'strategy': 'Momentum After Turnovers (Mid-Game Shifts)',
                    'trigger': f'{trailing_team} trailing but gaining momentum',
                    'confidence_level': 'MEDIUM',
                    'recommendation': {
                        'bet_type': 'moneyline',
                        'side': trailing_team,
                        'reasoning': f'{trailing_team} has momentum shift; underdogs with momentum undervalued'
                    },
                    'historical_performance': {
                        'win_rate': 40.0,  # Actual comeback rate
                        'value_rate': 55.0,  # Betting value
                        'turnover_impact': '+2.0 EPA',
                        'sample': 'NFL/NCAAF comeback scenarios',
                        'variance': 'HIGH - High volatility; variable edge'
                    },
                    'edge_percentage': 4.0,
                    'risk_level': 'HIGH',
                    'stake_recommendation': '1-3% bankroll',
                    'score_differential': score_diff
                })

        return opportunities

    def get_momentum_history(self, game_id: str) -> List[Dict]:
        """Get momentum history for a game"""
        return self.momentum_history.get(game_id, [])

    def get_current_momentum(self, game_id: str) -> Optional[Dict]:
        """Get current momentum state"""
        return self.current_momentum.get(game_id)

    def clear_game_data(self, game_id: str):
        """Clear tracking data for a completed game"""
        if game_id in self.game_events:
            del self.game_events[game_id]
        if game_id in self.momentum_history:
            del self.momentum_history[game_id]
        if game_id in self.current_momentum:
            del self.current_momentum[game_id]
