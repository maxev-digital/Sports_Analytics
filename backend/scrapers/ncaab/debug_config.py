#!/usr/bin/env python3
"""
Debug Config Values - Check what the model is actually using
"""

import sys
import os

# Add backend to path
sys.path.insert(0, 'backend')

print("="*70)
print("DEBUGGING CONFIG VALUES")
print("="*70)

# Try to import config
try:
    from config import HOME_COURT_ADVANTAGE, LEAGUE_AVG_EFFICIENCY
    print(f"✅ Config imported successfully")
    print(f"   HOME_COURT_ADVANTAGE: {HOME_COURT_ADVANTAGE}")
    print(f"   LEAGUE_AVG_EFFICIENCY: {LEAGUE_AVG_EFFICIENCY}")
    
    if LEAGUE_AVG_EFFICIENCY == 105.0:
        print("❌ STILL USING OLD VALUES!")
        print("   The calibration didn't take effect")
    elif LEAGUE_AVG_EFFICIENCY == 98.0:
        print("✅ USING NEW CALIBRATED VALUES!")
    else:
        print(f"⚠️  Using unexpected value: {LEAGUE_AVG_EFFICIENCY}")
        
except ImportError as e:
    print(f"❌ Cannot import config: {str(e)}")

# Check which config files exist
print(f"\n📁 Checking config file locations:")

config_locations = [
    "config.py",
    "backend/config.py",
    "backend\\config.py"
]

for location in config_locations:
    if os.path.exists(location):
        print(f"   ✅ Found: {location}")
        # Try to read the values
        try:
            with open(location, 'r') as f:
                content = f.read()
                if "LEAGUE_AVG_EFFICIENCY = 98.0" in content:
                    print(f"      ✅ Contains calibrated values")
                elif "LEAGUE_AVG_EFFICIENCY = 105.0" in content:
                    print(f"      ❌ Contains OLD values")
                else:
                    print(f"      ⚠️  Cannot determine values")
        except:
            print(f"      ❌ Cannot read file")
    else:
        print(f"   ❌ Missing: {location}")

print(f"\n💡 SOLUTION:")
print(f"   1. Copy config_calibrated.py to the correct location")
print(f"   2. Make sure both config.py AND backend/config.py are updated")
print("="*70)
