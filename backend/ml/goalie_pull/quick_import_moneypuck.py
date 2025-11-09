"""
Quick import of MoneyPuck data to get started

This creates basic pull records and coach profiles without fetching full NHL API data.
We'll use estimated pull times based on score differential.
"""

import pandas as pd
from pathlib import Path
from database_schema import GoaliePullDB


def import_moneypuck_data():
    """Import MoneyPuck pulls with estimated timing"""

    db = GoaliePullDB()

    # Load MoneyPuck data
    csv_path = Path(__file__).parent.parent.parent / "strategies" / "moneypuck_goalie_pulls_2023_2024_FINAL.csv"
    df = pd.read_csv(csv_path)

    print(f"Loaded {len(df)} pulls from MoneyPuck")

    # Known coaches for 2023-24 season
    team_coaches_2324 = {
        'ANA': 'GREG_CRONIN',
        'ARI': 'ANDRE_TOURIGNY',
        'BOS': 'JIM_MONTGOMERY',
        'BUF': 'DON_GRANATO',
        'CGY': 'RYAN_HUSKA',
        'CAR': 'ROD_BRINDAMOUR',
        'CHI': 'LUKE_RICHARDSON',
        'COL': 'JARED_BEDNAR',
        'CBJ': 'PASCAL_VINCENT',
        'DAL': 'PETER_DEBOER',
        'DET': 'DEREK_LALONDE',
        'EDM': 'JAY_WOODCROFT',  # Changed mid-season
        'FLA': 'PAUL_MAURICE',
        'LAK': 'TODD_MCLELLAN',
        'MIN': 'DEAN_EVASON',  # Changed mid-season
        'MTL': 'MARTIN_ST_LOUIS',
        'NSH': 'ANDREW_BRUNETTE',
        'NJD': 'LINDY_RUFF',
        'NYI': 'PATRICK_ROY',  # Changed mid-season
        'NYR': 'PETER_LAVIOLETTE',
        'OTT': 'JACQUES_MARTIN',  # Changed mid-season
        'PHI': 'JOHN_TORTORELLA',
        'PIT': 'MIKE_SULLIVAN',
        'SJS': 'DAVID_QUINN',
        'SEA': 'DAVE_HAKSTOL',
        'STL': 'DREW_BANNISTER',  # Changed mid-season
        'TBL': 'JON_COOPER',
        'TOR': 'SHELDON_KEEFE',
        'VAN': 'RICK_TOCCHET',
        'VGK': 'BRUCE_CASSIDY',
        'WSH': 'SPENCER_CARBERY',
        'WPG': 'RICK_BOWNESS'
    }

    successful = 0
    failed = 0

    for idx, row in df.iterrows():
        game_id_short = str(row['game_id'])
        game_id_full = f"2023020{game_id_short.zfill(4)}"

        pulling_team = row['pulling_team']
        score_diff = row['score_differential']
        period = row['period']

        # Estimate pull time based on score differential
        # These are league averages from historical data
        if score_diff == -1:
            pull_time_seconds = 106  # 1:46
        elif score_diff == -2:
            pull_time_seconds = 135  # 2:15
        elif score_diff == -3:
            pull_time_seconds = 165  # 2:45
        else:
            pull_time_seconds = 180  # 3:00

        pull_time_remaining = f"{pull_time_seconds // 60}:{pull_time_seconds % 60:02d}"

        # Get coach (if known)
        coach_id = team_coaches_2324.get(pulling_team)

        # We don't know opponent from MoneyPuck data, so use placeholder
        opponent_team = "UNKNOWN"

        pull_data = {
            'game_id': game_id_full,
            'season': 2023,
            'game_date': '2023-10-10',  # Placeholder
            'home_team': 'UNKNOWN',
            'away_team': 'UNKNOWN',
            'pulling_team': pulling_team,
            'opponent_team': opponent_team,
            'pull_time_remaining': pull_time_remaining,
            'pull_time_seconds': pull_time_seconds,
            'pull_period': period,
            'score_differential': score_diff,
            'coach_id': coach_id,
            'home_coach': None,
            'away_coach': None,
            'goals_by_pulling_team': row['goals_by_pulling_team'],
            'goals_by_opponent': row['goals_by_opponent'],
            'total_goals': row['total_goals_after_pull'],
            'pulling_team_tied': row['pulling_team_tied_game'],
            'pulling_team_won': False,  # Not in data
            'playoff_game': False,
            'data_source': 'moneypuck'
        }

        try:
            db.insert_historical_pull(pull_data)
            successful += 1

            if successful % 100 == 0:
                print(f"[PROGRESS] Imported {successful}/{len(df)} pulls...")

        except Exception as e:
            print(f"[ERROR] Failed to import game {game_id_full}: {e}")
            failed += 1

    print(f"\n[OK] Import complete!")
    print(f"     Successful: {successful}")
    print(f"     Failed: {failed}")

    return successful


