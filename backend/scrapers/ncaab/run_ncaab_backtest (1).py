#!/usr/bin/env python3
"""
NCAA Basketball Backtesting Workflow - Complete Script
Runs full backtest: Load data -> Predict -> Calculate metrics -> Upload to Sheets
"""

import pandas as pd
import numpy as np
import os
import sys
import glob
from datetime import datetime

# Add backend to path
sys.path.insert(0, 'backend')

try:
    from config import (
        GOOGLE_CREDENTIALS_PATH, GOOGLE_SHEET_ID,
        HOME_COURT_ADVANTAGE, LEAGUE_AVG_EFFICIENCY
    )
except ImportError:
    print("❌ Error: config.py not found")
    print("   Run: python setup_ncaab.py")
    sys.exit(1)

# Import prediction model
try:
    from models.ncaab.totals_predictor import NCAABTotalsPredictor
except ImportError:
    print("❌ Error: Prediction model not found")
    sys.exit(1)

# Import enhanced sheets uploader
try:
    sys.path.insert(0, '.')
    from ncaab_sheets_uploader_enhanced import NCAABSheetsUploaderEnhanced
except ImportError:
    print("⚠️  Warning: Enhanced sheets uploader not found")
    print("   Backtest will run but won't upload to Google Sheets")
    NCAABSheetsUploaderEnhanced = None


