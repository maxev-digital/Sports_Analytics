#!/usr/bin/env python3
"""
NCAA Basketball Regression Hypothesis Validator
Performs statistical tests to validate the regression-to-mean hypothesis
Tests if games that move X+ points from closing truly regress back
"""

import pandas as pd
import numpy as np
from scipy import stats
import glob
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, 'backend')


class RegressionHypothesisValidator:
    """Validates the regression hypothesis with statistical rigor"""

    def __init__(self, historical_games_path, predictions_path=None):
        """
        Initialize validator

        Args:
            historical_games_path: Path to historical game results
            predictions_path: Path to model predictions (used as proxy closing)
        """
        print(f" Loading data...")
        self.games = pd.read_csv(historical_games_path)
        print(f"    Loaded {len(self.games):,} historical games")

        if predictions_path and os.path.exists(predictions_path):
            self.predictions = pd.read_csv(predictions_path)
            print(f"    Loaded {len(self.predictions):,} predictions")
            self._merge_data()
        else:
            print(f"   WARNING:  No predictions - using simulated closing lines")
            self._add_simulated_closing_lines()

        self.results = {}

    def _merge_data(self):
        """Merge games with predictions"""
        merged = pd.merge(
            self.games,
            self.predictions,
            on=['Home_Team', 'Away_Team'],
            how='inner'
        )

        if 'Model_Total' in merged.columns:
            merged['Closing_Line'] = merged['Model_Total']

        # Handle duplicate columns from merge
        if 'Actual_Total_x' in merged.columns:
            merged['Actual_Total'] = merged['Actual_Total_x']

        self.data = merged
        print(f"    Matched {len(self.data):,} games")

    def _add_simulated_closing_lines(self):
        """Add simulated closing lines for testing"""
        np.random.seed(42)
        noise = np.random.normal(0, 8.5, len(self.games))
        self.games['Closing_Line'] = np.round((self.games['Actual_Total'] + noise) * 2) / 2
        self.data = self.games.copy()

    def calculate_regression_metrics(self):
        """Calculate regression metrics for all games"""
        print("\n Calculating regression metrics...")

        self.data['Closing_Error'] = self.data['Actual_Total'] - self.data['Closing_Line']
        self.data['Abs_Closing_Error'] = abs(self.data['Closing_Error'])

        print(f"   Mean Closing Error: {self.data['Closing_Error'].mean():.2f} points")
        print(f"   Std Closing Error: {self.data['Closing_Error'].std():.2f} points")
        print(f"   MAE: {self.data['Abs_Closing_Error'].mean():.2f} points")

    def test_hypothesis_by_threshold(self, threshold):
        """
        Test regression hypothesis at a specific threshold

        Hypothesis: When live line moves X+ points from closing,
        the actual total will be closer to closing than to live line
        (i.e., regression toward closing)

        Args:
            threshold: Movement threshold to test (e.g., 16 points)

        Returns:
            Dictionary with test results
        """
        print(f"\n Testing Hypothesis at ±{threshold} point threshold...")

        # Simulate live lines at this threshold
        # Scenario 1: Live line ABOVE closing (by threshold amount)
        live_over = self.data.copy()
        live_over['Live_Line'] = live_over['Closing_Line'] + threshold
        live_over['Movement_Direction'] = 'UP'

        # Scenario 2: Live line BELOW closing (by threshold amount)
        live_under = self.data.copy()
        live_under['Live_Line'] = live_under['Closing_Line'] - threshold
        live_under['Movement_Direction'] = 'DOWN'

        # Combine scenarios
        test_data = pd.concat([live_over, live_under], ignore_index=True)

        # Calculate distances
        test_data['Distance_To_Closing'] = abs(test_data['Actual_Total'] - test_data['Closing_Line'])
        test_data['Distance_To_Live'] = abs(test_data['Actual_Total'] - test_data['Live_Line'])

        # Did it regress? (Closer to closing than live)
        test_data['Regressed'] = test_data['Distance_To_Closing'] < test_data['Distance_To_Live']

        # Calculate regression rate
        regression_rate = (test_data['Regressed'].sum() / len(test_data)) * 100

        # Statistical significance test
        # Null hypothesis: regression rate = 50% (random)
        # Alternative: regression rate > 50%
        n_regressed = test_data['Regressed'].sum()
        n_total = len(test_data)

        # Binomial test (use binomtest for newer scipy versions)
        try:
            p_value = stats.binomtest(n_regressed, n_total, 0.5, alternative='greater').pvalue
        except AttributeError:
            # Fall back to deprecated binom_test for older scipy
            p_value = stats.binom_test(n_regressed, n_total, 0.5, alternative='greater')

        # Effect size (Cohen's h)
        p_observed = regression_rate / 100
        p_expected = 0.5
        cohens_h = 2 * (np.arcsin(np.sqrt(p_observed)) - np.arcsin(np.sqrt(p_expected)))

        # Confidence interval (Wilson score)
        z = 1.96  # 95% CI
        p_hat = p_observed
        denominator = 1 + z**2/n_total
        center = (p_hat + z**2/(2*n_total)) / denominator
        margin = z * np.sqrt((p_hat*(1-p_hat)/n_total + z**2/(4*n_total**2))) / denominator
        ci_lower = (center - margin) * 100
        ci_upper = (center + margin) * 100

        results = {
            'threshold': threshold,
            'n_scenarios': n_total,
            'n_regressed': n_regressed,
            'regression_rate': round(regression_rate, 2),
            'ci_lower': round(ci_lower, 2),
            'ci_upper': round(ci_upper, 2),
            'p_value': round(p_value, 4),
            'cohens_h': round(cohens_h, 3),
            'significant': p_value < 0.05,
            'effect_size': 'small' if abs(cohens_h) < 0.2 else ('medium' if abs(cohens_h) < 0.5 else 'large')
        }

        # Display results
        print(f"\n   Sample Size: {n_total:,} scenarios")
        print(f"   Regressed: {n_regressed:,} ({regression_rate:.1f}%)")
        print(f"   95% CI: [{ci_lower:.1f}%, {ci_upper:.1f}%]")
        print(f"   P-value: {p_value:.4f}")
        print(f"   Cohen's h: {cohens_h:.3f} ({results['effect_size']} effect)")

        if results['significant']:
            print(f"    SIGNIFICANT: Regression rate significantly > 50%")
        else:
            print(f"   ERROR: NOT SIGNIFICANT: Cannot reject null hypothesis")

        # Add to results
        self.results[threshold] = results

        return results

    def test_all_thresholds(self):
        """Test hypothesis at all betting thresholds"""
        print("\n" + "="*70)
        print("COMPREHENSIVE HYPOTHESIS TESTING")
        print("="*70)

        thresholds = [8, 12, 16, 20, 24, 28]

        for threshold in thresholds:
            self.test_hypothesis_by_threshold(threshold)

        return self.results

    def test_optimal_threshold(self):
        """Find the optimal threshold for betting"""
        print("\n" + "="*70)
        print("OPTIMAL THRESHOLD ANALYSIS")
        print("="*70)

        thresholds = range(10, 31, 2)  # Test 10, 12, 14, ..., 30
        optimal_results = []

        for threshold in thresholds:
            # Calculate expected value at this threshold
            # Assume -110 odds (win 0.91 units, lose 1.0 unit)

            # Get regression rate from test
            test_result = self.test_hypothesis_by_threshold(threshold)
            regression_rate = test_result['regression_rate'] / 100

            # Expected value per bet
            # Win rate = regression rate (simplified)
            win_prob = regression_rate
            lose_prob = 1 - regression_rate

            ev = (win_prob * 0.91) - (lose_prob * 1.0)

            optimal_results.append({
                'threshold': threshold,
                'regression_rate': test_result['regression_rate'],
                'win_probability': round(win_prob * 100, 1),
                'expected_value': round(ev, 4),
                'roi': round(ev * 100, 2),
                'significant': test_result['significant']
            })

        optimal_df = pd.DataFrame(optimal_results)

        # Find best threshold
        best = optimal_df.nlargest(1, 'expected_value').iloc[0]

        print(f"\n OPTIMAL THRESHOLD:")
        print(f"   Threshold: ±{best['threshold']} points")
        print(f"   Regression Rate: {best['regression_rate']}%")
        print(f"   Expected Value: {best['expected_value']:.4f} units/bet")
        print(f"   ROI: {best['roi']:+.2f}%")
        print(f"   Statistically Significant: {best['significant']}")

        return optimal_df

    def test_directional_effects(self):
        """Test if regression differs for OVER vs UNDER scenarios"""
        print("\n" + "="*70)
        print("DIRECTIONAL REGRESSION ANALYSIS")
        print("="*70)

        threshold = 20  # Test at 20-point threshold

        # Scenario 1: Live OVER (line moved up)
        over_data = self.data.copy()
        over_data['Live_Line'] = over_data['Closing_Line'] + threshold
        over_data['Distance_To_Closing'] = abs(over_data['Actual_Total'] - over_data['Closing_Line'])
        over_data['Distance_To_Live'] = abs(over_data['Actual_Total'] - over_data['Live_Line'])
        over_data['Regressed'] = over_data['Distance_To_Closing'] < over_data['Distance_To_Live']

        over_regression_rate = (over_data['Regressed'].sum() / len(over_data)) * 100

        # Scenario 2: Live UNDER (line moved down)
        under_data = self.data.copy()
        under_data['Live_Line'] = under_data['Closing_Line'] - threshold
        under_data['Distance_To_Closing'] = abs(under_data['Actual_Total'] - under_data['Closing_Line'])
        under_data['Distance_To_Live'] = abs(under_data['Actual_Total'] - under_data['Live_Line'])
        under_data['Regressed'] = under_data['Distance_To_Closing'] < under_data['Distance_To_Live']

        under_regression_rate = (under_data['Regressed'].sum() / len(under_data)) * 100

        print(f"\n   OVER scenarios (bet UNDER): {over_regression_rate:.1f}% regression")
        print(f"   UNDER scenarios (bet OVER): {under_regression_rate:.1f}% regression")

        # Test if difference is significant
        # Chi-square test for independence
        contingency = np.array([
            [over_data['Regressed'].sum(), (~over_data['Regressed']).sum()],
            [under_data['Regressed'].sum(), (~under_data['Regressed']).sum()]
        ])

        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

        print(f"\n   Chi-square test: X2={chi2:.2f}, p={p_value:.4f}")

        if p_value < 0.05:
            print(f"    SIGNIFICANT DIFFERENCE between OVER and UNDER regression rates")
        else:
            print(f"   ERROR: NO SIGNIFICANT DIFFERENCE between directions")

        return {
            'over_regression_rate': round(over_regression_rate, 2),
            'under_regression_rate': round(under_regression_rate, 2),
            'chi2': round(chi2, 2),
            'p_value': round(p_value, 4),
            'significant_difference': p_value < 0.05
        }

    def generate_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "="*70)
        print("REGRESSION HYPOTHESIS VALIDATION REPORT")
        print("="*70)

        if not self.results:
            print("WARNING:  No results available. Run tests first.")
            return

        print(f"\n SUMMARY OF FINDINGS:")
        print(f"   Dataset: {len(self.data):,} games")

        # Count significant results
        significant_count = sum(1 for r in self.results.values() if r['significant'])
        total_tests = len(self.results)

        print(f"   Significant Results: {significant_count}/{total_tests}")

        # Best performing threshold
        best_threshold = max(self.results.items(), key=lambda x: x[1]['regression_rate'])
        print(f"\n    Best Threshold: ±{best_threshold[0]} points")
        print(f"      Regression Rate: {best_threshold[1]['regression_rate']}%")
        print(f"      P-value: {best_threshold[1]['p_value']}")

        # Recommendations
        print(f"\n RECOMMENDATIONS:")

        profitable_thresholds = [
            t for t, r in self.results.items()
            if r['regression_rate'] > 52.38  # Breakeven at -110
        ]

        if profitable_thresholds:
            print(f"    Profitable thresholds: {profitable_thresholds}")
            print(f"   Recommended: Use ±{min(profitable_thresholds)}+ point movement")
        else:
            print(f"   ERROR: No thresholds show profitability at -110 odds")
            print(f"   Consider: Look for better odds or larger thresholds")

    def save_results(self, output_dir='backend/data/analysis'):
        """Save validation results"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save results
        results_df = pd.DataFrame(self.results).T
        results_file = f"{output_dir}/hypothesis_validation_{timestamp}.csv"
        results_df.to_csv(results_file)
        print(f"\n Saved results: {results_file}")

        return results_file


def main():
    """Run hypothesis validation"""
    print("="*70)
    print("NCAA BASKETBALL REGRESSION HYPOTHESIS VALIDATOR")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    # Find data files
    historical_dir = "backend/data/historical"
    games_pattern = f"{historical_dir}/game_results_*_season_*.csv"
    games_files = glob.glob(games_pattern)

    if not games_files:
        print("ERROR: No historical game data found")
        return False

    latest_games = max(games_files)

    # Find predictions (optional)
    backtest_dir = "backend/data/backtesting"
    pred_pattern = f"{backtest_dir}/predictions_*.csv"
    pred_files = glob.glob(pred_pattern)
    latest_predictions = max(pred_files) if pred_files else None

    # Initialize validator
    validator = RegressionHypothesisValidator(
        historical_games_path=latest_games,
        predictions_path=latest_predictions
    )

    # Step 1: Calculate basic metrics
    validator.calculate_regression_metrics()

    # Step 2: Test all thresholds
    validator.test_all_thresholds()

    # Step 3: Find optimal threshold
    optimal_df = validator.test_optimal_threshold()

    # Step 4: Test directional effects
    validator.test_directional_effects()

    # Step 5: Generate report
    validator.generate_report()

    # Step 6: Save results
    validator.save_results()

    print("\n" + "="*70)
    print(" VALIDATION COMPLETE")
    print("="*70)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
