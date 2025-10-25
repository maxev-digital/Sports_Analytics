#!/usr/bin/env python3
"""
Fix Google Sheets 404 Error
Diagnose and fix the Sheet access issue
"""

import os
import json

def check_sheet_setup():
    """Check Google Sheets configuration"""
    print("🔍 DIAGNOSING GOOGLE SHEETS 404 ERROR")
    print("="*50)
    
    # Check credentials
    creds_path = "google_sheets/credentials/service-account-key.json"
    
    if os.path.exists(creds_path):
        print("✅ Credentials file found")
        try:
            with open(creds_path, 'r') as f:
                creds = json.load(f)
                service_email = creds.get('client_email', 'Unknown')
                print(f"   📧 Service account: {service_email}")
        except:
            print("   ⚠️ Could not read service account email")
    else:
        print("❌ Credentials file not found")
        print(f"   Expected: {creds_path}")
        
    # Check config
    try:
        import sys
        sys.path.insert(0, 'backend')
        from config import GOOGLE_SHEET_ID
        print(f"✅ Sheet ID found: {GOOGLE_SHEET_ID[:20]}...")
        
        # Provide test URL
        test_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}"
        print(f"\n🔗 TEST URL: {test_url}")
        
        print("\n🔧 TROUBLESHOOTING STEPS:")
        print("1. Open the test URL above in your browser")
        print("2. If you get 404:")
        print("   - Sheet ID is wrong")
        print("   - Sheet was deleted")
        print("   - Need to create new sheet")
        print("\n3. If you can see the sheet:")
        print("   - Click 'Share' button")
        print(f"   - Add: {service_email}")
        print("   - Permission: Editor")
        print("   - Uncheck 'Notify people'")
        print("   - Click 'Share'")
        
        print("\n4. Alternative: Create new sheet")
        print("   - Go to: https://sheets.google.com")
        print("   - Create new sheet")
        print("   - Name it: NCAA Basketball Predictions")
        print("   - Share with service account")
        print("   - Copy new Sheet ID to config.py")
        
    except ImportError:
        print("❌ Could not load config.py")
    
    print("\n🚀 QUICK FIX:")
    print("Most likely: Sheet sharing not set up correctly")
    print("Solution: Share sheet with service account as Editor")

def create_new_sheet_instructions():
    """Instructions to create a new sheet"""
    print("\n📋 CREATE NEW SHEET (IF NEEDED):")
    print("="*50)
    print("1. Go to: https://sheets.google.com")
    print("2. Click: + Blank")
    print("3. Rename to: NCAA Basketball Predictions")
    print("4. Add headers in row 1:")
    print("   A: Date, B: Time, C: Home_Team, D: Away_Team")
    print("   E: Model_Total, F: Market_Total, G: Edge")
    print("   H: Recommendation, I: Confidence, J: Bet")
    print("5. Share with service account (Editor permission)")
    print("6. Copy Sheet ID from URL to config.py")

if __name__ == "__main__":
    check_sheet_setup()
    create_new_sheet_instructions()
