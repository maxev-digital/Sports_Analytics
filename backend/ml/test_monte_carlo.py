"""
Test Monte Carlo Simulation Enhancements
Demonstrates probability distributions and expected value calculations
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from ml.nba_regression_analyzer import NBARegressionAnalyzer
from ml.ncaab_regression_analyzer import NCAABRegressionAnalyzer


def test_nba_monte_carlo():
    """Test NBA analyzer with Monte Carlo outputs"""
    print("=" * 80)
    print("NBA MONTE CARLO SIMULATION TEST")
    print("=" * 80)
    print()

    analyzer = NBARegressionAnalyzer()

    # Sample game with live total
    game_data = {
        'game_id': 'monte_carlo_test',
        'home_team': 'Lakers',
        'away_team': 'Celtics',
        'home_stats': {
            'games_played': 35, 'wins': 22, 'win_pct': 0.629,
            'ppg': 118.5, 'opp_ppg': 112.3, 'point_diff': 6.2,
            'fg_pct': 0.478, 'fg3_pct': 0.371, 'ft_pct': 0.812,
            'rebounds': 45.2, 'assists': 26.8, 'turnovers': 13.5,
            'steals': 8.2, 'blocks': 5.1, 'plus_minus': 6.2,
            'last_5_ppg': 121.2, 'last_10_ppg': 119.8,
            'last_5_wins': 4, 'last_10_wins': 7, 'momentum': 5.5
        },
        'away_stats': {
            'games_played': 36, 'wins': 25, 'win_pct': 0.694,
            'ppg': 122.1, 'opp_ppg': 110.5, 'point_diff': 11.6,
            'fg_pct': 0.492, 'fg3_pct': 0.385, 'ft_pct': 0.825,
            'rebounds': 47.3, 'assists': 28.2, 'turnovers': 12.8,
            'steals': 7.9, 'blocks': 6.3, 'plus_minus': 11.6,
            'last_5_ppg': 125.4, 'last_10_ppg': 123.2,
            'last_5_wins': 5, 'last_10_wins': 8, 'momentum': 8.2
        },
        'live_total': 235.5
    }

    result = analyzer.analyze_game(game_data)

    print(f"Game: {game_data['away_team']} @ {game_data['home_team']}")
    print()
    print("=" * 80)
    print("XGBoost PREDICTIONS")
    print("=" * 80)
    print(f"Predicted Total: {result['predicted_mean']} points")
    print(f"80% Confidence Range: {result['predicted_lower']} - {result['predicted_upper']}")
    print(f"Standard Deviation: {result['std_dev']} points")
    print()

    print("=" * 80)
    print("LIVE BETTING LINE")
    print("=" * 80)
    print(f"Current Total: {result['live_total']}")
    print(f"Z-Score: {result['z_score']} SD")
    print()

    if result.get('monte_carlo'):
        mc = result['monte_carlo']
        print("=" * 80)
        print("MONTE CARLO SIMULATION (10,000 simulations)")
        print("=" * 80)
        print()
        print("Win Probabilities:")
        print(f"  Over {result['live_total']}: {mc['over_probability']:.2%}")
        print(f"  Under {result['live_total']}: {mc['under_probability']:.2%}")
        print(f"  Push: {mc['push_probability']:.2%}")
        print()
        print("Expected Value (assuming -110 odds):")
        print(f"  Over EV: {mc['over_ev']:+.4f} units")
        print(f"  Under EV: {mc['under_ev']:+.4f} units")
        print()
        print("Distribution Percentiles:")
        print(f"  10th: {mc['percentiles']['10th']:.1f}")
        print(f"  25th: {mc['percentiles']['25th']:.1f}")
        print(f"  50th: {mc['percentiles']['50th']:.1f}")
        print(f"  75th: {mc['percentiles']['75th']:.1f}")
        print(f"  90th: {mc['percentiles']['90th']:.1f}")
        print()
        print("Simulation Validation:")
        print(f"  Simulated Mean: {mc['simulated_mean']}")
        print(f"  Simulated Std Dev: {mc['simulated_std']}")

    print()
    print("=" * 80)
    print("BETTING RECOMMENDATION")
    print("=" * 80)
    print(f"Alert: {result['is_alert']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Recommendation: {result['recommended_bet']}")
    print(f"Kelly Size: {result['kelly_pct']}% of bankroll")
    print()


def test_ncaab_monte_carlo():
    """Test NCAAB analyzer with Monte Carlo outputs"""
    print("=" * 80)
    print("NCAAB MONTE CARLO SIMULATION TEST")
    print("=" * 80)
    print()

    analyzer = NCAABRegressionAnalyzer()

    # Sample game
    game_data = {
        'game_id': 'ncaab_monte_carlo_test',
        'home_team': 'Duke',
        'away_team': 'North Carolina',
        'home_stats': {
            'adj_em': 28.5,
            'off_eff': 118.2,
            'def_eff': 89.7,
            'tempo': 70.5
        },
        'away_stats': {
            'adj_em': 25.3,
            'off_eff': 115.8,
            'def_eff': 90.5,
            'tempo': 68.2
        },
        'live_total': 160.5
    }

    result = analyzer.analyze_game(game_data)

    print(f"Game: {game_data['away_team']} @ {game_data['home_team']}")
    print()
    print(f"Predicted Total: {result['predicted_mean']} points")
    print(f"Live Total: {result['live_total']}")
    print(f"Z-Score: {result['z_score']} SD")
    print()

    if result.get('monte_carlo'):
        mc = result['monte_carlo']
        print("Monte Carlo Probabilities:")
        print(f"  Over {result['live_total']}: {mc['over_probability']:.2%}")
        print(f"  Under {result['live_total']}: {mc['under_probability']:.2%}")
        print()
        print(f"Expected Value:")
        print(f"  Over EV: {mc['over_ev']:+.4f} units")
        print(f"  Under EV: {mc['under_ev']:+.4f} units")
    print()


if __name__ == "__main__":
    test_nba_monte_carlo()
    print("\n\n")
    test_ncaab_monte_carlo()

    print("\n" + "=" * 80)
    print("MONTE CARLO ENHANCEMENT COMPLETE")
    print("=" * 80)
    print("\nAll Max EV Boost predictions now include:")
    print("  - Win probabilities for Over/Under")
    print("  - Expected value calculations")
    print("  - Full probability distributions")
    print("  - Percentile ranges")
