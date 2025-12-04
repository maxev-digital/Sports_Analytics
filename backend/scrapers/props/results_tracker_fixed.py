"""
Player Props Results Tracker - Fixed for player_prop_predictions schema
Fetches actual game stats and grades props from previous day
Run daily at 3am CST after all games complete

Usage:
    python backend/scrapers/props/results_tracker_fixed.py
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
    Compatible with player_prop_predictions table
    Uses existing BallDontLieClient for API access
    """

    def __init__(self, db_path: str = "/root/sporttrader/backend/ml/predictions.db"):
        self.db_path = db_path
        self.stats_client = BallDontLieClient()

    def grade_previous_day_props(self, target_date: date = None):
        """
        Grade all props from previous day by fetching actual stats

        Args:
            target_date: Date to grade props for (default: yesterday)

        Returns:
            dict: Summary of grading results
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        print("=" * 70)
        print("PLAYER PROPS - RESULTS TRACKER (FIXED)")
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
            SELECT id, player_name, team, opponent, prop_type, market_line, recommendation
            FROM player_prop_predictions
            WHERE date(prediction_date) = ?
            AND result IS NULL
            ORDER BY player_name
        """, (str(target_date),))

        ungraded_props = cursor.fetchall()
        print(f"  ✅ Found {len(ungraded_props)} ungraded props")

        if len(ungraded_props) == 0:
            print("\n[INFO] No props to grade (either already graded or no props for this date)")

            # Get total graded count
            cursor.execute("SELECT COUNT(*) FROM player_prop_predictions WHERE result IS NOT NULL")
            total_graded = cursor.fetchone()[0]

            conn.close()
            return {"graded": 0, "errors": 0, "skipped": 0, "total_graded": total_graded}

        # Grade each prop
        print(f"\n[2/4] Fetching game stats and grading props...")
        print(f"  (This will take ~{len(ungraded_props) * 0.1:.0f} seconds due to API rate limiting)")
        graded_count = 0
        error_count = 0
        skipped_count = 0

        for prop_id, player_name, team, opponent, prop_type, market_line, recommendation in ungraded_props:
            try:
                # Get actual stat value from API
                actual_value = self._get_player_stat(player_name, prop_type, target_date)

                if actual_value is None:
                    print(f"  ⚠️  Could not get {prop_type} for {player_name}")
                    skipped_count += 1
                    continue

                # Determine result based on recommendation
                if recommendation == 'OVER':
                    result = 'WIN' if actual_value > market_line else 'LOSS'
                elif recommendation == 'UNDER':
                    result = 'WIN' if actual_value < market_line else 'LOSS'
                else:
                    result = 'PUSH'  # NO_PLAY recommendations

                # Update database
                cursor.execute("""
                    UPDATE player_prop_predictions
                    SET result = ?,
                        actual_value = ?,
                        graded_at = ?
                    WHERE id = ?
                """, (result, actual_value, datetime.now().isoformat(), prop_id))

                print(f"  ✅ {player_name} {prop_type}: {actual_value} vs {market_line} → {result}")
                graded_count += 1

            except Exception as e:
                print(f"  ❌ Failed to grade {player_name} {prop_type}: {e}")
                error_count += 1

        # Commit all changes
        print("\n[3/4] Saving results to database...")
        conn.commit()
        print(f"  ✅ Saved {graded_count} graded props")

        # Get summary stats
        print("\n[4/4] Generating summary...")
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN result = 'PUSH' THEN 1 ELSE 0 END) as pushes
            FROM player_prop_predictions
            WHERE date(prediction_date) = ?
            AND result IS NOT NULL
        """, (str(target_date),))

        stats = cursor.fetchone()
        total, wins, losses, pushes = stats

        conn.close()

        # Print summary
        print("=" * 70)
        print("GRADING SUMMARY")
        print("=" * 70)
        print(f"Date: {target_date}")
        print(f"Graded: {graded_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Errors: {error_count}")
        print()
        print(f"Results for {target_date}:")
        print(f"  Wins: {wins}/{total} ({wins/total*100:.1f}%)" if total > 0 else "  Wins: 0/0")
        print(f"  Losses: {losses}/{total} ({losses/total*100:.1f}%)" if total > 0 else "  Losses: 0/0")
        print(f"  Pushes: {pushes}/{total}" if total > 0 else "  Pushes: 0/0")
        print("=" * 70)

        return {
            "graded": graded_count,
            "errors": error_count,
            "skipped": skipped_count,
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "total": total
        }

    def _get_player_stat(self, player_name: str, prop_type: str, game_date: date) -> float:
        """
        Get actual stat value for a player on a specific date

        Args:
            player_name: Player's full name
            prop_type: Type of prop (points, rebounds, assists, etc.)
            game_date: Date of the game

        Returns:
            float: Actual stat value, or None if not found
        """
        try:
            # Find the player
            player = self.stats_client.get_player_by_name(player_name)
            if not player:
                return None

            # Get stats for that specific date
            stats = self.stats_client.get_player_recent_games(
                player['id'],
                last_n_days=1,  # Just that one day
                limit=1
            )

            if not stats:
                return None

            # Get the game from target date
            game = None
            for g in stats:
                game_obj = g.get('game', {})
                game_date_str = game_obj.get('date', '')[:10]  # YYYY-MM-DD
                if game_date_str == game_date.strftime("%Y-%m-%d"):
                    game = g
                    break

            if not game:
                return None

            # Extract the stat value
            stat_value = self._extract_stat(game, prop_type)
            return stat_value

        except Exception as e:
            print(f"    Error fetching stat: {e}")
            return None

    def _extract_stat(self, game_stats: dict, prop_type: str) -> float:
        """
        Extract specific stat from game stats

        Args:
            game_stats: Game stats dictionary from API
            prop_type: Type of prop to extract

        Returns:
            float: Stat value
        """
        # Map prop types to API fields
        stat_map = {
            'points': 'pts',
            'rebounds': 'reb',
            'assists': 'ast',
            'steals': 'stl',
            'blocks': 'blk',
            'threes': 'fg3m',
            '3pm': 'fg3m',
            'turnovers': 'turnover',
            'pra': lambda s: s.get('pts', 0) + s.get('reb', 0) + s.get('ast', 0),
            'pts+reb+ast': lambda s: s.get('pts', 0) + s.get('reb', 0) + s.get('ast', 0),
            'pts+reb': lambda s: s.get('pts', 0) + s.get('reb', 0),
            'pts+ast': lambda s: s.get('pts', 0) + s.get('ast', 0),
            'reb+ast': lambda s: s.get('reb', 0) + s.get('ast', 0),
        }

        prop_lower = prop_type.lower()

        # Check for combo stats
        if prop_lower in stat_map:
            field = stat_map[prop_lower]
            if callable(field):
                return field(game_stats)
            return game_stats.get(field, 0)

        # Try direct match
        return game_stats.get(prop_type, 0)


if __name__ == "__main__":
    """Test the grading system"""
    import sys
    from datetime import date, timedelta

    # Get date from command line or use yesterday
    if len(sys.argv) > 1:
        target_date = date.fromisoformat(sys.argv[1])
    else:
        target_date = date.today() - timedelta(days=1)

    tracker = PropsResultsTracker()
    result = tracker.grade_previous_day_props(target_date)

    print(f"\n✅ Grading complete!")
    print(f"Graded: {result['graded']}")
    print(f"Errors: {result['errors']}")
    print(f"Skipped: {result['skipped']}")

    sys.exit(0 if result['errors'] == 0 else 1)
