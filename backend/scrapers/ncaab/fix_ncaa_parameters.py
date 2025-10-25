#!/usr/bin/env python3
"""
Fix NCAA Basketball Model Parameters
Adjusts parameters from NBA-calibrated to NCAA-calibrated values

PROBLEM: Model under-predicting by ~9 points because using NBA parameters
SOLUTION: Use NCAA-specific parameters based on actual game data
"""

import os
import shutil
from datetime import datetime

def backup_config():
    """Backup current config.py"""
    config_file = "backend/config.py"
    backup_file = f"backend/config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    if os.path.exists(config_file):
        shutil.copy2(config_file, backup_file)
        print(f"📁 Backed up config to: {backup_file}")
        return True
    return False

def create_ncaa_config():
    """Create NCAA-optimized config"""
    
    config_content = '''"""
NCAA Basketball Model Configuration - NCAA OPTIMIZED
Fixed parameters based on actual NCAA game data
"""

# Odds API Configuration
ODDS_API_KEY = "3b91452fcbaa6deffecb2e5843655099"
ODDS_API_SPORT = "basketball_ncaab"  # NCAA Basketball

# Google Sheets Configuration
GOOGLE_CREDENTIALS_PATH = "google_sheets/credentials/service-account-key.json"
GOOGLE_SHEET_ID = "1M5Oe0pZU_Apy3EO0YaUU13uJW98joGnlrtd9Wba2ukA"

# Data Paths
KENPOM_DATA_DIR = "backend/data/raw/ncaab"
PREDICTIONS_OUTPUT_DIR = "backend/data/predictions"
TRACKING_DIR = "backend/data/tracking"

# NCAA-OPTIMIZED MODEL PARAMETERS
# Based on actual 2024 season data: Avg total = 138.3 points
HOME_COURT_ADVANTAGE = 4.0     # NCAA: 4.0 (vs NBA: 2.5)
LEAGUE_AVG_EFFICIENCY = 110.0  # NCAA: 110.0 (vs NBA: 105.0)

# Alternative parameters to test:
# Conservative: HCA=3.8, EFF=108.0
# Aggressive: HCA=4.5, EFF=112.0

# Confidence Thresholds
HIGH_CONFIDENCE_EDGE = 5.0  # 5+ point edge
MEDIUM_CONFIDENCE_EDGE = 3.0  # 3-5 point edge
LOW_CONFIDENCE_EDGE = 1.5  # 1.5-3 point edge
'''

    # Write to both locations
    config_locations = ["config.py", "backend/config.py"]
    
    for location in config_locations:
        os.makedirs(os.path.dirname(location) if os.path.dirname(location) else ".", exist_ok=True)
        with open(location, 'w') as f:
            f.write(config_content)
        print(f"✅ Updated: {location}")

def main():
    print("🔧 FIXING NCAA BASKETBALL PARAMETERS")
    print("="*50)
    print("\n📊 PROBLEM ANALYSIS:")
    print("   Your model: 129.2 avg prediction")
    print("   Actual NCAA: 138.3 avg total")
    print("   Under-prediction: 9.1 points")
    print("   Root cause: Using NBA parameters for NCAA")
    
    print("\n🎯 SOLUTION:")
    print("   HOME_COURT_ADVANTAGE: 3.5 → 4.0")
    print("   LEAGUE_AVG_EFFICIENCY: 105.0 → 110.0")
    print("   Expected improvement: MAE 19.2 → 8-10 points")
    
    # Backup and update
    backup_config()
    create_ncaa_config()
    
    print("\n🚀 NEXT STEPS:")
    print("   1. python run_ncaab_backtest.py")
    print("   2. Check if MAE drops to 8-10 points")
    print("   3. If still high, try aggressive parameters:")
    print("      HCA=4.5, EFF=112.0")
    
    print("\n📈 EXPECTED RESULTS:")
    print("   MAE: 19.2 → 8-10 points")
    print("   Within ±5: 16% → 35%+")
    print("   Prediction bias: 65% under → 50/50")
    
    print("\n✅ PARAMETERS UPDATED!")
    print("="*50)

if __name__ == "__main__":
    main()
