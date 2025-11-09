"""
XGBoost Analytics Adapter for NCAAB Advanced Tab

Uses trained quantile regression models to generate analytics
with ML-predicted confidence intervals and uncertainty estimates.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import xgboost as xgb
import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Comprehensive team name mapping (from NCAABTotalsPredictor)
TEAM_NAME_MAP = {
    # Major variations
    'UConn': 'Connecticut',
    'FDU': 'Fairleigh Dickinson',
    'Cal State Fullerton': 'CS Fullerton',
    'College of Charleston': 'Charleston',
    'IU Indianapolis': 'IUPUI',
    'San Diego State': 'San Diego St.',
    'Purdue': 'Purdue',
    'South Carolina': 'South Carolina',
    'Houston': 'Houston',
    'Youngstown State': 'Youngstown St.',
    'Omaha': 'Nebraska Omaha',
    'Kansas State': 'Kansas St.',
    'Kansas City': 'UMKC',
    'Ohio State': 'Ohio St.',
    'Albany (NY)': 'Albany NY',
    'Illinois': 'Illinois',
    'Fresno State': 'Fresno St.',
    'Colorado': 'Colorado',
    'Appalachian State': 'Appalachian St.',
    'Boise State': 'Boise St.',
    'Tarleton State': 'Tarleton St.',
    'UAB': 'UAB',
    'Utah State': 'Utah St.',
    'Western Kentucky': 'Western Kentucky',
    'Ball State': 'Ball St.',
    'Arizona State': 'Arizona St.',
    'Gardner-Webb': 'Gardner Webb',
    'Washington State': 'Washington St.',
    'Saint Mary\'s': 'Saint Mary\'s CA',
    'St. John\'s (NY)': 'St. John\'s',
    'Texas State': 'Texas St.',
    'Cleveland State': 'Cleveland St.',
    'Louisiana-Monroe': 'ULM',
    'UL Monroe': 'ULM',
    'New Mexico State': 'New Mexico St.',
    'Miami (OH)': 'Miami OH',
    'Miami (FL)': 'Miami FL',
    'UIC': 'Illinois Chicago',
    'South Dakota State': 'South Dakota St.',
    'Sam Houston': 'Sam Houston St.',
    'Norfolk State': 'Norfolk St.',
    'Missouri State': 'Missouri St.',
    'Montana State': 'Montana St.',
    'Penn State': 'Penn St.',
    'Illinois State': 'Illinois St.',
    'Tennessee State': 'Tennessee St.',
    'Murray State': 'Murray St.',
    'Austin Peay': 'Austin Peay',
    'Eastern Kentucky': 'Eastern Kentucky',
    'Western Carolina': 'Western Carolina',
    'Tennessee Tech': 'Tennessee Tech',
    'Eastern Illinois': 'Eastern Illinois',
    'Southeast Missouri State': 'Southeast Missouri St.',
    'Southern Illinois': 'Southern Illinois',
    'North Dakota State': 'North Dakota St.',
    'Stephen F. Austin': 'Stephen F Austin',
    'Abilene Christian': 'Abilene Christian',
    'Seattle U': 'Seattle',
    'Utah Valley': 'Utah Valley',
    'CSU Bakersfield': 'CS Bakersfield',
    'Long Beach State': 'Long Beach St.',
    'CSU Northridge': 'CS Northridge',
    'UC Davis': 'UC Davis',
    'UC Irvine': 'UC Irvine',
    'UC Riverside': 'UC Riverside',
    'UC Santa Barbara': 'UC Santa Barbara',
    'Loyola Marymount': 'Loyola Marymount',
    'Saint Mary\'s (CA)': 'Saint Mary\'s CA',
    'San Francisco': 'San Francisco',
    'Santa Clara': 'Santa Clara',
    'Gonzaga': 'Gonzaga',
    'Portland': 'Portland',
    'Stetson': 'Stetson',
    # Additional common variations
    'Ole Miss': 'Mississippi',
    'UNLV': 'UNLV',
    'LSU': 'LSU',
    'TCU': 'TCU',
    'SMU': 'SMU',
    'USC': 'USC',
    'UCLA': 'UCLA',
    'BYU': 'BYU',
    'VCU': 'VCU',
    'UCF': 'UCF',
    'UTEP': 'UTEP',
    'UTSA': 'UTSA',
    'Miami': 'Miami FL',
    'Pittsburgh': 'Pitt',
    'St. John\'s': 'St. John\'s',
    'St. Mary\'s': 'Saint Mary\'s CA',
    'Boston Univ.': 'Boston University',
    'Boston University': 'Boston University',
    'Arkansas St': 'Arkansas St.',
    'Arkansas State': 'Arkansas St.',
    'Alabama St': 'Alabama St.',
    'Alabama State': 'Alabama St.',
}


class XGBoostAnalyticsAdapter:
    """Generate analytics using trained XGBoost quantile models"""

    def __init__(self, kenpom_data: pd.DataFrame):
        """
        Initialize with KenPom data and load trained models

        Args:
            kenpom_data: DataFrame with columns ['Team', 'AdjEM', 'AdjOffEff', 'AdjDefEff', 'AdjTempo']
        """
        self.kenpom_df = kenpom_data

        # Rename columns if needed for consistency with trainer
        if 'AdjOffEff' in kenpom_data.columns:
            self.kenpom_df = self.kenpom_df.rename(columns={
                'AdjOffEff': 'AdjO',
                'AdjDefEff': 'AdjD',
                'AdjTempo': 'AdjT'
            })

        # Load trained models
        model_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'models')

        try:
            self.model_mean = xgb.Booster()
            self.model_mean.load_model(os.path.join(model_dir, 'ncaab_quantile_mean_latest.json'))

            self.model_lower = xgb.Booster()
            self.model_lower.load_model(os.path.join(model_dir, 'ncaab_quantile_lower_latest.json'))

            self.model_upper = xgb.Booster()
            self.model_upper.load_model(os.path.join(model_dir, 'ncaab_quantile_upper_latest.json'))

            logger.info("✅ XGBoost models loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load XGBoost models: {e}")
            raise

    def _normalize_team_name(self, team_name: str) -> str:
        """
        Normalize team names for matching using comprehensive mapping

        Steps:
        1. Strip mascots (e.g., "Duke Blue Devils" -> "Duke")
        2. Apply TEAM_NAME_MAP (e.g., "Ole Miss" -> "Mississippi")
        3. Return normalized name
        """
        team_name = str(team_name).strip()

        # Common mascots to remove (keep this for odds API names)
        mascots = [
            'Blue Devils', 'Tar Heels', 'Wildcats', 'Tigers', 'Bulldogs', 'Eagles',
            'Cardinals', 'Cavaliers', 'Demon Deacons', 'Yellow Jackets', 'Seminoles',
            'Hurricanes', 'Wolfpack', 'Panthers', 'Fighting Irish', 'Trojans', 'Bears',
            'Bruins', 'Ducks', 'Huskies', 'Cougars', 'Sun Devils', 'Utes', 'Buffaloes',
            'Beavers', 'Golden Bears', 'Cardinal', 'Crimson Tide', 'War Eagles', 'Aggies',
            'Volunteers', 'Gators', 'Gamecocks', 'Razorbacks', 'Rebels', 'Commodores',
            'Red Raiders', 'Longhorns', 'Sooners', 'Jayhawks', 'Cyclones', 'Mountaineers',
            'Terrapins', 'Spartans', 'Badgers', 'Cornhuskers', 'Hawkeyes', 'Boilermakers',
            'Hoosiers', 'Golden Gophers', 'Lions', 'Buckeyes', 'Nittany Lions', 'Scarlet Knights',
            'Roadrunners', 'Miners', 'Owls', 'Mean Green', 'Golden Hurricane', 'Mustangs',
            'Horned Frogs', 'Bearcats', 'Knights', 'Bulls', 'Rams', 'Broncos',
            'Aztecs', 'Lobos', 'Rainbow Warriors', 'Pilots', 'Zags', 'Gaels',
            'Dons', 'Waves', 'Anteaters', 'Highlanders', 'Tritons', 'Titans',
            'Matadors', '49ers', 'Gauchos', 'Phoenix', 'Raiders', 'Mastodons', 'Penguins',
            'Vikings', 'Flames', 'Bison', 'Grizzlies', 'Bobcats', 'Golden Eagles', 'Retrievers',
            'Seawolves', 'River Hawks', 'Greyhounds', 'Terriers', 'Catamounts',
            'Stags', 'Peacocks', 'Jaspers', 'Explorers', 'Minutemen', 'Flyers', 'Billikens',
            'Musketeers', 'Blue Jays', 'Hoyas', 'Friars', 'Pirates', 'Red Storm', 'Warriors',
            'Colonials', 'Dukes', 'Dragons', 'Spiders', 'Monarchs', 'Tribe', 'Pride', 'Hornets',
            'Lumberjacks', 'Red Wolves', 'Black Bears', 'Golden Panthers', 'Hatters', 'Warhawks'
        ]

        # Step 1: Strip mascot
        for mascot in mascots:
            if team_name.endswith(mascot):
                team_name = team_name[:-len(mascot)].strip()
                break

        # Step 2: Apply TEAM_NAME_MAP
        if team_name in TEAM_NAME_MAP:
            team_name = TEAM_NAME_MAP[team_name]

        return team_name.strip()

    def _find_team_stats(self, team_name: str) -> Optional[Dict]:
        """
        Find team stats in KenPom data with enhanced matching

        Steps:
        1. Normalize the team name (strip mascot + apply mapping)
        2. Try exact match
        3. Try case-insensitive match
        4. Try partial match (team words in KenPom name)
        5. Try fuzzy match (main word)
        """
        original_name = str(team_name).strip()
        normalized = self._normalize_team_name(original_name)

        # Step 1: Try exact match with normalized name
        match = self.kenpom_df[self.kenpom_df['Team'] == normalized]
        if len(match) > 0:
            row = match.iloc[0]
            return {
                'AdjEM': float(row['AdjEM']),
                'AdjOffEff': float(row['AdjO']),
                'AdjDefEff': float(row['AdjD']),
                'AdjTempo': float(row['AdjT'])
            }

        # Step 2: Try case-insensitive exact match
        normalized_lower = normalized.lower()
        for idx, row in self.kenpom_df.iterrows():
            if row['Team'].lower() == normalized_lower:
                return {
                    'AdjEM': float(row['AdjEM']),
                    'AdjOffEff': float(row['AdjO']),
                    'AdjDefEff': float(row['AdjD']),
                    'AdjTempo': float(row['AdjT'])
                }

        # Step 3: Try word matching (all words from input in KenPom name)
        team_words = set(normalized_lower.split())
        if team_words:
            for idx, row in self.kenpom_df.iterrows():
                kp_words = set(row['Team'].lower().split())
                # All input words must be in KenPom name
                if team_words.issubset(kp_words):
                    return {
                        'AdjEM': float(row['AdjEM']),
                        'AdjOffEff': float(row['AdjO']),
                        'AdjDefEff': float(row['AdjD']),
                        'AdjTempo': float(row['AdjT'])
                    }

        # Step 4: Try fuzzy matching (main word only)
        if team_words:
            main_word = list(team_words)[0]
            for idx, row in self.kenpom_df.iterrows():
                if main_word in row['Team'].lower():
                    return {
                        'AdjEM': float(row['AdjEM']),
                        'AdjOffEff': float(row['AdjO']),
                        'AdjDefEff': float(row['AdjD']),
                        'AdjTempo': float(row['AdjT'])
                    }

        # No match found
        logger.debug(f"Could not find KenPom data for '{original_name}' (normalized: '{normalized}')")
        return None

    def _calculate_game_features(self, home_stats: Dict, away_stats: Dict) -> Dict:
        """
        Calculate all 40 features for XGBoost model
        (Copied from NCAABQuantileTrainer for consistency)
        """
        features = {
            'home_adj_em': home_stats['AdjEM'],
            'away_adj_em': away_stats['AdjEM'],
            'home_off_eff': home_stats['AdjOffEff'],
            'away_off_eff': away_stats['AdjOffEff'],
            'home_def_eff': home_stats['AdjDefEff'],
            'away_def_eff': away_stats['AdjDefEff'],
            'home_tempo': home_stats['AdjTempo'],
            'away_tempo': away_stats['AdjTempo'],
        }

        # Tempo metrics
        features['avg_tempo'] = (home_stats['AdjTempo'] + away_stats['AdjTempo']) / 2

        # Differentials
        features['em_diff'] = home_stats['AdjEM'] - away_stats['AdjEM']
        features['off_eff_diff'] = home_stats['AdjOffEff'] - away_stats['AdjOffEff']
        features['def_eff_diff'] = away_stats['AdjDefEff'] - home_stats['AdjDefEff']
        features['tempo_diff'] = home_stats['AdjTempo'] - away_stats['AdjTempo']

        # Expected points (basic)
        features['expected_home_pts'] = (home_stats['AdjOffEff'] * features['avg_tempo']) / 100
        features['expected_away_pts'] = (away_stats['AdjOffEff'] * features['avg_tempo']) / 100

        # Expected points (adjusted for defense)
        home_off_vs_away_def = (home_stats['AdjOffEff'] + (100 - away_stats['AdjDefEff'])) / 2
        away_off_vs_home_def = (away_stats['AdjOffEff'] + (100 - home_stats['AdjDefEff'])) / 2

        features['expected_home_pts_adj'] = (home_off_vs_away_def * features['avg_tempo']) / 100
        features['expected_away_pts_adj'] = (away_off_vs_home_def * features['avg_tempo']) / 100

        # Expected totals
        features['expected_total_basic'] = features['expected_home_pts'] + features['expected_away_pts']
        features['expected_total_adj'] = features['expected_home_pts_adj'] + features['expected_away_pts_adj']

        # Efficiency margins
        features['home_eff_margin'] = home_stats['AdjOffEff'] - home_stats['AdjDefEff']
        features['away_eff_margin'] = away_stats['AdjOffEff'] - away_stats['AdjDefEff']

        # Combined metrics
        features['combined_off_eff'] = home_stats['AdjOffEff'] + away_stats['AdjOffEff']
        features['combined_def_eff'] = home_stats['AdjDefEff'] + away_stats['AdjDefEff']

        # Pace factor
        features['pace_factor'] = features['avg_tempo'] / 68.0
        features['tempo_over_avg'] = features['avg_tempo'] - 68.0

        # Binary indicators
        features['high_tempo_game'] = 1 if features['avg_tempo'] > 70 else 0
        features['low_tempo_game'] = 1 if features['avg_tempo'] < 66 else 0

        # Variance indicators
        features['tempo_variance'] = abs(home_stats['AdjTempo'] - away_stats['AdjTempo'])
        features['offense_advantage'] = max(0, features['off_eff_diff'])
        features['defense_advantage'] = max(0, features['def_eff_diff'])

        # Mismatch indicators
        features['mismatch_score'] = abs(features['em_diff'])
        features['competitive_balance'] = 1 / (1 + features['mismatch_score'] / 10)

        # Dominance indicators
        features['home_dominance'] = max(0, features['em_diff'])
        features['away_dominance'] = max(0, -features['em_diff'])
        features['blowout_potential'] = features['mismatch_score'] * features['pace_factor']
        features['close_game_indicator'] = 1 if features['mismatch_score'] < 5 else 0

        # Game style indicators
        features['offensive_game'] = 1 if features['combined_off_eff'] > 220 else 0
        features['defensive_game'] = 1 if features['combined_def_eff'] < 180 else 0

        # Expected margin
        features['expected_margin'] = features['expected_home_pts'] - features['expected_away_pts']
        features['expected_margin_adj'] = features['expected_home_pts_adj'] - features['expected_away_pts_adj']
        features['tempo_adjusted_margin'] = features['expected_margin_adj'] * features['pace_factor']

        return features

    def generate_analytics(self, home_team: str, away_team: str, live_total: float,
                          pregame_total: Optional[float] = None) -> Optional[Dict]:
        """
        Generate NCAAB analytics using XGBoost models

        Args:
            home_team: Home team name (with or without mascot)
            away_team: Away team name (with or without mascot)
            live_total: Current betting total
            pregame_total: Opening total (optional)

        Returns:
            Analytics dict for frontend or None if teams not found
        """
        # Find team stats
        home_stats = self._find_team_stats(home_team)
        away_stats = self._find_team_stats(away_team)

        if not home_stats or not away_stats:
            logger.warning(f"Could not find stats for {home_team} vs {away_team}")
            return None

        # Calculate features
        features = self._calculate_game_features(home_stats, away_stats)

        # Convert to DataFrame for XGBoost
        features_df = pd.DataFrame([features])
        dmatrix = xgb.DMatrix(features_df)

        # Get predictions from all 3 models
        pred_mean = float(self.model_mean.predict(dmatrix)[0])
        pred_lower = float(self.model_lower.predict(dmatrix)[0])
        pred_upper = float(self.model_upper.predict(dmatrix)[0])

        # Calculate uncertainty metrics
        confidence_interval_width = pred_upper - pred_lower
        std_dev = confidence_interval_width / 2.56  # 90th - 10th percentile ≈ 2.56 std devs

        # Calculate deviation from model
        deviation = live_total - pred_mean
        z_score = deviation / std_dev if std_dev > 0 else 0
        edge_points = abs(deviation)

        # Direction
        direction = "UNDER" if deviation > 0 else "OVER"

        # Confidence based on z-score and model uncertainty
        if abs(z_score) >= 2.5 and std_dev < 8:
            confidence = 90
        elif abs(z_score) >= 2.0 and std_dev < 10:
            confidence = 80
        elif abs(z_score) >= 1.5:
            confidence = 70
        elif abs(z_score) >= 1.0:
            confidence = 60
        else:
            confidence = 50

        # Kelly sizing (conservative, based on edge and confidence)
        kelly_fraction = min(0.05, (edge_points / 20) * (confidence / 100))
        kelly_pct = kelly_fraction * 100

        # Line movement
        line_movement = (live_total - pregame_total) if pregame_total else None

        return {
            # Top 5 Must-Have Metrics
            'direction': direction,
            'line': live_total,
            'z_score': round(z_score, 2),
            'edge_points': round(edge_points, 1),
            'model_prediction': round(pred_mean, 1),
            'live_total': live_total,
            'kelly_percentage': round(kelly_pct, 1),
            'confidence': confidence,

            # Secondary Metrics
            'pregame_total': pregame_total,
            'line_movement': round(line_movement, 1) if line_movement else None,
            'standard_deviation': round(std_dev, 1),
            'home_tempo': round(home_stats['AdjTempo'], 1),
            'away_tempo': round(away_stats['AdjTempo'], 1),
            'home_offensive_efficiency': round(home_stats['AdjOffEff'], 1),
            'away_offensive_efficiency': round(away_stats['AdjOffEff'], 1),
            'home_defensive_efficiency': round(home_stats['AdjDefEff'], 1),
            'away_defensive_efficiency': round(away_stats['AdjDefEff'], 1),
            'deviation_description': self._describe_deviation(abs(z_score)),

            # Additional ML-specific metrics (optional, not displayed by default)
            'predicted_lower_bound': round(pred_lower, 1),
            'predicted_upper_bound': round(pred_upper, 1),
            'confidence_interval_width': round(confidence_interval_width, 1),
        }

    def _describe_deviation(self, abs_z_score: float) -> str:
        """Human-readable deviation description"""
        if abs_z_score >= 3.0:
            return "Extreme deviation (3.0+ std devs)"
        elif abs_z_score >= 2.5:
            return "Very high deviation (2.5-3.0 std devs)"
        elif abs_z_score >= 2.0:
            return "High deviation (2.0-2.5 std devs)"
        elif abs_z_score >= 1.5:
            return "Moderate-high deviation (1.5-2.0 std devs)"
        elif abs_z_score >= 1.0:
            return "Moderate deviation (1.0-1.5 std devs)"
        else:
            return "Low deviation (< 1.0 std dev)"


# Quick test
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    # Load KenPom data
    kenpom_df = pd.read_csv('C:/Users/nashr/backend/data/raw/ncaab/kenpom_ratings_20251107_175341.csv')

    # Initialize adapter
    adapter = XGBoostAnalyticsAdapter(kenpom_df)

    # Test prediction
    analytics = adapter.generate_analytics(
        home_team='Duke Blue Devils',
        away_team='North Carolina Tar Heels',
        live_total=164.5,
        pregame_total=158.5
    )

    if analytics:
        print("\n✅ XGBoost Analytics Generated:")
        import json
        print(json.dumps(analytics, indent=2))
    else:
        print("❌ Could not generate analytics")
