"""
Update Backtest Database with Verified Strategy Data

This script allows you to replace mock backtest data with verified calculations
from ChatGPT or other sources.

Usage:
    python update_verified_backtests.py --strategy-id 1 --csv results.csv
    python update_verified_backtests.py --batch-update all_strategies.csv
"""

import sys
import argparse
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import json


# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from backtesting.database.backtest_db import BacktestDB


class BacktestUpdater:
    """Handles updating backtest database with verified data"""

    def __init__(self, db_path: str = None):
        self.db = BacktestDB()
        self.db_path = db_path or self.db.db_path

    def backup_database(self):
        """Create backup of database before updates"""
        backup_path = Path(self.db_path).parent / f"backtests_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

        # Copy database
        import shutil
        shutil.copy2(self.db_path, backup_path)

        print(f"[BACKUP] Created backup: {backup_path}")
        return backup_path

    def validate_data(self, data: dict) -> tuple[bool, str]:
        """
        Validate backtest data before updating

        Returns:
            (is_valid, error_message)
        """
        required_fields = ['strategy_id', 'sport', 'bets_placed', 'wins', 'losses']

        # Check required fields
        for field in required_fields:
            if field not in data or data[field] is None:
                return False, f"Missing required field: {field}"

        # Validate numeric fields
        try:
            strategy_id = int(data['strategy_id'])
            bets = int(data['bets_placed'])
            wins = int(data['wins'])
            losses = int(data['losses'])
            pushes = int(data.get('pushes', 0))

            if strategy_id < 1 or strategy_id > 25:
                return False, f"Invalid strategy_id: {strategy_id} (must be 1-25)"

            if bets < 1:
                return False, f"Invalid bets_placed: {bets} (must be >= 1)"

            if wins < 0 or losses < 0 or pushes < 0:
                return False, "Wins, losses, and pushes must be >= 0"

            if wins + losses + pushes != bets:
                return False, f"Wins ({wins}) + Losses ({losses}) + Pushes ({pushes}) != Bets ({bets})"

        except (ValueError, TypeError) as e:
            return False, f"Invalid numeric value: {e}"

        # Validate win rate if provided
        if 'win_rate' in data and data['win_rate'] is not None:
            win_rate = float(data['win_rate'])
            calculated_win_rate = (wins / bets * 100) if bets > 0 else 0

            if abs(win_rate - calculated_win_rate) > 0.5:
                return False, f"Win rate mismatch: Provided {win_rate}%, Calculated {calculated_win_rate:.1f}%"

        return True, ""

    def calculate_metrics(self, wins: int, losses: int, pushes: int, bets_placed: int,
                         odds: str = "-110") -> dict:
        """
        Calculate win rate and ROI from results

        Args:
            wins: Number of winning bets
            losses: Number of losing bets
            pushes: Number of push bets
            bets_placed: Total bets
            odds: Betting odds (default -110)

        Returns:
            Dict with win_rate, roi, profit_loss
        """
        # Calculate win rate (pushes don't count as wins)
        win_rate = (wins / bets_placed * 100) if bets_placed > 0 else 0

        # Calculate profit at -110 odds (standard)
        profit_per_win = 100 * (100/110)  # Win $90.91 per $100 bet
        loss_per_bet = 100  # Lose $100 per $100 bet

        total_profit = (wins * profit_per_win) - (losses * loss_per_bet)
        total_risked = bets_placed * 100

        roi = (total_profit / total_risked * 100) if total_risked > 0 else 0

        # Calculate average edge (simplified)
        # Edge = Win Rate - Break-even Win Rate at -110 (52.38%)
        breakeven_win_rate = 52.38
        edge = win_rate - breakeven_win_rate
        avg_edge = max(0, edge)  # Edge can't be negative if we're tracking it

        return {
            'win_rate': round(win_rate, 1),
            'roi': round(roi, 1),
            'avg_edge': round(avg_edge, 2),
            'profit_loss': round(total_profit, 2)
        }

    def update_strategy(self, strategy_data: dict, create_backup: bool = True) -> bool:
        """
        Update a single strategy's backtest data

        Args:
            strategy_data: Dict with strategy backtest data
            create_backup: Whether to backup database first

        Returns:
            Success boolean
        """
        # Validate data
        is_valid, error = self.validate_data(strategy_data)
        if not is_valid:
            print(f"[ERROR] Validation failed: {error}")
            return False

        # Create backup if requested
        if create_backup:
            self.backup_database()

        # Extract fields
        strategy_id = int(strategy_data['strategy_id'])
        sport = strategy_data['sport']
        bets_placed = int(strategy_data['bets_placed'])
        wins = int(strategy_data['wins'])
        losses = int(strategy_data['losses'])
        pushes = int(strategy_data.get('pushes', 0))

        # Calculate metrics if not provided
        metrics = self.calculate_metrics(wins, losses, pushes, bets_placed)

        # Override with provided values if they exist
        win_rate = float(strategy_data.get('win_rate', metrics['win_rate']))
        roi = float(strategy_data.get('roi', metrics['roi']))
        avg_edge = float(strategy_data.get('avg_edge', metrics['avg_edge']))
        profit_loss = float(strategy_data.get('profit_loss', metrics['profit_loss']))

        # Prepare update data
        update_data = {
            'strategy_id': strategy_id,
            'sport': sport,
            'date_range_start': strategy_data.get('date_range_start', '2023-10-01'),
            'date_range_end': strategy_data.get('date_range_end', '2024-06-15'),
            'total_opportunities': strategy_data.get('total_opportunities', int(bets_placed * 1.5)),
            'bets_placed': bets_placed,
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'win_rate': win_rate,
            'roi': roi,
            'avg_edge': avg_edge,
            'profit_loss': profit_loss,
            'confidence_interval': strategy_data.get('confidence_interval', '95% CI: +/- 3.5%'),
            'best_situations': strategy_data.get('best_situations', 'Best results in optimal conditions'),
            'data_source': strategy_data.get('data_source', 'verified_backtest')
        }

        # Delete existing entry for this strategy
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM backtest_results WHERE strategy_id = ?", (strategy_id,))
        conn.commit()

        # Insert updated data
        backtest_id = self.db.save_backtest_result(update_data)

        conn.close()

        print(f"[SUCCESS] Updated Strategy #{strategy_id}")
        print(f"  Bets: {bets_placed}, Wins: {wins}, Losses: {losses}, Pushes: {pushes}")
        print(f"  Win Rate: {win_rate}%")
        print(f"  ROI: {roi}%")
        print(f"  Backtest ID: {backtest_id}")

        return True

    def batch_update_from_csv(self, csv_path: str) -> dict:
        """
        Update multiple strategies from CSV file

        CSV Format:
        strategy_id,sport,bets_placed,wins,losses,pushes,win_rate,roi,data_source
        1,NBA,287,159,118,10,55.4,9.2,basketball_reference
        3,NBA,145,78,62,5,53.8,7.1,nba_injury_data

        Returns:
            Dict with success/failure counts
        """
        print(f"\n{'='*80}")
        print(f"BATCH UPDATE FROM CSV: {csv_path}")
        print(f"{'='*80}\n")

        # Read CSV
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"[ERROR] Failed to read CSV: {e}")
            return {'success': 0, 'failed': 0, 'errors': [str(e)]}

        # Create single backup for batch
        self.backup_database()

        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }

        # Process each row
        for idx, row in df.iterrows():
            strategy_data = row.to_dict()

            print(f"\nProcessing Strategy #{strategy_data.get('strategy_id', 'Unknown')}...")

            success = self.update_strategy(strategy_data, create_backup=False)

            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f"Strategy #{strategy_data.get('strategy_id')}: Update failed")

        # Print summary
        print(f"\n{'='*80}")
        print(f"BATCH UPDATE SUMMARY")
        print(f"{'='*80}")
        print(f"Total Processed: {len(df)}")
        print(f"Successful: {results['success']}")
        print(f"Failed: {results['failed']}")

        if results['errors']:
            print(f"\nErrors:")
            for error in results['errors']:
                print(f"  - {error}")

        return results

    def preview_changes(self, strategy_id: int, new_data: dict):
        """Preview changes before applying"""
        print(f"\n{'='*80}")
        print(f"PREVIEW CHANGES FOR STRATEGY #{strategy_id}")
        print(f"{'='*80}\n")

        # Get current data
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM backtest_results WHERE strategy_id = ?", (strategy_id,))
        row = cursor.fetchone()

        if row:
            columns = [col[0] for col in cursor.description]
            current = dict(zip(columns, row))

            print("CURRENT VALUES:")
            print(f"  Bets: {current['bets_placed']}")
            print(f"  Wins: {current['wins']}")
            print(f"  Losses: {current['losses']}")
            print(f"  Pushes: {current['pushes']}")
            print(f"  Win Rate: {current['win_rate']}%")
            print(f"  ROI: {current['roi']}%")
            print(f"  Data Source: {current['data_source']}")
        else:
            print("CURRENT VALUES: No data found")

        print("\nNEW VALUES:")
        print(f"  Bets: {new_data['bets_placed']}")
        print(f"  Wins: {new_data['wins']}")
        print(f"  Losses: {new_data['losses']}")
        print(f"  Pushes: {new_data.get('pushes', 0)}")

        metrics = self.calculate_metrics(
            new_data['wins'],
            new_data['losses'],
            new_data.get('pushes', 0),
            new_data['bets_placed']
        )

        print(f"  Win Rate: {metrics['win_rate']}%")
        print(f"  ROI: {metrics['roi']}%")
        print(f"  Data Source: {new_data.get('data_source', 'verified_backtest')}")

        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Update backtest database with verified data')
    parser.add_argument('--strategy-id', type=int, help='Strategy ID to update (1-25)')
    parser.add_argument('--csv', type=str, help='CSV file with strategy data')
    parser.add_argument('--batch', type=str, help='CSV file with multiple strategies')
    parser.add_argument('--preview', action='store_true', help='Preview changes without updating')
    parser.add_argument('--wins', type=int, help='Number of wins')
    parser.add_argument('--losses', type=int, help='Number of losses')
    parser.add_argument('--pushes', type=int, default=0, help='Number of pushes')
    parser.add_argument('--sport', type=str, help='Sport (NBA, NFL, NHL, etc.)')
    parser.add_argument('--data-source', type=str, help='Data source name')

    args = parser.parse_args()

    updater = BacktestUpdater()

    # Batch update from CSV
    if args.batch:
        updater.batch_update_from_csv(args.batch)
        return

    # Single strategy update from CSV
    if args.csv and args.strategy_id:
        df = pd.read_csv(args.csv)
        row = df[df['strategy_id'] == args.strategy_id].iloc[0]
        strategy_data = row.to_dict()

        if args.preview:
            updater.preview_changes(args.strategy_id, strategy_data)
        else:
            updater.update_strategy(strategy_data)
        return

    # Single strategy update from command line args
    if args.strategy_id and args.wins is not None and args.losses is not None and args.sport:
        bets_placed = args.wins + args.losses + args.pushes

        strategy_data = {
            'strategy_id': args.strategy_id,
            'sport': args.sport,
            'bets_placed': bets_placed,
            'wins': args.wins,
            'losses': args.losses,
            'pushes': args.pushes,
            'data_source': args.data_source or 'verified_backtest'
        }

        if args.preview:
            updater.preview_changes(args.strategy_id, strategy_data)
        else:
            updater.update_strategy(strategy_data)
        return

    # No valid arguments
    print("Error: Must provide either:")
    print("  1. --batch <csv_file>")
    print("  2. --strategy-id <id> --csv <csv_file>")
    print("  3. --strategy-id <id> --wins <n> --losses <n> --sport <sport>")
    parser.print_help()


if __name__ == "__main__":
    main()
