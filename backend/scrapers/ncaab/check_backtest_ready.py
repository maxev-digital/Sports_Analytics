#!/usr/bin/env python3
"""
NCAA Basketball Backtest Pre-Flight Check
Verifies all requirements are met before running backtest
"""

import os
import sys
import glob
import pandas as pd

def check_mark(condition):
    return "✅" if condition else "❌"

def print_header():
    print("="*70)
    print("NCAA BASKETBALL BACKTEST - PRE-FLIGHT CHECK")
    print("="*70)
    print("")

def check_config():
    """Check if config.py exists and has required values"""
    print("📋 STEP 1: Checking Configuration")
    print("-"*70)
    
    try:
        sys.path.insert(0, 'backend')
        from config import (
            GOOGLE_CREDENTIALS_PATH, GOOGLE_SHEET_ID,
            HOME_COURT_ADVANTAGE, LEAGUE_AVG_EFFICIENCY
        )
        
        print(f"   {check_mark(True)} config.py found")
        print(f"   {check_mark(GOOGLE_SHEET_ID != 'YOUR_SHEET_ID_HERE')} Google Sheet ID configured")
        print(f"   {check_mark(os.path.exists(GOOGLE_CREDENTIALS_PATH))} Google credentials found")
        print(f"   {check_mark(True)} Home court advantage: {HOME_COURT_ADVANTAGE}")
        print(f"   {check_mark(True)} League avg efficiency: {LEAGUE_AVG_EFFICIENCY}")
        
        return True
        
    except ImportError as e:
        print(f"   {check_mark(False)} config.py not found or incomplete")
        print(f"\n   💡 Run: python setup_ncaab.py")
        return False
    except Exception as e:
        print(f"   {check_mark(False)} Error loading config: {str(e)}")
        return False

def check_historical_data():
    """Check if historical data exists"""
    print("\n📊 STEP 2: Checking Historical Data")
    print("-"*70)
    
    historical_dir = "backend/data/historical"
    
    # Check KenPom data
    kenpom_pattern = f"{historical_dir}/kenpom_*_season_*.csv"
    kenpom_files = glob.glob(kenpom_pattern)
    
    kenpom_exists = len(kenpom_files) > 0
    print(f"   {check_mark(kenpom_exists)} Historical KenPom data")
    
    if kenpom_exists:
        latest_kenpom = max(kenpom_files)
        df = pd.read_csv(latest_kenpom)
        print(f"      File: {os.path.basename(latest_kenpom)}")
        print(f"      Teams: {len(df)}")
        
        # Verify columns
        required_cols = ['Team', 'AdjTempo', 'AdjOffEff', 'AdjDefEff']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"      ⚠️  Missing columns: {missing_cols}")
        else:
            print(f"      ✅ All required columns present")
    else:
        print(f"\n   💡 Get historical KenPom data:")
        print(f"      python historical_kenpom_scraper.py")
        print(f"      Email: gte.apw@gmail.com")
        print(f"      Password: Thewrench1!")
        print(f"      Year: 2024")
    
    # Check game results
    games_pattern = f"{historical_dir}/game_results_*_season_*.csv"
    games_files = glob.glob(games_pattern)
    
    games_exist = len(games_files) > 0
    print(f"\n   {check_mark(games_exist)} Historical game results")
    
    if games_exist:
        latest_games = max(games_files)
        df = pd.read_csv(latest_games)
        print(f"      File: {os.path.basename(latest_games)}")
        print(f"      Games: {len(df)}")
        
        # Verify columns
        required_cols = ['Home_Team', 'Away_Team', 'Actual_Total']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"      ⚠️  Missing columns: {missing_cols}")
        else:
            print(f"      ✅ All required columns present")
    else:
        print(f"\n   💡 Get historical game results:")
        print(f"      python game_results_scraper.py")
        print(f"      Year: 2024")
    
    return kenpom_exists and games_exist

def check_required_files():
    """Check if required scripts exist"""
    print("\n📁 STEP 3: Checking Required Files")
    print("-"*70)
    
    required_files = [
        ('Enhanced Sheets Uploader', 'ncaab_sheets_uploader_enhanced.py'),
        ('Backtest Runner', 'run_ncaab_backtest.py'),
        ('Prediction Model', 'backend/models/ncaab/totals_predictor.py'),
    ]
    
    all_exist = True
    
    for name, filepath in required_files:
        exists = os.path.exists(filepath)
        all_exist = all_exist and exists
        print(f"   {check_mark(exists)} {name}")
        if not exists:
            print(f"      Missing: {filepath}")
    
    return all_exist

