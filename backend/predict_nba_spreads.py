#!/usr/bin/env python3
import sys, joblib, torch, sqlite3, requests, numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

SPORT, BET_TYPE = "NBA", "spreads"
N_FEATURES = 40
MODELS_DIR = Path(__file__).parent / "ml" / "models"
DB = Path(__file__).parent / "ml" / "predictions.db"

print(f"{SPORT} {BET_TYPE} - Loading models...")
models, sport_lower = {}, SPORT.lower()

for name in ["xgboost", "lightgbm", "random_forest", "linear", "catboost"]:
    path = MODELS_DIR / f"{sport_lower}_{name}_{BET_TYPE}_enhanced.joblib"
    if path.exists():
        models[name] = joblib.load(path)

path = MODELS_DIR / f"{sport_lower}_pytorch_{BET_TYPE}_latest.pt"
if path.exists():
    models["pytorch"] = torch.load(path, map_location="cpu", weights_only=False)

path = MODELS_DIR / f"{sport_lower}_ensemble_{BET_TYPE}_latest.pt"
if path.exists():
    models["ensemble"] = torch.load(path, map_location="cpu", weights_only=False)

print(f"Loaded {len(models)} models")

games = []
for url in ["http://localhost:8000/api/games", "http://148.230.87.135:8000/api/games"]:
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            games = [g for g in r.json() if g.get("sport","").upper() == SPORT]
            break
    except: pass

print(f"Found {len(games)} games")
if not games or not models:
    sys.exit(0)

predictions = []
for game in games:
    home, away = game.get("home_team"), game.get("away_team")
    line = game.get("home_spread")
    date, time_str = game.get("commence_time_cst", "")[:10], game.get("commence_time_cst", "")[11:16]
    
    if not line or not home or not away:
        continue
    
    features = np.zeros((1, N_FEATURES))
    
    for model_name, model in models.items():
        try:
            if model_name in ["pytorch", "ensemble"]:
                model.eval()
                with torch.no_grad():
                    pred = model(torch.FloatTensor(features))
                    pred = torch.softmax(pred, dim=1)[0, 1].item() if pred.dim() > 1 and pred.shape[1] > 1 else pred.squeeze().item()
            else:
                pred = model.predict_proba(features)[0, 1] if BET_TYPE == "moneyline" and hasattr(model, "predict_proba") else model.predict(features)[0]
            
            edge = pred - line if BET_TYPE != "moneyline" else abs(pred - 0.5)
            rec = ("OVER" if edge > 3 else "UNDER" if edge < -3 else "") if BET_TYPE == "totals" else ("HOME" if edge > 2 else "AWAY" if edge < -2 else "") if BET_TYPE == "spreads" else ("HOME" if pred > 0.55 else "AWAY" if pred < 0.45 else "")
            
            predictions.append((SPORT, date, time_str, home, away, BET_TYPE, model_name, round(float(pred), 2), float(line), rec, round(abs(float(edge)), 2), round(float(edge), 2), datetime.now().isoformat()))
        except Exception as e:
            pass

if predictions:
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.executemany("INSERT INTO predictions (sport, game_date, game_time, home_team, away_team, bet_type, model, prediction, line, recommended_bet, confidence, edge, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", predictions)
    conn.commit()
    conn.close()
    print(f"SAVED {len(predictions)} predictions")
