"""
Enhanced NBA Props Predictor - Uses Real Player & Matchup Data
Uses ALL 22 enhanced features (player stats + opponent matchups)

This predictor uses the SAME features the models were trained on.
"""

import sys
import sqlite3
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List
import argparse

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import team stats scraper
from scrapers.teamrankings_nba_scraper import TeamRankingsNBAScraper


class EnhancedPropsPredictor:
    """
    Enhanced props predictor - uses 22 features (player stats + opponent matchups)
    Matches the enhanced trainer feature set
    """

    # Map prop types to player stat columns
    STAT_MAP = {
        'points': 'points_per_game',
        'rebounds': 'rebounds_per_game',
        'assists': 'assists_per_game',
        'threes': 'fg3_per_game',
        'blocks': 'blocks_per_game',
        'steals': 'steals_per_game',
        'PRA': None  # Calculated
    }

    LAST10_MAP = {
        'points': 'last_10_ppg',
        'rebounds': 'last_10_rpg',
        'assists': 'last_10_apg',
        'threes': None,
        'blocks': None,
        'steals': None,
        'PRA': None
    }

    OFFENSIVE_PROPS = ['points', 'assists', 'threes', 'PRA']
    DEFENSIVE_PROPS = ['rebounds', 'blocks', 'steals']

    def __init__(self, db_path: str = "data/player_props.db"):
        self.db_path = db_path
        self.models_dir = Path("D:/backend/ml/trained_models")
        self.models = {}
        self.team_scraper = TeamRankingsNBAScraper()
        self.team_stats = {}

    def load_team_stats(self):
        """Load team offensive and defensive ratings"""
        print(f"\n{'='*70}")
        print("LOADING TEAM STATS FROM TEAMRANKINGS")
        print(f"{'='*70}\n")

        try:
            all_team_data = self.team_scraper.fetch_all_team_stats()

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

            print(f"[OK] Loaded stats for {len(self.team_stats)} teams\n")

        except Exception as e:
            print(f"[WARN] Could not load team stats: {e}")
            print(f"  Continuing with neutral opponent ratings...\n")

    def load_models(self):
        """Load trained REGRESSION models"""
        import joblib

        print(f"\n{'='*70}")
        print("LOADING REGRESSION MODELS")
        print(f"{'='*70}\n")

        model_files = list(self.models_dir.glob("*_model.joblib"))

        for model_file in model_files:
            try:
                model_data = joblib.load(model_file)

                # Extract prop_type and model_type from filename
                # e.g., "points_xgboost_model.joblib"
                name_parts = model_file.stem.replace('_model', '').split('_')
                prop_type = name_parts[0]
                model_type = '_'.join(name_parts[1:])

                key = f"{prop_type}_{model_type}"
                self.models[key] = model_data

                acc = model_data.get('test_accuracy', 0)
                is_regression = model_data.get('is_regression', False)
                model_label = "REGRESSION" if is_regression else "CLASSIFICATION"
                print(f"  [OK] Loaded {key}: {acc:.1f}% acc ({model_label})")

            except Exception as e:
                print(f"  [ERROR] Failed to load {model_file.name}: {e}")

        print(f"\n[SUCCESS] Loaded {len(self.models)} models\n")

    def extract_enhanced_features(
        self,
        player_id: str,
        player_name: str,
        prop_type: str,
        market_line: float,
        home_away: str,
        opponent: str
    ) -> Dict:
        """
        Extract ALL 22 enhanced features matching the trainer
        Includes player stats + opponent matchups
        """
        # Query player stats from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Try to find by player_id first
        cursor.execute("""
            SELECT points_per_game, rebounds_per_game, assists_per_game,
                   fg3_per_game, blocks_per_game, steals_per_game,
                   minutes_per_game, fg_pct, games_played,
                   last_10_ppg, last_10_rpg, last_10_apg
            FROM player_stats_cache
            WHERE player_id = ?
        """, (player_id,))

        player_stats = cursor.fetchone()

        # Fallback: Try by player_name if ID lookup failed
        if not player_stats:
            cursor.execute("""
                SELECT points_per_game, rebounds_per_game, assists_per_game,
                       fg3_per_game, blocks_per_game, steals_per_game,
                       minutes_per_game, fg_pct, games_played,
                       last_10_ppg, last_10_rpg, last_10_apg
                FROM player_stats_cache
                WHERE player_name = ?
            """, (player_name,))
            player_stats = cursor.fetchone()

        conn.close()

        # Initialize features dict
        features = {}

        # 1. Market Line Features (6)
        features['market_line'] = market_line
        features['line_normalized'] = market_line / 100.0
        features['is_home'] = 1.0 if home_away == 'HOME' else 0.0
        features['is_away'] = 1.0 if home_away == 'AWAY' else 0.0
        features['line_squared'] = features['line_normalized'] ** 2
        features['line_log'] = np.log1p(market_line)

        # 2. Player Season Performance Features
        if player_stats:
            ppg, rpg, apg, fg3pg, bpg, spg, mpg, fg_pct, gp, l10_ppg, l10_rpg, l10_apg = player_stats

            # Get season average for this prop type
            if prop_type == 'PRA':
                season_avg = (ppg or 0) + (rpg or 0) + (apg or 0)
            else:
                stat_col = self.STAT_MAP[prop_type]
                season_avg = {
                    'points_per_game': ppg,
                    'rebounds_per_game': rpg,
                    'assists_per_game': apg,
                    'fg3_per_game': fg3pg,
                    'blocks_per_game': bpg,
                    'steals_per_game': spg
                }.get(stat_col, market_line)

            features['season_avg'] = season_avg if season_avg else market_line
            features['minutes_per_game'] = mpg if mpg else 30.0
            features['games_played'] = gp if gp else 10
            features['fg_pct'] = fg_pct if fg_pct else 0.45

            # 3. Recent Form Features (Last 10 games)
            if prop_type == 'PRA':
                last_10_avg = (l10_ppg or 0) + (l10_rpg or 0) + (l10_apg or 0)
            else:
                last10_col = self.LAST10_MAP.get(prop_type)
                if last10_col:
                    last_10_avg = {
                        'last_10_ppg': l10_ppg,
                        'last_10_rpg': l10_rpg,
                        'last_10_apg': l10_apg
                    }.get(last10_col, features['season_avg'])
                else:
                    last_10_avg = features['season_avg']

            features['last_10_avg'] = last_10_avg if last_10_avg else features['season_avg']
        else:
            # Fallback if no player stats found
            features['season_avg'] = market_line
            features['minutes_per_game'] = 30.0
            features['games_played'] = 10
            features['fg_pct'] = 0.45
            features['last_10_avg'] = market_line

        # Hot/cold indicator
        features['deviation_from_season'] = features['last_10_avg'] - features['season_avg']
        features['is_hot'] = 1.0 if features['deviation_from_season'] > 1.0 else 0.0
        features['is_cold'] = 1.0 if features['deviation_from_season'] < -1.0 else 0.0

        # 4. Market Comparison Features
        features['line_vs_season'] = features['market_line'] - features['season_avg']
        features['line_vs_last10'] = features['market_line'] - features['last_10_avg']
        features['implied_deviation_pct'] = (
            (features['market_line'] - features['season_avg']) /
            (features['season_avg'] + 0.1)
        )

        # 5. Opponent Matchup Features
        if self.team_stats and opponent:
            opp_normalized = opponent.strip()
            team_data = self.team_stats.get(opp_normalized, {})

            # Choose defensive or offensive rating based on prop type
            if prop_type in self.OFFENSIVE_PROPS:
                rating = team_data.get('defensive_rating', 110.0)
            else:
                rating = team_data.get('offensive_rating', 110.0)

            features['opponent_rating'] = rating
            features['opponent_rating_normalized'] = (rating - 110.0) / 10.0
        else:
            features['opponent_rating'] = 110.0
            features['opponent_rating_normalized'] = 0.0

        # 6. Interaction Features
        features['season_avg_x_minutes'] = features['season_avg'] * features['minutes_per_game'] / 30.0
        features['line_x_opponent'] = features['market_line'] * features['opponent_rating_normalized']

        return features

    def predict_prop(
        self,
        player_id: str,
        player_name: str,
        team: str,
        opponent: str,
        prop_type: str,
        market_line: float,
        home_away: str
    ) -> Dict:
        """
        Generate prediction using ALL 22 enhanced features
        """
        # Extract all 22 features
        features = self.extract_enhanced_features(
            player_id=player_id,
            player_name=player_name,
            prop_type=prop_type,
            market_line=market_line,
            home_away=home_away,
            opponent=opponent
        )

        # Convert to DataFrame (must match training feature order)
        feature_names = [
            'market_line', 'line_normalized', 'is_home', 'is_away',
            'line_squared', 'line_log', 'season_avg', 'minutes_per_game',
            'games_played', 'fg_pct', 'last_10_avg', 'deviation_from_season',
            'is_hot', 'is_cold', 'line_vs_season', 'line_vs_last10',
            'implied_deviation_pct', 'opponent_rating', 'opponent_rating_normalized',
            'season_avg_x_minutes', 'line_x_opponent'
        ]
        X = pd.DataFrame([features])[feature_names]

        # Get predictions from all models for this prop type
        predicted_values = []
        model_votes = {}

        for model_name in ['xgboost', 'lightgbm', 'random_forest', 'linear']:
            key = f"{prop_type}_{model_name}"

            if key in self.models:
                model_data = self.models[key]
                model = model_data['model']

                # Predict actual stat value (REGRESSION)
                predicted_value = model.predict(X)[0]
                predicted_values.append(predicted_value)
                model_votes[model_name] = predicted_value

        if not predicted_values:
            return None

        # Ensemble: average predicted values
        final_predicted_value = np.mean(predicted_values)

        # Compare predicted value to market line
        if final_predicted_value > market_line:
            recommendation = 'OVER'
            edge = final_predicted_value - market_line
            over_prob = 0.6  # Placeholder for compatibility
        elif final_predicted_value < market_line:
            recommendation = 'UNDER'
            edge = market_line - final_predicted_value
            over_prob = 0.4  # Placeholder for compatibility
        else:
            recommendation = 'PASS'
            edge = 0.0
            over_prob = 0.5

        # Calculate confidence based on edge magnitude
        # Larger edges = higher confidence
        edge_pct = (edge / market_line) * 100 if market_line > 0 else 0
        confidence = min(abs(edge_pct) * 2, 100)  # Scale edge % to confidence

        # Recommendation thresholds based on edge percentage
        if abs(edge_pct) < 5.0:
            recommendation = 'PASS'

        return {
            'player_id': player_id,
            'player_name': player_name,
            'team': team,
            'opponent': opponent,
            'prop_type': prop_type,
            'market_line': market_line,
            'over_prob': over_prob,  # Keep for compatibility
            'under_prob': 1 - over_prob,  # Keep for compatibility
            'confidence': confidence,
            'edge_pct': edge_pct,
            'recommendation': recommendation,
            'predicted_value': final_predicted_value,  # NEW: actual predicted value
            'home_away': home_away
        }

    def generate_predictions(self, target_date: date):
        """
        Generate predictions for all props on target date
        """
        print(f"\n{'='*70}")
        print(f"GENERATING PREDICTIONS FOR {target_date}")
        print(f"{'='*70}\n")

        # Load team stats if not already loaded
        if not self.team_stats:
            print("[1/4] Loading team stats...")
            self.load_team_stats()
        else:
            print("[1/4] Team stats already loaded\n")

        # Get props from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT player_id, player_name, team, opponent, prop_type, market_line, home_away, bookmaker
            FROM player_props_lines
            WHERE date = ?
            AND bookmaker != 'HISTORICAL_BACKFILL'
        """, (target_date.isoformat(),))

        props = cursor.fetchall()
        print(f"[2/4] Found {len(props)} props for {target_date}\n")

        if not props:
            print("[WARN] No props found for this date")
            conn.close()
            return None

        # Generate predictions
        print(f"[3/4] Generating predictions...")
        predictions_list = []

        for player_id, player_name, team, opponent, prop_type, market_line, home_away, bookmaker in props:
            try:
                prediction = self.predict_prop(
                    player_id=player_id,
                    player_name=player_name,
                    team=team,
                    opponent=opponent,
                    prop_type=prop_type,
                    market_line=market_line,
                    home_away=home_away
                )

                if prediction:
                    predictions_list.append(prediction)

            except Exception as e:
                print(f"  [ERROR] Failed to predict {player_name} {prop_type}: {e}")

        if not predictions_list:
            conn.close()
            return None

        # Convert to DataFrame
        predictions_df = pd.DataFrame(predictions_list)

        # Save to database
        print(f"\n[4/4] Saving {len(predictions_df)} predictions to database...")

        for idx, row in predictions_df.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO player_props_predictions
                (prediction_date, game_date, player_id, player_name, team, opponent,
                 prop_type, market_line, predicted_value, confidence, edge_pct, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date.today().isoformat(),
                target_date.isoformat(),
                row['player_id'],
                row['player_name'],
                row['team'],
                row['opponent'],
                row['prop_type'],
                row['market_line'],
                row['predicted_value'],  # Store actual predicted value (regression)
                row['confidence'],
                row['edge_pct'],
                row['recommendation']
            ))

        conn.commit()
        conn.close()

        print(f"  [OK] Predictions saved!\n")

        # Display summary
        self.display_summary(predictions_df)

        return predictions_df

    def display_summary(self, predictions_df: pd.DataFrame):
        """Display prediction summary"""
        print(f"\n{'='*70}")
        print("PREDICTION SUMMARY")
        print(f"{'='*70}\n")

        # Overall stats
        total = len(predictions_df)
        over_count = len(predictions_df[predictions_df['recommendation'] == 'OVER'])
        under_count = len(predictions_df[predictions_df['recommendation'] == 'UNDER'])
        pass_count = len(predictions_df[predictions_df['recommendation'] == 'PASS'])

        print(f"Total predictions: {total}")
        print(f"  OVER: {over_count} ({over_count/total*100:.1f}%)")
        print(f"  UNDER: {under_count} ({under_count/total*100:.1f}%)")
        print(f"  PASS: {pass_count} ({pass_count/total*100:.1f}%)")

        # By prop type
        print(f"\nBreakdown by prop type:")
        for prop_type in predictions_df['prop_type'].unique():
            count = len(predictions_df[predictions_df['prop_type'] == prop_type])
            print(f"  {prop_type}: {count} predictions")

        # High confidence picks
        high_conf = predictions_df[predictions_df['confidence'] >= 20]
        print(f"\nHigh confidence picks (20%+): {len(high_conf)}")

        if len(high_conf) > 0:
            print("\nTop 10 picks:")
            top_picks = high_conf.nlargest(10, 'confidence')
            for idx, row in top_picks.iterrows():
                print(f"\n{idx+1}. {row['player_name']} - {row['prop_type'].upper()}")
                print(f"   Market Line: {row['market_line']} | Predicted: {row['predicted_value']:.1f}")
                print(f"   Recommendation: {row['recommendation']} | Edge: {row['edge_pct']:+.2f}%")
                print(f"   Confidence: {row['confidence']:.1f}% | vs {row['opponent']}")

        print(f"\n{'='*70}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Enhanced NBA Props Predictor')
    parser.add_argument('--db-path', type=str, default='data/player_props.db',
                       help='Path to props database')
    parser.add_argument('--date', type=str, default=None,
                       help='Target date (YYYY-MM-DD), default: today')

    args = parser.parse_args()

    # Parse date
    if args.date:
        target_date = date.fromisoformat(args.date)
    else:
        target_date = date.today()

    # Initialize predictor
    predictor = EnhancedPropsPredictor(db_path=args.db_path)

    # Load models
    predictor.load_models()

    if not predictor.models:
        print("[ERROR] No models loaded! Train models first:")
        print("  python backend/ml/models/nba_props_trainer_enhanced.py --prop-type all")
        return

    # Generate predictions
    predictions = predictor.generate_predictions(target_date)

    if predictions is not None:
        print(f"[SUCCESS] Generated {len(predictions)} predictions!")
    else:
        print("[ERROR] No predictions generated")


if __name__ == "__main__":
    main()
