"""Configuration for Multi-Sport Live Betting System"""
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Odds API
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# BallDontLie API (NBA stats)
BALLDONTLIE_API_KEY = os.getenv("BALLDONTLIE_API_KEY", "")
BALLDONTLIE_API_BASE = "https://api.balldontlie.io/v1"

# Active Sports (Nov 2024 - Apr 2025: NBA, NCAAB, NHL, NFL in season)
SPORTS = [
    "basketball_nba",             # NBA (Oct-Apr)
    "americanfootball_nfl",       # NFL (Sep-Feb)
    "icehockey_nhl",              # NHL (Oct-Apr)
    "basketball_ncaab",           # NCAA Basketball (Nov-Apr)
    # OUT OF SEASON (Disabled to save API credits):
    # "americanfootball_ncaaf",   # NCAA Football (season ends Dec)
    # "baseball_mlb",             # MLB (Apr-Oct)
    # PERMANENTLY DISABLED TO SAVE API CREDITS:
    # "golf_pga_championship",    # PGA Golf
    # "tennis_atp",               # Tennis (ATP - Men's)
    # "tennis_wta",               # Tennis (WTA - Women's)
    # "mma_mixed_martial_arts",   # MMA/UFC
]
REGION = "us,us2,uk,au,eu"  # Fetch from all regions for maximum bookmaker coverage
MARKETS = "h2h,spreads,totals"  # Fetch money lines, spreads, and totals

# Adaptive Polling Configuration (CST timezone)
# Active Polling: 12pm-12am CST (5 second interval)
# Cache-Only Mode: 12am-12pm CST (no API calls, use cached data)
CACHE_ONLY_MODE_ENABLED = True
CACHE_ONLY_START_HOUR = 0   # 12am CST
CACHE_ONLY_END_HOUR = 12     # 12pm CST
ACTIVE_POLL_INTERVAL = 5     # seconds (when polling is active)
CACHE_CHECK_INTERVAL = 300   # seconds (5 min - how often to check time during cache mode)

def is_cache_only_time():
    """Check if current time is in cache-only window (12am-12pm CST)"""
    if not CACHE_ONLY_MODE_ENABLED:
        return False

    # Get current time in CST (UTC-6)
    cst = timezone(timedelta(hours=-6))
    now = datetime.now(cst)
    hour = now.hour

    # Cache-only between 12am and 12pm
    return CACHE_ONLY_START_HOUR <= hour < CACHE_ONLY_END_HOUR

def get_poll_interval():
    """Get current poll interval based on cache-only mode"""
    if is_cache_only_time():
        return CACHE_CHECK_INTERVAL  # Just check time, don't poll APIs
    return ACTIVE_POLL_INTERVAL  # Active polling (5 seconds)

# Legacy config (kept for backwards compatibility)
POLL_INTERVAL = get_poll_interval()
ADAPTIVE_POLLING_ENABLED = False  # Deprecated - using CACHE_ONLY_MODE instead
PEAK_POLL_INTERVAL = 5
OFF_PEAK_POLL_INTERVAL = 60
# NOTE: Team season stats are cached and only scraped ONCE per day
# Only live game data (scores, odds, time) needs frequent polling

# Quiet Hours - DISABLED (replaced by adaptive polling)
QUIET_HOURS_ENABLED = False
QUIET_HOURS_START = 23  # 11 PM (24-hour format)
QUIET_HOURS_END = 9     # 9 AM (24-hour format)

# Edge detection
MIN_EDGE = 5.0  # points

# ESPN stats now enabled - NBA working, adding NFL/NHL back
ENABLE_ESPN_STATS = False  # DISABLED: ESPN API calls cause massive slowdown (hundreds of sync calls)
