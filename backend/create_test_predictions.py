#!/usr/bin/env python3
"""
Create test predictions to demonstrate the Bet column logic
"""
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Create test predictions with different scenarios
test_predictions = []

# Test Case 1: TOTALS - OVER scenario
test_predictions.append({
    'prediction_id': 'TEST_TOTALS_OVER_Lakers_Celtics',
    'date_predicted': datetime.now().isoformat(),
    'game_date': (datetime.now() + timedelta(hours=2)).strftime('%Y-%m-%d'),
    'game_time': '07:00 PM',
    'sport': 'NBA',
    'away_team': 'Los Angeles Lakers',
    'home_team': 'Boston Celtics',
    'bet_type': 'totals',
    'model': 'ensemble',
    'predicted_value': 233.0,  # Prediction HIGHER than line
    'market_value': 228.5,     # Market line
    'edge': 4.5,               # Positive edge
    'recommendation': 'OVER',   # Should show OVER in green
    'confidence': 'HIGH',
    'bet_placed': 'YES'
})

# Test Case 2: TOTALS - UNDER scenario
test_predictions.append({
    'prediction_id': 'TEST_TOTALS_UNDER_Warriors_Suns',
    'date_predicted': datetime.now().isoformat(),
    'game_date': (datetime.now() + timedelta(hours=2)).strftime('%Y-%m-%d'),
    'game_time': '07:30 PM',
    'sport': 'NBA',
    'away_team': 'Golden State Warriors',
    'home_team': 'Phoenix Suns',
    'bet_type': 'totals',
    'model': 'xgboost',
    'predicted_value': 222.0,  # Prediction LOWER than line
    'market_value': 225.5,     # Market line
    'edge': -3.5,              # Negative edge
    'recommendation': 'UNDER',  # Should show UNDER in red
    'confidence': 'MEDIUM',
    'bet_placed': 'YES'
})

# Test Case 3: SPREADS - HOME scenario (favorite covers)
test_predictions.append({
    'prediction_id': 'TEST_SPREADS_HOME_Heat_Bucks',
    'date_predicted': datetime.now().isoformat(),
    'game_date': (datetime.now() + timedelta(hours=3)).strftime('%Y-%m-%d'),
    'game_time': '08:00 PM',
    'sport': 'NBA',
    'away_team': 'Miami Heat',
    'home_team': 'Milwaukee Bucks',
    'bet_type': 'spreads',
    'model': 'random_forest',
    'predicted_value': -8.5,   # Prediction more negative than spread (home wins by more)
    'market_value': -6.5,      # Market spread (home favored by 6.5)
    'edge': -2.0,
    'recommendation': 'HOME',   # Should show HOME in green
    'confidence': 'HIGH',
    'bet_placed': 'YES'
})

# Test Case 4: SPREADS - AWAY scenario (underdog covers)
test_predictions.append({
    'prediction_id': 'TEST_SPREADS_AWAY_Mavs_Nuggets',
    'date_predicted': datetime.now().isoformat(),
    'game_date': (datetime.now() + timedelta(hours=4)).strftime('%Y-%m-%d'),
    'game_time': '09:00 PM',
    'sport': 'NBA',
    'away_team': 'Dallas Mavericks',
    'home_team': 'Denver Nuggets',
    'bet_type': 'spreads',
    'model': 'lightgbm',
    'predicted_value': -3.0,   # Prediction less negative (away keeps it close)
    'market_value': -5.5,      # Market spread (home favored by 5.5)
    'edge': 2.5,
    'recommendation': 'AWAY',   # Should show AWAY in red
    'confidence': 'MEDIUM',
    'bet_placed': 'YES'
})

# Test Case 5: MONEYLINE scenario
test_predictions.append({
    'prediction_id': 'TEST_MONEYLINE_Nets_Knicks',
    'date_predicted': datetime.now().isoformat(),
    'game_date': (datetime.now() + timedelta(hours=3)).strftime('%Y-%m-%d'),
    'game_time': '07:30 PM',
    'sport': 'NBA',
    'away_team': 'Brooklyn Nets',
    'home_team': 'New York Knicks',
    'bet_type': 'moneyline',
    'model': 'ensemble',
    'predicted_value': 0.58,   # 58% win probability
    'market_value': 0.52,      # 52% implied probability
    'edge': 0.06,
    'recommendation': 'HOME',   # Should show HOME in green
    'confidence': 'MEDIUM',
    'bet_placed': 'YES'
})

# Create DataFrame
df = pd.DataFrame(test_predictions)

# Save to predictions log (append mode)
log_path = Path('data/tracking/predictions_log_multi_bet.csv')
log_path.parent.mkdir(parents=True, exist_ok=True)

# Check if file exists
if log_path.exists():
    existing_df = pd.read_csv(log_path)
    # Remove any existing TEST predictions
    existing_df = existing_df[~existing_df['prediction_id'].str.startswith('TEST_')]
    # Append new test predictions
    combined_df = pd.concat([existing_df, df], ignore_index=True)
    combined_df.to_csv(log_path, index=False)
    print(f"[OK] Added {len(df)} test predictions to existing log")
    print(f"  Total predictions: {len(combined_df)}")
else:
    df.to_csv(log_path, index=False)
    print(f"[OK] Created new log with {len(df)} test predictions")

# Print summary
print("\n=== TEST PREDICTIONS CREATED ===")
print("\nYou should now see these on the Edges page:")
print("\n1. Lakers @ Celtics (TOTALS)")
print("   Prediction: 233.0 | Line: 228.5 | Edge: +4.5")
print("   → BET COLUMN SHOULD SHOW: OVER (green)")

print("\n2. Warriors @ Suns (TOTALS)")
print("   Prediction: 222.0 | Line: 225.5 | Edge: -3.5")
print("   → BET COLUMN SHOULD SHOW: UNDER (red)")

print("\n3. Heat @ Bucks (SPREADS)")
print("   Prediction: -8.5 | Spread: -6.5 | Edge: -2.0")
print("   → BET COLUMN SHOULD SHOW: HOME (green) - Bucks cover")

print("\n4. Mavs @ Nuggets (SPREADS)")
print("   Prediction: -3.0 | Spread: -5.5 | Edge: +2.5")
print("   → BET COLUMN SHOULD SHOW: AWAY (red) - Mavs cover")

print("\n5. Nets @ Knicks (MONEYLINE)")
print("   Prediction: 58% | Implied: 52% | Edge: +6%")
print("   → BET COLUMN SHOULD SHOW: HOME (green)")

print("\n" + "="*50)
print("Go to: http://localhost:5174/edges")
print("="*50)
