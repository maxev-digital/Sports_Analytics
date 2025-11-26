"""
Volatility Arbitrage Strategy Configuration

Hybrid volatility arbitrage that enters +money positions during favorable
game states and optionally hedges when opposite side reaches target price.
"""

# Entry Criteria
MIN_ENTRY_ODDS = 180  # Minimum +180 to enter first position
MAX_ENTRY_ODDS = 350  # Maximum +350 (too risky beyond this)
MIN_EV_THRESHOLD = 0.05  # Minimum 5% edge required to enter

# Trigger Criteria (for second leg)
DEFAULT_TRIGGER_OFFSET = 80  # Default: if enter at +200, trigger at +280
MIN_TRIGGER_ODDS = 200  # Minimum +200 for second leg
MIN_LOCKED_PROFIT_PCT = 0.10  # Minimum 10% locked profit to justify hedge

# Position Management
MAX_OPEN_POSITIONS_PER_USER = 10  # Limit to prevent over-leverage
POSITION_EXPIRY_HOURS = 6  # Auto-close positions after 6 hours if game ends

# Sports Configuration
SUPPORTED_SPORTS = [
    'basketball_nba',
    'basketball_ncaab',
    'icehockey_nhl',
    'baseball_mlb',
    'americanfootball_nfl',
    'americanfootball_ncaaf'
]

# Volatility Factors by Sport (how volatile is the sport?)
SPORT_VOLATILITY = {
    'basketball_nba': 0.35,      # 35% of games trigger second leg
    'basketball_ncaab': 0.38,    # College more volatile
    'icehockey_nhl': 0.28,       # Goals = big swings
    'baseball_mlb': 0.25,        # Slower pace
    'americanfootball_nfl': 0.30,  # TD = huge swings
    'americanfootball_ncaaf': 0.33  # College more volatile
}

# Risk Management
BANKROLL_REQUIREMENTS = {
    # Stake: (Aggressive 50u, Standard 100u, Conservative 150u)
    100: (5000, 10000, 15000),
    200: (10000, 20000, 30000),
    300: (15000, 30000, 45000),
    400: (20000, 40000, 60000),
    500: (25000, 50000, 75000),
    600: (30000, 60000, 90000),
    700: (35000, 70000, 105000),
    800: (40000, 80000, 120000),
    900: (45000, 90000, 135000),
    1000: (50000, 100000, 150000)
}

# Expected Performance (from Monte Carlo)
EXPECTED_EV_PER_ATTEMPT = 0.157  # 15.7% of stake
HEDGE_TRIGGER_RATE = 0.35  # 35% of positions trigger hedge
SINGLE_LEG_EV = 0.08  # 8% EV when riding first bet alone

# Alert Configuration
TOAST_ALERT_ENABLED = True
TOAST_ALERT_PRIORITY = 'high'  # Show above other alerts
TOAST_ALERT_SOUND = True
TOAST_ALERT_PERSIST = True  # Don't auto-dismiss
