#!/usr/bin/env python3
"""
Train ALL 105 Models from Database - FIXED VERSION
7 model types × 3 bet types × 5 sports = 105 total models
"""
import sqlite3
import pandas as pd
import numpy as np
import joblib
import torch
import torch.nn as nn
from pathlib import Path
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, accuracy_score
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor, CatBoostClassifier
import sys
sys.path.append('/root/sporttrader/backend')
from ml.pytorch_models.tabular_net import TabularNetTrainer
from ml.pytorch_models.ensemble_weighter import EnsembleWeighter
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = '/root/sporttrader/backend/ml/predictions.db'
MODEL_DIR = Path('/root/sporttrader/backend/ml/models')

# Column mappings for each sport
COLUMN_MAPS = {
    'nba': {
        'total': 'actual_total',
        'home_margin': 'home_score - away_score',  # Calculate from scores
        'home_win': 'CASE WHEN home_score > away_score THEN 1 ELSE 0 END'
    },
    'ncaab': {
        'total': 'total',
        'home_margin': 'home_margin',
        'home_win': 'home_win'
    },
    'nhl': {
        'total': 'total',
        'home_margin': 'home_margin',
        'home_win': 'home_win'
    },
    'nfl': {
        'total': 'total',
        'home_margin': 'home_margin',
        'home_win': 'home_win'
    },
    'ncaaf': {
        'total': 'total',
        'home_margin': 'home_margin',
        'home_win': 'home_win'
    }
}

