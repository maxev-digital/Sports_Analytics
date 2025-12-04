#!/usr/bin/env python3
"""
NCAA Basketball Google Sheets Uploader - Enhanced Version
Supports multiple tabs: Predictions and Backtesting
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time

class NCAABSheetsUploaderEnhanced:
    def __init__(self, credentials_path, sheet_id):
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.client = None
        self.spreadsheet = None
        
    def connect(self):
        """Connect to Google Sheets"""
        print("   ☁️  Connecting to Google Sheets...")
        
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.credentials_path, scope)
        
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(self.sheet_id)
        
        print(f"   ✅ Connected to: {self.spreadsheet.title}")
    
    def get_or_create_worksheet(self, title):
        """Get existing worksheet or create new one"""
        try:
            worksheet = self.spreadsheet.worksheet(title)
            print(f"   ✅ Found existing tab: {title}")
            return worksheet
        except gspread.exceptions.WorksheetNotFound:
            print(f"   ➕ Creating new tab: {title}")
            worksheet = self.spreadsheet.add_worksheet(title=title, rows=1000, cols=20)
            return worksheet
    
    def format_predictions(self, df):
        """Format daily predictions for sheets"""
        columns = [
            'Date', 'Time', 'Home_Team', 'Away_Team',
            'Home_Tempo', 'Away_Tempo', 'Expected_Pace',
            'Home_OffEff', 'Away_OffEff',
            'Home_Points', 'Away_Points',
            'Model_Total', 'Market_Total', 'Edge',
            'Recommendation', 'Confidence', 'Bet'
        ]
        
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
        """Upload daily predictions to 'Predictions' tab"""
        print("   📤 Uploading daily predictions...")
        
        self.connect()
        
        # Get or create Predictions worksheet
        worksheet = self.get_or_create_worksheet("Predictions")
        
        # Format data
        formatted = self.format_predictions(df)
        
        # Clear existing data (except headers)
        print("   🗑️  Clearing old predictions...")
        worksheet.resize(rows=1)
        
        # Upload headers
        headers = formatted.columns.tolist()
        worksheet.update('A1', [headers])
        
        # Upload data
        print(f"   📊 Uploading {len(formatted)} predictions...")
        values = formatted.values.tolist()
        
        # Batch upload in chunks to avoid API limits
        chunk_size = 100
        for i in range(0, len(values), chunk_size):
            chunk = values[i:i+chunk_size]
            worksheet.append_rows(chunk)
            time.sleep(1)  # Rate limiting
        
        print(f"   ✅ Uploaded {len(formatted)} predictions to 'Predictions' tab")
    
    def format_backtest_results(self, predictions_df, metrics):
        """Format backtesting results for sheets"""
        
        # Create summary section
        summary_rows = [
            ["📊 BACKTESTING RESULTS SUMMARY", ""],
            ["", ""],
            ["Total Games Analyzed:", metrics.get('total_games', 'N/A')],
            ["Average Actual Total:", metrics.get('avg_total', 'N/A')],
            ["Average Model Prediction:", metrics.get('avg_prediction', 'N/A')],
            ["", ""],
            ["🎯 ACCURACY METRICS", ""],
            ["Mean Absolute Error (MAE):", f"{metrics.get('mae', 'N/A')} points"],
            ["Root Mean Squared Error (RMSE):", f"{metrics.get('rmse', 'N/A')} points"],
            ["Median Absolute Error:", f"{metrics.get('median_ae', 'N/A')} points"],
            ["", ""],
            ["✅ PREDICTIONS WITHIN:", ""],
            ["±3 points:", f"{metrics.get('within_3_pct', 'N/A')}%"],
            ["±5 points:", f"{metrics.get('within_5_pct', 'N/A')}%"],
            ["±7 points:", f"{metrics.get('within_7_pct', 'N/A')}%"],
            ["±10 points:", f"{metrics.get('within_10_pct', 'N/A')}%"],
            ["", ""],
            ["🔄 PREDICTION BIAS", ""],
            ["Over-predictions:", f"{metrics.get('over_predictions', 'N/A')} ({metrics.get('over_predictions', 0)/max(metrics.get('total_games', 1), 1)*100:.1f}%)"],
            ["Under-predictions:", f"{metrics.get('under_predictions', 'N/A')} ({metrics.get('under_predictions', 0)/max(metrics.get('total_games', 1), 1)*100:.1f}%)"],
            ["", ""],
            ["━" * 50, ""],
            ["DETAILED PREDICTIONS", ""],
        ]
        
        # Format predictions data
        display_cols = ['Home_Team', 'Away_Team', 'Model_Total', 'Actual_Total', 
                       'Error', 'Abs_Error', 'Home_Tempo', 'Away_Tempo', 'Expected_Pace']
        
        available_cols = [col for col in display_cols if col in predictions_df.columns]
        predictions_formatted = predictions_df[available_cols].copy()
        
        # Round numeric columns
        numeric_cols = ['Model_Total', 'Actual_Total', 'Error', 'Abs_Error', 
                       'Home_Tempo', 'Away_Tempo', 'Expected_Pace']
        for col in numeric_cols:
            if col in predictions_formatted.columns:
                predictions_formatted[col] = predictions_formatted[col].round(1)
        
        return summary_rows, predictions_formatted
    
    def upload_backtest_results(self, predictions_df, metrics):
        """Upload backtesting results to 'Backtesting' tab"""
        print("   📤 Uploading backtest results...")
        
        self.connect()
        
        # Get or create Backtesting worksheet
        worksheet = self.get_or_create_worksheet("Backtesting")
        
        # Format results
        summary_rows, predictions_formatted = self.format_backtest_results(predictions_df, metrics)
        
        # Clear existing data
        print("   🗑️  Clearing old backtest data...")
        worksheet.clear()
        
        # Upload summary section
        print("   📊 Uploading summary section...")
        for row_idx, row in enumerate(summary_rows, start=1):
            worksheet.update(f'A{row_idx}', [row])
            time.sleep(0.5)  # Rate limiting
        
        # Calculate starting row for predictions (after summary + spacer)
        predictions_start_row = len(summary_rows) + 2
        
        # Upload predictions headers
        print("   📊 Uploading detailed predictions...")
        headers = predictions_formatted.columns.tolist()
        worksheet.update(f'A{predictions_start_row}', [headers])
        
        # Upload predictions data in chunks
        values = predictions_formatted.values.tolist()
        chunk_size = 100
        
        for i in range(0, len(values), chunk_size):
            chunk = values[i:i+chunk_size]
            start_row = predictions_start_row + 1 + i
            
            # Build range string (e.g., A25:I124)
            end_col_letter = chr(ord('A') + len(headers) - 1)
            end_row = start_row + len(chunk) - 1
            range_str = f'A{start_row}:{end_col_letter}{end_row}'
            
            worksheet.update(range_str, chunk)
            time.sleep(1)  # Rate limiting
            
            if i + chunk_size < len(values):
                print(f"      Progress: {i + chunk_size}/{len(values)} rows...")
        
        print(f"   ✅ Uploaded {len(predictions_formatted)} predictions to 'Backtesting' tab")
        print(f"   📊 Summary metrics displayed in top section")
