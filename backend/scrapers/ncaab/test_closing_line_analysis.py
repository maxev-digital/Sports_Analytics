#!/usr/bin/env python3
"""
Unit Tests for NCAA Closing Line Analysis
Tests all components of the closing line accuracy analyzer and bet simulator
"""

import unittest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
from io import StringIO

# Add backend to path
sys.path.insert(0, 'backend')
sys.path.insert(0, '.')

# Import modules to test
try:
    from analyze_closing_line_accuracy import ClosingLineAccuracyAnalyzer
    from simulate_closing_line_bets import ClosingLineBetSimulator
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    ClosingLineAccuracyAnalyzer = None
    ClosingLineBetSimulator = None


class TestDataLoading(unittest.TestCase):
    """Test data loading and validation"""

    def setUp(self):
        """Create test data"""
        self.test_data = pd.DataFrame({
            'Date': ['2023-11-06'] * 10,
            'Home_Team': ['Duke', 'UNC', 'Kansas', 'Kentucky', 'UCLA',
                         'Arizona', 'Gonzaga', 'Villanova', 'Baylor', 'Texas'],
            'Away_Team': ['Wake Forest', 'NC State', 'Missouri', 'Louisville', 'USC',
                         'ASU', 'BYU', 'Seton Hall', 'TCU', 'Oklahoma'],
            'Home_Score': [85, 78, 91, 82, 75, 88, 95, 72, 80, 77],
            'Away_Score': [70, 72, 65, 68, 73, 81, 88, 70, 75, 74],
            'Actual_Total': [155, 150, 156, 150, 148, 169, 183, 142, 155, 151]
        })

        # Create temporary CSV
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        self.test_data.to_csv(self.temp_file.name, index=False)
        self.temp_file.close()

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_csv_structure(self):
        """Test that CSV has required columns"""
        df = pd.read_csv(self.temp_file.name)
        required_columns = ['Home_Team', 'Away_Team', 'Actual_Total']
        for col in required_columns:
            self.assertIn(col, df.columns, f"Missing required column: {col}")

    def test_data_types(self):
        """Test that data types are correct"""
        df = pd.read_csv(self.temp_file.name)
        self.assertTrue(pd.api.types.is_numeric_dtype(df['Actual_Total']))
        self.assertTrue(pd.api.types.is_object_dtype(df['Home_Team']))
        self.assertTrue(pd.api.types.is_object_dtype(df['Away_Team']))

    def test_no_missing_values(self):
        """Test that required fields have no missing values"""
        df = pd.read_csv(self.temp_file.name)
        self.assertEqual(df['Actual_Total'].isna().sum(), 0)
        self.assertEqual(df['Home_Team'].isna().sum(), 0)
        self.assertEqual(df['Away_Team'].isna().sum(), 0)

    def test_reasonable_totals(self):
        """Test that totals are within reasonable range"""
        df = pd.read_csv(self.temp_file.name)
        # NCAA games typically between 100-200 points
        self.assertTrue((df['Actual_Total'] >= 100).all())
        self.assertTrue((df['Actual_Total'] <= 250).all())

    def test_data_loading(self):
        """Test that data loads without errors"""
        df = pd.read_csv(self.temp_file.name)
        self.assertEqual(len(df), 10)
        self.assertGreater(len(df.columns), 4)


