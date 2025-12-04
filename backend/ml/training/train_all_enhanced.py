"""
ALL SPORTS ENHANCED Model Training - 78 Features + 7 Model Types
Unified enhanced trainer for NBA, NCAAB, NCAAF, NFL, NHL

Usage:
    python -m backend.ml.training.train_all_enhanced --sport nba --seasons 2023 2024 2025
    python -m backend.ml.training.train_all_enhanced --sport ncaab
    python -m backend.ml.training.train_all_enhanced --sport nhl
"""

import argparse
import joblib
import logging
import numpy as np
import pandas as pd
import torch
from pathlib import Path
from datetime import datetime
from typing import Dict
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

try:
    import xgboost as xgb
except ImportError:
    xgb = None

try:
    import lightgbm as lgb
except ImportError:
    lgb = None

try:
    import catboost as cb
except ImportError:
    cb = None

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import data loaders for all sports
from ml.data_loaders.nba_data_loader import load_nba_training_data
from ml.data_loaders.ncaab_data_loader import load_ncaab_training_data
from ml.data_loaders.nhl_data_loader import load_nhl_training_data
from ml.data_loaders.nfl_data_loader import load_nfl_training_data
from ml.data_loaders.ncaaf_data_loader import load_ncaaf_training_data

# Import feature engineers for all sports
from ml.feature_engineering.nba_features import NBAFeatureEngineer
from ml.feature_engineering.ncaab_features import NCAABFeatureEngineer
from ml.feature_engineering.nhl_features import NHLFeatureEngineer
from ml.feature_engineering.nfl_features import NFLFeatureEngineer
from ml.feature_engineering.ncaaf_features import NCAAFFeatureEngineer

# Import enhanced components
from ml.pytorch_models.tabular_net import TabularNet, TabularNetTrainer
from ml.pytorch_models.ensemble_weighter import EnsembleWeighter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Configuration flags
USE_ENHANCED_PIPELINE = True
USE_NEURAL_ENSEMBLE = True


