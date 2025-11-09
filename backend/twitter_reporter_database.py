"""
Twitter Reporter Database
Complete list of top sports reporters by sport and team
"""

from typing import Dict, List

# NBA Reporters - Tier 1 (National/Breaking News)
NBA_TIER1_REPORTERS = [
    {"username": "ShamsCharania", "name": "Shams Charania", "outlet": "The Athletic", "reliability": 1.0},
    {"username": "wojespn", "name": "Adrian Wojnarowski", "outlet": "ESPN", "reliability": 1.0},
    {"username": "ChrisBHaynes", "name": "Chris Haynes", "outlet": "TNT/Bleacher Report", "reliability": 0.95},
    {"username": "BA_Turner", "name": "Brad Turner", "outlet": "LA Times", "reliability": 0.95},
    {"username": "JonKrawczynski", "name": "Jon Krawczynski", "outlet": "The Athletic", "reliability": 0.9},
    {"username": "TheSteinLine", "name": "Marc Stein", "outlet": "Substack", "reliability": 0.95},
]

# NBA Reporters - Tier 2 (Beat Writers)
NBA_TIER2_REPORTERS = [
    {"username": "ramonashelburne", "name": "Ramona Shelburne", "outlet": "ESPN", "team": "Lakers", "reliability": 0.9},
    {"username": "WindhorstESPN", "name": "Brian Windhorst", "outlet": "ESPN", "team": "Cavaliers", "reliability": 0.9},
    {"username": "BobbyMarks42", "name": "Bobby Marks", "outlet": "ESPN", "reliability": 0.85},
    {"username": "KeithSmithNBA", "name": "Keith Smith", "outlet": "Spotrac", "reliability": 0.85},
]

# NFL Reporters - Tier 1 (National/Breaking News)
NFL_TIER1_REPORTERS = [
    {"username": "AdamSchefter", "name": "Adam Schefter", "outlet": "ESPN", "reliability": 1.0},
    {"username": "RapSheet", "name": "Ian Rapoport", "outlet": "NFL Network", "reliability": 1.0},
    {"username": "JayGlazer", "name": "Jay Glazer", "outlet": "Fox Sports", "reliability": 0.95},
    {"username": "TomPelissero", "name": "Tom Pelissero", "outlet": "NFL Network", "reliability": 0.9},
    {"username": "JFowlerESPN", "name": "Jeremy Fowler", "outlet": "ESPN", "reliability": 0.9},
    {"username": "diannaESPN", "name": "Dianna Russini", "outlet": "ESPN", "reliability": 0.9},
]

# MLB Reporters - Tier 1
MLB_TIER1_REPORTERS = [
    {"username": "JeffPassan", "name": "Jeff Passan", "outlet": "ESPN", "reliability": 1.0},
    {"username": "Ken_Rosenthal", "name": "Ken Rosenthal", "outlet": "The Athletic", "reliability": 1.0},
    {"username": "MarkBowman", "name": "Mark Bowman", "outlet": "MLB.com", "reliability": 0.9},
    {"username": "Feinsand", "name": "Mark Feinsand", "outlet": "MLB.com", "reliability": 0.9},
]

# NHL Reporters - Tier 1
NHL_TIER1_REPORTERS = [
    {"username": "FriedgeHNIC", "name": "Elliotte Friedman", "outlet": "Sportsnet", "reliability": 1.0},
    {"username": "PierreVLeBrun", "name": "Pierre LeBrun", "outlet": "The Athletic", "reliability": 1.0},
    {"username": "reporterchris", "name": "Chris Johnston", "outlet": "TSN", "reliability": 0.95},
    {"username": "frank_seravalli", "name": "Frank Seravalli", "outlet": "Daily Faceoff", "reliability": 0.9},
]

# Complete NBA Team Name Mappings
NBA_TEAM_MAPPINGS = {
    'Atlanta Hawks': ['Hawks', 'ATL', 'Atlanta'],
    'Boston Celtics': ['Celtics', 'BOS', 'Boston'],
    'Brooklyn Nets': ['Nets', 'BKN', 'Brooklyn'],
    'Charlotte Hornets': ['Hornets', 'CHA', 'Charlotte'],
    'Chicago Bulls': ['Bulls', 'CHI', 'Chicago'],
    'Cleveland Cavaliers': ['Cavaliers', 'Cavs', 'CLE', 'Cleveland'],
    'Dallas Mavericks': ['Mavericks', 'Mavs', 'DAL', 'Dallas'],
    'Denver Nuggets': ['Nuggets', 'DEN', 'Denver'],
    'Detroit Pistons': ['Pistons', 'DET', 'Detroit'],
    'Golden State Warriors': ['Warriors', 'GSW', 'Golden State'],
    'Houston Rockets': ['Rockets', 'HOU', 'Houston'],
    'Indiana Pacers': ['Pacers', 'IND', 'Indiana'],
    'Los Angeles Clippers': ['Clippers', 'LAC', 'LA Clippers'],
    'Los Angeles Lakers': ['Lakers', 'LAL', 'LA Lakers'],
    'Memphis Grizzlies': ['Grizzlies', 'MEM', 'Memphis'],
    'Miami Heat': ['Heat', 'MIA', 'Miami'],
    'Milwaukee Bucks': ['Bucks', 'MIL', 'Milwaukee'],
    'Minnesota Timberwolves': ['Timberwolves', 'Wolves', 'MIN', 'Minnesota'],
    'New Orleans Pelicans': ['Pelicans', 'NOP', 'New Orleans'],
    'New York Knicks': ['Knicks', 'NYK', 'New York'],
    'Oklahoma City Thunder': ['Thunder', 'OKC', 'Oklahoma City'],
    'Orlando Magic': ['Magic', 'ORL', 'Orlando'],
    'Philadelphia 76ers': ['76ers', 'Sixers', 'PHI', 'Philadelphia'],
    'Phoenix Suns': ['Suns', 'PHX', 'Phoenix'],
    'Portland Trail Blazers': ['Trail Blazers', 'Blazers', 'POR', 'Portland'],
    'Sacramento Kings': ['Kings', 'SAC', 'Sacramento'],
    'San Antonio Spurs': ['Spurs', 'SAS', 'San Antonio'],
    'Toronto Raptors': ['Raptors', 'TOR', 'Toronto'],
    'Utah Jazz': ['Jazz', 'UTA', 'Utah'],
    'Washington Wizards': ['Wizards', 'WAS', 'Washington'],
}

