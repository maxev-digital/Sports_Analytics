"""
Create sample NHL training data for testing

This creates synthetic NHL data so we can demonstrate the training pipeline working
"""

import pandas as pd
import numpy as np
from pathlib import Path

def create_sample_nhl_data(n_games=1000):
    """Create sample NHL training data"""

    np.random.seed(42)

    data = []

    teams = ['tor', 'mtl', 'bos', 'nyr', 'edm', 'cgy', 'van', 'wpg',
             'det', 'chi', 'pit', 'was', 'phi', 'nj', 'car', 'tb',
             'fla', 'dal', 'col', 'vgk', 'la', 'sj', 'ana', 'sea',
             'min', 'stl', 'nsh', 'ari', 'ott', 'buf', 'cbj', 'nyi']

    for i in range(n_games):
        # Random teams
        home_team = np.random.choice(teams)
        away_team = np.random.choice([t for t in teams if t != home_team])

        # Team stats (realistic NHL ranges)
        home_gpg = np.random.uniform(2.5, 3.8)
        away_gpg = np.random.uniform(2.5, 3.8)
        home_gapg = np.random.uniform(2.5, 3.8)
        away_gapg = np.random.uniform(2.5, 3.8)

        # Generate game outcome based on team strength
        home_advantage = 0.3
        expected_home = max(1.5, home_gpg - (away_gapg - 3.0) + home_advantage)
        expected_away = max(1.5, away_gpg - (home_gapg - 3.0))

        # Add randomness
        home_score = max(0, int(np.random.poisson(expected_home)))
        away_score = max(0, int(np.random.poisson(expected_away)))

        row = {
            'game_id': f'2024020{str(i).zfill(4)}',
            'date': f'2024-{np.random.randint(10,12):02d}-{np.random.randint(1,28):02d}',
            'season': '20242025',
            'home_team': home_team,
            'away_team': away_team,

            # Home stats
            'home_goals_per_game': home_gpg,
            'home_goals_against_per_game': home_gapg,
            'home_shots_per_game': np.random.uniform(28, 34),
            'home_shots_against_per_game': np.random.uniform(28, 34),
            'home_power_play_pct': np.random.uniform(15, 28),
            'home_penalty_kill_pct': np.random.uniform(75, 85),
            'home_faceoff_win_pct': np.random.uniform(47, 53),
            'home_shooting_pct': np.random.uniform(8, 12),
            'home_save_pct': np.random.uniform(0.900, 0.920),
            'home_pdo': np.random.uniform(98, 102),
            'home_win_pct': np.random.uniform(0.35, 0.65),

            # Away stats
            'away_goals_per_game': away_gpg,
            'away_goals_against_per_game': away_gapg,
            'away_shots_per_game': np.random.uniform(28, 34),
            'away_shots_against_per_game': np.random.uniform(28, 34),
            'away_power_play_pct': np.random.uniform(15, 28),
            'away_penalty_kill_pct': np.random.uniform(75, 85),
            'away_faceoff_win_pct': np.random.uniform(47, 53),
            'away_shooting_pct': np.random.uniform(8, 12),
            'away_save_pct': np.random.uniform(0.900, 0.920),
            'away_pdo': np.random.uniform(98, 102),
            'away_win_pct': np.random.uniform(0.35, 0.65),

            # Targets
            'home_score': home_score,
            'away_score': away_score,
            'total': home_score + away_score,
            'home_margin': home_score - away_score,
            'home_win': 1 if home_score > away_score else 0
        }

        data.append(row)

    df = pd.DataFrame(data)

    # Save to CSV
    output_dir = Path(__file__).parent.parent.parent / "data" / "historical" / "nhl"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "sample_training_data.csv"
    df.to_csv(output_file, index=False)

    print(f"Created {len(df)} sample games")
    print(f"Saved to: {output_file}")
    print(f"\nSample stats:")
    print(f"  Average total: {df['total'].mean():.2f}")
    print(f"  Home win %: {df['home_win'].mean():.1%}")
    print(f"  Average margin: {df['home_margin'].mean():.2f}")

    return df


if __name__ == "__main__":
    create_sample_nhl_data(n_games=1000)
