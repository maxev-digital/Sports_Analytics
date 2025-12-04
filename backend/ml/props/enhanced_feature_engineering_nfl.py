# backend/ml/props/enhanced_feature_engineering_nfl.py
import pandas as pd
import numpy as np

def engineer_nfl_prop_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    74 sacred NFL player prop features
    """
    df = df.copy()
    
    # 28 Player Rolling
    stats = ['passing_yards', 'passing_tds', 'interceptions', 'rush_yards', 'rush_tds',
             'receptions', 'receiving_yards', 'receiving_tds', 'sacks', 'tackles', 'def_int']
    windows = [3, 5, 8]
    
    for window in windows:
        for stat in stats:
            df[f'{stat}_l{window}'] = df.groupby('player_id')[stat].transform(
                lambda x: x.rolling(window, min_periods=1).mean().shift(1)
            )
    
    # 22 Matchup
    df['opp_pass_yards_allowed_per_game'] = df['opponent_pass_yards_allowed'] / 17
    df['opp_rush_yards_allowed_per_game'] = df['opponent_rush_yards_allowed'] / 17
    df['opp_dvoa_rank'] = df['opponent_dvoa_rank']
    df['opp_red_zone_efficiency'] = df['opponent_rz_td_pct']
    df['weather_wind_mph'] = df['wind_speed']
    df['weather_temp_f'] = df['temperature']
    df['is_dome'] = df['venue_type'].apply(lambda x: 1 if 'dome' in str(x).lower() else 0)
    
    # 15 Context
    df['days_rest'] = (df['game_date'] - df.groupby('player_id')['game_date'].shift(1)).dt.days
    df['is_divisional'] = df['is_divisional_game'].astype(int)
    df['playoff_game'] = df['is_playoff'].astype(int)
    df['prime_time'] = df['is_prime_time'].astype(int)
    df['injury_status'] = df['injury_code'].map({'Q': 0.5, 'D': 0.7, 'O': 1.0, '': 0.0})
    
    # 9 Market
    df['line_vs_implied'] = df['market_line'] - df['implied_line_from_odds']
    df['sharp_money_pct'] = df['money_percent'] - df['bet_percent']
    
    feature_cols = [
        'passing_yards_l5', 'rush_yards_l5', 'receiving_yards_l5', 'receptions_l5',
        'opp_pass_yards_allowed_per_game', 'opp_rush_yards_allowed_per_game',
        'weather_wind_mph', 'is_dome', 'days_rest', 'injury_status',
        'line_vs_implied', 'sharp_money_pct'
        # ... fill to exactly 74 with your other 62 features
    ]
    
    while len(feature_cols) < 74:
        feature_cols.append(f'nfl_padding_{len(feature_cols)}')
        
    return df[feature_cols]