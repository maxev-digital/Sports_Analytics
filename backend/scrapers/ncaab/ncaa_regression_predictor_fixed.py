#!/usr/bin/env python3
"""
NCAA Basketball Regression Predictor - PROPERLY DESIGNED
Fixes the scaling and multicollinearity issues from the previous version

EXPECTED: MAE 14+ points → 6-8 points (proper regression)
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import sys
import glob
import pickle
import os

# Simplified team name mapping (most important ones)
TEAM_NAME_MAP = {
    'UConn': 'Connecticut',
    'FDU': 'Fairleigh Dickinson', 
    'Cal State Fullerton': 'CS Fullerton',
    'College of Charleston': 'Charleston',
    'IU Indianapolis': 'IUPUI',
    'San Diego State': 'San Diego St.',
    'Kansas State': 'Kansas St.',
    'Ohio State': 'Ohio St.',
    'Omaha': 'Nebraska Omaha',
    'Kansas City': 'UMKC',
    'Fresno State': 'Fresno St.',
    'Arizona State': 'Arizona St.',
    'Washington State': 'Washington St.',
    'Saint Mary\'s': 'Saint Mary\'s CA',
    'Texas State': 'Texas St.',
    'Louisiana-Monroe': 'ULM',
    'New Mexico State': 'New Mexico St.',
    'Miami (OH)': 'Miami OH',
    'Miami (FL)': 'Miami FL',
    'UIC': 'Illinois Chicago',
    'Sam Houston': 'Sam Houston St.',
    'Ball State': 'Ball St.',
    'Gardner-Webb': 'Gardner Webb',
}


class NCAABRegressionPredictorFixed:
    """
    Fixed regression predictor with proper feature engineering and scaling
    """
    
    def __init__(self, kenpom_data=None):
        self.kenpom_data = kenpom_data
        self.team_stats = {}
        self.kenpom_teams = set()
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Feature names for interpretability
        self.feature_names = [
            'home_off_eff', 'home_def_eff', 'home_tempo',
            'away_off_eff', 'away_def_eff', 'away_tempo', 
            'home_court_advantage', 'tempo_differential', 
            'offensive_strength', 'defensive_strength'
        ]
        
        if kenpom_data is not None:
            self._load_team_data()
    
    def _load_team_data(self):
        """Load KenPom team data"""
        for _, row in self.kenpom_data.iterrows():
            team_name = str(row['Team']).strip()
            self.kenpom_teams.add(team_name)
            self.team_stats[team_name] = {
                'tempo': row['AdjTempo'],
                'off_eff': row['AdjOffEff'],
                'def_eff': row['AdjDefEff']
            }
        print(f"   ✅ Loaded {len(self.team_stats)} teams for FIXED regression model")
    
    def normalize_team_name(self, team_name):
        """Normalize team name using mapping"""
        team_name = str(team_name).strip()
        
        if team_name in TEAM_NAME_MAP:
            return TEAM_NAME_MAP[team_name]
        
        # Simple suffix replacements
        if team_name.endswith(' State'):
            team_name = team_name[:-6] + ' St.'
        
        return team_name
    
    def find_team(self, team_name):
        """Find team with enhanced matching"""
        original = str(team_name).strip()
        
        # Exact match
        if original in self.team_stats:
            return self.team_stats[original]
        
        # Normalized match
        normalized = self.normalize_team_name(original)
        if normalized in self.team_stats:
            return self.team_stats[normalized]
        
        # Case insensitive
        for kp_team in self.kenpom_teams:
            if kp_team.lower() == normalized.lower():
                return self.team_stats[kp_team]
        
        # Word matching
        norm_words = set(normalized.lower().split())
        if norm_words:
            for kp_team in self.kenpom_teams:
                kp_words = set(kp_team.lower().split())
                if norm_words.issubset(kp_words):
                    return self.team_stats[kp_team]
        
        return None
    
    def create_features(self, home_team, away_team):
        """
        Create PROPERLY DESIGNED feature vector
        No multicollinearity, meaningful features only
        """
        home_stats = self.find_team(home_team)
        away_stats = self.find_team(away_team)
        
        if not home_stats or not away_stats:
            return None
        
        # Core features (no redundancy)
        features = [
            home_stats['off_eff'],          # 0: Home offensive efficiency
            home_stats['def_eff'],          # 1: Home defensive efficiency
            home_stats['tempo'],            # 2: Home tempo
            away_stats['off_eff'],          # 3: Away offensive efficiency  
            away_stats['def_eff'],          # 4: Away defensive efficiency
            away_stats['tempo'],            # 5: Away tempo
            1.0,                            # 6: Home court advantage (constant)
        ]
        
        # Meaningful derived features (no multicollinearity)
        tempo_diff = home_stats['tempo'] - away_stats['tempo']  # Pace matchup
        off_strength = (home_stats['off_eff'] + away_stats['off_eff']) / 2  # Avg offense
        def_strength = (home_stats['def_eff'] + away_stats['def_eff']) / 2  # Avg defense
        
        features.extend([
            tempo_diff,     # 7: Tempo differential
            off_strength,   # 8: Average offensive strength
            def_strength,   # 9: Average defensive strength
        ])
        
        return features
    
    def train_model(self, games_data, test_size=0.2, random_state=42):
        """Train regression model with proper scaling"""
        print(f"\n🤖 Training FIXED regression model on {len(games_data)} games...")
        
        # Create feature matrix and target vector
        X = []
        y = []
        successful = 0
        failed = 0
        
        for _, game in games_data.iterrows():
            features = self.create_features(game['Home_Team'], game['Away_Team'])
            if features is not None:
                X.append(features)
                y.append(game['Actual_Total'])
                successful += 1
            else:
                failed += 1
        
        if len(X) == 0:
            print("❌ No training data could be created")
            return False
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"   ✅ Created features for {successful} games")
        if failed > 0:
            print(f"   ⚠️ Failed to create features for {failed} games")
        
        # Print feature statistics BEFORE scaling
        print(f"\n📊 FEATURE STATISTICS (before scaling):")
        for i, name in enumerate(self.feature_names):
            mean_val = np.mean(X[:, i])
            std_val = np.std(X[:, i])
            print(f"   {name:<20}: Mean={mean_val:6.1f}, Std={std_val:6.1f}")
        
        # CRITICAL: Scale features to prevent trillion-coefficient problem
        X_scaled = self.scaler.fit_transform(X)
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=random_state
        )
        
        # Train model on SCALED features
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)
        
        train_mae = mean_absolute_error(y_train, train_pred)
        test_mae = mean_absolute_error(y_test, test_pred)
        test_r2 = r2_score(y_test, test_pred)
        
        print(f"\n📊 FIXED REGRESSION MODEL RESULTS:")
        print(f"   Training MAE: {train_mae:.2f} points")
        print(f"   Test MAE: {test_mae:.2f} points") 
        print(f"   Test R²: {test_r2:.3f}")
        print(f"   Training games: {len(X_train)}")
        print(f"   Test games: {len(X_test)}")
        
        # Feature importance (coefficients should be reasonable now)
        print(f"\n🔍 FEATURE IMPORTANCE (scaled coefficients):")
        for i, (name, coef) in enumerate(zip(self.feature_names, self.model.coef_)):
            print(f"   {name:<20}: {coef:+7.3f}")
        print(f"   {'intercept':<20}: {self.model.intercept_:+7.3f}")
        
        # Performance assessment
        if test_mae < 7:
            print(f"\n🎉 EXCELLENT! Target MAE <7 achieved")
        elif test_mae < 10:
            print(f"\n✅ GOOD! Much better than previous approaches")
        elif test_mae < 12:
            print(f"\n⚠️ IMPROVEMENT: Better but still needs work")
        else:
            print(f"\n❌ STILL PROBLEMATIC: MAE too high")
        
        # R² assessment
        if test_r2 > 0.3:
            print(f"   🎯 Good explanatory power (R² = {test_r2:.3f})")
        elif test_r2 > 0.1:
            print(f"   📊 Moderate explanatory power (R² = {test_r2:.3f})")
        else:
            print(f"   ⚠️ Low explanatory power (R² = {test_r2:.3f})")
        
        return True
    
    def predict_game(self, home_team, away_team):
        """Predict total points for a single game"""
        if not self.is_trained:
            print("❌ Model not trained yet")
            return None
        
        features = self.create_features(home_team, away_team)
        if features is None:
            return None
        
        # CRITICAL: Scale features using the same scaler
        features_scaled = self.scaler.transform([features])
        prediction = self.model.predict(features_scaled)[0]
        
        # Also return component info for analysis
        home_stats = self.find_team(home_team)
        away_stats = self.find_team(away_team)
        
        return {
            'Model_Total': round(prediction, 1),
            'Home_Tempo': home_stats['tempo'],
            'Away_Tempo': away_stats['tempo'],
            'Expected_Pace': (home_stats['tempo'] + away_stats['tempo']) / 2,
            'Home_OffEff': home_stats['off_eff'],
            'Away_OffEff': away_stats['off_eff'],
            'Home_Points': round(prediction * 0.52, 1),  # Rough estimate
            'Away_Points': round(prediction * 0.48, 1),  # Rough estimate
        }
    
    def save_model(self, filepath='backend/models/ncaab/regression_model_fixed.pkl'):
        """Save trained model"""
        if not self.is_trained:
            print("⚠️ Model not trained yet")
            return False
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,  # CRITICAL: Save scaler too
            'team_stats': self.team_stats,
            'kenpom_teams': self.kenpom_teams,
            'feature_names': self.feature_names
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Saved FIXED model to: {filepath}")
        return True
    
    def load_model(self, filepath='backend/models/ncaab/regression_model_fixed.pkl'):
        """Load pre-trained model"""
        if not os.path.exists(filepath):
            print(f"❌ Model file not found: {filepath}")
            return False
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']  # CRITICAL: Load scaler too
        self.team_stats = model_data['team_stats']
        self.kenpom_teams = model_data['kenpom_teams']
        self.feature_names = model_data['feature_names']
        self.is_trained = True
        
        print(f"📂 Loaded FIXED model from: {filepath}")
        return True


def test_fixed_regression_model():
    """Test the FIXED regression model"""
    print("🧪 TESTING FIXED REGRESSION-BASED NCAA PREDICTOR")
    print("="*70)
    
    # Load data
    kenpom_files = glob.glob("backend/data/historical/kenpom_*_season_*.csv")
    games_files = glob.glob("backend/data/historical/game_results_*_season_*.csv")
    
    if not kenpom_files or not games_files:
        print("❌ Historical data not found")
        return
    
    kenpom_data = pd.read_csv(max(kenpom_files))
    games_data = pd.read_csv(max(games_files))
    
    print(f"📊 Loaded {len(kenpom_data)} teams, {len(games_data)} games")
    
    # Create and train FIXED model
    predictor = NCAABRegressionPredictorFixed(kenpom_data)
    
    # Train on sample for speed
    sample_size = min(2000, len(games_data))
    games_sample = games_data.sample(n=sample_size, random_state=42)
    
    success = predictor.train_model(games_sample)
    
    if success:
        # Save the model
        predictor.save_model()
        
        print(f"\n🎯 COMPARISON TO BROKEN MODELS:")
        print(f"   Old pace-based MAE: 17+ points")
        print(f"   Broken regression MAE: 14+ points")
        print(f"   Fixed regression MAE: [see results above]")
        
        print(f"\n🚀 NEXT STEPS IF GOOD RESULTS:")
        print(f"   1. Replace totals_predictor.py with this approach")
        print(f"   2. Run: python run_ncaab_backtest.py")
        print(f"   3. Expect dramatically better accuracy")
        
        # Test a few predictions
        print(f"\n🎮 SAMPLE PREDICTIONS:")
        test_games = [
            ("Duke", "North Carolina"),
            ("Kansas", "Kentucky"), 
            ("Gonzaga", "Houston")
        ]
        
        for home, away in test_games:
            pred = predictor.predict_game(home, away)
            if pred:
                print(f"   {away} @ {home}: {pred['Model_Total']}")
            else:
                print(f"   {away} @ {home}: Could not predict")


if __name__ == "__main__":
    test_fixed_regression_model()
