#!/usr/bin/env python3
"""
NCAA Basketball Daily Predictions - Master Script
Runs complete workflow: KenPom data → Odds → Predictions → Google Sheets
"""

import pandas as pd
import os
import sys
from datetime import datetime
import glob

# Add backend to path
sys.path.insert(0, 'backend')

try:
    from config import (
        ODDS_API_KEY, ODDS_API_SPORT, 
        GOOGLE_CREDENTIALS_PATH, GOOGLE_SHEET_ID,
        KENPOM_DATA_DIR, HOME_COURT_ADVANTAGE, LEAGUE_AVG_EFFICIENCY,
        HIGH_CONFIDENCE_EDGE, MEDIUM_CONFIDENCE_EDGE, LOW_CONFIDENCE_EDGE
    )
except ImportError:
    print("❌ Error: config.py not found or incomplete")
    print("   Run: python setup_ncaab.py")
    sys.exit(1)

# Import scrapers and models (will create these if needed)
try:
    from scrapers.odds.ncaab_odds_scraper import NCAABOddsScraper
except:
    print("⚠️  Odds scraper not found - will skip odds fetching")
    NCAABOddsScraper = None

try:
    from models.ncaab.totals_predictor import NCAABTotalsPredictor
except:
    print("⚠️  Prediction model not found - will create minimal version")
    NCAABTotalsPredictor = None

try:
    from sheets_integration.ncaab_sheets_uploader import NCAABSheetsUploader
except:
    print("⚠️  Sheets uploader not found - will skip Google Sheets")
    NCAABSheetsUploader = None


