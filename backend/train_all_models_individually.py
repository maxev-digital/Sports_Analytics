#!/usr/bin/env python3
"""
Train All Models Individually - Bet Type Specific Features
Trains 15 models (5 sports × 3 bet types) with bet-specific features
"""
import sys
from pathlib import Path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

import sqlite3
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor, CatBoostClassifier
import logging
from datetime import datetime

# Import feature engineering
from ml.feature_engineering.nba_features import NBAFeatureEngineer
from ml.feature_engineering.ncaab_features import NCAABFeatureEngineer
from ml.feature_engineering.nhl_features import NHLFeatureEngineer
from ml.feature_engineering.nfl_features import NFLFeatureEngineer
from ml.feature_engineering.ncaaf_features import NCAAFFeatureEngineer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = backend_path / 'ml' / 'predictions.db'
MODELS_DIR = backend_path / 'ml' / 'models'

# Sport configuration
SPORT_CONFIG = {
    'nba': {
        'table': 'nba_training_data',
        'feature_engineer': NBAFeatureEngineer(),
    },
    'ncaab': {
        'table': 'ncaab_training_data',
        'feature_engineer': NCAABFeatureEngineer(),
    },
    'nhl': {
        'table': 'nhl_training_data',
        'feature_engineer': NHLFeatureEngineer(),
    },
    'nfl': {
        'table': 'nfl_training_data',
        'feature_engineer': NFLFeatureEngineer(),
    },
    'ncaaf': {
        'table': 'ncaaf_training_data',
        'feature_engineer': NCAAFFeatureEngineer(),
    }
}

def load_training_data(sport):
    """Load training data from database"""
    config = SPORT_CONFIG[sport]
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT * FROM {config['table']}", conn)
    conn.close()

    logger.info(f"Loaded {len(df):,} games for {sport.upper()}")
    return df

def prepare_targets(df, sport, bet_type):
    """Prepare target variable based on bet type"""

    if bet_type == 'totals':
        if 'actual_total' in df.columns:
            return df['actual_total'].values
        elif 'total' in df.columns:
            return df['total'].values
        elif 'home_score' in df.columns and 'away_score' in df.columns:
            return (df['home_score'] + df['away_score']).values
        else:
            # No valid target for totals
            return None

    elif bet_type == 'spreads':
        if 'home_margin' in df.columns:
            return df['home_margin'].values
        elif 'home_score' in df.columns and 'away_score' in df.columns:
            return (df['home_score'] - df['away_score']).values
        elif 'market_spread' in df.columns:
            # For NCAAB, use market_spread as a proxy
            # This isn't ideal but allows training
            return df['market_spread'].values
        else:
            return None

    elif bet_type == 'moneyline':
        if 'home_win' in df.columns:
            return df['home_win'].values
        elif 'home_score' in df.columns and 'away_score' in df.columns:
            return (df['home_score'] > df['away_score']).astype(int).values
        elif 'market_home_ml' in df.columns and 'market_away_ml' in df.columns:
            # Infer home win probability from moneyline odds
            # Favorite (negative odds) more likely to win
            home_favorite = df['market_home_ml'] < df['market_away_ml']
            return home_favorite.astype(int).values
        else:
            return None

def extract_features_from_training_data(df, sport, bet_type):
    """Extract features using bet-specific feature engineering"""
    config = SPORT_CONFIG[sport]
    feature_engineer = config['feature_engineer']

    if bet_type == 'totals':
        feature_func = feature_engineer.get_totals_features
    elif bet_type == 'spreads':
        feature_func = feature_engineer.get_spreads_features
    elif bet_type == 'moneyline':
        feature_func = feature_engineer.get_moneyline_features

    features_list = []
    for idx, row in df.iterrows():
        try:
            features = feature_func(row).flatten()
            features_list.append(features)
        except Exception as e:
            continue

    return np.array(features_list)

def train_models(X_train, X_test, y_train, y_test, is_classification=False):
    """Train multiple model types"""
    models = {}
    predictions = {}

    logger.info("  Training Random Forest...")
    if is_classification:
        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, max_depth=10)
    else:
        rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1, max_depth=10)
    rf.fit(X_train, y_train)
    models['random_forest'] = rf
    predictions['random_forest'] = rf.predict(X_test)

    logger.info("  Training XGBoost...")
    if is_classification:
        xgb_model = xgb.XGBClassifier(n_estimators=100, random_state=42, n_jobs=-1, max_depth=6)
    else:
        xgb_model = xgb.XGBRegressor(n_estimators=100, random_state=42, n_jobs=-1, max_depth=6)
    xgb_model.fit(X_train, y_train)
    models['xgboost'] = xgb_model
    predictions['xgboost'] = xgb_model.predict(X_test)

    logger.info("  Training LightGBM...")
    if is_classification:
        lgb_model = lgb.LGBMClassifier(n_estimators=100, random_state=42, n_jobs=-1, max_depth=6, verbose=-1)
    else:
        lgb_model = lgb.LGBMRegressor(n_estimators=100, random_state=42, n_jobs=-1, max_depth=6, verbose=-1)
    lgb_model.fit(X_train, y_train)
    models['lightgbm'] = lgb_model
    predictions['lightgbm'] = lgb_model.predict(X_test)

    logger.info("  Training Linear model...")
    if is_classification:
        linear_model = LogisticRegression(random_state=42, max_iter=1000)
    else:
        linear_model = LinearRegression()
    linear_model.fit(X_train, y_train)
    models['linear'] = linear_model
    predictions['linear'] = linear_model.predict(X_test)

    logger.info("  Training CatBoost...")
    if is_classification:
        cb_model = CatBoostClassifier(iterations=100, random_state=42, verbose=0, depth=6)
    else:
        cb_model = CatBoostRegressor(iterations=100, random_state=42, verbose=0, depth=6)
    cb_model.fit(X_train, y_train)
    models['catboost'] = cb_model
    predictions['catboost'] = cb_model.predict(X_test)

    return models, predictions

