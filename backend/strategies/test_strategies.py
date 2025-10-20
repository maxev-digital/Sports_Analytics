"""
Test script for Phase 1 betting strategies
Verifies all modules are working correctly
"""

import sys
from datetime import datetime, timedelta

# Import strategy modules
from halftime_tracker import HalftimeTracker
from fatigue_detector import FatigueDetector
from weather_integration import WeatherIntegration
from momentum_detector import MomentumDetector


def test_halftime_tracker():
    """Test halftime/period tracking"""
    print("\n=== Testing Halftime Tracker ===")

    tracker = HalftimeTracker()

    # Simulate NBA game
    analysis = tracker.update_game_state(
        game_id="LAL_BOS_TEST",
        sport="NBA",
        period="2Q",
        time_remaining="2:30",
        home_score=52,
        away_score=48,
        home_team="Lakers",
        away_team="Celtics"
    )

    print(f"[OK] Game ID: {analysis['game_id']}")
    print(f"[OK] Period: {analysis['period']}")
    print(f"[OK] Score differential: {analysis['score_diff']}")
    print(f"[OK] Opportunities found: {len(analysis['opportunities'])}")

    if analysis['opportunities']:
        opp = analysis['opportunities'][0]
        print(f"  - Type: {opp['type']}")
        print(f"  - Strategy: {opp['strategy']}")
        print(f"  - Confidence: {opp['confidence_level']}")

    return True


def test_fatigue_detector():
    """Test fatigue detection"""
    print("\n=== Testing Fatigue Detector ===")

    detector = FatigueDetector()

    # Set up team schedules
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    three_days_ago = now - timedelta(days=3)

    # Lakers schedule (back-to-back)
    lakers_games = [
        {'date': yesterday, 'location': 'away', 'opponent': 'Warriors'},
        {'date': three_days_ago, 'location': 'home', 'opponent': 'Suns'}
    ]

    # Celtics schedule (rested)
    celtics_games = [
        {'date': three_days_ago, 'location': 'home', 'opponent': 'Heat'}
    ]

    detector.update_team_schedule("Lakers", "NBA", lakers_games)
    detector.update_team_schedule("Celtics", "NBA", celtics_games)

    # Analyze fatigue
    analysis = detector.analyze_fatigue(
        home_team="Lakers",
        away_team="Celtics",
        sport="NBA",
        game_date=now,
        home_miles_traveled=0,
        away_miles_traveled=2800,
        home_time_zones=0,
        away_time_zones=3
    )

    print(f"[OK] Home rest days: {analysis['home_rest_days']}")
    print(f"[OK] Away rest days: {analysis['away_rest_days']}")
    print(f"[OK] Home B2B: {analysis['home_back_to_back']}")
    print(f"[OK] Away B2B: {analysis['away_back_to_back']}")
    print(f"[OK] Fatigue differential: {analysis['fatigue_differential']}")
    print(f"[OK] Opportunities found: {len(analysis['opportunities'])}")

    if analysis['opportunities']:
        opp = analysis['opportunities'][0]
        print(f"  - Type: {opp['type']}")
        print(f"  - Confidence: {opp['confidence_level']}")
        print(f"  - Recommendation: {opp['recommendation']['bet_type']} - {opp['recommendation']['side']}")

    return True


def test_weather_integration():
    """Test weather integration"""
    print("\n=== Testing Weather Integration ===")

    weather = WeatherIntegration()

    # Update weather for NFL game
    weather.update_weather(
        game_id="GB_CHI_TEST",
        location="Lambeau Field",
        temperature=15,
        precipitation="snow",
        wind_speed=18,
        wind_direction="NW",
        humidity=85,
        conditions="heavy_snow"
    )

    # Analyze weather impact
    analysis = weather.analyze_weather_impact(
        game_id="GB_CHI_TEST",
        sport="NFL",
        home_team="Packers",
        away_team="Bears",
        current_total=44.5
    )

    print(f"[OK] Has weather data: {analysis['has_weather_data']}")
    print(f"[OK] Opportunities found: {len(analysis['opportunities'])}")

    if analysis['opportunities']:
        for opp in analysis['opportunities']:
            print(f"  - Type: {opp['type']}")
            print(f"  - Trigger: {opp['trigger']}")
            print(f"  - Recommendation: {opp['recommendation']['side']} (impact: {opp['recommendation']['estimated_impact']} pts)")

    return True


def test_momentum_detector():
    """Test momentum detection"""
    print("\n=== Testing Momentum Detector ===")

    detector = MomentumDetector(window_size_minutes=5)

    game_id = "BOS_MIA_TEST"

    # Simulate scoring run (8-0 run by home team)
    now = datetime.now()
    events = [
        ('score', 'home', 2.0, now - timedelta(minutes=3)),
        ('score', 'home', 2.0, now - timedelta(minutes=2, seconds=30)),
        ('turnover', 'away', 1.0, now - timedelta(minutes=2)),
        ('score', 'home', 2.0, now - timedelta(minutes=1, seconds=30)),
        ('score', 'home', 2.0, now - timedelta(seconds=45))
    ]

    for event_type, team, value, timestamp in events:
        detector.add_event(
            game_id=game_id,
            event_type=event_type,
            team=team,
            value=value,
            timestamp=timestamp
        )

    # Analyze momentum
    analysis = detector.calculate_momentum(
        game_id=game_id,
        sport="NBA",
        home_team="Celtics",
        away_team="Heat",
        home_score=48,
        away_score=42
    )

    print(f"[OK] Home momentum: {analysis['home_momentum']}")
    print(f"[OK] Away momentum: {analysis['away_momentum']}")
    print(f"[OK] Momentum differential: {analysis['momentum_differential']}")
    print(f"[OK] Momentum team: {analysis['momentum_team']}")
    print(f"[OK] Current run: {analysis['current_run']}")
    print(f"[OK] Opportunities found: {len(analysis['opportunities'])}")

    if analysis['opportunities']:
        opp = analysis['opportunities'][0]
        print(f"  - Type: {opp['type']}")
        print(f"  - Strategy: {opp['strategy']}")
        print(f"  - Confidence: {opp['confidence_level']}")

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("PHASE 1 BETTING STRATEGIES - TEST SUITE")
    print("=" * 60)

    tests = [
        ("Halftime Tracker", test_halftime_tracker),
        ("Fatigue Detector", test_fatigue_detector),
        ("Weather Integration", test_weather_integration),
        ("Momentum Detector", test_momentum_detector)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            print(f"\n[PASS] {test_name}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\n[FAIL] {test_name} - {str(e)}")

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