def train_sport_models(sport: str):
    """Train all 21 models for a sport (7 types × 3 bet types)"""
    logger.info('='*70)
    logger.info(f'TRAINING {sport.upper()} - 21 MODELS')
    logger.info('='*70)

    # Load data from database
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f'SELECT * FROM {sport}_training_data', conn)
    conn.close()

    logger.info(f'Loaded {len(df):,} games from database')

    if len(df) < 100:
        logger.warning(f'Not enough data for {sport} (need at least 100 games)')
        return

    # Calculate derived columns if needed for NBA
    if sport == 'nba':
        if 'home_margin' not in df.columns:
            df['home_margin'] = df['home_score'] - df['away_score']
        if 'home_win' not in df.columns:
            df['home_win'] = (df['home_score'] > df['away_score']).astype(int)
        if 'total' not in df.columns and 'actual_total' in df.columns:
            df['total'] = df['actual_total']

    # Get numeric feature columns only
    feature_cols = [c for c in df.columns if ('home_' in c or 'away_' in c)
                    and c not in ['home_score', 'away_score', 'home_win', 'home_margin', 'home_team', 'away_team']
                    and df[c].dtype in ['int64', 'float64']]

    logger.info(f'Using {len(feature_cols)} numeric features')

    # Check for NaN values in features
    X_check = df[feature_cols]
    if X_check.isnull().any().any():
        logger.warning(f'Found NaN values, filling with 0')
        df[feature_cols] = df[feature_cols].fillna(0)

    bet_types = ['totals', 'spreads', 'moneyline']
    models_trained = 0

    for bet_type in bet_types:
        logger.info(f'\nTraining {bet_type}...')

        X = df[feature_cols].values

        # Set target variable
        if bet_type == 'totals':
            if 'total' not in df.columns:
                logger.error(f'{sport} missing total column, skipping totals')
                continue
            y = df['total'].values
            is_classifier = False
        elif bet_type == 'spreads':
            if 'home_margin' not in df.columns:
                logger.error(f'{sport} missing home_margin column, skipping spreads')
                continue
            y = df['home_margin'].values
            is_classifier = False
        else:  # moneyline
            if 'home_win' not in df.columns:
                logger.error(f'{sport} missing home_win column, skipping moneyline')
                continue
            y = df['home_win'].values
            is_classifier = True

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Scale features
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        models = {}
        predictions = {}

        # 1. Random Forest
        logger.info(f'  Training Random Forest...')
        if is_classifier:
            models['random_forest'] = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        else:
            models['random_forest'] = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        models['random_forest'].fit(X_train, y_train)
        predictions['random_forest'] = models['random_forest'].predict(X_test)

        # 2. XGBoost
        logger.info(f'  Training XGBoost...')
        if is_classifier:
            models['xgboost'] = xgb.XGBClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        else:
            models['xgboost'] = xgb.XGBRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        models['xgboost'].fit(X_train, y_train)
        predictions['xgboost'] = models['xgboost'].predict(X_test)

        # 3. LightGBM
        logger.info(f'  Training LightGBM...')
        if is_classifier:
            models['lightgbm'] = lgb.LGBMClassifier(n_estimators=100, random_state=42, n_jobs=-1, verbose=-1)
        else:
            models['lightgbm'] = lgb.LGBMRegressor(n_estimators=100, random_state=42, n_jobs=-1, verbose=-1)
        models['lightgbm'].fit(X_train, y_train)
        predictions['lightgbm'] = models['lightgbm'].predict(X_test)

        # 4. Linear/Logistic Regression
        logger.info(f'  Training Linear/Logistic...')
        if is_classifier:
            models['linear'] = LogisticRegression(random_state=42, max_iter=1000)
        else:
            models['linear'] = LinearRegression()
        models['linear'].fit(X_train, y_train)
        predictions['linear'] = models['linear'].predict(X_test)

        # 5. CatBoost
        logger.info(f'  Training CatBoost...')
        if is_classifier:
            models['catboost'] = CatBoostClassifier(iterations=100, random_state=42, verbose=0)
        else:
            models['catboost'] = CatBoostRegressor(iterations=100, random_state=42, verbose=0)
        models['catboost'].fit(X_train, y_train)
        predictions['catboost'] = models['catboost'].predict(X_test)

        # 6. PyTorch TabularNet
        logger.info(f'  Training PyTorch...')
        pytorch_trainer = TabularNetTrainer(input_dim=X_train.shape[1])
        pytorch_model = pytorch_trainer.train(X_train, y_train, epochs=50)
        predictions['pytorch'] = pytorch_trainer.predict(X_test)
        models['pytorch'] = pytorch_model

        # 7. Neural Ensemble
        logger.info(f'  Training Ensemble...')
        base_preds = np.column_stack([predictions['random_forest'], predictions['xgboost'],
                                      predictions['lightgbm'], predictions['linear'],
                                      predictions['catboost'], predictions['pytorch']])

        ensemble = EnsembleWeighter(input_dim=X_train.shape[1], n_models=6)
        optimizer = torch.optim.Adam(ensemble.parameters(), lr=0.001)

        X_tensor = torch.FloatTensor(X_train)
        y_tensor = torch.FloatTensor(y_train).unsqueeze(1) if not is_classifier else torch.LongTensor(y_train)

        n_models = base_preds.shape[1]
        model_accs = torch.ones_like(X_tensor) / n_models

        for epoch in range(50):
            optimizer.zero_grad()
            preds, _ = ensemble(X_tensor, model_accs)

            if is_classifier:
                loss = nn.CrossEntropyLoss()(preds, y_tensor)
            else:
                loss = nn.MSELoss()(preds, y_tensor)

            loss.backward()
            optimizer.step()

        models['ensemble'] = ensemble

        with torch.no_grad():
            X_test_tensor = torch.FloatTensor(X_test)
            test_model_accs = torch.ones_like(X_test_tensor) / n_models
            ensemble_preds, _ = ensemble(X_test_tensor, test_model_accs)
            predictions['ensemble'] = ensemble_preds.numpy()

        # Calculate metrics
        for model_name, pred in predictions.items():
            if is_classifier:
                pred_binary = (pred > 0.5).astype(int) if model_name == 'ensemble' else pred
                acc = accuracy_score(y_test, pred_binary)
                logger.info(f'  {model_name}: Accuracy = {acc:.3f}')
            else:
                mae = mean_absolute_error(y_test, pred)
                logger.info(f'  {model_name}: MAE = {mae:.2f}')

        # Save models
        logger.info(f'  Saving models...')

        # Save sklearn/xgboost/lightgbm/catboost models
        for model_type in ['random_forest', 'xgboost', 'lightgbm', 'linear', 'catboost']:
            filename = f'{sport}_{model_type}_{bet_type}_enhanced.joblib'
            joblib.dump(models[model_type], MODEL_DIR / filename)
            models_trained += 1

        # Save PyTorch model
        pytorch_filename = f'{sport}_pytorch_{bet_type}_latest.pt'
        torch.save(models['pytorch'], MODEL_DIR / pytorch_filename)
        models_trained += 1

        # Save Ensemble model
        ensemble_filename = f'{sport}_ensemble_{bet_type}_latest.pt'
        torch.save(models['ensemble'], MODEL_DIR / ensemble_filename)
        models_trained += 1

        # Save scaler
        scaler_filename = f'{sport}_scaler_{bet_type}_enhanced.joblib'
        joblib.dump(scaler, MODEL_DIR / scaler_filename)

    logger.info(f'\n{sport.upper()} COMPLETE: Trained {models_trained} models')
    return models_trained

def main():
    logger.info('\n')
    logger.info('='*70)
    logger.info('TRAINING ALL 105 MODELS FROM DATABASE')
    logger.info('7 model types × 3 bet types × 5 sports = 105 total models')
    logger.info('='*70)
    logger.info('\n')

    sports = ['nba', 'ncaab', 'nhl', 'nfl', 'ncaaf']
    total_trained = 0

    for sport in sports:
        try:
            count = train_sport_models(sport)
            total_trained += count if count else 0
        except Exception as e:
            logger.error(f'Error training {sport}: {e}')
            import traceback
            traceback.print_exc()

    logger.info('\n')
    logger.info('='*70)
    logger.info('TRAINING COMPLETE')
    logger.info('='*70)

    # Count models in directory
    model_counts = {}
    for sport in sports:
        count = len(list(MODEL_DIR.glob(f'{sport}_*enhanced*.joblib'))) + \
                len(list(MODEL_DIR.glob(f'{sport}_*latest.pt')))
        model_counts[sport] = count
        logger.info(f'{sport.upper()}: {count} models')

    total_models = sum(model_counts.values())
    logger.info(f'\nTOTAL MODELS: {total_models}')
    logger.info(f'Expected: 105 (21 per sport × 5 sports)')

if __name__ == '__main__':
    main()
