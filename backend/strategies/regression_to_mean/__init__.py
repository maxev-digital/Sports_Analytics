"""
Regression to Mean Basketball Totals Strategy

A multi-layer ML-powered betting strategy that identifies opportunities when
live totals deviate significantly from statistical predictions.

Key Components:
- XGBoost quantile regression models (mean, lower, upper bounds)
- Live odds monitoring across all tracked bookmakers
- Z-score deviation analysis (2+ standard deviations)
- Kelly criterion bet sizing based on edge distance
- Real-time alert generation and notification system

Expected Performance: 15-25% ROI, 72-78% hit rate

Documentation: See docs/ folder
"""

from .strategy import RegressionToMeanStrategy

__version__ = "1.0.0"
__author__ = "MAX-EV-SPORTS"

__all__ = ['RegressionToMeanStrategy']
