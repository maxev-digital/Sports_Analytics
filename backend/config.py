"""Configuration for Multi-Sport Live Betting System"""
import os

# Odds API
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "f573a2895848c38064be4af4ff5f728b")
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
SPORTS = [
    "americanfootball_nfl",      # NFL
    "basketball_nba",             # NBA
    "basketball_ncaab",           # NCAA Basketball
    "icehockey_nhl",              # NHL
    "americanfootball_ncaaf",     # NCAA Football
    "baseball_mlb",               # MLB
    "golf_pga_championship",      # PGA Golf
    "tennis_atp",                 # Tennis (ATP - Men's)
    "tennis_wta",                 # Tennis (WTA - Women's)
    "mma_mixed_martial_arts",     # MMA/UFC
]
REGION = "us,us2,uk,au,eu"  # Fetch from all regions for maximum bookmaker coverage
MARKETS = "h2h,spreads,totals"  # Fetch money lines, spreads, and totals

# Polling
POLL_INTERVAL = 5  # seconds (5 seconds - fastest recommended rate)

# Edge detection
MIN_EDGE = 5.0  # points
