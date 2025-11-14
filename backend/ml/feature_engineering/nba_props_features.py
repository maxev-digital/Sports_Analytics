"""
NBA Player Props - Feature Engineering
Extracts 50+ features for ML model training and prediction

Features Categories:
1. Player Stats (20 features) - Season averages, recent form, splits
2. Matchup Features (15 features) - Opponent defense, pace, historical
3. Context Features (15 features) - Rest days, home/away, game context
4. Market Features (5 features) - Line value, odds analysis
"""

import sys
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.props.balldontlie_client import BallDontLieClient


class NBAPropsFeatureEngineer:
    """
    Extracts features for NBA player props ML models
    """

    def __init__(self, db_path: str = "data/player_props.db"):
        self.db_path = db_path
        self.stats_client = BallDontLieClient()
        self.current_season = 2024  # 2024-25 season

    def extract_features_for_prop(
        self,
        player_name: str,
        team: str,
        opponent: str,
        prop_type: str,
        market_line: float,
        game_date: date,
        home_away: str = "HOME"
    ) -> Dict[str, float]:
        """
        Extract all features for a single prop

        Returns dict with 50+ features ready for ML model
        """
        print(f"Extracting features for {player_name} {prop_type} O/U {market_line} vs {opponent}...")

        features = {}

        # 1. Player Stats Features (20)
        player_features = self._extract_player_stats_features(
            player_name, prop_type, game_date
        )
        features.update(player_features)

        # 2. Matchup Features (15)
        matchup_features = self._extract_matchup_features(
            player_name, team, opponent, prop_type, game_date
        )
        features.update(matchup_features)

        # 3. Context Features (15)
        context_features = self._extract_context_features(
            player_name, team, opponent, home_away, game_date
        )
        features.update(context_features)

        # 4. Market Features (5)
        market_features = self._extract_market_features(
            player_name, prop_type, market_line, features
        )
        features.update(market_features)

        print(f"  [OK] Extracted {len(features)} features")
        return features

    # =========================================================================
    # 1. PLAYER STATS FEATURES (20 features)
    # =========================================================================

    def _extract_player_stats_features(
        self,
        player_name: str,
        prop_type: str,
        game_date: date
    ) -> Dict[str, float]:
        """
        Extract player statistics features
        - Season averages
        - Last 5/10 games averages
        - Home/away splits
        - Recent trends
        """
        features = {}

        # Get player from BallDontLie
        player = self.stats_client.get_player_by_name(player_name)
        if not player:
            print(f"  [WARN] Player not found: {player_name}, using defaults")
            return self._get_default_player_features()

        player_id = player['id']

        # Get season averages
        season_avg = self.stats_client.get_player_season_averages(
            player_id, self.current_season
        )

        if season_avg:
            features['season_avg'] = self._get_stat_value(season_avg, prop_type)
            features['season_mins'] = season_avg.get('min', 0.0)
            features['season_games_played'] = season_avg.get('games_played', 0)
        else:
            features['season_avg'] = 0.0
            features['season_mins'] = 0.0
            features['season_games_played'] = 0

        # Get recent games (last 30 days to capture L5 and L10)
        recent_games = self.stats_client.get_player_recent_games(
            player_id=player_id,
            last_n_days=30,
            limit=15
        )

        if recent_games and len(recent_games) > 0:
            # Last 5 games average
            last_5 = recent_games[:5]
            features['last_5_avg'] = np.mean([
                self._get_stat_value(g, prop_type) for g in last_5
            ])
            features['last_5_mins'] = np.mean([g.get('min', 0) for g in last_5])

            # Last 10 games average
            last_10 = recent_games[:10]
            features['last_10_avg'] = np.mean([
                self._get_stat_value(g, prop_type) for g in last_10
            ])
            features['last_10_mins'] = np.mean([g.get('min', 0) for g in last_10])

            # Last 3 games average (for trend detection)
            last_3 = recent_games[:3]
            features['last_3_avg'] = np.mean([
                self._get_stat_value(g, prop_type) for g in last_3
            ])

            # Trend: L3 vs L10 (positive = improving)
            features['trend_l3_vs_l10'] = features['last_3_avg'] - features['last_10_avg']

            # Consistency (standard deviation of last 10)
            last_10_values = [self._get_stat_value(g, prop_type) for g in last_10]
            features['consistency_std'] = np.std(last_10_values)

            # Home/Away splits
            home_games = [g for g in recent_games if self._is_home_game(g, player['team'])]
            away_games = [g for g in recent_games if not self._is_home_game(g, player['team'])]

            if home_games:
                features['home_avg'] = np.mean([
                    self._get_stat_value(g, prop_type) for g in home_games
                ])
            else:
                features['home_avg'] = features.get('season_avg', 0.0)

            if away_games:
                features['away_avg'] = np.mean([
                    self._get_stat_value(g, prop_type) for g in away_games
                ])
            else:
                features['away_avg'] = features.get('season_avg', 0.0)

            # Recent minutes trend (are they getting more/less playing time?)
            recent_mins = [g.get('min', 0) for g in last_5]
            features['mins_trend'] = recent_mins[0] - recent_mins[-1] if len(recent_mins) >= 2 else 0.0

        else:
            # No recent games - use defaults
            features.update({
                'last_5_avg': features.get('season_avg', 0.0),
                'last_5_mins': features.get('season_mins', 0.0),
                'last_10_avg': features.get('season_avg', 0.0),
                'last_10_mins': features.get('season_mins', 0.0),
                'last_3_avg': features.get('season_avg', 0.0),
                'trend_l3_vs_l10': 0.0,
                'consistency_std': 0.0,
                'home_avg': features.get('season_avg', 0.0),
                'away_avg': features.get('season_avg', 0.0),
                'mins_trend': 0.0
            })

        return features

    # =========================================================================
    # 2. MATCHUP FEATURES (15 features)
    # =========================================================================

    def _extract_matchup_features(
        self,
        player_name: str,
        team: str,
        opponent: str,
        prop_type: str,
        game_date: date
    ) -> Dict[str, float]:
        """
        Extract matchup-specific features
        - Opponent defensive rating
        - Opponent pace
        - Historical performance vs opponent
        - Defensive rank against prop type
        """
        features = {}

        # TODO: Opponent team stats (pace, defensive rating)
        # For now, use placeholders - will enhance with team stats API
        features['opp_pace'] = 100.0  # League average pace
        features['opp_def_rating'] = 110.0  # League average defense

        # Opponent strength (based on record - placeholder)
        features['opp_win_pct'] = 0.500  # Neutral

        # Defensive rank vs prop type (placeholder)
        # e.g., how good is opponent at defending rebounds?
        features['opp_def_rank_prop'] = 15.0  # Middle of pack (1-30)

        # Historical performance vs this opponent
        # Query database for past games vs this opponent
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT AVG(actual_value), COUNT(*)
            FROM player_props_results
            WHERE player_name = ?
            AND opponent = ?
            AND prop_type = ?
        """, (player_name, opponent, prop_type))

        result = cursor.fetchone()
        conn.close()

        if result and result[1] > 0:
            features['vs_opp_avg'] = result[0]
            features['vs_opp_games'] = result[1]
        else:
            features['vs_opp_avg'] = 0.0
            features['vs_opp_games'] = 0

        # Matchup difficulty score (composite)
        # Higher = tougher matchup
        features['matchup_difficulty'] = (
            features['opp_def_rating'] / 110.0 +
            features['opp_win_pct'] * 2 +
            (30 - features['opp_def_rank_prop']) / 30.0
        ) / 3.0

        return features

    # =========================================================================
    # 3. CONTEXT FEATURES (15 features)
    # =========================================================================

    def _extract_context_features(
        self,
        player_name: str,
        team: str,
        opponent: str,
        home_away: str,
        game_date: date
    ) -> Dict[str, float]:
        """
        Extract contextual features
        - Rest days
        - Home/away
        - Days since last game
        - Team context
        - Season timing
        """
        features = {}

        # Home/away indicator
        features['is_home'] = 1.0 if home_away == "HOME" else 0.0

        # Rest days (placeholder - needs schedule data)
        features['rest_days'] = 1.0  # Default 1 day rest
        features['is_back_to_back'] = 0.0  # Default not B2B

        # Days into season (affects player conditioning, strategy)
        season_start = date(2024, 10, 22)  # 2024-25 season start
        features['days_into_season'] = (game_date - season_start).days

        # Month of season (0-6 for Oct-Apr)
        features['season_month'] = game_date.month - 10 if game_date.month >= 10 else game_date.month + 2

        # Team pace (placeholder - needs team stats)
        features['team_pace'] = 100.0  # League average

        # Expected game total (from odds - placeholder)
        features['game_total'] = 220.0  # Typical NBA total

        # Blowout risk (placeholder - based on team strength difference)
        features['blowout_risk'] = 0.0

        return features

    # =========================================================================
    # 4. MARKET FEATURES (5 features)
    # =========================================================================

    def _extract_market_features(
        self,
        player_name: str,
        prop_type: str,
        market_line: float,
        player_features: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Extract market-based features
        - Line vs averages
        - Implied edge
        """
        features = {}

        # Line vs season average
        season_avg = player_features.get('season_avg', market_line)
        features['line_vs_season_avg'] = market_line - season_avg

        # Line vs last 10 average
        last_10_avg = player_features.get('last_10_avg', market_line)
        features['line_vs_last_10_avg'] = market_line - last_10_avg

        # Line percentage of season average (how far off is line?)
        if season_avg > 0:
            features['line_pct_of_season'] = market_line / season_avg
        else:
            features['line_pct_of_season'] = 1.0

        # Implied over probability (from -110 odds = 52.4%)
        features['implied_over_prob'] = 0.524

        # Value indicator (positive = line is low compared to recent form)
        features['value_indicator'] = last_10_avg - market_line

        return features

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _get_stat_value(self, game_stats: dict, prop_type: str) -> float:
        """
        Extract stat value from game stats based on prop type
        """
        stat_map = {
            "points": "pts",
            "rebounds": "reb",
            "assists": "ast",
            "threes": "fg3m",
            "blocks": "blk",
            "steals": "stl"
        }

        stat_key = stat_map.get(prop_type)
        if stat_key:
            return float(game_stats.get(stat_key, 0.0))

        # Handle PRA (points + rebounds + assists)
        if prop_type == "PRA":
            pts = game_stats.get("pts", 0)
            reb = game_stats.get("reb", 0)
            ast = game_stats.get("ast", 0)
            return float(pts + reb + ast)

        return 0.0

    def _is_home_game(self, game_stats: dict, team_abbr: str) -> bool:
        """
        Determine if game was home or away
        """
        game = game_stats.get('game', {})
        home_team = game.get('home_team', {})
        return home_team.get('abbreviation', '') == team_abbr

    def _get_default_player_features(self) -> Dict[str, float]:
        """
        Return default features when player data unavailable
        """
        return {
            'season_avg': 0.0,
            'season_mins': 0.0,
            'season_games_played': 0,
            'last_5_avg': 0.0,
            'last_5_mins': 0.0,
            'last_10_avg': 0.0,
            'last_10_mins': 0.0,
            'last_3_avg': 0.0,
            'trend_l3_vs_l10': 0.0,
            'consistency_std': 0.0,
            'home_avg': 0.0,
            'away_avg': 0.0,
            'mins_trend': 0.0
        }

    # =========================================================================
    # BATCH FEATURE EXTRACTION
    # =========================================================================

    def extract_features_for_all_props(
        self,
        props_date: date
    ) -> pd.DataFrame:
        """
        Extract features for all props on a given date
        Returns DataFrame ready for ML training
        """
        print(f"\n{'='*70}")
        print(f"NBA PROPS - FEATURE EXTRACTION")
        print(f"{'='*70}")
        print(f"Date: {props_date}")
        print()

        # Get all props from database for this date
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT player_name, team, opponent, home_away,
                   prop_type, market_line, game_id
            FROM player_props_lines
            WHERE date = ?
        """, (props_date,))

        props = cursor.fetchall()
        conn.close()

        print(f"[1/2] Found {len(props)} props to extract features for")

        if len(props) == 0:
            print(f"  [WARN] No props found for {props_date}")
            return pd.DataFrame()

        # Extract features for each prop
        print(f"[2/2] Extracting features...")
        all_features = []

        for i, prop in enumerate(props, 1):
            player_name, team, opponent, home_away, prop_type, market_line, game_id = prop

            if i % 50 == 0:
                print(f"  Progress: {i}/{len(props)} ({i/len(props)*100:.1f}%)")

            try:
                features = self.extract_features_for_prop(
                    player_name=player_name,
                    team=team,
                    opponent=opponent,
                    prop_type=prop_type,
                    market_line=market_line,
                    game_date=props_date,
                    home_away=home_away
                )

                # Add metadata
                features['player_name'] = player_name
                features['team'] = team
                features['opponent'] = opponent
                features['prop_type'] = prop_type
                features['market_line'] = market_line
                features['game_date'] = str(props_date)
                features['game_id'] = game_id

                all_features.append(features)

            except Exception as e:
                print(f"  [ERROR] Failed to extract features for {player_name} {prop_type}: {e}")

        # Convert to DataFrame
        df = pd.DataFrame(all_features)

        print(f"\n{'='*70}")
        print(f"[SUCCESS] Feature extraction complete!")
        print(f"{'='*70}")
        print(f"Props processed: {len(all_features)}/{len(props)}")
        print(f"Features per prop: {len(df.columns) - 7}")  # Exclude metadata columns
        print(f"\nDataFrame shape: {df.shape}")
        print(f"\n{'='*70}\n")

        return df


# =============================================================================
# TESTING
# =============================================================================

def test_feature_extraction():
    """
    Test feature extraction on a single prop
    """
    from datetime import date

    engineer = NBAPropsFeatureEngineer()

    # Test with a known player
    features = engineer.extract_features_for_prop(
        player_name="LeBron James",
        team="LAL",
        opponent="BOS",
        prop_type="points",
        market_line=25.5,
        game_date=date.today(),
        home_away="HOME"
    )

    print("\n" + "="*70)
    print("FEATURE EXTRACTION TEST")
    print("="*70)
    print(f"Player: LeBron James")
    print(f"Prop: Points O/U 25.5 vs BOS")
    print(f"\nFeatures extracted: {len(features)}")
    print("\nSample features:")
    for key, value in list(features.items())[:10]:
        print(f"  {key}: {value}")
    print("="*70)


if __name__ == "__main__":
    test_feature_extraction()
