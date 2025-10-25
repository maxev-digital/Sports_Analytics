#!/usr/bin/env python3
"""
Quick Model Calibration - Test Better Parameters
Run this to see if adjusting parameters improves accuracy
"""

import pandas as pd
import numpy as np
import sys
sys.path.insert(0, 'backend')

from models.ncaab.totals_predictor import NCAABTotalsPredictor

def test_parameters(kenpom_file, games_file, hca, league_avg):
    """Test specific parameter combination"""
    
    # Load data
    kenpom_data = pd.read_csv(kenpom_file)
    games_data = pd.read_csv(games_file)
    
    # Create predictor with test parameters
    predictor = NCAABTotalsPredictor(
        kenpom_data=kenpom_data,
        home_court_advantage=hca,
        league_avg_eff=league_avg
    )
    
    # Generate predictions for first 500 games (faster test)
    test_games = games_data.head(500)
    predictions = []
    
    for _, game in test_games.iterrows():
        pred = predictor.predict_game(game['Home_Team'], game['Away_Team'])
        if pred:
            predictions.append({
                'Model_Total': pred['Model_Total'],
                'Actual_Total': game['Actual_Total']
            })
    
    if not predictions:
        return None
    
    df = pd.DataFrame(predictions)
    
    # Calculate metrics
    df['Error'] = df['Model_Total'] - df['Actual_Total']
    df['Abs_Error'] = abs(df['Error'])
    
    mae = df['Abs_Error'].mean()
    avg_actual = df['Actual_Total'].mean()
    avg_predicted = df['Model_Total'].mean()
    bias = (df['Error'] > 0).sum() / len(df) * 100
    
    return {
        'MAE': round(mae, 2),
        'Avg_Actual': round(avg_actual, 1),
        'Avg_Predicted': round(avg_predicted, 1),
        'Over_Pct': round(bias, 1),
        'Sample_Size': len(df)
    }

def main():
    """Test different parameter combinations"""
    
    print("🔧 NCAA BASKETBALL MODEL CALIBRATION")
    print("="*50)
    
    # Find latest files
    import glob
    kenpom_files = glob.glob("backend/data/historical/kenpom_*_season_*.csv")
    games_files = glob.glob("backend/data/historical/game_results_*_season_*.csv")
    
    if not kenpom_files or not games_files:
        print("❌ Historical data not found")
        print("   Make sure you have files in backend/data/historical/")
        return
    
    kenpom_file = max(kenpom_files)
    games_file = max(games_files)
    
    print(f"📊 Testing with:")
    print(f"   KenPom: {kenpom_file}")
    print(f"   Games: {games_file}")
    print("")
    
    # Test parameter combinations
    parameter_tests = [
        # Current (bad results)
        (3.5, 105.0, "Current (Bad)"),
        
        # Higher league average (NCAA scores more than NBA)
        (3.5, 110.0, "Higher League Avg"),
        (3.5, 112.0, "Even Higher Avg"),
        (3.5, 115.0, "Much Higher Avg"),
        
        # Higher home court advantage
        (4.5, 110.0, "Higher HCA + Avg"),
        (5.0, 112.0, "High HCA + Avg"),
        (4.0, 113.0, "Balanced"),
    ]
    
    print(f"{'Parameters':<20} {'MAE':<8} {'Actual':<8} {'Model':<8} {'Over%':<6} {'Status'}")
    print("-" * 60)
    
    best_mae = float('inf')
    best_params = None
    
    for hca, league_avg, name in parameter_tests:
        print(f"{name:<20} ", end="")
        
        try:
            results = test_parameters(kenpom_file, games_file, hca, league_avg)
            
            if results:
                mae = results['MAE']
                
                print(f"{mae:<8} {results['Avg_Actual']:<8} {results['Avg_Predicted']:<8} {results['Over_Pct']:<6} ", end="")
                
                if mae < 10:
                    print("✅ Good")
                elif mae < 15:
                    print("⚠️  OK")
                else:
                    print("❌ Bad")
                
                if mae < best_mae:
                    best_mae = mae
                    best_params = (hca, league_avg, name)
            else:
                print("❌ Failed")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    if best_params:
        hca, league_avg, name = best_params
        print(f"\n🏆 BEST PARAMETERS: {name}")
        print(f"   HOME_COURT_ADVANTAGE = {hca}")
        print(f"   LEAGUE_AVG_EFFICIENCY = {league_avg}")
        print(f"   MAE = {best_mae}")
        
        print(f"\n🔧 TO APPLY:")
        print(f"   1. Edit backend/config.py")
        print(f"   2. Change HOME_COURT_ADVANTAGE = {hca}")
        print(f"   3. Change LEAGUE_AVG_EFFICIENCY = {league_avg}")
        print(f"   4. Re-run: python run_ncaab_backtest.py")

if __name__ == "__main__":
    main()
