#!/usr/bin/env python3
"""
KenPom Scraper using Selenium (Real Browser) - FIXED VERSION
Properly extracts offensive efficiency, defensive efficiency, and tempo
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
from datetime import datetime
import os

class KenPomSeleniumScraper:
    def __init__(self, email=None, password=None, headless=False):
        """
        Initialize Selenium scraper for KenPom
        
        Args:
            email: KenPom login email
            password: KenPom login password
            headless: Run browser in background (True) or visible (False)
        """
        self.email = email
        self.password = password
        self.base_url = "https://kenpom.com"
        self.driver = None
        self.headless = headless
    
    def setup_driver(self):
        """Set up Chrome WebDriver with appropriate options"""
        print("Setting up Chrome browser...")
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # Make browser look more real
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # User agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("SUCCESS: Chrome browser ready")
            return True
        except Exception as e:
            print(f"ERROR: Failed to start Chrome: {str(e)}")
            print("\nSOLUTION:")
            print("   1. Install Chrome browser")
            print("   2. Download ChromeDriver from:")
            print("      https://chromedriver.chromium.org/downloads")
            print("   3. Add ChromeDriver to PATH")
            return False
    
    def login(self):
        """Login to KenPom using Selenium"""
        print("Logging into KenPom...")
        
        try:
            # Navigate to KenPom
            print("   Opening KenPom homepage...")
            self.driver.get(self.base_url)
            time.sleep(2)
            
            # Find login form
            print("   Looking for login form...")
            
            try:
                # Find email field
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "email"))
                )
                
                password_field = self.driver.find_element(By.NAME, "password")
                submit_button = self.driver.find_element(By.NAME, "submit")
                
                # Enter credentials
                print("   Entering credentials...")
                email_field.clear()
                email_field.send_keys(self.email)
                time.sleep(0.5)
                
                password_field.clear()
                password_field.send_keys(self.password)
                time.sleep(0.5)
                
                # Click submit
                print("   Submitting login...")
                submit_button.click()
                time.sleep(3)
                
                # Check if login was successful
                page_source = self.driver.page_source
                
                if 'Log Out' in page_source or 'Logout' in page_source:
                    print("SUCCESS: Successfully logged into KenPom")
                    return True
                elif 'Invalid' in page_source or 'invalid' in page_source:
                    print("ERROR: Login failed - Invalid credentials")
                    return False
                else:
                    print("WARNING: Login status unclear - attempting to proceed...")
                    return True
                    
            except Exception as e:
                print(f"ERROR: Could not find login form: {str(e)}")
                print("   KenPom page structure may have changed")
                return False

        except Exception as e:
            print(f"ERROR: Login error: {str(e)}")
            return False
    
    def scrape_ratings(self, year=None):
        """
        Scrape KenPom ratings for a specific season

        Args:
            year: Season year (2023, 2024, 2025, etc.). None = current season
        """
        if year:
            print(f"Scraping KenPom ratings for {year} season...")
            url = f"{self.base_url}/index.php?y={year}"
        else:
            print("Scraping KenPom ratings (current season)...")
            url = f"{self.base_url}/index.php"

        try:
            # Navigate to ratings page
            self.driver.get(url)
            time.sleep(3)
            
            # Get page source and parse with pandas
            from io import StringIO
            page_source = self.driver.page_source
            
            # Use pandas to read HTML tables
            dfs = pd.read_html(StringIO(page_source))
            
            if not dfs:
                print("ERROR: No tables found on page")
                return None
            
            # The main ratings table is usually the first one
            df = dfs[0]
            
            # Handle MultiIndex columns (KenPom uses multi-level headers)
            if isinstance(df.columns, pd.MultiIndex):
                # Take the last level of column names (most specific)
                df.columns = df.columns.get_level_values(-1)
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Make column names unique (KenPom has duplicates like ORtg, ORtg for stat and rank)
            # pandas.read_html might create duplicates, so we need to make them unique
            df.columns = pd.Series(df.columns).fillna('Unknown')
            
            # Add suffixes to duplicates
            cols = pd.Series(df.columns)
            for dup in cols[cols.duplicated()].unique():
                dup_indices = [i for i, x in enumerate(cols) if x == dup]
                for i, idx in enumerate(dup_indices):
                    if i > 0:  # Keep first occurrence, rename others
                        cols.iloc[idx] = f"{dup}_{i}"
            
            df.columns = cols.tolist()
            
            print(f"   Detected {len(df.columns)} columns")
            print(f"   First 12 columns (after dedup): {list(df.columns[:12])}")
            
            # KenPom standard format (by position is most reliable):
            # 0=Rank, 1=Team, 2=Conf, 3=W-L, 4=AdjEM, 5=AdjO, 6=AdjO Rank, 7=AdjD, 8=AdjD Rank, 9=AdjT
            
            # Create mapping by position
            column_mapping = {}
            
            if len(df.columns) > 0: column_mapping[df.columns[0]] = 'Rank'
            if len(df.columns) > 1: column_mapping[df.columns[1]] = 'Team'
            if len(df.columns) > 2: column_mapping[df.columns[2]] = 'Conference'
            if len(df.columns) > 3: column_mapping[df.columns[3]] = 'Record'
            if len(df.columns) > 4: column_mapping[df.columns[4]] = 'AdjEM'
            
            # Find offensive efficiency (look for first ORtg or AdjO without _1 suffix)
            off_found = False
            for i in range(5, min(8, len(df.columns))):
                col_str = str(df.columns[i]).lower()
                # Skip duplicates (they have _1, _2 suffix)
                if '_' in col_str:
                    continue
                if 'ortg' in col_str or 'adjo' in col_str:
                    column_mapping[df.columns[i]] = 'AdjOffEff'
                    print(f"   Found offensive efficiency at column {i}: {df.columns[i]}")
                    off_found = True
                    break
            
            if not off_found and len(df.columns) > 5:
                # Default to position 5 if it doesn't have underscore suffix
                if '_' not in str(df.columns[5]):
                    column_mapping[df.columns[5]] = 'AdjOffEff'
                    print(f"   WARNING: Assumed offensive efficiency at column 5: {df.columns[5]}")
            
            # Find defensive efficiency (look for first DRtg or AdjD without _1 suffix)
            def_found = False
            for i in range(6, min(10, len(df.columns))):
                col_str = str(df.columns[i]).lower()
                # Skip duplicates (they have _1, _2 suffix)
                if '_' in col_str:
                    continue
                if 'drtg' in col_str or 'adjd' in col_str:
                    column_mapping[df.columns[i]] = 'AdjDefEff'
                    print(f"   Found defensive efficiency at column {i}: {df.columns[i]}")
                    def_found = True
                    break
            
            if not def_found and len(df.columns) > 7:
                # Default to position 7 if it doesn't have underscore suffix
                if '_' not in str(df.columns[7]):
                    column_mapping[df.columns[7]] = 'AdjDefEff'
                    print(f"   WARNING: Assumed defensive efficiency at column 7: {df.columns[7]}")
            
            # Find tempo (look for first AdjT or Tempo without _1 suffix)
            tempo_found = False
            for i in range(9, min(12, len(df.columns))):
                col_str = str(df.columns[i]).lower()
                # Skip duplicates (they have _1, _2 suffix)
                if '_' in col_str:
                    continue
                if 'adjt' in col_str or 'tempo' in col_str:
                    column_mapping[df.columns[i]] = 'AdjTempo'
                    print(f"   Found tempo at column {i}: {df.columns[i]}")
                    tempo_found = True
                    break
            
            if not tempo_found and len(df.columns) > 9:
                # Default to position 9 if it doesn't have underscore suffix
                if '_' not in str(df.columns[9]):
                    column_mapping[df.columns[9]] = 'AdjTempo'
                    print(f"   WARNING: Assumed tempo at column 9: {df.columns[9]}")
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Extract additional advanced stats for ML
            # Look for eFG% (Effective Field Goal %)
            for i, col in enumerate(df.columns):
                col_str = str(col).lower()
                if 'efg' in col_str and '_' not in col_str and 'AdjOffEfg' not in column_mapping.values():
                    column_mapping[col] = 'AdjOffEfg'
                    print(f"   Found offensive eFG% at column {i}: {col}")
                    break

            # Look for defensive eFG%
            for i, col in enumerate(df.columns):
                col_str = str(col).lower()
                if 'efg' in col_str and 'd' in col_str and '_' not in col_str and 'AdjDefEfg' not in column_mapping.values():
                    column_mapping[col] = 'AdjDefEfg'
                    print(f"   Found defensive eFG% at column {i}: {col}")
                    break

            # Look for TO% (Turnover %)
            for i, col in enumerate(df.columns):
                col_str = str(col).lower()
                if ('to' in col_str or 'turnover' in col_str) and 'o' in col_str and '_' not in col_str and 'OffTO' not in column_mapping.values():
                    column_mapping[col] = 'OffTO'
                    print(f"   Found offensive TO% at column {i}: {col}")
                    break

            # Look for defensive TO%
            for i, col in enumerate(df.columns):
                col_str = str(col).lower()
                if ('to' in col_str or 'turnover' in col_str) and 'd' in col_str and '_' not in col_str and 'DefTO' not in column_mapping.values():
                    column_mapping[col] = 'DefTO'
                    print(f"   Found defensive TO% at column {i}: {col}")
                    break

            # Look for ORB% (Offensive Rebound %)
            for i, col in enumerate(df.columns):
                col_str = str(col).lower()
                if 'orb' in col_str and '_' not in col_str and 'OffORB' not in column_mapping.values():
                    column_mapping[col] = 'OffORB'
                    print(f"   Found offensive rebound% at column {i}: {col}")
                    break

            # Look for DRB% (Defensive Rebound %)
            for i, col in enumerate(df.columns):
                col_str = str(col).lower()
                if 'drb' in col_str and '_' not in col_str and 'DefDRB' not in column_mapping.values():
                    column_mapping[col] = 'DefDRB'
                    print(f"   Found defensive rebound% at column {i}: {col}")
                    break

            # Apply all column mappings
            df = df.rename(columns=column_mapping)

            # Keep essential + advanced columns
            essential_cols = [
                'Rank', 'Team', 'Conference', 'Record', 'AdjEM',
                'AdjOffEff', 'AdjDefEff', 'AdjTempo',
                # Advanced stats for ML
                'AdjOffEfg', 'AdjDefEfg',
                'OffTO', 'DefTO',
                'OffORB', 'DefDRB'
            ]
            available_cols = [col for col in essential_cols if col in df.columns]

            print(f"\n   Extracted columns: {available_cols}")
            
            # Verify critical stats
            critical_missing = []
            for col in ['Team', 'AdjTempo', 'AdjOffEff', 'AdjDefEff']:
                if col not in df.columns:
                    critical_missing.append(col)
            
            if critical_missing:
                print(f"\n   ERROR: MISSING CRITICAL COLUMNS: {critical_missing}")
                print(f"   Available after rename: {list(df.columns)}")
                print("\n   This will prevent accurate predictions!")
                return None
            
            # Select columns
            df = df[available_cols]

            # Convert numeric columns (including new advanced stats)
            numeric_cols = [
                'Rank', 'AdjEM', 'AdjOffEff', 'AdjDefEff', 'AdjTempo',
                'AdjOffEfg', 'AdjDefEfg', 'OffTO', 'DefTO', 'OffORB', 'DefDRB'
            ]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove any rows with NaN in critical columns
            df = df.dropna(subset=['Team', 'AdjTempo', 'AdjOffEff', 'AdjDefEff'])
            
            print(f"\nSUCCESS: Successfully scraped {len(df)} teams")

            # Show ranges for validation
            if len(df) > 0:
                print(f"\nCore Stats:")
                print(f"   Tempo: {df['AdjTempo'].min():.1f} - {df['AdjTempo'].max():.1f}")
                print(f"   OffEff: {df['AdjOffEff'].min():.1f} - {df['AdjOffEff'].max():.1f}")
                print(f"   DefEff: {df['AdjDefEff'].min():.1f} - {df['AdjDefEff'].max():.1f}")

                # Show advanced stats if available
                if 'AdjOffEfg' in df.columns and df['AdjOffEfg'].notna().any():
                    print(f"\nAdvanced Stats (for ML):")
                    print(f"   Off eFG%: {df['AdjOffEfg'].min():.1f} - {df['AdjOffEfg'].max():.1f}")
                if 'AdjDefEfg' in df.columns and df['AdjDefEfg'].notna().any():
                    print(f"   Def eFG%: {df['AdjDefEfg'].min():.1f} - {df['AdjDefEfg'].max():.1f}")
                if 'OffTO' in df.columns and df['OffTO'].notna().any():
                    print(f"   Off TO%: {df['OffTO'].min():.1f} - {df['OffTO'].max():.1f}")
                if 'DefTO' in df.columns and df['DefTO'].notna().any():
                    print(f"   Def TO%: {df['DefTO'].min():.1f} - {df['DefTO'].max():.1f}")
                if 'OffORB' in df.columns and df['OffORB'].notna().any():
                    print(f"   Off ORB%: {df['OffORB'].min():.1f} - {df['OffORB'].max():.1f}")
                if 'DefDRB' in df.columns and df['DefDRB'].notna().any():
                    print(f"   Def DRB%: {df['DefDRB'].min():.1f} - {df['DefDRB'].max():.1f}")
            
            return df
            
        except Exception as e:
            print(f"ERROR: Error scraping ratings: {str(e)}")
            import traceback
            print(f"   Details: {traceback.format_exc()}")
            return None
    
    def save_to_csv(self, df, output_dir='backend/data/raw/ncaab', year=None):
        """Save scraped data to CSV"""
        if df is None or df.empty:
            print("WARNING: No data to save")
            return None

        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if year:
            filename = f"{output_dir}/kenpom_{year}_{timestamp}.csv"
        else:
            filename = f"{output_dir}/kenpom_ratings_{timestamp}.csv"

        df.to_csv(filename, index=False)
        print(f"Saved: {filename}")

        return filename
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("Browser closed")
    
    def run(self, year=None):
        """Main execution flow for single season"""
        if not self.email or not self.password:
            print("ERROR: KenPom credentials not provided")
            return None

        # Set up browser
        if not self.setup_driver():
            return None

        try:
            # Login
            if not self.login():
                self.close()
                return None

            # Wait a bit after login
            time.sleep(2)

            # Scrape ratings
            df = self.scrape_ratings(year)

            if df is not None and not df.empty:
                # Save to CSV
                saved_file = self.save_to_csv(df, year=year)
                if saved_file:
                    print(f"\nSUCCESS: CSV FILE CREATED: {saved_file}")
                else:
                    print("\nWARNING: CSV save may have failed")
            else:
                print("\nERROR: No data to save")

            return df

        finally:
            # Always close browser
            self.close()

    def run_multiple_seasons(self, years=[2023, 2024, 2025]):
        """
        Scrape multiple seasons in one session (efficient)

        Args:
            years: List of season years to scrape

        Returns:
            Dict of {year: dataframe}
        """
        if not self.email or not self.password:
            print("ERROR: KenPom credentials not provided")
            return None

        # Set up browser
        if not self.setup_driver():
            return None

        results = {}

        try:
            # Login once
            if not self.login():
                self.close()
                return None

            print(f"\nScraping {len(years)} seasons: {years}")

            # Scrape each season
            for year in years:
                print(f"\n{'='*70}")
                print(f"SEASON: {year}")
                print(f"{'='*70}")

                # Wait between requests
                time.sleep(3)

                # Scrape this season
                df = self.scrape_ratings(year)

                if df is not None and not df.empty:
                    # Save to CSV
                    saved_file = self.save_to_csv(df, year=year)
                    results[year] = df
                    print(f"SUCCESS: {year} season: {len(df)} teams scraped")
                else:
                    print(f"ERROR: {year} season: No data")
                    results[year] = None

            return results

        finally:
            # Always close browser
            self.close()


def main():
    """Test function"""
    print("="*70)
    print("KENPOM SELENIUM SCRAPER - NCAA BASKETBALL")
    print("="*70)
    print("\nWARNING: This scraper uses a real Chrome browser")
    print("Requirements:")
    print("  1. Chrome browser installed")
    print("  2. ChromeDriver installed")
    print("  3. pip install selenium")
    print("")
    
    # Get credentials
    email = input("Enter KenPom email: ").strip()
    password = input("Enter KenPom password: ").strip()
    
    if not email or not password:
        print("ERROR: Credentials required")
        return
    
    # Ask about headless mode
    headless_input = input("\nRun browser in background (y/N)? ").strip().lower()
    headless = headless_input == 'y'
    
    scraper = KenPomSeleniumScraper(email=email, password=password, headless=headless)
    df = scraper.run()
    
    if df is not None:
        print("\n" + "="*70)
        print("TOP 10 TEAMS:")
        print("="*70)
        display_cols = [
            'Rank', 'Team', 'Conference',
            'AdjTempo', 'AdjOffEff', 'AdjDefEff',
            'AdjOffEfg', 'AdjDefEfg', 'OffTO', 'DefTO'
        ]
        available_cols = [col for col in display_cols if col in df.columns]
        print(df[available_cols].head(10).to_string(index=False))

        print(f"\nSUCCESS: Total features extracted: {len(df.columns)}")
        print(f"   Features: {', '.join(df.columns.tolist())}")


if __name__ == "__main__":
    main()