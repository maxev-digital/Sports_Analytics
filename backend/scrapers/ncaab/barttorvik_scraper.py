#!/usr/bin/env python3
"""
Barttorvik.com NCAAB Scraper - Alternative to KenPom
Free, public NCAAB analytics API - more reliable than scraping KenPom

Barttorvik provides similar metrics to KenPom:
- Adjusted Offensive Efficiency (AdjOE)
- Adjusted Defensive Efficiency (AdjDE)
- Adjusted Tempo
- NET Rankings and more

Data is freely available without login required.
"""

import requests
import pandas as pd
from datetime import datetime
import os

class BartttorvikScraper:
    """Scraper for Barttorvik NCAAB analytics"""

    def __init__(self):
        self.base_url = "https://barttorvik.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_current_season_ratings(self):
        """
        Fetch current season team ratings from Barttorvik
        Scrapes the main ratings page which is publicly accessible

        Returns:
            pandas.DataFrame with columns matching KenPom format
        """
        print("Fetching Barttorvik ratings...")

        try:
            # Get current year
            current_year = datetime.now().year
            season_year = current_year if datetime.now().month >= 11 else current_year

            # Barttorvik main ratings page
            url = f"{self.base_url}?year={season_year}"
            print(f"Fetching from: {url}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Parse HTML tables using pandas
            tables = pd.read_html(response.text)

            if not tables:
                print("ERROR: No tables found in Barttorvik page")
                return None

            # The main ratings table is usually the largest table
            df = max(tables, key=len)
            print(f"✅ Retrieved {len(df)} teams from Barttorvik")

            # Convert to KenPom-compatible format
            df_kenpom = self._convert_to_kenpom_format(df)

            return df_kenpom

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Network error fetching Barttorvik data: {e}")
            return None
        except ValueError as e:
            print(f"ERROR: Could not parse Barttorvik page: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Failed to fetch Barttorvik data: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _convert_to_kenpom_format(self, df):
        """
        Convert Barttorvik data to KenPom-compatible format

        Mapping (case-insensitive column names):
        - barthag/BARTHAGRank -> AdjEM (adjusted efficiency margin)
        - AdjOE/AdjO -> AdjOffEff (adjusted offensive efficiency)
        - AdjDE/AdjD -> AdjDefEff (adjusted defensive efficiency)
        - AdjT/AdjTempo -> AdjTempo (adjusted tempo)
        """
        print("Converting Barttorvik data to KenPom format...")
        print(f"Input columns: {list(df.columns)}")

        # Make column names lowercase for easier matching
        df.columns = df.columns.str.lower().str.strip()

        # Try to find the right columns (Barttorvik uses various formats)
        team_col = next((c for c in df.columns if 'team' in c or 'school' in c), df.columns[1])
        conf_col = next((c for c in df.columns if 'conf' in c), None)
        record_col = next((c for c in df.columns if 'record' in c or 'w-l' in c), None)

        # Efficiency columns
        adjoe_col = next((c for c in df.columns if 'adjo' in c), None)
        adjde_col = next((c for c in df.columns if 'adjd' in c and 'rank' not in c), None)
        adjt_col = next((c for c in df.columns if 'adjt' in c and 'rank' not in c), None)
        barthag_col = next((c for c in df.columns if 'barthag' in c and 'rank' not in c), None)

        # Build KenPom-format DataFrame
        df_converted = pd.DataFrame({
            'Rank': df.get(df.columns[0], range(1, len(df) + 1)),  # First column usually rank
            'Team': df[team_col].astype(str).str.strip() if team_col else ['Unknown'] * len(df),
            'Conference': df[conf_col].astype(str) if conf_col else [''] * len(df),
            'Record': df[record_col].astype(str) if record_col else ['0-0'] * len(df),
            'AdjEM': (df[barthag_col].astype(float) * 100) if barthag_col else [0] * len(df),
            'AdjOffEff': df[adjoe_col].astype(float) if adjoe_col else [100] * len(df),
            'AdjDefEff': df[adjde_col].astype(float) if adjde_col else [100] * len(df),
            'AdjTempo': df[adjt_col].astype(float) if adjt_col else [70] * len(df)
        })

        # Clean numeric columns
        for col in ['AdjEM', 'AdjOffEff', 'AdjDefEff', 'AdjTempo']:
            df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce').fillna(0)

        # Ensure Rank is sequential
        df_converted['Rank'] = range(1, len(df_converted) + 1)

        print(f"✅ Converted {len(df_converted)} teams")
        print(f"Output columns: {list(df_converted.columns)}")

        return df_converted

    def save_ratings(self, df, output_dir='backend/data/raw/ncaab'):
        """
        Save ratings to CSV file with timestamp

        Args:
            df: DataFrame with ratings
            output_dir: Directory to save file
        """
        if df is None or len(df) == 0:
            print("ERROR: No data to save")
            return None

        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'kenpom_ratings_{timestamp}.csv'  # Keep filename as kenpom for compatibility
        filepath = os.path.join(output_dir, filename)

        # Save to CSV
        df.to_csv(filepath, index=False)
        print(f"✅ Saved ratings to: {filepath}")

        return filepath

    def run(self):
        """
        Main method - fetch and save current season ratings

        Returns:
            pandas.DataFrame with ratings or None if failed
        """
        print("=" * 60)
        print("Starting Barttorvik scraper...")
        print("=" * 60)

        # Get ratings
        df = self.get_current_season_ratings()

        if df is not None and len(df) > 0:
            # Save to file
            filepath = self.save_ratings(df)

            # Show summary
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Teams scraped: {len(df)}")
            print(f"Features: {len(df.columns)}")
            print(f"\nTop 5 Teams:")
            print(df.head(5)[['Rank', 'Team', 'AdjEM', 'AdjOffEff', 'AdjDefEff']].to_string(index=False))

            if 'AdjTempo' in df.columns:
                print(f"\nTempo range: {df['AdjTempo'].min():.1f} - {df['AdjTempo'].max():.1f}")
            if 'AdjOffEff' in df.columns:
                print(f"OffEff range: {df['AdjOffEff'].min():.1f} - {df['AdjOffEff'].max():.1f}")
            if 'AdjDefEff' in df.columns:
                print(f"DefEff range: {df['AdjDefEff'].min():.1f} - {df['AdjDefEff'].max():.1f}")

            print("=" * 60)
            print("✅ Barttorvik scraper completed successfully")
            print("=" * 60)

            return df
        else:
            print("=" * 60)
            print("❌ Failed to scrape Barttorvik data")
            print("=" * 60)
            return None


if __name__ == "__main__":
    """Test the scraper"""
    scraper = BartttorvikScraper()
    df = scraper.run()

    if df is not None:
        print("\n✅ SUCCESS!")
        exit(0)
    else:
        print("\n❌ FAILED")
        exit(1)
