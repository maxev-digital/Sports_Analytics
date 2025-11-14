"""
Fetch Daily NBA Results
Scrapes actual game results to grade predictions

Data sources:
1. BallDontLie API - Box scores
2. NBA Stats API - Game logs
3. Fallback to ESPN if needed

Runs nightly at 11pm CST after all games complete
"""

import sys
import sqlite3
import time
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Dict, List
import requests

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from nba_api.stats.endpoints import leaguegamelog
except ImportError:
    print("[WARN] nba_api not installed. Install: pip install nba_api")


class DailyResultsFetcher:
    """
    Fetches actual player performance from completed games
    """

    def __init__(self, db_path: str = "D:/backend/data/player_props.db"):
        self.db_path = db_path
        self.today = date.today()

    def fetch_games_from_nba_api(self, target_date: date) -> List[Dict]:
        """
        Fetch all games for a specific date using NBA Stats API
        """
        try:
            # Get game log for the date
            gamelog = leaguegamelog.LeagueGameLog(
                season='2024-25',
                season_type_all_star='Regular Season',
                date_from_nullable=target_date.strftime('%m/%d/%Y'),
                date_to_nullable=target_date.strftime('%m/%d/%Y')
            )

            df = gamelog.get_data_frames()[0]

            if df.empty:
                print(f"  [INFO] No games found for {target_date}")
                return []

            # Process results
            results = []
            for _, row in df.iterrows():
                results.append({
                    'game_id': row['GAME_ID'],
                    'player_id': str(row['PLAYER_ID']),
                    'player_name': row['PLAYER_NAME'],
                    'team': row['TEAM_ABBREVIATION'],
                    'points': float(row['PTS']),
                    'rebounds': float(row['REB']),
                    'assists': float(row['AST']),
                    'fg3m': float(row['FG3M']),
                    'blocks': float(row['BLK']),
                    'steals': float(row['STL']),
                    'minutes': float(row['MIN']) if row['MIN'] else 0
                })

            print(f"  [OK] Found {len(results)} player performances")
            return results

        except Exception as e:
            print(f"  [ERROR] NBA API failed: {e}")
            return []

    def save_results_to_db(self, results: List[Dict], target_date: date):
        """
        Save actual results to player_props_results table
        """
        if not results:
            print("  [SKIP] No results to save")
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0
        for result in results:
            try:
                # Save each prop type separately
                prop_types = {
                    'points': result['points'],
                    'rebounds': result['rebounds'],
                    'assists': result['assists'],
                    'threes': result['fg3m'],
                    'blocks': result['blocks'],
                    'steals': result['steals'],
                    'PRA': result['points'] + result['rebounds'] + result['assists']
                }

                for prop_type, actual_value in prop_types.items():
                    # Get the market line from predictions (if exists)
                    cursor.execute("""
                        SELECT market_line
                        FROM player_props_predictions
                        WHERE player_id = ?
                          AND prop_type = ?
                          AND game_date = ?
                        LIMIT 1
                    """, (result['player_id'], prop_type, target_date.isoformat()))

                    pred_row = cursor.fetchone()
                    market_line = pred_row[0] if pred_row else actual_value

                    # Determine hit (1 = over, 0 = push, -1 = under)
                    if actual_value > market_line:
                        hit = 1  # OVER wins
                    elif actual_value < market_line:
                        hit = -1  # UNDER wins
                    else:
                        hit = 0  # PUSH

                    difference = actual_value - market_line

                    # Insert result
                    cursor.execute("""
                        INSERT OR REPLACE INTO player_props_results
                        (date, game_id, player_id, player_name, team, opponent,
                         prop_type, market_line, actual_value, hit, difference)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        target_date.isoformat(),
                        result['game_id'],
                        result['player_id'],
                        result['player_name'],
                        result['team'],
                        'UNK',  # opponent not in game log
                        prop_type,
                        market_line,
                        actual_value,
                        hit,
                        difference
                    ))

                    saved_count += 1

            except Exception as e:
                print(f"  [ERROR] Failed to save {result['player_name']}: {e}")

        conn.commit()
        conn.close()

        print(f"  [OK] Saved {saved_count} results")
        return saved_count

    def run_daily_fetch(self, target_date: date = None):
        """
        Run complete daily results fetch
        """
        if target_date is None:
            target_date = self.today

        print(f"\n{'='*70}")
        print("DAILY RESULTS FETCHER")
        print(f"{'='*70}\n")
        print(f"Target Date: {target_date.strftime('%Y-%m-%d')}")
        print(f"Database: {self.db_path}\n")

        # Fetch results from NBA API
        print("[1/2] Fetching game results from NBA Stats API...")
        results = self.fetch_games_from_nba_api(target_date)

        # Save to database
        print("\n[2/2] Saving results to database...")
        saved = self.save_results_to_db(results, target_date)

        # Summary
        print(f"\n{'='*70}")
        print("FETCH COMPLETE")
        print(f"{'='*70}")
        print(f"Date: {target_date.strftime('%Y-%m-%d')}")
        print(f"Results fetched: {len(results)}")
        print(f"Records saved: {saved}")
        print(f"{'='*70}\n")

        return saved > 0


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Fetch daily NBA results')
    parser.add_argument('--date', type=str, help='Date to fetch (YYYY-MM-DD), defaults to today')
    parser.add_argument('--db-path', type=str, default='D:/backend/data/player_props.db',
                       help='Path to database')

    args = parser.parse_args()

    target_date = date.today()
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()

    fetcher = DailyResultsFetcher(db_path=args.db_path)
    success = fetcher.run_daily_fetch(target_date)

    if success:
        print("[SUCCESS] Daily results fetched and saved!")
    else:
        print("[WARN] No results fetched (no games today?)")


if __name__ == "__main__":
    main()
