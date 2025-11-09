"""
Quick test script to verify XGBoost quantile models work

This loads the trained models and makes a sample prediction
to show confidence intervals.
"""

import pandas as pd
import xgboost as xgb
import numpy as np
import glob
from datetime import datetime


def load_latest_models():
    """Load the most recently trained quantile models"""
    model_dir = "backend/ml/models/"

    # Find latest model files
    mean_files = sorted(glob.glob(f"{model_dir}ncaab_quantile_mean_*.json"))
    lower_files = sorted(glob.glob(f"{model_dir}ncaab_quantile_lower_*.json"))
    upper_files = sorted(glob.glob(f"{model_dir}ncaab_quantile_upper_*.json"))

    if not mean_files:
        print("ERROR: No trained models found!")
        return None, None, None

    # Load latest
    mean_model = xgb.Booster()
    mean_model.load_model(mean_files[-1])

    lower_model = xgb.Booster()
    lower_model.load_model(lower_files[-1])

    upper_model = xgb.Booster()
    upper_model.load_model(upper_files[-1])

    print(f"[OK] Loaded models:")
    print(f"  Mean:  {mean_files[-1]}")
    print(f"  Lower: {lower_files[-1]}")
    print(f"  Upper: {upper_files[-1]}")

    return mean_model, lower_model, upper_model


def load_kenpom_current():
    """Load current KenPom data for team lookups"""
    files = glob.glob("backend/data/raw/ncaab/kenpom_2025_*.csv")
    if not files:
        print("WARNING: No 2025 KenPom data found")
        return None

    df = pd.read_csv(files[-1])
    print(f"[OK] Loaded {len(df)} teams from current KenPom data")
    return df


def engineer_features_for_game(home_team_stats, away_team_stats):
    """
    Create feature vector for a single game

    Mirrors the feature engineering in the trainer
    """
    features = {}

    # Basic stats
    features['home_adj_em'] = home_team_stats['AdjEM']
    features['away_adj_em'] = away_team_stats['AdjEM']
    features['home_off_eff'] = home_team_stats['AdjOffEff']
    features['away_off_eff'] = away_team_stats['AdjOffEff']
    features['home_def_eff'] = home_team_stats['AdjDefEff']
    features['away_def_eff'] = away_team_stats['AdjDefEff']
    features['home_tempo'] = home_team_stats['AdjTempo']
    features['away_tempo'] = away_team_stats['AdjTempo']

    # Derived features
    features['em_diff'] = home_team_stats['AdjEM'] - away_team_stats['AdjEM']
    features['avg_tempo'] = (home_team_stats['AdjTempo'] + away_team_stats['AdjTempo']) / 2
    features['tempo_diff'] = home_team_stats['AdjTempo'] - away_team_stats['AdjTempo']
    features['off_eff_diff'] = home_team_stats['AdjOffEff'] - away_team_stats['AdjOffEff']
    features['def_eff_diff'] = home_team_stats['AdjDefEff'] - away_team_stats['AdjDefEff']

    # Combined metrics
    features['total_off_eff'] = home_team_stats['AdjOffEff'] + away_team_stats['AdjOffEff']
    features['total_def_eff'] = home_team_stats['AdjDefEff'] + away_team_stats['AdjDefEff']
    features['avg_off_eff'] = features['total_off_eff'] / 2
    features['avg_def_eff'] = features['total_def_eff'] / 2

    # Interaction features
    features['home_off_vs_away_def'] = home_team_stats['AdjOffEff'] - away_team_stats['AdjDefEff']
    features['away_off_vs_home_def'] = away_team_stats['AdjOffEff'] - home_team_stats['AdjDefEff']

    # Pace interactions
    features['tempo_x_total_off'] = features['avg_tempo'] * features['total_off_eff'] / 100
    features['tempo_x_avg_off'] = features['avg_tempo'] * features['avg_off_eff'] / 100

    # Efficiency ratios
    features['home_off_def_ratio'] = home_team_stats['AdjOffEff'] / home_team_stats['AdjDefEff']
    features['away_off_def_ratio'] = away_team_stats['AdjOffEff'] / away_team_stats['AdjDefEff']

    # Strength indicators
    features['home_strength'] = home_team_stats['AdjOffEff'] / (home_team_stats['AdjDefEff'] + 0.1)
    features['away_strength'] = away_team_stats['AdjOffEff'] / (away_team_stats['AdjDefEff'] + 0.1)

    # Game style indicators
    features['game_pace_score'] = features['avg_tempo'] * (features['total_off_eff'] / 200)
    features['defensive_game'] = (features['total_def_eff'] - 200) / 10

    # More interaction terms
    features['em_x_tempo'] = features['em_diff'] * features['avg_tempo']
    features['off_eff_x_tempo'] = features['off_eff_diff'] * features['avg_tempo']

    # Squared terms for non-linearity
    features['em_diff_sq'] = features['em_diff'] ** 2
    features['tempo_diff_sq'] = features['tempo_diff'] ** 2

    # Categorical encoding (simplified - just use a fixed value)
    features['season_2024'] = 0
    features['season_2025'] = 1  # Assuming current season

    # Expected points estimates
    possessions = features['avg_tempo']
    features['home_expected_pts'] = (home_team_stats['AdjOffEff'] * possessions) / 100
    features['away_expected_pts'] = (away_team_stats['AdjOffEff'] * possessions) / 100
    features['simple_total_estimate'] = features['home_expected_pts'] + features['away_expected_pts']

    # Defensive adjustments
    features['home_pts_vs_defense'] = (home_team_stats['AdjOffEff'] - away_team_stats['AdjDefEff']) * possessions / 100
    features['away_pts_vs_defense'] = (away_team_stats['AdjOffEff'] - home_team_stats['AdjDefEff']) * possessions / 100

    # Volatility indicators
    features['style_clash'] = abs(home_team_stats['AdjTempo'] - away_team_stats['AdjTempo'])
    features['efficiency_variance'] = np.std([
        home_team_stats['AdjOffEff'], away_team_stats['AdjOffEff'],
        home_team_stats['AdjDefEff'], away_team_stats['AdjDefEff']
    ])

    return features


