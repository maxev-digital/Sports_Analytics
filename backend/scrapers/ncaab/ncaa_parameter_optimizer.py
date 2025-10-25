#!/usr/bin/env python3
"""
NCAA Basketball Parameter Optimizer
Tests multiple parameter combinations to find optimal values for NCAA basketball

Based on your backtest results showing 9-point under-prediction
"""

import pandas as pd
import numpy as np
import sys
import glob

# Add backend to path
sys.path.insert(0, 'backend')

def load_test_data():
    """Load a sample of historical data for testing"""
    # Find most recent files
    kenpom_files = glob.glob("backend/data/historical/kenpom_*_season_*.csv")
    games_files = glob.glob("backend/data/historical/game_results_*_season_*.csv")
    
    if not kenpom_files or not games_files:
        print("❌ Historical data not found")
        return None, None
    
    kenpom_data = pd.read_csv(max(kenpom_files))
    games_data = pd.read_csv(max(games_files))
    
    # Take a sample for faster testing
    games_sample = games_data.sample(n=min(500, len(games_data)), random_state=42)
    
    return kenpom_data, games_sample

def test_parameters(kenpom_data, games_data, hca, league_avg):
    """Test specific parameter combination"""
    
    # Quick predictor class for testing
    class QuickPredictor:
        def __init__(self, kenpom_data, hca, league_avg):
            self.hca = hca
            self.league_avg = league_avg
            self.team_stats = {}
            
            for _, row in kenpom_data.iterrows():
                team_name = str(row['Team']).strip()
                self.team_stats[team_name] = {
                    'tempo': row['AdjTempo'],
                    'off_eff': row['AdjOffEff'],
                    'def_eff': row['AdjDefEff']
                }
        
        def find_team(self, team_name):
            team_name = str(team_name).strip()
            
            # Exact match
            if team_name in self.team_stats:
                return self.team_stats[team_name]
            
            # Partial match
            for kmp_team, stats in self.team_stats.items():
                if team_name.lower() in kmp_team.lower() or kmp_team.lower() in team_name.lower():
                    return stats
            
            return None
        
        def predict_game(self, home_team, away_team):
            home_stats = self.find_team(home_team)
            away_stats = self.find_team(away_team)
            
            if not home_stats or not away_stats:
                return None
            
            # Calculate expected pace
            expected_pace = np.sqrt(home_stats['tempo'] * away_stats['tempo'])
            
            # Calculate efficiencies
            home_eff = home_stats['off_eff'] - (away_stats['def_eff'] - self.league_avg) + self.hca
            away_eff = away_stats['off_eff'] - (home_stats['def_eff'] - self.league_avg)
            
            # Calculate points
            home_points = (home_eff / 100) * expected_pace
            away_points = (away_eff / 100) * expected_pace
            
            return home_points + away_points
    
    # Test predictions
    predictor = QuickPredictor(kenpom_data, hca, league_avg)
    predictions = []
    actuals = []
    
    for _, game in games_data.iterrows():
        pred = predictor.predict_game(game['Home_Team'], game['Away_Team'])
        if pred is not None:
            predictions.append(pred)
            actuals.append(game['Actual_Total'])
    
    if len(predictions) == 0:
        return None
    
    predictions = np.array(predictions)
    actuals = np.array(actuals)
    
    # Calculate metrics
    mae = np.mean(np.abs(predictions - actuals))
    avg_actual = np.mean(actuals)
    avg_pred = np.mean(predictions)
    within_5 = np.mean(np.abs(predictions - actuals) <= 5) * 100
    
    return {
        'mae': mae,
        'avg_actual': avg_actual,
        'avg_pred': avg_pred,
        'within_5': within_5,
        'sample_size': len(predictions)
    }

def main():
    print("🧪 NCAA BASKETBALL PARAMETER OPTIMIZER")
    print("="*60)
    
    # Load data
    print("📊 Loading historical data...")
    kenpom_data, games_data = load_test_data()
    
    if kenpom_data is None:
        print("❌ Cannot load data")
        return
    
    print(f"   ✅ Loaded {len(kenpom_data)} teams, {len(games_data)} games")
    
    # Parameter combinations to test
    # Based on NCAA characteristics: Higher scoring, different pace
    test_params = [
        # Current (your results)
        (3.5, 105.0, "Current (Bad)"),
        
        # NCAA-optimized based on 138.3 avg
        (4.0, 110.0, "NCAA Optimized"),
        (4.2, 111.0, "NCAA High"),
        (3.8, 109.0, "NCAA Conservative"),
        
        # Alternative approaches
        (4.5, 112.0, "Aggressive"),
        (3.5, 112.0, "High Efficiency Only"),
        (4.5, 108.0, "High HCA Only"),
        
        # Based on your actual avg (138.3)
        (4.0, 113.0, "Target 138 Avg"),
        (3.5, 115.0, "Very High Efficiency"),
    ]
    
    print(f"\n🔬 Testing {len(test_params)} parameter combinations...")
    print(f"{'Parameters':<20} {'MAE':<8} {'Actual':<8} {'Model':<8} {'±5%':<6} {'Status'}")
    print("-" * 60)
    
    best_mae = float('inf')
    best_params = None
    
    for hca, eff, name in test_params:
        results = test_parameters(kenpom_data, games_data, hca, eff)
        
        if results is None:
            print(f"{name:<20} FAILED")
            continue
        
        mae = results['mae']
        actual_avg = results['avg_actual']
        pred_avg = results['avg_pred']
        within_5 = results['within_5']
        
        # Status evaluation
        if mae < 7:
            status = "✅ Excellent"
        elif mae < 10:
            status = "✅ Good"
        elif mae < 15:
            status = "⚠️ OK"
        else:
            status = "❌ Bad"
        
        print(f"{name:<20} {mae:<8.2f} {actual_avg:<8.1f} {pred_avg:<8.1f} {within_5:<6.1f} {status}")
        
        if mae < best_mae:
            best_mae = mae
            best_params = (hca, eff, name)
    
    print("\n🏆 BEST PARAMETERS:", best_params[2])
    print(f"   HOME_COURT_ADVANTAGE = {best_params[0]}")
    print(f"   LEAGUE_AVG_EFFICIENCY = {best_params[1]}")
    print(f"   MAE = {best_mae:.2f}")
    
    print("\n🔧 TO APPLY:")
    print("   1. Edit backend/config.py")
    print(f"   2. Change HOME_COURT_ADVANTAGE = {best_params[0]}")
    print(f"   3. Change LEAGUE_AVG_EFFICIENCY = {best_params[1]}")
    print("   4. Run: python run_ncaab_backtest.py")
    
    # Additional recommendations
    print("\n💡 ANALYSIS:")
    if best_mae > 10:
        print("   ⚠️ Still high MAE - may need methodology changes")
        print("   Consider: Different pace calculation or efficiency formula")
    elif best_mae > 7:
        print("   📊 Good improvement - fine-tune from here")
    else:
        print("   🎉 Excellent results - ready for production!")

if __name__ == "__main__":
    main()
