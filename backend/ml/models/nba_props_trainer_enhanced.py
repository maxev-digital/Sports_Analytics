"""
Enhanced NBA Props Model Trainer - Uses Real Player & Matchup Data
Predictions now based on actual performance, not just betting lines!

Features (20+):
- Player season averages (PPG, RPG, APG, etc.)
- Recent form (last 10 games)
- Market comparison (line vs performance)
- Opponent matchup ratings (defensive/offensive)
- Home/away splits
- Minutes played
"""

import sys
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple
import argparse

# ML imports
import xgboost as xgb
import lightgbm as lgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
import joblib

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import team stats scraper
from scrapers.teamrankings_nba_scraper import TeamRankingsNBAScraper


class EnhancedNBAPropsTrainer:
    """Enhanced NBA Props Model Trainer with Real Features"""

    PROP_TYPES = ['points', 'rebounds', 'assists', 'threes', 'blocks', 'steals', 'PRA']

    # Map prop types to player stat columns
    STAT_MAP = {
        'points': 'points_per_game',
        'rebounds': 'rebounds_per_game',
        'assists': 'assists_per_game',
        'threes': 'fg3_per_game',
        'blocks': 'blocks_per_game',
        'steals': 'steals_per_game',
        'PRA': None  # Calculated as points + rebounds + assists
    }

    LAST10_MAP = {
        'points': 'last_10_ppg',
        'rebounds': 'last_10_rpg',
        'assists': 'last_10_apg',
        'threes': None,  # Not available
        'blocks': None,
        'steals': None,
        'PRA': None
    }

    # Offensive props use opponent defensive rating
    # Defensive props use opponent offensive rating
    OFFENSIVE_PROPS = ['points', 'assists', 'threes', 'PRA']
    DEFENSIVE_PROPS = ['rebounds', 'blocks', 'steals']

    def __init__(self, db_path: str = "D:/backend/data/player_props.db"):
        self.db_path = db_path
        self.models_dir = Path("D:/backend/ml/trained_models")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.team_scraper = TeamRankingsNBAScraper()
        self.team_stats = {}

    def load_team_stats(self):
        """Load team offensive and defensive ratings"""
        print(f"\n{'='*70}")
        print("LOADING TEAM STATS FROM TEAMRANKINGS")
        print(f"{'='*70}\n")

        try:
            # Fetch all team stats from TeamRankings
            all_team_data = self.team_scraper.fetch_all_team_stats()

            # Extract offensive and defensive ratings
            for team_name, stats in all_team_data.items():
                self.team_stats[team_name] = {
                    'offensive_rating': stats['pts_per_game'],
                    'defensive_rating': stats['pts_allowed'],
                    'pace': stats.get('pace', 100.0),
                    'assists': stats.get('assists', 25.0),
                    'turnovers': stats.get('turnovers', 14.0),
                    'steals': stats.get('steals', 7.5),
                    'blocks': stats.get('blocks', 5.0),
                    'rebounds': stats.get('total_rebounds', 45.0)
                }

            print(f"[OK] Loaded stats for {len(self.team_stats)} teams")
            if self.team_stats:
                sample_team = list(self.team_stats.keys())[0]
                sample_data = self.team_stats[sample_team]
                print(f"  Sample: {sample_team}")
                print(f"    Offensive: {sample_data['offensive_rating']:.1f} PPG")
                print(f"    Defensive: {sample_data['defensive_rating']:.1f} PPG allowed")

        except Exception as e:
            print(f"[WARN] Could not load team stats: {e}")
            print(f"  Continuing without opponent matchup features...")
            import traceback
            traceback.print_exc()

    def prepare_training_data(self, prop_type: str, min_samples: int = 100):
        """
        Load historical results and enrich with player + matchup features
        """
        print(f"\n{'='*70}")
        print(f"PREPARING DATA FOR {prop_type.upper()}")
        print(f"{'='*70}\n")

        conn = sqlite3.connect(self.db_path)

        # Get historical results with player stats and opponent info
        # Note: player_stats_cache has CURRENT stats, not historical
        # So we join only on player_id and use latest stats as proxy
        query = """
            SELECT
                r.prop_type,
                r.market_line,
                r.actual_value,
                r.hit,
                r.player_id,
                r.player_name,
                l.home_away,
                l.date,
                l.opponent,
                s.points_per_game,
                s.rebounds_per_game,
                s.assists_per_game,
                s.fg3_per_game,
                s.blocks_per_game,
                s.steals_per_game,
                s.minutes_per_game,
                s.fg_pct,
                s.last_10_ppg,
                s.last_10_rpg,
                s.last_10_apg,
                s.games_played
            FROM player_props_results r
            JOIN player_props_lines l
                ON r.date = l.date
                AND r.player_id = l.player_id
                AND r.prop_type = l.prop_type
            LEFT JOIN player_stats_cache s
                ON r.player_id = s.player_id
            WHERE r.prop_type = ?
                AND r.actual_value IS NOT NULL
        """

        df = pd.read_sql_query(query, conn, params=(prop_type,))
        conn.close()

        print(f"[1/5] Loaded {len(df)} historical results")

        if len(df) < min_samples:
            print(f"[ERROR] Only {len(df)} samples (need {min_samples}+)")
            return None, None, None, None, None

        # Extract features
        print(f"[2/5] Engineering features...")
        features_df = self._engineer_features(df, prop_type)

        if len(features_df) == 0:
            print(f"[ERROR] No valid features after engineering")
            return None, None, None, None, None

        # Split features and target
        feature_cols = [c for c in features_df.columns if c not in ['actual_value', 'hit']]
        X = features_df[feature_cols]
        y = features_df['actual_value'].values

        print(f"[3/5] Feature matrix: {X.shape}")
        print(f"  Features: {', '.join(feature_cols[:10])}...")

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        print(f"[4/5] Train: {len(X_train)}, Test: {len(X_test)}")
        print(f"[5/5] Target range: [{y.min():.1f}, {y.max():.1f}], mean: {y.mean():.1f}")

        return X_train, X_test, y_train, y_test, feature_cols

    def _engineer_features(self, df: pd.DataFrame, prop_type: str) -> pd.DataFrame:
        """Create all features from raw data"""

        features = pd.DataFrame()

        # 1. Market Line Features (6)
        features['market_line'] = df['market_line']
        features['line_normalized'] = df['market_line'] / 100.0
        features['is_home'] = (df['home_away'] == 'HOME').astype(float)
        features['is_away'] = (df['home_away'] == 'AWAY').astype(float)
        features['line_squared'] = features['line_normalized'] ** 2
        features['line_log'] = np.log1p(df['market_line'])

        # 2. Player Season Performance Features
        stat_col = self.STAT_MAP[prop_type]

        if prop_type == 'PRA':
            # Calculate PRA as sum
            features['season_avg'] = (
                df['points_per_game'].fillna(0) +
                df['rebounds_per_game'].fillna(0) +
                df['assists_per_game'].fillna(0)
            )
        else:
            features['season_avg'] = df[stat_col].fillna(df['market_line'])

        features['minutes_per_game'] = df['minutes_per_game'].fillna(30.0)
        features['games_played'] = df['games_played'].fillna(10)
        features['fg_pct'] = df['fg_pct'].fillna(0.45)

        # 3. Recent Form Features (Last 10 games)
        last10_col = self.LAST10_MAP.get(prop_type)

        if prop_type == 'PRA':
            features['last_10_avg'] = (
                df['last_10_ppg'].fillna(0) +
                df['last_10_rpg'].fillna(0) +
                df['last_10_apg'].fillna(0)
            )
        elif last10_col and last10_col in df.columns:
            features['last_10_avg'] = df[last10_col].fillna(features['season_avg'])
        else:
            features['last_10_avg'] = features['season_avg']  # Fallback

        # Hot/cold indicator
        features['deviation_from_season'] = features['last_10_avg'] - features['season_avg']
        features['is_hot'] = (features['deviation_from_season'] > 1.0).astype(float)
        features['is_cold'] = (features['deviation_from_season'] < -1.0).astype(float)

        # 4. Market Comparison Features
        features['line_vs_season'] = features['market_line'] - features['season_avg']
        features['line_vs_last10'] = features['market_line'] - features['last_10_avg']

        # Implied deviation percentage
        features['implied_deviation_pct'] = (
            (features['market_line'] - features['season_avg']) /
            (features['season_avg'] + 0.1)  # Avoid division by zero
        )

        # 5. Opponent Matchup Features
        if self.team_stats:
            opponent_ratings = []

            for opponent in df['opponent']:
                # Normalize opponent name to match team stats keys
                opp_normalized = opponent.strip()
                team_data = self.team_stats.get(opp_normalized, {})

                # Choose defensive or offensive rating based on prop type
                if prop_type in self.OFFENSIVE_PROPS:
                    # Offensive props: use opponent defensive rating
                    rating = team_data.get('defensive_rating', 110.0)  # League avg
                else:
                    # Defensive props: use opponent offensive rating
                    rating = team_data.get('offensive_rating', 110.0)

                opponent_ratings.append(rating)

            features['opponent_rating'] = opponent_ratings
            features['opponent_rating_normalized'] = (np.array(opponent_ratings) - 110.0) / 10.0
        else:
            features['opponent_rating'] = 110.0  # Neutral
            features['opponent_rating_normalized'] = 0.0

        # 6. Interaction Features
        features['season_avg_x_minutes'] = features['season_avg'] * features['minutes_per_game'] / 30.0
        features['line_x_opponent'] = features['market_line'] * features['opponent_rating_normalized']

        # 7. Target (actual performance)
        features['actual_value'] = df['actual_value']

        # Drop rows with missing critical features
        features = features.dropna()

        print(f"  Created {len(features.columns)} features for {len(features)} samples")

        return features

    def train_xgboost(self, X_train, y_train, X_test, y_test):
        """Train XGBoost Regressor"""
        print(f"  Training XGBoost...")

        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            random_state=42,
            eval_metric='rmse'
        )

        model.fit(X_train, y_train, verbose=False)
        y_pred = model.predict(X_test)

        return self._calculate_metrics(y_test, y_pred, X_test, model)

    def train_lightgbm(self, X_train, y_train, X_test, y_test):
        """Train LightGBM Regressor"""
        print(f"  Training LightGBM...")

        model = lgb.LGBMRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            random_state=42,
            verbose=-1
        )

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        return self._calculate_metrics(y_test, y_pred, X_test, model)

    def train_random_forest(self, X_train, y_train, X_test, y_test):
        """Train Random Forest Regressor"""
        print(f"  Training Random Forest...")

        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        return self._calculate_metrics(y_test, y_pred, X_test, model)

    def train_linear(self, X_train, y_train, X_test, y_test):
        """Train Linear Regression"""
        print(f"  Training Linear Regression...")

        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        return self._calculate_metrics(y_test, y_pred, X_test, model)

    def _calculate_metrics(self, y_test, y_pred, X_test, model):
        """Calculate regression metrics"""
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # OVER/UNDER accuracy (predicting direction vs market line)
        market_lines = X_test['market_line'].values
        actual_over = (y_test > market_lines)
        predicted_over = (y_pred > market_lines)
        over_under_accuracy = np.mean(actual_over == predicted_over) * 100

        return {
            'model': model,
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'over_under_accuracy': over_under_accuracy,
            'test_accuracy': over_under_accuracy,
            'is_regression': True
        }

    def train_single_prop(self, prop_type: str, min_samples: int = 100):
        """Train all 4 models for a single prop type"""
        print(f"\n{'='*70}")
        print(f"TRAINING: {prop_type.upper()}")
        print(f"{'='*70}\n")

        # Prepare data
        X_train, X_test, y_train, y_test, feature_cols = self.prepare_training_data(
            prop_type, min_samples
        )

        if X_train is None:
            print(f"[SKIP] Not enough data for {prop_type}")
            return False

        # Train all 4 model types
        models_trained = 0

        for model_type, train_func in [
            ('xgboost', self.train_xgboost),
            ('lightgbm', self.train_lightgbm),
            ('random_forest', self.train_random_forest),
            ('linear', self.train_linear)
        ]:
            try:
                model_data = train_func(X_train, y_train, X_test, y_test)

                # Add metadata
                model_data.update({
                    'model_type': model_type,
                    'prop_type': prop_type,
                    'feature_names': feature_cols,
                    'trained_date': datetime.now().isoformat()
                })

                # Save model
                model_path = self.models_dir / f"{prop_type}_{model_type}_model.joblib"
                joblib.dump(model_data, model_path)

                print(f"    {model_type}: RMSE={model_data['rmse']:.3f}, "
                      f"MAE={model_data['mae']:.3f}, "
                      f"R²={model_data['r2']:.3f}, "
                      f"O/U Acc={model_data['over_under_accuracy']:.1f}%")

                models_trained += 1

            except Exception as e:
                print(f"    [ERROR] {model_type} failed: {e}")

        print(f"\n[SUCCESS] Trained {models_trained}/4 models for {prop_type}")
        return models_trained > 0

    def train_all(self, min_samples: int = 100):
        """Train models for all prop types"""
        print(f"\n{'#'*70}")
        print(f"# ENHANCED NBA PROPS TRAINER - FULL TRAINING")
        print(f"#   Using real player stats + opponent matchups!")
        print(f"{'#'*70}\n")

        # Load team stats first
        self.load_team_stats()

        start_time = datetime.now()
        total_trained = 0

        for prop_type in self.PROP_TYPES:
            if self.train_single_prop(prop_type, min_samples):
                total_trained += 1

        duration = (datetime.now() - start_time).total_seconds()

        print(f"\n{'='*70}")
        print(f"TRAINING COMPLETE")
        print(f"{'='*70}")
        print(f"  Prop types trained: {total_trained}/{len(self.PROP_TYPES)}")
        print(f"  Total models: {total_trained * 4}")
        print(f"  Duration: {duration:.1f}s")
        print(f"  Saved to: {self.models_dir}")
        print(f"\n{'='*70}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Enhanced NBA Props Model Trainer')
    parser.add_argument('--prop-type', type=str, default='all',
                       help='Prop type to train (or "all")')
    parser.add_argument('--min-samples', type=int, default=100,
                       help='Minimum samples required for training')
    parser.add_argument('--db-path', type=str, default='D:/backend/data/player_props.db',
                       help='Path to props database')

    args = parser.parse_args()

    trainer = EnhancedNBAPropsTrainer(db_path=args.db_path)

    if args.prop_type == 'all':
        trainer.train_all(min_samples=args.min_samples)
    else:
        trainer.train_single_prop(args.prop_type, min_samples=args.min_samples)


if __name__ == "__main__":
    main()