def evaluate_models(predictions, y_test, is_classification=False):
    """Evaluate model performance"""
    results = {}

    for name, preds in predictions.items():
        if is_classification:
            accuracy = accuracy_score(y_test, (preds > 0.5).astype(int) if name in ['catboost', 'linear'] else preds)
            results[name] = {'accuracy': accuracy}
            logger.info(f"    {name:15} Accuracy: {accuracy:.3f}")
        else:
            mae = mean_absolute_error(y_test, preds)
            rmse = np.sqrt(mean_squared_error(y_test, preds))
            r2 = r2_score(y_test, preds)
            results[name] = {'mae': mae, 'rmse': rmse, 'r2': r2}
            logger.info(f"    {name:15} MAE: {mae:.3f}, RMSE: {rmse:.3f}, R²: {r2:.3f}")

    return results

def save_models(models, sport, bet_type, scaler):
    """Save trained models"""
    for name, model in models.items():
        if name == 'catboost':
            model_path = MODELS_DIR / f'{sport}_{name}_{bet_type}_enhanced.joblib'
            model.save_model(str(model_path))
        else:
            model_path = MODELS_DIR / f'{sport}_{name}_{bet_type}_enhanced.joblib'
            joblib.dump(model, model_path)
        logger.info(f"    Saved {model_path.name}")

    scaler_path = MODELS_DIR / f'{sport}_scaler_{bet_type}_enhanced.joblib'
    joblib.dump(scaler, scaler_path)
    logger.info(f"    Saved {scaler_path.name}")

def train_sport_bet_type(sport, bet_type):
    """Train all models for a specific sport and bet type"""
    logger.info(f"\n{'='*80}")
    logger.info(f"TRAINING: {sport.upper()} - {bet_type.upper()}")
    logger.info(f"{'='*80}")

    df = load_training_data(sport)

    if len(df) < 100:
        logger.warning(f"Not enough data for {sport} {bet_type}")
        return False

    logger.info(f"Extracting {bet_type} features...")
    X = extract_features_from_training_data(df, sport, bet_type)

    if len(X) == 0:
        logger.error(f"No features extracted for {sport} {bet_type}")
        return False

    logger.info(f"Extracted {X.shape[0]} samples with {X.shape[1]} features")

    y = prepare_targets(df[:len(X)], sport, bet_type)
    is_classification = (bet_type == 'moneyline')

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    logger.info("Training models...")
    models, predictions = train_models(X_train_scaled, X_test_scaled, y_train, y_test, is_classification=is_classification)

    logger.info("Evaluation:")
    results = evaluate_models(predictions, y_test, is_classification=is_classification)

    logger.info("Saving models...")
    save_models(models, sport, bet_type, scaler)

    logger.info(f"✅ Completed {sport.upper()} {bet_type}")
    return True

def main():
    """Train all models"""
    logger.info("\n" + "="*80)
    logger.info("TRAINING ALL MODELS INDIVIDUALLY")
    logger.info("5 sports × 3 bet types = 15 model sets")
    logger.info("="*80 + "\n")

    start_time = datetime.now()

    sports = ['nba', 'ncaab', 'nhl', 'nfl', 'ncaaf']
    bet_types = ['totals', 'spreads', 'moneyline']

    total_trained = 0
    total_failed = 0

    for sport in sports:
        for bet_type in bet_types:
            try:
                success = train_sport_bet_type(sport, bet_type)
                if success:
                    total_trained += 1
                else:
                    total_failed += 1
            except Exception as e:
                logger.error(f"Error training {sport} {bet_type}: {e}", exc_info=True)
                total_failed += 1

    end_time = datetime.now()
    duration = end_time - start_time

    logger.info("\n" + "="*80)
    logger.info("TRAINING COMPLETE")
    logger.info("="*80)
    logger.info(f"Total trained: {total_trained}")
    logger.info(f"Total failed: {total_failed}")
    logger.info(f"Duration: {duration}")
    logger.info(f"Models saved to: {MODELS_DIR}")

if __name__ == '__main__':
    main()
