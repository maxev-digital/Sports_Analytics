#!/usr/bin/env python3
"""
NCAA Basketball Totals Predictor - ENHANCED VERSION
Pace-based methodology using KenPom metrics with intelligent team name mapping

FIXES: Team name mismatches that caused 69% of predictions to fail
"""

import pandas as pd
import numpy as np


# Comprehensive team name mapping to solve mismatches
TEAM_NAME_MAP = {
    # Major variations that cause 69% of failures
    'UConn': 'Connecticut',
    'FDU': 'Fairleigh Dickinson',
    'Cal State Fullerton': 'CS Fullerton',
    'College of Charleston': 'Charleston',
    'IU Indianapolis': 'IUPUI',
    'San Diego State': 'San Diego St.',
    'Purdue': 'Purdue',  # Avoid matching "Purdue Fort Wayne"
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
    
    # Additional common mappings to improve success rate
    'Illinois State': 'Illinois St.',
    'Cal State Northridge': 'CS Northridge',
    'Cal Poly': 'Cal Poly',
    'UT Martin': 'Tennessee Martin',
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
    'Pacific': 'Pacific',
    'Loyola Marymount': 'Loyola Marymount',
    'Pepperdine': 'Pepperdine',
    'Saint Mary\'s (CA)': 'Saint Mary\'s CA',
    'San Francisco': 'San Francisco',
    'Santa Clara': 'Santa Clara',
    'Gonzaga': 'Gonzaga',
    'Portland': 'Portland',
    'Stetson': 'Stetson',
}


class NCAABTotalsPredictor:
    def __init__(self, kenpom_data, home_court_advantage=3.5, league_avg_eff=105.0):
        self.kenpom = kenpom_data
        self.hca = home_court_advantage
        self.league_avg = league_avg_eff
        
        # Create team lookup dictionary and set for faster searches
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
        
        print(f"   ✅ Loaded {len(self.team_stats)} teams into predictor")
    
    def normalize_team_name(self, team_name):
        """Normalize team name using comprehensive mapping"""
        team_name = str(team_name).strip()
        
        # Direct mapping
        if team_name in TEAM_NAME_MAP:
            return TEAM_NAME_MAP[team_name]
        
        # Common suffix replacements
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
        """Enhanced team finder with comprehensive mapping and detailed logging"""
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
        
        # Step 4: Word matching (handles "Arizona" vs "Arizona St.")
        team_words = set(normalized.lower().split())
        
        # First try: All words from input appear in KenPom name
        for kp_team in self.kenpom_teams:
            kp_words = set(kp_team.lower().split())
            if team_words.issubset(kp_words) and len(team_words) > 0:
                self.successful_lookups += 1
                return self.team_stats[kp_team]
        
        # Second try: Main word matching (first word is usually school name)
        if team_words:
            main_word = list(team_words)[0]
            for kp_team in self.kenpom_teams:
                if main_word in kp_team.lower():
                    self.successful_lookups += 1
                    return self.team_stats[kp_team]
        
        # No match found - track for improvement
        self.failed_lookups += 1
        return None
    
    def predict_game(self, home_team, away_team):
        """Predict total points for a single game"""
        home_stats = self.find_team(home_team)
        away_stats = self.find_team(away_team)
        
        if not home_stats or not away_stats:
            return None
        
        # Calculate expected pace (geometric mean)
        expected_pace = np.sqrt(home_stats['tempo'] * away_stats['tempo'])
        
        # Calculate home team efficiency (with home court advantage)
        home_eff = home_stats['off_eff'] - (away_stats['def_eff'] - self.league_avg) + self.hca
        
        # Calculate away team efficiency
        away_eff = away_stats['off_eff'] - (home_stats['def_eff'] - self.league_avg)
        
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
                    'Edge': round(edge, 1),
                    'Recommendation': recommendation,
                    'Confidence': confidence,
                    'Bet': bet
                })
        
        df = pd.DataFrame(predictions)
        
        if len(df) > 0:
            # Sort by edge (highest first)
            df = df.sort_values('Edge', ascending=False)
            print(f"   ✅ {len(df)} predictions generated")
            print(f"   HIGH confidence: {len(df[df['Confidence'] == 'HIGH'])}")
            print(f"   MEDIUM confidence: {len(df[df['Confidence'] == 'MEDIUM'])}")
            print(f"   LOW confidence: {len(df[df['Confidence'] == 'LOW'])}")
        
        # Print lookup statistics
        total_lookups = self.successful_lookups + self.failed_lookups
        if total_lookups > 0:
            success_rate = (self.successful_lookups / total_lookups) * 100
            print(f"   📊 Team lookup success rate: {success_rate:.1f}% ({self.successful_lookups}/{total_lookups})")
        
        return df


def test_team_mapping():
    """Test the team name mapping system"""
    print("="*70)
    print("TESTING ENHANCED TEAM NAME MAPPING")
    print("="*70)
    
    # Create fake KenPom data with common names
    fake_kenpom = pd.DataFrame({
        'Team': [
            'Connecticut', 'Fairleigh Dickinson', 'CS Fullerton', 'Charleston',
            'IUPUI', 'San Diego St.', 'Purdue', 'Kansas St.', 'Ohio St.',
            'Nebraska Omaha', 'UMKC', 'Illinois', 'Fresno St.'
        ],
        'AdjTempo': [70.0] * 13,
        'AdjOffEff': [110.0] * 13,
        'AdjDefEff': [100.0] * 13
    })
    
    predictor = NCAABTotalsPredictor(fake_kenpom)
    
    # Test problematic team names from diagnostic
    test_cases = [
        'UConn', 'FDU', 'Cal State Fullerton', 'College of Charleston',
        'IU Indianapolis', 'San Diego State', 'Purdue', 'Kansas State',
        'Ohio State', 'Omaha', 'Kansas City', 'Illinois', 'Fresno State'
    ]
    
    print("\nTesting team name resolution:")
    print(f"{'Input Name':<25} {'→':<3} {'Matched KenPom Name':<25} {'Status'}")
    print("-" * 70)
    
    successful = 0
    for test_name in test_cases:
        stats = predictor.find_team(test_name)
        if stats:
            print(f"{test_name:<25} → {'SUCCESS':<25} ✅")
            successful += 1
        else:
            print(f"{test_name:<25} → {'NOT FOUND':<25} ❌")
    
    success_rate = (successful / len(test_cases)) * 100
    print(f"\n📊 Test Results: {successful}/{len(test_cases)} successful ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT! Team mapping should dramatically reduce failures")
    elif success_rate >= 70:
        print("✅ GOOD! Significant improvement expected")
    else:
        print("⚠️  NEEDS WORK! Add more mappings for missing teams")


if __name__ == "__main__":
    test_team_mapping()
