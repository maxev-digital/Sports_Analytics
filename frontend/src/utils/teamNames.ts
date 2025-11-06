/**
 * Team Name Formatting Utility
 *
 * Converts abbreviated team names to full "City Team" format
 * Supports NBA, NHL, NFL, NCAAF, NCAAB
 */

// NBA Team Name Mappings
const NBA_TEAMS: Record<string, string> = {
  // Common variations to handle
  'Atlanta Hawks': 'Atlanta Hawks',
  'Hawks': 'Atlanta Hawks',
  'ATL': 'Atlanta Hawks',

  'Boston Celtics': 'Boston Celtics',
  'Celtics': 'Boston Celtics',
  'BOS': 'Boston Celtics',

  'Brooklyn Nets': 'Brooklyn Nets',
  'Nets': 'Brooklyn Nets',
  'BKN': 'Brooklyn Nets',

  'Charlotte Hornets': 'Charlotte Hornets',
  'Hornets': 'Charlotte Hornets',
  'CHA': 'Charlotte Hornets',

  'Chicago Bulls': 'Chicago Bulls',
  'Bulls': 'Chicago Bulls',
  'CHI': 'Chicago Bulls',

  'Cleveland Cavaliers': 'Cleveland Cavaliers',
  'Cavaliers': 'Cleveland Cavaliers',
  'CLE': 'Cleveland Cavaliers',

  'Dallas Mavericks': 'Dallas Mavericks',
  'Mavericks': 'Dallas Mavericks',
  'DAL': 'Dallas Mavericks',

  'Denver Nuggets': 'Denver Nuggets',
  'Nuggets': 'Denver Nuggets',
  'DEN': 'Denver Nuggets',

  'Detroit Pistons': 'Detroit Pistons',
  'Pistons': 'Detroit Pistons',
  'DET': 'Detroit Pistons',

  'Golden State Warriors': 'Golden State Warriors',
  'Warriors': 'Golden State Warriors',
  'GSW': 'Golden State Warriors',

  'Houston Rockets': 'Houston Rockets',
  'Rockets': 'Houston Rockets',
  'HOU': 'Houston Rockets',

  'Indiana Pacers': 'Indiana Pacers',
  'Pacers': 'Indiana Pacers',
  'IND': 'Indiana Pacers',

  'LA Clippers': 'Los Angeles Clippers',
  'Los Angeles Clippers': 'Los Angeles Clippers',
  'Clippers': 'Los Angeles Clippers',
  'LAC': 'Los Angeles Clippers',

  'Los Angeles Lakers': 'Los Angeles Lakers',
  'Lakers': 'Los Angeles Lakers',
  'LAL': 'Los Angeles Lakers',

  'Memphis Grizzlies': 'Memphis Grizzlies',
  'Grizzlies': 'Memphis Grizzlies',
  'MEM': 'Memphis Grizzlies',

  'Miami Heat': 'Miami Heat',
  'Heat': 'Miami Heat',
  'MIA': 'Miami Heat',

  'Milwaukee Bucks': 'Milwaukee Bucks',
  'Bucks': 'Milwaukee Bucks',
  'MIL': 'Milwaukee Bucks',

  'Minnesota Timberwolves': 'Minnesota Timberwolves',
  'Timberwolves': 'Minnesota Timberwolves',
  'MIN': 'Minnesota Timberwolves',

  'New Orleans Pelicans': 'New Orleans Pelicans',
  'Pelicans': 'New Orleans Pelicans',
  'NOP': 'New Orleans Pelicans',

  'New York Knicks': 'New York Knicks',
  'Knicks': 'New York Knicks',
  'NYK': 'New York Knicks',

  'Oklahoma City Thunder': 'Oklahoma City Thunder',
  'Thunder': 'Oklahoma City Thunder',
  'OKC': 'Oklahoma City Thunder',

  'Orlando Magic': 'Orlando Magic',
  'Magic': 'Orlando Magic',
  'ORL': 'Orlando Magic',

  'Philadelphia 76ers': 'Philadelphia 76ers',
  '76ers': 'Philadelphia 76ers',
  'PHI': 'Philadelphia 76ers',

  'Phoenix Suns': 'Phoenix Suns',
  'Suns': 'Phoenix Suns',
  'PHX': 'Phoenix Suns',
  'PHO': 'Phoenix Suns', // Sports Data IO abbreviation

  'Portland Trail Blazers': 'Portland Trail Blazers',
  'Trail Blazers': 'Portland Trail Blazers',
  'POR': 'Portland Trail Blazers',

  'Sacramento Kings': 'Sacramento Kings',
  'Kings': 'Sacramento Kings',
  'SAC': 'Sacramento Kings',

  'San Antonio Spurs': 'San Antonio Spurs',
  'Spurs': 'San Antonio Spurs',
  'SAS': 'San Antonio Spurs',

  'Toronto Raptors': 'Toronto Raptors',
  'Raptors': 'Toronto Raptors',
  'TOR': 'Toronto Raptors',

  'Utah Jazz': 'Utah Jazz',
  'Jazz': 'Utah Jazz',
  'UTA': 'Utah Jazz',

  'Washington Wizards': 'Washington Wizards',
  'Wizards': 'Washington Wizards',
  'WAS': 'Washington Wizards',
};

