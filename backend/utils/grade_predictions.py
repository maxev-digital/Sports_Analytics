"""
Grade Predictions Utility
Compares predictions against actual results and calculates performance metrics

Updates:
- Win/Loss/Push for each prediction
- Overall accuracy by prop type
- ROI calculations
- Confidence-level performance

Runs nightly after fetch_daily_results.py
"""

import sys
import sqlite3
from pathlib import Path
from datetime import date, datetime
from collections import defaultdict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class PredictionGrader:
    """
    Grades predictions and tracks performance metrics
    """

    def __init__(self, db_path: str = "D:/backend/data/player_props.db"):
        self.db_path = db_path
        self.stats = defaultdict(lambda: {
            'total': 0,
            'wins': 0,
            'losses': 0,
            'pushes': 0
        })

    def grade_todays_predictions(self, target_date: date = None):
        """
        Grade all predictions for a specific date
        """
        if target_date is None:
            target_date = date.today()

        print(f"\n{'='*70}")
        print("GRADING PREDICTIONS")
        print(f"{'='*70}\n")
        print(f"Target Date: {target_date.strftime('%Y-%m-%d')}\n")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all predictions for the date
        cursor.execute("""
            SELECT id, player_id, player_name, prop_type, market_line,
                   predicted_value, recommendation, confidence
            FROM player_props_predictions
            WHERE game_date = ?
              AND result IS NULL
        """, (target_date.isoformat(),))

        predictions = cursor.fetchall()

        if not predictions:
            print(f"[INFO] No ungraded predictions found for {target_date}")
            conn.close()
            return

        print(f"[1/2] Found {len(predictions)} predictions to grade\n")

        graded_count = 0
        for pred_id, player_id, player_name, prop_type, market_line, predicted_value, recommendation, confidence in predictions:

            # Get actual result
            cursor.execute("""
                SELECT actual_value, hit
                FROM player_props_results
                WHERE player_id = ?
                  AND prop_type = ?
                  AND date = ?
            """, (player_id, prop_type, target_date.isoformat()))

            result_row = cursor.fetchone()

            if not result_row:
                continue  # No result yet, player didn't play

            actual_value, hit = result_row

            # Determine prediction result
            if recommendation == 'OVER':
                if hit == 1:  # actual > line
                    result = 'WIN'
                elif hit == 0:  # actual == line
                    result = 'PUSH'
                else:  # actual < line
                    result = 'LOSS'
            elif recommendation == 'UNDER':
                if hit == -1:  # actual < line
                    result = 'WIN'
                elif hit == 0:  # actual == line
                    result = 'PUSH'
                else:  # actual > line
                    result = 'LOSS'
            else:  # PASS
                result = 'PASS'

            # Update prediction with result
            cursor.execute("""
                UPDATE player_props_predictions
                SET actual_value = ?,
                    result = ?
                WHERE id = ?
            """, (actual_value, result, pred_id))

            # Track stats
            self.stats[prop_type]['total'] += 1
            if result == 'WIN':
                self.stats[prop_type]['wins'] += 1
            elif result == 'LOSS':
                self.stats[prop_type]['losses'] += 1
            elif result == 'PUSH':
                self.stats[prop_type]['pushes'] += 1

            self.stats['overall']['total'] += 1
            if result == 'WIN':
                self.stats['overall']['wins'] += 1
            elif result == 'LOSS':
                self.stats['overall']['losses'] += 1
            elif result == 'PUSH':
                self.stats['overall']['pushes'] += 1

            graded_count += 1

        conn.commit()
        conn.close()

        print(f"[2/2] Graded {graded_count} predictions\n")

        # Display results
        self.display_performance()

        return graded_count

    def display_performance(self):
        """
        Display performance metrics
        """
        print(f"{'='*70}")
        print("PERFORMANCE SUMMARY")
        print(f"{'='*70}\n")

        for prop_type, stats in sorted(self.stats.items()):
            if stats['total'] == 0:
                continue

            total = stats['total']
            wins = stats['wins']
            losses = stats['losses']
            pushes = stats['pushes']

            # Calculate win rate (excluding pushes)
            decisions = wins + losses
            win_rate = (wins / decisions * 100) if decisions > 0 else 0

            # Calculate ROI (assuming -110 odds)
            # Win: +0.91 units, Loss: -1.00 units, Push: 0 units
            profit = (wins * 0.91) - (losses * 1.0)
            roi = (profit / total * 100) if total > 0 else 0

            print(f"{prop_type.upper()}")
            print(f"  Total: {total}")
            print(f"  Wins: {wins} ({wins/total*100:.1f}%)")
            print(f"  Losses: {losses} ({losses/total*100:.1f}%)")
            print(f"  Pushes: {pushes} ({pushes/total*100:.1f}%)")
            print(f"  Win Rate: {win_rate:.1f}% (excl. pushes)")
            print(f"  ROI: {roi:+.1f}%")
            print(f"  Profit: {profit:+.2f} units\n")

        print(f"{'='*70}\n")

    def calculate_historical_performance(self):
        """
        Calculate all-time performance metrics
        """
        print(f"\n{'='*70}")
        print("HISTORICAL PERFORMANCE")
        print(f"{'='*70}\n")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all graded predictions
        cursor.execute("""
            SELECT prop_type, recommendation, result
            FROM player_props_predictions
            WHERE result IS NOT NULL
              AND result != 'PASS'
        """)

        all_predictions = cursor.fetchall()
        conn.close()

        if not all_predictions:
            print("[INFO] No historical predictions found")
            return

        # Aggregate stats
        prop_stats = defaultdict(lambda: defaultdict(int))

        for prop_type, recommendation, result in all_predictions:
            prop_stats[prop_type][result] += 1
            prop_stats['overall'][result] += 1

        # Display
        for prop_type, results in sorted(prop_stats.items()):
            total = sum(results.values())
            wins = results['WIN']
            losses = results['LOSS']
            pushes = results['PUSH']

            decisions = wins + losses
            win_rate = (wins / decisions * 100) if decisions > 0 else 0

            profit = (wins * 0.91) - (losses * 1.0)
            roi = (profit / total * 100) if total > 0 else 0

            print(f"{prop_type.upper()} - All Time")
            print(f"  Total: {total}")
            print(f"  Win Rate: {win_rate:.1f}%")
            print(f"  ROI: {roi:+.1f}%")
            print(f"  Profit: {profit:+.2f} units\n")

        print(f"{'='*70}\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Grade predictions')
    parser.add_argument('--date', type=str, help='Date to grade (YYYY-MM-DD), defaults to today')
    parser.add_argument('--historical', action='store_true', help='Show historical performance')
    parser.add_argument('--db-path', type=str, default='D:/backend/data/player_props.db',
                       help='Path to database')

    args = parser.parse_args()

    grader = PredictionGrader(db_path=args.db_path)

    if args.historical:
        grader.calculate_historical_performance()
    else:
        target_date = date.today()
        if args.date:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()

        graded = grader.grade_todays_predictions(target_date)

        if graded > 0:
            print(f"[SUCCESS] Graded {graded} predictions!")
        else:
            print(f"[INFO] No predictions to grade")


if __name__ == "__main__":
    main()
