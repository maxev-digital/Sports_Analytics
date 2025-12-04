#!/usr/bin/env python3
"""Generate individual prediction scripts for each sport/bet combination"""

# Configuration
SPORTS_BETS = {
    "NBA": ["totals", "spreads", "moneyline"],
    "NHL": ["totals", "spreads", "moneyline"],
    "NFL": ["totals", "spreads", "moneyline"],
    "NCAAF": ["totals", "spreads", "moneyline"],
    "NCAAB": ["totals"]
}

# Template for each prediction script
template = """#!/usr/bin/env python3
import sys, joblib, torch, sqlite3, requests, numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

SPORT = "{sport}"
BET_TYPE = "{bet_type}"
MODELS_DIR = Path(__file__).parent / "ml" / "models"
DB = Path(__file__).parent / "ml" / "predictions.db"

print(f"{{SPORT}} {{BET_TYPE}} - Loading models...")
models = {{}}
sport_lower = SPORT.lower()

for name in ["xgboost", "lightgbm", "random_forest", "linear", "catboost"]:
    path = MODELS_DIR / f"{{sport_lower}}_{{name}}_{{BET_TYPE}}_enhanced.joblib"
    if path.exists():
        models[name] = joblib.load(path)
        print(f"  ok {{name}}")

path = MODELS_DIR / f"{{sport_lower}}_pytorch_{{BET_TYPE}}_latest.pt"
if path.exists():
    models["pytorch"] = torch.load(path, map_location="cpu", weights_only=False)
    print(f"  ok pytorch")

path = MODELS_DIR / f"{{sport_lower}}_ensemble_{{BET_TYPE}}_latest.pt"
if path.exists():
    models["ensemble"] = torch.load(path, map_location="cpu", weights_only=False)
    print(f"  ok ensemble")

print(f"Loaded {{len(models)}} models")

print("Fetching games...")
games = []
for url in ["http://localhost:8000/api/games", "http://148.230.87.135:8000/api/games"]:
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            games = [g for g in r.json() if g.get("sport","").upper() == SPORT]
            break
    except: pass

print(f"Found {{len(games)}} games")

if not games or not models:
    print("No games or models")
    sys.exit(0)

predictions = []
for game in games:
    home = game.get("home_team")
    away = game.get("away_team")
    line = game.get("{line_key}")
    date = game.get("commence_time_cst", "")[:10]
    time_str = game.get("commence_time_cst", "")[11:16]

    if not line or not home or not away:
        continue

    features = np.array([[220.0]]).reshape(1, -1)

    for model_name, model in models.items():
        try:
            if model_name in ["pytorch", "ensemble"]:
                model.eval()
                with torch.no_grad():
                    pred = model(torch.FloatTensor(features))
                    if pred.dim() > 1 and pred.shape[1] > 1:
                        pred = torch.softmax(pred, dim=1)[0, 1].item()
                    else:
                        pred = pred.squeeze().item()
            else:
                if BET_TYPE == "moneyline" and hasattr(model, "predict_proba"):
                    pred = model.predict_proba(features)[0, 1]
                else:
                    pred = model.predict(features)[0]

            edge = pred - line if BET_TYPE != "moneyline" else abs(pred - 0.5)
            rec = ""
            if BET_TYPE == "totals":
                rec = "OVER" if edge > 3 else "UNDER" if edge < -3 else ""
            elif BET_TYPE == "spreads":
                rec = "HOME" if edge > 2 else "AWAY" if edge < -2 else ""
            elif BET_TYPE == "moneyline":
                rec = "HOME" if pred > 0.55 else "AWAY" if pred < 0.45 else ""

            predictions.append((
                SPORT, date, time_str, home, away, BET_TYPE, model_name,
                round(float(pred), 2), float(line), rec, round(abs(float(edge)), 2),
                round(float(edge), 2), datetime.now().isoformat()
            ))
        except Exception as e:
            print(f"  error {{model_name}}: {{e}}")

if predictions:
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.executemany(
        "INSERT INTO predictions (sport, game_date, game_time, home_team, away_team, bet_type, model, prediction, line, recommended_bet, confidence, edge, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        predictions
    )
    conn.commit()
    conn.close()
    print(f"SAVED {{len(predictions)}} predictions")
else:
    print("No predictions")
"""

# Generate all scripts
created = []
for sport, bet_types in SPORTS_BETS.items():
    for bet_type in bet_types:
        line_key = "total" if bet_type == "totals" else "home_spread" if bet_type == "spreads" else "home_ml"

        script_content = template.format(
            sport=sport,
            bet_type=bet_type,
            line_key=line_key
        )

        filename = f"predict_{sport.lower()}_{bet_type}.py"
        with open(filename, "w") as f:
            f.write(script_content)

        created.append(filename)
        print(f"Created {filename}")

# Create master runner
master_lines = ['#!/usr/bin/env python3',
'import subprocess, sys',
'from pathlib import Path',
'',
'scripts = [']

for script in created:
    master_lines.append(f'    "{script}",')

master_lines.extend([
']',
'',
'print("RUNNING ALL PREDICTIONS")',
'print("="*60)',
'success = 0',
'failed = []',
'',
'for script in scripts:',
'    print(f"Running {script}...")',
'    try:',
'        result = subprocess.run(',
'            [sys.executable, script],',
'            cwd=Path(__file__).parent,',
'            capture_output=True,',
'            text=True,',
'            timeout=30',
'        )',
'        if result.returncode == 0:',
'            success += 1',
'            print(result.stdout)',
'        else:',
'            failed.append(script)',
'            print(f"FAILED: {result.stderr}")',
'    except Exception as e:',
'        failed.append(script)',
'        print(f"ERROR: {e}")',
'',
'print(f"Success: {success}/{len(scripts)}")',
'if failed:',
'    print(f"Failed: {failed}")',
])

with open("run_all_predictions.py", "w") as f:
    f.write('\n'.join(master_lines))

print(f"\nCreated {len(created)} prediction scripts + master script")
print("Run with: python3 run_all_predictions.py")
