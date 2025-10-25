"""
Test script for Favorite Comeback Detector
"""

from favorite_comeback_detector import FavoriteComeb ackDetector

def test_favorite_trailing_q1():
    """Test case: Favorite trailing after Q1"""
    detector = FavoriteComeb ackDetector()

    result = detector.analyze_comeback_opportunity(
        game_id="TEST_001",
        sport="NBA",
        home_team="Lakers",
        away_team="Pistons",
        home_score=32,  # Lakers (favorite) trailing
        away_score=28,  # Pistons leading
        period="1Q",
        time_remaining="1:30",
        home_team_favorite=True,
        pregame_spread=8.5,
        current_spread=-2.5,
        home_season_stats={"ppg": 115.0, "fg_pct": 48.0},
        away_season_stats={"ppg": 105.0, "fg_pct": 44.0},
        quarter_stats={"favorite_fg_pct": 40.0, "underdog_fg_pct": 58.0}
    )

    print("\n[TEST 1] Favorite Trailing After Q1")
    print("=" * 60)
    print(f"Game: {result.get('favorite')} vs {result.get('underdog')}")
    print(f"Score Differential: {result.get('score_differential')}")
    print(f"Has Opportunity: {result.get('has_opportunity')}")

    if result.get('has_opportunity'):
        regression = result.get('regression_analysis', {})
        print(f"Regression Score: {regression.get('regression_score')}")
        print(f"Strong Regression: {regression.get('has_strong_regression')}")

        for opp in result.get('opportunities', []):
            print(f"\nStrategy: {opp.get('strategy')}")
            print(f"Confidence: {opp.get('confidence_level')}")
            print(f"Recommendation: {opp.get('recommendation', {}).get('reasoning')}")
            print(f"Historical Win Rate: {opp.get('historical_performance', {}).get('win_rate')}%")

    print("[PASS]" if result.get('has_opportunity') else "[INFO] No opportunity detected")


def test_favorite_trailing_halftime():
    """Test case: Favorite trailing at halftime"""
    detector = FavoriteComeb ackDetector()

    result = detector.analyze_comeback_opportunity(
        game_id="TEST_002",
        sport="NBA",
        home_team="Celtics",
        away_team="Hornets",
        home_score=52,
        away_score=58,  # Celtics (favorite) trailing by 6
        period="Half",
        time_remaining="0:00",
        home_team_favorite=True,
        pregame_spread=10.0,
        current_spread=-4.0,
        home_season_stats={"ppg": 118.0, "fg_pct": 49.0},
        away_season_stats={"ppg": 108.0, "fg_pct": 45.0},
        quarter_stats={"favorite_fg_pct": 42.0, "underdog_fg_pct": 54.0}
    )

    print("\n[TEST 2] Favorite Trailing at Halftime")
    print("=" * 60)
    print(f"Game: {result.get('favorite')} vs {result.get('underdog')}")
    print(f"Score Differential: {result.get('score_differential')}")
    print(f"Has Opportunity: {result.get('has_opportunity')}")

    if result.get('has_opportunity'):
        for opp in result.get('opportunities', []):
            print(f"\nConfidence: {opp.get('confidence_level')}")
            print(f"Edge: {opp.get('edge_percentage')}%")
            print(f"Historical: {opp.get('historical_performance', {}).get('ats_coverage')}")

    print("[PASS]" if result.get('has_opportunity') else "[INFO] No opportunity detected")


def test_favorite_leading():
    """Test case: Favorite leading (should NOT trigger)"""
    detector = FavoriteComeb ackDetector()

    result = detector.analyze_comeback_opportunity(
        game_id="TEST_003",
        sport="NBA",
        home_team="Warriors",
        away_team="Wizards",
        home_score=35,  # Warriors (favorite) leading
        away_score=28,
        period="1Q",
        time_remaining="1:00",
        home_team_favorite=True,
        pregame_spread=12.0,
        current_spread=7.0
    )

    print("\n[TEST 3] Favorite Leading (Should NOT Trigger)")
    print("=" * 60)
    print(f"Has Opportunity: {result.get('has_opportunity')}")
    print(f"Reason: {result.get('reason')}")
    print("[PASS]" if not result.get('has_opportunity') else "[FAIL]")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("FAVORITE COMEBACK DETECTOR TESTS")
    print("=" * 60)

    try:
        test_favorite_trailing_q1()
        test_favorite_trailing_halftime()
        test_favorite_leading()

        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