# Sport-specific enhanced feature definitions
ENHANCED_FEATURES_BY_SPORT = {
    'nba': {
        'home_rest_days': 2, 'away_rest_days': 2,
        'rest_advantage': 0, 'home_b2b': 0, 'away_b2b': 0,
        'home_travel_miles_7d': 0, 'away_travel_miles_7d': 500,
        'travel_fatigue_index': 0.5, 'timezone_changes': 0,
        'home_clutch_rating': 0.5, 'away_clutch_rating': 0.5,
        'home_injury_score': 0, 'away_injury_score': 0,
        'home_stars_out': 0, 'away_stars_out': 0,
        'home_lineup_stability': 0.7, 'away_lineup_stability': 0.7,
        'h2h_home_win_pct': 0.5, 'h2h_avg_total': 220,
        'h2h_avg_spread': 0, 'h2h_home_cover_pct': 0.5,
        'ref_ou_tendency': 0, 'ref_foul_rate': 0,
        'home_expected_fg_pct': 0.46, 'away_expected_fg_pct': 0.46,
    },
    'ncaab': {
        'home_rest_days': 3, 'away_rest_days': 3,
        'rest_advantage': 0, 'home_b2b': 0, 'away_b2b': 0,
        'home_travel_miles_7d': 0, 'away_travel_miles_7d': 300,
        'travel_fatigue_index': 0.3, 'conference_game': 0,
        'home_kenpom_luck': 0, 'away_kenpom_luck': 0,
        'home_sos': 0, 'away_sos': 0,
        'home_injury_score': 0, 'away_injury_score': 0,
        'h2h_home_win_pct': 0.5, 'h2h_avg_total': 145,
        'h2h_avg_spread': 0, 'tournament_game': 0,
        'neutral_site': 0, 'rivalry_game': 0,
        'home_3pt_pct_last5': 0.33, 'away_3pt_pct_last5': 0.33,
    },
    'nhl': {
        'home_rest_days': 2, 'away_rest_days': 2,
        'rest_advantage': 0, 'home_b2b': 0, 'away_b2b': 0,
        'home_travel_miles_7d': 0, 'away_travel_miles_7d': 400,
        'travel_fatigue_index': 0.4, 'timezone_changes': 0,
        'home_goalie_sv_pct': 0.91, 'away_goalie_sv_pct': 0.91,
        'home_goalie_gaa': 2.8, 'away_goalie_gaa': 2.8,
        'home_pp_pct': 0.20, 'away_pp_pct': 0.20,
        'home_pk_pct': 0.80, 'away_pk_pct': 0.80,
        'home_corsi': 50, 'away_corsi': 50,
        'home_fenwick': 50, 'away_fenwick': 50,
        'h2h_home_win_pct': 0.5, 'h2h_avg_total': 5.5,
        'empty_net_frequency': 0.1, 'goalie_pull_time': 0,
    },
    'nfl': {
        'home_rest_days': 7, 'away_rest_days': 7,
        'rest_advantage': 0, 'short_week': 0, 'bye_week_boost': 0,
        'home_travel_miles': 0, 'away_travel_miles': 500,
        'travel_fatigue_index': 0.2, 'timezone_changes': 0,
        'home_injury_score': 0, 'away_injury_score': 0,
        'home_qb_rating': 90, 'away_qb_rating': 90,
        'home_rushing_rank': 16, 'away_rushing_rank': 16,
        'home_pass_def_rank': 16, 'away_pass_def_rank': 16,
        'home_redzone_pct': 0.55, 'away_redzone_pct': 0.55,
        'home_turnover_diff': 0, 'away_turnover_diff': 0,
        'h2h_home_win_pct': 0.5, 'h2h_avg_total': 45,
        'divisional_game': 0, 'primetime_game': 0,
        'weather_factor': 0, 'dome_game': 0,
    },
    'ncaaf': {
        'home_rest_days': 7, 'away_rest_days': 7,
        'rest_advantage': 0, 'bye_week_boost': 0,
        'home_travel_miles': 0, 'away_travel_miles': 400,
        'travel_fatigue_index': 0.25, 'conference_game': 0,
        'home_sp_plus': 0, 'away_sp_plus': 0,
        'home_fpi': 0, 'away_fpi': 0,
        'home_injury_score': 0, 'away_injury_score': 0,
        'home_recruiting_rank': 50, 'away_recruiting_rank': 50,
        'home_returning_production': 0.5, 'away_returning_production': 0.5,
        'h2h_home_win_pct': 0.5, 'h2h_avg_total': 55,
        'rivalry_game': 0, 'ranked_matchup': 0,
        'weather_factor': 0, 'altitude_factor': 0,
    },
}


def add_enhanced_features_generic(df: pd.DataFrame, sport: str) -> pd.DataFrame:
    """Add enhanced features based on sport type"""
    logger.info(f"Adding enhanced features for {sport.upper()}")

    defaults = ENHANCED_FEATURES_BY_SPORT.get(sport, ENHANCED_FEATURES_BY_SPORT['nba'])

    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    # Calculate derived features (common across sports)
    if 'home_rest_days' in df.columns and 'away_rest_days' in df.columns:
        df['rest_advantage'] = np.clip(df['home_rest_days'] - df['away_rest_days'], -4, 4)
        df['home_b2b'] = (df['home_rest_days'] == 0).astype(int) if sport in ['nba', 'nhl'] else 0
        df['away_b2b'] = (df['away_rest_days'] == 0).astype(int) if sport in ['nba', 'nhl'] else 0

    if 'home_travel_miles_7d' in df.columns and 'away_travel_miles_7d' in df.columns:
        df['travel_fatigue_index'] = (df['away_travel_miles_7d'] - df['home_travel_miles_7d']) / 1000
    elif 'home_travel_miles' in df.columns and 'away_travel_miles' in df.columns:
        df['travel_fatigue_index'] = (df['away_travel_miles'] - df['home_travel_miles']) / 1000

    if 'home_injury_score' in df.columns and 'away_injury_score' in df.columns:
        df['injury_advantage'] = df['away_injury_score'] - df['home_injury_score']

    logger.info(f"Enhanced features added. Total columns: {len(df.columns)}")
    return df.fillna(0)