// NHL Team Name Mappings
const NHL_TEAMS: Record<string, string> = {
  'Anaheim Ducks': 'Anaheim Ducks',
  'Ducks': 'Anaheim Ducks',
  'ANA': 'Anaheim Ducks',

  'Boston Bruins': 'Boston Bruins',
  'Bruins': 'Boston Bruins',
  'BOS': 'Boston Bruins',

  'Buffalo Sabres': 'Buffalo Sabres',
  'Sabres': 'Buffalo Sabres',
  'BUF': 'Buffalo Sabres',

  'Calgary Flames': 'Calgary Flames',
  'Flames': 'Calgary Flames',
  'CGY': 'Calgary Flames',

  'Carolina Hurricanes': 'Carolina Hurricanes',
  'Hurricanes': 'Carolina Hurricanes',
  'CAR': 'Carolina Hurricanes',

  'Chicago Blackhawks': 'Chicago Blackhawks',
  'Blackhawks': 'Chicago Blackhawks',
  'CHI': 'Chicago Blackhawks',

  'Colorado Avalanche': 'Colorado Avalanche',
  'Avalanche': 'Colorado Avalanche',
  'COL': 'Colorado Avalanche',

  'Columbus Blue Jackets': 'Columbus Blue Jackets',
  'Blue Jackets': 'Columbus Blue Jackets',
  'CBJ': 'Columbus Blue Jackets',

  'Dallas Stars': 'Dallas Stars',
  'Stars': 'Dallas Stars',
  'DAL': 'Dallas Stars',

  'Detroit Red Wings': 'Detroit Red Wings',
  'Red Wings': 'Detroit Red Wings',
  'DET': 'Detroit Red Wings',

  'Edmonton Oilers': 'Edmonton Oilers',
  'Oilers': 'Edmonton Oilers',
  'EDM': 'Edmonton Oilers',

  'Florida Panthers': 'Florida Panthers',
  'Panthers': 'Florida Panthers',
  'FLA': 'Florida Panthers',

  'Los Angeles Kings': 'Los Angeles Kings',
  'Kings': 'Los Angeles Kings',
  'LAK': 'Los Angeles Kings',

  'Minnesota Wild': 'Minnesota Wild',
  'Wild': 'Minnesota Wild',
  'MIN': 'Minnesota Wild',

  'Montreal Canadiens': 'Montreal Canadiens',
  'Canadiens': 'Montreal Canadiens',
  'MTL': 'Montreal Canadiens',
  'MON': 'Montreal Canadiens', // Sports Data IO abbreviation

  'Nashville Predators': 'Nashville Predators',
  'Predators': 'Nashville Predators',
  'NSH': 'Nashville Predators',
  'NAS': 'Nashville Predators', // Sports Data IO abbreviation

  'New Jersey Devils': 'New Jersey Devils',
  'Devils': 'New Jersey Devils',
  'NJD': 'New Jersey Devils',
  'NJ': 'New Jersey Devils', // Sports Data IO abbreviation

  'New York Islanders': 'New York Islanders',
  'Islanders': 'New York Islanders',
  'NYI': 'New York Islanders',

  'New York Rangers': 'New York Rangers',
  'Rangers': 'New York Rangers',
  'NYR': 'New York Rangers',

  'Ottawa Senators': 'Ottawa Senators',
  'Senators': 'Ottawa Senators',
  'OTT': 'Ottawa Senators',

  'Philadelphia Flyers': 'Philadelphia Flyers',
  'Flyers': 'Philadelphia Flyers',
  'PHI': 'Philadelphia Flyers',

  'Pittsburgh Penguins': 'Pittsburgh Penguins',
  'Penguins': 'Pittsburgh Penguins',
  'PIT': 'Pittsburgh Penguins',

  'San Jose Sharks': 'San Jose Sharks',
  'Sharks': 'San Jose Sharks',
  'SJS': 'San Jose Sharks',

  'Seattle Kraken': 'Seattle Kraken',
  'Kraken': 'Seattle Kraken',
  'SEA': 'Seattle Kraken',

  'St Louis Blues': 'St. Louis Blues',
  'St. Louis Blues': 'St. Louis Blues',
  'Blues': 'St. Louis Blues',
  'STL': 'St. Louis Blues',

  'Tampa Bay Lightning': 'Tampa Bay Lightning',
  'Lightning': 'Tampa Bay Lightning',
  'TBL': 'Tampa Bay Lightning',

  'Toronto Maple Leafs': 'Toronto Maple Leafs',
  'Maple Leafs': 'Toronto Maple Leafs',
  'TOR': 'Toronto Maple Leafs',

  'Vancouver Canucks': 'Vancouver Canucks',
  'Canucks': 'Vancouver Canucks',
  'VAN': 'Vancouver Canucks',

  'Vegas Golden Knights': 'Vegas Golden Knights',
  'Golden Knights': 'Vegas Golden Knights',
  'VGK': 'Vegas Golden Knights',

  'Washington Capitals': 'Washington Capitals',
  'Capitals': 'Washington Capitals',
  'WSH': 'Washington Capitals',
  'WAS': 'Washington Capitals', // Sports Data IO abbreviation

  'Winnipeg Jets': 'Winnipeg Jets',
  'Jets': 'Winnipeg Jets',
  'WPG': 'Winnipeg Jets',
};

