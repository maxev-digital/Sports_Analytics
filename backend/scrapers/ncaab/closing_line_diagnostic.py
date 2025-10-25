#!/usr/bin/env python3
"""
Diagnostic: Check what deviations actually exist in your closing line data
"""

import pandas as pd
import numpy as np

# Load your matched data
import os
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
file_path = os.path.join(base_dir, 'data', 'analysis', 'comprehensive_closing_vs_actual_20251011_110047.csv')
df = pd.read_csv(file_path)

print("="*70)
print("CLOSING LINE DEVIATION DIAGNOSTIC")
print("="*70)
print(f"\nTotal Games: {len(df)}")

# Basic statistics
print(f"\n DEVIATION STATISTICS:")
print(f"   Mean deviation: {df['Deviation'].mean():.2f} points")
print(f"   Std deviation: {df['Deviation'].std():.2f} points")
print(f"   Min deviation: {df['Deviation'].min():.2f} points")
print(f"   Max deviation: {df['Deviation'].max():.2f} points")
print(f"   Median deviation: {df['Deviation'].median():.2f} points")

# Distribution by threshold
print(f"\n GAMES MEETING DEVIATION THRESHOLDS:")
print(f"{'Threshold':<15} {'Count':<10} {'Percentage'}")
print("-"*70)

for threshold in [5, 8, 10, 12, 15, 18, 20, 25, 30]:
    count = (abs(df['Deviation']) >= threshold).sum()
    pct = (count / len(df)) * 100
    print(f">={threshold} points{' '*(6-len(str(threshold)))} {count:<10} {pct:5.1f}%")

# Show the most extreme games
print(f"\n TOP 10 MOST EXTREME DEVIATIONS:")
print("-"*70)
top_deviations = df.nlargest(10, 'Abs_Deviation')[['Date', 'Home_Team', 'Away_Team', 'Closing_Total', 'Actual_Total', 'Deviation']]
print(top_deviations.to_string(index=False))

# Distribution visualization (text-based)
print(f"\n DEVIATION DISTRIBUTION (histogram):")
print("-"*70)

bins = [-30, -20, -15, -10, -5, 0, 5, 10, 15, 20, 30]
labels = ['<-20', '-20 to -15', '-15 to -10', '-10 to -5', '-5 to 0',
          '0 to 5', '5 to 10', '10 to 15', '15 to 20', '>20']

df['bin'] = pd.cut(df['Deviation'], bins=bins, labels=labels, include_lowest=True)
bin_counts = df['bin'].value_counts().sort_index()

for label, count in bin_counts.items():
    bar = '#' * int((count / len(df)) * 50)
    pct = (count / len(df)) * 100
    print(f"{label:>12} | {bar} {count} ({pct:.1f}%)")

# Key insight
print(f"\n KEY INSIGHTS:")
games_20plus = (abs(df['Deviation']) >= 20).sum()
if games_20plus == 0:
    print("   WARNING: CRITICAL: Zero games deviated 20+ points from closing!")
    print("   Your 20-point threshold is too high for this dataset.")
    print("   Realistic thresholds for NCAA: 8-12 points")
elif games_20plus < 10:
    print(f"   WARNING: Only {games_20plus} games deviated 20+ points")
    print("   Sample size too small for statistical significance")
    print("   Consider lower thresholds: 10-15 points")
else:
    print(f"   SUCCESS: {games_20plus} games deviated 20+ points")
    print("   Sufficient sample for analysis")

# Recommendation
print(f"\n RECOMMENDED ACTION:")
most_common_threshold = None
for threshold in [8, 10, 12, 15]:
    count = (abs(df['Deviation']) >= threshold).sum()
    if count >= 30:  # Want at least 30 games for decent sample
        most_common_threshold = threshold
        break

if most_common_threshold:
    count = (abs(df['Deviation']) >= most_common_threshold).sum()
    print(f"   Use {most_common_threshold}-point threshold")
    print(f"   Sample size: {count} games ({count/len(df)*100:.1f}%)")
else:
    print(f"   Dataset may be too small for meaningful analysis")
    print(f"   Need more historical data or lower thresholds")

print("="*70)
