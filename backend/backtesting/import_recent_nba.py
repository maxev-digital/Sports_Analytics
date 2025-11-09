"""
Quick script to import recent NBA games for backtesting
"""

from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from data_sources.espn_client import ESPNClient

def import_last_n_days(days: int = 7):
    """Import NBA games from last N days"""
    client = ESPNClient()

    end_date = datetime.now() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=days)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    print(f"Importing NBA games from {start_str} to {end_str}")
    games = client.import_date_range(start_str, end_str, save_to_db=True)

    print(f"\n[OK] Imported {len(games)} games")
    return games

if __name__ == "__main__":
    import_last_n_days(days=14)  # Last 2 weeks
