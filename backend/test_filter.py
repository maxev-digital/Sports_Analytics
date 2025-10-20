"""Quick test of the filtering with actual data"""
import asyncio
from game_tracker import GameTracker
from settings_database import SettingsDatabase
from main import filter_games_by_bookmakers, normalize_bookmaker_name

async def test():
    # Get games
    tracker = GameTracker()
    await tracker.update_games()
    games = tracker.get_all_games()

    print(f"Total games: {len(games)}")

    if not games:
        print("No games to filter!")
        return

    # Get settings
    db = SettingsDatabase()
    settings = db.get_settings('default')
    enabled = settings['enabled_bookmakers']

    print(f"Enabled bookmakers: {len(enabled)}")
    print(f"Sample enabled: {enabled[:3]}")

    # Test normalization
    if games[0].odds:
        first_odd = games[0].odds[0]
        print(f"\nFirst odds bookmaker: '{first_odd.bookmaker}'")
        print(f"Normalized: '{normalize_bookmaker_name(first_odd.bookmaker)}'")
        print(f"Is in enabled? {normalize_bookmaker_name(first_odd.bookmaker) in [normalize_bookmaker_name(bm) for bm in enabled]}")

    # Run filter
    filtered = filter_games_by_bookmakers(games, enabled)
    print(f"\nFiltered games: {len(filtered)}")

    if filtered:
        print(f"First filtered game has {len(filtered[0].odds)} odds")
    else:
        print("NO GAMES PASSED FILTER!")
        # Debug why
        print("\nDebug: Checking first game...")
        first_game = games[0]
        print(f"First game has {len(first_game.odds)} total odds")
        enabled_norm = {normalize_bookmaker_name(bm) for bm in enabled}
        matching_odds = []
        for odd in first_game.odds:
            odd_norm = normalize_bookmaker_name(odd.bookmaker)
            if odd_norm in enabled_norm:
                matching_odds.append(odd.bookmaker)
        print(f"Matching odds in first game: {len(matching_odds)}")
        print(f"Matches: {matching_odds}")

if __name__ == "__main__":
    asyncio.run(test())