// NFL Team Name Mappings
const NFL_TEAMS: Record<string, string> = {
  'Arizona Cardinals': 'Arizona Cardinals',
  'Cardinals': 'Arizona Cardinals',
  'ARI': 'Arizona Cardinals',

  'Atlanta Falcons': 'Atlanta Falcons',
  'Falcons': 'Atlanta Falcons',
  'ATL': 'Atlanta Falcons',

  'Baltimore Ravens': 'Baltimore Ravens',
  'Ravens': 'Baltimore Ravens',
  'BAL': 'Baltimore Ravens',

  'Buffalo Bills': 'Buffalo Bills',
  'Bills': 'Buffalo Bills',
  'BUF': 'Buffalo Bills',

  'Carolina Panthers': 'Carolina Panthers',
  'Panthers': 'Carolina Panthers',
  'CAR': 'Carolina Panthers',

  'Chicago Bears': 'Chicago Bears',
  'Bears': 'Chicago Bears',
  'CHI': 'Chicago Bears',

  'Cincinnati Bengals': 'Cincinnati Bengals',
  'Bengals': 'Cincinnati Bengals',
  'CIN': 'Cincinnati Bengals',

  'Cleveland Browns': 'Cleveland Browns',
  'Browns': 'Cleveland Browns',
  'CLE': 'Cleveland Browns',

  'Dallas Cowboys': 'Dallas Cowboys',
  'Cowboys': 'Dallas Cowboys',
  'DAL': 'Dallas Cowboys',

  'Denver Broncos': 'Denver Broncos',
  'Broncos': 'Denver Broncos',
  'DEN': 'Denver Broncos',

  'Detroit Lions': 'Detroit Lions',
  'Lions': 'Detroit Lions',
  'DET': 'Detroit Lions',

  'Green Bay Packers': 'Green Bay Packers',
  'Packers': 'Green Bay Packers',
  'GB': 'Green Bay Packers',

  'Houston Texans': 'Houston Texans',
  'Texans': 'Houston Texans',
  'HOU': 'Houston Texans',

  'Indianapolis Colts': 'Indianapolis Colts',
  'Colts': 'Indianapolis Colts',
  'IND': 'Indianapolis Colts',

  'Jacksonville Jaguars': 'Jacksonville Jaguars',
  'Jaguars': 'Jacksonville Jaguars',
  'JAX': 'Jacksonville Jaguars',

  'Kansas City Chiefs': 'Kansas City Chiefs',
  'Chiefs': 'Kansas City Chiefs',
  'KC': 'Kansas City Chiefs',

  'Las Vegas Raiders': 'Las Vegas Raiders',
  'Raiders': 'Las Vegas Raiders',
  'LV': 'Las Vegas Raiders',

  'Los Angeles Chargers': 'Los Angeles Chargers',
  'Chargers': 'Los Angeles Chargers',
  'LAC': 'Los Angeles Chargers',

  'Los Angeles Rams': 'Los Angeles Rams',
  'Rams': 'Los Angeles Rams',
  'LAR': 'Los Angeles Rams',

  'Miami Dolphins': 'Miami Dolphins',
  'Dolphins': 'Miami Dolphins',
  'MIA': 'Miami Dolphins',

  'Minnesota Vikings': 'Minnesota Vikings',
  'Vikings': 'Minnesota Vikings',
  'MIN': 'Minnesota Vikings',

  'New England Patriots': 'New England Patriots',
  'Patriots': 'New England Patriots',
  'NE': 'New England Patriots',

  'New Orleans Saints': 'New Orleans Saints',
  'Saints': 'New Orleans Saints',
  'NO': 'New Orleans Saints',

  'New York Giants': 'New York Giants',
  'Giants': 'New York Giants',
  'NYG': 'New York Giants',

  'New York Jets': 'New York Jets',
  'NY Jets': 'New York Jets',
  'NYJ': 'New York Jets',

  'Philadelphia Eagles': 'Philadelphia Eagles',
  'Eagles': 'Philadelphia Eagles',
  'PHI': 'Philadelphia Eagles',

  'Pittsburgh Steelers': 'Pittsburgh Steelers',
  'Steelers': 'Pittsburgh Steelers',
  'PIT': 'Pittsburgh Steelers',

  'San Francisco 49ers': 'San Francisco 49ers',
  '49ers': 'San Francisco 49ers',
  'SF': 'San Francisco 49ers',

  'Seattle Seahawks': 'Seattle Seahawks',
  'Seahawks': 'Seattle Seahawks',
  'SEA': 'Seattle Seahawks',

  'Tampa Bay Buccaneers': 'Tampa Bay Buccaneers',
  'Buccaneers': 'Tampa Bay Buccaneers',
  'TB': 'Tampa Bay Buccaneers',

  'Tennessee Titans': 'Tennessee Titans',
  'Titans': 'Tennessee Titans',
  'TEN': 'Tennessee Titans',

  'Washington Commanders': 'Washington Commanders',
  'Commanders': 'Washington Commanders',
  'WAS': 'Washington Commanders',
};

