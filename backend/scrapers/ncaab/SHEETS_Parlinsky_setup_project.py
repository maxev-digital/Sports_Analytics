#!/usr/bin/env python3
"""
NBA Betting Model Project Setup Script
=====================================
This script creates the complete folder structure and installs required packages
for the NBA betting model project.

IMPORTANT: This is for educational purposes only. Sports betting involves 
significant financial risk. Only use with money you can afford to lose.
"""

import os
import subprocess
import sys

def create_directory(path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"✅ Created directory: {path}")
    else:
        print(f"📁 Directory already exists: {path}")

def create_file(path, content=""):
    """Create file with optional content"""
    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write(content)
        print(f"✅ Created file: {path}")
    else:
        print(f"📄 File already exists: {path}")

def install_packages():
    """Install required Python packages"""
    packages = [
        'pandas',
        'numpy', 
        'requests',
        'beautifulsoup4',
        'gspread',
        'google-auth',
        'google-auth-oauthlib',
        'google-auth-httplib2',
        'google-api-python-client',
        'python-dotenv'
    ]
    
    print("\n📦 Installing required packages...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed: {package}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install: {package}")

def main():
    print("🏀 NBA Betting Model Project Setup")
    print("=" * 50)
    print("Creating folder structure and installing packages...")
    print("\n⚠️  IMPORTANT: This is for educational purposes only!")
    print("⚠️  Sports betting involves significant financial risk!")
    print("⚠️  Only bet money you can afford to lose!\n")
    
    # Create main project directories
    directories = [
        "backend",
        "backend/scrapers",
        "backend/scrapers/nba",
        "backend/scrapers/odds", 
        "backend/models",
        "backend/models/nba",
        "backend/utils",
        "backend/sheets_integration",
        "backend/data",
        "backend/data/raw",
        "backend/data/raw/nba",
        "backend/data/predictions",
        "backend/data/tracking",
        "google_sheets",
        "google_sheets/credentials"
    ]
    
    print("📁 Creating directories...")
    for directory in directories:
        create_directory(directory)
    
    # Create main files with basic structure
    files_content = {
        "run_daily_predictions.py": '''#!/usr/bin/env python3
"""
NBA Betting Model - Master Daily Script
=====================================
This is the main script that runs the entire daily workflow.

USAGE: python run_daily_predictions.py

IMPORTANT DISCLAIMERS:
- This is for educational purposes only
- Sports betting involves significant financial risk
- No guarantee of profit - most bettors lose money
- Only bet money you can afford to lose completely
- Use strict bankroll management
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def main():
    """Main daily workflow - orchestrates all components"""
    print("🏀 NBA Daily Predictions Workflow")
    print("=" * 50)
    
    # TODO: Import and run all components
    # 1. Scrape NBA stats
    # 2. Fetch betting odds
    # 3. Analyze rest days
    # 4. Generate predictions
    # 5. Calculate edges
    # 6. Log predictions
    # 7. Upload to Google Sheets
    
    print("⚠️  Remember: This is for educational purposes only!")
    print("⚠️  Sports betting involves significant financial risk!")

if __name__ == "__main__":
    main()
''',
        
        "backend/scrapers/nba/nba_api_stats.py": '''"""
NBA Stats Scraper
================
Scrapes official NBA team statistics from NBA.com API
"""

import requests
import pandas as pd

class NBAStatscraper:
    """Scrapes NBA team stats from official NBA.com API"""
    
    def __init__(self):
        self.base_url = "https://stats.nba.com/stats/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_team_stats(self):
        """Get current season team statistics"""
        # TODO: Implement NBA stats scraping
        pass
    
    def get_pace_stats(self):
        """Get team pace statistics"""
        # TODO: Implement pace stats scraping
        pass
''',

        "backend/scrapers/nba/schedule_scraper.py": '''"""
NBA Schedule Scraper & Rest Days Analyzer
=========================================
Scrapes NBA schedule and calculates rest days for each team
"""

import requests
import pandas as pd
from datetime import datetime, timedelta

class ScheduleScraper:
    """Scrapes NBA schedule and analyzes rest days"""
    
    def __init__(self):
        self.base_url = "https://stats.nba.com/stats/"
    
    def get_schedule(self):
        """Get full season schedule"""
        # TODO: Implement schedule scraping
        pass
    
    def calculate_rest_days(self, team_id, game_date):
        """Calculate days of rest for a team before a game"""
        # TODO: Implement rest days calculation
        pass
    
    def detect_back_to_back(self):
        """Detect back-to-back game situations"""
        # TODO: Implement B2B detection
        pass
''',

        "backend/scrapers/odds/odds_api_scraper.py": '''"""
Betting Odds Scraper
===================
Scrapes betting odds from multiple sportsbooks via Odds API
"""

import requests
import pandas as pd

class OddsScraper:
    """Scrapes betting odds from Odds API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4/sports"
    
    def get_nba_odds(self):
        """Get NBA totals odds from multiple sportsbooks"""
        # TODO: Implement odds scraping
        pass
    
    def calculate_consensus_total(self, odds_data):
        """Calculate consensus total from multiple books"""
        # TODO: Implement consensus calculation
        pass
''',

        "backend/models/nba/totals_predictor.py": '''"""
NBA Totals Prediction Model
==========================
Predicts NBA game totals using pace-based methodology with rest day adjustments
"""

import pandas as pd
import numpy as np

class TotalsPredictor:
    """NBA totals prediction model with rest day analysis"""
    
    def __init__(self):
        self.home_court_advantage = 2.5
    
    def predict_total(self, home_team, away_team, rest_data=None):
        """Predict game total with optional rest day adjustments"""
        # TODO: Implement prediction model
        pass
    
    def calculate_pace_adjustment(self, rest_days):
        """Calculate pace adjustment based on rest days"""
        if rest_days == 0:  # Back-to-back
            return -2.0
        elif rest_days >= 3:  # Well rested
            return 1.5
        else:
            return 0.0
    
    def calculate_edge(self, predicted_total, market_total):
        """Calculate edge and assign confidence level"""
        edge = abs(predicted_total - market_total)
        
        if edge >= 10:
            return edge, "NONE"  # Too high, proceed with caution
        elif edge >= 5:
            return edge, "HIGH"
        elif edge >= 3:
            return edge, "MEDIUM"
        elif edge >= 2:
            return edge, "LOW"
        else:
            return edge, "NONE"
''',

        "backend/utils/performance_tracker.py": '''"""
Performance Tracking System
===========================
Tracks predictions, records results, and calculates performance metrics
"""

import pandas as pd
import csv
from datetime import datetime
import os

class PerformanceTracker:
    """Tracks model performance and calculates metrics"""
    
    def __init__(self):
        self.data_dir = "backend/data/tracking"
        self.predictions_file = f"{self.data_dir}/predictions_log.csv"
        self.results_file = f"{self.data_dir}/results_log.csv"
        self.performance_file = f"{self.data_dir}/performance_summary.csv"
    
    def log_prediction(self, game_data):
        """Log a prediction to the tracking system"""
        # TODO: Implement prediction logging
        pass
    
    def record_result(self, game_id, final_score):
        """Record actual game result"""
        # TODO: Implement result recording
        pass
    
    def calculate_performance(self):
        """Calculate win rate, ROI, and other metrics"""
        # TODO: Implement performance calculation
        pass
    
    def show_interactive_menu(self):
        """Show interactive menu for tracking operations"""
        while True:
            print("\\n📊 Performance Tracking Menu")
            print("1. Log today's predictions")
            print("2. Record game results")
            print("3. View performance summary")
            print("4. Export to CSV")
            print("5. Exit")
            
            choice = input("\\nSelect option (1-5): ")
            
            if choice == "1":
                self.log_todays_predictions()
            elif choice == "2":
                self.record_game_results()
            elif choice == "3":
                self.show_performance_summary()
            elif choice == "4":
                self.export_to_csv()
            elif choice == "5":
                break
            else:
                print("Invalid option. Please try again.")
    
    def log_todays_predictions(self):
        """Log today's predictions"""
        print("TODO: Implement prediction logging")
    
    def record_game_results(self):
        """Record game results"""
        print("TODO: Implement result recording")
    
    def show_performance_summary(self):
        """Show performance summary"""
        print("TODO: Implement performance display")
    
    def export_to_csv(self):
        """Export performance data to CSV"""
        print("TODO: Implement CSV export")

if __name__ == "__main__":
    tracker = PerformanceTracker()
    tracker.show_interactive_menu()
''',

        "backend/sheets_integration/nba_sheets_uploader.py": '''"""
Google Sheets Integration
========================
Uploads predictions to Google Sheets with formatting
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

class SheetsUploader:
    """Uploads NBA predictions to Google Sheets"""
    
    def __init__(self, credentials_path):
        self.credentials_path = credentials_path
        self.gc = None
    
    def authenticate(self):
        """Authenticate with Google Sheets API"""
        # TODO: Implement Google Sheets authentication
        pass
    
    def upload_predictions(self, predictions_df):
        """Upload predictions with formatting"""
        # TODO: Implement upload with color coding
        pass
    
    def format_sheet(self, worksheet):
        """Apply formatting to the sheet"""
        # TODO: Implement formatting (colors, borders, etc.)
        pass
''',

        "requirements.txt": '''# NBA Betting Model Requirements
# ==============================

# Data manipulation
pandas>=1.5.0
numpy>=1.21.0

# Web scraping and API calls
requests>=2.28.0
beautifulsoup4>=4.11.0

# Google Sheets integration
gspread>=5.7.0
google-auth>=2.15.0
google-auth-oauthlib>=0.8.0
google-auth-httplib2>=0.1.0
google-api-python-client>=2.70.0

# Environment management
python-dotenv>=0.19.0

# Optional: Data visualization
matplotlib>=3.6.0
seaborn>=0.12.0
''',

        ".env.example": '''# NBA Betting Model Environment Variables
# =====================================
# Copy this file to .env and fill in your actual values

# Odds API Configuration
ODDS_API_KEY=your_odds_api_key_here

# Google Sheets Configuration  
GOOGLE_SHEETS_ID=your_google_sheets_id_here

# Other Configuration
PROJECT_NAME=NBA_Betting_Model
DEBUG=False
''',

        "README.md": '''# NBA Betting Model

## ⚠️ IMPORTANT DISCLAIMERS

**This is for educational purposes only.**
- Sports betting involves significant financial risk
- No guarantee of profit - most bettors lose money
- Only bet money you can afford to lose completely
- Use strict bankroll management
- Know when to walk away

## Quick Start

1. Install Python 3.8 or higher
2. Run the setup script: `python setup_project.py`
3. Copy `.env.example` to `.env` and fill in your API keys
4. Run daily predictions: `python run_daily_predictions.py`

## Daily Workflow

Every morning (2 minutes):
```bash
python run_daily_predictions.py
```

After games are played:
```bash
python backend/utils/performance_tracker.py
```

## Project Structure

```
project/
├── run_daily_predictions.py    # Master script
├── backend/
│   ├── scrapers/              # Data collection
│   ├── models/                # Prediction models
│   ├── utils/                 # Utilities
│   ├── sheets_integration/    # Google Sheets
│   └── data/                  # Data storage
└── google_sheets/             # Credentials
```

## Responsible Gambling Resources

- National Council on Problem Gambling: 1-800-522-4700
- Website: ncpgambling.org
- Gamblers Anonymous: gamblersanonymous.org
'''
    }
    
    print("\n📄 Creating files with basic structure...")
    for file_path, content in files_content.items():
        create_file(file_path, content)
    
    # Create empty CSV files
    csv_files = [
        "backend/data/tracking/predictions_log.csv",
        "backend/data/tracking/results_log.csv", 
        "backend/data/tracking/performance_summary.csv"
    ]
    
    for csv_file in csv_files:
        create_file(csv_file, "")
    
    # Create __init__.py files for Python packages
    init_files = [
        "backend/__init__.py",
        "backend/scrapers/__init__.py",
        "backend/scrapers/nba/__init__.py",
        "backend/scrapers/odds/__init__.py",
        "backend/models/__init__.py",
        "backend/models/nba/__init__.py",
        "backend/utils/__init__.py",
        "backend/sheets_integration/__init__.py"
    ]
    
    for init_file in init_files:
        create_file(init_file, "# Python package init file\\n")
    
    # Install packages
    install_packages()
    
    print("\n" + "=" * 60)
    print("✅ PROJECT SETUP COMPLETE!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Copy .env.example to .env and add your API keys")
    print("2. Get an Odds API key from: https://the-odds-api.com/")
    print("3. Set up Google Sheets authentication")
    print("4. Use AI to fill in the TODO sections in each file")
    print("5. Read the full documentation before using")
    print("\n⚠️  REMEMBER: This is for educational purposes only!")
    print("⚠️  Sports betting involves significant financial risk!")
    print("⚠️  Only bet money you can afford to lose!")

if __name__ == "__main__":
    main()