class EnhancedModelTrainer:
    """Universal enhanced trainer for all 5 sports - 7 model types"""

    def __init__(self, sport: str, output_dir: Path = None):
        self.sport = sport.lower()
        self.output_dir = output_dir or Path(__file__).parent.parent / "models"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.scaler = StandardScaler()

        # Get sport-specific feature engineer
        self.feature_engineer = self._get_feature_engineer()

    def _get_feature_engineer(self):
        """Return the appropriate feature engineer for the sport"""
        engineers = {
            'nba': NBAFeatureEngineer,
            'ncaab': NCAABFeatureEngineer,
            'nhl': NHLFeatureEngineer,
            'nfl': NFLFeatureEngineer,
            'ncaaf': NCAAFFeatureEngineer,
        }
        return engineers.get(self.sport, NBAFeatureEngineer)()

    def create_enhanced_feature_matrix(self, df: pd.DataFrame, bet_type: str) -> np.ndarray:
        """Create enhanced feature matrix combining base + sport-specific enhanced features"""
        if USE_ENHANCED_PIPELINE:
            # Add enhanced columns to dataframe
            df = add_enhanced_features_generic(df, self.sport)

            # Get base features from sport-specific engineer
            base_X = self.feature_engineer.create_feature_matrix(df, bet_type)

            # Get enhanced feature columns
            enhanced_cols = list(ENHANCED_FEATURES_BY_SPORT.get(self.sport, {}).keys())
            enhanced_X = df[enhanced_cols].values if all(c in df.columns for c in enhanced_cols) else np.zeros((len(df), len(enhanced_cols)))

            # Combine features
            X = np.hstack([base_X, enhanced_X])
            logger.info(f"Created {self.sport.upper()} enhanced feature matrix: {X.shape}")
            return X
        else:
            return self.feature_engineer.create_feature_matrix(df, bet_type)

    def train_all_models(self, df: pd.DataFrame, bet_type: str = 'totals') -> Dict:
        """Train all 7 model types"""
        logger.info("=" * 70)
        logger.info(f"ENHANCED {self.sport.upper()} TRAINING - {bet_type.upper()} - 7 Models")
        logger.info("=" * 70)

        # Prepare features
        X = self.create_enhanced_feature_matrix(df, bet_type)

        # Get target based on bet type
        if bet_type == 'totals':
            y = df['total'].values if 'total' in df.columns else df['game_total'].values
        elif bet_type == 'spreads':
            y = df['home_margin'].values if 'home_margin' in df.columns else df['spread'].values
        elif bet_type == 'moneyline':
            if 'home_margin' in df.columns:
                y = (df['home_margin'] > 0).astype(int).values
            else:
                y = df['home_win'].values if 'home_win' in df.columns else np.zeros(len(df))

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )

        models = {}
        predictions = {}
        metadata = {
            'sport': self.sport,
            'n_features': X.shape[1],
            'feature_pipeline': 'enhanced' if USE_ENHANCED_PIPELINE else 'base',
            'training_date': datetime.now().isoformat(),
            'n_train_samples': len(X_train),
            'n_test_samples': len(X_test),
            'model_stats': {}
        }

        is_classifier = bet_type == 'moneyline'

        # 1. Random Forest
        logger.info("Training Random Forest...")
        if is_classifier:
            rf = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
        else:
            rf = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        predictions['random_forest'] = rf.predict(X_test)
        models['random_forest'] = rf
        metadata['model_stats']['random_forest'] = self._calc_metrics(y_test, predictions['random_forest'], is_classifier)

        # 2. XGBoost
        if xgb:
            logger.info("Training XGBoost...")
            if is_classifier:
                xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
            else:
                xgb_model = xgb.XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
            xgb_model.fit(X_train, y_train)
            predictions['xgboost'] = xgb_model.predict(X_test)
            models['xgboost'] = xgb_model
            metadata['model_stats']['xgboost'] = self._calc_metrics(y_test, predictions['xgboost'], is_classifier)

        # 3. LightGBM
        if lgb:
            logger.info("Training LightGBM...")
            if is_classifier:
                lgb_model = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1)
            else:
                lgb_model = lgb.LGBMRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1)
            lgb_model.fit(X_train, y_train)
            predictions['lightgbm'] = lgb_model.predict(X_test)
            models['lightgbm'] = lgb_model
            metadata['model_stats']['lightgbm'] = self._calc_metrics(y_test, predictions['lightgbm'], is_classifier)

        # 4. Linear/Logistic Regression
        logger.info("Training Linear Regression...")
        if is_classifier:
            lr = LogisticRegression(max_iter=1000, random_state=42)
        else:
            lr = LinearRegression()
        lr.fit(X_train, y_train)
        predictions['linear'] = lr.predict(X_test)
        models['linear'] = lr
        metadata['model_stats']['linear'] = self._calc_metrics(y_test, predictions['linear'], is_classifier)

        # 5. CatBoost
        if cb:
            logger.info("Training CatBoost...")
            if is_classifier:
                cb_model = cb.CatBoostClassifier(iterations=100, depth=6, learning_rate=0.1, random_state=42, verbose=0)
            else:
                cb_model = cb.CatBoostRegressor(iterations=100, depth=6, learning_rate=0.1, random_state=42, verbose=0)
            cb_model.fit(X_train, y_train)
            predictions['catboost'] = cb_model.predict(X_test)
            models['catboost'] = cb_model
            metadata['model_stats']['catboost'] = self._calc_metrics(y_test, predictions['catboost'], is_classifier)

        # 6. PyTorch TabularNet
        logger.info("Training PyTorch TabularNet...")
        pytorch_trainer = TabularNetTrainer(input_dim=X.shape[1])
        pytorch_model = pytorch_trainer.train(X_train, y_train, epochs=50)
        predictions['pytorch'] = pytorch_trainer.predict(X_test)
        models['pytorch'] = pytorch_model
        metadata['model_stats']['pytorch'] = self._calc_metrics(y_test, predictions['pytorch'], is_classifier)

        # 7. Neural Ensemble
        if USE_NEURAL_ENSEMBLE and len(predictions) >= 4:
            logger.info("Training Neural Ensemble Weighter...")
            base_preds = np.column_stack([predictions[k] for k in sorted(predictions.keys())])
            ensemble = EnsembleWeighter(n_models=len(predictions))
            ensemble_preds = self._train_ensemble(ensemble, base_preds, y_test, epochs=100)
            predictions['neural_ensemble'] = ensemble_preds
            models['ensemble_weighter'] = ensemble
            metadata['model_stats']['neural_ensemble'] = self._calc_metrics(y_test, ensemble_preds, is_classifier)

            weights = torch.softmax(ensemble.weights, dim=0).detach().numpy()
            logger.info(f"Learned ensemble weights: {dict(zip(sorted(predictions.keys())[:-1], weights.round(3)))}")

        # Save all models
        for name, model in models.items():
            if name == 'pytorch':
                torch.save(model.state_dict(), self.output_dir / f"{self.sport}_pytorch_{bet_type}_enhanced.pt")
            elif name == 'ensemble_weighter':
                torch.save(model.state_dict(), self.output_dir / f"{self.sport}_ensemble_{bet_type}_enhanced.pt")
            else:
                joblib.dump(model, self.output_dir / f"{self.sport}_{name}_{bet_type}_enhanced.joblib")

        # Save scaler and metadata
        joblib.dump(self.scaler, self.output_dir / f"{self.sport}_scaler_{bet_type}_enhanced.joblib")
        joblib.dump(metadata, self.output_dir / f"{self.sport}_{bet_type}_enhanced_metadata.joblib")

        logger.info(f"\n{'='*70}")
        logger.info(f"{self.sport.upper()} MODEL PERFORMANCE SUMMARY:")
        for model_name, stats in metadata['model_stats'].items():
            if is_classifier:
                logger.info(f"  {model_name}: Accuracy={stats.get('accuracy', 0):.3f}")
            else:
                logger.info(f"  {model_name}: MAE={stats.get('mae', 0):.3f}")
        logger.info(f"{'='*70}")

        return metadata

    def _train_ensemble(self, ensemble, base_preds, y_true, epochs=100) -> np.ndarray:
        """Train the neural ensemble weighter"""
        optimizer = torch.optim.Adam(ensemble.parameters(), lr=0.01)
        X_tensor = torch.FloatTensor(base_preds)
        y_tensor = torch.FloatTensor(y_true)

        for epoch in range(epochs):
            optimizer.zero_grad()
            preds, _ = ensemble(X_tensor, model_accs)
            loss = torch.nn.functional.mse_loss(preds, y_tensor)
            loss.backward()
            optimizer.step()

        with torch.no_grad():
            final_preds, _ = ensemble(X_tensor, model_accs)
            return final_preds.numpy()

    def _calc_metrics(self, y_true, y_pred, is_classifier=False) -> Dict:
        """Calculate model performance metrics"""
        if is_classifier:
            y_pred_binary = (y_pred > 0.5).astype(int) if y_pred.dtype == float else y_pred
            return {
                'accuracy': float((y_pred_binary == y_true).mean()),
                'n_samples': len(y_true)
            }
        else:
            return {
                'mae': float(mean_absolute_error(y_true, y_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
                'r2': float(r2_score(y_true, y_pred)),
                'n_samples': len(y_true)
            }


def load_training_data(sport: str, seasons: list):
    """Load training data for the specified sport"""
    loaders = {
        'nba': load_nba_training_data,
        'ncaab': load_ncaab_training_data,
        'nhl': load_nhl_training_data,
        'nfl': load_nfl_training_data,
        'ncaaf': load_ncaaf_training_data,
    }
    loader = loaders.get(sport)
    if loader:
        return loader(seasons=seasons)
    raise ValueError(f"Unknown sport: {sport}")


def main():
    parser = argparse.ArgumentParser(description='Train Enhanced Models for All Sports')
    parser.add_argument('--sport', type=str, required=True, choices=['nba', 'ncaab', 'nhl', 'nfl', 'ncaaf', 'all'])
    parser.add_argument('--seasons', nargs='+', type=str, default=['2022-23', '2023-24', '2024-25'])
    parser.add_argument('--bet-types', nargs='+', default=['totals', 'spreads', 'moneyline'])
    args = parser.parse_args()

    sports = ['nba', 'ncaab', 'nhl', 'nfl', 'ncaaf'] if args.sport == 'all' else [args.sport]

    for sport in sports:
        logger.info(f"\n{'#'*70}")
        logger.info(f"# TRAINING {sport.upper()} ENHANCED MODELS")
        logger.info(f"{'#'*70}\n")

        trainer = EnhancedModelTrainer(sport=sport)

        try:
            logger.info(f"Loading {sport.upper()} training data for seasons: {args.seasons}")
            df = load_training_data(sport, args.seasons)
            logger.info(f"Loaded {len(df)} training samples")

            for bet_type in args.bet_types:
                try:
                    trainer.train_all_models(df, bet_type=bet_type)
                except Exception as e:
                    logger.error(f"Error training {sport} {bet_type}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error loading data for {sport}: {e}")
            continue

    logger.info("\n" + "=" * 70)
    logger.info("ENHANCED TRAINING COMPLETE - ALL SPORTS")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
