"""
Test Script for BetUS Auto-Fill
Fetches a random live game from Odds API and creates a test alert for BetUS
"""

import requests
import random
import json
from datetime import datetime

# Configuration
ODDS_API_KEY = "YOUR_ODDS_API_KEY"  # Replace with your actual key
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# Test alert storage (simulates backend alerts)
test_alerts = {
    "arbitrage": {
        "alerts": [],
        "count": 0
    }
}

def fetch_live_games(sport='basketball_nba'):
    """Fetch live games from Odds API"""
    url = f"{ODDS_API_BASE}/sports/{sport}/odds/"

    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'us',
        'markets': 'h2h,spreads,totals',
        'oddsFormat': 'american',
        'bookmakers': 'betus,draftkings,fanduel'
    }

    print(f"🔍 Fetching live {sport} games from Odds API...")

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        games = response.json()

        print(f"✅ Found {len(games)} games")
        return games

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching games: {e}")
        return []

def create_test_opportunity(game):
    """Create a fake arbitrage opportunity from a real game"""

    if not game:
        print("❌ No game provided")
        return None

    # Extract game info
    home_team = game.get('home_team', 'Unknown')
    away_team = game.get('away_team', 'Unknown')
    commence_time = game.get('commence_time', datetime.now().isoformat())
    sport_key = game.get('sport_key', 'basketball_nba')
    game_id = game.get('id', 'test-game-' + str(random.randint(1000, 9999)))

    # Get bookmakers
    bookmakers = game.get('bookmakers', [])

    if len(bookmakers) < 2:
        print("❌ Not enough bookmakers for this game")
        return None

    # Find BetUS odds
    betus_book = next((b for b in bookmakers if b['key'] == 'betus'), None)
    other_book = next((b for b in bookmakers if b['key'] != 'betus'), bookmakers[0])

    if not betus_book:
        print("⚠️ BetUS not available, using first bookmaker as fake BetUS")
        betus_book = bookmakers[0]

    # Get totals market (Over/Under)
    betus_totals = next((m for m in betus_book.get('markets', []) if m['key'] == 'totals'), None)
    other_totals = next((m for m in other_book.get('markets', []) if m['key'] == 'totals'), None)

    if not betus_totals or not other_totals:
        print("❌ Totals market not available")
        return None

    # Get Over/Under outcomes
    betus_over = next((o for o in betus_totals['outcomes'] if o['name'] == 'Over'), None)
    other_under = next((o for o in other_totals['outcomes'] if o['name'] == 'Under'), None)

    if not betus_over or not other_under:
        print("❌ Over/Under outcomes not available")
        return None

    # Create fake arbitrage opportunity (BetUS Over vs Other Under)
    opportunity = {
        "id": f"test-{game_id}",
        "game_id": game_id,
        "sport": sport_key,
        "sport_key": sport_key,
        "home_team": home_team,
        "away_team": away_team,
        "commence_time": commence_time,
        "game": f"{away_team} @ {home_team}",

        # Market info
        "market_type": "totals",
        "market_key": "totals",

        # BetUS leg (Book 1)
        "book1": "betus",
        "book_a": "betus",
        "outcome1": "Over",
        "outcome": "Over",
        "point": betus_over.get('point', 225.5),
        "odds1": betus_over.get('price', -110),
        "odds": betus_over.get('price', -110),
        "stake_book1": 100,
        "stake_amount": 100,

        # Other book leg (Book 2)
        "book2": other_book['key'],
        "book_b": other_book['key'],
        "outcome2": "Under",
        "point2": other_under.get('point', 225.5),
        "odds2": other_under.get('price', -110),
        "stake_book2": 100,

        # Arbitrage stats (fake for testing)
        "profit_percentage": 2.5,
        "profit_percent": 2.5,
        "guaranteed_profit": 5.00,
        "total_stake": 200,

        # Timestamp
        "timestamp": datetime.now().isoformat(),
        "detected_at": datetime.now().isoformat()
    }

    print(f"\n✅ Created test opportunity:")
    print(f"   Game: {away_team} @ {home_team}")
    print(f"   Market: Totals")
    print(f"   BetUS: {opportunity['outcome']} {opportunity['point']} ({opportunity['odds']})")
    print(f"   {other_book['key'].upper()}: {opportunity['outcome2']} {opportunity['point2']} ({opportunity['odds2']})")
    print(f"   Profit: {opportunity['profit_percentage']}%")

    return opportunity

def save_test_alert(opportunity):
    """Save test alert to JSON file for backend to serve"""

    test_alerts['arbitrage']['alerts'] = [opportunity]
    test_alerts['arbitrage']['count'] = 1

    # Save to file
    output_file = "test_alert.json"
    with open(output_file, 'w') as f:
        json.dump(test_alerts, f, indent=2)

    print(f"\n💾 Saved test alert to {output_file}")
    print(f"\n📋 Test Alert JSON:")
    print(json.dumps(opportunity, indent=2))

def main():
    """Main test function"""

    print("=" * 60)
    print("BetUS Auto-Fill Test Script")
    print("=" * 60)
    print()

    # Step 1: Fetch live games
    sports_to_try = [
        'basketball_nba',
        'americanfootball_nfl',
        'icehockey_nhl',
        'baseball_mlb'
    ]

    games = []
    for sport in sports_to_try:
        games = fetch_live_games(sport)
        if games:
            print(f"✅ Using {sport} games")
            break

    if not games:
        print("\n❌ No live games found from Odds API")
        print("\n💡 Creating a mock game for testing...")

        # Create mock game if API fails
        mock_game = {
            "id": "mock-game-123",
            "sport_key": "basketball_nba",
            "commence_time": datetime.now().isoformat(),
            "home_team": "Los Angeles Lakers",
            "away_team": "Golden State Warriors",
            "bookmakers": [
                {
                    "key": "betus",
                    "title": "BetUS",
                    "markets": [
                        {
                            "key": "totals",
                            "outcomes": [
                                {"name": "Over", "price": -110, "point": 225.5},
                                {"name": "Under", "price": -110, "point": 225.5}
                            ]
                        }
                    ]
                },
                {
                    "key": "draftkings",
                    "title": "DraftKings",
                    "markets": [
                        {
                            "key": "totals",
                            "outcomes": [
                                {"name": "Over", "price": -110, "point": 226.5},
                                {"name": "Under", "price": -110, "point": 226.5}
                            ]
                        }
                    ]
                }
            ]
        }
        games = [mock_game]

    # Step 2: Pick a random game
    random_game = random.choice(games)
    print(f"\n🎲 Selected random game: {random_game.get('away_team')} @ {random_game.get('home_team')}")

    # Step 3: Create test opportunity
    opportunity = create_test_opportunity(random_game)

    if not opportunity:
        print("\n❌ Could not create test opportunity")
        return

    # Step 4: Save to file
    save_test_alert(opportunity)

    print("\n" + "=" * 60)
    print("✅ Test alert ready!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Make sure your extension is loaded")
    print("2. Click the 'Test BetUS' button in the popup")
    print("3. OR run your backend with this test alert")
    print()

if __name__ == "__main__":
    main()
