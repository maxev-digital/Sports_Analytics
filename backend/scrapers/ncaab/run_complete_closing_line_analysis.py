#!/usr/bin/env python3
"""
Complete NCAA Closing Line Analysis Workflow
Runs all analysis components and uploads results to Google Sheets

Workflow:
1. Run unit tests to validate components
2. Analyze closing line accuracy
3. Simulate betting strategy
4. Validate regression hypothesis
5. Upload comprehensive results to Google Sheets
"""

import pandas as pd
import os
import sys
import glob
from datetime import datetime
import subprocess

# Add backend to path
sys.path.insert(0, 'backend')
sys.path.insert(0, '.')

# Import components
try:
    from analyze_closing_line_accuracy import ClosingLineAccuracyAnalyzer
    from simulate_closing_line_bets import ClosingLineBetSimulator
    from validate_regression_hypothesis import RegressionHypothesisValidator
except ImportError as e:
    print(f"ERROR: Error importing modules: {e}")
    sys.exit(1)

# Import Google Sheets uploader
try:
    from ncaab_sheets_uploader_enhanced import NCAABSheetsUploaderEnhanced
except ImportError:
    print("WARNING:  Enhanced sheets uploader not found")
    NCAABSheetsUploaderEnhanced = None


class CompleteClosingLineWorkflow:
    """Runs complete closing line analysis workflow"""

    def __init__(self):
        self.start_time = datetime.now()
        self.results = {}

        # Configuration
        try:
            from config import GOOGLE_CREDENTIALS_PATH, GOOGLE_SHEET_ID
            self.google_credentials = GOOGLE_CREDENTIALS_PATH
            self.google_sheet_id = GOOGLE_SHEET_ID
        except:
            self.google_credentials = "google_sheets/credentials/service-account-key.json"
            self.google_sheet_id = "1M5Oe0pZU_Apy3EO0YaUU13uJW98joGnlrtd9Wba2ukA"

    def print_header(self):
        """Print workflow header"""
        print("="*80)
        print("NCAA BASKETBALL COMPLETE CLOSING LINE ANALYSIS")
        print("="*80)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("")

    def run_tests(self):
        """Run unit tests"""
        print("\n[STEP 1/5] RUNNING UNIT TESTS")
        print("-"*80)

        try:
            # Import and run tests
            from test_closing_line_analysis import run_all_tests

            success = run_all_tests()

            if not success:
                print("WARNING:  Some tests failed - continuing anyway")

            self.results['tests_passed'] = success
            return True

        except Exception as e:
            print(f"ERROR: Error running tests: {e}")
            print("   Continuing without test validation...")
            self.results['tests_passed'] = False
            return True

    def analyze_accuracy(self):
        """Analyze closing line accuracy"""
        print("\n[STEP 2/5] ANALYZING CLOSING LINE ACCURACY")
        print("-"*80)

        try:
            analyzer = ClosingLineAccuracyAnalyzer(use_backtest_predictions=True)

            # Load data
            if not analyzer.load_historical_data():
                return False

            # Try to load predictions, fall back to simulated
            if analyzer.load_backtest_predictions():
                analyzer.merge_with_predictions()
            else:
                print("   Using simulated closing lines...")
                analyzer.add_simulated_closing_lines()

            # Run analysis
            if not analyzer.analyze_accuracy():
                return False

            if not analyzer.create_threshold_table():
                return False

            # Save results
            analyzer.save_local_results()

            # Store for upload
            self.results['accuracy_analysis'] = analyzer.analysis_results
            self.results['threshold_table'] = analyzer.threshold_table

            print("    Accuracy analysis complete")
            return True

        except Exception as e:
            print(f"ERROR: Error in accuracy analysis: {e}")
            return False

    def simulate_bets(self):
        """Simulate betting strategy"""
        print("\n[STEP 3/5] SIMULATING BETTING STRATEGY")
        print("-"*80)

        try:
            # Find data files
            historical_dir = "backend/data/historical"
            games_pattern = f"{historical_dir}/game_results_*_season_*.csv"
            games_files = glob.glob(games_pattern)

            if not games_files:
                print("ERROR: No historical games found")
                return False

            latest_games = max(games_files)

            # Find predictions (optional)
            backtest_dir = "backend/data/backtesting"
            pred_pattern = f"{backtest_dir}/predictions_*.csv"
            pred_files = glob.glob(pred_pattern)
            latest_predictions = max(pred_files) if pred_files else None

            # Run simulation
            simulator = ClosingLineBetSimulator(
                historical_games_path=latest_games,
                predictions_path=latest_predictions
            )

            if not simulator.merge_data():
                return False

            if not simulator.simulate_live_betting():
                return False

            simulator.calculate_performance()
            simulator.display_results()

            # Save results
            simulator.save_results()

            # Store for upload
            self.results['simulation'] = simulator.performance_summary
            self.results['bet_log'] = simulator.bet_log

            print("    Bet simulation complete")
            return True

        except Exception as e:
            print(f"ERROR: Error in bet simulation: {e}")
            import traceback
            traceback.print_exc()
            return False

    def validate_hypothesis(self):
        """Validate regression hypothesis"""
        print("\n[STEP 4/5] VALIDATING REGRESSION HYPOTHESIS")
        print("-"*80)

        try:
            # Find data files
            historical_dir = "backend/data/historical"
            games_pattern = f"{historical_dir}/game_results_*_season_*.csv"
            games_files = glob.glob(games_pattern)

            if not games_files:
                print("ERROR: No historical games found")
                return False

            latest_games = max(games_files)

            # Find predictions (optional)
            backtest_dir = "backend/data/backtesting"
            pred_pattern = f"{backtest_dir}/predictions_*.csv"
            pred_files = glob.glob(pred_pattern)
            latest_predictions = max(pred_files) if pred_files else None

            # Run validation
            validator = RegressionHypothesisValidator(
                historical_games_path=latest_games,
                predictions_path=latest_predictions
            )

            validator.calculate_regression_metrics()
            validator.test_all_thresholds()
            optimal_df = validator.test_optimal_threshold()
            directional = validator.test_directional_effects()

            validator.generate_report()
            validator.save_results()

            # Store for upload
            self.results['hypothesis_validation'] = validator.results
            self.results['optimal_threshold'] = optimal_df
            self.results['directional'] = directional

            print("    Hypothesis validation complete")
            return True

        except Exception as e:
            print(f"ERROR: Error in hypothesis validation: {e}")
            import traceback
            traceback.print_exc()
            return False

    def upload_to_sheets(self):
        """Upload all results to Google Sheets"""
        print("\n[STEP 5/5] UPLOADING TO GOOGLE SHEETS")
        print("-"*80)

        if NCAABSheetsUploaderEnhanced is None:
            print("   WARNING:  Sheets uploader not available - skipping upload")
            return False

        try:
            uploader = NCAABSheetsUploaderEnhanced(
                credentials_path=self.google_credentials,
                sheet_id=self.google_sheet_id
            )

            uploader.connect()

            # Upload accuracy analysis
            if 'accuracy_analysis' in self.results:
                self._upload_accuracy_analysis(uploader)

            # Upload bet simulation results
            if 'simulation' in self.results:
                self._upload_simulation_results(uploader)

            # Upload hypothesis validation
            if 'hypothesis_validation' in self.results:
                self._upload_hypothesis_results(uploader)

            print(f"\n    All results uploaded to Google Sheets")
            print(f"    View: https://docs.google.com/spreadsheets/d/{self.google_sheet_id}")

            return True

        except Exception as e:
            print(f"   ERROR: Error uploading to sheets: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _upload_accuracy_analysis(self, uploader):
        """Upload accuracy analysis to sheets"""
        worksheet = uploader.get_or_create_worksheet("Line Accuracy")
        worksheet.clear()

        analysis = self.results['accuracy_analysis']
        threshold_table = self.results['threshold_table']

        # Create summary data
        data = [
            [' CLOSING LINE ACCURACY ANALYSIS', ''],
            ['', ''],
            ['Total Games', analysis['total_games']],
            ['Average Closing Total', analysis['avg_closing_total']],
            ['Average Actual Total', analysis['avg_actual_total']],
            ['', ''],
            [' ACCURACY METRICS', ''],
            ['Mean Error', f"{analysis['mean_error']} pts"],
            ['Std Deviation', f"{analysis['std_deviation']} pts"],
            ['MAE', f"{analysis['mae']} pts"],
            ['', ''],
            [' THRESHOLDS', ''],
            ['Movement', 'Historical %', 'Regression %', 'Recommendation']
        ]

        # Add threshold rows
        for _, row in threshold_table.iterrows():
            data.append([
                f"±{row['movement']} pts",
                f"{row['historical_accuracy']}%",
                f"{row['regression_prob']}%",
                row['recommendation']
            ])

        worksheet.update('A1', data, value_input_option='RAW')
        print("    Uploaded accuracy analysis")

    def _upload_simulation_results(self, uploader):
        """Upload simulation results to sheets"""
        worksheet = uploader.get_or_create_worksheet("Bet Simulation")
        worksheet.clear()

        sim = self.results['simulation']

        # Create summary data
        data = [
            [' BET SIMULATION RESULTS', ''],
            ['', ''],
            ['Total Opportunities', sim['total_bets']],
            ['Wins', sim['wins']],
            ['Losses', sim['losses']],
            ['Pushes', sim['pushes']],
            ['Win Rate', f"{sim['win_rate']}%"],
            ['Total Profit', f"{sim['total_profit']:+.2f} units"],
            ['ROI', f"{sim['roi']:+.1f}%"],
            ['Regression Rate', f"{sim['regression_rate']}%"],
            ['', ''],
            [' BY THRESHOLD', ''],
            ['Tier', 'Threshold', 'Opportunities', 'Wins', 'Losses', 'Win Rate', 'Profit', 'ROI']
        ]

        # Add tier performance
        if not sim['tier_performance'].empty:
            for _, row in sim['tier_performance'].iterrows():
                data.append([
                    row['tier'],
                    f"±{row['threshold']} pts",
                    row['opportunities'],
                    row['wins'],
                    row['losses'],
                    f"{row['win_rate']}%",
                    f"{row['profit']:+.2f}",
                    f"{row['roi']:+.1f}%"
                ])

        worksheet.update('A1', data, value_input_option='RAW')
        print("    Uploaded bet simulation")

    def _upload_hypothesis_results(self, uploader):
        """Upload hypothesis validation to sheets"""
        worksheet = uploader.get_or_create_worksheet("Hypothesis Validation")
        worksheet.clear()

        results = self.results['hypothesis_validation']

        # Create summary data
        data = [
            [' REGRESSION HYPOTHESIS VALIDATION', ''],
            ['', ''],
            ['Hypothesis: Games that move X+ points from closing regress back', ''],
            ['', ''],
            ['Threshold', 'Scenarios', 'Regressed', 'Rate %', '95% CI', 'P-value', 'Significant?']
        ]

        # Add test results
        for threshold, result in results.items():
            data.append([
                f"±{threshold} pts",
                result['n_scenarios'],
                result['n_regressed'],
                f"{result['regression_rate']}%",
                f"[{result['ci_lower']}%, {result['ci_upper']}%]",
                f"{result['p_value']:.4f}",
                ' Yes' if result['significant'] else 'ERROR: No'
            ])

        worksheet.update('A1', data, value_input_option='RAW')
        print("    Uploaded hypothesis validation")

    def generate_summary_report(self):
        """Generate final summary report"""
        print("\n" + "="*80)
        print("COMPLETE ANALYSIS SUMMARY")
        print("="*80)

        # Timing
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        print(f"\n  Total Time: {int(duration // 60)}m {int(duration % 60)}s")

        # Tests
        if 'tests_passed' in self.results:
            status = " PASSED" if self.results['tests_passed'] else "WARNING:  SOME FAILURES"
            print(f" Unit Tests: {status}")

        # Accuracy
        if 'accuracy_analysis' in self.results:
            analysis = self.results['accuracy_analysis']
            print(f"\n Closing Line Accuracy:")
            print(f"   Sample Size: {analysis['total_games']:,} games")
            print(f"   MAE: {analysis['mae']} points")
            print(f"   Std Dev: {analysis['std_deviation']} points")

        # Simulation
        if 'simulation' in self.results:
            sim = self.results['simulation']
            print(f"\n Bet Simulation:")
            print(f"   Opportunities: {sim['total_bets']:,}")
            print(f"   Win Rate: {sim['win_rate']}%")
            print(f"   ROI: {sim['roi']:+.1f}%")
            print(f"   Profit: {sim['total_profit']:+.2f} units")

            # Profitability assessment
            if sim['win_rate'] > 52.38:
                print(f"    PROFITABLE strategy at -110 odds")
            else:
                print(f"   ERROR: UNPROFITABLE - need better odds or threshold")

        # Hypothesis
        if 'hypothesis_validation' in self.results:
            results = self.results['hypothesis_validation']
            significant_count = sum(1 for r in results.values() if r['significant'])
            print(f"\n Hypothesis Validation:")
            print(f"   Significant Results: {significant_count}/{len(results)}")

            # Find best threshold
            best = max(results.items(), key=lambda x: x[1]['regression_rate'])
            print(f"   Best Threshold: ±{best[0]} pts ({best[1]['regression_rate']}%)")

        print("\n RECOMMENDATIONS:")

        if 'simulation' in self.results:
            sim = self.results['simulation']
            if not sim['tier_performance'].empty:
                profitable = sim['tier_performance'][sim['tier_performance']['roi'] > 0]
                if len(profitable) > 0:
                    best_tier = profitable.nlargest(1, 'roi').iloc[0]
                    print(f"    Use ±{best_tier['threshold']} point threshold")
                    print(f"    Expected ROI: {best_tier['roi']:+.1f}%")
                else:
                    print(f"   ERROR: No profitable thresholds found at current odds")
                    print(f"    Consider: Better odds, larger thresholds, or different strategy")

        print("\n📁 All results saved to: backend/data/analysis/")
        print(f" Google Sheets: https://docs.google.com/spreadsheets/d/{self.google_sheet_id}")

        print("\n" + "="*80)

    def run(self):
        """Run complete workflow"""
        self.print_header()

        # Step 1: Tests
        if not self.run_tests():
            print("\nWARNING:  Tests failed but continuing...")

        # Step 2: Accuracy analysis
        if not self.analyze_accuracy():
            print("\nERROR: Workflow failed at accuracy analysis")
            return False

        # Step 3: Bet simulation
        if not self.simulate_bets():
            print("\nERROR: Workflow failed at bet simulation")
            return False

        # Step 4: Hypothesis validation
        if not self.validate_hypothesis():
            print("\nERROR: Workflow failed at hypothesis validation")
            return False

        # Step 5: Upload to sheets
        sheets_success = self.upload_to_sheets()
        if not sheets_success:
            print("\nWARNING:  Google Sheets upload failed - results saved locally")

        # Final summary
        self.generate_summary_report()

        return True


def main():
    """Main entry point"""
    workflow = CompleteClosingLineWorkflow()
    success = workflow.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
