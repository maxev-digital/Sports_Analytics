"""
NBA First Half (1H) Feature Engineering
CREATED: 2025-11-28

Extracts features specifically for first half totals prediction.
Uses 1H-specific team averages and H2H data.

Feature count: 27 features
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)

# League averages for 1H
NBA_AVG_1H_TOTAL = 113.0
NBA_AVG_PACE = 99.0
NBA_AVG_OFF_RATING = 113.0
NBA_AVG_DEF_RATING = 113.0
NBA_AVG_USAGE = 20.0

# Feature column order (must match model training)
FEATURE_COLUMNS_1H = [
    "home_pace", "away_pace",
    "home_off_rating", "away_off_rating",
    "home_def_rating", "away_def_rating",
    "home_rest_days", "away_rest_days",
    "home_b2b", "away_b2b",
    "home_last5_avg_1h_total", "away_last5_avg_1h_total",
    "home_key_injuries", "away_key_injuries",
    "home_team_usage", "away_team_usage",
    "h2h_weighted_avg_1h_total", "h2h_recency_score_1h", "h2h_1h_bias",
    "pace_diff", "off_def_matchup_home", "off_def_matchup_away",
    "rest_diff", "injury_diff", "total_injuries",
    "usage_diff", "avg_team_usage"
]


def engineer_1h_features(row: pd.Series) -> np.ndarray:
    """Extract 27 features for 1H totals prediction"""
    features = np.zeros(27)

    # Basic team stats [0-5]
    home_pace = row.get("home_pace", NBA_AVG_PACE)
    away_pace = row.get("away_pace", NBA_AVG_PACE)
    home_off = row.get("home_off_rating", NBA_AVG_OFF_RATING)
    away_off = row.get("away_off_rating", NBA_AVG_OFF_RATING)
    home_def = row.get("home_def_rating", NBA_AVG_DEF_RATING)
    away_def = row.get("away_def_rating", NBA_AVG_DEF_RATING)

    features[0] = home_pace
    features[1] = away_pace
    features[2] = home_off
    features[3] = away_off
    features[4] = home_def
    features[5] = away_def

    # Rest days and B2B [6-9]
    features[6] = row.get("home_rest_days", 1.0)
    features[7] = row.get("away_rest_days", 1.0)
    features[8] = 1.0 if row.get("home_b2b", False) else 0.0
    features[9] = 1.0 if row.get("away_b2b", False) else 0.0

    # 1H-specific team averages [10-11]
    features[10] = row.get("home_last5_avg_1h_total", NBA_AVG_1H_TOTAL)
    features[11] = row.get("away_last5_avg_1h_total", NBA_AVG_1H_TOTAL)

    # Injuries [12-13]
    features[12] = row.get("home_key_injuries", 0.0)
    features[13] = row.get("away_key_injuries", 0.0)

    # Usage [14-15]
    home_usage = row.get("home_team_usage", NBA_AVG_USAGE)
    away_usage = row.get("away_team_usage", NBA_AVG_USAGE)
    features[14] = home_usage
    features[15] = away_usage

    # 1H-specific H2H features [16-18]
    features[16] = row.get("h2h_weighted_avg_1h_total", NBA_AVG_1H_TOTAL)
    features[17] = row.get("h2h_recency_score_1h", 0.0)
    features[18] = row.get("h2h_1h_bias", 0.0)

    # Derived features [19-26]
    features[19] = home_pace - away_pace  # pace_diff
    features[20] = home_off - away_def  # off_def_matchup_home
    features[21] = away_off - home_def  # off_def_matchup_away
    features[22] = features[6] - features[7]  # rest_diff
    features[23] = features[12] - features[13]  # injury_diff
    features[24] = features[12] + features[13]  # total_injuries
    features[25] = home_usage - away_usage  # usage_diff
    features[26] = (home_usage + away_usage) / 2  # avg_team_usage

    return features.reshape(1, -1)


def enrich_game_with_1h_features(game_data: Dict, home_abbr: str, away_abbr: str) -> Dict:
    """Enrich game data with 1H-specific features from cache files"""
    
    # Add 1H team averages
    try:
        from ml.feature_engineering.nba_1h_averages import get_cached_1h_averages
        h1_avgs = get_cached_1h_averages(home_abbr, away_abbr)
        game_data["home_last5_avg_1h_total"] = h1_avgs.get("home_avg", NBA_AVG_1H_TOTAL)
        game_data["away_last5_avg_1h_total"] = h1_avgs.get("away_avg", NBA_AVG_1H_TOTAL)
    except Exception as e:
        logger.warning(f"Could not load 1H team averages: {e}")
        game_data["home_last5_avg_1h_total"] = NBA_AVG_1H_TOTAL
        game_data["away_last5_avg_1h_total"] = NBA_AVG_1H_TOTAL

    # Add 1H H2H features (use regular H2H as proxy for now)
    try:
        cache_file = Path(__file__).parent.parent.parent / "data" / "cache" / "h2h_features.json"
        if cache_file.exists():
            with open(cache_file, "r") as f:
                h2h_cache = json.load(f)
            
            key = f"{home_abbr}_{away_abbr}"
            alt_key = f"{away_abbr}_{home_abbr}"
            
            if key in h2h_cache:
                h2h = h2h_cache[key]
                # Estimate 1H as ~48% of full game total
                game_data["h2h_weighted_avg_1h_total"] = h2h.get("h2h_weighted_avg_total", 226.0) * 0.48
                game_data["h2h_recency_score_1h"] = h2h.get("h2h_recency_score", 0.0)
                game_data["h2h_1h_bias"] = h2h.get("h2h_total_bias", 0.0) * 0.48
            elif alt_key in h2h_cache:
                h2h = h2h_cache[alt_key]
                game_data["h2h_weighted_avg_1h_total"] = h2h.get("h2h_weighted_avg_total", 226.0) * 0.48
                game_data["h2h_recency_score_1h"] = h2h.get("h2h_recency_score", 0.0)
                game_data["h2h_1h_bias"] = h2h.get("h2h_total_bias", 0.0) * 0.48
            else:
                game_data["h2h_weighted_avg_1h_total"] = NBA_AVG_1H_TOTAL
                game_data["h2h_recency_score_1h"] = 0.0
                game_data["h2h_1h_bias"] = 0.0
    except Exception as e:
        logger.warning(f"Could not load 1H H2H features: {e}")
        game_data["h2h_weighted_avg_1h_total"] = NBA_AVG_1H_TOTAL
        game_data["h2h_recency_score_1h"] = 0.0
        game_data["h2h_1h_bias"] = 0.0

    return game_data


def get_1h_feature_names() -> List[str]:
    """Get list of feature names in order"""
    return FEATURE_COLUMNS_1H.copy()


if __name__ == "__main__":
    print("NBA 1H Feature Engineering - Test")
    print(f"Feature count: {len(FEATURE_COLUMNS_1H)}")
    for i, name in enumerate(FEATURE_COLUMNS_1H):
        print(f"  [{i}] {name}")
