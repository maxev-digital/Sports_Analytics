"""
Real-Time Live Analytics Engine
Tracks momentum, latency, edge calculations, and strategy performance in real-time
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
import statistics

class LiveAnalyticsEngine:
    """
    Core analytics engine that tracks:
    - Game momentum and trends
    - API latency and data freshness
    - True odds probability vs market
    - Live edge calculations
    - Strategy performance metrics
    """

    def __init__(self):
        # Momentum tracking (last 20 data points per game)
        self.momentum_history: Dict[str, deque] = {}

        # Latency monitoring
        self.latency_history = deque(maxlen=100)
        self.last_update_times: Dict[str, datetime] = {}

        # Edge calculations
        self.edge_history: Dict[str, List[Dict]] = {}

        # True odds tracking
        self.true_odds_cache: Dict[str, Dict] = {}

        # Strategy performance
        self.strategy_metrics: Dict[str, Dict] = {
            'multi_sport_ensemble': {'hits': 0, 'misses': 0, 'avg_edge': 0.0},
            'live_betting': {'hits': 0, 'misses': 0, 'avg_edge': 0.0},
            'pace_based': {'hits': 0, 'misses': 0, 'avg_edge': 0.0},
            'fatigue': {'hits': 0, 'misses': 0, 'avg_edge': 0.0},
            'regression': {'hits': 0, 'misses': 0, 'avg_edge': 0.0},
            'moneyline': {'hits': 0, 'misses': 0, 'avg_edge': 0.0}
        }

        # Trend detection
        self.trend_indicators: Dict[str, Dict] = {}

    def track_latency(self, endpoint: str, latency_ms: float):
        """Track API call latency"""
        self.latency_history.append({
            'endpoint': endpoint,
            'latency_ms': latency_ms,
            'timestamp': datetime.now()
        })

    def get_average_latency(self) -> float:
        """Get average latency across all recent calls"""
        if not self.latency_history:
            return 0.0
        return statistics.mean([l['latency_ms'] for l in self.latency_history])

    def get_latency_by_endpoint(self) -> Dict[str, float]:
        """Get average latency grouped by endpoint"""
        endpoint_latencies = {}
        for entry in self.latency_history:
            endpoint = entry['endpoint']
            if endpoint not in endpoint_latencies:
                endpoint_latencies[endpoint] = []
            endpoint_latencies[endpoint].append(entry['latency_ms'])

        return {
            endpoint: statistics.mean(latencies)
            for endpoint, latencies in endpoint_latencies.items()
        }

    def update_momentum(self, game_id: str, metric: str, value: float):
        """
        Track momentum for a specific game metric
        Metrics: 'score_diff', 'pace', 'shooting_pct', 'turnovers', etc.
        """
        key = f"{game_id}_{metric}"
        if key not in self.momentum_history:
            self.momentum_history[key] = deque(maxlen=20)

        self.momentum_history[key].append({
            'value': value,
            'timestamp': datetime.now()
        })

    def calculate_momentum_trend(self, game_id: str, metric: str) -> Dict:
        """
        Calculate momentum trend (accelerating, decelerating, stable)
        Returns direction, strength, and recent change
        """
        key = f"{game_id}_{metric}"
        if key not in self.momentum_history or len(self.momentum_history[key]) < 5:
            return {'direction': 'neutral', 'strength': 0.0, 'change': 0.0}

        data_points = list(self.momentum_history[key])
        values = [d['value'] for d in data_points]

        # Calculate trend using recent vs earlier averages
        recent_avg = statistics.mean(values[-5:])
        earlier_avg = statistics.mean(values[:5]) if len(values) >= 10 else statistics.mean(values[:-5])

        change = recent_avg - earlier_avg
        change_pct = (change / earlier_avg * 100) if earlier_avg != 0 else 0.0

        # Determine direction and strength
        if abs(change_pct) < 2:
            direction = 'neutral'
            strength = 0.0
        elif change_pct > 5:
            direction = 'strongly_positive'
            strength = min(change_pct / 10, 1.0)
        elif change_pct > 0:
            direction = 'positive'
            strength = change_pct / 5
        elif change_pct < -5:
            direction = 'strongly_negative'
            strength = min(abs(change_pct) / 10, 1.0)
        else:
            direction = 'negative'
            strength = abs(change_pct) / 5

        return {
            'direction': direction,
            'strength': strength,
            'change': change,
            'change_pct': change_pct,
            'recent_avg': recent_avg,
            'earlier_avg': earlier_avg
        }

    def calculate_true_odds(self, game_id: str, market_odds: Dict,
                           our_probability: float) -> Dict:
        """
        Calculate true odds vs market odds to find edge

        market_odds: {'over': -110, 'under': -110}
        our_probability: 0.55 (55% chance of over)
        """
        # Convert American odds to implied probability
        def american_to_prob(odds: int) -> float:
            if odds > 0:
                return 100 / (odds + 100)
            else:
                return abs(odds) / (abs(odds) + 100)

        # Convert probability to fair American odds
        def prob_to_american(prob: float) -> int:
            if prob >= 0.5:
                return int(-1 * (prob * 100) / (1 - prob))
            else:
                return int((100 * (1 - prob)) / prob)

        market_over_prob = american_to_prob(market_odds.get('over', -110))
        market_under_prob = american_to_prob(market_odds.get('under', -110))

        # Calculate our fair odds
        our_over_prob = our_probability
        our_under_prob = 1 - our_probability

        our_fair_over = prob_to_american(our_over_prob)
        our_fair_under = prob_to_american(our_under_prob)

        # Calculate edge
        over_edge = our_over_prob - market_over_prob
        under_edge = our_under_prob - market_under_prob

        # Determine best play
        best_play = None
        best_edge = 0.0

        if over_edge > 0.03:  # 3% edge threshold
            best_play = 'OVER'
            best_edge = over_edge
        elif under_edge > 0.03:
            best_play = 'UNDER'
            best_edge = under_edge

        result = {
            'game_id': game_id,
            'market_odds': market_odds,
            'market_over_prob': round(market_over_prob, 4),
            'market_under_prob': round(market_under_prob, 4),
            'our_over_prob': round(our_over_prob, 4),
            'our_under_prob': round(our_under_prob, 4),
            'our_fair_over': our_fair_over,
            'our_fair_under': our_fair_under,
            'over_edge': round(over_edge, 4),
            'under_edge': round(under_edge, 4),
            'best_play': best_play,
            'best_edge': round(best_edge, 4),
            'edge_pct': round(best_edge * 100, 2),
            'timestamp': datetime.now().isoformat()
        }

        # Cache the result
        self.true_odds_cache[game_id] = result

        # Track edge history
        if game_id not in self.edge_history:
            self.edge_history[game_id] = []
        self.edge_history[game_id].append(result)

        # Keep only last 50 edge calculations per game
        if len(self.edge_history[game_id]) > 50:
            self.edge_history[game_id] = self.edge_history[game_id][-50:]

        return result

    def get_edge_movement(self, game_id: str) -> Optional[Dict]:
        """
        Track how edge has moved over time
        Indicates if line is moving in our favor or against us
        """
        if game_id not in self.edge_history or len(self.edge_history[game_id]) < 2:
            return None

        history = self.edge_history[game_id]
        latest = history[-1]
        previous = history[-2]

        edge_change = latest['best_edge'] - previous['best_edge']

        return {
            'game_id': game_id,
            'current_edge': latest['best_edge'],
            'previous_edge': previous['best_edge'],
            'edge_change': round(edge_change, 4),
            'direction': 'improving' if edge_change > 0 else 'declining',
            'best_play': latest['best_play'],
            'status': 'getting_better' if edge_change > 0.01 else 'getting_worse' if edge_change < -0.01 else 'stable'
        }

    def update_data_freshness(self, source: str):
        """Track when data sources were last updated"""
        self.last_update_times[source] = datetime.now()

    def get_data_freshness(self) -> Dict[str, float]:
        """Get seconds since last update for each data source"""
        now = datetime.now()
        return {
            source: (now - last_time).total_seconds()
            for source, last_time in self.last_update_times.items()
        }

    def detect_trend(self, game_id: str, game_data: Dict) -> Dict:
        """
        Detect betting trends:
        - Line movement patterns
        - Public betting percentage shifts
        - Sharp money indicators
        - Reverse line movement
        """
        trends = {
            'game_id': game_id,
            'line_movement': self._detect_line_movement(game_id, game_data),
            'momentum_shift': self._detect_momentum_shift(game_id),
            'sharp_action': self._detect_sharp_action(game_id, game_data),
            'timestamp': datetime.now().isoformat()
        }

        self.trend_indicators[game_id] = trends
        return trends

    def _detect_line_movement(self, game_id: str, game_data: Dict) -> Dict:
        """Detect significant line movement"""
        if game_id not in self.edge_history or len(self.edge_history[game_id]) < 5:
            return {'detected': False, 'type': 'insufficient_data'}

        history = self.edge_history[game_id][-5:]

        # Check if market odds have moved consistently in one direction
        over_odds = [h['market_odds'].get('over', 0) for h in history]

        if len(set(over_odds)) > 1:
            movement = over_odds[-1] - over_odds[0]
            if abs(movement) >= 5:  # 5 points of movement
                return {
                    'detected': True,
                    'type': 'significant_movement',
                    'direction': 'toward_over' if movement > 0 else 'toward_under',
                    'points_moved': movement
                }

        return {'detected': False, 'type': 'stable'}

    def _detect_momentum_shift(self, game_id: str) -> Dict:
        """Detect game momentum shifts"""
        score_trend = self.calculate_momentum_trend(game_id, 'score_diff')
        pace_trend = self.calculate_momentum_trend(game_id, 'pace')

        if score_trend['direction'] in ['strongly_positive', 'strongly_negative']:
            return {
                'detected': True,
                'type': 'momentum_shift',
                'score_direction': score_trend['direction'],
                'pace_direction': pace_trend.get('direction', 'neutral'),
                'strength': score_trend['strength']
            }

        return {'detected': False}

    def _detect_sharp_action(self, game_id: str, game_data: Dict) -> Dict:
        """
        Detect sharp money (reverse line movement)
        Line moves opposite to public betting percentage
        """
        # This would need public betting percentage data
        # For now, detect based on line movement vs edge
        if game_id in self.true_odds_cache:
            true_odds = self.true_odds_cache[game_id]
            edge_movement = self.get_edge_movement(game_id)

            if edge_movement and edge_movement['status'] == 'getting_worse':
                return {
                    'detected': True,
                    'type': 'possible_sharp_action',
                    'line_moving_against_value': True
                }

        return {'detected': False}

    def update_strategy_performance(self, strategy_name: str,
                                   won: bool, edge: float):
        """Update strategy performance metrics"""
        if strategy_name not in self.strategy_metrics:
            self.strategy_metrics[strategy_name] = {
                'hits': 0, 'misses': 0, 'avg_edge': 0.0
            }

        metrics = self.strategy_metrics[strategy_name]

        if won:
            metrics['hits'] += 1
        else:
            metrics['misses'] += 1

        # Update average edge
        total_bets = metrics['hits'] + metrics['misses']
        metrics['avg_edge'] = (
            (metrics['avg_edge'] * (total_bets - 1) + edge) / total_bets
        )

    def get_strategy_performance(self) -> Dict:
        """Get performance metrics for all strategies"""
        performance = {}

        for strategy, metrics in self.strategy_metrics.items():
            total = metrics['hits'] + metrics['misses']
            win_rate = (metrics['hits'] / total * 100) if total > 0 else 0.0

            performance[strategy] = {
                'wins': metrics['hits'],
                'losses': metrics['misses'],
                'total_bets': total,
                'win_rate': round(win_rate, 2),
                'avg_edge': round(metrics['avg_edge'], 4),
                'roi': round(metrics['avg_edge'] * 100 * win_rate / 100, 2)
            }

        return performance

    def get_live_summary(self) -> Dict:
        """Get comprehensive live analytics summary"""
        return {
            'system_performance': {
                'avg_latency_ms': round(self.get_average_latency(), 2),
                'latency_by_endpoint': {
                    k: round(v, 2)
                    for k, v in self.get_latency_by_endpoint().items()
                },
                'data_freshness': self.get_data_freshness(),
                'games_tracked': len(self.momentum_history),
                'active_edges': len([
                    g for g, odds in self.true_odds_cache.items()
                    if odds.get('best_edge', 0) > 0.03
                ])
            },
            'strategy_performance': self.get_strategy_performance(),
            'active_trends': len([
                t for t in self.trend_indicators.values()
                if t.get('line_movement', {}).get('detected', False) or
                   t.get('momentum_shift', {}).get('detected', False)
            ]),
            'timestamp': datetime.now().isoformat()
        }

# Global instance
analytics_engine = LiveAnalyticsEngine()
