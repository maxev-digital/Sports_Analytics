"""
Possession-by-Possession Monte Carlo Simulation for NBA Totals
Simulates remaining game based on current state and returns probability distributions

This module:
1. Takes current game state (quarter, time, score)
2. Calculates remaining possessions based on team pace
3. Simulates each possession individually with variance
4. Returns probability distribution for final total
5. Calculates over/under probabilities vs market line
6. Computes edge and Kelly Criterion bet sizing
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class GameState:
    """Current state of a live game"""
    quarter: int
    time_remaining: str  # Format: "4:32" (MM:SS)
    home_score: int
    away_score: int


@dataclass
class TeamStats:
    """Team statistics needed for simulation"""
    pace: float  # Possessions per 48 minutes
    off_rating: float  # Offensive rating (points per 100 possessions)
    def_rating: float  # Defensive rating (points allowed per 100 possessions)


class PossessionMonteCarloSimulator:
    """Simulates remaining possessions in an NBA game"""

    # NBA game constants
    MINUTES_PER_QUARTER = 12
    QUARTERS_IN_REGULATION = 4

    # Variance parameters (calibrated from historical data)
    PACE_VARIANCE = 0.10  # ±10% possession variance
    EFFICIENCY_VARIANCE = 0.08  # ±8% efficiency variance per possession

    def __init__(self):
        pass

    def parse_time_remaining(self, time_str: str) -> float:
        """
        Parse time string to minutes

        Args:
            time_str: "4:32" format (MM:SS)

        Returns:
            4.533 (minutes as float)
        """
        parts = time_str.split(":")
        minutes = int(parts[0])
        seconds = int(parts[1])
        return minutes + (seconds / 60.0)

    def calculate_remaining_time(self, quarter: int, time_remaining: str) -> float:
        """
        Calculate total remaining game time in minutes

        Args:
            quarter: Current quarter (1-4)
            time_remaining: Time left in current quarter ("4:32")

        Returns:
            Total minutes remaining in regulation
        """
        time_left_this_quarter = self.parse_time_remaining(time_remaining)
        quarters_remaining = max(0, self.QUARTERS_IN_REGULATION - quarter)

        total_time = time_left_this_quarter + (quarters_remaining * self.MINUTES_PER_QUARTER)
        return total_time

    def estimate_remaining_possessions(self, remaining_minutes: float,
                                      home_pace: float, away_pace: float) -> float:
        """
        Estimate number of possessions remaining in game

        Args:
            remaining_minutes: Minutes left in game
            home_pace: Home team pace (possessions per 48 min)
            away_pace: Away team pace (possessions per 48 min)

        Returns:
            Estimated possessions remaining for each team
        """
        # Average the two team paces
        avg_pace = (home_pace + away_pace) / 2.0

        # Possessions per minute
        possessions_per_minute = avg_pace / 48.0

        # Total possessions remaining (each team gets roughly equal)
        total_possessions = possessions_per_minute * remaining_minutes

        return total_possessions

    def simulate_possession(self, off_rating: float, def_rating: Optional[float] = None) -> float:
        """
        Simulate a single possession and return points scored

        Args:
            off_rating: Offensive rating (points per 100 possessions)
            def_rating: Defensive rating of opponent (optional adjustment)

        Returns:
            Points scored on this possession (usually 0, 1, 2, or 3)
        """
        # Adjust offensive rating based on defense if provided
        if def_rating is not None:
            # Adjust for opponent defense (league average is ~110)
            league_avg = 110.0
            adjusted_rating = off_rating * (league_avg / def_rating)
        else:
            adjusted_rating = off_rating

        # Expected points per possession
        expected_points = adjusted_rating / 100.0

        # Add variance (efficiency varies possession-to-possession)
        variance = self.EFFICIENCY_VARIANCE * expected_points
        actual_points = np.random.normal(expected_points, variance)

        # Clamp to realistic values (0 to 4 points, though 4 is rare)
        actual_points = max(0.0, min(4.0, actual_points))

        return actual_points

    def simulate_game_completion(self, game_state: GameState,
                                 home_stats: TeamStats,
                                 away_stats: TeamStats,
                                 n_simulations: int = 10000) -> List[float]:
        """
        Simulate remaining game and return array of final totals

        Args:
            game_state: Current game state (quarter, time, scores)
            home_stats: Home team statistics
            away_stats: Away team statistics
            n_simulations: Number of simulations to run

        Returns:
            Array of simulated final totals (home_score + away_score)
        """
        # Calculate remaining time
        remaining_minutes = self.calculate_remaining_time(
            game_state.quarter,
            game_state.time_remaining
        )

        # Estimate remaining possessions
        base_possessions = self.estimate_remaining_possessions(
            remaining_minutes,
            home_stats.pace,
            away_stats.pace
        )

        # Run simulations
        final_totals = []

        for _ in range(n_simulations):
            # Add variance to possession count
            possessions_variance = base_possessions * self.PACE_VARIANCE
            actual_possessions = np.random.normal(base_possessions, possessions_variance)
            actual_possessions = max(1, int(actual_possessions))  # At least 1 possession

            # Start with current scores
            home_score = game_state.home_score
            away_score = game_state.away_score

            # Simulate each remaining possession (alternating)
            for i in range(actual_possessions):
                if i % 2 == 0:
                    # Home possession
                    points = self.simulate_possession(
                        home_stats.off_rating,
                        away_stats.def_rating
                    )
                    home_score += points
                else:
                    # Away possession
                    points = self.simulate_possession(
                        away_stats.off_rating,
                        home_stats.def_rating
                    )
                    away_score += points

            final_total = home_score + away_score
            final_totals.append(final_total)

        return np.array(final_totals)

    def analyze_simulation(self, simulated_totals: np.ndarray,
                          market_total: float) -> Dict:
        """
        Analyze simulation results and calculate probabilities

        Args:
            simulated_totals: Array of simulated final totals
            market_total: Current betting market total

        Returns:
            Dictionary with probabilities, EV, percentiles, etc.
        """
        # Calculate win probabilities
        over_probability = np.mean(simulated_totals > market_total)
        under_probability = np.mean(simulated_totals < market_total)
        push_probability = np.mean(simulated_totals == market_total)

        # Calculate expected value (assuming -110 odds both sides)
        # American -110 = 1.909 decimal odds, returns $0.909 profit per $1 bet
        over_ev = (over_probability * 0.909) - (under_probability * 1.0)
        under_ev = (under_probability * 0.909) - (over_probability * 1.0)

        # Determine which side has edge
        if over_ev > 0 and over_ev > under_ev:
            recommended_bet = "OVER"
            edge = over_ev
            win_prob = over_probability
        elif under_ev > 0 and under_ev > over_ev:
            recommended_bet = "UNDER"
            edge = under_ev
            win_prob = under_probability
        else:
            recommended_bet = None
            edge = 0.0
            win_prob = 0.5

        # Calculate Kelly Criterion bet size
        kelly_pct = self._calculate_kelly(win_prob, edge) if edge > 0 else 0.0

        # Distribution percentiles
        percentiles = {
            '5th': float(np.percentile(simulated_totals, 5)),
            '10th': float(np.percentile(simulated_totals, 10)),
            '25th': float(np.percentile(simulated_totals, 25)),
            '50th': float(np.percentile(simulated_totals, 50)),
            '75th': float(np.percentile(simulated_totals, 75)),
            '90th': float(np.percentile(simulated_totals, 90)),
            '95th': float(np.percentile(simulated_totals, 95))
        }

        return {
            'over_probability': round(float(over_probability), 4),
            'under_probability': round(float(under_probability), 4),
            'push_probability': round(float(push_probability), 4),
            'over_ev': round(float(over_ev), 4),
            'under_ev': round(float(under_ev), 4),
            'recommended_bet': recommended_bet,
            'edge': round(float(edge), 4),
            'kelly_pct': round(float(kelly_pct), 2),
            'percentiles': percentiles,
            'mean': round(float(np.mean(simulated_totals)), 1),
            'median': round(float(np.median(simulated_totals)), 1),
            'std_dev': round(float(np.std(simulated_totals)), 2),
            'min': round(float(np.min(simulated_totals)), 1),
            'max': round(float(np.max(simulated_totals)), 1)
        }

    def _calculate_kelly(self, win_prob: float, edge: float) -> float:
        """
        Calculate Kelly Criterion bet size

        Args:
            win_prob: Probability of winning the bet
            edge: Expected value per dollar bet

        Returns:
            Recommended bet size as percentage of bankroll
        """
        if win_prob <= 0.5 or edge <= 0:
            return 0.0

        # Assuming -110 odds (1.909 decimal)
        decimal_odds = 1.909

        # Kelly formula: (p * odds - 1) / (odds - 1)
        kelly = (win_prob * decimal_odds - 1) / (decimal_odds - 1)

        # Use quarter Kelly for safety
        quarter_kelly = kelly / 4

        # Cap at 5% for safety
        return min(quarter_kelly * 100, 5.0)

    def run_monte_carlo(self, game_state: GameState,
                       home_stats: TeamStats,
                       away_stats: TeamStats,
                       market_total: float,
                       n_simulations: int = 10000) -> Dict:
        """
        Run full Monte Carlo analysis

        Args:
            game_state: Current game state
            home_stats: Home team statistics
            away_stats: Away team statistics
            market_total: Current betting market total
            n_simulations: Number of simulations to run

        Returns:
            Complete analysis dictionary
        """
        # Run simulations
        simulated_totals = self.simulate_game_completion(
            game_state,
            home_stats,
            away_stats,
            n_simulations
        )

        # Analyze results
        analysis = self.analyze_simulation(simulated_totals, market_total)

        # Add metadata
        remaining_time = self.calculate_remaining_time(
            game_state.quarter,
            game_state.time_remaining
        )

        remaining_possessions = self.estimate_remaining_possessions(
            remaining_time,
            home_stats.pace,
            away_stats.pace
        )

        analysis['metadata'] = {
            'current_total': game_state.home_score + game_state.away_score,
            'remaining_minutes': round(remaining_time, 2),
            'estimated_remaining_possessions': round(remaining_possessions, 1),
            'n_simulations': n_simulations
        }

        return analysis


# Example usage
if __name__ == "__main__":
    # Example: Lakers vs Celtics, Q3 4:32 remaining, score 82-78
    simulator = PossessionMonteCarloSimulator()

    game_state = GameState(
        quarter=3,
        time_remaining="4:32",
        home_score=82,
        away_score=78
    )

    home_stats = TeamStats(
        pace=100.5,
        off_rating=118.2,
        def_rating=110.5
    )

    away_stats = TeamStats(
        pace=98.3,
        off_rating=115.8,
        def_rating=108.9
    )

    market_total = 235.5

    print("=" * 80)
    print("POSSESSION-BASED MONTE CARLO SIMULATION")
    print("=" * 80)
    print()
    print(f"Current State: Q{game_state.quarter} {game_state.time_remaining}")
    print(f"Score: Home {game_state.home_score} - Away {game_state.away_score}")
    print(f"Current Total: {game_state.home_score + game_state.away_score}")
    print(f"Market Total: {market_total}")
    print()
    print("Running 10,000 simulations...")
    print()

    result = simulator.run_monte_carlo(
        game_state,
        home_stats,
        away_stats,
        market_total,
        n_simulations=10000
    )

    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    print(f"Simulated Mean Total: {result['mean']}")
    print(f"Simulated Median Total: {result['median']}")
    print(f"Standard Deviation: {result['std_dev']}")
    print()
    print("Win Probabilities:")
    print(f"  Over {market_total}: {result['over_probability']:.2%}")
    print(f"  Under {market_total}: {result['under_probability']:.2%}")
    print()
    print("Expected Value:")
    print(f"  Over EV: {result['over_ev']:+.4f} units")
    print(f"  Under EV: {result['under_ev']:+.4f} units")
    print()
    print(f"Recommended Bet: {result['recommended_bet']}")
    print(f"Edge: {result['edge']:+.4f} units")
    print(f"Kelly Bet Size: {result['kelly_pct']:.2f}% of bankroll")
    print()
    print("Distribution Percentiles:")
    for pct, value in result['percentiles'].items():
        print(f"  {pct}: {value:.1f}")
    print()
    print("Metadata:")
    print(f"  Current Total: {result['metadata']['current_total']}")
    print(f"  Remaining Minutes: {result['metadata']['remaining_minutes']}")
    print(f"  Estimated Remaining Possessions: {result['metadata']['estimated_remaining_possessions']}")
    print(f"  Simulations Run: {result['metadata']['n_simulations']:,}")
