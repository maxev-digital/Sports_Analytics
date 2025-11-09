# backend/goalie_alert.py
from ml.models.goalie_pull_predictor import GoaliePullPredictor
import asyncio

predictor = GoaliePullPredictor()

async def check_goalie_pull(game_state, websocket):
    prob = predictor.predict(game_state)
    
    if prob > 0.75 and game_state['seconds_remaining'] < 180:
        alert = {
            'type': 'goalie_pull_prediction',
            'team': game_state['trailing_team'],
            'prob': f"{prob:.1%}",
            'time_left': f"{game_state['seconds_remaining']}s",
            'bet_options': [
                {"label": "Empty Net Over 0.5", "odds": "+350", "ev": "+42%"},
                {"label": "Trailing Team Total Over", "odds": "+280", "ev": "+38%"},
                {"label": "Next Goal", "odds": "+400", "ev": "+40%"}
            ]
        }
        await websocket.send_json(alert)