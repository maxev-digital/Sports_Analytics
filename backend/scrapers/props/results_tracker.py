"""
Player Props Results Tracker
Fetches actual game stats and grades props from previous day
Run daily at 2am CST after all games complete

Usage:
    python backend/scrapers/props/results_tracker.py
"""
import sys
import sqlite3
from pathlib import Path
from datetime import datetime, date, timedelta

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.props.balldontlie_client import BallDontLieClient


class PropsResultsTracker:
    """
    Grades player props by fetching actual game stats
    """

    def __init__(self, db_path: str = "D:/backend/data/player_props.db"):
        self.db_path = db_path
        self.stats_client = BallDontLieClient()

    def grade_previous_day_props(self, target_date: date = None):
        """
        Grade all props from previous day by fetching actual stats
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        print("=" * 70)
        print("PLAYER PROPS - RESULTS TRACKER")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target date: {target_date}")
        print(f"Database: {self.db_path}")
        print()

        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all props from target date that haven't been graded yet
        print("[1/4] Fetching ungraded props...")
        cursor.execute("""
            SELECT DISTINCT player_id, player_name, team, opponent, prop_type, market_line
            FROM player_props_lines
            WHERE date = ?
            AND player_id NOT IN (
                SELECT player_id FROM player_props_results
                WHERE date = ? AND prop_type = player_props_lines.prop_type
            )
        """, (target_date, target_date))

        ungraded_props = cursor.fetchall()
        print(f"  [OK] Found {len(ungraded_props)} ungraded props")

        if len(ungraded_props) == 0:
            print("\n[INFO] No props to grade (either already graded or no props for this date)")

            # Get total count before closing
            cursor.execute("SELECT COUNT(*) FROM player_props_results")
            total_all_time = cursor.fetchone()[0]

            conn.close()
            return {"graded": 0, "errors": 0, "skipped": 0, "total_all_time": total_all_time}

        # Grade each prop
        print(f"\n[2/4] Fetching game stats and grading props...")
        graded_count = 0
        error_count = 0
        skipped_count = 0

        for player_id, player_name, team, opponent, prop_type, market_line in ungraded_props:
            try:
                # Search for player on BallDontLie
                player = self.stats_client.get_player_by_name(player_name)

                if not player:
                    print(f"  [SKIP] Could not find player: {player_name}")
                    skipped_count += 1
                    continue

                # Get games from target date
                # NOTE: Database has 2025 dates but we need 2024 season data
                # Map to equivalent date in current season
                real_season_date = target_date.replace(year=2024) if target_date.year == 2025 else target_date

                # Fetch stats for the real season date
                url = f"{self.stats_client.BASE_URL}/stats"
                params = {
                    'player_ids[]': player['id'],
                    'start_date': (real_season_date - timedelta(days=1)).strftime("%Y-%m-%d"),
                    'end_date': (real_season_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                    'per_page': 10
                }

                response = self.stats_client.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                games = data.get('data', [])

                if not games:
                    print(f"  [SKIP] No game found for {player_name} on {target_date}")
                    skipped_count += 1
                    continue

                # Find game from real season date
                target_game = None
                for game in games:
                    game_date_str = game.get('game', {}).get('date', '')[:10]
                    game_date = datetime.fromisoformat(game_date_str).date()

                    # Match on month/day (ignore year due to 2024/2025 mapping)
                    if game_date.month == real_season_date.month and game_date.day == real_season_date.day:
                        target_game = game
                        break

                if not target_game:
                    print(f"  [SKIP] No game on exact date for {player_name}")
                    skipped_count += 1
                    continue

                # Extract actual stat value
                actual_value = self._get_stat_value(target_game, prop_type)

                if actual_value is None:
                    print(f"  [SKIP] Could not get {prop_type} for {player_name}")
                    skipped_count += 1
                    continue

                # Determine if prop hit (over)
                hit = actual_value > market_line
                difference = actual_value - market_line

                # Store result in database
                cursor.execute("""
                    INSERT OR REPLACE INTO player_props_results
                    (date, player_id, player_name, team, opponent, prop_type,
                     market_line, actual_value, hit, difference)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    target_date,
                    player_id,
                    player_name,
                    team,
                    opponent,
                    prop_type,
                    market_line,
                    actual_value,
                    hit,
                    difference
                ))

                hit_str = "HIT" if hit else "MISS"
                print(f"  [OK] {player_name} {prop_type}: {actual_value} vs {market_line} = {hit_str}")
                graded_count += 1

            except Exception as e:
                print(f"  [ERROR] Failed to grade {player_name} {prop_type}: {e}")
                error_count += 1

        # Commit results
        conn.commit()

        # Update predictions table with results
        print(f"\n[3/5] Updating predictions with results...")
        cursor.execute("""
            UPDATE player_props_predictions
            SET actual_value = (
                    SELECT r.actual_value
                    FROM player_props_results r
                    WHERE r.player_id = player_props_predictions.player_id
                      AND r.date = player_props_predictions.game_date
                      AND r.prop_type = player_props_predictions.prop_type
                ),
                result = (
                    SELECT CASE
                        WHEN r.actual_value = player_props_predictions.market_line THEN 'PUSH'
                        WHEN r.actual_value > player_props_predictions.market_line
                             AND player_props_predictions.recommendation = 'OVER' THEN 'WIN'
                        WHEN r.actual_value < player_props_predictions.market_line
                             AND player_props_predictions.recommendation = 'UNDER' THEN 'WIN'
                        ELSE 'LOSS'
                    END
                    FROM player_props_results r
                    WHERE r.player_id = player_props_predictions.player_id
                      AND r.date = player_props_predictions.game_date
                      AND r.prop_type = player_props_predictions.prop_type
                )
            WHERE game_date = ?
              AND EXISTS (
                  SELECT 1 FROM player_props_results r
                  WHERE r.player_id = player_props_predictions.player_id
                    AND r.date = player_props_predictions.game_date
                    AND r.prop_type = player_props_predictions.prop_type
              )
        """, (target_date,))

        updated_predictions = cursor.rowcount
        print(f"  [OK] Updated {updated_predictions} predictions with results")
        conn.commit()

        # Summary statistics
        print(f"\n[4/5] Summary for {target_date}...")

        # Hit rate by prop type
        cursor.execute("""
            SELECT prop_type,
                   COUNT(*) as total,
                   SUM(CASE WHEN hit = 1 THEN 1 ELSE 0 END) as hits,
                   AVG(difference) as avg_difference
            FROM player_props_results
            WHERE date = ?
            GROUP BY prop_type
        """, (target_date,))

        prop_stats = cursor.fetchall()
        print(f"  Props graded by type:")
        for prop_type, total, hits, avg_diff in prop_stats:
            hit_rate = (hits / total * 100) if total > 0 else 0
            print(f"    - {prop_type}: {hits}/{total} hit ({hit_rate:.1f}%) | Avg diff: {avg_diff:+.2f}")

        # Overall statistics
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN hit = 1 THEN 1 ELSE 0 END) as hits
            FROM player_props_results
            WHERE date = ?
        """, (target_date,))

        total, hits = cursor.fetchone()
        overall_hit_rate = (hits / total * 100) if total > 0 else 0

        # All-time statistics
        cursor.execute("SELECT COUNT(*) FROM player_props_results")
        total_all_time = cursor.fetchone()[0]

        conn.close()

        print(f"\n  Overall hit rate: {hits}/{total} ({overall_hit_rate:.1f}%)")
        print(f"  Total results all-time: {total_all_time}")

        # Analysis
        print(f"\n[5/5] Analysis...")
        if overall_hit_rate > 0:
            print(f"  Breakeven rate: 52.4% (standard -110 odds)")
            if overall_hit_rate > 52.4:
                print(f"  [GOOD] Hit rate above breakeven!")
            else:
                print(f"  [INFO] Hit rate below breakeven (expected for random sample)")

        print("\n" + "=" * 70)
        print("[SUCCESS] Props grading complete!")
        print("=" * 70)

        return {
            "date": str(target_date),
            "graded": graded_count,
            "errors": error_count,
            "skipped": skipped_count,
            "total_all_time": total_all_time
        }

    def _get_stat_value(self, game_stats: dict, prop_type: str) -> float:
        """
        Extract stat value from game stats based on prop type
        """
        stat_map = {
            "points": "pts",
            "rebounds": "reb",
            "assists": "ast",
            "threes": "fg3m",
            "blocks": "blk",
            "steals": "stl"
        }

        stat_key = stat_map.get(prop_type)
        if stat_key:
            return game_stats.get(stat_key, 0.0)

        # Handle PRA (points + rebounds + assists)
        if prop_type == "PRA":
            pts = game_stats.get("pts", 0)
            reb = game_stats.get("reb", 0)
            ast = game_stats.get("ast", 0)
            return pts + reb + ast

        return None


def main():
    """
    Main entry point for results tracker
    """
    tracker = PropsResultsTracker()

    # Grade yesterday's props
    yesterday = date.today() - timedelta(days=1)
    result = tracker.grade_previous_day_props(yesterday)

    if result:
        print(f"\nGrading completed!")
        print(f"Graded: {result['graded']} props")
        print(f"Skipped: {result['skipped']} (no game data)")
        print(f"Errors: {result['errors']}")
        print(f"Database now has: {result['total_all_time']} graded results")

    # Backup recommendation
    print("\n" + "=" * 70)
    print("REMINDER: Run backup script to save this data!")
    print("  python backup_props_data.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
