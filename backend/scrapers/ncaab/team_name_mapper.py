#!/usr/bin/env python3
"""
NCAA Basketball Team Name Mapping
Maps common team name variations to KenPom standard names

This solves the issue where game result scrapers use different names than KenPom
(e.g., "UConn" in games vs "Connecticut" in KenPom)
"""

# Complete mapping dictionary: Game Result Name → KenPom Name
TEAM_NAME_MAP = {
    # Major variations
    'UConn': 'Connecticut',
    'Purdue': 'Purdue',  # Keep as-is, but map "Purdue" games to avoid matching "Purdue Fort Wayne"
    'Houston': 'Houston',  # Keep as-is
    'South Carolina': 'South Carolina',  # Keep as-is
    'Kansas State': 'Kansas St.',
    'Ohio State': 'Ohio St.',
    'Colorado': 'Colorado',  # Keep as-is
    'Arizona State': 'Arizona St.',
    'Illinois': 'Illinois',  # Keep as-is
    'Illinois State': 'Illinois St.',
    'Washington State': 'Washington St.',
    'Miami (OH)': 'Miami OH',
    'Miami (FL)': 'Miami FL',
    'Penn State': 'Penn St.',
    'Montana State': 'Montana St.',
    'Missouri State': 'Missouri St.',
    'Fresno State': 'Fresno St.',
    'Utah State': 'Utah St.',
    'Boise State': 'Boise St.',
    'Ball State': 'Ball St.',
    'Cleveland State': 'Cleveland St.',
    'New Mexico State': 'New Mexico St.',
    'San Diego State': 'San Diego St.',
    'South Dakota State': 'South Dakota St.',
    'Tarleton State': 'Tarleton St.',
    
    # Conference abbreviations
    'College of Charleston': 'Charleston',
    'Saint Mary\'s': 'Saint Mary\'s CA',
    'St. John\'s (NY)': 'St. John\'s',
    'San Diego State': 'San Diego St.',
    
    # Abbreviated names
    'FDU': 'Fairleigh Dickinson',
    'UAB': 'UAB',  # Already correct
    'UIC': 'Illinois Chicago',
    'IU Indianapolis': 'IUPUI',
    
    # City-based names
    'Albany (NY)': 'Albany NY',
    'Omaha': 'Nebraska Omaha',
    'Kansas City': 'UMKC',
    
    # State schools
    'Louisiana-Monroe': 'ULM',
    'Cal State Fullerton': 'CS Fullerton',
    'Texas State': 'Texas St.',
    
    # Samford/Sam Houston
    'Sam Houston': 'Sam Houston St.',
    'Samford': 'Samford',  # These are different schools!
    
    # Others
    'Gardner-Webb': 'Gardner Webb',
    'Youngstown State': 'Youngstown St.',
    'Appalachian State': 'Appalachian St.',
    'Norfolk State': 'Norfolk St.',
    'Grand Canyon': 'Grand Canyon',  # Already correct
    'Western Kentucky': 'Western Kentucky',  # Already correct
    'Oakland': 'Oakland',  # Already correct
    'Vermont': 'Vermont',  # Already correct
    'Colgate': 'Colgate',  # Already correct
    'Clemson': 'Clemson',  # Already correct
    'Stetson': 'Stetson',  # Already correct
}

# Common suffixes that should be stripped or standardized
SUFFIX_REPLACEMENTS = {
    ' State': ' St.',
    ' (OH)': ' OH',
    ' (FL)': ' FL',
    ' (NY)': ' NY',
}


def normalize_team_name(team_name):
    """
    Normalize a team name to match KenPom format
    
    Args:
        team_name: Raw team name from game results
    
    Returns:
        Normalized team name that should match KenPom
    """
    # First check direct mapping
    if team_name in TEAM_NAME_MAP:
        return TEAM_NAME_MAP[team_name]
    
    # Apply suffix replacements
    normalized = team_name
    for old_suffix, new_suffix in SUFFIX_REPLACEMENTS.items():
        if normalized.endswith(old_suffix):
            normalized = normalized[:-len(old_suffix)] + new_suffix
    
    return normalized


def fuzzy_match_team(team_name, kenpom_teams):
    """
    Attempt fuzzy matching if direct mapping fails
    
    Args:
        team_name: Team name to match
        kenpom_teams: List of valid KenPom team names
    
    Returns:
        Best matching KenPom team name or None
    """
    # Normalize first
    normalized = normalize_team_name(team_name)
    
    # Check if normalized version exists
    if normalized in kenpom_teams:
        return normalized
    
    # Try case-insensitive exact match
    normalized_lower = normalized.lower()
    for kp_team in kenpom_teams:
        if kp_team.lower() == normalized_lower:
            return kp_team
    
    # Try partial word matching (e.g., "Arizona" matches "Arizona St.")
    team_words = set(normalized.lower().split())
    
    for kp_team in kenpom_teams:
        kp_words = set(kp_team.lower().split())
        
        # If all words from game name appear in KenPom name, it's likely a match
        if team_words.issubset(kp_words):
            return kp_team
        
        # Or if KenPom has all words from game name
        if kp_words.issubset(team_words):
            return kp_team
    
    # No match found
    return None


# Test function
if __name__ == "__main__":
    print("="*70)
    print("TEAM NAME MAPPER - TEST")
    print("="*70)
    
    test_cases = [
        'UConn',
        'Purdue',
        'Houston',
        'Miami (OH)',
        'Saint Mary\'s',
        'FDU',
        'Kansas City',
        'Sam Houston',
    ]
    
    print("\nTesting direct mappings:")
    for test in test_cases:
        mapped = normalize_team_name(test)
        print(f"   {test:<30} → {mapped}")
    
    print("\n✅ Mapping system ready!")
    print("   Import this module in totals_predictor.py")
