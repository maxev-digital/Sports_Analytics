#!/usr/bin/env python3
"""
Fix missing market_total and predicted_total values in results_log.csv
by merging with predictions_log_multi_bet.csv
"""
import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File paths
DATA_DIR = Path(__file__).parent / 'data' / 'tracking'
PREDICTIONS_LOG = DATA_DIR / 'predictions_log_multi_bet.csv'
RESULTS_LOG = DATA_DIR / 'results_log.csv'
RESULTS_BACKUP = DATA_DIR / 'results_log_backup_before_fix.csv'

def main():
    logger.info("="*80)
    logger.info("FIXING MISSING PREDICTION VALUES IN RESULTS_LOG")
    logger.info("="*80)

    # Load both files
    logger.info(f"Loading predictions from {PREDICTIONS_LOG}")
    predictions_df = pd.read_csv(PREDICTIONS_LOG)

    logger.info(f"Loading results from {RESULTS_LOG}")
    results_df = pd.read_csv(RESULTS_LOG)

    # Backup original results_log
    logger.info(f"Creating backup at {RESULTS_BACKUP}")
    results_df.to_csv(RESULTS_BACKUP, index=False)

    # Count how many rows are missing these values
    missing_market = results_df['market_total'].isna().sum()
    missing_predicted = results_df['predicted_total'].isna().sum()
    logger.info(f"Rows missing market_total: {missing_market}")
    logger.info(f"Rows missing predicted_total: {missing_predicted}")

    if missing_market == 0 and missing_predicted == 0:
        logger.info("No missing values found! Nothing to fix.")
        return

    # Merge with predictions to get missing values
    # Use prediction_id as the key
    logger.info("Merging with predictions data...")

    # Select only needed columns from predictions
    pred_cols = ['prediction_id', 'predicted_total', 'market_total', 'predicted_value', 'market_value']
    predictions_subset = predictions_df[pred_cols].copy()

    # Create combined columns with fallback logic
    predictions_subset['pred_total_final'] = predictions_subset['predicted_value'].fillna(predictions_subset['predicted_total'])
    predictions_subset['market_total_final'] = predictions_subset['market_value'].fillna(predictions_subset['market_total'])

    # Merge
    results_merged = results_df.merge(
        predictions_subset[['prediction_id', 'pred_total_final', 'market_total_final']],
        on='prediction_id',
        how='left',
        suffixes=('', '_from_pred')
    )

    # Update missing values
    mask_market = results_merged['market_total'].isna()
    mask_predicted = results_merged['predicted_total'].isna()

    updated_market = mask_market.sum()
    updated_predicted = mask_predicted.sum()

    results_merged.loc[mask_market, 'market_total'] = results_merged.loc[mask_market, 'market_total_final']
    results_merged.loc[mask_predicted, 'predicted_total'] = results_merged.loc[mask_predicted, 'pred_total_final']

    # Drop temporary columns
    results_merged = results_merged.drop(columns=['pred_total_final', 'market_total_final'])

    logger.info(f"Updated {updated_market} market_total values")
    logger.info(f"Updated {updated_predicted} predicted_total values")

    # Save updated results
    logger.info(f"Saving updated results to {RESULTS_LOG}")
    results_merged.to_csv(RESULTS_LOG, index=False)

    # Verify
    remaining_missing_market = results_merged['market_total'].isna().sum()
    remaining_missing_predicted = results_merged['predicted_total'].isna().sum()
    logger.info(f"Remaining rows with missing market_total: {remaining_missing_market}")
    logger.info(f"Remaining rows with missing predicted_total: {remaining_missing_predicted}")

    logger.info("="*80)
    logger.info("FIX COMPLETE")
    logger.info("="*80)

if __name__ == '__main__':
    main()