class NCAABPredictionWorkflow:
    def __init__(self):
        self.start_time = datetime.now()
        self.kenpom_data = None
        self.odds_data = None
        self.predictions = None
        
    def print_header(self):
        """Print workflow header"""
        print("="*70)
        print("NCAA BASKETBALL DAILY PREDICTIONS")
        print("="*70)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
    
    def load_kenpom_data(self):
        """Load most recent KenPom data"""
        print("STEP 1: LOADING KENPOM STATISTICS")
        print("-"*70)
        
        # Find most recent KenPom CSV
        csv_pattern = f"{KENPOM_DATA_DIR}/kenpom_ratings_*.csv"
        csv_files = glob.glob(csv_pattern)
        
        if not csv_files:
            print(f"❌ No KenPom data found in: {KENPOM_DATA_DIR}")
            print("   Run: python backend/scrapers/ncaab/kenpom_scraper_selenium.py")
            return False
        
        latest_csv = max(csv_files)
        
        try:
            self.kenpom_data = pd.read_csv(latest_csv)
            
            # Verify required columns
            required_cols = ['Team', 'AdjTempo', 'AdjOffEff', 'AdjDefEff']
            missing = [col for col in required_cols if col not in self.kenpom_data.columns]
            
            if missing:
                print(f"❌ Missing columns in KenPom data: {missing}")
                return False
            
            print(f"✅ Loaded {len(self.kenpom_data)} teams from KenPom")
            print(f"   File: {os.path.basename(latest_csv)}")
            print(f"   Tempo range: {self.kenpom_data['AdjTempo'].min():.1f} - {self.kenpom_data['AdjTempo'].max():.1f}")
            print(f"   OffEff range: {self.kenpom_data['AdjOffEff'].min():.1f} - {self.kenpom_data['AdjOffEff'].max():.1f}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading KenPom data: {str(e)}")
            return False
    
    def fetch_odds(self):
        """Fetch betting odds from API"""
        print("\nSTEP 2: FETCHING BETTING ODDS")
        print("-"*70)
        
        if not NCAABOddsScraper:
            print("⚠️  Odds scraper not available - skipping")
            return False
        
        try:
            scraper = NCAABOddsScraper(api_key=ODDS_API_KEY)
            self.odds_data = scraper.fetch_odds()
            
            if self.odds_data is not None and len(self.odds_data) > 0:
                print(f"✅ Found {len(self.odds_data)} games with betting lines")
                return True
            else:
                print("⚠️  No games with odds found (might be offseason)")
                return False
                
        except Exception as e:
            print(f"❌ Error fetching odds: {str(e)}")
            return False
    
    def generate_predictions(self):
        """Generate predictions using KenPom data and odds"""
        print("\nSTEP 3: GENERATING PREDICTIONS")
        print("-"*70)
        
        if self.kenpom_data is None:
            print("❌ Cannot generate predictions without KenPom data")
            return False
        
        # Use predictor if available, otherwise create minimal predictions
        if NCAABTotalsPredictor:
            try:
                predictor = NCAABTotalsPredictor(kenpom_data=self.kenpom_data)
                self.predictions = predictor.predict_all_games(odds_data=self.odds_data)
                
                if self.predictions is not None and len(self.predictions) > 0:
                    print(f"✅ Generated {len(self.predictions)} predictions")
                    return True
                else:
                    print("⚠️  No predictions generated")
                    return False
                    
            except Exception as e:
                print(f"❌ Error generating predictions: {str(e)}")
                return False
        else:
            print("⚠️  Prediction model not available")
            return False
    
    def upload_to_sheets(self):
        """Upload predictions to Google Sheets"""
        print("\nSTEP 4: UPLOADING TO GOOGLE SHEETS")
        print("-"*70)
        
        if self.predictions is None or len(self.predictions) == 0:
            print("⚠️  No predictions to upload")
            return False
        
        if not NCAABSheetsUploader:
            print("⚠️  Sheets uploader not available - skipping")
            return False
        
        try:
            uploader = NCAABSheetsUploader(
                credentials_path=GOOGLE_CREDENTIALS_PATH,
                sheet_id=GOOGLE_SHEET_ID
            )
            
            uploader.upload_predictions(self.predictions)
            print(f"✅ Uploaded to Google Sheets")
            print(f"🔗 View: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading to Google Sheets: {str(e)}")
            return False
    
    def show_top_bets(self):
        """Display top betting opportunities"""
        if self.predictions is None or len(self.predictions) == 0:
            return
        
        print("\n" + "="*70)
        print("🏆 TOP 5 BETTING OPPORTUNITIES")
        print("="*70)
        
        # Sort by edge (highest first)
        if 'Edge' in self.predictions.columns:
            top_bets = self.predictions.nlargest(5, 'Edge')
            
            for i, row in enumerate(top_bets.itertuples(), 1):
                confidence = getattr(row, 'Confidence', 'UNKNOWN')
                edge = getattr(row, 'Edge', 0)
                home_team = getattr(row, 'Home_Team', 'Home')
                away_team = getattr(row, 'Away_Team', 'Away')
                model_total = getattr(row, 'Model_Total', 0)
                market_total = getattr(row, 'Market_Total', 0)
                recommendation = getattr(row, 'Recommendation', 'N/A')
                
                print(f"\n#{i} - {confidence} CONFIDENCE ({edge:.1f} point edge)")
                print(f"   {away_team} @ {home_team}")
                print(f"   Model: {model_total:.1f} | Market: {market_total:.1f}")
                print(f"   Bet: {recommendation} {market_total:.1f}")
        else:
            print("   ⚠️  Edge calculation not available")
    
    def run(self):
        """Run complete workflow"""
        self.print_header()
        
        # Step 1: Load KenPom
        if not self.load_kenpom_data():
            print("\n❌ Workflow failed at Step 1")
            return False
        
        # Step 2: Fetch Odds
        odds_success = self.fetch_odds()
        if not odds_success:
            print("   ⚠️  Continuing without live odds data")
        
        # Step 3: Generate Predictions
        if not self.generate_predictions():
            print("\n❌ Workflow failed at Step 3")
            return False
        
        # Step 4: Upload to Sheets
        sheets_success = self.upload_to_sheets()
        if not sheets_success:
            print("   ⚠️  Predictions generated but not uploaded to Sheets")
        
        # Show top bets
        self.show_top_bets()
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "="*70)
        print("✅ WORKFLOW COMPLETE")
        print(f"Time: {int(duration // 60)}m {int(duration % 60)}s")
        print("="*70)
        
        return True


def main():
    """Main entry point"""
    workflow = NCAABPredictionWorkflow()
    success = workflow.run()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
