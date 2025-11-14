#!/usr/bin/env python3
"""
Reconstruct Predictions from Results
Creates matching prediction records from existing graded results
"""
import pandas as pd
from pathlib import Path
from datetime import datetime

TRACKING_DIR = Path("/root/sporttrader/backend/data/tracking")
RESULTS_LOG = TRACKING_DIR / "results_log.csv"
PREDICTIONS_LOG = TRACKING_DIR / "predictions_log_multi_bet.csv"

def main():
    print("="*70)
    print("RECONSTRUCTING PREDICTIONS FROM RESULTS")
    print("="*70)

    # Load results
    results_df = pd.read_csv(RESULTS_LOG)
    print(f"Loaded {len(results_df)} results")

    # Load existing predictions to append to them
    if PREDICTIONS_LOG.exists():
        existing_preds = pd.read_csv(PREDICTIONS_LOG)
        print(f"Loaded {len(existing_preds)} existing predictions")
    else:
        existing_preds = pd.DataFrame()

    # Create predictions from results
    predictions = []

    for _, result in results_df.iterrows():
        # Extract info from prediction_id
        pred_id = result['prediction_id']
        parts = str(pred_id).split('_')

        # Determine format and extract data
        if parts[0] in ['NBA', 'NCAAB', 'NHL', 'NFL', 'NCAAF']:
            # New format
            sport = parts[0]
            bet_type = 'totals' if 'totals' in pred_id.lower() else ('spreads' if 'spreads' in pred_id.lower() else 'moneyline')
            model = parts[-1]
        else:
            # Old format
            sport = 'NBA'  # Default
            bet_type = parts[-2] if len(parts) > 2 else 'totals'
            model = parts[-1] if len(parts) > 1 else 'ensemble'

        # Create prediction record
        pred = {
            'prediction_id': pred_id,
            'date_predicted': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'game_date': result['game_date'],
            'game_time': '07:00 PM',  # Default
            'sport': sport,
            'away_team': result['away_team'],
            'home_team': result['home_team'],
            'bet_type': bet_type,
            'model': model,
            'predicted_value': result.get('predicted_total', 0),
            'market_value': result.get('market_total', 0),
            'edge': result.get('edge_accuracy', 0),
            'recommendation': result['recommendation'],
            'confidence': result['confidence'],
            'bet_placed': 'YES' if result['confidence'] in ['HIGH', 'MEDIUM', 'LOW'] else 'NO'
        }

        predictions.append(pred)

    new_preds_df = pd.DataFrame(predictions)

    # Combine with existing (remove duplicates)
    if len(existing_preds) > 0:
        combined = pd.concat([existing_preds, new_preds_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=['prediction_id'], keep='last')
    else:
        combined = new_preds_df

    # Save
    combined.to_csv(PREDICTIONS_LOG, index=False)

    print(f"\n✅ Reconstructed {len(new_preds_df)} predictions from results")
    print(f"✅ Total predictions in log: {len(combined)}")
    print("="*70)

if __name__ == "__main__":
    main()