# Complete NFL Team Name Mappings
NFL_TEAM_MAPPINGS = {
    'Arizona Cardinals': ['Cardinals', 'ARI', 'Arizona'],
    'Atlanta Falcons': ['Falcons', 'ATL', 'Atlanta'],
    'Baltimore Ravens': ['Ravens', 'BAL', 'Baltimore'],
    'Buffalo Bills': ['Bills', 'BUF', 'Buffalo'],
    'Carolina Panthers': ['Panthers', 'CAR', 'Carolina'],
    'Chicago Bears': ['Bears', 'CHI', 'Chicago'],
    'Cincinnati Bengals': ['Bengals', 'CIN', 'Cincinnati'],
    'Cleveland Browns': ['Browns', 'CLE', 'Cleveland'],
    'Dallas Cowboys': ['Cowboys', 'DAL', 'Dallas'],
    'Denver Broncos': ['Broncos', 'DEN', 'Denver'],
    'Detroit Lions': ['Lions', 'DET', 'Detroit'],
    'Green Bay Packers': ['Packers', 'GB', 'Green Bay'],
    'Houston Texans': ['Texans', 'HOU', 'Houston'],
    'Indianapolis Colts': ['Colts', 'IND', 'Indianapolis'],
    'Jacksonville Jaguars': ['Jaguars', 'Jags', 'JAX', 'Jacksonville'],
    'Kansas City Chiefs': ['Chiefs', 'KC', 'Kansas City'],
    'Las Vegas Raiders': ['Raiders', 'LV', 'Las Vegas'],
    'Los Angeles Chargers': ['Chargers', 'LAC', 'LA Chargers'],
    'Los Angeles Rams': ['Rams', 'LAR', 'LA Rams'],
    'Miami Dolphins': ['Dolphins', 'MIA', 'Miami'],
    'Minnesota Vikings': ['Vikings', 'MIN', 'Minnesota'],
    'New England Patriots': ['Patriots', 'Pats', 'NE', 'New England'],
    'New Orleans Saints': ['Saints', 'NO', 'New Orleans'],
    'New York Giants': ['Giants', 'NYG', 'New York Giants'],
    'New York Jets': ['Jets', 'NYJ', 'New York Jets'],
    'Philadelphia Eagles': ['Eagles', 'PHI', 'Philadelphia'],
    'Pittsburgh Steelers': ['Steelers', 'PIT', 'Pittsburgh'],
    'San Francisco 49ers': ['49ers', 'SF', 'San Francisco'],
    'Seattle Seahawks': ['Seahawks', 'SEA', 'Seattle'],
    'Tampa Bay Buccaneers': ['Buccaneers', 'Bucs', 'TB', 'Tampa Bay'],
    'Tennessee Titans': ['Titans', 'TEN', 'Tennessee'],
    'Washington Commanders': ['Commanders', 'WAS', 'Washington'],
}

# Injury Keywords by Severity
INJURY_KEYWORDS = {
    'CRITICAL': [
        'ruled out',
        'placed on IR',
        'placed on IL',
        'season-ending',
        'torn ACL',
        'torn MCL',
        'surgery',
        'will not play',
    ],
    'HIGH': [
        'out',
        'sidelined',
        'will miss',
        'expected to miss',
        'unavailable',
        'week-to-week',
    ],
    'MEDIUM': [
        'doubtful',
        'unlikely',
        'game-time decision',
    ],
    'LOW': [
        'questionable',
        'day-to-day',
        'probable',
        'limited',
    ],
}

def get_all_reporters() -> Dict[str, List]:
    """Get all reporters grouped by sport"""
    return {
        'NBA': NBA_TIER1_REPORTERS + NBA_TIER2_REPORTERS,
        'NFL': NFL_TIER1_REPORTERS,
        'MLB': MLB_TIER1_REPORTERS,
        'NHL': NHL_TIER1_REPORTERS,
    }

def get_team_mappings() -> Dict[str, Dict]:
    """Get all team mappings by sport"""
    return {
        'NBA': NBA_TEAM_MAPPINGS,
        'NFL': NFL_TEAM_MAPPINGS,
    }
