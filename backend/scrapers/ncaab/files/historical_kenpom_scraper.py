#!/usr/bin/env python3
"""
Historical KenPom Data Scraper - 2024 Season
Gets previous season's KenPom ratings for backtesting
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

class HistoricalKenPomScraper:
    def __init__(self, email, password, headless=False):
        self.email = email
        self.password = password
        self.base_url = "https://kenpom.com"
        self.driver = None
        self.headless = headless
    
    def setup_driver(self):
        """Set up Chrome WebDriver"""
        print("🔧 Setting up Chrome browser...")
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome browser ready")
            return True
        except Exception as e:
            print(f"❌ Failed to start Chrome: {str(e)}")
            return False
    
    def login(self):
        """Login to KenPom"""
        print("🔐 Logging into KenPom...")
        
        try:
            self.driver.get(self.base_url)
            time.sleep(2)
            
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            
            password_field = self.driver.find_element(By.NAME, "password")
            submit_button = self.driver.find_element(By.NAME, "submit")
            
            email_field.clear()
            email_field.send_keys(self.email)
            time.sleep(0.5)
            
            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(0.5)
            
            submit_button.click()
            time.sleep(3)
            
            page_source = self.driver.page_source
            
            if 'Log Out' in page_source or 'Logout' in page_source:
                print("✅ Successfully logged into KenPom")
                return True
            else:
                print("⚠️ Login status unclear - attempting to proceed...")
                return True
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
    
    def scrape_historical_season(self, year=2024):
        """
        Scrape KenPom ratings for a historical season
        
        Args:
            year: Season year (e.g., 2024 for 2023-24 season)
        """
        print(f"📊 Scraping KenPom ratings for {year-1}-{year} season...")
        
        try:
            # Navigate to historical ratings (format: index.php?y=2024)
            url = f"{self.base_url}/index.php?y={year}"
            print(f"   URL: {url}")
            
            self.driver.get(url)
            time.sleep(3)
            
            # Get page source and parse with pandas
            from io import StringIO
            page_source = self.driver.page_source
            
            dfs = pd.read_html(StringIO(page_source))
            
            if not dfs:
                print("❌ No tables found on page")
                return None
            
            df = dfs[0]
            
            # Handle MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(-1)
            
            df.columns = df.columns.str.strip()
            
            # Make column names unique (handle duplicates)
            cols = pd.Series(df.columns)
            for dup in cols[cols.duplicated()].unique():
                dup_indices = [i for i, x in enumerate(cols) if x == dup]
                for i, idx in enumerate(dup_indices):
                    if i > 0:
                        cols.iloc[idx] = f"{dup}_{i}"
            
            df.columns = cols.tolist()
            
            print(f"   Detected {len(df.columns)} columns")
            
            # Create mapping by position (KenPom structure)
            column_mapping = {}
            
            if len(df.columns) > 0: column_mapping[df.columns[0]] = 'Rank'
            if len(df.columns) > 1: column_mapping[df.columns[1]] = 'Team'
            if len(df.columns) > 2: column_mapping[df.columns[2]] = 'Conference'
            if len(df.columns) > 3: column_mapping[df.columns[3]] = 'Record'
            if len(df.columns) > 4: column_mapping[df.columns[4]] = 'AdjEM'
            
            # Find offensive efficiency (skip columns with underscores)
            for i in range(5, min(8, len(df.columns))):
                col_str = str(df.columns[i]).lower()
                if '_' not in col_str:
                    if 'ortg' in col_str or 'adjo' in col_str:
                        column_mapping[df.columns[i]] = 'AdjOffEff'
                        break
            
            # Find defensive efficiency
            for i in range(6, min(10, len(df.columns))):
                col_str = str(df.columns[i]).lower()
                if '_' not in col_str:
                    if 'drtg' in col_str or 'adjd' in col_str:
                        column_mapping[df.columns[i]] = 'AdjDefEff'
                        break
            
            # Find tempo
            for i in range(9, min(12, len(df.columns))):
                col_str = str(df.columns[i]).lower()
                if '_' not in col_str:
                    if 'adjt' in col_str or 'tempo' in col_str:
                        column_mapping[df.columns[i]] = 'AdjTempo'
                        break
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Keep essential columns
            essential_cols = ['Rank', 'Team', 'Conference', 'Record', 'AdjEM', 'AdjOffEff', 'AdjDefEff', 'AdjTempo']
            available_cols = [col for col in essential_cols if col in df.columns]
            
            # Verify critical columns
            critical_missing = []
            for col in ['Team', 'AdjTempo', 'AdjOffEff', 'AdjDefEff']:
                if col not in df.columns:
                    critical_missing.append(col)
            
            if critical_missing:
                print(f"   ❌ MISSING CRITICAL COLUMNS: {critical_missing}")
                return None
            
            df = df[available_cols]
            
            # Convert numeric columns
            numeric_cols = ['Rank', 'AdjEM', 'AdjOffEff', 'AdjDefEff', 'AdjTempo']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove rows with NaN in critical columns
            df = df.dropna(subset=['Team', 'AdjTempo', 'AdjOffEff', 'AdjDefEff'])
            
            print(f"\n✅ Successfully scraped {len(df)} teams")
            
            if len(df) > 0:
                print(f"📈 Tempo range: {df['AdjTempo'].min():.1f} - {df['AdjTempo'].max():.1f}")
                print(f"📈 OffEff range: {df['AdjOffEff'].min():.1f} - {df['AdjOffEff'].max():.1f}")
                print(f"📈 DefEff range: {df['AdjDefEff'].min():.1f} - {df['AdjDefEff'].max():.1f}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error scraping {year} season: {str(e)}")
            import traceback
            print(f"   Details: {traceback.format_exc()}")
            return None
    
    def save_to_csv(self, df, year, output_dir='backend/data/historical'):
        """Save historical data to CSV"""
        if df is None or df.empty:
            print("⚠️ No data to save")
            return None
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/kenpom_{year}_season_{timestamp}.csv"
        
        df.to_csv(filename, index=False)
        print(f"💾 Saved: {filename}")
        
        return filename
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            print("🔒 Browser closed")
    
    def run(self, year=2024):
        """Main execution flow"""
        if not self.setup_driver():
            return None
        
        try:
            if not self.login():
                self.close()
                return None
            
            time.sleep(2)
            
            df = self.scrape_historical_season(year=year)
            
            if df is not None:
                saved_file = self.save_to_csv(df, year=year)
                if saved_file:
                    print(f"\n✅ CSV FILE CREATED: {saved_file}")
            
            return df
            
        finally:
            self.close()


def main():
    """Test function"""
    print("="*70)
    print("HISTORICAL KENPOM SCRAPER - 2024 SEASON")
    print("="*70)
    print("\n⚠️ This scraper gets LAST SEASON's data for backtesting")
    print("")
    
    email = input("Enter KenPom email: ").strip()
    password = input("Enter KenPom password: ").strip()
    
    if not email or not password:
        print("❌ Credentials required")
        return
    
    headless_input = input("\nRun browser in background (y/N)? ").strip().lower()
    headless = headless_input == 'y'
    
    # You can also scrape multiple seasons
    print("\nWhich season do you want to scrape?")
    print("  2024 = 2023-24 season (most recent complete season)")
    print("  2023 = 2022-23 season")
    print("  etc.")
    year_input = input("\nEnter year (default: 2024): ").strip()
    year = int(year_input) if year_input else 2024
    
    scraper = HistoricalKenPomScraper(email=email, password=password, headless=headless)
    df = scraper.run(year=year)
    
    if df is not None:
        print("\n" + "="*70)
        print(f"TOP 10 TEAMS ({year-1}-{year} SEASON):")
        print("="*70)
        display_cols = ['Rank', 'Team', 'Conference', 'AdjTempo', 'AdjOffEff', 'AdjDefEff']
        available_cols = [col for col in display_cols if col in df.columns]
        print(df[available_cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
