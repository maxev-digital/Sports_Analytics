"""
Populate Player Stats Cache
Fetches current season stats for all players and caches in database
"""

import sys
import sqlite3
import time
from pathlib import Path
from datetime import date
from typing import Dict, List

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.props.balldontlie_client import BallDontLieClient


class PlayerStatsCachePopulator:
    """
    Fetches and caches player season statistics
    """

    def __init__(self, db_path: str = "data/player_props.db"):
        self.db_path = db_path
        self.stats_client = BallDontLieClient()
        self.current_season = 2024  # 2024-25 season

    def get_unique_players(self) -> List[tuple]:
        """Get all unique players from props lines"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT player_id, player_name, team
            FROM player_props_lines
            ORDER BY player_name
        """)

        players = cursor.fetchall()
        conn.close()

        return players

    def fetch_and_cache_player_stats(self, player_id: str, player_name: str, team: str):
        """
        Fetch player's season stats and cache in database
        """
        try:
            # Get season averages from BallDontLie
            season_avg = self.stats_client.get_player_season_averages(
                player_id, self.current_season
            )

            if not season_avg:
                print(f"  [SKIP] No stats for {player_name}")
                return False

            # Calculate last 10 game stats (if available)
            # For now, use season averages as proxy
            last_10_ppg = season_avg.get('pts', 0)
            last_10_rpg = season_avg.get('reb', 0)
            last_10_apg = season_avg.get('ast', 0)

            # Determine trend direction (placeholder - would need game log)
            trend_direction = 'STABLE'

            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO player_stats_cache
                (player_id, player_name, team, date, games_played, minutes_per_game,
                 points_per_game, rebounds_per_game, assists_per_game, fg3_per_game,
                 blocks_per_game, steals_per_game, fg_pct, last_10_ppg, last_10_rpg,
                 last_10_apg, trend_direction)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player_id,
                player_name,
                team,
                date.today().isoformat(),
                season_avg.get('games_played', 0),
                season_avg.get('min', 0),
                season_avg.get('pts', 0),
                season_avg.get('reb', 0),
                season_avg.get('ast', 0),
                season_avg.get('fg3m', 0),
                season_avg.get('blk', 0),
                season_avg.get('stl', 0),
                season_avg.get('fg_pct', 0),
                last_10_ppg,
                last_10_rpg,
                last_10_apg,
                trend_direction
            ))

            conn.commit()
            conn.close()

            print(f"  [OK] Cached stats for {player_name}: {season_avg.get('pts', 0):.1f} PPG, {season_avg.get('reb', 0):.1f} RPG, {season_avg.get('ast', 0):.1f} APG")
            return True

        except Exception as e:
            print(f"  [ERROR] Failed to fetch stats for {player_name}: {e}")
            return False

    def populate_all_players(self):
        """
        Fetch and cache stats for all unique players
        """
        print(f"\n{'='*70}")
        print("POPULATING PLAYER STATS CACHE")
        print(f"{'='*70}\n")

        # Get all unique players
        players = self.get_unique_players()
        print(f"[1/2] Found {len(players)} unique players\n")

        # Fetch stats for each player
        print(f"[2/2] Fetching season stats from BallDontLie API...\n")

        cached_count = 0
        skipped_count = 0

        for i, (player_id, player_name, team) in enumerate(players, 1):
            if i % 10 == 0:
                print(f"\nProgress: {i}/{len(players)} ({i/len(players)*100:.1f}%)")

            success = self.fetch_and_cache_player_stats(player_id, player_name, team)

            if success:
                cached_count += 1
            else:
                skipped_count += 1

            # Rate limiting
            time.sleep(0.3)

        # Summary
        print(f"\n{'='*70}")
        print("CACHE POPULATION COMPLETE")
        print(f"{'='*70}")
        print(f"Players cached: {cached_count}")
        print(f"Players skipped: {skipped_count}")
        print(f"Total processed: {len(players)}")
        print(f"{'='*70}\n")

        return {
            'cached': cached_count,
            'skipped': skipped_count,
            'total': len(players)
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Populate player stats cache')
    parser.add_argument('--db-path', type=str, default='data/player_props.db',
                       help='Path to props database')

    args = parser.parse_args()

    populator = PlayerStatsCachePopulator(db_path=args.db_path)
    result = populator.populate_all_players()

    if result['cached'] > 0:
        print(f"[SUCCESS] Cached stats for {result['cached']} players!")
        print(f"\nYou can now:")
        print(f"1. Retrain models with full features (33 features instead of 6)")
        print(f"2. Use the full predictor instead of fast predictor")
        print(f"3. Get better predictions with player-specific data")
    else:
        print(f"[ERROR] No player stats were cached")


if __name__ == "__main__":
    main()
