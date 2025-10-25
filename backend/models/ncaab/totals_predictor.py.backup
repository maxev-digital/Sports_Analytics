#!/usr/bin/env python3
"""
NCAA Basketball Totals Predictor
Pace-based methodology using KenPom metrics
"""

import pandas as pd
import numpy as np

class NCAABTotalsPredictor:
    def __init__(self, kenpom_data, home_court_advantage=3.5, league_avg_eff=105.0):
        self.kenpom = kenpom_data
        self.hca = home_court_advantage
        self.league_avg = league_avg_eff
        
        # Create team lookup dictionary
        self.team_stats = {}
        for _, row in kenpom_data.iterrows():
            team_name = str(row['Team']).strip()
            self.team_stats[team_name] = {
                'tempo': row['AdjTempo'],
                'off_eff': row['AdjOffEff'],
                'def_eff': row['AdjDefEff']
            }
    
    def find_team(self, team_name):
        """Find team stats with fuzzy matching"""
        team_name = str(team_name).strip()
        
        # Exact match
        if team_name in self.team_stats:
            return self.team_stats[team_name]
        
        # Partial match
        for kenpom_team, stats in self.team_stats.items():
            if team_name.lower() in kenpom_team.lower() or kenpom_team.lower() in team_name.lower():
                return stats
        
        return None
    
    def predict_game(self, home_team, away_team):
        """Predict total points for a single game"""
        home_stats = self.find_team(home_team)
        away_stats = self.find_team(away_team)
        
        if not home_stats or not away_stats:
            return None
        
        # Calculate expected pace (geometric mean)
        expected_pace = np.sqrt(home_stats['tempo'] * away_stats['tempo'])
        
        # Calculate home team efficiency
        home_eff = home_stats['off_eff'] - (away_stats['def_eff'] - self.league_avg) + self.hca
        
        # Calculate away team efficiency
        away_eff = away_stats['off_eff'] - (home_stats['def_eff'] - self.league_avg)
        
        # Calculate expected points
        home_points = (home_eff / 100) * expected_pace
        away_points = (away_eff / 100) * expected_pace
        
        total = home_points + away_points
        
        return {
            'Expected_Pace': expected_pace,
            'Home_OffEff': home_eff,
            'Away_OffEff': away_eff,
            'Home_Points': home_points,
            'Away_Points': away_points,
            'Model_Total': total,
            'Home_Tempo': home_stats['tempo'],
            'Away_Tempo': away_stats['tempo']
        }
    
    def predict_all_games(self, odds_data):
        """Generate predictions for all games with odds"""
        if odds_data is None or len(odds_data) == 0:
            print("   ⚠️  No odds data provided")
            return pd.DataFrame()
        
        predictions = []
        
        for _, game in odds_data.iterrows():
            home_team = game['Home_Team']
            away_team = game['Away_Team']
            market_total = game['Market_Total']
            
            pred = self.predict_game(home_team, away_team)
            
            if pred:
                model_total = pred['Model_Total']
                edge = abs(model_total - market_total)
                
                # Determine recommendation
                if model_total > market_total:
                    recommendation = f"OVER {market_total:.1f}"
                else:
                    recommendation = f"UNDER {market_total:.1f}"
                
                # Assign confidence
                if edge >= 5.0:
                    confidence = "HIGH"
                    bet = "YES"
                elif edge >= 3.0:
                    confidence = "MEDIUM"
                    bet = "YES"
                elif edge >= 1.5:
                    confidence = "LOW"
                    bet = "YES"
                else:
                    confidence = "NONE"
                    bet = "NO"
                
                predictions.append({
                    'Date': game.get('Date', ''),
                    'Time': game.get('Time', ''),
                    'Home_Team': home_team,
                    'Away_Team': away_team,
                    'Home_Tempo': pred['Home_Tempo'],
                    'Away_Tempo': pred['Away_Tempo'],
                    'Expected_Pace': pred['Expected_Pace'],
                    'Home_OffEff': pred['Home_OffEff'],
                    'Home_DefEff': 0,  # Not used in display
                    'Away_OffEff': pred['Away_OffEff'],
                    'Away_DefEff': 0,  # Not used in display
                    'Home_Points': pred['Home_Points'],
                    'Away_Points': pred['Away_Points'],
                    'Model_Total': model_total,
                    'Market_Total': market_total,
                    'Edge': edge,
                    'Recommendation': recommendation,
                    'Confidence': confidence,
                    'Bet': bet
                })
            else:
                print(f"   ⚠️  Could not find stats for: {home_team} vs {away_team}")
        
        df = pd.DataFrame(predictions)
        
        if len(df) > 0:
            # Sort by edge (highest first)
            df = df.sort_values('Edge', ascending=False)
            print(f"   ✅ {len(df)} predictions generated")
            print(f"   HIGH confidence: {len(df[df['Confidence'] == 'HIGH'])}")
            print(f"   MEDIUM confidence: {len(df[df['Confidence'] == 'MEDIUM'])}")
            print(f"   LOW confidence: {len(df[df['Confidence'] == 'LOW'])}")
        
        return df
