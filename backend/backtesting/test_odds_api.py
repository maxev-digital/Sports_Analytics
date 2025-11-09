"""
Test script for The Odds API historical odds client
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

# Add data_sources to path
sys.path.append(str(Path(__file__).parent))

from data_sources.odds_api_historical import OddsAPIHistoricalClient


def main():
    """Test The Odds API with a few recent dates"""

    print("\n" + "="*60)
    print("TESTING THE ODDS API - HISTORICAL DATA ACCESS")
    print("="*60)

    # Initialize client
    try:
        client = OddsAPIHistoricalClient()
        print("[OK] Client initialized with API key")
    except ValueError as e:
        print(f"[ERROR] {e}")
        print("\nMake sure ODDS_API_KEY is set in backend/.env")
        return

    # Test with recent dates (last 7 days)
    print("\nTesting recent historical data availability...")
    print("Note: The Odds API may have limited historical access")
    print("="*60 + "\n")

    test_dates = [
        (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),  # Yesterday
        (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),  # 1 week ago
        (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),  # 1 month ago
    ]

    for date in test_dates:
        print(f"\nTesting date: {date}")
        print("-" * 40)

        odds = client.get_historical_odds(
            sport='basketball_nba',
            date=date,
            markets='totals'
        )

        if odds:
            print(f"[OK] Found {len(odds)} games with odds")
            if len(odds) > 0:
                game = odds[0]
                print(f"\nSample game:")
                print(f"  {game.get('away_team')} @ {game.get('home_team')}")
                print(f"  Bookmakers: {len(game.get('bookmakers', []))}")
                if game.get('bookmakers'):
                    bm = game['bookmakers'][0]
                    print(f"  Sample bookmaker: {bm.get('key')}")
        else:
            print(f"[WARNING] No odds data available for {date}")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nNOTE: The Odds API historical endpoint availability:")
    print("- Free tier: Usually only recent data (last few days)")
    print("- Paid tier: May have extended historical access")
    print("- For 3+ years of historical data, consider SBR scraper")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
