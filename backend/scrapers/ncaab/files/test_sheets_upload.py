#!/usr/bin/env python3
"""
Test NCAA Basketball Google Sheets Upload
Creates fake predictions and uploads to verify Sheets integration
"""

import pandas as pd
import sys
import random
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, 'backend')

try:
    from config import GOOGLE_CREDENTIALS_PATH, GOOGLE_SHEET_ID
    from sheets_integration.ncaab_sheets_uploader import NCAABSheetsUploader
except ImportError as e:
    print(f"❌ Error importing: {str(e)}")
    print("   Make sure you're in C:\\Users\\nashr\\")
    sys.exit(1)


def generate_fake_predictions(num_games=20):
    """Generate fake NCAA Basketball predictions for testing"""
    
    teams = [
        "Duke", "North Carolina", "Kansas", "Kentucky", "Gonzaga",
        "Villanova", "Michigan", "UCLA", "Arizona", "Texas",
        "Houston", "Purdue", "Connecticut", "Tennessee", "Arkansas",
        "Baylor", "Auburn", "Alabama", "Wisconsin", "Illinois"
    ]
    
    conferences = ["ACC", "Big 12", "Big Ten", "SEC", "Big East", "Pac-12"]
    
    predictions = []
    
    # Generate games for next 3 days
    for day in range(3):
        game_date = datetime.now() + timedelta(days=day)
        
        for game_num in range(num_games // 3):
            # Random teams
            home_team = random.choice(teams)
            away_team = random.choice([t for t in teams if t != home_team])
            
            # Random tempos (60-75 possessions)
            home_tempo = round(random.uniform(60, 75), 1)
            away_tempo = round(random.uniform(60, 75), 1)
            expected_pace = round((home_tempo + away_tempo) / 2, 1)
            
            # Random efficiencies (95-125 points per 100 possessions)
            home_off_eff = round(random.uniform(95, 125), 1)
            away_off_eff = round(random.uniform(95, 125), 1)
            
            # Calculate points
            home_points = round((home_off_eff / 100) * expected_pace, 1)
            away_points = round((away_off_eff / 100) * expected_pace, 1)
            model_total = round(home_points + away_points, 1)
            
            # Market total (slightly different from model)
            market_total = model_total + random.uniform(-8, 8)
            market_total = round(market_total * 2) / 2  # Round to .0 or .5
            
            # Edge and recommendation
            edge = abs(model_total - market_total)
            recommendation = f"OVER {market_total}" if model_total > market_total else f"UNDER {market_total}"
            
            # Confidence
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
                'Date': game_date.strftime('%m/%d'),
                'Time': f"{random.randint(5, 9)}:00 PM",
                'Home_Team': home_team,
                'Away_Team': away_team,
                'Home_Tempo': home_tempo,
                'Away_Tempo': away_tempo,
                'Expected_Pace': expected_pace,
                'Home_OffEff': home_off_eff,
                'Home_DefEff': 0,  # Not displayed
                'Away_OffEff': away_off_eff,
                'Away_DefEff': 0,  # Not displayed
                'Home_Points': home_points,
                'Away_Points': away_points,
                'Model_Total': model_total,
                'Market_Total': market_total,
                'Edge': round(edge, 1),
                'Recommendation': recommendation,
                'Confidence': confidence,
                'Bet': bet
            })
    
    df = pd.DataFrame(predictions)
    
    # Sort by edge (highest first)
    df = df.sort_values('Edge', ascending=False)
    
    return df


def main():
    """Test Google Sheets upload with fake data"""
    print("="*70)
    print("NCAA BASKETBALL - GOOGLE SHEETS UPLOAD TEST")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Generate fake predictions
    print("📊 Step 1: Generating fake predictions...")
    df = generate_fake_predictions(num_games=20)
    print(f"   ✅ Generated {len(df)} fake predictions")
    print(f"   HIGH confidence: {len(df[df['Confidence'] == 'HIGH'])}")
    print(f"   MEDIUM confidence: {len(df[df['Confidence'] == 'MEDIUM'])}")
    print(f"   LOW confidence: {len(df[df['Confidence'] == 'LOW'])}")
    
    # Display top 5
    print("\n🏆 Top 5 Predictions (by edge):")
    print("-"*70)
    for i, row in enumerate(df.head(5).itertuples(), 1):
        print(f"#{i} - {row.Confidence} CONFIDENCE ({row.Edge} point edge)")
        print(f"   {row.Away_Team} @ {row.Home_Team}")
        print(f"   Model: {row.Model_Total} | Market: {row.Market_Total}")
        print(f"   Bet: {row.Recommendation}\n")
    
    # Upload to Google Sheets
    print("☁️  Step 2: Uploading to Google Sheets...")
    try:
        uploader = NCAABSheetsUploader(
            credentials_path=GOOGLE_CREDENTIALS_PATH,
            sheet_id=GOOGLE_SHEET_ID
        )
        
        uploader.upload_predictions(df)
        
        print(f"✅ Successfully uploaded {len(df)} predictions!")
        print(f"🔗 View your sheet: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}")
        print("")
        print("="*70)
        print("TEST COMPLETE - Check your Google Sheet!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"❌ Error uploading to Google Sheets: {str(e)}")
        import traceback
        print(f"\nDetails:\n{traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