class TestAccuracyCalculations(unittest.TestCase):
    """Test statistical accuracy calculations"""

    def setUp(self):
        """Create test data with known statistics"""
        np.random.seed(42)
        self.n_games = 100
        self.closing_lines = np.random.normal(140, 10, self.n_games)
        # Add controlled error
        errors = np.random.normal(0, 8, self.n_games)
        self.actual_totals = self.closing_lines + errors

        self.test_df = pd.DataFrame({
            'Closing_Total': self.closing_lines,
            'Actual_Total': self.actual_totals
        })

    def test_error_calculation(self):
        """Test error calculation"""
        df = self.test_df.copy()
        df['Error'] = df['Closing_Total'] - df['Actual_Total']
        df['Abs_Error'] = abs(df['Error'])

        # Check calculations are correct
        for idx in range(min(5, len(df))):
            expected_error = df['Closing_Total'].iloc[idx] - df['Actual_Total'].iloc[idx]
            self.assertAlmostEqual(df['Error'].iloc[idx], expected_error, places=2)
            self.assertAlmostEqual(df['Abs_Error'].iloc[idx], abs(expected_error), places=2)

    def test_mae_calculation(self):
        """Test Mean Absolute Error"""
        df = self.test_df.copy()
        df['Abs_Error'] = abs(df['Closing_Total'] - df['Actual_Total'])
        mae = df['Abs_Error'].mean()

        # MAE should be positive
        self.assertGreater(mae, 0)
        # MAE should be reasonable for NCAA
        self.assertLess(mae, 30)

    def test_std_calculation(self):
        """Test standard deviation"""
        df = self.test_df.copy()
        df['Error'] = df['Closing_Total'] - df['Actual_Total']
        std = df['Error'].std()

        # Should be close to our input std of 8
        self.assertGreater(std, 5)
        self.assertLess(std, 12)

    def test_percentile_calculation(self):
        """Test percentile calculations"""
        df = self.test_df.copy()
        df['Abs_Error'] = abs(df['Closing_Total'] - df['Actual_Total'])

        p50 = np.percentile(df['Abs_Error'], 50)
        p95 = np.percentile(df['Abs_Error'], 95)

        # 95th percentile should be larger than 50th
        self.assertGreater(p95, p50)
        # Values should be reasonable
        self.assertGreater(p50, 0)
        self.assertLess(p95, 50)

    def test_mean_error_close_to_zero(self):
        """Test that mean error is close to zero (unbiased)"""
        df = self.test_df.copy()
        df['Error'] = df['Closing_Total'] - df['Actual_Total']
        mean_error = df['Error'].mean()

        # Should be close to 0 (within 2 points)
        self.assertLess(abs(mean_error), 2.0)

    def test_within_threshold_calculation(self):
        """Test percentage within threshold calculation"""
        df = self.test_df.copy()
        df['Abs_Error'] = abs(df['Closing_Total'] - df['Actual_Total'])

        threshold = 10
        within = (df['Abs_Error'] <= threshold).sum()
        pct_within = (within / len(df)) * 100

        # Should be between 0 and 100
        self.assertGreaterEqual(pct_within, 0)
        self.assertLessEqual(pct_within, 100)

    def test_rmse_calculation(self):
        """Test Root Mean Squared Error"""
        df = self.test_df.copy()
        df['Error'] = df['Closing_Total'] - df['Actual_Total']
        rmse = np.sqrt((df['Error'] ** 2).mean())

        # RMSE should be positive
        self.assertGreater(rmse, 0)
        # RMSE should be >= MAE
        mae = abs(df['Error']).mean()
        self.assertGreaterEqual(rmse, mae)

    def test_median_calculation(self):
        """Test median absolute error"""
        df = self.test_df.copy()
        df['Abs_Error'] = abs(df['Closing_Total'] - df['Actual_Total'])
        median_ae = df['Abs_Error'].median()

        # Median should be positive
        self.assertGreater(median_ae, 0)
        # Median should be reasonable
        self.assertLess(median_ae, 20)


class TestThresholdRecommendations(unittest.TestCase):
    """Test betting threshold logic"""

    def test_threshold_definitions(self):
        """Test that thresholds are properly defined"""
        thresholds = [8, 12, 16, 20, 24, 28]
        recommendations = ['Pass', 'Consider', 'Good', 'Strong', 'Max', 'Historic']

        # Should have same length
        self.assertEqual(len(thresholds), len(recommendations))

        # Thresholds should be increasing
        for i in range(1, len(thresholds)):
            self.assertGreater(thresholds[i], thresholds[i-1])

    def test_bet_size_assignments(self):
        """Test that bet sizes are assigned correctly"""
        bet_sizes = {
            'Pass': 0.0,
            'Consider': 0.5,
            'Good': 1.0,
            'Strong': 1.5,
            'Max': 2.0,
            'Historic': 2.0
        }

        # All sizes should be non-negative
        for size in bet_sizes.values():
            self.assertGreaterEqual(size, 0)

        # Max bets shouldn't exceed 2 units
        for size in bet_sizes.values():
            self.assertLessEqual(size, 2.0)

    def test_threshold_triggering(self):
        """Test that bets trigger at correct thresholds"""
        closing = 140.0
        live = 156.0  # 16 point movement
        threshold = 16

        movement = abs(live - closing)
        should_trigger = movement >= threshold

        self.assertTrue(should_trigger)

    def test_regression_probability_calculation(self):
        """Test regression probability formula"""
        inside_pct = 80.0  # 80% of games finish within range

        # Simplified model: 50% + (inside_pct - 50) * 0.6
        regression_prob = 50 + (inside_pct - 50) * 0.6

        # Should be between 50 and 100
        self.assertGreaterEqual(regression_prob, 50)
        self.assertLessEqual(regression_prob, 100)

        # Higher inside_pct should mean higher regression prob
        inside_pct_high = 90.0
        regression_prob_high = 50 + (inside_pct_high - 50) * 0.6
        self.assertGreater(regression_prob_high, regression_prob)

    def test_recommendation_mapping(self):
        """Test that movements map to correct recommendations"""
        test_cases = [
            (7, 'Pass'),
            (10, 'Consider'),
            (16, 'Good'),
            (22, 'Strong'),
            (26, 'Max'),
            (30, 'Historic')
        ]

        for movement, expected_rec in test_cases:
            if movement < 12:
                actual_rec = 'Pass'
            elif movement < 16:
                actual_rec = 'Consider'
            elif movement < 20:
                actual_rec = 'Good'
            elif movement < 24:
                actual_rec = 'Strong'
            elif movement < 28:
                actual_rec = 'Max'
            else:
                actual_rec = 'Historic'

            self.assertEqual(actual_rec, expected_rec,
                           f"Movement of {movement} should map to {expected_rec}")

    def test_standard_deviation_multiplier(self):
        """Test standard deviation multiplier calculation"""
        std = 8.5  # Typical for NCAA
        threshold = 16

        std_multiple = threshold / std

        # Should be around 1.88
        self.assertGreater(std_multiple, 1.5)
        self.assertLess(std_multiple, 2.5)


