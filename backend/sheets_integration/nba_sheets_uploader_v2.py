#!/usr/bin/env python3
"""
NBA Predictions Google Sheets Uploader V2
Multi-tab version with performance tracking
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime, timedelta
import os
import json

class NBAGoogleSheetsUploaderV2:
    """Multi-tab Google Sheets uploader with performance tracking"""
    
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
        print("🔐 Authenticating...")
        
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(f"Credentials not found: {self.credentials_file}")
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.credentials_file, 
            self.scope
        )
        self.client = gspread.authorize(creds)
        print("✓ Authentication successful")
        
    def open_sheet_by_id(self, sheet_id):
        """Open existing sheet by ID"""
        print(f"📂 Opening Google Sheet...")
        self.sheet = self.client.open_by_key(sheet_id)
        print(f"✓ Opened: {self.sheet.title}")
        return self.sheet
    
    def setup_all_tabs(self):
        """Create all necessary tabs"""
        print("\n📑 Setting up tabs...")
        
        # Tab 1: Predictions (already exists)
        try:
            predictions_ws = self.sheet.worksheet("Predictions")
            print("✓ Found Predictions tab")
        except:
            predictions_ws = self.sheet.add_worksheet(title="Predictions", rows=100, cols=20)
            print("✓ Created Predictions tab")
        
        # Tab 2: Results Tracker
        try:
            results_ws = self.sheet.worksheet("Results Tracker")
            print("✓ Found Results Tracker tab")
        except:
            results_ws = self.sheet.add_worksheet(title="Results Tracker", rows=1000, cols=15)
            self._setup_results_tracker(results_ws)
            print("✓ Created Results Tracker tab")
        
        # Tab 3: Performance Dashboard
        try:
            dashboard_ws = self.sheet.worksheet("Performance Dashboard")
            print("✓ Found Performance Dashboard tab")
        except:
            dashboard_ws = self.sheet.add_worksheet(title="Performance Dashboard", rows=50, cols=10)
            self._setup_dashboard(dashboard_ws)
            print("✓ Created Performance Dashboard tab")
        
        # Tab 4: Betting History
        try:
            history_ws = self.sheet.worksheet("Betting History")
            print("✓ Found Betting History tab")
        except:
            history_ws = self.sheet.add_worksheet(title="Betting History", rows=1000, cols=12)
            self._setup_betting_history(history_ws)
            print("✓ Created Betting History tab")
        
        # Tab 5: Model Calibration
        try:
            calibration_ws = self.sheet.worksheet("Model Calibration")
            print("✓ Found Model Calibration tab")
        except:
            calibration_ws = self.sheet.add_worksheet(title="Model Calibration", rows=1000, cols=10)
            self._setup_calibration(calibration_ws)
            print("✓ Created Model Calibration tab")
        
        return predictions_ws, results_ws, dashboard_ws, history_ws, calibration_ws
    
    def _setup_results_tracker(self, worksheet):
        """Setup Results Tracker tab"""
        headers = [
            'Date', 'Game', 'Predicted Total', 'Market Total', 
            'Actual Total', 'Edge', 'Our Pick', 'Result',
            'Confidence', 'Notes', 'Entered Date'
        ]
        worksheet.update(values=[headers], range_name='A1')
        
        # Format header
        worksheet.format('A1:K1', {
            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'horizontalAlignment': 'CENTER'
        })
        worksheet.freeze(rows=1)
        
        # Instructions
        instructions = [
            ["INSTRUCTIONS:"],
            ["1. After each game finishes, enter the actual total points"],
            ["2. Result will auto-calculate: WIN/LOSS/PUSH"],
            ["3. Dashboard will update automatically"],
            [""],
            ["TIP: Copy games from Predictions tab after they finish"]
        ]
        worksheet.update(values=instructions, range_name='A2')
        worksheet.format('A2', {'textFormat': {'bold': True}})
    
    def _setup_dashboard(self, worksheet):
        """Setup Performance Dashboard tab"""
        # Title
        worksheet.update(values=[["NBA TOTALS MODEL - PERFORMANCE DASHBOARD"]], range_name='A1')
        worksheet.merge_cells('A1:F1')
        worksheet.format('A1', {
            'backgroundColor': {'red': 0.1, 'green': 0.1, 'blue': 0.1},
            'textFormat': {'bold': True, 'fontSize': 16, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'horizontalAlignment': 'CENTER'
        })
        
        # Overall stats section
        sections = [
            [""],
            ["OVERALL PERFORMANCE", "", "", "", "", ""],
            ["Metric", "Value", "", "Target", "Status", ""],
            ["Total Bets", "=COUNTA('Results Tracker'!H:H)-1", "", "-", "", ""],
            ["Wins", "=COUNTIF('Results Tracker'!H:H,\"WIN\")", "", "-", "", ""],
            ["Losses", "=COUNTIF('Results Tracker'!H:H,\"LOSS\")", "", "-", "", ""],
            ["Pushes", "=COUNTIF('Results Tracker'!H:H,\"PUSH\")", "", "-", "", ""],
            ["Win Rate", "=IF(B4=0,0,B5/(B4-B7))", "", "55%", "=IF(B8>=0.55,\"✅\",\"❌\")", ""],
            ["Win Rate (w/ Pushes)", "=IF(B4=0,0,B5/B4)", "", "53%", "=IF(B9>=0.53,\"✅\",\"❌\")", ""],
            [""],
            ["BY CONFIDENCE LEVEL", "", "", "", "", ""],
            ["Confidence", "Bets", "Wins", "Win Rate", "Target", "Status"],
            ["HIGH", "=COUNTIF('Results Tracker'!I:I,\"HIGH\")", "=COUNTIFS('Results Tracker'!I:I,\"HIGH\",'Results Tracker'!H:H,\"WIN\")", "=IF(B13=0,0,C13/B13)", "58%", "=IF(D13>=0.58,\"✅\",\"❌\")"],
            ["MEDIUM", "=COUNTIF('Results Tracker'!I:I,\"MEDIUM\")", "=COUNTIFS('Results Tracker'!I:I,\"MEDIUM\",'Results Tracker'!H:H,\"WIN\")", "=IF(B14=0,0,C14/B14)", "54%", "=IF(D14>=0.54,\"✅\",\"❌\")"],
            ["LOW", "=COUNTIF('Results Tracker'!I:I,\"LOW\")", "=COUNTIFS('Results Tracker'!I:I,\"LOW\",'Results Tracker'!H:H,\"WIN\")", "=IF(B15=0,0,C15/B15)", "52%", "=IF(D15>=0.52,\"✅\",\"❌\")"],
            [""],
            ["EDGE ACCURACY", "", "", "", "", ""],
            ["Average Edge", "=AVERAGE('Results Tracker'!F:F)", "", "", "", ""],
            ["Avg Edge (Winners)", "=AVERAGEIF('Results Tracker'!H:H,\"WIN\",'Results Tracker'!F:F)", "", "", "", ""],
            ["Avg Edge (Losers)", "=AVERAGEIF('Results Tracker'!H:H,\"LOSS\",'Results Tracker'!F:F)", "", "", "", ""],
            [""],
            ["NOTES:", "", "", "", "", ""],
            ["- Need 50+ bets for statistical significance", "", "", "", "", ""],
            ["- Win rate should increase with confidence level", "", "", "", "", ""],
            ["- If losing consistently, recalibrate model", "", "", "", "", ""]
        ]
        
        worksheet.update(values=sections, range_name='A2')
        
        # Format headers
        worksheet.format('A3:F3', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}})
        worksheet.format('A12:F12', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}})
        worksheet.format('A13:F13', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.85}})
        
        # Format percentages
        worksheet.format('B8:B9', {'numberFormat': {'type': 'PERCENT', 'pattern': '0.0%'}})
        worksheet.format('D13:D15', {'numberFormat': {'type': 'PERCENT', 'pattern': '0.0%'}})
        
    def _setup_betting_history(self, worksheet):
        """Setup Betting History tab"""
        headers = [
            'Date', 'Game', 'Pick', 'Line', 'Result', 
            'Units Risked', 'Units Won/Lost', 'Running Total',
            'Confidence', 'Edge', 'Notes'
        ]
        worksheet.update(values=[headers], range_name='A1')
        
        worksheet.format('A1:K1', {
            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'horizontalAlignment': 'CENTER'
        })
        worksheet.freeze(rows=1)
        
        # Instructions
        instructions = [
            ["BANKROLL TRACKING"],
            ["Starting Bankroll: $1,000  (Edit this)"],
            ["Unit Size: 1% = $10  (Edit this)"],
            [""],
            ["Copy results from Results Tracker tab"],
            ["Calculate units: HIGH=3u, MEDIUM=2u, LOW=1u"]
        ]
        worksheet.update(values=instructions, range_name='A2')
        
    def _setup_calibration(self, worksheet):
        """Setup Model Calibration tab"""
        headers = [
            'Date', 'Game', 'Model Predicted', 'Actual Total', 
            'Difference', 'Model Error', 'Market Total', 
            'Market Error', 'Model vs Market'
        ]
        worksheet.update(values=[headers], range_name='A1')
        
        worksheet.format('A1:I1', {
            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'horizontalAlignment': 'CENTER'
        })
        worksheet.freeze(rows=1)
        
        # Summary stats
        stats = [
            [""],
            ["CALIBRATION STATS"],
            ["Average Model Error:", "=AVERAGE(F:F)"],
            ["Average Market Error:", "=AVERAGE(H:H)"],
            ["Model Better Than Market:", "=COUNTIF(I:I,\"<0\")/COUNTA(I:I)"],
            [""],
            ["If model error > market error consistently, recalibrate"]
        ]
        worksheet.update(values=stats, range_name='K2')
        worksheet.format('K3', {'textFormat': {'bold': True}})
    
    def upload_predictions(self, predictions_csv='backend/data/predictions/nba_predictions_latest.csv'):
        """Upload predictions to Predictions tab"""
        print("\n📊 Uploading predictions...")
        
        if not os.path.exists(predictions_csv):
            raise FileNotFoundError(f"File not found: {predictions_csv}")
        
        df = pd.read_csv(predictions_csv)
        print(f"✓ Loaded {len(df)} predictions")
        
        worksheet = self.sheet.worksheet("Predictions")
        worksheet.clear()
        
        # Headers
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
        
        worksheet.update(values=rows, range_name='A1')
        
        # Apply formatting
        self._format_predictions_tab(worksheet, len(df))
        
        print("✓ Predictions uploaded")
        
    def _format_predictions_tab(self, worksheet, num_rows):
        """Format predictions tab"""
        # Header
        worksheet.format('A1:S1', {
            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'horizontalAlignment': 'CENTER'
        })
        worksheet.freeze(rows=1)
        
        # Color code by confidence
        for i in range(2, num_rows + 2):
            try:
                confidence = worksheet.acell(f'K{i}').value
                
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
        
        # Center numbers
        worksheet.format('G:S', {'horizontalAlignment': 'CENTER'})
        
        # Timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        worksheet.update(values=[[f'Last Updated: {timestamp}']], range_name=f'A{num_rows + 3}')


def upload_to_sheets_v2():
    """Main upload function"""
    print("="*70)
    print("NBA PREDICTIONS → GOOGLE SHEETS (V2 - Multi-Tab)")
    print("="*70)
    
    # Get service account email
    with open('google_sheets/credentials/service-account-key.json', 'r') as f:
        service_email = json.load(f)['client_email']
    
    print(f"\n📋 Service Account: {service_email}")
    
    # Check for saved sheet ID
    config_file = 'google_sheets/sheet_config.json'
    sheet_id = None
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            sheet_id = config.get('sheet_id')
            print(f"✓ Found saved Sheet ID")
    
    if not sheet_id:
        sheet_id = input("\n📝 Enter your Google Sheet ID: ").strip()
        
        # Extract from URL if needed
        if 'docs.google.com/spreadsheets/d/' in sheet_id:
            import re
            match = re.search(r'/d/([a-zA-Z0-9-_]+)', sheet_id)
            if match:
                sheet_id = match.group(1)
        
        # Save for next time
        with open(config_file, 'w') as f:
            json.dump({'sheet_id': sheet_id}, f)
        print(f"✓ Saved Sheet ID for future use")
    
    uploader = NBAGoogleSheetsUploaderV2()
    
    try:
        uploader.authenticate()
        uploader.open_sheet_by_id(sheet_id)
        uploader.setup_all_tabs()
        uploader.upload_predictions()
        
        print("\n" + "="*70)
        print("✅ SUCCESS!")
        print("="*70)
        print(f"\n🔗 Google Sheet: {uploader.sheet.url}")
        print("\n📑 Tabs created:")
        print("  1. Predictions - Current week's picks")
        print("  2. Results Tracker - Record outcomes")
        print("  3. Performance Dashboard - Win rate & stats")
        print("  4. Betting History - Bankroll tracking")
        print("  5. Model Calibration - Accuracy analysis")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    upload_to_sheets_v2()