#!/usr/bin/env python3
"""
NCAA Basketball Model - Methodology Analysis
Diagnose why parameter optimization failed and propose better approach

FINDING: All parameters give MAE >15 points = methodology issue, not calibration
"""

import pandas as pd
import numpy as np
import sys
import glob

def analyze_methodology_problems():
    """Analyze why the current pace-based approach isn't working"""
    
    print("🔬 NCAA BASKETBALL METHODOLOGY ANALYSIS")
    print("="*60)
    print("\n📊 PARAMETER OPTIMIZATION RESULTS ANALYSIS:")
    print("   All tested parameters: MAE 15-24 points")
    print("   Target for useful model: MAE <7 points") 
    print("   Gap: 2-3x worse than needed")
    print("   Conclusion: Methodology problem, not parameter problem")
    
    print("\n🎯 LIKELY ISSUES WITH CURRENT APPROACH:")
    print("\n1. PACE CALCULATION (Geometric Mean):")
    print("   Current: √(home_tempo × away_tempo)")
    print("   Problem: May not reflect actual game pace")
    print("   NCAA Reality: Pace varies by style matchups")
    
    print("\n2. EFFICIENCY CALCULATION:")
    print("   Current: team_off - (opponent_def - league_avg)")
    print("   Problem: May be too extreme for NCAA")
    print("   NCAA Reality: More variance, different baselines")
    
    print("\n3. HOME COURT ADVANTAGE:")
    print("   Current: Fixed points added to home team")
    print("   Problem: May affect pace AND efficiency differently")
    print("   NCAA Reality: HCA varies by venue, conference")
    
    print("\n4. MISSING FACTORS:")
    print("   ❌ Conference strength adjustments")
    print("   ❌ Recent form (hot/cold streaks)")  
    print("   ❌ Rest days / travel")
    print("   ❌ Altitude adjustments")
    print("   ❌ Tournament vs regular season")

def propose_simplified_approach():
    """Propose a simpler, more direct approach"""
    
    print("\n🚀 PROPOSED SOLUTION: SIMPLIFIED REGRESSION MODEL")
    print("="*60)
    print("\nInstead of complex pace calculations, use direct regression:")
    print("\n📈 LINEAR REGRESSION APPROACH:")
    print("   Total = α + β₁×(Home_OffEff) + β₂×(Away_OffEff)")
    print("         + β₃×(Home_DefEff) + β₄×(Away_DefEff)")  
    print("         + β₅×(Home_Tempo) + β₆×(Away_Tempo)")
    print("         + β₇×(HCA) + β₈×(Conference_Avg)")
    
    print("\n✅ ADVANTAGES:")
    print("   • Let data determine relationships")
    print("   • No assumptions about pace calculation")
    print("   • Can add more factors easily")
    print("   • Interpretable coefficients")
    print("   • Likely much more accurate")
    
    print("\n📊 EXPECTED PERFORMANCE:")
    print("   Target MAE: 5-8 points (vs current 17+)")
    print("   Within ±5: 40-50% (vs current 18%)")
    print("   R²: 0.3-0.5 (explainable variance)")

def create_regression_predictor():
    """Create a simple regression-based predictor"""
    
    print("\n🔧 IMPLEMENTATION PLAN:")
    print("="*60)
    print("\n1. COLLECT TRAINING DATA:")
    print("   • Use your existing 2,345 games")
    print("   • Features: Home/Away OffEff, DefEff, Tempo")
    print("   • Target: Actual_Total")
    
    print("\n2. TRAIN MODEL:")
    print("   • sklearn LinearRegression")
    print("   • 80/20 train/test split")
    print("   • Cross-validation")
    
    print("\n3. FEATURE ENGINEERING:")
    print("   • Tempo_Avg = (Home_Tempo + Away_Tempo) / 2")
    print("   • Eff_Diff = (Home_Off + Away_Off) - (Home_Def + Away_Def)")
    print("   • Pace_Product = Home_Tempo × Away_Tempo")
    print("   • HCA_Binary = 1 for home team")
    
    print("\n4. VALIDATION:")
    print("   • Compare MAE on test set")
    print("   • Should be <10 points easily")
    print("   • If >10, add more features")

def implementation_code():
    """Show actual implementation"""
    
    code = '''
# Simple Linear Regression Predictor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

def create_features(home_stats, away_stats):
    """Create regression features"""
    return [
        home_stats['off_eff'],    # Home offensive efficiency
        home_stats['def_eff'],    # Home defensive efficiency  
        home_stats['tempo'],      # Home tempo
        away_stats['off_eff'],    # Away offensive efficiency
        away_stats['def_eff'],    # Away defensive efficiency
        away_stats['tempo'],      # Away tempo
        1,                        # Home court advantage (binary)
        (home_stats['tempo'] + away_stats['tempo']) / 2,  # Average tempo
        home_stats['off_eff'] + away_stats['off_eff'],    # Combined offense
        home_stats['def_eff'] + away_stats['def_eff'],    # Combined defense
    ]

# Training
X = [create_features(home, away) for home, away in training_games]
y = [actual_total for actual_total in training_totals]

model = LinearRegression()
model.fit(X, y)

# Prediction
def predict_game(home_team, away_team):
    home_stats = find_team(home_team)
    away_stats = find_team(away_team)
    features = create_features(home_stats, away_stats)
    return model.predict([features])[0]
'''
    
    print("\n💻 SAMPLE CODE:")
    print("-" * 60)
    print(code)

def main():
    analyze_methodology_problems()
    propose_simplified_approach() 
    create_regression_predictor()
    implementation_code()
    
    print("\n🎯 RECOMMENDATION:")
    print("="*60)
    print("ABANDON current pace-based approach")
    print("BUILD simple linear regression model")
    print("EXPECT dramatic improvement: MAE 17→7 points")
    print("\n🚀 NEXT STEP:")
    print("Create: regression_predictor.py")
    print("Time: 30 minutes to implement")
    print("Payoff: Working model finally!")

if __name__ == "__main__":
    main()
