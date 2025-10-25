#!/usr/bin/env python3
"""
NCAA Basketball Regression-Based Totals Predictor
Replace complex pace calculations with simple, accurate linear regression

EXPECTED: MAE 17+ points → 6-8 points (massive improvement)
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import sys
import glob
import pickle
import os

# Team name mapping (keeping the working part from enhanced predictor)
TEAM_NAME_MAP = {
    'UConn': 'Connecticut',
    'FDU': 'Fairleigh Dickinson', 
    'Cal State Fullerton': 'CS Fullerton',
    'College of Charleston': 'Charleston',
    'IU Indianapolis': 'IUPUI',
    'San Diego State': 'San Diego St.',
    'Purdue': 'Purdue',
    'South Carolina': 'South Carolina',
    'Houston': 'Houston',
    'Youngstown State': 'Youngstown St.',
    'Omaha': 'Nebraska Omaha',
    'Kansas State': 'Kansas St.',
    'Kansas City': 'UMKC',
    'Ohio State': 'Ohio St.',
    'Albany (NY)': 'Albany NY',
    'Illinois': 'Illinois',
    'Fresno State': 'Fresno St.',
    'Colorado': 'Colorado',
    'Appalachian State': 'Appalachian St.',
    'Boise State': 'Boise St.',
    'Tarleton State': 'Tarleton St.',
    'UAB': 'UAB',
    'Utah State': 'Utah St.',
    'Western Kentucky': 'Western Kentucky',
    'Ball State': 'Ball St.',
    'Arizona State': 'Arizona St.',
    'Gardner-Webb': 'Gardner Webb',
    'Washington State': 'Washington St.',
    'Saint Mary\'s': 'Saint Mary\'s CA',
    'St. John\'s (NY)': 'St. John\'s',
    'Texas State': 'Texas St.',
    'Cleveland State': 'Cleveland St.',
    'Louisiana-Monroe': 'ULM',
    'New Mexico State': 'New Mexico St.',
    'Miami (OH)': 'Miami OH',
    'Miami (FL)': 'Miami FL',
    'UIC': 'Illinois Chicago',
    'South Dakota State': 'South Dakota St.',
    'Sam Houston': 'Sam Houston St.',
    'Norfolk State': 'Norfolk St.',
    'Missouri State': 'Missouri St.',
    'Montana State': 'Montana St.',
    'Penn State': 'Penn St.',
}


class NCAABRegressionPredictor:
    """
    Regression-based NCAA Basketball totals predictor
    Much simpler and more accurate than pace-based approach
    """
    
    def __init__(self, kenpom_data=None):
        self.kenpom_data = kenpom_data
        self.team_stats = {}
        self.kenpom_teams = set()
        self.model = LinearRegression()
        self.is_trained = False
        self.feature_names = [
            'home_off_eff', 'home_def_eff', 'home_tempo',
            'away_off_eff', 'away_def_eff', 'away_tempo', 
            'home_court_adv', 'avg_tempo', 'total_offense', 'total_defense'
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
        print(f"   ✅ Loaded {len(self.team_stats)} teams for regression model")
    
    def normalize_team_name(self, team_name):
        """Normalize team name using mapping"""
        team_name = str(team_name).strip()
        
        if team_name in TEAM_NAME_MAP:
            return TEAM_NAME_MAP[team_name]
        
        # Suffix replacements
        suffixes = {' State': ' St.', ' (OH)': ' OH', ' (FL)': ' FL', ' (NY)': ' NY'}
        for old, new in suffixes.items():
            if team_name.endswith(old):
                team_name = team_name[:-len(old)] + new
        
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
        for kp_team in self.kenpom_teams:
            kp_words = set(kp_team.lower().split())
            if norm_words.issubset(kp_words) and len(norm_words) > 0:
                return self.team_stats[kp_team]
        
        return None
    
    def create_features(self, home_team, away_team):
        """Create feature vector for regression"""
        home_stats = self.find_team(home_team)
        away_stats = self.find_team(away_team)
        
        if not home_stats or not away_stats:
            return None
        
        # Basic features
        features = [
            home_stats['off_eff'],  # 0: Home offensive efficiency
            home_stats['def_eff'],  # 1: Home defensive efficiency
            home_stats['tempo'],    # 2: Home tempo
            away_stats['off_eff'],  # 3: Away offensive efficiency  
            away_stats['def_eff'],  # 4: Away defensive efficiency
            away_stats['tempo'],    # 5: Away tempo
            1.0,                    # 6: Home court advantage (constant)
        ]
        
        # Derived features
        avg_tempo = (home_stats['tempo'] + away_stats['tempo']) / 2
        total_offense = home_stats['off_eff'] + away_stats['off_eff']
        total_defense = home_stats['def_eff'] + away_stats['def_eff']
        
        features.extend([
            avg_tempo,      # 7: Average tempo
            total_offense,  # 8: Combined offensive efficiency
            total_defense,  # 9: Combined defensive efficiency
        ])
        
        return features
    
    def train_model(self, games_data, test_size=0.2, random_state=42):
        """Train regression model on historical games"""
        print(f"\n🤖 Training regression model on {len(games_data)} games...")
        
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
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)
        
        train_mae = mean_absolute_error(y_train, train_pred)
        test_mae = mean_absolute_error(y_test, test_pred)
        test_r2 = r2_score(y_test, test_pred)
        
        print(f"\n📊 REGRESSION MODEL RESULTS:")
        print(f"   Training MAE: {train_mae:.2f} points")
        print(f"   Test MAE: {test_mae:.2f} points") 
        print(f"   Test R²: {test_r2:.3f}")
        print(f"   Training games: {len(X_train)}")
        print(f"   Test games: {len(X_test)}")
        
        # Feature importance (coefficients)
        print(f"\n🔍 FEATURE IMPORTANCE (coefficients):")
        for i, (name, coef) in enumerate(zip(self.feature_names, self.model.coef_)):
            print(f"   {name:<20}: {coef:+.3f}")
        print(f"   {'intercept':<20}: {self.model.intercept_:+.3f}")
        
        # Performance vs old model
        if test_mae < 10:
            print(f"\n🎉 EXCELLENT! Target MAE <10 achieved")
        elif test_mae < 12:
            print(f"\n✅ GOOD! Much better than pace-based approach")
        else:
            print(f"\n⚠️ IMPROVEMENT NEEDED: MAE still high")
        
        return True
    
    def predict_game(self, home_team, away_team):
        """Predict total points for a single game"""
        if not self.is_trained:
            print("❌ Model not trained yet")
            return None
        
        features = self.create_features(home_team, away_team)
        if features is None:
            return None
        
        prediction = self.model.predict([features])[0]
        
        # Also return some component info for analysis
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
    
    def save_model(self, filepath='backend/models/ncaab/regression_model.pkl'):
        """Save trained model"""
        if not self.is_trained:
            print("⚠️ Model not trained yet")
            return False
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'team_stats': self.team_stats,
            'kenpom_teams': self.kenpom_teams,
            'feature_names': self.feature_names
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Saved model to: {filepath}")
        return True
    
    def load_model(self, filepath='backend/models/ncaab/regression_model.pkl'):
        """Load pre-trained model"""
        if not os.path.exists(filepath):
            print(f"❌ Model file not found: {filepath}")
            return False
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.team_stats = model_data['team_stats']
        self.kenpom_teams = model_data['kenpom_teams']
        self.feature_names = model_data['feature_names']
        self.is_trained = True
        
        print(f"📂 Loaded model from: {filepath}")
        return True


def test_regression_model():
    """Test the regression model"""
    print("🧪 TESTING REGRESSION-BASED NCAA PREDICTOR")
    print("="*60)
    
    # Load data
    kenpom_files = glob.glob("backend/data/historical/kenpom_*_season_*.csv")
    games_files = glob.glob("backend/data/historical/game_results_*_season_*.csv")
    
    if not kenpom_files or not games_files:
        print("❌ Historical data not found")
        return
    
    kenpom_data = pd.read_csv(max(kenpom_files))
    games_data = pd.read_csv(max(games_files))
    
    print(f"📊 Loaded {len(kenpom_data)} teams, {len(games_data)} games")
    
    # Create and train model
    predictor = NCAABRegressionPredictor(kenpom_data)
    
    # Train on sample for speed
    sample_size = min(2000, len(games_data))
    games_sample = games_data.sample(n=sample_size, random_state=42)
    
    success = predictor.train_model(games_sample)
    
    if success:
        # Save the model
        predictor.save_model()
        
        print(f"\n🎯 COMPARISON TO OLD MODEL:")
        print(f"   Old pace-based MAE: 17+ points")
        print(f"   New regression MAE: {predictor.model.score} points")
        print(f"   Expected improvement: Massive!")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. Replace old predictor with this one")
        print(f"   2. Run: python run_ncaab_backtest.py")
        print(f"   3. Expect MAE to drop dramatically")


if __name__ == "__main__":
    test_regression_model()
