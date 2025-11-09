#!/usr/bin/env python3
"""
Scrape Historical KenPom Data for Last 2 Years

This will scrape 2023, 2024, and 2025 seasons to get training data
for the regression-to-mean XGBoost model.

Usage:
    python scrape_historical_kenpom.py
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ken_pom_scraper_selenium_fixed import KenPomSeleniumScraper


def main():
    print("="*70)
    print("HISTORICAL KENPOM DATA COLLECTION")
    print("="*70)
    print("\nThis will scrape 3 seasons: 2023, 2024, 2025")
    print("Estimated time: 2-3 minutes\n")

    # Your KenPom credentials
    EMAIL = "gte.apw@gmail.com"
    PASSWORD = "Thewrench1!"

    # Seasons to scrape (last 2+ years)
    SEASONS = [2023, 2024, 2025]

    print(f"Using account: {EMAIL}")
    print(f"Seasons: {SEASONS}\n")

    # Ask about headless mode
    headless_input = input("Run browser in background? (Y/n): ").strip().lower()
    headless = headless_input != 'n'

    print(f"\nBrowser mode: {'Background (headless)' if headless else 'Visible'}\n")

    # Create scraper
    scraper = KenPomSeleniumScraper(
        email=EMAIL,
        password=PASSWORD,
        headless=headless
    )

    # Scrape all seasons
    results = scraper.run_multiple_seasons(years=SEASONS)

    # Summary
    print("\n" + "="*70)
    print("SCRAPING COMPLETE!")
    print("="*70)

    if results:
        for year, df in results.items():
            if df is not None:
                print(f"SUCCESS {year}: {len(df)} teams")
            else:
                print(f"FAILED {year}: No data")

        print(f"\nFiles saved to: backend/data/raw/ncaab/")
        print(f"   - kenpom_2023_*.csv")
        print(f"   - kenpom_2024_*.csv")
        print(f"   - kenpom_2025_*.csv")

        print(f"\nNext step: Train XGBoost model with this data")
        print(f"   python backend/ml/ncaab_xgboost_quantile_trainer.py")
    else:
        print("FAILED: Scraping failed")

    return results


if __name__ == "__main__":
    main()
