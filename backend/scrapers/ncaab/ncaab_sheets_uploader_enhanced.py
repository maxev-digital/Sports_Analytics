#!/usr/bin/env python3
"""
NCAA Basketball Google Sheets Uploader - ENHANCED VERSION
Supports multiple tabs: Predictions and Backtesting Results
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
        print("   ✅ Connected successfully")
        
    def get_or_create_worksheet(self, tab_name):
        """Get existing worksheet or create new one"""
        try:
            worksheet = self.spreadsheet.worksheet(tab_name)
            print(f"   ✅ Found existing tab: {tab_name}")
            return worksheet
        except gspread.exceptions.WorksheetNotFound:
            print(f"   📝 Creating new tab: {tab_name}")
            worksheet = self.spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=26)
            return worksheet
    
    def format_predictions(self, df):
        """Format predictions for sheets"""
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
    
    def format_backtest_results(self, predictions_df, metrics):
        """Format backtesting results for sheets"""
        
        # Create summary section
        summary_rows = [
            ['📊 BACKTESTING RESULTS SUMMARY', ''],
            ['', ''],
            ['Total Games Analyzed:', metrics.get('total_games', 0)],
            ['Average Actual Total:', metrics.get('avg_total', 0)],
            ['Average Model Prediction:', metrics.get('avg_prediction', 0)],
            ['', ''],
            ['🎯 ACCURACY METRICS', ''],
            ['Mean Absolute Error (MAE):', f"{metrics.get('mae', 0)} points"],
            ['Root Mean Squared Error (RMSE):', f"{metrics.get('rmse', 0)} points"],
            ['Median Absolute Error:', f"{metrics.get('median_ae', 0)} points"],
            ['', ''],
            ['✅ PREDICTIONS WITHIN:', ''],
            ['±3 points:', f"{metrics.get('within_3_pct', 0)}%"],
            ['±5 points:', f"{metrics.get('within_5_pct', 0)}%"],
            ['±7 points:', f"{metrics.get('within_7_pct', 0)}%"],
            ['±10 points:', f"{metrics.get('within_10_pct', 0)}%"],
            ['', ''],
            ['🔄 PREDICTION BIAS', ''],
            ['Over-predictions:', f"{metrics.get('over_predictions', 0)} ({metrics.get('over_predictions', 0)/max(metrics.get('total_games', 1), 1)*100:.1f}%)"],
            ['Under-predictions:', f"{metrics.get('under_predictions', 0)} ({metrics.get('under_predictions', 0)/max(metrics.get('total_games', 1), 1)*100:.1f}%)"],
            ['', ''],
            ['', ''],
            ['📋 DETAILED PREDICTIONS', '']
        ]
        
        # Format predictions dataframe
        pred_columns = ['Home_Team', 'Away_Team', 'Model_Total', 'Actual_Total', 
                       'Error', 'Abs_Error', 'Home_Tempo', 'Away_Tempo', 'Expected_Pace']
        
        available_cols = [col for col in pred_columns if col in predictions_df.columns]
        formatted_preds = predictions_df[available_cols].copy()
        
        # Round numeric columns
        numeric_cols = ['Model_Total', 'Actual_Total', 'Error', 'Abs_Error',
                       'Home_Tempo', 'Away_Tempo', 'Expected_Pace']
        
        for col in numeric_cols:
            if col in formatted_preds.columns:
                formatted_preds[col] = formatted_preds[col].round(1)
        
        return summary_rows, formatted_preds
    
    def upload_predictions(self, df, tab_name='Predictions'):
        """Upload predictions to specified tab"""
        if not self.spreadsheet:
            self.connect()
        
        print(f"   📤 Uploading to tab: {tab_name}")
        
        # Get or create worksheet
        worksheet = self.get_or_create_worksheet(tab_name)
        
        # Format data
        formatted = self.format_predictions(df)
        
        # Clear existing data
        print("   🗑️  Clearing old data...")
        worksheet.clear()
        
        # Upload headers
        headers = formatted.columns.tolist()
        worksheet.update('A1', [headers], value_input_option='RAW')
        
        # Upload data
        print(f"   📤 Uploading {len(formatted)} rows...")
        values = formatted.values.tolist()
        
        if values:
            # Upload in batches of 100 to avoid API limits
            batch_size = 100
            for i in range(0, len(values), batch_size):
                batch = values[i:i+batch_size]
                start_row = i + 2  # +2 because row 1 is headers, rows are 1-indexed
                end_row = start_row + len(batch) - 1
                
                cell_range = f'A{start_row}:' + chr(65 + len(headers) - 1) + f'{end_row}'
                worksheet.update(cell_range, batch, value_input_option='RAW')
                
                print(f"      Uploaded rows {start_row}-{end_row}")
                
                # Small delay to respect API rate limits
                if i + batch_size < len(values):
                    time.sleep(1)
        
        # Apply formatting
        self._apply_prediction_formatting(worksheet, len(values))
        
        print(f"   ✅ Upload complete!")
        return worksheet
    
    def upload_backtest_results(self, predictions_df, metrics, tab_name='Backtesting'):
        """Upload backtesting results to specified tab"""
        if not self.spreadsheet:
            self.connect()
        
        print(f"   📤 Uploading backtest results to tab: {tab_name}")
        
        # Get or create worksheet
        worksheet = self.get_or_create_worksheet(tab_name)
        
        # Clear existing data
        print("   🗑️  Clearing old data...")
        worksheet.clear()
        
        # Format data
        summary_rows, formatted_preds = self.format_backtest_results(predictions_df, metrics)
        
        # Upload summary section
        print("   📊 Uploading summary...")
        worksheet.update('A1', summary_rows, value_input_option='RAW')
        
        # Calculate where predictions start (after summary + 1 blank row)
        predictions_start_row = len(summary_rows) + 2
        
        # Upload predictions headers
        pred_headers = formatted_preds.columns.tolist()
        worksheet.update(f'A{predictions_start_row}', [pred_headers], value_input_option='RAW')
        
        # Upload predictions data
        print(f"   📤 Uploading {len(formatted_preds)} prediction details...")
        pred_values = formatted_preds.values.tolist()
        
        if pred_values:
            # Upload in batches
            batch_size = 100
            for i in range(0, len(pred_values), batch_size):
                batch = pred_values[i:i+batch_size]
                start_row = predictions_start_row + 1 + i
                end_row = start_row + len(batch) - 1
                
                cell_range = f'A{start_row}:' + chr(65 + len(pred_headers) - 1) + f'{end_row}'
                worksheet.update(cell_range, batch, value_input_option='RAW')
                
                print(f"      Uploaded rows {start_row}-{end_row}")
                
                if i + batch_size < len(pred_values):
                    time.sleep(1)
        
        # Apply formatting
        self._apply_backtest_formatting(worksheet, len(summary_rows), len(pred_values))
        
        print(f"   ✅ Backtest upload complete!")
        return worksheet
    
    def _apply_prediction_formatting(self, worksheet, num_rows):
        """Apply color coding to prediction tab"""
        try:
            # Format header row (bold, gray background)
            worksheet.format('A1:Z1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
            
            # Freeze header row
            worksheet.freeze(rows=1)
            
            print("   🎨 Applied formatting")
            
        except Exception as e:
            print(f"   ⚠️  Could not apply formatting: {str(e)}")
    
    def _apply_backtest_formatting(self, worksheet, summary_rows, pred_rows):
        """Apply formatting to backtest tab"""
        try:
            # Format summary section headers (bold)
            worksheet.format('A1:B25', {
                'textFormat': {'bold': True}
            })
            
            # Format prediction headers
            pred_header_row = summary_rows + 2
            worksheet.format(f'A{pred_header_row}:Z{pred_header_row}', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
            
            # Freeze rows above predictions
            worksheet.freeze(rows=pred_header_row)
            
            print("   🎨 Applied backtest formatting")
            
        except Exception as e:
            print(f"   ⚠️  Could not apply formatting: {str(e)}")


def test_multi_tab_upload():
    """Test uploading to multiple tabs"""
    print("="*70)
    print("TESTING MULTI-TAB GOOGLE SHEETS UPLOAD")
    print("="*70)
    
    # These should come from config
    credentials_path = "google_sheets/credentials/service-account-key.json"
    sheet_id = "YOUR_SHEET_ID"  # Replace with actual ID from config.py
    
    # Create fake predictions
    fake_predictions = pd.DataFrame({
        'Date': ['11/15', '11/15', '11/16'],
        'Time': ['7:00 PM', '9:00 PM', '7:30 PM'],
        'Home_Team': ['Duke', 'Kansas', 'North Carolina'],
        'Away_Team': ['North Carolina', 'Kentucky', 'Virginia'],
        'Home_Tempo': [71.2, 68.5, 69.3],
        'Away_Tempo': [69.8, 70.1, 66.4],
        'Expected_Pace': [70.5, 69.3, 67.8],
        'Home_OffEff': [118.3, 115.2, 114.8],
        'Away_OffEff': [116.7, 117.8, 112.4],
        'Home_Points': [83.4, 79.8, 77.8],
        'Away_Points': [82.3, 81.6, 76.2],
        'Model_Total': [165.7, 161.4, 154.0],
        'Market_Total': [158.5, 159.5, 152.5],
        'Edge': [7.2, 1.9, 1.5],
        'Recommendation': ['OVER 158.5', 'OVER 159.5', 'OVER 152.5'],
        'Confidence': ['HIGH', 'LOW', 'LOW'],
        'Bet': ['YES', 'YES', 'YES']
    })
    
    # Create fake backtest results
    fake_backtest_predictions = pd.DataFrame({
        'Home_Team': ['Duke', 'Kansas', 'Gonzaga', 'Alabama', 'Houston'],
        'Away_Team': ['UNC', 'Kentucky', 'Baylor', 'Auburn', 'Tennessee'],
        'Model_Total': [165.3, 161.2, 157.8, 171.2, 138.4],
        'Actual_Total': [162.0, 159.0, 155.0, 168.0, 142.0],
        'Error': [3.3, 2.2, 2.8, 3.2, -3.6],
        'Abs_Error': [3.3, 2.2, 2.8, 3.2, 3.6],
        'Home_Tempo': [71.2, 68.5, 69.8, 72.1, 65.3],
        'Away_Tempo': [69.8, 70.1, 68.4, 71.8, 64.7],
        'Expected_Pace': [70.5, 69.3, 69.1, 71.9, 65.0]
    })
    
    fake_metrics = {
        'total_games': 5,
        'mae': 3.0,
        'rmse': 3.2,
        'median_ae': 2.8,
        'within_3_pct': 60.0,
        'within_5_pct': 100.0,
        'within_7_pct': 100.0,
        'within_10_pct': 100.0,
        'over_predictions': 4,
        'under_predictions': 1,
        'avg_total': 157.2,
        'avg_prediction': 158.8
    }
    
    try:
        uploader = NCAABSheetsUploaderEnhanced(credentials_path, sheet_id)
        
        print("\n📊 Step 1: Uploading predictions to 'Predictions' tab...")
        uploader.upload_predictions(fake_predictions, tab_name='Predictions')
        
        print("\n📊 Step 2: Uploading backtest results to 'Backtesting' tab...")
        uploader.upload_backtest_results(fake_backtest_predictions, fake_metrics, tab_name='Backtesting')
        
        print("\n" + "="*70)
        print("✅ MULTI-TAB UPLOAD SUCCESSFUL!")
        print(f"🔗 View: https://docs.google.com/spreadsheets/d/{sheet_id}")
        print("="*70)
        print("\nCheck your Google Sheet - you should see 2 tabs:")
        print("  1. Predictions - Your daily predictions")
        print("  2. Backtesting - Historical performance analysis")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    test_multi_tab_upload()