/**
 * Format team name to full "City Team" format
 *
 * @param teamName - Raw team name from API (could be abbreviation, partial name, or full name)
 * @param sportKey - Sport identifier (basketball_nba, icehockey_nhl, americanfootball_nfl, etc.)
 * @returns Formatted full team name
 */
export function formatTeamName(teamName: string, sportKey: string): string {
  if (!teamName) return teamName;

  // Determine which mapping to use based on sport
  let teamMap: Record<string, string> = {};

  if (sportKey.includes('basketball_nba')) {
    teamMap = NBA_TEAMS;
  } else if (sportKey.includes('icehockey_nhl')) {
    teamMap = NHL_TEAMS;
  } else if (sportKey.includes('americanfootball_nfl')) {
    teamMap = NFL_TEAMS;
  } else if (sportKey.includes('americanfootball_ncaaf')) {
    // NCAAF - return as is (college names are usually full already)
    return teamName;
  } else if (sportKey.includes('basketball_ncaab')) {
    // NCAAB - return as is (college names are usually full already)
    return teamName;
  }

  // Try exact match first
  if (teamMap[teamName]) {
    return teamMap[teamName];
  }

  // Try case-insensitive match
  const lowerTeamName = teamName.toLowerCase();
  for (const [key, value] of Object.entries(teamMap)) {
    if (key.toLowerCase() === lowerTeamName) {
      return value;
    }
  }

  // If no match found, return original
  return teamName;
}

/**
 * Format team name for compact display (for mobile/small screens)
 * Returns abbreviated form if needed
 */
export function formatTeamNameCompact(teamName: string, sportKey: string): string {
  const fullName = formatTeamName(teamName, sportKey);

  // For mobile, you might want to show just the team name without city
  // This is optional - remove if you always want full names
  const parts = fullName.split(' ');
  if (parts.length > 2) {
    // Return last word (team name) for very long names
    return parts[parts.length - 1];
  }

  return fullName;
}
