#!/usr/bin/env python3
"""
NCAA Basketball Totals Predictor - IMPROVED METHODOLOGY
Fixes the high variance issue by using more conservative adjustments
"""

import pandas as pd
import numpy as np

# Comprehensive team name mapping (keeping the working part)
TEAM_NAME_MAP = {
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
    'Samford': 'Samford',
    'Vermont': 'Vermont',
    'Colgate': 'Colgate',
    'Clemson': 'Clemson',
    'Oakland': 'Oakland',
    'Grand Canyon': 'Grand Canyon',
}

class NCAABTotalsPredictor:
    def __init__(self, kenpom_data, home_court_advantage=3.5, league_avg_eff=105.0):
        self.kenpom = kenpom_data
        self.hca = home_court_advantage
        self.league_avg = league_avg_eff
        
        # Create team lookup dictionary
        self.team_stats = {}
        self.kenpom_teams = set()
        self.successful_lookups = 0
        self.failed_lookups = 0
        
        for _, row in kenpom_data.iterrows():
            team_name = str(row['Team']).strip()
            self.kenpom_teams.add(team_name)
            self.team_stats[team_name] = {
                'tempo': row['AdjTempo'],
                'off_eff': row['AdjOffEff'],
                'def_eff': row['AdjDefEff']
            }
    
    def normalize_team_name(self, team_name):
        """Normalize team name using comprehensive mapping"""
        team_name = str(team_name).strip()
        
        if team_name in TEAM_NAME_MAP:
            return TEAM_NAME_MAP[team_name]
        
        normalized = team_name
        suffix_replacements = {
            ' State': ' St.',
            ' (OH)': ' OH',
            ' (FL)': ' FL',
            ' (NY)': ' NY',
            ' (CA)': ' CA',
        }
        
        for old_suffix, new_suffix in suffix_replacements.items():
            if normalized.endswith(old_suffix):
                normalized = normalized[:-len(old_suffix)] + new_suffix
        
        return normalized
    
    def find_team(self, team_name):
        """Enhanced team finder with comprehensive mapping"""
        original_name = str(team_name).strip()
        
        # Step 1: Exact match
        if original_name in self.team_stats:
            self.successful_lookups += 1
            return self.team_stats[original_name]
        
        # Step 2: Use mapping
        normalized = self.normalize_team_name(original_name)
        if normalized in self.team_stats:
            self.successful_lookups += 1
            return self.team_stats[normalized]
        
        # Step 3: Case-insensitive exact match
        normalized_lower = normalized.lower()
        for kp_team in self.kenpom_teams:
            if kp_team.lower() == normalized_lower:
                self.successful_lookups += 1
                return self.team_stats[kp_team]
        
        # Step 4: Word matching
        team_words = set(normalized.lower().split())
        
        for kp_team in self.kenpom_teams:
            kp_words = set(kp_team.lower().split())
            if team_words.issubset(kp_words) and len(team_words) > 0:
                self.successful_lookups += 1
                return self.team_stats[kp_team]
        
        self.failed_lookups += 1
        return None
    
    def predict_game(self, home_team, away_team):
        """IMPROVED prediction methodology with more conservative adjustments"""
        home_stats = self.find_team(home_team)
        away_stats = self.find_team(away_team)
        
        if not home_stats or not away_stats:
            return None
        
        # IMPROVED METHOD 1: Use arithmetic mean for pace (more stable than geometric)
        expected_pace = (home_stats['tempo'] + away_stats['tempo']) / 2
        
        # IMPROVED METHOD 2: More conservative efficiency adjustments
        # Reduce the impact of defensive efficiency differences
        
        # Original method was too aggressive with adjustments
        # home_eff = home_stats['off_eff'] - (away_stats['def_eff'] - self.league_avg) + self.hca
        
        # NEW METHOD: Cap the defensive adjustments to avoid extreme predictions
        def_adjustment_home = min(max(away_stats['def_eff'] - self.league_avg, -10), 10)
        def_adjustment_away = min(max(home_stats['def_eff'] - self.league_avg, -10), 10)
        
        home_eff = home_stats['off_eff'] - def_adjustment_home + self.hca
        away_eff = away_stats['off_eff'] - def_adjustment_away
        
        # IMPROVED METHOD 3: Apply a regression to the mean factor
        # Extreme efficiency predictions get pulled back toward league average
        regression_factor = 0.85  # Pull 15% back toward average
        
        home_eff = self.league_avg + (home_eff - self.league_avg) * regression_factor
        away_eff = self.league_avg + (away_eff - self.league_avg) * regression_factor
        
        # Calculate expected points
        home_points = (home_eff / 100) * expected_pace
        away_points = (away_eff / 100) * expected_pace
        
        total = home_points + away_points
        
        return {
            'Expected_Pace': round(expected_pace, 1),
            'Home_OffEff': round(home_eff, 1),
            'Away_OffEff': round(away_eff, 1),
            'Home_Points': round(home_points, 1),
            'Away_Points': round(away_points, 1),
            'Model_Total': round(total, 1),
            'Home_Tempo': home_stats['tempo'],
            'Away_Tempo': away_stats['tempo']
        }
    
    def predict_all_games(self, odds_data):
        """Generate predictions for all games with odds"""
        if odds_data is None or len(odds_data) == 0:
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
                
                if model_total > market_total:
                    recommendation = f"OVER {market_total:.1f}"
                else:
                    recommendation = f"UNDER {market_total:.1f}"
                
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
                    'Home_DefEff': 0,
                    'Away_OffEff': pred['Away_OffEff'],
                    'Away_DefEff': 0,
                    'Home_Points': pred['Home_Points'],
                    'Away_Points': pred['Away_Points'],
                    'Model_Total': model_total,
                    'Market_Total': market_total,
                    'Edge': round(edge, 1),
                    'Recommendation': recommendation,
                    'Confidence': confidence,
                    'Bet': bet
                })
        
        df = pd.DataFrame(predictions)
        
        if len(df) > 0:
            df = df.sort_values('Edge', ascending=False)
        
        return df
