"""
Master training script for all ML models across all sports.
Trains NBA, NCAAB, NFL, and NHL prediction models.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all models
from models.nba import (
    lightgbm_totals,
    linear_regression_spreads,
    linear_regression_totals,
    logistic_regression_moneyline,
    random_forest_moneyline,
    random_forest_spreads,
    xgboost_spreads
)

from models.ncaab import (
    lightgbm_moneyline,
    lightgbm_spreads,
    lightgbm_totals as ncaab_lightgbm_totals,
    linear_regression_spreads as ncaab_linear_spreads,
    linear_regression_totals as ncaab_linear_totals,
    logistic_regression_moneyline as ncaab_logistic_ml,
    random_forest_moneyline as ncaab_rf_ml,
    random_forest_spreads as ncaab_rf_spreads,
    random_forest_totals as ncaab_rf_totals,
    xgboost_moneyline as ncaab_xgb_ml,
    xgboost_spreads as ncaab_xgb_spreads,
    xgboost_totals as ncaab_xgb_totals
)

from models.nhl import (
    lightgbm_moneyline as nhl_lightgbm_ml,
    lightgbm_spreads as nhl_lightgbm_spreads,
    lightgbm_totals as nhl_lightgbm_totals,
    linear_regression_spreads as nhl_linear_spreads,
    linear_regression_totals as nhl_linear_totals,
    logistic_regression_moneyline as nhl_logistic_ml,
    random_forest_moneyline as nhl_rf_ml,
    random_forest_spreads as nhl_rf_spreads,
    random_forest_totals as nhl_rf_totals,
    xgboost_moneyline as nhl_xgb_ml,
    xgboost_spreads as nhl_xgb_spreads,
    xgboost_totals as nhl_xgb_totals
)

from models.nfl import (
    linear_regression_spreads as nfl_linear_spreads
)


class ModelTrainer:
    """Centralized model training orchestrator"""

    def __init__(self):
        self.base_path = Path(__file__).parent
        self.data_path = self.base_path / "data"
        self.historical_path = self.data_path / "historical"
        self.results = []

    def load_nba_data(self):
        """Load NBA historical data"""
        print("\n[NBA] Loading historical data...")
        nba_file = self.historical_path / "nba" / "nba_historical_latest.csv"

        if not nba_file.exists():
            print(f"[NBA] ERROR: {nba_file} not found!")
            return None

        df = pd.read_csv(nba_file)
        print(f"[NBA] Loaded {len(df)} games from {df['season'].min()} to {df['season'].max()}")
        return df

    def load_ncaab_data(self):
        """Load NCAAB historical data with KenPom ratings"""
        print("\n[NCAAB] Loading historical data...")
        ncaab_path = self.historical_path / "ncaab"

        # Load game results
        games_dfs = []
        for year in [2023, 2024, 2025]:
            file_path = ncaab_path / f"games_{year}.csv"
            if file_path.exists():
                df = pd.read_csv(file_path)
                games_dfs.append(df)
                print(f"[NCAAB] Loaded {len(df)} games from {year}")

        if not games_dfs:
            print("[NCAAB] ERROR: No game data found!")
            return None

        games = pd.concat(games_dfs, ignore_index=True)
        print(f"[NCAAB] Total games: {len(games)}")
        return games

    def load_nfl_data(self):
        """Load NFL historical data"""
        print("\n[NFL] Loading historical data...")
        nfl_file = self.historical_path / "nfl" / "sample_training_data.csv"

        if not nfl_file.exists():
            print(f"[NFL] ERROR: {nfl_file} not found!")
            return None

        df = pd.read_csv(nfl_file)
        print(f"[NFL] Loaded {len(df)} games")
        return df

    def load_nhl_data(self):
        """Load NHL historical data"""
        print("\n[NHL] Loading historical data...")
        nhl_file = self.historical_path / "nhl" / "sample_training_data.csv"

        if not nhl_file.exists():
            print(f"[NHL] ERROR: {nhl_file} not found!")
            return None

        df = pd.read_csv(nhl_file)
        print(f"[NHL] Loaded {len(df)} games")
        return df

    def train_nba_models(self, data):
        """Train all NBA models"""
        if data is None or len(data) == 0:
            print("[NBA] Skipping - no data available")
            return

        print("\n" + "="*60)
        print("TRAINING NBA MODELS")
        print("="*60)

        models = [
            ("LightGBM Totals", lightgbm_totals),
            ("Linear Regression Spreads", linear_regression_spreads),
            ("Linear Regression Totals", linear_regression_totals),
            ("Logistic Regression Moneyline", logistic_regression_moneyline),
            ("Random Forest Moneyline", random_forest_moneyline),
            ("Random Forest Spreads", random_forest_spreads),
            ("XGBoost Spreads", xgboost_spreads)
        ]

        for name, model_module in models:
            try:
                print(f"\n[NBA - {name}] Training...")
                if hasattr(model_module, 'train'):
                    metrics = model_module.train(data)
                    self.results.append({
                        'sport': 'NBA',
                        'model': name,
                        'status': 'SUCCESS',
                        'metrics': metrics
                    })
                    print(f"[NBA - {name}] ✓ Training complete")
                else:
                    print(f"[NBA - {name}] No train() function found - skipping")

            except Exception as e:
                print(f"[NBA - {name}] ERROR: {str(e)}")
                self.results.append({
                    'sport': 'NBA',
                    'model': name,
                    'status': 'FAILED',
                    'error': str(e)
                })

    def train_ncaab_models(self, data):
        """Train all NCAAB models"""
        if data is None or len(data) == 0:
            print("[NCAAB] Skipping - no data available")
            return

        print("\n" + "="*60)
        print("TRAINING NCAAB MODELS")
        print("="*60)

        models = [
            ("LightGBM Moneyline", lightgbm_moneyline),
            ("LightGBM Spreads", lightgbm_spreads),
            ("LightGBM Totals", ncaab_lightgbm_totals),
            ("Linear Regression Spreads", ncaab_linear_spreads),
            ("Linear Regression Totals", ncaab_linear_totals),
            ("Logistic Regression Moneyline", ncaab_logistic_ml),
            ("Random Forest Moneyline", ncaab_rf_ml),
            ("Random Forest Spreads", ncaab_rf_spreads),
            ("Random Forest Totals", ncaab_rf_totals),
            ("XGBoost Moneyline", ncaab_xgb_ml),
            ("XGBoost Spreads", ncaab_xgb_spreads),
            ("XGBoost Totals", ncaab_xgb_totals)
        ]

        for name, model_module in models:
            try:
                print(f"\n[NCAAB - {name}] Training...")
                if hasattr(model_module, 'train'):
                    metrics = model_module.train(data)
                    self.results.append({
                        'sport': 'NCAAB',
                        'model': name,
                        'status': 'SUCCESS',
                        'metrics': metrics
                    })
                    print(f"[NCAAB - {name}] ✓ Training complete")
                else:
                    print(f"[NCAAB - {name}] No train() function found - skipping")

            except Exception as e:
                print(f"[NCAAB - {name}] ERROR: {str(e)}")
                self.results.append({
                    'sport': 'NCAAB',
                    'model': name,
                    'status': 'FAILED',
                    'error': str(e)
                })

    def train_nhl_models(self, data):
        """Train all NHL models"""
        if data is None or len(data) == 0:
            print("[NHL] Skipping - no data available")
            return

        print("\n" + "="*60)
        print("TRAINING NHL MODELS")
        print("="*60)

        models = [
            ("LightGBM Moneyline", nhl_lightgbm_ml),
            ("LightGBM Spreads", nhl_lightgbm_spreads),
            ("LightGBM Totals", nhl_lightgbm_totals),
            ("Linear Regression Spreads", nhl_linear_spreads),
            ("Linear Regression Totals", nhl_linear_totals),
            ("Logistic Regression Moneyline", nhl_logistic_ml),
            ("Random Forest Moneyline", nhl_rf_ml),
            ("Random Forest Spreads", nhl_rf_spreads),
            ("Random Forest Totals", nhl_rf_totals),
            ("XGBoost Moneyline", nhl_xgb_ml),
            ("XGBoost Spreads", nhl_xgb_spreads),
            ("XGBoost Totals", nhl_xgb_totals)
        ]

        for name, model_module in models:
            try:
                print(f"\n[NHL - {name}] Training...")
                if hasattr(model_module, 'train'):
                    metrics = model_module.train(data)
                    self.results.append({
                        'sport': 'NHL',
                        'model': name,
                        'status': 'SUCCESS',
                        'metrics': metrics
                    })
                    print(f"[NHL - {name}] ✓ Training complete")
                else:
                    print(f"[NHL - {name}] No train() function found - skipping")

            except Exception as e:
                print(f"[NHL - {name}] ERROR: {str(e)}")
                self.results.append({
                    'sport': 'NHL',
                    'model': name,
                    'status': 'FAILED',
                    'error': str(e)
                })

    def train_nfl_models(self, data):
        """Train all NFL models"""
        if data is None or len(data) == 0:
            print("[NFL] Skipping - no data available")
            return

        print("\n" + "="*60)
        print("TRAINING NFL MODELS")
        print("="*60)

        models = [
            ("Linear Regression Spreads", nfl_linear_spreads)
        ]

        for name, model_module in models:
            try:
                print(f"\n[NFL - {name}] Training...")
                if hasattr(model_module, 'train'):
                    metrics = model_module.train(data)
                    self.results.append({
                        'sport': 'NFL',
                        'model': name,
                        'status': 'SUCCESS',
                        'metrics': metrics
                    })
                    print(f"[NFL - {name}] ✓ Training complete")
                else:
                    print(f"[NFL - {name}] No train() function found - skipping")

            except Exception as e:
                print(f"[NFL - {name}] ERROR: {str(e)}")
                self.results.append({
                    'sport': 'NFL',
                    'model': name,
                    'status': 'FAILED',
                    'error': str(e)
                })

    def print_summary(self):
        """Print training summary"""
        print("\n" + "="*60)
        print("TRAINING SUMMARY")
        print("="*60)

        for sport in ['NBA', 'NCAAB', 'NHL', 'NFL']:
            sport_results = [r for r in self.results if r['sport'] == sport]
            if sport_results:
                success = len([r for r in sport_results if r['status'] == 'SUCCESS'])
                failed = len([r for r in sport_results if r['status'] == 'FAILED'])
                print(f"\n{sport}: {success} succeeded, {failed} failed")

                for result in sport_results:
                    status_icon = "✓" if result['status'] == 'SUCCESS' else "✗"
                    print(f"  {status_icon} {result['model']}")
                    if result['status'] == 'FAILED':
                        print(f"    Error: {result.get('error', 'Unknown error')}")

        total_success = len([r for r in self.results if r['status'] == 'SUCCESS'])
        total_failed = len([r for r in self.results if r['status'] == 'FAILED'])

        print("\n" + "="*60)
        print(f"TOTAL: {total_success} models trained successfully, {total_failed} failed")
        print("="*60)

    def run(self):
        """Run full training pipeline"""
        print("="*60)
        print("MAX-EV SPORTS - MODEL TRAINING PIPELINE")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        # Load data
        nba_data = self.load_nba_data()
        ncaab_data = self.load_ncaab_data()
        nfl_data = self.load_nfl_data()
        nhl_data = self.load_nhl_data()

        # Train models
        self.train_nba_models(nba_data)
        self.train_ncaab_models(ncaab_data)
        self.train_nhl_models(nhl_data)
        self.train_nfl_models(nfl_data)

        # Print summary
        self.print_summary()

        print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.run()
