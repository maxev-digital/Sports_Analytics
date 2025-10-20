"""Debug script to check bookmaker key mismatch"""
import asyncio
from game_tracker import GameTracker
from settings_database import SettingsDatabase

async def debug_bookmakers():
    """Check what bookmakers are in games vs settings"""
    # Initialize tracker
    tracker = GameTracker()
    await tracker.update_games()

    # Get all games
    games = tracker.get_all_games()
    print(f"\n{'='*60}")
    print(f"Total games fetched: {len(games)}")
    print(f"{'='*60}\n")

    if games:
        # Check first game's bookmakers
        first_game = games[0]
        print(f"First game: {first_game.state.away_team.name} @ {first_game.state.home_team.name}")
        print(f"Number of odds entries: {len(first_game.odds)}")
        print(f"\nBookmakers in first game odds:")
        for i, odd in enumerate(first_game.odds[:10]):  # Show first 10
            print(f"  {i+1}. {odd.bookmaker}")

        # Collect all unique bookmaker keys from games
        all_bookmakers = set()
        for game in games:
            for odd in game.odds:
                all_bookmakers.add(odd.bookmaker)

        print(f"\n{'='*60}")
        print(f"All unique bookmakers in games ({len(all_bookmakers)}):")
        print(f"{'='*60}")
        for bm in sorted(all_bookmakers):
            print(f"  - {bm}")

    # Get settings bookmakers
    print(f"\n{'='*60}")
    print(f"Bookmakers enabled in settings:")
    print(f"{'='*60}")

    db = SettingsDatabase()
    settings = db.get_settings('default')
    if settings:
        enabled = settings['enabled_bookmakers']
        print(f"Total enabled: {len(enabled)}")
        for bm in sorted(enabled)[:10]:  # Show first 10
            print(f"  - {bm}")

    # Check for matches
    if games and settings:
        enabled_set = set(settings['enabled_bookmakers'])
        game_set = all_bookmakers

        print(f"\n{'='*60}")
        print(f"Matching bookmakers: {len(enabled_set & game_set)}")
        print(f"{'='*60}")
        matches = enabled_set & game_set
        for bm in sorted(matches)[:10]:
            print(f"  - {bm}")

        print(f"\n{'='*60}")
        print(f"Enabled but not in games: {len(enabled_set - game_set)}")
        print(f"{'='*60}")
        missing = enabled_set - game_set
        for bm in sorted(missing)[:10]:
            print(f"  - {bm}")

        print(f"\n{'='*60}")
        print(f"In games but not enabled: {len(game_set - enabled_set)}")
        print(f"{'='*60}")
        extra = game_set - enabled_set
        for bm in sorted(extra)[:10]:
            print(f"  - {bm}")

if __name__ == "__main__":
    asyncio.run(debug_bookmakers())