def check_google_sheets():
    """Check Google Sheets connectivity"""
    print("\n☁️  STEP 4: Checking Google Sheets Access")
    print("-"*70)
    
    try:
        sys.path.insert(0, 'backend')
        from config import GOOGLE_CREDENTIALS_PATH, GOOGLE_SHEET_ID
        
        # Try to import gspread
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            print(f"   {check_mark(True)} Required packages installed")
        except ImportError:
            print(f"   {check_mark(False)} Missing packages")
            print(f"\n   💡 Install: pip install gspread oauth2client")
            return False
        
        # Check credentials file
        creds_exist = os.path.exists(GOOGLE_CREDENTIALS_PATH)
        print(f"   {check_mark(creds_exist)} Credentials file exists")
        
        if not creds_exist:
            print(f"\n   💡 Copy credentials from NBA/NFL project:")
            print(f"      Copy to: {GOOGLE_CREDENTIALS_PATH}")
            return False
        
        # Try to connect
        try:
            print(f"   🔄 Testing connection...")
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                GOOGLE_CREDENTIALS_PATH, scope)
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
            
            print(f"   {check_mark(True)} Connection successful!")
            print(f"      Sheet: {spreadsheet.title}")
            print(f"      Tabs: {len(spreadsheet.worksheets())}")
            
            return True
            
        except Exception as e:
            print(f"   {check_mark(False)} Connection failed: {str(e)}")
            print(f"\n   💡 Solutions:")
            print(f"      1. Verify Sheet ID in config.py")
            print(f"      2. Share sheet with service account (Editor access)")
            print(f"      3. Check credentials file is valid")
            return False
        
    except Exception as e:
        print(f"   {check_mark(False)} Error: {str(e)}")
        return False

def estimate_runtime():
    """Estimate how long backtest will take"""
    print("\n⏱️  STEP 5: Runtime Estimate")
    print("-"*70)
    
    historical_dir = "backend/data/historical"
    games_pattern = f"{historical_dir}/game_results_*_season_*.csv"
    games_files = glob.glob(games_pattern)
    
    if games_files:
        latest_games = max(games_files)
        df = pd.read_csv(latest_games)
        num_games = len(df)
        
        # Estimate: ~0.05 seconds per game + 30 seconds overhead
        estimated_seconds = (num_games * 0.05) + 30
        estimated_minutes = int(estimated_seconds / 60)
        
        print(f"   Games to process: {num_games:,}")
        print(f"   Estimated time: {estimated_minutes} minutes")
        
        if num_games > 3000:
            print(f"   ☕ Grab a coffee - this will take a few minutes!")
    else:
        print(f"   ⚠️  Cannot estimate - no game data found")

def print_summary(config_ok, data_ok, files_ok, sheets_ok):
    """Print final summary"""
    print("\n" + "="*70)
    print("PRE-FLIGHT CHECK SUMMARY")
    print("="*70)
    
    checks = [
        ("Configuration", config_ok),
        ("Historical Data", data_ok),
        ("Required Files", files_ok),
        ("Google Sheets", sheets_ok),
    ]
    
    all_passed = all(status for _, status in checks)
    
    for name, status in checks:
        print(f"   {check_mark(status)} {name}")
    
    print("\n" + "="*70)
    
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("\nYou're ready to run the backtest:")
        print("   python run_ncaab_backtest.py")
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("\nPlease fix the issues above before running backtest.")
        print("\nCommon solutions:")
        print("  • Missing config: python setup_ncaab.py")
        print("  • Missing data: python historical_kenpom_scraper.py")
        print("  • Missing data: python game_results_scraper.py")
        print("  • Sheets issue: Check sharing permissions")
    
    print("="*70)
    
    return all_passed

def main():
    """Run all checks"""
    print_header()
    
    config_ok = check_config()
    data_ok = check_historical_data()
    files_ok = check_required_files()
    sheets_ok = check_google_sheets()
    
    estimate_runtime()
    
    all_passed = print_summary(config_ok, data_ok, files_ok, sheets_ok)
    
    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
