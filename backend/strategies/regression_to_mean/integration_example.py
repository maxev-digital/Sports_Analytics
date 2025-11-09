"""
Integration Example: How to add ncaab_analytics to your game API response

This shows how to use the RegressionToMeanStrategy to populate
the ncaab_analytics field for the frontend Advanced tab.
"""

from strategy import RegressionToMeanStrategy


def add_analytics_to_game(game_data: dict, strategy: RegressionToMeanStrategy) -> dict:
    """
    Add ncaab_analytics to a game data dictionary

    Args:
        game_data: Your existing game data dict (with state, odds, etc.)
        strategy: Initialized RegressionToMeanStrategy instance

    Returns:
        game_data with ncaab_analytics field added (if opportunity exists)
    """

    # Only process NCAAB games
    if game_data.get('state', {}).get('sport_key') != 'basketball_ncaab':
        return game_data

    # Extract game features (you'll get these from your feature engineering)
    game_features = {
        'home_team': game_data['state']['home_team']['name'],
        'away_team': game_data['state']['away_team']['name'],
        'home_adj_em': 25.5,  # From KenPom or your stats DB
        'away_adj_em': 22.1,
        'home_off_eff': 118.2,
        'away_off_eff': 115.7,
        'home_def_eff': 92.7,
        'away_def_eff': 93.6,
        'home_tempo': 72.5,
        'away_tempo': 70.2,
        'avg_tempo': 71.35,
        'tempo_variance': 2.3,
        'competitive_balance': 0.48,
        # ... add all 40+ features your model needs
    }

    # Extract live totals from odds data
    live_totals = {}
    pregame_total = None

    for odds in game_data.get('odds', []):
        bookmaker = odds.get('bookmaker')
        total = odds.get('total')
        if total:
            live_totals[bookmaker] = total

        # Get pregame total (you might store this differently)
        if odds.get('opening_total'):
            pregame_total = odds['opening_total']

    if not live_totals:
        return game_data  # No totals available

    # Analyze game for regression opportunities
    alerts = strategy.analyze_game(game_features, live_totals, pregame_total)

    # If we have an alert (opportunity detected), format for frontend
    if alerts:
        # Use the first/best alert (you could pick best bookmaker)
        best_alert = alerts[0]

        # Convert to frontend format
        game_data['ncaab_analytics'] = strategy.format_for_frontend(
            best_alert,
            game_features
        )
    else:
        # No opportunity - don't add analytics field
        # (frontend won't show Advanced tab)
        game_data['ncaab_analytics'] = None

    return game_data


# Example usage in your API endpoint:
def example_api_integration():
    """
    Example of how to integrate in your /api/games endpoint
    """

    # Initialize strategy once at startup
    strategy = RegressionToMeanStrategy(
        model_path="backend/ml/models/ncaab_xgboost_totals.json",
        z_score_threshold=2.0,
        min_confidence=0.60,
        min_edge=3.0
    )

    # Your existing code to fetch games
    games = fetch_live_games()  # Your existing function

    # Process each game
    for game in games:
        # Add analytics if opportunity exists
        game = add_analytics_to_game(game, strategy)

    return games  # Return to frontend


# Quick test function
if __name__ == "__main__":
    # Test the formatter
    strategy = RegressionToMeanStrategy()

    # Mock alert data
    alert = {
        'direction': 'UNDER',
        'bet_total': 164.5,
        'z_score': 2.3,
        'edge_points': 8.2,
        'predicted_total': 156.3,
        'live_total': 164.5,
        'kelly_fraction': 0.032,
        'confidence': 0.78,
        'pregame_total': 158.5,
        'total_movement': 6.0,
        'std_dev': 10.1,
        'deviation_description': 'High deviation (2.0-2.5 std devs)'
    }

    game_features = {
        'home_tempo': 72.5,
        'away_tempo': 70.2,
        'home_off_eff': 118.2,
        'away_off_eff': 115.7,
        'home_def_eff': 92.7,
        'away_def_eff': 93.6,
    }

    # Convert to frontend format
    analytics = strategy.format_for_frontend(alert, game_features)

    # Print result
    import json
    print("Frontend Analytics Format:")
    print(json.dumps(analytics, indent=2))

    print("\nThis data will make the purple 'Advanced' tab appear!")
