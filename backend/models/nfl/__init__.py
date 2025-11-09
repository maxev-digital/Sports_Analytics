"""
NFL prediction models for totals, spreads, and moneyline

Per sports-betting-models-guide.md:
- Spreads: Linear/Polynomial Regression is primary (power ratings work well)
- Totals: Regression with game script factors
- Player Props: Random Forest/XGBoost

Available models:
- Linear Regression (totals, spreads) - PRIMARY for NFL
- Polynomial Regression (spreads, totals)
- Random Forest (totals, spreads, moneyline, player props)
- XGBoost (totals, spreads, moneyline, player props)
- LightGBM (totals, spreads, moneyline, player props)
- Logistic Regression (moneyline)
"""
