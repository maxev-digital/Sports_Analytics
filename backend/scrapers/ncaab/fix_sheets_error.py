#!/usr/bin/env python3
"""
Fix Google Sheets Connection
Diagnose and fix the 404 error when uploading to Google Sheets
"""

import os
import json

def check_sheets_config():
    """Check Google Sheets configuration"""
    
    print("🔧 DIAGNOSING GOOGLE SHEETS ERROR")
    print("="*50)
    
    # Check config.py exists
    config_files = ["config.py", "backend/config.py"]
    config_found = False
    
    for config_file in config_files:
        if os.path.exists(config_file):
            config_found = True
            print(f"✅ Found config: {config_file}")
            
            # Read config
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                    
                # Check for placeholder
                if 'YOUR_SHEET_ID_HERE' in content:
                    print("❌ Sheet ID not configured (still has placeholder)")
                    print("\n🔧 SOLUTION:")
                    print("   1. Create a new Google Sheet")
                    print("   2. Get the Sheet ID from URL")
                    print("   3. Replace YOUR_SHEET_ID_HERE in config.py")
                    return False
                    
                # Extract sheet ID
                lines = content.split('\n')
                for line in lines:
                    if 'GOOGLE_SHEET_ID' in line and '=' in line:
                        sheet_id = line.split('=')[1].strip().strip('"\'')
                        if len(sheet_id) > 10:
                            print(f"✅ Sheet ID found: {sheet_id[:20]}...")
                            
                            # Check credentials
                            creds_found = False
                            for line in lines:
                                if 'GOOGLE_CREDENTIALS_PATH' in line and '=' in line:
                                    creds_path = line.split('=')[1].strip().strip('"\'')
                                    if os.path.exists(creds_path):
                                        print(f"✅ Credentials found: {creds_path}")
                                        creds_found = True
                                        
                                        # Try to read service account email
                                        try:
                                            with open(creds_path, 'r') as cf:
                                                creds_data = json.load(cf)
                                                email = creds_data.get('client_email', 'Unknown')
                                                print(f"✅ Service account: {email}")
                                        except:
                                            print("⚠️  Could not read credentials file")
                                    else:
                                        print(f"❌ Credentials not found: {creds_path}")
                                    break
                            
                            if creds_found:
                                print("\n🔧 GOOGLE SHEETS 404 ERROR SOLUTIONS:")
                                print("1. Make sure you shared the sheet with service account")
                                print("2. Give Editor permissions to service account")
                                print("3. Check if Sheet ID is correct")
                                print("4. Try creating a new sheet")
                                
                                print(f"\n📋 MANUAL TEST:")
                                print(f"   1. Go to: https://docs.google.com/spreadsheets/d/{sheet_id}")
                                print(f"   2. If you get 404, the Sheet ID is wrong")
                                print(f"   3. If you can see it, check sharing settings")
                                
                                return True
                        break
                
            except Exception as e:
                print(f"❌ Error reading config: {str(e)}")
            break
    
    if not config_found:
        print("❌ No config.py found")
        print("   Run: python setup_ncaab.py")
        return False

if __name__ == "__main__":
    check_sheets_config()
