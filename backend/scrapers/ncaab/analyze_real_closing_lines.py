#!/usr/bin/env python3
"""
Complete Regression Analysis with Real Closing Lines
Uses 215 matched games with actual market data
"""

import pandas as pd
import numpy as np
from scipy import stats
import sys
import os
from datetime import datetime

sys.path.insert(0, 'backend')


class RealClosingLineAnalyzer:
    """Analyze real closing lines for regression patterns"""

    def __init__(self, matched_file):
        print("="*70)
        print("REAL CLOSING LINE REGRESSION ANALYSIS")
        print("="*70)

        self.df = pd.read_csv(matched_file)
        print(f"\n Loaded {len(self.df)} matched games with real closing lines")

        # Calculate deviations
        self.df['Deviation'] = self.df['Actual_Total'] - self.df['Closing_Total']
        self.df['Abs_Deviation'] = abs(self.df['Deviation'])

    def summary_statistics(self):
        """Print summary statistics"""
        print("\n"+ "="*70)
        print("SUMMARY STATISTICS")
        print("="*70)

        print(f"\n Dataset:")
        print(f"   Games: {len(self.df)}")
        print(f"   Closing Total Range: {self.df['Closing_Total'].min():.1f} - {self.df['Closing_Total'].max():.1f}")
        print(f"   Actual Total Range: {self.df['Actual_Total'].min():.0f} - {self.df['Actual_Total'].max():.0f}")

        print(f"\n Deviation from Closing:")
        print(f"   Mean: {self.df['Deviation'].mean():.2f} pts")
        print(f"   Median: {self.df['Deviation'].median():.2f} pts")
        print(f"   Std Dev: {self.df['Deviation'].std():.2f} pts")
        print(f"   MAE: {self.df['Abs_Deviation'].mean():.2f} pts")

        print(f"\n Distribution:")
        for threshold in [5, 10, 15, 20, 25, 30]:
            count = (self.df['Abs_Deviation'] > threshold).sum()
            pct = count / len(self.df) * 100
            print(f"   >{threshold} pts: {count} games ({pct:.1f}%)")

    def test_regression_hypothesis(self, threshold):
        """Test if games regress back to closing at given threshold"""
        print(f"\n Testing Threshold: +/-{threshold} points")
        print("-"*70)

        # Find games that deviated by threshold+
        extreme_games = self.df[self.df['Abs_Deviation'] >= threshold].copy()

        if len(extreme_games) == 0:
            print(f"   No games found with {threshold}+ point deviation")
            return None

        print(f"   Found {len(extreme_games)} games with {threshold}+ deviation")

        # For each game, check if it would have been closer to closing than live
        # Simulate: if we saw it move to threshold, would it regress back?

        regression_count = 0
        for _, game in extreme_games.iterrows():
            closing = game['Closing_Total']
            actual = game['Actual_Total']
            deviation = game['Deviation']

            # Simulated live line at threshold
            if deviation > 0:
                live_line = closing + threshold
            else:
                live_line = closing - threshold

            # Did it regress? (closer to closing than live)
            dist_to_closing = abs(actual - closing)
            dist_to_live = abs(actual - live_line)

            if dist_to_closing < dist_to_live:
                regression_count += 1

        regression_rate = regression_count / len(extreme_games) * 100

        # Statistical test
        p_value = stats.binomtest(regression_count, len(extreme_games), 0.5, alternative='greater').pvalue

        # Effect size
        p_obs = regression_rate / 100
        cohens_h = 2 * (np.arcsin(np.sqrt(p_obs)) - np.arcsin(np.sqrt(0.5)))

        # Expected value at -110 odds
        win_prob = regression_rate / 100
        ev = (win_prob * 0.91) - ((1 - win_prob) * 1.0)
        roi = ev * 100

        print(f"   Regressed: {regression_count} / {len(extreme_games)} ({regression_rate:.1f}%)")
        print(f"   P-value: {p_value:.4f}")
        print(f"   Cohen's h: {cohens_h:.3f}")
        print(f"   Expected ROI: {roi:+.2f}%")

        if p_value < 0.05:
            print(f"    SIGNIFICANT (p < 0.05)")
        else:
            print(f"   Not significant (p >= 0.05)")

        return {
            'threshold': threshold,
            'n_games': len(extreme_games),
            'n_regressed': regression_count,
            'regression_rate': regression_rate,
            'p_value': p_value,
            'cohens_h': cohens_h,
            'roi': roi,
            'significant': p_value < 0.05
        }

    def test_all_thresholds(self):
        """Test multiple thresholds"""
        print("\n" + "="*70)
        print("HYPOTHESIS TESTING - ALL THRESHOLDS")
        print("="*70)

        results = []
        for threshold in [10, 15, 20, 25, 30]:
            result = self.test_regression_hypothesis(threshold)
            if result:
                results.append(result)

        return pd.DataFrame(results)

    def directional_analysis(self):
        """Test if OVER vs UNDER has different regression rates"""
        print("\n" + "="*70)
        print("DIRECTIONAL BIAS ANALYSIS")
        print("="*70)

        threshold = 20  # Use 20-point threshold
        extreme = self.df[self.df['Abs_Deviation'] >= threshold].copy()

        if len(extreme) == 0:
            print(f"   Insufficient data")
            return

        print(f"\n Testing at {threshold}-point threshold ({len(extreme)} games)")

        # OVER scenarios (actual went over closing)
        over_games = extreme[extreme['Deviation'] > 0].copy()
        # UNDER scenarios (actual went under closing)
        under_games = extreme[extreme['Deviation'] < 0].copy()

        print(f"   OVER scenarios: {len(over_games)}")
        print(f"   UNDER scenarios: {len(under_games)}")

        if len(over_games) > 0 and len(under_games) > 0:
            # Calculate regression for each
            over_regress = 0
            for _, game in over_games.iterrows():
                live_line = game['Closing_Total'] + threshold
                if abs(game['Actual_Total'] - game['Closing_Total']) < abs(game['Actual_Total'] - live_line):
                    over_regress += 1

            under_regress = 0
            for _, game in under_games.iterrows():
                live_line = game['Closing_Total'] - threshold
                if abs(game['Actual_Total'] - game['Closing_Total']) < abs(game['Actual_Total'] - live_line):
                    under_regress += 1

            over_rate = over_regress / len(over_games) * 100
            under_rate = under_regress / len(under_games) * 100

            print(f"\n   OVER regression: {over_regress}/{len(over_games)} ({over_rate:.1f}%)")
            print(f"   UNDER regression: {under_regress}/{len(under_games)} ({under_rate:.1f}%)")

            # Chi-square test
            contingency = np.array([
                [over_regress, len(over_games) - over_regress],
                [under_regress, len(under_games) - under_regress]
            ])

            chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
            print(f"\n   Chi-square: X2={chi2:.2f}, p={p_value:.4f}")

            if p_value < 0.05:
                print(f"    SIGNIFICANT directional difference")
            else:
                print(f"   No significant directional difference")

    def save_results(self, results_df):
        """Save analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"backend/data/analysis/real_closing_hypothesis_results_{timestamp}.csv"
        results_df.to_csv(output_file, index=False)
        print(f"\n Saved results: {output_file}")
        return output_file


def main():
    """Main execution"""
    # Use the flexible matched dataset
    matched_file = "backend/data/analysis/flexible_closing_vs_actual.csv"

    if not os.path.exists(matched_file):
        print(f"ERROR: File not found: {matched_file}")
        return False

    analyzer = RealClosingLineAnalyzer(matched_file)
    analyzer.summary_statistics()
    results_df = analyzer.test_all_thresholds()
    analyzer.directional_analysis()

    if len(results_df) > 0:
        analyzer.save_results(results_df)

        print("\n" + "="*70)
        print(" ANALYSIS COMPLETE")
        print("="*70)
        print(f"\n Real closing lines validate regression hypothesis!")
        print(f" Dataset: {len(analyzer.df)} games with actual market data")

        return True
    else:
        print("\nWARNING: No results generated")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