class NCAABBacktesterIntegrated:
    """Integrated backtester with prediction generation and metrics"""
    
    def __init__(self, kenpom_data):
        self.kenpom_data = kenpom_data
        self.predictor = NCAABTotalsPredictor(
            kenpom_data=kenpom_data,
            home_court_advantage=HOME_COURT_ADVANTAGE,
            league_avg_eff=LEAGUE_AVG_EFFICIENCY
        )
    
    def generate_predictions(self, games_df):
        """Generate predictions for all historical games"""
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
                if successful % 500 == 0:
                    print(f"   Progress: {successful} predictions generated...")
            else:
                failed += 1
        
        print(f"   ✅ Successful predictions: {successful}")
        if failed > 0:
            pct_failed = (failed / (successful + failed)) * 100
            print(f"   ⚠️  Failed predictions: {failed} ({pct_failed:.1f}%)")
            if pct_failed > 15:
                print(f"   ⚠️  High failure rate - check team name matching")
        
        return pd.DataFrame(predictions)
    
    def calculate_metrics(self, predictions_df):
        """Calculate comprehensive performance metrics"""
        df = predictions_df.dropna(subset=['Actual_Total'])
        
        if len(df) == 0:
            return {}
        
        print(f"\n📈 Calculating metrics for {len(df)} games...")
        
        # Core metrics
        mae = df['Abs_Error'].mean()
        rmse = np.sqrt((df['Error'] ** 2).mean())
        median_ae = df['Abs_Error'].median()
        
        # Accuracy bands
        within_3 = (df['Abs_Error'] <= 3).sum() / len(df) * 100
        within_5 = (df['Abs_Error'] <= 5).sum() / len(df) * 100
        within_7 = (df['Abs_Error'] <= 7).sum() / len(df) * 100
        within_10 = (df['Abs_Error'] <= 10).sum() / len(df) * 100
        
        # Bias analysis
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
            'over_predictions': over_predictions,
            'under_predictions': under_predictions,
            'avg_total': round(df['Actual_Total'].mean(), 1),
            'avg_prediction': round(df['Model_Total'].mean(), 1)
        }
        
        return metrics
    
    def display_metrics(self, metrics):
        """Display metrics in readable format"""
        print("\n" + "="*70)
        print("BACKTESTING RESULTS")
        print("="*70)
        
        print(f"\n📊 Sample Size: {metrics['total_games']:,} games")
        print(f"📊 Average Actual Total: {metrics['avg_total']}")
        print(f"📊 Average Model Prediction: {metrics['avg_prediction']}")
        
        print("\n🎯 Accuracy Metrics:")
        print(f"   Mean Absolute Error (MAE): {metrics['mae']} points")
        print(f"   Root Mean Squared Error (RMSE): {metrics['rmse']} points")
        print(f"   Median Absolute Error: {metrics['median_ae']} points")
        
        # Interpret MAE
        if metrics['mae'] < 5:
            print(f"   ✅ Excellent accuracy!")
        elif metrics['mae'] < 7:
            print(f"   ✅ Good accuracy - ready for production")
        elif metrics['mae'] < 8:
            print(f"   ⚠️  Acceptable - consider calibration")
        else:
            print(f"   ❌ Needs calibration - adjust parameters")
        
        print("\n✅ Predictions Within:")
        print(f"   ±3 points: {metrics['within_3_pct']}%")
        print(f"   ±5 points: {metrics['within_5_pct']}%")
        print(f"   ±7 points: {metrics['within_7_pct']}%")
        print(f"   ±10 points: {metrics['within_10_pct']}%")
        
        # Interpret within ±5
        if metrics['within_5_pct'] > 50:
            print(f"   ✅ Excellent precision!")
        elif metrics['within_5_pct'] > 40:
            print(f"   ✅ Professional-level precision")
        elif metrics['within_5_pct'] > 35:
            print(f"   ⚠️  Acceptable precision")
        else:
            print(f"   ❌ Low precision - needs improvement")
        
        print("\n🔄 Prediction Bias:")
        over_pct = metrics['over_predictions'] / metrics['total_games'] * 100
        under_pct = metrics['under_predictions'] / metrics['total_games'] * 100
        print(f"   Over-predictions: {metrics['over_predictions']:,} ({over_pct:.1f}%)")
        print(f"   Under-predictions: {metrics['under_predictions']:,} ({under_pct:.1f}%)")
        
        # Interpret bias
        if 48 <= over_pct <= 52:
            print(f"   ✅ Excellent balance - no systematic bias")
        elif 45 <= over_pct <= 55:
            print(f"   ✅ Good balance")
        else:
            print(f"   ⚠️  Biased - consider adjusting LEAGUE_AVG_EFFICIENCY")
        
        print("\n" + "="*70)
    
    def save_results(self, predictions_df, metrics, output_dir='backend/data/backtesting'):
        """Save backtest results to CSV"""
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
    """Main workflow orchestrator"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.kenpom_data = None
        self.games_data = None
        self.predictions = None
        self.metrics = None
    
    def print_header(self):
        print("="*70)
        print("NCAA BASKETBALL BACKTESTING WORKFLOW")
        print("="*70)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
    
    def check_historical_data(self):
        """Check if historical data exists"""
        print("STEP 1: CHECKING HISTORICAL DATA")
        print("-"*70)
        
        historical_dir = "backend/data/historical"
        
        # Find KenPom data
        kenpom_pattern = f"{historical_dir}/kenpom_*_season_*.csv"
        kenpom_files = glob.glob(kenpom_pattern)
        
        if not kenpom_files:
            print("❌ No historical KenPom data found")
            print(f"   Run: python historical_kenpom_scraper.py")
            return False
        
        self.kenpom_file = max(kenpom_files)
        print(f"✅ Found KenPom data: {os.path.basename(self.kenpom_file)}")
        
        # Find game results
        games_pattern = f"{historical_dir}/game_results_*_season_*.csv"
        games_files = glob.glob(games_pattern)
        
        if not games_files:
            print("❌ No historical game results found")
            print(f"   Run: python game_results_scraper.py")
            return False
        
        self.games_file = max(games_files)
        print(f"✅ Found game results: {os.path.basename(self.games_file)}")
        
        return True
    
    def load_data(self):
        """Load historical data"""
        print("\nSTEP 2: LOADING HISTORICAL DATA")
        print("-"*70)
        
        try:
            # Load KenPom
            self.kenpom_data = pd.read_csv(self.kenpom_file)
            print(f"✅ Loaded {len(self.kenpom_data)} teams from KenPom")
            
            # Verify columns
            required_cols = ['Team', 'AdjTempo', 'AdjOffEff', 'AdjDefEff']
            missing = [col for col in required_cols if col not in self.kenpom_data.columns]
            if missing:
                print(f"❌ Missing KenPom columns: {missing}")
                return False
            
            # Load games
            self.games_data = pd.read_csv(self.games_file)
            print(f"✅ Loaded {len(self.games_data):,} historical games")
            
            # Verify columns
            required_cols = ['Home_Team', 'Away_Team', 'Actual_Total']
            missing = [col for col in required_cols if col not in self.games_data.columns]
            if missing:
                print(f"❌ Missing game columns: {missing}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {str(e)}")
            return False
    
    def run_backtest(self):
        """Run the backtest"""
        print("\nSTEP 3: RUNNING BACKTEST")
        print("-"*70)
        
        try:
            backtester = NCAABBacktesterIntegrated(kenpom_data=self.kenpom_data)
            
            # Generate predictions
            self.predictions = backtester.generate_predictions(self.games_data)
            
            if self.predictions is None or len(self.predictions) == 0:
                print("❌ No predictions generated")
                return False
            
            # Calculate metrics
            self.metrics = backtester.calculate_metrics(self.predictions)
            
            if not self.metrics:
                print("❌ Could not calculate metrics")
                return False
            
            # Display results
            backtester.display_metrics(self.metrics)
            
            # Save results
            backtester.save_results(self.predictions, self.metrics)
            
            return True
            
        except Exception as e:
            print(f"❌ Error during backtest: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def upload_to_sheets(self):
        """Upload results to Google Sheets"""
        print("\nSTEP 4: UPLOADING TO GOOGLE SHEETS")
        print("-"*70)
        
        if NCAABSheetsUploaderEnhanced is None:
            print("⚠️  Enhanced sheets uploader not available")
            print("   Results saved locally only")
            return False
        
        try:
            uploader = NCAABSheetsUploaderEnhanced(
                credentials_path=GOOGLE_CREDENTIALS_PATH,
                sheet_id=GOOGLE_SHEET_ID
            )
            
            uploader.upload_backtest_results(self.predictions, self.metrics)
            
            print(f"\n✅ Upload complete!")
            print(f"🔗 View: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}")
            print(f"   Check the 'Backtesting' tab")
            
            return True
            
        except Exception as e:
            print(f"❌ Error uploading to Google Sheets: {str(e)}")
            print(f"   Results are still saved locally")
            return False
    
    def run(self):
        """Run complete workflow"""
        self.print_header()
        
        # Step 1: Check data
        if not self.check_historical_data():
            print("\n❌ Workflow failed at Step 1")
            return False
        
        # Step 2: Load data
        if not self.load_data():
            print("\n❌ Workflow failed at Step 2")
            return False
        
        # Step 3: Run backtest
        if not self.run_backtest():
            print("\n❌ Workflow failed at Step 3")
            return False
        
        # Step 4: Upload to sheets
        sheets_success = self.upload_to_sheets()
        if not sheets_success:
            print("   ⚠️  Backtest complete but not uploaded to Sheets")
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "="*70)
        print("✅ BACKTESTING WORKFLOW COMPLETE")
        print(f"Time: {int(duration // 60)}m {int(duration % 60)}s")
        print(f"Games analyzed: {len(self.predictions.dropna(subset=['Actual_Total'])):,}")
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
