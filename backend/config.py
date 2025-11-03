"""Configuration for Multi-Sport Live Betting System"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Odds API
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# BallDontLie API (NBA stats)
BALLDONTLIE_API_KEY = os.getenv("BALLDONTLIE_API_KEY", "")
BALLDONTLIE_API_BASE = "https://api.balldontlie.io/v1"
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

# Quiet Hours - Stop Odds API calls during low-traffic hours to save costs
QUIET_HOURS_ENABLED = False  # Set to False to disable quiet hours
QUIET_HOURS_START = 23  # 11 PM (24-hour format)
QUIET_HOURS_END = 9     # 9 AM (24-hour format)

# Edge detection
MIN_EDGE = 5.0  # points

# ESPN stats now enabled - NBA working, adding NFL/NHL back
ENABLE_ESPN_STATS = True  # Enables NFL, NHL, MLB stats fetching from ESPN
