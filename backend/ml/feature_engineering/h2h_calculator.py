"""
H2H (Head-to-Head) Feature Calculator
CREATED: 2025-11-27

Computes recency-weighted H2H features from historical game results.
Uses auto-switching lambda based on calendar (trade deadline, season phase).

Features generated:
- h2h_weighted_avg_total: Recency-weighted average total points in H2H games
- h2h_recency_score: Sum of weights (measure of H2H data quality)
- h2h_total_bias: Difference from teams' recent averages

Run daily before predictions:
    python3 ml/feature_engineering/h2h_calculator.py
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_FILE = PROJECT_ROOT / "data" / "tracking" / "results_log_COMBINED.csv"
H2H_CACHE_FILE = PROJECT_ROOT / "data" / "cache" / "h2h_features.json"


def get_dynamic_lambda(game_date: pd.Timestamp, sport: str = "NBA") -> float:
    """
    Auto-switching recency decay parameter based on calendar.

    Early season: λ=0.95 (longer memory, rosters settling)
    Mid season: λ=1.05 (balanced)
    Pre-deadline: λ=1.15 (more recent games matter more)
    Post-deadline: λ=1.25 (new rotations, recent only)

    Args:
        game_date: Date of the game being predicted
        sport: Sport type (affects trade deadline date)

    Returns:
        Lambda value for exponential decay
    """
    if isinstance(game_date, str):
        game_date = pd.to_datetime(game_date)

    # Determine season year (Oct-Dec = start of season)
    season_year = game_date.year if game_date.month >= 10 else game_date.year - 1

    # Trade deadlines by sport
    deadlines = {
        "NBA": f"{season_year + 1}-02-08",
        "NHL": f"{season_year + 1}-03-07",
        "NFL": f"{season_year}-11-01",  # NFL is calendar year
        "NCAAB": f"{season_year + 1}-02-15",  # No trades but roster changes
        "NCAAF": f"{season_year}-10-15",
    }

    trade_deadline = pd.Timestamp(deadlines.get(sport.upper(), f"{season_year + 1}-02-08"))

    if game_date >= trade_deadline:
        return 1.25  # Post-deadline: heavy recency
    elif game_date.month >= 2:
        return 1.15  # Pre-deadline
    elif game_date.month <= 11:
        return 0.95  # Early season
    else:
        return 1.05  # Mid season


def compute_h2h_features(
    home_team: str,
    away_team: str,
    game_date: str,
    historical_df: pd.DataFrame,
    sport: str = "NBA",
    lookback_years: int = 3
) -> dict:
    """
    Compute recency-weighted H2H features for a matchup.

    Args:
        home_team: Home team name
        away_team: Away team name
        game_date: Date of the game (YYYY-MM-DD)
        historical_df: DataFrame with historical results
        sport: Sport type
        lookback_years: How many years back to look

    Returns:
        Dict with H2H features
    """
    game_date = pd.to_datetime(game_date)
    lambda_val = get_dynamic_lambda(game_date, sport)
    cutoff = game_date - pd.Timedelta(days=365 * lookback_years)

    # Find past H2H matchups (either team at home)
    mask = (
        (
            ((historical_df['home_team'] == home_team) & (historical_df['away_team'] == away_team)) |
            ((historical_df['home_team'] == away_team) & (historical_df['away_team'] == home_team))
        ) &
        (historical_df['game_date'] < game_date) &
        (historical_df['game_date'] >= cutoff) &
        (historical_df['sport'].str.upper() == sport.upper())
    )

    past_games = historical_df[mask].copy()

    # Default values if no H2H history
    if len(past_games) == 0:
        return {
            'h2h_weighted_avg_total': get_league_avg_total(sport),
            'h2h_recency_score': 0.0,
            'h2h_total_bias': 0.0,
            'h2h_games_found': 0,
            'lambda_used': lambda_val
        }

    # Sort by date and compute weights
    past_games = past_games.sort_values('game_date')
    days_ago = (game_date - past_games['game_date']).dt.days.values
    weights = np.exp(-lambda_val * days_ago / 365.0)

    # Get totals from H2H games
    totals = past_games['actual_total'].values

    # Weighted average total
    weighted_avg = np.average(totals, weights=weights)

    # Recency score (sum of weights - measure of data quality)
    recency_score = weights.sum()

    # Total bias (H2H vs league average)
    league_avg = get_league_avg_total(sport)
    total_bias = weighted_avg - league_avg

    return {
        'h2h_weighted_avg_total': round(weighted_avg, 2),
        'h2h_recency_score': round(recency_score, 3),
        'h2h_total_bias': round(total_bias, 2),
        'h2h_games_found': len(past_games),
        'lambda_used': lambda_val
    }


def get_league_avg_total(sport: str) -> float:
    """Get league average total by sport"""
    averages = {
        "NBA": 226.0,
        "NCAAB": 145.0,
        "NHL": 6.0,
        "NFL": 45.0,
        "NCAAF": 52.0
    }
    return averages.get(sport.upper(), 200.0)


def build_h2h_cache(upcoming_games: list = None) -> dict:
    """
    Build H2H feature cache for all upcoming games.

    Args:
        upcoming_games: List of dicts with home_team, away_team, game_date, sport
                       If None, generates for common matchups

    Returns:
        Dict mapping matchup keys to H2H features
    """
    logger.info("Loading historical results...")

    if not RESULTS_FILE.exists():
        logger.error(f"Results file not found: {RESULTS_FILE}")
        return {}

    df = pd.read_csv(RESULTS_FILE)
    df['game_date'] = pd.to_datetime(df['game_date'])

    # Filter to games with actual results
    df = df[df['actual_total'].notna()].copy()

    logger.info(f"Loaded {len(df)} historical games with results")

    h2h_cache = {}

    if upcoming_games:
        # Compute for specific upcoming games
        for game in upcoming_games:
            key = f"{game['sport']}_{game['away_team']}_{game['home_team']}_{game['game_date']}"
            features = compute_h2h_features(
                home_team=game['home_team'],
                away_team=game['away_team'],
                game_date=game['game_date'],
                historical_df=df,
                sport=game['sport']
            )
            h2h_cache[key] = features

            if features['h2h_games_found'] > 0:
                logger.info(f"  {key}: {features['h2h_games_found']} H2H games, "
                           f"avg total={features['h2h_weighted_avg_total']}")
    else:
        # Build cache for all unique team pairs in data
        logger.info("Building cache for all historical matchups...")

        for sport in df['sport'].unique():
            sport_df = df[df['sport'] == sport]

            # Get unique team pairs
            team_pairs = set()
            for _, row in sport_df.iterrows():
                pair = tuple(sorted([row['home_team'], row['away_team']]))
                team_pairs.add((pair, sport))

            logger.info(f"  {sport}: {len(team_pairs)} unique matchups")

            # Compute H2H for each pair (using today's date)
            today = datetime.now().strftime('%Y-%m-%d')
            for (team1, team2), sport_name in team_pairs:
                key = f"{sport_name}_{team1}_vs_{team2}"
                features = compute_h2h_features(
                    home_team=team1,
                    away_team=team2,
                    game_date=today,
                    historical_df=df,
                    sport=sport_name
                )
                h2h_cache[key] = features

    # Save cache
    H2H_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(H2H_CACHE_FILE, 'w') as f:
        json.dump(h2h_cache, f, indent=2, default=str)

    logger.info(f"Saved H2H cache with {len(h2h_cache)} entries to {H2H_CACHE_FILE}")

    return h2h_cache


def get_h2h_features(home_team: str, away_team: str, sport: str, game_date: str = None) -> dict:
    """
    Get H2H features from cache or compute on-the-fly.

    Args:
        home_team: Home team name
        away_team: Away team name
        sport: Sport type
        game_date: Game date (optional, defaults to today)

    Returns:
        Dict with H2H features
    """
    if game_date is None:
        game_date = datetime.now().strftime('%Y-%m-%d')

    # Try exact match in cache
    key = f"{sport}_{away_team}_{home_team}_{game_date}"

    if H2H_CACHE_FILE.exists():
        with open(H2H_CACHE_FILE, 'r') as f:
            cache = json.load(f)

        if key in cache:
            return cache[key]

        # Try reverse matchup key
        reverse_key = f"{sport}_{sorted([home_team, away_team])[0]}_vs_{sorted([home_team, away_team])[1]}"
        if reverse_key in cache:
            return cache[reverse_key]

    # Compute on-the-fly if not in cache
    if RESULTS_FILE.exists():
        df = pd.read_csv(RESULTS_FILE)
        df['game_date'] = pd.to_datetime(df['game_date'])
        df = df[df['actual_total'].notna()]

        return compute_h2h_features(
            home_team=home_team,
            away_team=away_team,
            game_date=game_date,
            historical_df=df,
            sport=sport
        )

    # Return defaults
    return {
        'h2h_weighted_avg_total': get_league_avg_total(sport),
        'h2h_recency_score': 0.0,
        'h2h_total_bias': 0.0,
        'h2h_games_found': 0,
        'lambda_used': 1.0
    }


if __name__ == "__main__":
    """Run daily to refresh H2H cache"""
    logger.info("=" * 60)
    logger.info("H2H FEATURE CALCULATOR")
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # Build cache for all historical matchups
    cache = build_h2h_cache()

    # Test with a sample matchup
    test_features = get_h2h_features(
        home_team="Cleveland Cavaliers",
        away_team="Milwaukee Bucks",
        sport="NBA"
    )

    logger.info("\nTest H2H lookup (Cavaliers vs Bucks):")
    for k, v in test_features.items():
        logger.info(f"  {k}: {v}")

    logger.info("\nH2H Calculator complete!")