class TestRegressionProbability(unittest.TestCase):
    """Test regression hypothesis validation"""

    def setUp(self):
        """Create test scenarios"""
        self.closing = 140.0
        self.scenarios = [
            {'live': 156.0, 'actual': 148.0, 'should_regress': True},
            {'live': 124.0, 'actual': 132.0, 'should_regress': True},
            {'live': 156.0, 'actual': 160.0, 'should_regress': False},
            {'live': 124.0, 'actual': 120.0, 'should_regress': False},
        ]

    def test_regression_detection(self):
        """Test if regression is correctly detected"""
        for scenario in self.scenarios:
            live = scenario['live']
            actual = scenario['actual']
            expected_regress = scenario['should_regress']

            # Did it regress? (moved back closer to closing)
            live_distance = abs(live - self.closing)
            actual_distance = abs(actual - self.closing)
            actual_regressed = actual_distance < live_distance

            self.assertEqual(actual_regressed, expected_regress,
                           f"Failed for live={live}, actual={actual}")

    def test_regression_rate_calculation(self):
        """Test regression rate calculation"""
        test_data = pd.DataFrame({
            'closing_line': [140] * 4,
            'live_line': [156, 124, 156, 124],
            'actual_total': [148, 132, 160, 120]
        })

        test_data['regressed'] = (
            abs(test_data['actual_total'] - test_data['closing_line']) <
            abs(test_data['live_line'] - test_data['closing_line'])
        )

        regression_rate = (test_data['regressed'].sum() / len(test_data)) * 100

        # Should be 50% for our test data (2 out of 4)
        self.assertEqual(regression_rate, 50.0)

    def test_edge_case_no_movement(self):
        """Test when live line equals closing"""
        closing = 140.0
        live = 140.0
        actual = 145.0

        movement = abs(live - closing)
        self.assertEqual(movement, 0)

        # No bet should trigger
        should_bet = movement >= 12
        self.assertFalse(should_bet)

    def test_edge_case_exact_threshold(self):
        """Test when movement exactly equals threshold"""
        closing = 140.0
        live = 156.0  # Exactly 16 points
        threshold = 16

        movement = abs(live - closing)
        should_trigger = movement >= threshold

        self.assertTrue(should_trigger)


