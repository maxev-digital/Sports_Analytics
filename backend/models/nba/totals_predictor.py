#!/usr/bin/env python3
"""
NBA Totals Predictor
Uses pace and offensive/defensive efficiency to predict game totals
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

class NBATotalsPredictor:
    """Predict NBA game totals using team pace and efficiency stats"""
    
    def __init__(self, team_stats_df):
        """
        Initialize with team statistics DataFrame
        
        Required columns:
        - team_name, pace, off_rating, def_rating
        """
        self.team_stats = team_stats_df.set_index('team_name')
        self.league_avg_pace = team_stats_df['pace'].mean()
        self.league_avg_off = team_stats_df['off_rating'].mean()
        self.league_avg_def = team_stats_df['def_rating'].mean()
        
        print(f"League Averages:")
        print(f"  Pace: {self.league_avg_pace:.1f}")
        print(f"  Off Rating: {self.league_avg_off:.1f}")
        print(f"  Def Rating: {self.league_avg_def:.1f}")
    
    def predict_game_total(self, home_team, away_team, game_context=None):
        """
        Predict total points for an NBA game
        
        Args:
            home_team: Home team name
            away_team: Away team name
            game_context: Dict with rest_days, back_to_back flags
        
        Returns:
            Dict with prediction details
        """
        
        if game_context is None:
            game_context = {}
        
        # Get team stats
        try:
            home_stats = self.team_stats.loc[home_team]
            away_stats = self.team_stats.loc[away_team]
        except KeyError as e:
            return {
                'error': f"Team not found: {e}",
                'predicted_total': None
            }
        
        # === STEP 1: CALCULATE EXPECTED PACE ===
        home_pace = home_stats['pace']
        away_pace = away_stats['pace']
        
        # Use geometric mean
        base_pace = (home_pace * away_pace) ** 0.5
        
        # === REST DAYS ADJUSTMENTS ===
        pace_adjustment = 0
        rest_factor_desc = []
        
        home_rest = game_context.get('home_days_rest')
        away_rest = game_context.get('away_days_rest')
        
        if home_rest is not None and away_rest is not None:
            # Back-to-back penalties (0 days rest)
            if home_rest == 0:
                pace_adjustment -= 2.0
                rest_factor_desc.append("Home B2B (-2.0)")
            if away_rest == 0:
                pace_adjustment -= 2.0
                rest_factor_desc.append("Away B2B (-2.0)")
            
            # Fresh team bonuses (3+ days rest)
            if home_rest >= 3 and away_rest <= 1:
                pace_adjustment += 1.5
                rest_factor_desc.append("Home Fresh (+1.5)")
            elif away_rest >= 3 and home_rest <= 1:
                pace_adjustment += 1.5
                rest_factor_desc.append("Away Fresh (+1.5)")
            
            # Both teams rested
            if home_rest >= 2 and away_rest >= 2:
                pace_adjustment += 1.0
                rest_factor_desc.append("Both Rested (+1.0)")
        
        expected_pace = base_pace + pace_adjustment
        
        # === STEP 2: CALCULATE EXPECTED EFFICIENCY ===
        
        # Home team offense vs Away team defense
        home_off = home_stats['off_rating']
        away_def = away_stats['def_rating']
        
        # Home court advantage
        home_expected_eff = home_off - (away_def - self.league_avg_def) + 2.5
        
        # Away team offense vs Home team defense
        away_off = away_stats['off_rating']
        home_def = home_stats['def_rating']
        
        away_expected_eff = away_off - (home_def - self.league_avg_def)
        
        # === STEP 3: CONVERT TO POINTS ===
        home_expected_points = (home_expected_eff / 100) * expected_pace
        away_expected_points = (away_expected_eff / 100) * expected_pace
        
        # === STEP 4: FINAL PREDICTION ===
        predicted_total = home_expected_points + away_expected_points
        
        return {
            'predicted_total': round(predicted_total, 1),
            'home_expected_points': round(home_expected_points, 1),
            'away_expected_points': round(away_expected_points, 1),
            'expected_pace': round(expected_pace, 1),
            'breakdown': {
                'home_pace': round(home_pace, 1),
                'away_pace': round(away_pace, 1),
                'home_off_rating': round(home_off, 1),
                'away_off_rating': round(away_off, 1),
                'home_def_rating': round(home_def, 1),
                'away_def_rating': round(away_def, 1),
                'pace_adjustment': round(pace_adjustment, 1),
                'rest_factors': rest_factor_desc if rest_factor_desc else ['None']
            }
        }
    
    def calculate_edge(self, predicted_total, market_total):
        """Calculate betting edge vs market"""
        edge = abs(predicted_total - market_total)
        
        recommendation = {
            'edge': round(edge, 1),
            'side': None,
            'confidence': None,
            'bet': False
        }
        
        # Edge thresholds
        if edge >= 5.0:
            recommendation['confidence'] = 'HIGH'
            recommendation['bet'] = True
        elif edge >= 3.0:
            recommendation['confidence'] = 'MEDIUM'
            recommendation['bet'] = True
        elif edge >= 2.0:
            recommendation['confidence'] = 'LOW'
            recommendation['bet'] = False
        else:
            recommendation['confidence'] = 'NONE'
            recommendation['bet'] = False
        
        if predicted_total > market_total:
            recommendation['side'] = 'OVER'
        else:
            recommendation['side'] = 'UNDER'
        
        return recommendation


if __name__ == "__main__":
    # Test the predictor
    print("="*60)
    print("NBA TOTALS PREDICTOR - TEST")
    print("="*60)
    
    # Load latest team stats
    stats_file = 'backend/data/raw/nba/nba_team_stats_latest.csv'
    
    if not os.path.exists(stats_file):
        print(f"❌ Team stats not found: {stats_file}")
        print("Run: python backend/scrapers/nba/nba_api_stats.py first")
    else:
        team_stats = pd.read_csv(stats_file)
        
        # Initialize predictor
        predictor = NBATotalsPredictor(team_stats)
        
        # Test prediction
        print("\n" + "="*60)
        print("TEST PREDICTION")
        print("="*60)
        
        # Use first two teams from stats
        home = team_stats.iloc[0]['team_name']
        away = team_stats.iloc[1]['team_name']
        
        print(f"\nGame: {away} @ {home}")
        
        result = predictor.predict_game_total(home, away)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"\n📊 Prediction:")
            print(f"  Total: {result['predicted_total']}")
            print(f"  {home}: {result['home_expected_points']}")
            print(f"  {away}: {result['away_expected_points']}")
            print(f"  Expected Pace: {result['expected_pace']}")
            
            # Test edge calculation
            market_total = 220.5
            edge = predictor.calculate_edge(result['predicted_total'], market_total)
            
            print(f"\n💰 vs Market Total: {market_total}")
            print(f"  Edge: {edge['edge']} points")
            print(f"  Recommendation: {edge['side']} ({edge['confidence']})")
            print(f"  Bet: {'YES ✅' if edge['bet'] else 'NO ❌'}")