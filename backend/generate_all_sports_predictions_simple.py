"""
Generate sample predictions for ALL sports
Adds them to predictions_log.csv for the Max EV Edges page
"""
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import random

# Sample matchups for each sport
sample_games = {
    'NBA': [
        ('Los Angeles Lakers', 'Boston Celtics', 228.5),
        ('Golden State Warriors', 'Phoenix Suns', 225.5),
        ('Miami Heat', 'Milwaukee Bucks', 221.0),
        ('Dallas Mavericks', 'Denver Nuggets', 230.0),
    ],
    'NCAAB': [
        ('Duke', 'North Carolina', 145.5),
        ('Kansas', 'Kentucky', 152.0),
        ('Gonzaga', 'UCLA', 148.5),
        ('Villanova', 'Georgetown', 141.0),
    ],
    'NFL': [
        ('Kansas City Chiefs', 'Buffalo Bills', 52.5),
        ('Philadelphia Eagles', 'Dallas Cowboys', 48.5),
        ('San Francisco 49ers', 'Seattle Seahawks', 45.0),
    ],
    'NCAAF': [
        ('Alabama', 'Georgia', 56.5),
        ('Ohio State', 'Michigan', 54.0),
        ('Clemson', 'Florida State', 51.5),
    ],
    'NHL': [
        ('Toronto Maple Leafs', 'Montreal Canadiens', 6.5),
        ('Boston Bruins', 'New York Rangers', 6.0),
        ('Colorado Avalanche', 'Vegas Golden Knights', 6.5),
    ]
}

predictions = []
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
game_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

for sport, games in sample_games.items():
    print(f"\n[{sport}] Generating predictions...")

    for away_team, home_team, market_total in games:
        # Generate predicted total with variance
        predicted_total = market_total + random.uniform(-10, 10)
        edge = predicted_total - market_total

        # Determine confidence
        if abs(edge) >= 5.0:
            confidence = 'HIGH'
            bet_placed = 'YES'
        elif abs(edge) >= 3.0:
            confidence = 'MEDIUM'
            bet_placed = 'YES'
        elif abs(edge) >= 2.0:
            confidence = 'LOW'
            bet_placed = 'YES'
        else:
            confidence = 'NONE'
            bet_placed = 'NO'

        recommendation = 'OVER' if edge > 0 else 'UNDER'
        game_time = f"{random.choice(['07:00', '07:30', '08:00', '10:00'])} PM"
        pred_id = f"{sport}_{game_date.replace('-', '')}_{away_team.replace(' ', '_')}_{home_team.replace(' ', '_')}"

        predictions.append({
            'prediction_id': pred_id,
            'date_predicted': timestamp,
            'game_date': game_date,
            'game_time': game_time,
            'away_team': away_team,
            'home_team': home_team,
            'predicted_total': round(predicted_total, 1),
            'market_total': market_total,
            'edge': round(edge, 1),
            'recommendation': recommendation,
            'confidence': confidence,
            'bet_placed': bet_placed
        })

        print(f"  {away_team} @ {home_team}: Edge = {edge:+.1f} ({confidence})")

# Save to predictions_log.csv
tracking_dir = Path(__file__).parent / "data" / "tracking"
tracking_dir.mkdir(parents=True, exist_ok=True)
tracking_file = tracking_dir / "predictions_log.csv"

# Load existing if exists
if tracking_file.exists():
    existing = pd.read_csv(tracking_file)
    existing['game_date'] = pd.to_datetime(existing['game_date'])
    today = pd.Timestamp.now().normalize()
    existing = existing[existing['game_date'] >= today]
else:
    existing = pd.DataFrame()

# Combine and save
new_df = pd.DataFrame(predictions)
combined = pd.concat([existing, new_df], ignore_index=True)
combined = combined.drop_duplicates(subset=['prediction_id'], keep='last')
combined.to_csv(tracking_file, index=False)

print(f"\n[OK] Generated {len(predictions)} predictions across 5 sports")
print(f"[OK] Saved to {tracking_file}")
print(f"[OK] Total predictions: {len(combined)}")

# Breakdown
for sport in ['NBA', 'NCAAB', 'NFL', 'NCAAF', 'NHL']:
    count = len([p for p in predictions if p['prediction_id'].startswith(sport)])
    print(f"  {sport}: {count} predictions")