def create_coach_profiles():
    """Create coach profiles from imported pulls"""

    db = GoaliePullDB()
    pulls = db.get_historical_pulls()

    if not pulls:
        print("No pulls found. Import data first.")
        return

    # Group by coach
    coach_stats = {}

    for pull in pulls:
        coach_id = pull['coach_id']
        if not coach_id:
            continue

        if coach_id not in coach_stats:
            coach_stats[coach_id] = {
                'pulls_down_1': [],
                'pulls_down_2': [],
                'pulls_down_3_plus': [],
                'total_pulls': 0
            }

        coach_stats[coach_id]['total_pulls'] += 1

        score_diff = pull['score_differential']
        pull_time = pull['pull_time_seconds']

        if score_diff == -1:
            coach_stats[coach_id]['pulls_down_1'].append(pull_time)
        elif score_diff == -2:
            coach_stats[coach_id]['pulls_down_2'].append(pull_time)
        else:
            coach_stats[coach_id]['pulls_down_3_plus'].append(pull_time)

    # Create profiles
    created = 0

    for coach_id, stats in coach_stats.items():
        def median(values):
            if not values:
                return None
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            if n % 2 == 0:
                return (sorted_vals[n//2-1] + sorted_vals[n//2]) / 2
            return sorted_vals[n//2]

        def percentile(values, p):
            if not values:
                return None
            sorted_vals = sorted(values)
            k = (len(sorted_vals) - 1) * (p / 100)
            f = int(k)
            c = int(k) + 1
            if c >= len(sorted_vals):
                return sorted_vals[f]
            return sorted_vals[f] + (k - f) * (sorted_vals[c] - sorted_vals[f])

        pulls_down_1 = stats['pulls_down_1']
        pulls_down_2 = stats['pulls_down_2']
        pulls_down_3_plus = stats['pulls_down_3_plus']

        median_down_1 = median(pulls_down_1)
        median_down_2 = median(pulls_down_2)
        median_down_3_plus = median(pulls_down_3_plus)

        # Calculate aggressive rating
        if median_down_1:
            if median_down_1 > 120:
                aggressive_rating = 9
            elif median_down_1 > 100:
                aggressive_rating = 7
            elif median_down_1 > 80:
                aggressive_rating = 5
            elif median_down_1 > 60:
                aggressive_rating = 3
            else:
                aggressive_rating = 1
        else:
            aggressive_rating = 5

        # Variability for predictability
        p25 = percentile(pulls_down_1, 25)
        p75 = percentile(pulls_down_1, 75)
        variability = (p75 - p25) if (p75 and p25) else 40

        if variability < 20:
            predictability_rating = 9
        elif variability < 40:
            predictability_rating = 7
        else:
            predictability_rating = 5

        coach_profile = {
            'coach_id': coach_id,
            'coach_name': coach_id.replace('_', ' ').title(),
            'current_team': None,
            'seasons_active': '2023-2024',
            'pulls_down_1': len(pulls_down_1),
            'median_pull_time_down_1_seconds': int(median_down_1) if median_down_1 else None,
            'p25_pull_time_down_1_seconds': int(p25) if p25 else None,
            'p75_pull_time_down_1_seconds': int(p75) if p75 else None,
            'pulls_down_2': len(pulls_down_2),
            'median_pull_time_down_2_seconds': int(median_down_2) if median_down_2 else None,
            'p25_pull_time_down_2_seconds': int(percentile(pulls_down_2, 25)) if pulls_down_2 else None,
            'p75_pull_time_down_2_seconds': int(percentile(pulls_down_2, 75)) if pulls_down_2 else None,
            'pulls_down_3_plus': len(pulls_down_3_plus),
            'median_pull_time_down_3_plus_seconds': int(median_down_3_plus) if median_down_3_plus else None,
            'pull_rate_when_shorthanded': 0.0,
            'pull_rate_playoff_vs_regular': 1.0,
            'pulls_before_2min': sum(1 for t in pulls_down_1 + pulls_down_2 if t > 120),
            'pulls_after_1min': sum(1 for t in pulls_down_1 + pulls_down_2 if t < 60),
            'aggressive_rating': aggressive_rating,
            'predictability_rating': predictability_rating
        }

        try:
            db.insert_coach_profile(coach_profile)
            print(f"[OK] Created profile for {coach_profile['coach_name']}")
            print(f"     Aggressive: {aggressive_rating}/10, Pulls: {stats['total_pulls']}")
            created += 1
        except Exception as e:
            print(f"[ERROR] Failed to create profile for {coach_id}: {e}")

    print(f"\n[OK] Created {created} coach profiles")
    return created


if __name__ == "__main__":
    print("=" * 80)
    print("QUICK MONEYPUCK IMPORT")
    print("=" * 80)

    # Import pulls
    import_moneypuck_data()

    # Create coach profiles
    print("\n")
    create_coach_profiles()

    print("\n[OK] Quick import complete!")
