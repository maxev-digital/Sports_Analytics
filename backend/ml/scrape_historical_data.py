"""
Quick script to scrape 2023-24 NHL season goalie pull data

Run this to populate the database with historical patterns
"""

import sys
import os

# Add data_collection to path
sys.path.append(os.path.dirname(__file__))

from data_collection.nhl_historical_scraper import NHLHistoricalScraper


def main():
    """Run historical data scraper"""
    print("\n" + "=" * 80)
    print(" NHL GOALIE PULL HISTORICAL DATA SCRAPER")
    print("=" * 80)
    print("\nThis will scrape the entire 2023-24 NHL season for goalie pull events.")
    print("Expected time: ~45-60 minutes (1,312 games)")
    print("\nOptions:")
    print("  1. Test mode (10 games) - ~30 seconds")
    print("  2. Sample mode (100 games) - ~5 minutes")
    print("  3. Full season (1,312 games) - ~45-60 minutes")
    print("\nEnter choice (1/2/3): ", end="")

    try:
        choice = input().strip()

        scraper = NHLHistoricalScraper()

        if choice == "1":
            print("\n🧪 Running in TEST mode (10 games)...")
            scraper.scrape_season(season="20232024", max_games=10)

        elif choice == "2":
            print("\n📊 Running in SAMPLE mode (100 games)...")
            scraper.scrape_season(season="20232024", max_games=100)

        elif choice == "3":
            print("\n🏒 Running FULL SEASON scrape (1,312 games)...")
            print("⚠️  This will take 45-60 minutes. Press Ctrl+C to cancel.\n")
            scraper.scrape_season(season="20232024")

        else:
            print("Invalid choice. Exiting.")
            return

        print("\n✅ Scraping complete! Database is ready for ML predictions.")
        print("\nNext steps:")
        print("  1. Start backend: cd backend && python main.py")
        print("  2. Test API: curl http://localhost:8000/api/ml/goalie-pull/team-analysis/Boston%20Bruins")

    except KeyboardInterrupt:
        print("\n\n⏹️  Scraping canceled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
