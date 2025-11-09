"""
Goals Probability Model - Calculates P(≥1 goal before horn)

Uses regime-based simulation to estimate probability of at least 1 goal
being scored before time expires, given:
- Current game state
- Expected goalie pull timing (from propensity model)
- Team strength metrics

This is Layer B of the timing alpha system.
"""

import numpy as np
from typing import Dict, Optional
from database_schema import GoaliePullDB


class GoalsProbabilityModel:
    """Calculates probability of ≥1 goal before horn"""

    def __init__(self):
        self.db = GoaliePullDB()

        # League average goal rates per minute by regime
        # Based on NHL historical data
        self.lambda_5v5 = 0.10  # Goals per minute, 5v5 play
        self.lambda_6v5_offense = 0.30  # Goals per minute, extra attacker (before pull obvious)
        self.lambda_6v5_EN = 0.35  # Goals per minute, extra attacker (after pull obvious)
        self.lambda_EN_against = 0.80  # Empty net goals against per minute

        # Team strength adjustments will be loaded when available
        self.team_strengths = {}

    def simulate_goals(
        self,
        time_remaining_seconds: int,
        pull_propensity: float,
        trailing_team_strength: float = 1.0,
        leading_team_strength: float = 1.0,
        n_simulations: int = 10000
    ) -> float:
        """
        Monte Carlo simulation of goals before horn

        Args:
            time_remaining_seconds: Seconds left in period
            pull_propensity: P(pull in next 15s) from propensity model
            trailing_team_strength: Multiplier for trailing team offense (default 1.0 = league avg)
            leading_team_strength: Multiplier for leading team defense (default 1.0 = league avg)
            n_simulations: Number of Monte Carlo simulations

        Returns:
            Probability of ≥1 goal before horn (0.0 to 1.0)
        """
        goals_in_simulation = []

        for _ in range(n_simulations):
            total_goals = 0
            time_remaining = time_remaining_seconds

            # Sample when pull will happen (if at all)
            # Use propensity as probability of pull happening soon
            will_pull = np.random.random() < pull_propensity

            if will_pull:
                # Sample pull time from exponential distribution
                # Higher propensity = earlier pull
                mean_time_to_pull = 30 if pull_propensity > 0.5 else 60
                time_to_pull = min(np.random.exponential(mean_time_to_pull), time_remaining - 10)
                time_to_pull = max(time_to_pull, 5)  # At least 5s before horn
            else:
                time_to_pull = time_remaining + 10  # No pull

            # Simulate goals before pull
            time_before_pull = min(time_to_pull, time_remaining)
            if time_before_pull > 0:
                lambda_adjusted = self.lambda_5v5 * trailing_team_strength
                goals_before_pull = np.random.poisson(lambda_adjusted * time_before_pull / 60)
                total_goals += goals_before_pull

            # Simulate goals after pull (if pull happened)
            if will_pull and time_to_pull < time_remaining:
                time_after_pull = time_remaining - time_to_pull

                # Both teams can score with goalie pulled
                # Trailing team (extra attacker)
                lambda_offense = self.lambda_6v5_EN * trailing_team_strength
                goals_by_trailing = np.random.poisson(lambda_offense * time_after_pull / 60)

                # Leading team (empty net)
                lambda_en_against = self.lambda_EN_against * leading_team_strength
                goals_by_leading = np.random.poisson(lambda_en_against * time_after_pull / 60)

                total_goals += goals_by_trailing + goals_by_leading

            goals_in_simulation.append(total_goals)

        # Calculate P(≥1 goal)
        p_at_least_1 = np.mean([g >= 1 for g in goals_in_simulation])

        return p_at_least_1

    def calculate_probability_fast(
        self,
        time_remaining_seconds: int,
        pull_propensity: float,
        trailing_team_strength: float = 1.0,
        leading_team_strength: float = 1.0
    ) -> float:
        """
        Fast analytical approximation (no simulation)

        Uses Poisson probabilities for each regime

        Returns:
            Probability of ≥1 goal before horn
        """
        # Estimate time splits
        if pull_propensity > 0.5:
            time_to_pull = 30  # High propensity = pull soon
        elif pull_propensity > 0.3:
            time_to_pull = 60  # Medium propensity
        else:
            time_to_pull = time_remaining_seconds + 10  # Low propensity = no pull

        time_to_pull = min(time_to_pull, time_remaining_seconds)

        # Time before pull
        time_before_pull = min(time_to_pull, time_remaining_seconds)

        # Time after pull
        will_pull = pull_propensity > 0.3  # Threshold for "likely pull"
        if will_pull and time_to_pull < time_remaining_seconds:
            time_after_pull = time_remaining_seconds - time_to_pull
        else:
            time_after_pull = 0

        # Calculate expected goals in each regime
        # Regime 1: Before pull (5v5)
        lambda_before = self.lambda_5v5 * trailing_team_strength
        expected_goals_before = lambda_before * time_before_pull / 60

        # Regime 2: After pull (6v5 + EN)
        lambda_after_offense = self.lambda_6v5_EN * trailing_team_strength
        lambda_after_defense = self.lambda_EN_against * leading_team_strength
        expected_goals_after = (lambda_after_offense + lambda_after_defense) * time_after_pull / 60

        # Total expected goals
        total_expected_goals = expected_goals_before + expected_goals_after

        # P(≥1 goal) using Poisson
        # P(X ≥ 1) = 1 - P(X = 0) = 1 - e^(-λ)
        p_at_least_1 = 1 - np.exp(-total_expected_goals)

        return p_at_least_1

    def calculate_fair_price(
        self,
        p_goal: float,
        cushion_decimal: float = 0.12
    ) -> Dict:
        """
        Calculate fair betting price given probability

        Args:
            p_goal: Probability of ≥1 goal (0.0 to 1.0)
            cushion_decimal: Required cushion in decimal odds (default 0.12 = 12 cents)

        Returns:
            Dict with fair price, minimum acceptable price, etc.
        """
        # Fair decimal odds
        fair_decimal = 1 / p_goal if p_goal > 0 else 999.0

        # Minimum acceptable (with cushion)
        min_acceptable_decimal = fair_decimal + cushion_decimal

        # Convert to American odds
        def decimal_to_american(decimal):
            if decimal >= 2.0:
                return int((decimal - 1) * 100)
            else:
                return int(-100 / (decimal - 1))

        fair_american = decimal_to_american(fair_decimal)
        min_acceptable_american = decimal_to_american(min_acceptable_decimal)

        return {
            'p_goal': p_goal,
            'fair_decimal': round(fair_decimal, 2),
            'fair_american': fair_american,
            'min_acceptable_decimal': round(min_acceptable_decimal, 2),
            'min_acceptable_american': min_acceptable_american,
            'cushion_decimal': cushion_decimal
        }

    def evaluate_bet(
        self,
        offered_odds_american: int,
        fair_price: Dict
    ) -> Dict:
        """
        Evaluate if offered odds meet our requirements

        Args:
            offered_odds_american: Offered price (e.g., +160)
            fair_price: Dict from calculate_fair_price()

        Returns:
            Dict with bet decision, EV, etc.
        """
        # Convert offered odds to decimal
        if offered_odds_american >= 100:
            offered_decimal = 1 + offered_odds_american / 100
        else:
            offered_decimal = 1 - 100 / offered_odds_american

        # Calculate EV
        p_goal = fair_price['p_goal']
        ev = (p_goal * (offered_decimal - 1)) - ((1 - p_goal) * 1)
        ev_pct = ev * 100

        # Check if meets requirements
        meets_cushion = offered_decimal >= fair_price['min_acceptable_decimal']
        meets_ev = ev_pct >= 2.0  # Minimum 2% EV

        # Decision
        take_bet = meets_cushion and meets_ev

        # Cushion captured
        cushion_captured = offered_decimal - fair_price['fair_decimal']

        return {
            'take_bet': take_bet,
            'offered_decimal': round(offered_decimal, 2),
            'offered_american': offered_odds_american,
            'fair_decimal': fair_price['fair_decimal'],
            'fair_american': fair_price['fair_american'],
            'cushion_captured': round(cushion_captured, 2),
            'ev': round(ev, 4),
            'ev_pct': round(ev_pct, 1),
            'meets_cushion': meets_cushion,
            'meets_ev': meets_ev
        }


