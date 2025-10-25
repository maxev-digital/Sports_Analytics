#!/usr/bin/env python3
"""
Automated Historical Closing Lines Scraper
Non-interactive version for automated execution
"""

import sys
sys.path.insert(0, 'backend')

from historical_closing_scraper import HistoricalClosingLinesScraper
from config import ODDS_API_KEY

def main():
    print("="*70)
    print("AUTOMATED HISTORICAL CLOSING LINES SCRAPER")
    print("="*70)
    print(f"Season: 2023-2024")
    print(f"API Key: {ODDS_API_KEY[:10]}...")
    print("")

    # Initialize scraper
    scraper = HistoricalClosingLinesScraper(
        api_key=ODDS_API_KEY,
        season_year=2024
    )

    # Scrape season (auto-confirm)
    closing_lines_df = scraper.scrape_season(save_frequency=10, auto_confirm=True)

    if closing_lines_df is not None and len(closing_lines_df) > 0:
        # Save raw closing lines
        closing_file = scraper.save_results(
            closing_lines_df,
            output_dir='backend/data/historical'
        )

        # Match with actual results
        matched_df = scraper.match_with_actual_results(closing_lines_df)

        if matched_df is not None and len(matched_df) > 0:
            # Save matched dataset for analysis
            analysis_file = scraper.save_results(matched_df)

            print("\n" + "="*70)
            print(" SUCCESS!")
            print("="*70)
            print(f"\nFiles created:")
            print(f"1. Raw closing lines: {closing_file}")
            print(f"2. Matched with actuals: {analysis_file}")
            print(f"\n Ready for regression analysis!")
            print(f"   - {len(matched_df)} games with closing lines + actual results")
            return True
        else:
            print("\nWARNING: Could not match closing lines with actual results")
            return False
    else:
        print("\nERROR: No closing lines retrieved")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
