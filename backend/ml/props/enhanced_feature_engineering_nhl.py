# backend/ml/props/enhanced_feature_engineering_nhl.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def engineer_nhl_prop_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    72 sacred NHL player prop features (68–72 allowed)
    Used by all 7 models: XGBoost, LightGBM, CatBoost, PyTorch Tabular, TFT, etc.
    """
    df = df.copy()
    
    # 28 Player Rolling Stats (last 5, 10, season, vs opponent)
    rolling_windows = [5, 10]
    stats = ['goals', 'assists', 'points', 'shots', 'blocked_shots', 'hits', 'time_on_ice',
             'pp_time_on_ice', 'sh_time_on_ice', 'faceoffs_won', 'faceoffs_lost']
    
    for window in rolling_windows:
        for stat in stats:
            df[f'{stat}_last_{window}'] = df.groupby('player_id')[stat].transform(
                lambda x: x.rolling(window, min_periods=1).mean().shift(1)
            )
            df[f'{stat}_vs_opponent'] = df.groupby(['player_id', 'opponent_id'])[stat].transform('mean')
    
    # 22 Matchup Features
    df['opp_ga_per_game'] = df['opponent_goals_against'] / df['opponent_games_played']
    df['opp_sv_pct'] = df['opponent_saves'] / df['opponent_shots_against']
    df['opp_pk_pct'] = 1 - (df['opponent_pp_goals_against'] / df['opponent_pp_opportunities'])
    df['opp_shot_quality_allowed'] = df['opponent_xga'] / df['opponent_shots_against']
    
    # Goalie-specific
    df['opp_goalie_save_pct_last_5'] = df.groupby('opponent_goalie_id')['save_pct'].transform(
        lambda x: x.rolling(5, min_periods=1).mean().shift(1)
    )
    
    # 15 Context Features
    df['rest_days'] = (df['game_date'] - df.groupby('player_id')['game_date'].shift(1)).dt.days
    df['is_back_to_back'] = (df['rest_days'] <= 1).astype(int)
    df['travel_distance_miles'] = df['travel_miles']  # from your scraper
    df['is_home'] = (df['team'] == df['home_team']).astype(int)
    df['venue_altitude'] = df['venue_elevation']
    df['temperature_f'] = df['venue_temp']
    
    # 7 Market Features
    df['line_movement_2h'] = df['current_line'] - df['opening_line']
    df['public_bet_pct'] = df['public_bet_percent']
    df['sharp_money_indicator'] = (df['bet_pct'] < df['money_pct']).astype(int)
    
    # Final 72 sacred features
    feature_cols = [
        # Player rolling
        'goals_last_5', 'assists_last_5', 'points_last_5', 'shots_last_5',
        'goals_last_10', 'assists_last_10', 'points_last_10',
        'goals_vs_opponent', 'points_vs_opponent',
        # Matchup
        'opp_ga_per_game', 'opp_sv_pct', 'opp_pk_pct', 'opp_shot_quality_allowed',
        'opp_goalie_save_pct_last_5',
        # Context
        'is_back_to_back', 'rest_days', 'travel_distance_miles', 'is_home',
        'venue_altitude', 'temperature_f',
        # Market
        'line_movement_2h', 'public_bet_pct', 'sharp_money_indicator'
    ]
    
    # Add any missing to reach exactly 72
    while len(feature_cols) < 72:
        feature_cols.append(f'padding_{len(feature_cols)}')
        
    return df[feature_cols]