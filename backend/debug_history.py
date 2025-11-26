"""
Debug script to test history endpoint logic
"""
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Load data
RESULTS_LOG = Path(__file__).parent / "data" / "tracking" / "results_log.csv"
merged_df = pd.read_csv(RESULTS_LOG)

print(f"Total rows in results_log.csv: {len(merged_df)}")

# Filter ensemble
model = 'ensemble'
merged_df = merged_df[merged_df['model'].str.lower() == model.lower()]
print(f"After model filter (ensemble): {len(merged_df)}")

# Convert dates
merged_df['game_date_dt'] = pd.to_datetime(merged_df['game_date'], format='mixed', errors='coerce')
print(f"NaT values after date parsing: {merged_df['game_date_dt'].isna().sum()}")

# Filter by date
days = 30
cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
print(f"\nCutoff date for {days} days: {cutoff_date}")
merged_df = merged_df[merged_df['game_date_dt'] >= cutoff_date]
print(f"After date filter (>= cutoff): {len(merged_df)}")

# Group by day
merged_df['date'] = merged_df['game_date_dt'].dt.date

unique_dates = sorted([d for d in merged_df['date'].unique() if pd.notna(d)])
print(f"\nUnique dates found: {len(unique_dates)}")
for date in unique_dates:
    count = len(merged_df[merged_df['date'] == date])
    print(f"  {date}: {count} predictions")

print("\n" + "="*80)
print("Now simulating the history endpoint loop...")
print("="*80)

history_data = []
cumulative_wins = 0
cumulative_total = 0
cumulative_profit = 0

for i, date in enumerate(sorted(merged_df['date'].unique())):
    if pd.isna(date):
        print(f"Skipping NaT date")
        continue

    day_df = merged_df[merged_df['date'] == date]
    day_wins = len(day_df[day_df['result'] == 'WIN'])
    day_losses = len(day_df[day_df['result'] == 'LOSS'])
    day_total = day_wins + day_losses
    day_profit = day_df['profit_loss'].sum() if 'profit_loss' in day_df.columns else 0

    cumulative_wins += day_wins
    cumulative_total += day_total
    cumulative_profit += day_profit

    print(f"\nDate {i+1}: {date}")
    print(f"  Daily: {day_wins}W-{day_losses}L, {len(day_df)} total, {day_profit:.2f} units")
    print(f"  Cumulative: {cumulative_wins}W-{cumulative_total-cumulative_wins}L, {cumulative_profit:.2f} units")

    history_data.append({
        "period": str(date),
        "predictions": len(day_df),
        "wins": day_wins,
        "units_won": round(cumulative_profit, 2)
    })

print(f"\n\nFinal history_data length: {len(history_data)}")
print("History data:")
for entry in history_data:
    print(f"  {entry['period']}: {entry['predictions']} predictions, {entry['units_won']} cumulative units")
