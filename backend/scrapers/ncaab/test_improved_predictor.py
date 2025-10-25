#!/usr/bin/env python3
"""
Test Improved NCAA Basketball Predictor
Compares original vs improved methodology
"""

import pandas as pd
import numpy as np
import sys
import shutil
import os

sys.path.insert(0, 'backend')

def test_improved_predictor():
    """Test the improved predictor against the original"""
    
    print("🧪 TESTING IMPROVED PREDICTOR METHODOLOGY")
    print("="*60)
    
    # Find data files
    import glob
    kenpom_files = glob.glob("backend/data/historical/kenpom_*_season_*.csv")
    games_files = glob.glob("backend/data/historical/game_results_*_season_*.csv")
    
    if not kenpom_files or not games_files:
        print("❌ Historical data not found")
        return
    
    kenpom_file = max(kenpom_files)
    games_file = max(games_files)
    
    # Load data
    kenpom_data = pd.read_csv(kenpom_file)
    games_data = pd.read_csv(games_file)
    
    # Test on first 1000 games for speed
    test_games = games_data.head(1000)
    
    print(f"📊 Testing on {len(test_games)} games")
    print(f"   KenPom teams: {len(kenpom_data)}")
    print("")
    
    # Test original predictor
    print("🔸 Testing ORIGINAL predictor...")
    try:
        from models.ncaab.totals_predictor import NCAABTotalsPredictor as OriginalPredictor
        
        original_predictor = OriginalPredictor(kenpom_data)
        original_predictions = []
        
        for _, game in test_games.iterrows():
            pred = original_predictor.predict_game(game['Home_Team'], game['Away_Team'])
            if pred:
                original_predictions.append({
                    'Model_Total': pred['Model_Total'],
                    'Actual_Total': game['Actual_Total']
                })
        
        if original_predictions:
            orig_df = pd.DataFrame(original_predictions)
            orig_df['Error'] = orig_df['Model_Total'] - orig_df['Actual_Total']
            orig_df['Abs_Error'] = abs(orig_df['Error'])
            
            orig_mae = orig_df['Abs_Error'].mean()
            orig_avg_actual = orig_df['Actual_Total'].mean()
            orig_avg_predicted = orig_df['Model_Total'].mean()
            orig_within_5 = (orig_df['Abs_Error'] <= 5).sum() / len(orig_df) * 100
            
            print(f"   ✅ Original Results:")
            print(f"      MAE: {orig_mae:.2f} points")
            print(f"      Actual avg: {orig_avg_actual:.1f}")
            print(f"      Model avg: {orig_avg_predicted:.1f}")
            print(f"      Within ±5: {orig_within_5:.1f}%")
            print(f"      Sample: {len(orig_df)} games")
        else:
            print("   ❌ Original predictor failed")
            orig_mae = 999
            
    except Exception as e:
        print(f"   ❌ Original predictor error: {str(e)}")
        orig_mae = 999
    
    # Test improved predictor
    print("\n🔹 Testing IMPROVED predictor...")
    try:
        from improved_totals_predictor import NCAABTotalsPredictor as ImprovedPredictor
        
        improved_predictor = ImprovedPredictor(kenpom_data)
        improved_predictions = []
        
        for _, game in test_games.iterrows():
            pred = improved_predictor.predict_game(game['Home_Team'], game['Away_Team'])
            if pred:
                improved_predictions.append({
                    'Model_Total': pred['Model_Total'],
                    'Actual_Total': game['Actual_Total']
                })
        
        if improved_predictions:
            imp_df = pd.DataFrame(improved_predictions)
            imp_df['Error'] = imp_df['Model_Total'] - imp_df['Actual_Total']
            imp_df['Abs_Error'] = abs(imp_df['Error'])
            
            imp_mae = imp_df['Abs_Error'].mean()
            imp_avg_actual = imp_df['Actual_Total'].mean()
            imp_avg_predicted = imp_df['Model_Total'].mean()
            imp_within_5 = (imp_df['Abs_Error'] <= 5).sum() / len(imp_df) * 100
            
            print(f"   ✅ Improved Results:")
            print(f"      MAE: {imp_mae:.2f} points")
            print(f"      Actual avg: {imp_avg_actual:.1f}")
            print(f"      Model avg: {imp_avg_predicted:.1f}")
            print(f"      Within ±5: {imp_within_5:.1f}%")
            print(f"      Sample: {len(imp_df)} games")
            
            # Compare
            print(f"\n📈 IMPROVEMENT:")
            mae_improvement = orig_mae - imp_mae
            within_5_improvement = imp_within_5 - orig_within_5
            
            if mae_improvement > 0:
                print(f"   ✅ MAE improved by {mae_improvement:.2f} points")
            else:
                print(f"   ❌ MAE got worse by {abs(mae_improvement):.2f} points")
            
            if within_5_improvement > 0:
                print(f"   ✅ Within ±5 improved by {within_5_improvement:.1f}%")
            else:
                print(f"   ❌ Within ±5 got worse by {abs(within_5_improvement):.1f}%")
            
            # Decide whether to replace
            if imp_mae < orig_mae and imp_mae < 10:
                print(f"\n🚀 RECOMMENDATION: Replace with improved predictor")
                
                # Backup and replace
                backup_path = "backend/models/ncaab/totals_predictor_original.py"
                current_path = "backend/models/ncaab/totals_predictor.py"
                improved_path = "improved_totals_predictor.py"
                
                if os.path.exists(current_path):
                    shutil.copy2(current_path, backup_path)
                    print(f"   📁 Backed up original to: {backup_path}")
                
                shutil.copy2(improved_path, current_path)
                print(f"   ✅ Replaced with improved predictor")
                
                print(f"\n🎯 NOW RUN:")
                print(f"   python run_ncaab_backtest.py")
                
                return True
            else:
                print(f"\n⚠️  RECOMMENDATION: Keep original predictor")
                print(f"   Improved version not significantly better")
                return False
        else:
            print("   ❌ Improved predictor failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Improved predictor error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    test_improved_predictor()
