"""
Sport Detection Module
Detects sport based on team names
"""

# NBA Teams
NBA_TEAMS = {
    'Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets', 'Chicago Bulls',
    'Cleveland Cavaliers', 'Dallas Mavericks', 'Denver Nuggets', 'Detroit Pistons', 'Golden State Warriors',
    'Houston Rockets', 'Indiana Pacers', 'LA Clippers', 'Los Angeles Clippers', 'Los Angeles Lakers',
    'Memphis Grizzlies', 'Miami Heat', 'Milwaukee Bucks', 'Minnesota Timberwolves', 'New Orleans Pelicans',
    'New York Knicks', 'Oklahoma City Thunder', 'Orlando Magic', 'Philadelphia 76ers', 'Phoenix Suns',
    'Portland Trail Blazers', 'Sacramento Kings', 'San Antonio Spurs', 'Toronto Raptors', 'Utah Jazz',
    'Washington Wizards'
}

# NFL Teams
NFL_TEAMS = {
    'Arizona Cardinals', 'Atlanta Falcons', 'Baltimore Ravens', 'Buffalo Bills', 'Carolina Panthers',
    'Chicago Bears', 'Cincinnati Bengals', 'Cleveland Browns', 'Dallas Cowboys', 'Denver Broncos',
    'Detroit Lions', 'Green Bay Packers', 'Houston Texans', 'Indianapolis Colts', 'Jacksonville Jaguars',
    'Kansas City Chiefs', 'Las Vegas Raiders', 'Los Angeles Chargers', 'Los Angeles Rams', 'Miami Dolphins',
    'Minnesota Vikings', 'New England Patriots', 'New Orleans Saints', 'New York Giants', 'New York Jets',
    'Philadelphia Eagles', 'Pittsburgh Steelers', 'San Francisco 49ers', 'Seattle Seahawks', 'Tampa Bay Buccaneers',
    'Tennessee Titans', 'Washington Commanders'
}

# NHL Teams
NHL_TEAMS = {
    'Anaheim Ducks', 'Arizona Coyotes', 'Boston Bruins', 'Buffalo Sabres', 'Calgary Flames',
    'Carolina Hurricanes', 'Chicago Blackhawks', 'Colorado Avalanche', 'Columbus Blue Jackets', 'Dallas Stars',
    'Detroit Red Wings', 'Edmonton Oilers', 'Florida Panthers', 'Los Angeles Kings', 'Minnesota Wild',
    'Montreal Canadiens', 'Nashville Predators', 'New Jersey Devils', 'New York Islanders', 'New York Rangers',
    'Ottawa Senators', 'Philadelphia Flyers', 'Pittsburgh Penguins', 'San Jose Sharks', 'Seattle Kraken',
    'St. Louis Blues', 'Tampa Bay Lightning', 'Toronto Maple Leafs', 'Vancouver Canucks', 'Vegas Golden Knights',
    'Washington Capitals', 'Winnipeg Jets'
}

# MLB Teams
MLB_TEAMS = {
    'Arizona Diamondbacks', 'Atlanta Braves', 'Baltimore Orioles', 'Boston Red Sox', 'Chicago Cubs',
    'Chicago White Sox', 'Cincinnati Reds', 'Cleveland Guardians', 'Colorado Rockies', 'Detroit Tigers',
    'Houston Astros', 'Kansas City Royals', 'Los Angeles Angels', 'Los Angeles Dodgers', 'Miami Marlins',
    'Milwaukee Brewers', 'Minnesota Twins', 'New York Mets', 'New York Yankees', 'Oakland Athletics',
    'Philadelphia Phillies', 'Pittsburgh Pirates', 'San Diego Padres', 'San Francisco Giants', 'Seattle Mariners',
    'St. Louis Cardinals', 'Tampa Bay Rays', 'Texas Rangers', 'Toronto Blue Jays', 'Washington Nationals'
}

# NCAAB - Common teams (partial list, will match based on keywords)
NCAAB_KEYWORDS = {
    'Wildcats', 'Tar Heels', 'Blue Devils', 'Spartans', 'Jayhawks', 'Hoosiers', 'Bruins', 'Longhorns',
    'Wolverines', 'Volunteers', 'Bulldogs', 'Tigers', 'Crimson Tide', 'Gators', 'Orangemen', 'Cardinal',
    'Seminoles', 'Aggies', 'Mountaineers', 'Hawkeyes', 'Badgers', 'Illini', 'Boilermakers', 'Buckeyes',
    'Huskies', 'Terrapins', 'Cavaliers', 'Hokies', 'Panthers', 'Orange', 'Commodores', 'Razorbacks'
}

# NCAAF - Same keywords as NCAAB since college teams play both sports
NCAAF_KEYWORDS = NCAAB_KEYWORDS


def detect_sport(home_team: str, away_team: str) -> str:
    """
    Detect sport based on team names
    Returns: 'NBA', 'NFL', 'NHL', 'MLB', 'NCAAB', 'NCAAF', or 'UNKNOWN'
    """

    # Check NBA
    if home_team in NBA_TEAMS or away_team in NBA_TEAMS:
        return 'NBA'

    # Check NFL
    if home_team in NFL_TEAMS or away_team in NFL_TEAMS:
        return 'NFL'

    # Check NHL
    if home_team in NHL_TEAMS or away_team in NHL_TEAMS:
        return 'NHL'

    # Check MLB
    if home_team in MLB_TEAMS or away_team in MLB_TEAMS:
        return 'MLB'

    # Check college sports (NCAAB/NCAAF) by keywords
    # If it has college keywords and we can't determine which, default to NCAAB for basketball context
    home_lower = home_team.lower()
    away_lower = away_team.lower()

    for keyword in NCAAB_KEYWORDS:
        if keyword.lower() in home_lower or keyword.lower() in away_lower:
            # Check for football indicators
            if any(word in home_lower or word in away_lower for word in ['football', 'bowl']):
                return 'NCAAF'
            # Default to basketball for college
            return 'NCAAB'

    # Check for university/college in name
    if 'university' in home_lower or 'college' in home_lower or 'state' in home_lower:
        if 'football' in home_lower or 'football' in away_lower:
            return 'NCAAF'
        return 'NCAAB'

    return 'UNKNOWN'


def is_nba_team(team_name: str) -> bool:
    """Check if team is NBA"""
    return team_name in NBA_TEAMS


def is_nfl_team(team_name: str) -> bool:
    """Check if team is NFL"""
    return team_name in NFL_TEAMS


def is_nhl_team(team_name: str) -> bool:
    """Check if team is NHL"""
    return team_name in NHL_TEAMS


def is_mlb_team(team_name: str) -> bool:
    """Check if team is MLB"""
    return team_name in MLB_TEAMS
