#!/usr/bin/env python3
"""
NCAA Basketball Closing Line Accuracy Analyzer
Analyzes how accurate closing totals are vs actual game totals
Establishes thresholds for live middle betting opportunities
Uploads results to Google Sheets
"""

import pandas as pd
import numpy as np
import glob
import os
import sys
from datetime import datetime
from scipy import stats

# Add backend to path for imports
sys.path.insert(0, 'backend')

# Import Google Sheets uploader
sys.path.insert(0, '.')
try:
    from ncaab_sheets_uploader_enhanced import NCAABSheetsUploaderEnhanced
except ImportError:
    print("Warning: Enhanced sheets uploader not found")
    NCAABSheetsUploaderEnhanced = None


class ClosingLineAccuracyAnalyzer:
    """Analyzes closing line accuracy to establish betting thresholds"""
    
    def __init__(self, use_backtest_predictions=False):
        self.games_data = None
        self.analysis_results = None
        self.threshold_table = None
        self.use_backtest_predictions = use_backtest_predictions
        self.predictions_data = None

    def load_historical_data(self):
        """Load historical game results with actual totals"""
        print("Loading historical game data...")

        # Find game results files
        games_pattern = "backend/data/historical/game_results_*_season_*.csv"
        games_files = glob.glob(games_pattern)

        if not games_files:
            print("ERROR: No historical game results found")
            print("   Run: python game_results_scraper.py first")
            return False

        # Load most recent file
        latest_file = max(games_files)
        self.games_data = pd.read_csv(latest_file)

        print(f"   Loaded {len(self.games_data):,} games from {os.path.basename(latest_file)}")

        # Check for required columns
        if 'Actual_Total' not in self.games_data.columns:
            print("ERROR: Missing Actual_Total column")
            return False

        return True

    def load_backtest_predictions(self):
        """Load backtest predictions to use as proxy closing lines"""
        print("\nLoading backtest predictions...")

        pred_pattern = "backend/data/backtesting/predictions_*.csv"
        pred_files = glob.glob(pred_pattern)

        if not pred_files:
            print("   WARNING: No backtest predictions found")
            print("   Run: python run_ncaab_backtest.py first")
            return False

        # Load most recent predictions
        latest_pred = max(pred_files)
        self.predictions_data = pd.read_csv(latest_pred)

        print(f"   Loaded {len(self.predictions_data):,} predictions from {os.path.basename(latest_pred)}")

        return True

    def merge_with_predictions(self):
        """Merge games with predictions to get model-based closing lines"""
        if self.predictions_data is None:
            print("   WARNING: No predictions to merge")
            return False

        print("\nMerging games with predictions...")

        # Merge on team names
        merged = pd.merge(
            self.games_data,
            self.predictions_data,
            on=['Home_Team', 'Away_Team'],
            how='inner'
        )

        # Use Model_Total as Closing_Total
        if 'Model_Total' in merged.columns:
            merged['Closing_Total'] = merged['Model_Total']
            # Use Actual_Total_x (from games) as the true actual
            if 'Actual_Total_x' in merged.columns:
                merged['Actual_Total'] = merged['Actual_Total_x']

        print(f"   Matched {len(merged):,} games ({len(merged)/len(self.games_data)*100:.1f}%)")

        self.games_data = merged
        return True
    
    def add_simulated_closing_lines(self):
        """
        Add simulated closing lines for analysis
        In reality, you'd get these from odds data
        For now, we'll simulate them as Actual_Total + small random noise
        """
        print("\nSimulating closing lines...")
        
        # In a real scenario, you'd load actual closing lines
        # For demonstration, we'll create realistic closing lines
        # Closing lines are typically very close to actual totals with some variance
        
        np.random.seed(42)  # For reproducibility
        
        # Add realistic noise to simulate closing lines
        # Standard deviation of ~8-10 points is realistic for NCAA
        noise = np.random.normal(0, 8.5, len(self.games_data))
        
        # Round to nearest 0.5 (how totals are typically set)
        self.games_data['Closing_Total'] = np.round(
            self.games_data['Actual_Total'] + noise * 0.5
        ) / 0.5
        
        print(f"   Added closing lines for {len(self.games_data):,} games")
    
    def analyze_accuracy(self):
        """Analyze closing line accuracy vs actual results"""
        print("\nAnalyzing closing line accuracy...")
        
        # Calculate differences
        self.games_data['Error'] = self.games_data['Closing_Total'] - self.games_data['Actual_Total']
        self.games_data['Abs_Error'] = abs(self.games_data['Error'])
        
        # Calculate key statistics
        mean_error = self.games_data['Error'].mean()
        median_error = self.games_data['Error'].median()
        std_error = self.games_data['Error'].std()
        mae = self.games_data['Abs_Error'].mean()
        
        # Calculate percentiles
        percentiles = [50, 68, 80, 90, 95, 99, 99.7]
        percentile_values = {}
        
        for p in percentiles:
            percentile_values[p] = np.percentile(self.games_data['Abs_Error'], p)
        
        # Store results
        self.analysis_results = {
            'total_games': len(self.games_data),
            'mean_error': round(mean_error, 2),
            'median_error': round(median_error, 2),
            'std_deviation': round(std_error, 2),
            'mae': round(mae, 2),
            'percentiles': percentile_values,
            'avg_actual_total': round(self.games_data['Actual_Total'].mean(), 1),
            'avg_closing_total': round(self.games_data['Closing_Total'].mean(), 1)
        }
        
        # Display results
        print("\n" + "="*60)
        print("CLOSING LINE ACCURACY ANALYSIS")
        print("="*60)
        print(f"\nSample Size: {self.analysis_results['total_games']:,} games")
        print(f"Average Actual Total: {self.analysis_results['avg_actual_total']}")
        print(f"Average Closing Total: {self.analysis_results['avg_closing_total']}")

        print(f"\nAccuracy Metrics:")
        print(f"   Mean Error: {self.analysis_results['mean_error']} points")
        print(f"   Median Error: {self.analysis_results['median_error']} points")
        print(f"   Standard Deviation: {self.analysis_results['std_deviation']} points")
        print(f"   Mean Absolute Error: {self.analysis_results['mae']} points")
        
        print(f"\nError Distribution (% of games within range):")
        for p in percentiles:
            value = percentile_values[p]
            print(f"   {p:5.1f}% of games finish within +/-{value:5.1f} points of closing")
        
        return True
    
    def create_threshold_table(self):
        """Create betting threshold recommendations"""
        print("\nCreating threshold recommendations...")
        
        std = self.analysis_results['std_deviation']
        
        # Define thresholds based on standard deviations
        thresholds = [
            {
                'movement': 8,
                'std_multiple': round(8 / std, 1),
                'historical_accuracy': self._calculate_percentage_within(8),
                'regression_prob': 0,  # Will calculate
                'recommendation': 'Pass - Too Common'
            },
            {
                'movement': 12,
                'std_multiple': round(12 / std, 1),
                'historical_accuracy': self._calculate_percentage_within(12),
                'regression_prob': 0,
                'recommendation': 'Consider - Moderate Edge'
            },
            {
                'movement': 16,
                'std_multiple': round(16 / std, 1),
                'historical_accuracy': self._calculate_percentage_within(16),
                'regression_prob': 0,
                'recommendation': 'Good - Strong Edge'
            },
            {
                'movement': 20,
                'std_multiple': round(20 / std, 1),
                'historical_accuracy': self._calculate_percentage_within(20),
                'regression_prob': 0,
                'recommendation': 'Excellent - Very Strong'
            },
            {
                'movement': 24,
                'std_multiple': round(24 / std, 1),
                'historical_accuracy': self._calculate_percentage_within(24),
                'regression_prob': 0,
                'recommendation': 'Max Bet - Extreme Value'
            },
            {
                'movement': 28,
                'std_multiple': round(28 / std, 1),
                'historical_accuracy': self._calculate_percentage_within(28),
                'regression_prob': 0,
                'recommendation': 'Max Bet - Historic Outlier'
            }
        ]
        
        # Calculate regression probability
        # If X% historically finish within range, then (100-X)/2 % chance it regresses back
        for t in thresholds:
            inside_pct = t['historical_accuracy']
            # Probability it regresses from outside to inside
            # Using simplified model: if you're outside the range, 50% + edge chance to regress
            t['regression_prob'] = round(50 + (inside_pct - 50) * 0.6, 1)
        
        self.threshold_table = pd.DataFrame(thresholds)
        
        # Display table
        print("\n" + "="*60)
        print("LIVE BETTING THRESHOLD RECOMMENDATIONS")
        print("="*60)
        print("\nWhen live total moves X points from closing:")
        print("-"*60)
        
        for _, row in self.threshold_table.iterrows():
            print(f"\n+/-{row['movement']} points ({row['std_multiple']}std):")
            print(f"   Historical: {row['historical_accuracy']:.1f}% finish within this range")
            print(f"   Regression Probability: {row['regression_prob']:.1f}%")
            print(f"   Action: {row['recommendation']}")
        
        return True
    
    def _calculate_percentage_within(self, threshold):
        """Calculate what percentage of games finish within threshold of closing"""
        within = (self.games_data['Abs_Error'] <= threshold).sum()
        total = len(self.games_data)
        return round((within / total) * 100, 1)
    
    def create_analytics_summary(self):
        """Create summary DataFrame for Google Sheets"""
        
        # Create summary section
        summary_data = [
            ['🎯 CLOSING LINE ACCURACY ANALYSIS', ''],
            ['', ''],
            ['Total Games Analyzed', self.analysis_results['total_games']],
            ['Average Closing Total', self.analysis_results['avg_closing_total']],
            ['Average Actual Total', self.analysis_results['avg_actual_total']],
            ['', ''],
            ['📊 ACCURACY METRICS', ''],
            ['Mean Error', f"{self.analysis_results['mean_error']} points"],
            ['Standard Deviation', f"{self.analysis_results['std_deviation']} points"],
            ['Mean Absolute Error', f"{self.analysis_results['mae']} points"],
            ['', ''],
            ['📈 PERCENTILE DISTRIBUTION', ''],
            ['50% of games within', f"±{self.analysis_results['percentiles'][50]:.1f} points"],
            ['68% of games within', f"±{self.analysis_results['percentiles'][68]:.1f} points"],
            ['80% of games within', f"±{self.analysis_results['percentiles'][80]:.1f} points"],
            ['90% of games within', f"±{self.analysis_results['percentiles'][90]:.1f} points"],
            ['95% of games within', f"±{self.analysis_results['percentiles'][95]:.1f} points"],
            ['99% of games within', f"±{self.analysis_results['percentiles'][99]:.1f} points"],
            ['', ''],
            ['🎲 LIVE BETTING THRESHOLDS', ''],
            ['Movement', 'Historical Accuracy', 'Regression Prob', 'Recommendation']
        ]
        
        # Add threshold recommendations
        for _, row in self.threshold_table.iterrows():
            summary_data.append([
                f"+/-{row['movement']} pts ({row['std_multiple']}std)",
                f"{row['historical_accuracy']}%",
                f"{row['regression_prob']}%",
                row['recommendation']
            ])
        
        return summary_data
    
    def upload_to_sheets(self):
        """Upload analysis to Google Sheets"""
        print("\nUploading to Google Sheets...")
        
        if NCAABSheetsUploaderEnhanced is None:
            print("   WARNING: Sheets uploader not available")
            return False
        
        try:
            # Your config values
            GOOGLE_SHEET_ID = "1M5Oe0pZU_Apy3EO0YaUU13uJW98joGnlrtd9Wba2ukA"
            GOOGLE_CREDENTIALS_PATH = "google_sheets/credentials/service-account-key.json"
            
            uploader = NCAABSheetsUploaderEnhanced(
                credentials_path=GOOGLE_CREDENTIALS_PATH,
                sheet_id=GOOGLE_SHEET_ID
            )
            
            # Connect
            uploader.connect()
            
            # Get or create worksheet
            worksheet = uploader.get_or_create_worksheet("Line Accuracy Analysis")
            
            # Clear existing data
            worksheet.clear()
            
            # Create and upload summary
            summary_data = self.create_analytics_summary()
            
            # Upload all data at once
            worksheet.update('A1', summary_data, value_input_option='RAW')
            
            # Format headers
            worksheet.format('A1:D1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
            
            print(f"   Uploaded to 'Line Accuracy Analysis' tab")
            print(f"   View: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}")
            
            return True
            
        except Exception as e:
            print(f"   ERROR uploading to sheets: {str(e)}")
            return False
    
    def save_local_results(self):
        """Save results locally"""
        output_dir = 'backend/data/analysis'
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save threshold table
        threshold_file = f"{output_dir}/threshold_analysis_{timestamp}.csv"
        self.threshold_table.to_csv(threshold_file, index=False)
        print(f"\nSaved threshold table: {threshold_file}")
        
        # Save detailed game analysis
        games_file = f"{output_dir}/games_accuracy_{timestamp}.csv"
        games_subset = self.games_data[['Home_Team', 'Away_Team', 'Actual_Total', 
                                        'Closing_Total', 'Error', 'Abs_Error']]
        games_subset.to_csv(games_file, index=False)
        print(f"Saved game analysis: {games_file}")


def main():
    """Run the closing line accuracy analysis"""
    print("="*70)
    print("NCAA BASKETBALL CLOSING LINE ACCURACY ANALYZER")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    # Check for command line args
    use_predictions = '--use-predictions' in sys.argv or '-p' in sys.argv

    analyzer = ClosingLineAccuracyAnalyzer(use_backtest_predictions=use_predictions)

    # Step 1: Load historical data
    if not analyzer.load_historical_data():
        print("ERROR: Failed to load data")
        return False

    # Step 2: Get closing lines (either from predictions or simulated)
    if use_predictions:
        print("\nUsing backtest predictions as closing lines")
        if analyzer.load_backtest_predictions():
            if not analyzer.merge_with_predictions():
                print("WARNING: Failed to merge - falling back to simulated lines")
                analyzer.add_simulated_closing_lines()
        else:
            print("WARNING: Falling back to simulated closing lines")
            analyzer.add_simulated_closing_lines()
    else:
        print("\nNOTE: Using simulated closing lines for demonstration")
        print("   Use --use-predictions flag to use backtest predictions")
        print("   Or provide actual historical closing lines from odds provider")
        analyzer.add_simulated_closing_lines()

    # Step 3: Analyze accuracy
    if not analyzer.analyze_accuracy():
        print("ERROR: Analysis failed")
        return False

    # Step 4: Create threshold table
    if not analyzer.create_threshold_table():
        print("ERROR: Failed to create thresholds")
        return False

    # Step 5: Save results
    analyzer.save_local_results()

    # Step 6: Upload to Google Sheets
    analyzer.upload_to_sheets()

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print("\nKEY FINDINGS:")
    print(f"   Standard Deviation: {analyzer.analysis_results['std_deviation']} points")
    print(f"   95% of games within: +/-{analyzer.analysis_results['percentiles'][95]:.1f} points")
    print(f"   99% of games within: +/-{analyzer.analysis_results['percentiles'][99]:.1f} points")

    print("\nRECOMMENDED STRATEGY:")
    print("   1. Watch games live")
    print("   2. When total moves 16+ points from closing - Consider betting")
    print("   3. When total moves 20+ points from closing - Strong bet")
    print("   4. When total moves 24+ points from closing - Max bet")

    print("\nNEXT STEPS:")
    if not use_predictions:
        print("   1. Run backtest: python run_ncaab_backtest.py")
        print("   2. Re-run with: python analyze_closing_line_accuracy.py --use-predictions")
    print("   3. Run bet simulation: python simulate_closing_line_bets.py")
    print("   4. Validate hypothesis: python validate_regression_hypothesis.py")
    print("   5. Build live monitoring system")

    print("="*70)


if __name__ == "__main__":
    main()
