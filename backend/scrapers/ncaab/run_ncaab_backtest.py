#!/usr/bin/env python3
"""
NCAA Basketball Complete Backtesting Workflow
Gets historical data, runs backtest, uploads to Google Sheets
"""

import pandas as pd
import os
import sys
import glob
from datetime import datetime

# Add backend to path
sys.path.insert(0, 'backend')

try:
    from config import (
        GOOGLE_CREDENTIALS_PATH, GOOGLE_SHEET_ID,
        KENPOM_DATA_DIR
    )
except ImportError:
    print("❌ Error: config.py not found")
    print("   Make sure you've run setup_ncaab.py")
    sys.exit(1)

# Import scrapers and models
try:
    from models.ncaab.totals_predictor import NCAABTotalsPredictor
except:
    print("⚠️  Prediction model not found")
    NCAABTotalsPredictor = None

# Import enhanced sheets uploader
sys.path.insert(0, '.')
from ncaab_sheets_uploader_enhanced import NCAABSheetsUploaderEnhanced


class NCAABBacktesterIntegrated:
    """Enhanced backtester with Google Sheets integration"""
    
    def __init__(self, kenpom_data_path):
        self.kenpom_path = kenpom_data_path
        
        # Load KenPom data
        print(f"📊 Loading KenPom data from: {kenpom_data_path}")
        self.kenpom_data = pd.read_csv(kenpom_data_path)
        print(f"   ✅ Loaded {len(self.kenpom_data)} teams")
        
        # Initialize predictor
        if NCAABTotalsPredictor:
            self.predictor = NCAABTotalsPredictor(
                kenpom_data=self.kenpom_data,
                home_court_advantage=3.5,
                league_avg_eff=105.0
            )
        else:
            self.predictor = None
            print("   ❌ Predictor not available")
    
    def generate_predictions(self, games_df):
        """Generate predictions for historical games"""
        print(f"\n🔮 Generating predictions for {len(games_df)} games...")
        
        predictions = []
        successful = 0
        failed = 0
        
        for idx, game in games_df.iterrows():
            home_team = game['Home_Team']
            away_team = game['Away_Team']
            actual_total = game.get('Actual_Total', None)
            
            # Generate prediction
            pred = self.predictor.predict_game(home_team, away_team)
            
            if pred:
                model_total = pred['Model_Total']
                
                # Calculate error if we have actual result
                error = None
                abs_error = None
                if actual_total is not None:
                    error = model_total - actual_total
                    abs_error = abs(error)
                
                predictions.append({
                    'Home_Team': home_team,
                    'Away_Team': away_team,
                    'Model_Total': round(model_total, 1),
                    'Actual_Total': actual_total,
                    'Error': round(error, 1) if error is not None else None,
                    'Abs_Error': round(abs_error, 1) if abs_error is not None else None,
                    'Home_Tempo': pred['Home_Tempo'],
                    'Away_Tempo': pred['Away_Tempo'],
                    'Expected_Pace': pred['Expected_Pace']
                })
                successful += 1
                
                # Progress indicator
                if successful % 100 == 0:
                    print(f"   Progress: {successful}/{len(games_df)} predictions...")
            else:
                failed += 1
        
        print(f"   ✅ Successful predictions: {successful}")
        if failed > 0:
            print(f"   ⚠️  Failed predictions: {failed}")
        
        return pd.DataFrame(predictions)
    
    def calculate_metrics(self, predictions_df):
        """Calculate performance metrics"""
        import numpy as np
        
        # Filter to games with actual results
        df = predictions_df.dropna(subset=['Actual_Total'])
        
        if len(df) == 0:
            print("⚠️  No games with actual results to analyze")
            return {}
        
        print(f"\n📈 Calculating metrics for {len(df)} games...")
        
        # Mean Absolute Error (MAE)
        mae = df['Abs_Error'].mean()
        
        # Root Mean Squared Error (RMSE)
        rmse = np.sqrt((df['Error'] ** 2).mean())
        
        # Median Absolute Error
        median_ae = df['Abs_Error'].median()
        
        # Percentage within X points
        within_3 = (df['Abs_Error'] <= 3).sum() / len(df) * 100
        within_5 = (df['Abs_Error'] <= 5).sum() / len(df) * 100
        within_7 = (df['Abs_Error'] <= 7).sum() / len(df) * 100
        within_10 = (df['Abs_Error'] <= 10).sum() / len(df) * 100
        
        # Over/Under prediction
        over_predictions = (df['Error'] > 0).sum()
        under_predictions = (df['Error'] < 0).sum()
        
        metrics = {
            'total_games': len(df),
            'mae': round(mae, 2),
            'rmse': round(rmse, 2),
            'median_ae': round(median_ae, 2),
            'within_3_pct': round(within_3, 1),
            'within_5_pct': round(within_5, 1),
            'within_7_pct': round(within_7, 1),
            'within_10_pct': round(within_10, 1),
            'over_predictions': int(over_predictions),
            'under_predictions': int(under_predictions),
            'avg_total': round(df['Actual_Total'].mean(), 1),
            'avg_prediction': round(df['Model_Total'].mean(), 1)
        }
        
        return metrics
    
    def display_metrics(self, metrics):
        """Display metrics in readable format"""
        print("\n" + "="*70)
        print("BACKTESTING RESULTS")
        print("="*70)
        
        print(f"\n📊 Sample Size: {metrics['total_games']} games")
        print(f"📊 Average Actual Total: {metrics['avg_total']}")
        print(f"📊 Average Model Prediction: {metrics['avg_prediction']}")
        
        print("\n🎯 Accuracy Metrics:")
        print(f"   Mean Absolute Error (MAE): {metrics['mae']} points")
        print(f"   Root Mean Squared Error (RMSE): {metrics['rmse']} points")
        print(f"   Median Absolute Error: {metrics['median_ae']} points")
        
        print("\n✅ Predictions Within:")
        print(f"   ±3 points: {metrics['within_3_pct']}%")
        print(f"   ±5 points: {metrics['within_5_pct']}%")
        print(f"   ±7 points: {metrics['within_7_pct']}%")
        print(f"   ±10 points: {metrics['within_10_pct']}%")
        
        print("\n🔄 Prediction Bias:")
        over_pct = metrics['over_predictions']/metrics['total_games']*100
        under_pct = metrics['under_predictions']/metrics['total_games']*100
        print(f"   Over-predictions: {metrics['over_predictions']} ({over_pct:.1f}%)")
        print(f"   Under-predictions: {metrics['under_predictions']} ({under_pct:.1f}%)")
        
        print("\n" + "="*70)
    
    def save_results_local(self, predictions_df, metrics, output_dir='backend/data/backtesting'):
        """Save backtest results locally"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save predictions
        predictions_file = f"{output_dir}/predictions_{timestamp}.csv"
        predictions_df.to_csv(predictions_file, index=False)
        print(f"\n💾 Saved predictions: {predictions_file}")
        
        # Save metrics
        metrics_file = f"{output_dir}/metrics_{timestamp}.csv"
        metrics_df = pd.DataFrame([metrics])
        metrics_df.to_csv(metrics_file, index=False)
        print(f"💾 Saved metrics: {metrics_file}")
        
        return predictions_file, metrics_file


class NCAABBacktestWorkflow:
    """Complete backtesting workflow"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.kenpom_data = None
        self.historical_games = None
        self.predictions = None
        self.metrics = None
    
    def print_header(self):
        """Print workflow header"""
        print("="*70)
        print("NCAA BASKETBALL BACKTESTING WORKFLOW")
        print("="*70)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
    
    def check_historical_data(self):
        """Check if historical data exists"""
        print("STEP 1: CHECKING HISTORICAL DATA")
        print("-"*70)
        
        # Check for historical KenPom data
        historical_dir = "backend/data/historical"
        kenpom_pattern = f"{historical_dir}/kenpom_*_season_*.csv"
        kenpom_files = glob.glob(kenpom_pattern)
        
        if not kenpom_files:
            print("❌ No historical KenPom data found")
            print("\n💡 Run this command to get 2024 season data:")
            print("   python historical_kenpom_scraper.py")
            print("\n   Email: gte.apw@gmail.com")
            print("   Password: Thewrench1!")
            print("   Year: 2024")
            return False
        
        latest_kenpom = max(kenpom_files)
        self.kenpom_path = latest_kenpom
        print(f"✅ Found KenPom data: {os.path.basename(latest_kenpom)}")
        
        # Check for game results
        games_pattern = f"{historical_dir}/game_results_*_season_*.csv"
        games_files = glob.glob(games_pattern)
        
        if not games_files:
            print("❌ No historical game results found")
            print("\n💡 Run this command to get 2024 game results:")
            print("   python game_results_scraper.py")
            print("\n   Year: 2024")
            return False
        
        latest_games = max(games_files)
        self.games_path = latest_games
        print(f"✅ Found game results: {os.path.basename(latest_games)}")
        
        return True
    
    def load_data(self):
        """Load historical data"""
        print("\nSTEP 2: LOADING HISTORICAL DATA")
        print("-"*70)
        
        # Load KenPom
        self.kenpom_data = pd.read_csv(self.kenpom_path)
        print(f"✅ Loaded {len(self.kenpom_data)} teams from KenPom")
        
        # Load game results
        self.historical_games = pd.read_csv(self.games_path)
        print(f"✅ Loaded {len(self.historical_games)} games")
        
        return True
    
    def run_backtest(self):
        """Run the backtest"""
        print("\nSTEP 3: RUNNING BACKTEST")
        print("-"*70)
        
        backtester = NCAABBacktesterIntegrated(self.kenpom_path)
        
        # Generate predictions
        self.predictions = backtester.generate_predictions(self.historical_games)
        
        if self.predictions is None or len(self.predictions) == 0:
            print("❌ No predictions generated")
            return False
        
        # Calculate metrics
        self.metrics = backtester.calculate_metrics(self.predictions)
        
        if not self.metrics:
            print("❌ Could not calculate metrics")
            return False
        
        # Display metrics
        backtester.display_metrics(self.metrics)
        
        # Save locally
        backtester.save_results_local(self.predictions, self.metrics)
        
        return True
    
    def upload_to_sheets(self):
        """Upload results to Google Sheets"""
        print("\nSTEP 4: UPLOADING TO GOOGLE SHEETS")
        print("-"*70)
        
        try:
            uploader = NCAABSheetsUploaderEnhanced(
                credentials_path=GOOGLE_CREDENTIALS_PATH,
                sheet_id=GOOGLE_SHEET_ID
            )
            
            uploader.upload_backtest_results(
                predictions_df=self.predictions,
                metrics=self.metrics,
                tab_name='Backtesting'
            )
            
            print(f"\n✅ Uploaded to Google Sheets")
            print(f"🔗 View: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading to Google Sheets: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def run(self):
        """Run complete workflow"""
        self.print_header()
        
        # Step 1: Check data
        if not self.check_historical_data():
            print("\n❌ Historical data missing - cannot proceed")
            print("\nPlease run the data collection scripts first:")
            print("  1. python historical_kenpom_scraper.py")
            print("  2. python game_results_scraper.py")
            return False
        
        # Step 2: Load data
        if not self.load_data():
            print("\n❌ Failed to load data")
            return False
        
        # Step 3: Run backtest
        if not self.run_backtest():
            print("\n❌ Backtest failed")
            return False
        
        # Step 4: Upload to Sheets
        sheets_success = self.upload_to_sheets()
        if not sheets_success:
            print("\n⚠️  Results generated but not uploaded to Sheets")
            print("   Check local files in backend/data/backtesting/")
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "="*70)
        print("✅ BACKTESTING WORKFLOW COMPLETE")
        print(f"Time: {int(duration // 60)}m {int(duration % 60)}s")
        print("="*70)
        
        return True


def main():
    """Main entry point"""
    workflow = NCAABBacktestWorkflow()
    success = workflow.run()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
