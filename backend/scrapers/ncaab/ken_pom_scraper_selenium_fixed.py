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
        print("🔧 Setting up Chrome browser...")
        
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
            print("✅ Chrome browser ready")
            return True
        except Exception as e:
            print(f"❌ Failed to start Chrome: {str(e)}")
            print("\n💡 SOLUTION:")
            print("   1. Install Chrome browser")
            print("   2. Download ChromeDriver from:")
            print("      https://chromedriver.chromium.org/downloads")
            print("   3. Add ChromeDriver to PATH")
            return False
    
    def login(self):
        """Login to KenPom using Selenium"""
        print("🔐 Logging into KenPom...")
        
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
                    print("✅ Successfully logged into KenPom")
                    return True
                elif 'Invalid' in page_source or 'invalid' in page_source:
                    print("❌ Login failed - Invalid credentials")
                    return False
                else:
                    print("⚠️ Login status unclear - attempting to proceed...")
                    return True
                    
            except Exception as e:
                print(f"❌ Could not find login form: {str(e)}")
                print("   KenPom page structure may have changed")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
    
    def scrape_ratings(self):
        """Scrape current season ratings from KenPom"""
        print("📊 Scraping KenPom ratings...")
        
        try:
            # Navigate to main ratings page
            self.driver.get(f"{self.base_url}/index.php")
            time.sleep(3)
            
            # Get page source and parse with pandas
            from io import StringIO
            page_source = self.driver.page_source
            
            # Use pandas to read HTML tables
            dfs = pd.read_html(StringIO(page_source))
            
            if not dfs:
                print("❌ No tables found on page")
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
                    print(f"   ✓ Found offensive efficiency at column {i}: {df.columns[i]}")
                    off_found = True
                    break
            
            if not off_found and len(df.columns) > 5:
                # Default to position 5 if it doesn't have underscore suffix
                if '_' not in str(df.columns[5]):
                    column_mapping[df.columns[5]] = 'AdjOffEff'
                    print(f"   ⚠️  Assumed offensive efficiency at column 5: {df.columns[5]}")
            
            # Find defensive efficiency (look for first DRtg or AdjD without _1 suffix)
            def_found = False
            for i in range(6, min(10, len(df.columns))):
                col_str = str(df.columns[i]).lower()
                # Skip duplicates (they have _1, _2 suffix)
                if '_' in col_str:
                    continue
                if 'drtg' in col_str or 'adjd' in col_str:
                    column_mapping[df.columns[i]] = 'AdjDefEff'
                    print(f"   ✓ Found defensive efficiency at column {i}: {df.columns[i]}")
                    def_found = True
                    break
            
            if not def_found and len(df.columns) > 7:
                # Default to position 7 if it doesn't have underscore suffix
                if '_' not in str(df.columns[7]):
                    column_mapping[df.columns[7]] = 'AdjDefEff'
                    print(f"   ⚠️  Assumed defensive efficiency at column 7: {df.columns[7]}")
            
            # Find tempo (look for first AdjT or Tempo without _1 suffix)
            tempo_found = False
            for i in range(9, min(12, len(df.columns))):
                col_str = str(df.columns[i]).lower()
                # Skip duplicates (they have _1, _2 suffix)
                if '_' in col_str:
                    continue
                if 'adjt' in col_str or 'tempo' in col_str:
                    column_mapping[df.columns[i]] = 'AdjTempo'
                    print(f"   ✓ Found tempo at column {i}: {df.columns[i]}")
                    tempo_found = True
                    break
            
            if not tempo_found and len(df.columns) > 9:
                # Default to position 9 if it doesn't have underscore suffix
                if '_' not in str(df.columns[9]):
                    column_mapping[df.columns[9]] = 'AdjTempo'
                    print(f"   ⚠️  Assumed tempo at column 9: {df.columns[9]}")
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Keep only essential columns
            essential_cols = ['Rank', 'Team', 'Conference', 'Record', 'AdjEM', 'AdjOffEff', 'AdjDefEff', 'AdjTempo']
            available_cols = [col for col in essential_cols if col in df.columns]
            
            print(f"\n   📋 Extracted columns: {available_cols}")
            
            # Verify critical stats
            critical_missing = []
            for col in ['Team', 'AdjTempo', 'AdjOffEff', 'AdjDefEff']:
                if col not in df.columns:
                    critical_missing.append(col)
            
            if critical_missing:
                print(f"\n   ❌ MISSING CRITICAL COLUMNS: {critical_missing}")
                print(f"   Available after rename: {list(df.columns)}")
                print("\n   This will prevent accurate predictions!")
                return None
            
            # Select columns
            df = df[available_cols]
            
            # Convert numeric columns
            numeric_cols = ['Rank', 'AdjEM', 'AdjOffEff', 'AdjDefEff', 'AdjTempo']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove any rows with NaN in critical columns
            df = df.dropna(subset=['Team', 'AdjTempo', 'AdjOffEff', 'AdjDefEff'])
            
            print(f"\n✅ Successfully scraped {len(df)} teams")
            
            # Show ranges for validation
            if len(df) > 0:
                print(f"📈 Tempo range: {df['AdjTempo'].min():.1f} - {df['AdjTempo'].max():.1f}")
                print(f"📈 OffEff range: {df['AdjOffEff'].min():.1f} - {df['AdjOffEff'].max():.1f}")
                print(f"📈 DefEff range: {df['AdjDefEff'].min():.1f} - {df['AdjDefEff'].max():.1f}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error scraping ratings: {str(e)}")
            import traceback
            print(f"   Details: {traceback.format_exc()}")
            return None
    
    def save_to_csv(self, df, output_dir='backend/data/raw/ncaab'):
        """Save scraped data to CSV"""
        if df is None or df.empty:
            print("⚠️ No data to save")
            return None
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/kenpom_ratings_{timestamp}.csv"
        
        df.to_csv(filename, index=False)
        print(f"💾 Saved: {filename}")
        
        return filename
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("🔒 Browser closed")
    
    def run(self):
        """Main execution flow"""
        if not self.email or not self.password:
            print("❌ KenPom credentials not provided")
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
            df = self.scrape_ratings()
            
            if df is not None and not df.empty:
                # Save to CSV
                saved_file = self.save_to_csv(df)
                if saved_file:
                    print(f"\n✅ CSV FILE CREATED: {saved_file}")
                else:
                    print("\n⚠️ Warning: CSV save may have failed")
            else:
                print("\n❌ No data to save")
            
            return df
            
        finally:
            # Always close browser
            self.close()


def main():
    """Test function"""
    print("="*70)
    print("KENPOM SELENIUM SCRAPER - NCAA BASKETBALL")
    print("="*70)
    print("\n⚠️ This scraper uses a real Chrome browser")
    print("Requirements:")
    print("  1. Chrome browser installed")
    print("  2. ChromeDriver installed")
    print("  3. pip install selenium")
    print("")
    
    # Get credentials
    email = input("Enter KenPom email: ").strip()
    password = input("Enter KenPom password: ").strip()
    
    if not email or not password:
        print("❌ Credentials required")
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
        display_cols = ['Rank', 'Team', 'Conference', 'AdjTempo', 'AdjOffEff', 'AdjDefEff']
        available_cols = [col for col in display_cols if col in df.columns]
        print(df[available_cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()