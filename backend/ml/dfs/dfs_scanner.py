# backend/ml/dfs/dfs_scanner.py
import json
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Any
from pathlib import Path

# Your sacred player prop predictor (already exists)
from ml.props.predictor import generate_single_prop_prediction

DB_PATH = "ml/predictions.db"
STATIC_PATH = Path("frontend/public/static")

# 8 DFS platforms we crush
DFS_SITES = {
    "PrizePicks": {"scraper": "prizepicks", "payouts": {2: 3, 3: 5, 4: 10, 5: 20, 6: 25}},
    "Underdog":    {"scraper": "underdog",    "payouts": {2: 3, 3: 6, 4: 10, 5: 20}},
    "Fliff":       {"scraper": "fliff",       "payouts": {2: 3, 3: 5, 4: 10, 5: 20}},
    "Sleeper":     {"scraper": "sleeper",     "payouts": {2: 3, 3: 5, 4: 10, 5: 20}},
    "ParlayPlay":  {"scraper": "parlayplay",  "payouts": {2: 3, 3: 5, 4: 10, 5: 20}},
    "Betr Picks":  {"scraper": "betr",        "payouts": {2: 3, 3: 6, 4: 12, 5: 25}},
    "Chalkboard":  {"scraper": "chalkboard",  "payouts": {2: 3, 3: 5, 4: 10}},
    "Dabble":      {"scraper": "dabble",      "payouts": {2: 3, 3: 5, 4: 10, 5: 20}},
}

def get_dfs_lines(site: str) -> List[Dict]:
    """Placeholder — replace with your real scrapers"""
    # In real version: call your playwright/headless scrapers
    # For now, return mock or load from cache
    cache_file = Path(f"backend/ml/dfs/cache/{site.lower()}_{date.today()}.json")
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    return []

def calculate_ev(true_prob: float, payout: float) -> float:
    return (true_prob * payout) - 1.0

def run_dfs_scanner():
    print(f"[{datetime.now()}] DFS Crusher scanning 8 platforms...")
    results = []

    for site_name, config in DFS_SITES.items():
        lines = get_dfs_lines(site_name)
        for line in lines:
            player = line['player_name']
            stat = line['stat_type']
            market_line = line['line']
            direction = line.get('direction', 'Higher')  # or 'Lower'

            # Run through your sacred 7-model prop ensemble
            pred = generate_single_prop_prediction(player, stat, market_line)
            if not pred or pred['confidence'] < 0.65:
                continue

            true_prob = pred['over_probability'] if direction == "Higher" else pred['under_probability']
            edge = pred['edge']

            # Only show +EV demons
            if edge < 5.0:
                continue

            payout = config['payouts'].get(line.get('legs', 2), 3)
            ev = calculate_ev(true_prob, payout)

            if ev < 0.15:  # 15%+ EV only
                continue

            results.append({
                "site": site_name,
                "bestPlay": f"{player} {stat} {direction} {market_line}",
                "trueWinRate": f"{true_prob:.1%}",
                "payout": f"{payout}x",
                "ev": f"+{ev:.0%}",
                "demonScore": int(edge * 2),  # visual intensity
                "entriesToday": len(lines),
                "logo": site_name.lower().replace(" ", ""),
                "gradient": {
                    "PrizePicks": "from-amber-700 via-orange-800 to-black border-amber-600",
                    "Underdog": "from-purple-700 via-pink-800 to-black border-purple-600",
                    "Fliff": "from-red-800 via-black to-black border-red-700",
                    "Sleeper": "from-blue-cyan-700 via-blue-800 to-black border-cyan-600",
                }.get(site_name, "from-gray-700 to-black border-gray-600")
            })

    # Sort by EV descending
    results = sorted(results, key=lambda x: float(x['ev'].strip('+ %')), reverse=True)[:24]

    # Save for frontend
    output = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_demons": len(results),
        "platforms": list({r['site'] for r in results}),
        "plays": results
    }

    # 1. Save to static JSON (instant frontend load)
    STATIC_PATH.mkdir(parents=True, exist_ok=True)
    with open(STATIC_PATH / "dfs_crusher.json", "w") as f:
        json.dump(output, f, indent=2)

    # 2. Save to DB (optional backup)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS dfs_crusher_daily (date TEXT PRIMARY KEY, data TEXT)")
    conn.execute("INSERT OR REPLACE INTO dfs_crusher_daily VALUES (?, ?)",
                 (date.today().isoformat(), json.dumps(output)))
    conn.commit()
    conn.close()

    print(f"[{datetime.now()}] DFS Crusher complete — {len(results)} demons found!")
    return output