#!/usr/bin/env python3
"""
NBA Predictions Google Sheets Uploader
Uploads predictions to YOUR Google Sheet (not service account's)
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import os

class NBAGoogleSheetsUploader:
    """Upload NBA predictions to Google Sheets with formatting"""
    
    def __init__(self, credentials_file='google_sheets/credentials/service-account-key.json'):
        self.credentials_file = credentials_file
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.client = None
        self.sheet = None
        
    def authenticate(self):
        """Authenticate with Google Sheets API"""
        print("🔐 Authenticating with Google Sheets...")
        
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_file}"
            )
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.credentials_file, 
            self.scope
        )
        self.client = gspread.authorize(creds)
        print("✓ Authentication successful")
        
    def open_sheet_by_id(self, sheet_id):
        """Open existing sheet by ID"""
        print(f"📂 Opening your Google Sheet...")
        self.sheet = self.client.open_by_key(sheet_id)
        print(f"✓ Opened sheet: {self.sheet.title}")
        print(f"✓ Sheet URL: {self.sheet.url}")
        return self.sheet
    
    def upload_predictions(self, predictions_csv='backend/data/predictions/nba_predictions_latest.csv'):
        """Upload predictions with formatting"""
        print("\n📊 Loading predictions...")
        
        if not os.path.exists(predictions_csv):
            raise FileNotFoundError(f"Predictions file not found: {predictions_csv}")
        
        df = pd.read_csv(predictions_csv)
        print(f"✓ Loaded {len(df)} predictions")
        
        # Get or create worksheet
        try:
            worksheet = self.sheet.worksheet("Predictions")
        except:
            worksheet = self.sheet.add_worksheet(title="Predictions", rows=100, cols=20)
        
        # Clear existing data
        worksheet.clear()
        
        # Prepare data for upload
        print("📝 Formatting data...")
        
        # Create header row
        headers = [
            'Date', 'Day', 'Time', 'Days Until', 
            'Away Team', 'Home Team',
            'Model Total', 'Market Total', 'Edge',
            'Recommendation', 'Confidence', 'BET?',
            'Away Pace', 'Home Pace', 'Expected Pace',
            'Away Off', 'Home Off', 'Away Def', 'Home Def'
        ]
        
        # Prepare rows
        rows = [headers]
        
        for _, pred in df.iterrows():
            row = [
                pred['game_date'],
                pred['day_of_week'],
                pred['game_time'],
                pred['days_until'],
                pred['away_team'],
                pred['home_team'],
                pred['predicted_total'],
                pred['market_total'],
                pred['edge'],
                pred['recommendation'],
                pred['confidence'],
                pred['bet'],
                pred['away_pace'],
                pred['home_pace'],
                pred['expected_pace'],
                pred['away_off_rating'],
                pred['home_off_rating'],
                pred['away_def_rating'],
                pred['home_def_rating']
            ]
            rows.append(row)
        
        # Upload data
        print("⬆️  Uploading to Google Sheets...")
        worksheet.update(values=rows, range_name='A1')
        
        # Apply formatting
        print("🎨 Applying formatting...")
        self._apply_formatting(worksheet, len(df))
        
        print(f"\n✅ Upload complete!")
        print(f"📊 View your sheet: {self.sheet.url}")
        
        return self.sheet.url
    
    def _apply_formatting(self, worksheet, num_rows):
        """Apply colors and formatting to the sheet"""
        
        # Format header row
        worksheet.format('A1:S1', {
            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'horizontalAlignment': 'CENTER'
        })
        
        # Freeze header row
        worksheet.freeze(rows=1)
        
        # Color code confidence levels
        for i in range(2, num_rows + 2):
            cell_range = f'K{i}'
            
            try:
                confidence = worksheet.acell(cell_range).value
                
                if confidence == 'HIGH':
                    worksheet.format(f'A{i}:S{i}', {
                        'backgroundColor': {'red': 0.85, 'green': 1, 'blue': 0.85}
                    })
                elif confidence == 'MEDIUM':
                    worksheet.format(f'A{i}:S{i}', {
                        'backgroundColor': {'red': 1, 'green': 1, 'blue': 0.85}
                    })
            except:
                pass
        
        # Bold BET column
        worksheet.format('L:L', {'textFormat': {'bold': True}})
        
        # Center align numbers
        worksheet.format('G:S', {'horizontalAlignment': 'CENTER'})
        
        # Add timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        worksheet.update(values=[[f'Last Updated: {timestamp}']], range_name=f'A{num_rows + 3}')


def upload_to_sheets():
    """Main upload function"""
    print("="*70)
    print("NBA PREDICTIONS → GOOGLE SHEETS")
    print("="*70)
    
    # Get service account email
    import json
    with open('google_sheets/credentials/service-account-key.json', 'r') as f:
        service_email = json.load(f)['client_email']
    
    print(f"\n📋 SETUP INSTRUCTIONS:")
    print(f"1. Go to: https://sheets.google.com")
    print(f"2. Create a blank sheet named 'NBA Totals Predictions'")
    print(f"3. Click Share and add this email as Editor:")
    print(f"   {service_email}")
    print(f"4. Copy the Sheet ID from the URL")
    print(f"   (the long string between /d/ and /edit)")
    
    sheet_id = input("\n📝 Enter your Google Sheet ID: ").strip()
    
    if not sheet_id:
        print("❌ No Sheet ID provided. Exiting.")
        return
    
    uploader = NBAGoogleSheetsUploader()
    
    try:
        uploader.authenticate()
        uploader.open_sheet_by_id(sheet_id)
        url = uploader.upload_predictions()
        
        print("\n" + "="*70)
        print("✅ SUCCESS!")
        print("="*70)
        print(f"\n🔗 Your Google Sheet: {url}")
        print("\n💡 Save this Sheet ID for future uploads: " + sheet_id)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    upload_to_sheets()