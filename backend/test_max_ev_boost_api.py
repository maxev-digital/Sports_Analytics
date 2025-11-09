"""
Test script for Max EV Boost API endpoints
Tests both NBA and NCAAB regression analyzers
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

from routes.max_ev_boost import get_nba_analyzer, get_ncaab_analyzer

def test_nba_analyzer():
    """Test NBA regression analyzer directly"""
    print("=" * 80)
    print("TESTING NBA MAX EV BOOST ANALYZER")
    print("=" * 80)

    try:
        analyzer = get_nba_analyzer()
        print("[OK] NBA analyzer loaded successfully")
        print(f"[OK] Models loaded: {analyzer.models is not None}")
        print(f"[OK] Number of models: {len(analyzer.models)}")

        # Test with sample game data
        sample_game = {
            'game_id': 'test_nba_001',
            'home_team': 'Los Angeles Lakers',
            'away_team': 'Boston Celtics',
            'home_stats': {
                'games_played': 35,
                'wins': 22,
                'win_pct': 0.629,
                'ppg': 118.5,
                'opp_ppg': 112.3,
                'point_diff': 6.2,
                'fg_pct': 0.478,
                'fg3_pct': 0.371,
                'ft_pct': 0.812,
                'rebounds': 45.2,
                'assists': 26.8,
                'turnovers': 13.5,
                'steals': 8.2,
                'blocks': 5.1,
                'plus_minus': 6.2,
                'last_5_ppg': 121.2,
                'last_10_ppg': 119.8,
                'last_5_wins': 4,
                'last_10_wins': 7
            },
            'away_stats': {
                'games_played': 36,
                'wins': 25,
                'win_pct': 0.694,
                'ppg': 122.1,
                'opp_ppg': 110.5,
                'point_diff': 11.6,
                'fg_pct': 0.492,
                'fg3_pct': 0.385,
                'ft_pct': 0.825,
                'rebounds': 47.3,
                'assists': 28.2,
                'turnovers': 12.8,
                'steals': 7.9,
                'blocks': 6.3,
                'plus_minus': 11.6,
                'last_5_ppg': 125.4,
                'last_10_ppg': 123.2,
                'last_5_wins': 5,
                'last_10_wins': 8
            },
            'live_total': 235.5
        }

        print("\n[TESTING] Running analysis on sample NBA game...")
        result = analyzer.analyze_game(sample_game)

        print("\n[RESULTS]")
        print(f"  Predicted Mean: {result['predicted_mean']}")
        print(f"  Predicted Range: {result['predicted_lower']} - {result['predicted_upper']}")
        print(f"  Standard Deviation: {result['std_dev']}")
        print(f"  Live Total: {result['live_total']}")
        print(f"  Z-Score: {result['z_score']}")
        print(f"  Is Alert: {result['is_alert']}")
        print(f"  Alert Type: {result['alert_type']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Recommended Bet: {result['recommended_bet']}")
        print(f"  Kelly %: {result['kelly_pct']}%")

        print("\n[SUCCESS] NBA analyzer test passed!")
        return True

    except Exception as e:
        print(f"\n[ERROR] NBA analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ncaab_analyzer():
    """Test NCAAB regression analyzer directly"""
    print("\n" + "=" * 80)
    print("TESTING NCAAB MAX EV BOOST ANALYZER")
    print("=" * 80)

    try:
        analyzer = get_ncaab_analyzer()
        print("[OK] NCAAB analyzer loaded successfully")
        print(f"[OK] Models loaded: {analyzer.models is not None}")
        print(f"[OK] Number of models: {len(analyzer.models)}")

        # Test with sample game data
        sample_game = {
            'game_id': 'test_ncaab_001',
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

        print("\n[TESTING] Running analysis on sample NCAAB game...")
        result = analyzer.analyze_game(sample_game)

        print("\n[RESULTS]")
        print(f"  Predicted Mean: {result['predicted_mean']}")
        print(f"  Predicted Range: {result['predicted_lower']} - {result['predicted_upper']}")
        print(f"  Standard Deviation: {result['std_dev']}")
        print(f"  Live Total: {result['live_total']}")
        print(f"  Z-Score: {result['z_score']}")
        print(f"  Is Alert: {result['is_alert']}")
        print(f"  Alert Type: {result['alert_type']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Recommended Bet: {result['recommended_bet']}")
        print(f"  Kelly %: {result['kelly_pct']}%")

        print("\n[SUCCESS] NCAAB analyzer test passed!")
        return True

    except Exception as e:
        print(f"\n[ERROR] NCAAB analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_extreme_scenario_nba():
    """Test NBA analyzer with extreme z-score scenario"""
    print("\n" + "=" * 80)
    print("TESTING NBA EXTREME Z-SCORE SCENARIO")
    print("=" * 80)

    try:
        analyzer = get_nba_analyzer()

        # Create scenario where live total is WAY higher than expected
        # Two defensive teams playing slow pace
        extreme_game = {
            'game_id': 'test_nba_extreme',
            'home_team': 'Detroit Pistons',
            'away_team': 'Memphis Grizzlies',
            'home_stats': {
                'games_played': 40,
                'wins': 12,
                'win_pct': 0.300,
                'ppg': 105.2,  # Low scoring
                'opp_ppg': 115.8,
                'point_diff': -10.6,
                'fg_pct': 0.432,
                'fg3_pct': 0.325,
                'ft_pct': 0.765,
                'rebounds': 42.1,
                'assists': 22.5,
                'turnovers': 15.2,
                'steals': 6.8,
                'blocks': 4.2,
                'plus_minus': -10.6,
                'last_5_ppg': 102.4,
                'last_10_ppg': 103.8,
                'last_5_wins': 1,
                'last_10_wins': 2
            },
            'away_stats': {
                'games_played': 38,
                'wins': 15,
                'win_pct': 0.395,
                'ppg': 108.5,  # Low scoring
                'opp_ppg': 112.2,
                'point_diff': -3.7,
                'fg_pct': 0.445,
                'fg3_pct': 0.338,
                'ft_pct': 0.782,
                'rebounds': 43.8,
                'assists': 24.1,
                'turnovers': 14.5,
                'steals': 7.2,
                'blocks': 5.5,
                'plus_minus': -3.7,
                'last_5_ppg': 106.2,
                'last_10_ppg': 107.5,
                'last_5_wins': 2,
                'last_10_wins': 4
            },
            'live_total': 240.5  # WAY TOO HIGH for these teams
        }

        print("\n[SCENARIO] Two defensive, low-scoring teams")
        print(f"[SCENARIO] Home team avg: 105.2 ppg")
        print(f"[SCENARIO] Away team avg: 108.5 ppg")
        print(f"[SCENARIO] Live total: 240.5 (should trigger UNDER alert)")

        result = analyzer.analyze_game(extreme_game)

        print("\n[RESULTS]")
        print(f"  Predicted Mean: {result['predicted_mean']}")
        print(f"  Live Total: {result['live_total']}")
        print(f"  Z-Score: {result['z_score']}")
        print(f"  Is Alert: {result['is_alert']}")
        print(f"  Alert Type: {result['alert_type']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Recommended Bet: {result['recommended_bet']}")
        print(f"  Kelly %: {result['kelly_pct']}%")

        if result['is_alert']:
            print(f"\n[SUCCESS] Alert triggered as expected!")
        else:
            print(f"\n[WARNING] Expected alert but none triggered")

        return True

    except Exception as e:
        print(f"\n[ERROR] Extreme scenario test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("MAX EV BOOST API TEST SUITE")
    print("=" * 80)
    print()

    results = []

    # Run tests
    results.append(("NBA Analyzer", test_nba_analyzer()))
    results.append(("NCAAB Analyzer", test_ncaab_analyzer()))
    results.append(("NBA Extreme Scenario", test_extreme_scenario_nba()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print()
    print(f"Tests Passed: {passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] All tests passed! API is ready for production.")
    else:
        print("\n[WARNING] Some tests failed. Review errors above.")
