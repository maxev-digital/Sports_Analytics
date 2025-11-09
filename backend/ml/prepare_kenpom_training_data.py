"""
Prepare KenPom Training Data for XGBoost

Combines:
1. Historical KenPom ratings (2023, 2024, 2025)
2. Historical game results from NCAAB

Creates training dataset with actual game totals.
"""

import pandas as pd
import glob
import os


def load_kenpom_data():
    """Load all KenPom historical data"""
    kenpom_files = glob.glob("backend/data/raw/ncaab/kenpom_*.csv")

    print(f"Found {len(kenpom_files)} KenPom files:")
    for f in kenpom_files:
        print(f"  - {f}")

    # Load and combine all seasons
    all_data = []
    for file in kenpom_files:
        # Extract year from filename (kenpom_2023_*.csv)
        year = file.split('kenpom_')[-1].split('_')[0]
        if year.isdigit():
            df = pd.read_csv(file)
            df['season'] = int(year)
            all_data.append(df)
            print(f"    Loaded {len(df)} teams from {year}")

    combined = pd.concat(all_data, ignore_index=True)
    print(f"\n[OK] Total: {len(combined)} team-seasons")
    return combined


def create_mock_training_data(kenpom_df):
    """
    Create mock training data for initial XGBoost testing

    NOTE: This uses end-of-season KenPom stats paired with synthetic game results.
    For production, we'd scrape actual game results from Sports-Reference.

    For tonight's demo, this gives us something to train on!
    """

    print("\n[SETUP] Creating mock training data...")

    games = []

    # For each season
    for season in kenpom_df['season'].unique():
        season_teams = kenpom_df[kenpom_df['season'] == season].copy()

        print(f"\n  Season {season}: {len(season_teams)} teams")

        # Create synthetic matchups (top 100 teams)
        top_teams = season_teams.nsmallest(100, 'Rank')

        # Generate ~500 synthetic games per season
        for i in range(0, min(50, len(top_teams)), 2):
            for j in range(i+1, min(i+10, len(top_teams))):
                home = top_teams.iloc[i]
                away = top_teams.iloc[j]

                # Calculate expected total using KenPom formula
                avg_tempo = (home['AdjTempo'] + away['AdjTempo']) / 2
                home_expected = (home['AdjOffEff'] * avg_tempo) / 100
                away_expected = (away['AdjOffEff'] * avg_tempo) / 100
                expected_total = home_expected + away_expected

                # Add some variance (games don't always match expectations)
                import random
                actual_total = expected_total + random.uniform(-15, 15)

                game = {
                    'season': season,
                    'home_team': home['Team'],
                    'away_team': away['Team'],
                    'home_adj_em': home['AdjEM'],
                    'away_adj_em': away['AdjEM'],
                    'home_off_eff': home['AdjOffEff'],
                    'away_off_eff': away['AdjOffEff'],
                    'home_def_eff': home['AdjDefEff'],
                    'away_def_eff': away['AdjDefEff'],
                    'home_tempo': home['AdjTempo'],
                    'away_tempo': away['AdjTempo'],
                    'actual_total': actual_total
                }
                games.append(game)

        print(f"    Generated {len([g for g in games if g['season'] == season])} games")

    df = pd.DataFrame(games)
    print(f"\n[OK] Total training games: {len(df)}")

    return df


def main():
    print("="*70)
    print("PREPARE KENPOM TRAINING DATA")
    print("="*70)

    # Load KenPom data
    kenpom_df = load_kenpom_data()

    # Create training data
    training_df = create_mock_training_data(kenpom_df)

    # Save
    output_file = "backend/data/ncaab_training_data.csv"
    training_df.to_csv(output_file, index=False)

    print(f"\n[SAVED] {output_file}")
    print(f"\n[DATA SUMMARY]:")
    print(f"   Games: {len(training_df)}")
    print(f"   Seasons: {training_df['season'].unique()}")
    print(f"   Avg total: {training_df['actual_total'].mean():.1f}")
    print(f"   Total range: {training_df['actual_total'].min():.1f} - {training_df['actual_total'].max():.1f}")

    print(f"\n[READY] Ready for XGBoost training!")
    print(f"   Run: python backend/ml/ncaab_xgboost_quantile_trainer.py")

    print(f"\n[NOTE] This uses end-of-season KenPom stats + synthetic games")
    print(f"   For production, we'd scrape actual game results from Sports-Reference")
    print(f"   But this is good enough for initial model training tonight!")


if __name__ == "__main__":
    main()
