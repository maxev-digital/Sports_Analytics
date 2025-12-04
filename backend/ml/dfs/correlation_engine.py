"""
Correlation Engine for DFS Crusher
===================================

This module identifies correlated player prop combos for PrizePicks and Underdog Fantasy.

Key Features:
- Calculate correlation matrix between props
- Generate 2-6 leg combos
- Detect "Demon Mode" (high correlation + all positive edges)
- Detect "Goblin Mode" (negative correlation traps)
- Save to correlated_combos table

Workflow:
1. Load today's predictions from player_props_predictions
2. Calculate correlation matrix (historical data + same-player correlations)
3. Generate combos (2-6 legs) with positive edges
4. Score combos by edge, correlation, confidence
5. Detect Demon/Goblin modes
6. Save to database

Author: Max EV Sports ML Team
Date: December 2025
Version: 1.0
"""

import sqlite3
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from itertools import combinations

import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "predictions.db"


class CorrelationEngine:
    """
    DFS Crusher Correlation Engine.

    Generates correlated prop combos for PrizePicks/Underdog.
    """

    def __init__(self, sport: str = 'nba'):
        self.sport = sport.lower()
        self.correlation_matrix = None
        self.predictions_df = None

    def load_todays_predictions(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        Load today's predictions from database.

        Args:
            date: YYYY-MM-DD (default: today)

        Returns:
            DataFrame with predictions
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"Loading predictions for {date}...")

        conn = sqlite3.connect(str(DB_PATH))

        query = """
            SELECT
                player_name,
                team,
                opponent,
                prop_type,
                market_line,
                predicted_value,
                edge,
                edge_pct,
                confidence_level,
                recommendation,
                xgboost_pred,
                lightgbm_pred,
                rf_pred,
                linear_pred,
                pytorch_pred,
                catboost_pred
            FROM player_props_predictions
            WHERE prediction_date = ? AND sport = ?
            AND recommendation IN ('OVER', 'UNDER')
            ORDER BY ABS(edge) DESC
        """

        df = pd.read_sql_query(query, conn, params=[date, self.sport])
        conn.close()

        logger.info(f"Loaded {len(df)} predictions with actionable recommendations")

        self.predictions_df = df
        return df

    def calculate_correlation_matrix(self) -> pd.DataFrame:
        """
        Calculate correlation matrix between all props.

        Uses:
        1. Same-player correlations (known relationships)
        2. Historical data from props_results (future enhancement)
        3. Team dynamics (future enhancement)

        Returns:
            N x N correlation matrix
        """
        logger.info("Calculating correlation matrix...")

        if self.predictions_df is None or len(self.predictions_df) == 0:
            logger.warning("No predictions available for correlation calculation")
            return pd.DataFrame()

        n = len(self.predictions_df)
        corr_matrix = np.zeros((n, n))

        # Calculate pairwise correlations
        for i in range(n):
            for j in range(n):
                if i == j:
                    corr_matrix[i, j] = 1.0
                else:
                    corr = self._calculate_prop_correlation(i, j)
                    corr_matrix[i, j] = corr

        # Create DataFrame with prop labels
        prop_labels = [
            f"{row['player_name']}_{row['prop_type']}"
            for _, row in self.predictions_df.iterrows()
        ]

        corr_df = pd.DataFrame(
            corr_matrix,
            index=prop_labels,
            columns=prop_labels
        )

        logger.info(f"Correlation matrix shape: {corr_df.shape}")

        self.correlation_matrix = corr_df
        return corr_df

    def _calculate_prop_correlation(self, idx1: int, idx2: int) -> float:
        """
        Calculate correlation between two props.

        Args:
            idx1: Index of first prop
            idx2: Index of second prop

        Returns:
            Correlation coefficient (-1 to 1)
        """
        prop1 = self.predictions_df.iloc[idx1]
        prop2 = self.predictions_df.iloc[idx2]

        # Same player correlations
        if prop1['player_name'] == prop2['player_name']:
            return self._same_player_correlation(prop1['prop_type'], prop2['prop_type'])

        # Same team correlations
        if prop1['team'] == prop2['team']:
            return self._same_team_correlation(prop1, prop2)

        # Different teams (game script effects)
        if prop1['opponent'] == prop2['team'] or prop1['team'] == prop2['opponent']:
            return self._opponent_correlation(prop1, prop2)

        # No correlation
        return 0.0

    def _same_player_correlation(self, prop_type1: str, prop_type2: str) -> float:
        """
        Known correlations between prop types for same player.

        Based on NBA statistics research.
        """
        correlations = {
            ('points', 'field_goal_attempts'): 0.85,
            ('points', 'field_goal_made'): 0.90,
            ('points', 'free_throw_attempts'): 0.70,
            ('points', 'minutes'): 0.75,
            ('points', 'assists'): 0.40,
            ('points', 'rebounds'): 0.30,
            ('assists', 'turnovers'): 0.65,
            ('assists', 'minutes'): 0.70,
            ('assists', 'steals'): 0.45,
            ('rebounds', 'minutes'): 0.70,
            ('rebounds', 'blocks'): 0.55,
            ('rebounds', 'steals'): 0.30,
            ('threes', 'points'): 0.75,
            ('threes', 'field_goal_attempts'): 0.60,
            ('steals', 'blocks'): 0.40,
            ('blocks', 'rebounds'): 0.55,
        }

        # Check both directions
        key1 = (prop_type1, prop_type2)
        key2 = (prop_type2, prop_type1)

        if key1 in correlations:
            return correlations[key1]
        elif key2 in correlations:
            return correlations[key2]
        else:
            # Default: moderate positive correlation for same player
            return 0.35

    def _same_team_correlation(self, prop1: pd.Series, prop2: pd.Series) -> float:
        """
        Correlation between teammates.

        Generally negative (competing for stats) unless facilitator relationship.
        """
        # Assists + teammate scoring = positive
        if prop1['prop_type'] == 'assists' and prop2['prop_type'] == 'points':
            return 0.45
        if prop1['prop_type'] == 'points' and prop2['prop_type'] == 'assists':
            return 0.45

        # Rebounds competition = negative
        if prop1['prop_type'] == 'rebounds' and prop2['prop_type'] == 'rebounds':
            return -0.25

        # Scoring competition = slight negative
        if prop1['prop_type'] == 'points' and prop2['prop_type'] == 'points':
            return -0.15

        # Default: slight negative (competing for usage)
        return -0.10

    def _opponent_correlation(self, prop1: pd.Series, prop2: pd.Series) -> float:
        """
        Correlation between opposing players.

        Game script and pace effects.
        """
        # High-scoring games benefit both teams' scorers
        if prop1['prop_type'] == 'points' and prop2['prop_type'] == 'points':
            return 0.40

        # High pace benefits everyone
        if prop1['prop_type'] in ['points', 'assists'] and prop2['prop_type'] in ['points', 'assists']:
            return 0.30

        # Default: slight positive (pace effects)
        return 0.15

    def generate_combos(
        self,
        min_legs: int = 2,
        max_legs: int = 6,
        min_edge: float = 1.0,
        max_correlation: float = 0.75,
        min_correlation: float = 0.3
    ) -> List[Dict]:
        """
        Generate 2-6 leg combos.

        Args:
            min_legs: Minimum legs (2-6)
            max_legs: Maximum legs (2-6)
            min_edge: Minimum edge per prop (%)
            max_correlation: Maximum average correlation
            min_correlation: Minimum correlation for Demon Mode

        Returns:
            List of combo dictionaries
        """
        logger.info(f"Generating combos ({min_legs}-{max_legs} legs)...")

        if self.predictions_df is None or len(self.predictions_df) == 0:
            logger.warning("No predictions available")
            return []

        if self.correlation_matrix is None:
            self.calculate_correlation_matrix()

        all_combos = []

        # Generate combos for each leg count
        for num_legs in range(min_legs, max_legs + 1):
            combos = self._generate_n_leg_combos(
                num_legs, min_edge, max_correlation, min_correlation
            )
            all_combos.extend(combos)

        logger.info(f"Generated {len(all_combos)} total combos")

        # Sort by combo score
        all_combos.sort(key=lambda x: x['combo_score'], reverse=True)

        return all_combos

    def _generate_n_leg_combos(
        self,
        n: int,
        min_edge: float,
        max_correlation: float,
        min_correlation: float
    ) -> List[Dict]:
        """Generate all n-leg combos."""
        combos = []

        # Get all combinations of n props
        for combo_indices in combinations(range(len(self.predictions_df)), n):
            # Get props for this combo
            props = [self.predictions_df.iloc[i] for i in combo_indices]

            # Filter: all props must have sufficient edge
            if any(abs(prop['edge_pct']) < min_edge for prop in props):
                continue

            # Calculate average correlation
            avg_corr = self._calculate_combo_correlation(combo_indices)

            # Filter: correlation within acceptable range
            if avg_corr > max_correlation:
                continue

            # Score combo
            combo = self._score_combo(props, combo_indices, avg_corr, min_correlation)
            combos.append(combo)

        logger.info(f"Generated {len(combos)} {n}-leg combos")
        return combos

    def _calculate_combo_correlation(self, indices: Tuple[int]) -> float:
        """Calculate average pairwise correlation for combo."""
        if len(indices) < 2:
            return 0.0

        correlations = []
        for i, idx1 in enumerate(indices):
            for idx2 in indices[i+1:]:
                corr = self.correlation_matrix.iloc[idx1, idx2]
                correlations.append(corr)

        return np.mean(correlations)

    def _score_combo(
        self,
        props: List[pd.Series],
        indices: Tuple[int],
        avg_corr: float,
        min_correlation: float
    ) -> Dict:
        """
        Score combo and detect Demon/Goblin modes.

        Scoring formula:
        - Average edge: 40%
        - Correlation strength: 30%
        - Confidence levels: 20%
        - Diversity: 10%
        """
        # Calculate metrics
        avg_edge = np.mean([abs(prop['edge_pct']) for prop in props])

        confidence_map = {'ULTRA': 1.0, 'HIGH': 0.75, 'MEDIUM': 0.5, 'LOW': 0.25}
        avg_confidence = np.mean([
            confidence_map.get(prop['confidence_level'], 0.5)
            for prop in props
        ])

        # Diversity bonus (unique players/teams)
        unique_players = len(set(prop['player_name'] for prop in props))
        unique_teams = len(set(prop['team'] for prop in props))
        diversity = (unique_players / len(props)) * 0.5 + (unique_teams / len(props)) * 0.5

        # Correlation strength (positive correlation is good for Demon Mode)
        corr_strength = max(0, avg_corr) / 1.0  # Normalize to 0-1

        # Combo score
        combo_score = (
            (avg_edge / 10.0) * 0.4 +      # Normalize edge to 0-1
            corr_strength * 0.3 +
            avg_confidence * 0.2 +
            diversity * 0.1
        ) * 10  # Scale to 0-10

        # Demon Mode detection
        is_demon = (
            avg_corr >= min_correlation and
            all(prop['edge_pct'] > 0 for prop in props) and
            avg_confidence >= 0.6
        )

        # Goblin Mode detection (negative correlation trap)
        is_goblin = (
            avg_corr < -0.2 and
            combo_score < 5.0
        )

        # PrizePicks payout multipliers
        payout_multipliers = {2: 3, 3: 5, 4: 10, 5: 20, 6: 50}
        payout = payout_multipliers.get(len(props), 1)

        # Build combo dictionary
        combo = {
            'combo_id': f"{self.sport}_{datetime.now().strftime('%Y%m%d')}_{len(props)}leg_{id(props)}",
            'sport': self.sport,
            'players': json.dumps([prop['player_name'] for prop in props]),
            'props': json.dumps([prop['prop_type'] for prop in props]),
            'lines': json.dumps([float(prop['market_line']) for prop in props]),
            'directions': json.dumps([prop['recommendation'] for prop in props]),
            'true_probability': float(0.5 + (avg_confidence * 0.3)),  # Estimate from confidence
            'prize_picks_payout': float(payout),
            'expected_value_percent': float(avg_edge),
            'demon_goblin_score': float(combo_score),
            'site_with_best_line': 'PrizePicks',
            'display_edge': float(avg_edge),
            'display_confidence': 'DEMON' if is_demon else ('GOBLIN' if is_goblin else 'NORMAL'),
            'display_recommendation': 'BET' if combo_score >= 6.0 else 'PASS',
            'display_win_rate': None,
            'display_units': None,
            'display_roi': None,
            'created_at': datetime.now().isoformat(),
            # Extra metadata (not in DB)
            'avg_correlation': float(avg_corr),
            'combo_score': float(combo_score),
            'is_demon_mode': is_demon,
            'is_goblin_mode': is_goblin,
            'num_legs': len(props),
            'props_details': [
                {
                    'player_name': prop['player_name'],
                    'team': prop['team'],
                    'prop_type': prop['prop_type'],
                    'market_line': float(prop['market_line']),
                    'predicted_value': float(prop['predicted_value']),
                    'edge': float(prop['edge']),
                    'edge_pct': float(prop['edge_pct']),
                    'confidence_level': prop['confidence_level'],
                    'recommendation': prop['recommendation']
                }
                for prop in props
            ]
        }

        return combo

    def save_combos_to_database(self, combos: List[Dict]):
        """
        Save combos to correlated_combos table.

        Args:
            combos: List of combo dictionaries
        """
        logger.info(f"Saving {len(combos)} combos to database...")

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Clear old combos for today
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            "DELETE FROM correlated_combos WHERE combo_id LIKE ?",
            (f"{self.sport}_{today.replace('-', '')}%",)
        )

        # Insert new combos
        saved_count = 0
        for combo in combos:
            try:
                cursor.execute("""
                    INSERT INTO correlated_combos (
                        combo_id, sport, players, props, lines, directions,
                        true_probability, prize_picks_payout, expected_value_percent,
                        demon_goblin_score, site_with_best_line, display_edge,
                        display_confidence, display_recommendation, display_win_rate,
                        display_units, display_roi, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    combo['combo_id'],
                    combo['sport'],
                    combo['players'],
                    combo['props'],
                    combo['lines'],
                    combo['directions'],
                    combo['true_probability'],
                    combo['prize_picks_payout'],
                    combo['expected_value_percent'],
                    combo['demon_goblin_score'],
                    combo['site_with_best_line'],
                    combo['display_edge'],
                    combo['display_confidence'],
                    combo['display_recommendation'],
                    combo['display_win_rate'],
                    combo['display_units'],
                    combo['display_roi'],
                    combo['created_at']
                ))
                saved_count += 1
            except Exception as e:
                logger.warning(f"Failed to save combo: {e}")

        conn.commit()
        conn.close()

        logger.info(f"Saved {saved_count} combos to database")

    def generate_todays_correlated_combos(self):
        """
        Main entry point: Generate all correlated combos for today.

        Called by predictor.py after predictions are generated.
        """
        logger.info("=" * 80)
        logger.info("DFS CRUSHER - GENERATING CORRELATED COMBOS")
        logger.info("=" * 80)
        logger.info(f"Sport: {self.sport}")
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        logger.info("")

        try:
            # Step 1: Load predictions
            predictions_df = self.load_todays_predictions()

            if len(predictions_df) == 0:
                logger.warning("No predictions available. Skipping combo generation.")
                return

            # Step 2: Calculate correlation matrix
            self.calculate_correlation_matrix()

            # Step 3: Generate combos
            combos = self.generate_combos(
                min_legs=2,
                max_legs=6,
                min_edge=1.0,           # Min 1% edge
                max_correlation=0.75,   # Max 75% correlation
                min_correlation=0.5     # Min 50% for Demon Mode
            )

            if len(combos) == 0:
                logger.warning("No viable combos generated.")
                return

            # Step 4: Save to database
            self.save_combos_to_database(combos)

            # Step 5: Log stats
            demon_count = sum(1 for c in combos if c['is_demon_mode'])
            goblin_count = sum(1 for c in combos if c['is_goblin_mode'])

            logger.info("")
            logger.info("=" * 80)
            logger.info("COMBO GENERATION COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Total combos: {len(combos)}")
            logger.info(f"Demon Mode combos: {demon_count}")
            logger.info(f"Goblin Mode combos: {goblin_count}")
            logger.info(f"Top combo score: {combos[0]['combo_score']:.2f}/10")
            logger.info("")

        except Exception as e:
            logger.error(f"Error generating combos: {e}", exc_info=True)
            raise


# ============================================================================
# STANDALONE FUNCTIONS (for cron job & imports)
# ============================================================================

def generate_todays_correlated_combos(sport: str = 'nba'):
    """
    Standalone function for cron job or manual execution.

    Usage:
        python -c "from ml.props.correlation_engine import generate_todays_correlated_combos; generate_todays_correlated_combos()"
    """
    engine = CorrelationEngine(sport=sport)
    engine.generate_todays_correlated_combos()


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate correlated prop combos')
    parser.add_argument('--sport', type=str, default='nba', help='Sport (nba, nfl, nhl)')

    args = parser.parse_args()

    # Generate combos
    generate_todays_correlated_combos(sport=args.sport)


if __name__ == "__main__":
    main()
