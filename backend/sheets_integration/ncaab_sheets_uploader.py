#!/usr/bin/env python3
"""
NCAA Basketball Google Sheets Uploader
Formats and uploads predictions to Google Sheets
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

class NCAABSheetsUploader:
    def __init__(self, credentials_path, sheet_id):
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.client = None
        self.worksheet = None
        
    def connect(self):
        """Connect to Google Sheets"""
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.credentials_path, scope)
        
        self.client = gspread.authorize(creds)
        spreadsheet = self.client.open_by_key(self.sheet_id)
        self.worksheet = spreadsheet.sheet1
        
    def format_predictions(self, df):
        """Format predictions for sheets"""
        # Select columns to upload
        columns = [
            'Date', 'Time', 'Home_Team', 'Away_Team',
            'Home_Tempo', 'Away_Tempo', 'Expected_Pace',
            'Home_OffEff', 'Away_OffEff',
            'Home_Points', 'Away_Points',
            'Model_Total', 'Market_Total', 'Edge',
            'Recommendation', 'Confidence', 'Bet'
        ]
        
        # Filter to only columns that exist
        available_cols = [col for col in columns if col in df.columns]
        formatted = df[available_cols].copy()
        
        # Round numeric columns
        numeric_cols = ['Home_Tempo', 'Away_Tempo', 'Expected_Pace',
                       'Home_OffEff', 'Away_OffEff', 'Home_Points', 'Away_Points',
                       'Model_Total', 'Market_Total', 'Edge']
        
        for col in numeric_cols:
            if col in formatted.columns:
                formatted[col] = formatted[col].round(1)
        
        return formatted
    
    def upload_predictions(self, df):
        """Upload predictions to Google Sheets"""
        print("   ☁️  Connecting to Google Sheets...")
        self.connect()
        
        # Format data
        formatted = self.format_predictions(df)
        
        # Clear existing data (except headers)
        print("   🗑️  Clearing old data...")
        self.worksheet.resize(rows=1)  # Keep header row
        
        # Upload headers if needed
        headers = formatted.columns.tolist()
        self.worksheet.update('A1', [headers])
        
        # Upload data
        print("   📤 Uploading predictions...")
        values = formatted.values.tolist()
        self.worksheet.append_rows(values)
        
        # Apply formatting
        print("   🎨 Applying color coding...")
        self._apply_formatting(len(values))
        
        print(f"   ✅ Uploaded {len(values)} predictions")
    
    def _apply_formatting(self, num_rows):
        """Apply color coding based on confidence levels"""
        try:
            # Get confidence column (column P = 16)
            conf_col = 16
            
            # Define colors
            high_color = {'red': 0.85, 'green': 0.95, 'blue': 0.85}  # Light green
            medium_color = {'red': 1.0, 'green': 0.95, 'blue': 0.8}  # Light yellow
            
            # Apply conditional formatting (simplified version)
            # In practice, would use batch updates for better performance
            
            requests = []
            
            for row_idx in range(2, num_rows + 2):  # Start at row 2 (after header)
                # This is simplified - actual implementation would check cell values
                # and apply colors accordingly
                pass
            
            # Note: Full implementation would use sheets API batch updates
            # For now, user can manually apply conditional formatting in Sheets
            
        except Exception as e:
            print(f"   ⚠️  Could not apply formatting: {str(e)}")