if __name__ == "__main__":
    print("=" * 80)
    print("GOALS PROBABILITY MODEL TEST")
    print("=" * 80)

    model = GoalsProbabilityModel()

    # Test scenario: Team down 1 with 2:30 remaining, high pull propensity
    test_scenario = {
        'time_remaining_seconds': 150,  # 2:30
        'pull_propensity': 0.48,  # 48% chance of pull in next 15s
        'trailing_team_strength': 1.05,  # Slightly above average
        'leading_team_strength': 0.95  # Slightly below average
    }

    print("\nTest Scenario:")
    print(f"  Time Remaining: {test_scenario['time_remaining_seconds']}s (2:30)")
    print(f"  Pull Propensity: {test_scenario['pull_propensity']:.1%}")
    print(f"  Trailing Team Strength: {test_scenario['trailing_team_strength']:.2f}x")
    print(f"  Leading Team Strength: {test_scenario['leading_team_strength']:.2f}x")

    # Calculate probability
    print("\n[CALCULATING] Running simulations...")
    p_goal_sim = model.simulate_goals(**test_scenario, n_simulations=10000)
    print(f"  Monte Carlo (10k sims): {p_goal_sim:.1%}")

    p_goal_fast = model.calculate_probability_fast(**test_scenario)
    print(f"  Fast approximation: {p_goal_fast:.1%}")

    # Calculate fair price
    print("\n[PRICING]")
    fair_price = model.calculate_fair_price(p_goal_fast, cushion_decimal=0.12)
    print(f"  Fair Price: {fair_price['fair_american']} ({fair_price['fair_decimal']} decimal)")
    print(f"  Min Acceptable (+ cushion): {fair_price['min_acceptable_american']} ({fair_price['min_acceptable_decimal']} decimal)")

    # Evaluate sample bets
    print("\n[BET EVALUATION]")
    test_odds = [+120, +140, +160, +180, +200]

    for odds in test_odds:
        result = model.evaluate_bet(odds, fair_price)
        decision = "[BET]" if result['take_bet'] else "[PASS]"
        print(f"  {decision} Offered +{odds}: EV={result['ev_pct']:+.1f}%, Cushion={result['cushion_captured']:+.2f}")

    print("\n" + "=" * 80)
    print("[OK] Goals probability model test complete!")