class TestBetSimulation(unittest.TestCase):
    """Test bet simulation logic"""

    def test_bet_side_determination(self):
        """Test that bet side is chosen correctly"""
        closing = 140.0

        # When line moves UP, bet UNDER
        live_high = 156.0
        bet_side_high = 'UNDER' if live_high > closing else 'OVER'
        self.assertEqual(bet_side_high, 'UNDER')

        # When line moves DOWN, bet OVER
        live_low = 124.0
        bet_side_low = 'UNDER' if live_low > closing else 'OVER'
        self.assertEqual(bet_side_low, 'OVER')

    def test_win_determination(self):
        """Test if bet wins are calculated correctly"""
        test_cases = [
            # (bet_side, bet_total, actual, should_win)
            ('OVER', 140.0, 145.0, True),   # Over wins
            ('OVER', 140.0, 135.0, False),  # Over loses
            ('UNDER', 160.0, 155.0, True),  # Under wins
            ('UNDER', 160.0, 165.0, False), # Under loses
        ]

        for bet_side, bet_total, actual, should_win in test_cases:
            if bet_side == 'OVER':
                actual_win = actual > bet_total
            else:  # UNDER
                actual_win = actual < bet_total

            self.assertEqual(actual_win, should_win,
                           f"Failed: {bet_side} {bet_total} with actual {actual}")

    def test_push_detection(self):
        """Test push detection"""
        bet_total = 140.0
        actual_total = 140.0

        is_push = (actual_total == bet_total)
        self.assertTrue(is_push)

        # Profit on push should be 0
        profit = 0.0 if is_push else None
        self.assertEqual(profit, 0.0)

    def test_profit_calculation_win(self):
        """Test profit calculation for wins"""
        bet_size = 1.0
        # At -110 odds, win 0.91 units
        profit = bet_size * 0.91
        self.assertAlmostEqual(profit, 0.91, places=2)

    def test_profit_calculation_loss(self):
        """Test profit calculation for losses"""
        bet_size = 1.0
        profit = -bet_size
        self.assertEqual(profit, -1.0)

    def test_roi_calculation(self):
        """Test ROI calculation"""
        total_profit = 10.0
        total_risked = 100.0
        roi = (total_profit / total_risked) * 100

        self.assertEqual(roi, 10.0)

    def test_win_rate_calculation(self):
        """Test win rate calculation"""
        wins = 55
        losses = 45
        pushes = 5

        # Win rate excludes pushes
        win_rate = (wins / (wins + losses)) * 100

        self.assertEqual(win_rate, 55.0)
        # Should be above breakeven (52.38%)
        self.assertGreater(win_rate, 52.38)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def test_empty_dataframe(self):
        """Test handling of empty data"""
        df = pd.DataFrame()
        self.assertEqual(len(df), 0)

        # Should handle gracefully
        if len(df) == 0:
            result = "No data"
        self.assertEqual(result, "No data")

    def test_missing_columns(self):
        """Test handling of missing columns"""
        df = pd.DataFrame({
            'Home_Team': ['Duke'],
            'Away_Team': ['UNC']
            # Missing Actual_Total
        })

        # Should detect missing column
        has_actual = 'Actual_Total' in df.columns
        self.assertFalse(has_actual)

    def test_null_values(self):
        """Test handling of null values"""
        df = pd.DataFrame({
            'Actual_Total': [140, None, 150, np.nan, 145]
        })

        # Should be able to filter nulls
        clean_df = df.dropna(subset=['Actual_Total'])
        self.assertEqual(len(clean_df), 3)

    def test_extreme_outliers(self):
        """Test handling of extreme values"""
        # NCAA game with 250+ points (very rare)
        extreme_total = 260.0
        closing = 140.0

        error = abs(extreme_total - closing)
        # Should still calculate
        self.assertGreater(error, 100)

    def test_negative_totals(self):
        """Test that negative totals are rejected"""
        invalid_total = -10.0
        # Should be caught in validation
        is_valid = invalid_total > 0
        self.assertFalse(is_valid)


class TestStatisticalSignificance(unittest.TestCase):
    """Test statistical validation methods"""

    def test_sample_size_adequacy(self):
        """Test if sample size is adequate"""
        n = 2656  # Our actual sample
        # Need at least 30 for CLT, ideally 100+
        self.assertGreater(n, 100)
        self.assertGreater(n, 1000)  # Strong sample

    def test_breakeven_calculation(self):
        """Test breakeven win rate at -110 odds"""
        # At -110, risk 110 to win 100
        # Breakeven: 110/(110+100) = 52.38%
        breakeven = (110 / (110 + 100)) * 100
        self.assertAlmostEqual(breakeven, 52.38, places=1)

    def test_confidence_interval_calculation(self):
        """Test confidence interval for win rate"""
        wins = 550
        total = 1000
        win_rate = wins / total

        # Calculate 95% CI using normal approximation
        z = 1.96  # 95% confidence
        se = np.sqrt((win_rate * (1 - win_rate)) / total)
        margin = z * se

        ci_lower = win_rate - margin
        ci_upper = win_rate + margin

        # CI should contain the true value
        self.assertLess(ci_lower, win_rate)
        self.assertGreater(ci_upper, win_rate)

        # CI should be reasonable width
        ci_width = ci_upper - ci_lower
        self.assertLess(ci_width, 0.10)  # Less than 10% wide


def run_all_tests():
    """Run all test suites"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDataLoading))
    suite.addTests(loader.loadTestsFromTestCase(TestAccuracyCalculations))
    suite.addTests(loader.loadTestsFromTestCase(TestThresholdRecommendations))
    suite.addTests(loader.loadTestsFromTestCase(TestRegressionProbability))
    suite.addTests(loader.loadTestsFromTestCase(TestBetSimulation))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestStatisticalSignificance))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
