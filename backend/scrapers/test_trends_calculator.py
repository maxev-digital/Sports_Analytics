"""
Quick test of NFL betting trends calculator logic
Creates a test database with sample completed games
"""
import sqlite3
import os
from datetime import datetime, timezone
from nfl_betting_trends_calculator import NFLBettingTrendsCalculator

def create_test_database():
    """Create a test database with sample completed NFL games"""
    db_path = 'test_odds_history.db'

    # Remove old test database
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE game_odds_pregame (
        id INTEGER PRIMARY KEY,
        game_id TEXT,
        sport_key TEXT,
        home_team TEXT,
        away_team TEXT,
        commence_time TEXT,
        home_spread REAL,
        total_over_under REAL,
        snapshot_type TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE game_results (
        game_id TEXT PRIMARY KEY,
        home_score INTEGER,
        away_score INTEGER,
        completed INTEGER
    )
    """)

    # Insert test games (Kansas City Chiefs last 5 games)
    test_games = [
        # Game 1: Chiefs 30, Raiders 20 (Spread: KC -7.5, Total: 45.5)
        # ATS: Chiefs cover (30-20=10 > 7.5), Over (50 > 45.5)
        {
            'game_id': 'game1',
            'home_team': 'Kansas City Chiefs',
            'away_team': 'Las Vegas Raiders',
            'home_spread': -7.5,
            'total': 45.5,
            'home_score': 30,
            'away_score': 20
        },
        # Game 2: Bills 27, Chiefs 24 (Spread: KC +3.5, Total: 49.5)
        # ATS: Chiefs cover as dog (24+3.5=27.5 > 27), Under (51 > 49.5 - over)
        {
            'game_id': 'game2',
            'home_team': 'Buffalo Bills',
            'away_team': 'Kansas City Chiefs',
            'home_spread': -3.5,
            'total': 49.5,
            'home_score': 27,
            'away_score': 24
        },
        # Game 3: Chiefs 26, Saints 13 (Spread: KC -4.5, Total: 43.5)
        # ATS: Chiefs don't cover (26-13=13 > 4.5 - they cover!), Under (39 < 43.5)
        {
            'game_id': 'game3',
            'home_team': 'Kansas City Chiefs',
            'away_team': 'New Orleans Saints',
            'home_spread': -4.5,
            'total': 43.5,
            'home_score': 26,
            'away_score': 13
        },
        # Game 4: Chargers 17, Chiefs 16 (Spread: KC +1.5, Total: 45.5)
        # ATS: Chiefs don't cover as dog (16+1.5=17.5 > 17 - push!), Under (33 < 45.5)
        {
            'game_id': 'game4',
            'home_team': 'Los Angeles Chargers',
            'away_team': 'Kansas City Chiefs',
            'home_spread': -1.5,
            'total': 45.5,
            'home_score': 17,
            'away_score': 16
        },
        # Game 5: Chiefs 28, Panthers 27 (Spread: KC -10.5, Total: 47.5)
        # ATS: Chiefs don't cover (28-27=1 < 10.5), Over (55 > 47.5)
        {
            'game_id': 'game5',
            'home_team': 'Kansas City Chiefs',
            'away_team': 'Carolina Panthers',
            'home_spread': -10.5,
            'total': 47.5,
            'home_score': 28,
            'away_score': 27
        }
    ]

    # Insert games
    now = datetime.now(timezone.utc).isoformat()
    for game in test_games:
        cursor.execute("""
        INSERT INTO game_odds_pregame
        (game_id, sport_key, home_team, away_team, commence_time,
         home_spread, total_over_under, snapshot_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game['game_id'],
            'americanfootball_nfl',
            game['home_team'],
            game['away_team'],
            now,
            game['home_spread'],
            game['total'],
            'closing'
        ))

        cursor.execute("""
        INSERT INTO game_results
        (game_id, home_score, away_score, completed)
        VALUES (?, ?, ?, ?)
        """, (
            game['game_id'],
            game['home_score'],
            game['away_score'],
            1
        ))

    conn.commit()
    conn.close()

    print(f"[OK] Created test database with {len(test_games)} completed games")
    return db_path

if __name__ == '__main__':
    # Create test database
    db_path = create_test_database()

    # Test the calculator
    print("\nTesting NFL Betting Trends Calculator...\n")

    calculator = NFLBettingTrendsCalculator(db_path=db_path)
    trends = calculator.calculate_team_trends(lookback_days=365)

    if trends:
        print(f"[OK] Successfully calculated trends for {len(trends)} teams\n")

        # Show Kansas City Chiefs trends
        if 'Kansas City Chiefs' in trends:
            kc = trends['Kansas City Chiefs']
            print("Kansas City Chiefs Trends:")
            print(f"  Games Analyzed: {kc['games_analyzed']}")
            print(f"\n  ATS Record:")
            print(f"    Overall: {kc['ats_record']['wins']}-{kc['ats_record']['losses']}-{kc['ats_record']['pushes']}")
            print(f"    Win %: {kc['ats_win_pct']:.1%}")
            print(f"    Home: {kc['ats_home']['wins']}-{kc['ats_home']['losses']}-{kc['ats_home']['pushes']}")
            print(f"    Away: {kc['ats_away']['wins']}-{kc['ats_away']['losses']}-{kc['ats_away']['pushes']}")
            print(f"    Last 5: {kc['ats_last_5']}")

            print(f"\n  Over/Under:")
            print(f"    Overall: {kc['ou_record']['overs']}-{kc['ou_record']['unders']}-{kc['ou_record']['pushes']}")
            print(f"    Over %: {kc['ou_win_pct']:.1%}")
            print(f"    Home: {kc['ou_home']['overs']}-{kc['ou_home']['unders']}-{kc['ou_home']['pushes']}")
            print(f"    Away: {kc['ou_away']['overs']}-{kc['ou_away']['unders']}-{kc['ou_away']['pushes']}")
            print(f"    Last 5: {kc['ou_last_5']}")

        print("\n[OK] Calculator is working correctly!")
    else:
        print("[NO] No trends calculated")

    # Cleanup
    os.remove(db_path)
    print(f"\nCleaned up test database")