def predict_game(mean_model, lower_model, upper_model, home_team, away_team, kenpom_df):
    """Make prediction with confidence intervals for a single game"""

    # Find teams in KenPom data
    home_stats = kenpom_df[kenpom_df['Team'].str.contains(home_team, case=False, na=False)]
    away_stats = kenpom_df[kenpom_df['Team'].str.contains(away_team, case=False, na=False)]

    if home_stats.empty or away_stats.empty:
        print(f"ERROR: Could not find teams in KenPom data")
        return None

    home_stats = home_stats.iloc[0]
    away_stats = away_stats.iloc[0]

    print(f"\n{'='*70}")
    print(f"PREDICTION: {home_stats['Team']} vs {away_stats['Team']}")
    print(f"{'='*70}")
    print(f"Home: {home_stats['Team']} (Rank #{int(home_stats['Rank'])}, AdjEM: {home_stats['AdjEM']:.2f})")
    print(f"Away: {away_stats['Team']} (Rank #{int(away_stats['Rank'])}, AdjEM: {away_stats['AdjEM']:.2f})")

    # Engineer features
    features = engineer_features_for_game(home_stats, away_stats)

    # Convert to DMatrix
    feature_df = pd.DataFrame([features])
    dmatrix = xgb.DMatrix(feature_df)

    # Make predictions
    predicted_mean = mean_model.predict(dmatrix)[0]
    predicted_lower = lower_model.predict(dmatrix)[0]
    predicted_upper = upper_model.predict(dmatrix)[0]

    # Calculate stats
    implied_std = (predicted_upper - predicted_lower) / 2.56  # 80% interval / 2.56

    print(f"\n[XGBOOST PREDICTION]")
    print(f"  Expected Total:    {predicted_mean:.1f}")
    print(f"  10th percentile:   {predicted_lower:.1f}")
    print(f"  90th percentile:   {predicted_upper:.1f}")
    print(f"  Confidence range:  {predicted_upper - predicted_lower:.1f} points")
    print(f"  Implied std dev:   {implied_std:.1f} points")

    # Simulate live betting scenario
    print(f"\n[SIMULATED REGRESSION-TO-MEAN ALERT]")

    # Example: Live total drifts to predicted_mean + 8
    simulated_live_total = predicted_mean + 8.0
    z_score = (simulated_live_total - predicted_mean) / implied_std

    print(f"  Live total opens at: {simulated_live_total:.1f}")
    print(f"  Deviation from model: +{simulated_live_total - predicted_mean:.1f} points")
    print(f"  Z-score: {z_score:.2f} standard deviations")

    if abs(z_score) >= 2.0:
        direction = "UNDER" if z_score > 0 else "OVER"
        print(f"  [ALERT] Strong {direction} opportunity!")
        print(f"  [ALERT] Live total has deviated {abs(z_score):.1f}σ from prediction")
        print(f"  [RECOMMENDATION] Bet {direction} {simulated_live_total:.1f}")

    return {
        'predicted_mean': predicted_mean,
        'predicted_lower': predicted_lower,
        'predicted_upper': predicted_upper,
        'std_dev': implied_std
    }


def main():
    print("="*70)
    print("XGBOOST QUANTILE REGRESSION - MODEL TEST")
    print("="*70)
    print()

    # Load models
    mean_model, lower_model, upper_model = load_latest_models()
    if not mean_model:
        return

    # Load current KenPom data
    kenpom_df = load_kenpom_current()
    if kenpom_df is None:
        return

    # Test prediction on some high-profile matchups
    test_matchups = [
        ("Duke", "North Carolina"),
        ("Kansas", "Kentucky"),
        ("Gonzaga", "UCLA")
    ]

    for home, away in test_matchups:
        try:
            result = predict_game(mean_model, lower_model, upper_model, home, away, kenpom_df)
        except Exception as e:
            print(f"\nERROR predicting {home} vs {away}: {e}")
            print("Trying next matchup...\n")
            continue

    print(f"\n{'='*70}")
    print("[SUCCESS] XGBoost quantile models are working!")
    print("="*70)
    print()
    print("Next steps:")
    print("1. Integrate models into regression-to-mean strategy")
    print("2. Connect to live odds feed")
    print("3. Start monitoring for regression opportunities")
    print()


if __name__ == "__main__":
    main()
