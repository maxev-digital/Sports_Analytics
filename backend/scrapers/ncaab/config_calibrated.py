"""
NCAA Basketball Model Configuration - CALIBRATED VERSION
Fixed to reduce the +7 point prediction bias found in backtesting
"""

# Odds API Configuration
ODDS_API_KEY = "3b91452fcbaa6deffecb2e5843655099"
ODDS_API_SPORT = "basketball_ncaab"  # NCAA Basketball

# Google Sheets Configuration
GOOGLE_CREDENTIALS_PATH = "google_sheets/credentials/service-account-key.json"
GOOGLE_SHEET_ID = "YOUR_SHEET_ID_HERE"  # Replace with your actual sheet ID

# Data Paths
KENPOM_DATA_DIR = "backend/data/raw/ncaab"
PREDICTIONS_OUTPUT_DIR = "backend/data/predictions"
TRACKING_DIR = "backend/data/tracking"

# Model Parameters - CALIBRATED BASED ON BACKTEST RESULTS
HOME_COURT_ADVANTAGE = 3.0  # Reduced from 3.5
LEAGUE_AVG_EFFICIENCY = 98.0  # Reduced from 105.0 (major fix for +7 point bias)

# Confidence Thresholds
HIGH_CONFIDENCE_EDGE = 5.0  # 5+ point edge
MEDIUM_CONFIDENCE_EDGE = 3.0  # 3-5 point edge
LOW_CONFIDENCE_EDGE = 1.5  # 1.5-3 point edge