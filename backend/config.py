"""Configuration for Multi-Sport Live Betting System"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Odds API
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
SPORTS = [
    "basketball_nba",             # NBA
    "americanfootball_nfl",       # NFL
    "americanfootball_ncaaf",     # NCAA Football
    "icehockey_nhl",              # NHL
    "baseball_mlb",               # MLB
    "basketball_ncaab",           # NCAA Basketball
    # DISABLED TO SAVE API CREDITS:
    # "golf_pga_championship",      # PGA Golf
    # "tennis_atp",                 # Tennis (ATP - Men's)
    # "tennis_wta",                 # Tennis (WTA - Women's)
    # "mma_mixed_martial_arts",     # MMA/UFC
]
REGION = "us,us2,uk,au,eu"  # Fetch from all regions for maximum bookmaker coverage
MARKETS = "h2h,spreads,totals"  # Fetch money lines, spreads, and totals

# Polling
POLL_INTERVAL = 5  # seconds (5 seconds - fastest recommended rate)

# Edge detection
MIN_EDGE = 5.0  # points
