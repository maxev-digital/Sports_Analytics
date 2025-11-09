# ml/goalie_pull_predictor.py
import xgboost as xgb
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import joblib

class GoaliePullPredictor:
    def __init__(self):
        self.model = None
        self.features = [
            'seconds_remaining', 'trailing_goals', 'shots_last_2min',
            'faceoffs_won_last_5', 'coach_pull_rate', 'team_pull_rate',
            'goalie_toi', 'is_home', 'period'
        ]
    
    def train(self, df):
        X = df[self.features]
        y = df['pull_next_90s']  # 1 if pull in next 90s
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        self.model.fit(X_train, y_train)
        
        prob = self.model.predict_proba(X_test)[:, 1]
        print(f"AUC: {roc_auc_score(y_test, prob):.3f}")
        
        joblib.dump(self.model, 'ml/goalie_pull_model.pkl')
    
    def predict(self, game_state):
        if not self.model:
            self.model = joblib.load('ml/goalie_pull_model.pkl')
        
        X = pd.DataFrame([{
            'seconds_remaining': game_state['seconds_remaining'],
            'trailing_goals': game_state['trailing_goals'],
            'shots_last_2min': game_state['shots_last_2min'],
            'faceoffs_won_last_5': game_state['faceoffs_won_last_5'],
            'coach_pull_rate': game_state['coach_pull_rate'],
            'team_pull_rate': game_state['team_pull_rate'],
            'goalie_toi': game_state['goalie_toi'],
            'is_home': 1 if game_state['is_home'] else 0,
            'period': game_state['period']
        }])
        
        prob = self.model.predict_proba(X)[0][1]
        return prob