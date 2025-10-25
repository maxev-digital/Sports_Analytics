#!/usr/bin/env python3
"""
Enter Game Results
Records actual outcomes and uploads to Google Sheets
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import os
import json

class ResultsEntry:
    """Record game results and update tracking sheets"""
    
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
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.credentials_file, 
            self.scope
        )
        self.client = gspread.authorize(creds)
        print("✓ Authenticated")
        
    def open_sheet(self):
        """Open sheet by saved ID"""
        config_file = 'google_sheets/sheet_config.json'
        
        if not os.path.exists(config_file):
            print("❌ No saved sheet ID. Run nba_sheets_uploader_v2.py first")
            return False
        
        with open(config_file, 'r') as f:
            config = json.load(f)
            sheet_id = config.get('sheet_id')
        
        self.sheet = self.client.open_by_key(sheet_id)
        print(f"✓ Opened: {self.sheet.title}")
        return True
        
    def get_finished_games(self):
        """Load predictions and identify finished games"""
        predictions_file = 'backend/data/predictions/nba_predictions_latest.csv'
        
        if not os.path.exists(predictions_file):
            print("❌ No predictions found. Run daily_nba_predictions.py first")
            return None
        
        df = pd.read_csv(predictions_file)
        
        # Filter to games that should have finished (yesterday or earlier)
        df['game_date'] = pd.to_datetime(df['game_date'])
        yesterday = pd.Timestamp.now().date() - pd.Timedelta(days=1)
        
        finished = df[df['game_date'].dt.date <= yesterday].copy()
        
        if len(finished) == 0:
            print("⚠️  No finished games in predictions")
            return None
        
        print(f"\n📋 Found {len(finished)} games that may have finished:")
        print("-"*70)
        
        for idx, game in finished.iterrows():
            print(f"{idx+1}. {game['game_date'].strftime('%m/%d')} - "
                  f"{game['away_team']} @ {game['home_team']} "
                  f"(Model: {game['predicted_total']}, Market: {game['market_total']}, "
                  f"{game['recommendation']}, {game['confidence']})")
        
        return finished
    
    def enter_results(self, games_df):
        """Prompt user to enter actual totals"""
        results = []
        
        print("\n" + "="*70)
        print("ENTER RESULTS")
        print("="*70)
        print("For each game, enter the ACTUAL TOTAL POINTS")
        print("(Enter 0 to skip a game)")
        print("-"*70)
        
        for idx, game in games_df.iterrows():
            print(f"\n{game['away_team']} @ {game['home_team']}")
            print(f"Date: {game['game_date'].strftime('%Y-%m-%d')}")
            print(f"Our Prediction: {game['predicted_total']}")
            print(f"Market Line: {game['market_total']}")
            print(f"Our Pick: {game['recommendation']} (Edge: {game['edge']}, Confidence: {game['confidence']})")
            
            while True:
                try:
                    actual_total = input("Enter ACTUAL TOTAL (or 0 to skip): ").strip()
                    actual_total = float(actual_total)
                    
                    if actual_total == 0:
                        print("⏭️  Skipped")
                        break
                    
                    if actual_total < 100 or actual_total > 300:
                        confirm = input(f"⚠️  {actual_total} seems unusual. Confirm? (y/n): ")
                        if confirm.lower() != 'y':
                            continue
                    
                    # Calculate result
                    result = self._calculate_result(
                        game['recommendation'],
                        game['market_total'],
                        actual_total
                    )
                    
                    game_info = {
                        'date': game['game_date'].strftime('%Y-%m-%d'),
                        'game': f"{game['away_team']} @ {game['home_team']}",
                        'predicted_total': game['predicted_total'],
                        'market_total': game['market_total'],
                        'actual_total': actual_total,
                        'edge': game['edge'],
                        'our_pick': f"{game['recommendation']} {game['market_total']}",
                        'result': result,
                        'confidence': game['confidence'],
                        'notes': '',
                        'entered_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    results.append(game_info)
                    
                    emoji = "✅" if result == "WIN" else "❌" if result == "LOSS" else "🟡"
                    print(f"{emoji} Result: {result}")
                    
                    break
                    
                except ValueError:
                    print("❌ Invalid input. Enter a number.")
        
        return results
    
    def _calculate_result(self, recommendation, market_total, actual_total):
        """Determine WIN/LOSS/PUSH"""
        # PUSH if exactly on the line
        if actual_total == market_total:
            return "PUSH"
        
        # Check if our pick was correct
        if recommendation == "OVER":
            if actual_total > market_total:
                return "WIN"
            else:
                return "LOSS"
        else:  # UNDER
            if actual_total < market_total:
                return "WIN"
            else:
                return "LOSS"
    
    def upload_to_sheets(self, results):
        """Upload results to Results Tracker and Model Calibration tabs"""
        if not results:
            print("\n⚠️  No results to upload")
            return
        
        print(f"\n⬆️  Uploading {len(results)} results to Google Sheets...")
        
        # Results Tracker tab
        results_ws = self.sheet.worksheet("Results Tracker")
        
        # Get next empty row
        existing_data = results_ws.get_all_values()
        next_row = len(existing_data) + 1
        
        # Skip if first rows are instructions
        if next_row <= 7:
            next_row = 8
        
        # Prepare rows
        rows = []
        for r in results:
            row = [
                r['date'],
                r['game'],
                r['predicted_total'],
                r['market_total'],
                r['actual_total'],
                r['edge'],
                r['our_pick'],
                r['result'],
                r['confidence'],
                r['notes'],
                r['entered_date']
            ]
            rows.append(row)
        
        # Upload to Results Tracker
        results_ws.update(values=rows, range_name=f'A{next_row}')
        print("✓ Updated Results Tracker")
        
        # Also upload to Model Calibration tab
        calibration_ws = self.sheet.worksheet("Model Calibration")
        
        # Get next row
        cal_existing = calibration_ws.get_all_values()
        cal_next_row = len(cal_existing) + 1
        
        cal_rows = []
        for r in results:
            model_error = abs(r['predicted_total'] - r['actual_total'])
            market_error = abs(r['market_total'] - r['actual_total'])
            
            cal_row = [
                r['date'],
                r['game'],
                r['predicted_total'],
                r['actual_total'],
                r['predicted_total'] - r['actual_total'],  # Difference
                model_error,
                r['market_total'],
                market_error,
                model_error - market_error  # Negative = model better
            ]
            cal_rows.append(cal_row)
        
        calibration_ws.update(values=cal_rows, range_name=f'A{cal_next_row}')
        print("✓ Updated Model Calibration")
        
        # Color code results
        for i, r in enumerate(results):
            row_num = next_row + i
            
            if r['result'] == 'WIN':
                results_ws.format(f'A{row_num}:K{row_num}', {
                    'backgroundColor': {'red': 0.85, 'green': 1, 'blue': 0.85}
                })
            elif r['result'] == 'LOSS':
                results_ws.format(f'A{row_num}:K{row_num}', {
                    'backgroundColor': {'red': 1, 'green': 0.85, 'blue': 0.85}
                })
            else:  # PUSH
                results_ws.format(f'A{row_num}:K{row_num}', {
                    'backgroundColor': {'red': 1, 'green': 1, 'blue': 0.85}
                })
        
        print("\n✅ Upload complete!")
        print(f"🔗 View: {self.sheet.url}")
        
        # Show summary
        wins = sum(1 for r in results if r['result'] == 'WIN')
        losses = sum(1 for r in results if r['result'] == 'LOSS')
        pushes = sum(1 for r in results if r['result'] == 'PUSH')
        
        print(f"\n📊 Session Summary:")
        print(f"   Wins: {wins}")
        print(f"   Losses: {losses}")
        print(f"   Pushes: {pushes}")
        
        if wins + losses > 0:
            win_rate = wins / (wins + losses) * 100
            print(f"   Win Rate: {win_rate:.1f}%")


def main():
    """Main results entry workflow"""
    print("="*70)
    print("NBA RESULTS ENTRY")
    print("="*70)
    
    entry = ResultsEntry()
    
    try:
        entry.authenticate()
        
        if not entry.open_sheet():
            return
        
        # Get finished games
        finished_games = entry.get_finished_games()
        
        if finished_games is None:
            return
        
        # Enter results
        results = entry.enter_results(finished_games)
        
        if not results:
            print("\n⚠️  No results entered")
            return
        
        # Upload to sheets
        entry.upload_to_sheets(results)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()