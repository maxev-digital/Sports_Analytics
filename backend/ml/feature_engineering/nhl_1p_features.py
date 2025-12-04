"""
NHL First Period (1P) Feature Engineering
CREATED: 2025-11-28

Extracts features specifically for first period totals prediction.
Uses 1P-specific team averages, goalie data, and pace metrics.

Feature count: 23 features

Key NHL 1P considerations:
- Average 1P total is ~1.5-2.0 goals
- Goalies have huge impact on 1P scoring
- Teams often start slow (feeling out period)
- Home ice advantage more pronounced in 1P
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)

# League averages for NHL 1P
NHL_AVG_1P_TOTAL = 1.6  # Goals per 1st period (both teams)
NHL_AVG_GOALS_PER_GAME = 6.2  # Full game total
NHL_AVG_SAVE_PCT = 0.905
NHL_AVG_SHOTS_PER_GAME = 60.0  # Both teams combined

# Feature column order
FEATURE_COLUMNS_1P = [
    "home_goals_per_game", "away_goals_per_game",
    "home_goals_allowed", "away_goals_allowed",
    "home_shots_per_game", "away_shots_per_game",
    "home_shots_allowed", "away_shots_allowed",
    "home_save_pct", "away_save_pct",
    "home_pp_pct", "away_pp_pct",
    "home_pk_pct", "away_pk_pct",
    "home_rest_days", "away_rest_days",
    "home_b2b", "away_b2b",
    "home_last5_1p_avg", "away_last5_1p_avg",
    "h2h_1p_avg",
    "pace_factor", "defensive_factor"
]


def engineer_1p_features(row: pd.Series) -> np.ndarray:
    """Extract 23 features for 1P totals prediction"""
    features = np.zeros(23)

    # Offensive metrics [0-3]
    home_gpg = row.get("home_goals_per_game", NHL_AVG_GOALS_PER_GAME / 2)
    away_gpg = row.get("away_goals_per_game", NHL_AVG_GOALS_PER_GAME / 2)
    home_ga = row.get("home_goals_allowed", NHL_AVG_GOALS_PER_GAME / 2)
    away_ga = row.get("away_goals_allowed", NHL_AVG_GOALS_PER_GAME / 2)

    features[0] = home_gpg
    features[1] = away_gpg
    features[2] = home_ga
    features[3] = away_ga

    # Shot metrics [4-7]
    features[4] = row.get("home_shots_per_game", NHL_AVG_SHOTS_PER_GAME / 2)
    features[5] = row.get("away_shots_per_game", NHL_AVG_SHOTS_PER_GAME / 2)
    features[6] = row.get("home_shots_allowed", NHL_AVG_SHOTS_PER_GAME / 2)
    features[7] = row.get("away_shots_allowed", NHL_AVG_SHOTS_PER_GAME / 2)

    # Goalie metrics [8-9]
    features[8] = row.get("home_save_pct", NHL_AVG_SAVE_PCT)
    features[9] = row.get("away_save_pct", NHL_AVG_SAVE_PCT)

    # Special teams [10-13]
    features[10] = row.get("home_pp_pct", 0.20)
    features[11] = row.get("away_pp_pct", 0.20)
    features[12] = row.get("home_pk_pct", 0.80)
    features[13] = row.get("away_pk_pct", 0.80)

    # Rest [14-17]
    features[14] = row.get("home_rest_days", 1.0)
    features[15] = row.get("away_rest_days", 1.0)
    features[16] = 1.0 if row.get("home_b2b", False) else 0.0
    features[17] = 1.0 if row.get("away_b2b", False) else 0.0

    # 1P-specific averages [18-20]
    features[18] = row.get("home_last5_1p_avg", NHL_AVG_1P_TOTAL / 2)
    features[19] = row.get("away_last5_1p_avg", NHL_AVG_1P_TOTAL / 2)
    features[20] = row.get("h2h_1p_avg", NHL_AVG_1P_TOTAL)

    # Derived features [21-22]
    # Pace factor: higher shots = more chances
    total_shots = features[4] + features[5]
    features[21] = total_shots / NHL_AVG_SHOTS_PER_GAME  # pace_factor

    # Defensive factor: average of save percentages
    features[22] = (features[8] + features[9]) / 2 / NHL_AVG_SAVE_PCT  # defensive_factor

    return features.reshape(1, -1)


def enrich_game_with_1p_features(game_data: Dict, home_abbr: str, away_abbr: str) -> Dict:
    """Enrich game data with 1P-specific features"""
    
    # Estimate 1P averages from full game stats
    # NHL 1P is typically ~26% of full game scoring
    home_gpg = game_data.get("home_goals_per_game", 3.1)
    away_gpg = game_data.get("away_goals_per_game", 3.1)
    
    game_data["home_last5_1p_avg"] = home_gpg * 0.26
    game_data["away_last5_1p_avg"] = away_gpg * 0.26
    
    # H2H estimate
    game_data["h2h_1p_avg"] = NHL_AVG_1P_TOTAL
    
    # Load H2H from cache if available
    try:
        cache_file = Path(__file__).parent.parent.parent / "data" / "cache" / "h2h_features.json"
        if cache_file.exists():
            with open(cache_file, "r") as f:
                h2h_cache = json.load(f)
            
            key = f"{home_abbr}_{away_abbr}"
            alt_key = f"{away_abbr}_{home_abbr}"
            
            if key in h2h_cache:
                h2h = h2h_cache[key]
                # Estimate 1P from full game H2H
                game_data["h2h_1p_avg"] = h2h.get("h2h_weighted_avg_total", 6.2) * 0.26
            elif alt_key in h2h_cache:
                h2h = h2h_cache[alt_key]
                game_data["h2h_1p_avg"] = h2h.get("h2h_weighted_avg_total", 6.2) * 0.26
    except Exception as e:
        logger.warning(f"Could not load H2H for NHL 1P: {e}")
    
    return game_data


def get_1p_feature_names() -> List[str]:
    """Get list of feature names in order"""
    return FEATURE_COLUMNS_1P.copy()


if __name__ == "__main__":
    print("NHL 1P Feature Engineering - Test")
    print(f"Feature count: {len(FEATURE_COLUMNS_1P)}")
    for i, name in enumerate(FEATURE_COLUMNS_1P):
        print(f"  [{i}] {name}")
