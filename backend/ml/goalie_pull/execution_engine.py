"""
Execution Engine - Real-time goalie pull timing alpha system

Monitors live NHL games and generates alerts when:
1. Pull propensity ≥ threshold
2. Offered odds ≥ fair price + cushion
3. Expected value ≥ minimum EV

This is the production system that generates betting signals.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
import json

from propensity_model import PullPropensityModel
from goals_probability import GoalsProbabilityModel
from database_schema import GoaliePullDB


class GoaliePullExecutionEngine:
    """Real-time execution engine for goalie pull timing alpha"""

    def __init__(self, config: Dict = None):
        self.db = GoaliePullDB()
        self.propensity_model = PullPropensityModel()
        self.goals_model = GoalsProbabilityModel()

        # Load trained propensity model
        try:
            self.propensity_model.load_model()
            print("[OK] Propensity model loaded")
        except FileNotFoundError:
            print("[WARNING] Propensity model not found. Train first.")

        # Configuration
        self.config = config or self.get_default_config()

        # Active games being monitored
        self.active_games = {}

        # Alerts generated (to avoid duplicates)
        self.alerts_sent = set()

    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            # Propensity thresholds by coach type
            'propensity_threshold_aggressive': 0.35,  # 35% for aggressive coaches
            'propensity_threshold_moderate': 0.45,  # 45% for moderate coaches
            'propensity_threshold_conservative': 0.60,  # 60% for conservative coaches

            # Pricing requirements
            'cushion_decimal': 0.12,  # 12 cents cushion
            'min_ev_pct': 2.0,  # Minimum 2% EV

            # Bet sizing
            'kelly_fraction': 0.25,  # Quarter Kelly
            'max_bet_pct_bankroll': 0.02,  # Max 2% of bankroll

            # Market conditions
            'max_quote_age_seconds': 3.0,  # Reject quotes older than 3s
            'min_book_limit': 100,  # Minimum $100 limit

            # Time windows
            'min_time_remaining': 60,  # Start monitoring at 5:00
            'max_time_remaining': 300,  # Stop monitoring at 1:00

            # Execution
            'scan_interval_seconds': 5,  # Check every 5 seconds
        }

    def get_coach_threshold(self, coach_id: str) -> float:
        """Get propensity threshold for coach"""
        if not coach_id:
            return self.config['propensity_threshold_moderate']

        coach_profile = self.propensity_model.coach_profiles.get(coach_id)

        if not coach_profile:
            return self.config['propensity_threshold_moderate']

        aggressive_rating = coach_profile.get('aggressive_rating', 5)

        if aggressive_rating >= 7:
            return self.config['propensity_threshold_aggressive']
        elif aggressive_rating <= 3:
            return self.config['propensity_threshold_conservative']
        else:
            return self.config['propensity_threshold_moderate']

    def evaluate_game_state(
        self,
        game_state: Dict,
        offered_odds: Optional[int] = None
    ) -> Dict:
        """
        Evaluate current game state for betting opportunity

        Args:
            game_state: Current game state dict
            offered_odds: Current offered odds (American, e.g., +160)

        Returns:
            Dict with evaluation results
        """
        # Extract key info
        time_remaining = game_state['time_remaining_seconds']
        coach_id = game_state.get('coach_id')

        # Check if in monitoring window
        if time_remaining < self.config['min_time_remaining'] or time_remaining > self.config['max_time_remaining']:
            return {
                'alert': False,
                'reason': 'Outside time window'
            }

        # Step 1: Calculate pull propensity
        pull_propensity = self.propensity_model.predict(game_state)

        # Step 2: Check against coach-specific threshold
        threshold = self.get_coach_threshold(coach_id)

        if pull_propensity < threshold:
            return {
                'alert': False,
                'reason': f'Propensity {pull_propensity:.1%} < threshold {threshold:.1%}',
                'pull_propensity': pull_propensity,
                'threshold': threshold
            }

        # Step 3: Calculate goals probability
        trailing_team_strength = game_state.get('trailing_team_strength', 1.0)
        leading_team_strength = game_state.get('leading_team_strength', 1.0)

        p_goal = self.goals_model.calculate_probability_fast(
            time_remaining_seconds=time_remaining,
            pull_propensity=pull_propensity,
            trailing_team_strength=trailing_team_strength,
            leading_team_strength=leading_team_strength
        )

        # Step 4: Calculate fair price
        fair_price = self.goals_model.calculate_fair_price(
            p_goal=p_goal,
            cushion_decimal=self.config['cushion_decimal']
        )

        # Step 5: Evaluate offered odds (if provided)
        if offered_odds:
            bet_eval = self.goals_model.evaluate_bet(offered_odds, fair_price)

            if not bet_eval['take_bet']:
                return {
                    'alert': False,
                    'reason': f'Odds {offered_odds} do not meet requirements',
                    'pull_propensity': pull_propensity,
                    'p_goal': p_goal,
                    'fair_price': fair_price,
                    'bet_eval': bet_eval
                }

            # Calculate bet size
            bankroll = game_state.get('bankroll', 10000)  # Default $10k
            bet_size = self.calculate_bet_size(
                p_goal=p_goal,
                offered_odds=offered_odds,
                bankroll=bankroll
            )

            return {
                'alert': True,
                'reason': 'TAKE BET',
                'pull_propensity': pull_propensity,
                'threshold': threshold,
                'p_goal': p_goal,
                'fair_price': fair_price,
                'bet_eval': bet_eval,
                'bet_size': bet_size,
                'recommendation': f"BET ${bet_size:.0f} on OVER 0.5 goals at {offered_odds}"
            }

        else:
            # No odds provided, just return analysis
            return {
                'alert': True,
                'reason': 'Alert conditions met - awaiting odds',
                'pull_propensity': pull_propensity,
                'threshold': threshold,
                'p_goal': p_goal,
                'fair_price': fair_price,
                'recommendation': f"Look for odds better than {fair_price['min_acceptable_american']}"
            }

    def calculate_bet_size(
        self,
        p_goal: float,
        offered_odds: int,
        bankroll: float
    ) -> float:
        """
        Calculate bet size using Kelly Criterion

        Args:
            p_goal: Probability of goal
            offered_odds: American odds
            bankroll: Current bankroll

        Returns:
            Bet size in dollars
        """
        # Convert odds to decimal
        if offered_odds >= 100:
            b = offered_odds / 100
        else:
            b = -100 / offered_odds

        # Kelly fraction
        f_kelly = (p_goal * (b + 1) - 1) / b

        # Apply fraction (quarter Kelly)
        f_actual = f_kelly * self.config['kelly_fraction']

        # Calculate bet size
        bet_size = f_actual * bankroll

        # Apply caps
        max_bet = self.config['max_bet_pct_bankroll'] * bankroll
        bet_size = min(bet_size, max_bet)
        bet_size = max(bet_size, 0)  # No negative bets

        return bet_size

    def generate_alert(
        self,
        game_id: str,
        game_state: Dict,
        evaluation: Dict
    ) -> Dict:
        """
        Generate formatted alert

        Args:
            game_id: NHL game ID
            game_state: Game state dict
            evaluation: Evaluation results

        Returns:
            Alert dict ready for logging/sending
        """
        alert = {
            'alert_timestamp': datetime.now().isoformat(),
            'game_id': game_id,
            'home_team': game_state.get('home_team'),
            'away_team': game_state.get('away_team'),
            'trailing_team': game_state.get('trailing_team'),
            'time_remaining': f"{game_state['time_remaining_seconds'] // 60}:{game_state['time_remaining_seconds'] % 60:02d}",
            'time_remaining_seconds': game_state['time_remaining_seconds'],
            'score_diff': game_state['score_differential'],
            'coach_id': game_state.get('coach_id'),

            # Model outputs
            'pull_propensity': evaluation['pull_propensity'],
            'p_at_least_1_goal': evaluation['p_goal'],
            'fair_price_decimal': evaluation['fair_price']['fair_decimal'],
            'fair_price_american': evaluation['fair_price']['fair_american'],
            'required_cushion': self.config['cushion_decimal'],

            # Bet details (if applicable)
            'bet_placed': False,  # Updated when bet is actually placed
        }

        if 'bet_eval' in evaluation:
            alert.update({
                'bookmaker': game_state.get('bookmaker', 'Unknown'),
                'offered_price_american': evaluation['bet_eval']['offered_american'],
                'offered_price_decimal': evaluation['bet_eval']['offered_decimal'],
                'cushion_captured': evaluation['bet_eval']['cushion_captured'],
                'ev_at_entry': evaluation['bet_eval']['ev_pct'],
                'bet_size': evaluation.get('bet_size', 0),
                'kelly_fraction': self.config['kelly_fraction'],
            })

        return alert

    def log_alert(self, alert: Dict) -> int:
        """Log alert to database"""
        alert_id = self.db.insert_alert(alert)
        print(f"[ALERT] #{alert_id} logged: {alert['trailing_team']} @ {alert['time_remaining']}")
        return alert_id

    def monitor_live_games(self, duration_seconds: int = 3600):
        """
        Monitor live NHL games (simulation for now)

        Args:
            duration_seconds: How long to monitor (default 1 hour)
        """
        print("=" * 80)
        print("GOALIE PULL EXECUTION ENGINE - LIVE MONITORING")
        print("=" * 80)
        print(f"Configuration:")
        print(f"  Propensity Thresholds: Aggressive={self.config['propensity_threshold_aggressive']:.0%}, " +
              f"Moderate={self.config['propensity_threshold_moderate']:.0%}, " +
              f"Conservative={self.config['propensity_threshold_conservative']:.0%}")
        print(f"  Cushion Required: {self.config['cushion_decimal']:.2f} decimal ({self.config['cushion_decimal']*100:.0f} cents)")
        print(f"  Min EV: {self.config['min_ev_pct']:.1f}%")
        print(f"  Kelly Fraction: {self.config['kelly_fraction']:.2f}")
        print(f"  Scan Interval: {self.config['scan_interval_seconds']}s")
        print("\n[INFO] Monitoring simulation (replace with real NHL API in production)")
        print("=" * 80)

        start_time = time.time()
        alerts_generated = 0

        # Simulation: Test scenarios
        # In production, this would fetch live games from NHL API
        test_scenarios = [
            {
                'game_id': '2024020100',
                'home_team': 'CAR',
                'away_team': 'NYR',
                'trailing_team': 'NYR',
                'time_remaining_seconds': 150,
                'score_differential': -1,
                'coach_id': 'PETER_LAVIOLETTE',
                'bankroll': 10000,
                'bookmaker': 'DraftKings',
                'offered_odds': +160
            },
            {
                'game_id': '2024020101',
                'home_team': 'FLA',
                'away_team': 'TBL',
                'trailing_team': 'TBL',
                'time_remaining_seconds': 135,
                'score_differential': -2,
                'coach_id': 'JON_COOPER',
                'bankroll': 10000,
                'bookmaker': 'FanDuel',
                'offered_odds': +140
            }
        ]

        for scenario in test_scenarios:
            print(f"\n[SCANNING] {scenario['game_id']}: {scenario['away_team']} @ {scenario['home_team']}")
            print(f"           Time: {scenario['time_remaining_seconds']}s, Down {abs(scenario['score_differential'])}")

            # Evaluate
            evaluation = self.evaluate_game_state(
                game_state=scenario,
                offered_odds=scenario['offered_odds']
            )

            if evaluation['alert']:
                print(f"  [ALERT] {evaluation['reason']}")
                print(f"          Propensity: {evaluation['pull_propensity']:.1%} (threshold: {evaluation['threshold']:.1%})")
                print(f"          P(goal): {evaluation['p_goal']:.1%}")
                print(f"          Fair Price: {evaluation['fair_price']['fair_american']}")

                if 'bet_eval' in evaluation:
                    print(f"          Offered: {scenario['offered_odds']} (EV: {evaluation['bet_eval']['ev_pct']:+.1f}%)")
                    print(f"          Bet Size: ${evaluation['bet_size']:.0f}")
                    print(f"          [ACTION] {evaluation['recommendation']}")

                    # Generate and log alert
                    alert = self.generate_alert(scenario['game_id'], scenario, evaluation)
                    alert_id = self.log_alert(alert)
                    alerts_generated += 1
            else:
                print(f"  [PASS] {evaluation['reason']}")

        print("\n" + "=" * 80)
        print(f"[COMPLETE] Monitoring simulation finished")
        print(f"           Alerts Generated: {alerts_generated}")
        print("=" * 80)

        return alerts_generated


if __name__ == "__main__":
    # Initialize engine
    engine = GoaliePullExecutionEngine()

    # Run monitoring simulation
    engine.monitor_live_games(duration_seconds=60)

    print("\n[OK] Execution engine test complete!")
