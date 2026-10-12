/**
 * Static NFL team data — abbreviations and 2025 preseason power ratings.
 * Used so game cards can show ratings/ATS without waiting for the F5 matchup API.
 */

/** Maps full Odds API team name → NFL abbreviation (uppercase) */
export const NFL_TEAM_ABBR: Record<string, string> = {
  'Arizona Cardinals':     'ARI',
  'Atlanta Falcons':       'ATL',
  'Baltimore Ravens':      'BAL',
  'Buffalo Bills':         'BUF',
  'Carolina Panthers':     'CAR',
  'Chicago Bears':         'CHI',
  'Cincinnati Bengals':    'CIN',
  'Cleveland Browns':      'CLE',
  'Dallas Cowboys':        'DAL',
  'Denver Broncos':        'DEN',
  'Detroit Lions':         'DET',
  'Green Bay Packers':     'GB',
  'Houston Texans':        'HOU',
  'Indianapolis Colts':    'IND',
  'Jacksonville Jaguars':  'JAX',
  'Kansas City Chiefs':    'KC',
  'Las Vegas Raiders':     'LV',
  'Los Angeles Chargers':  'LAC',
  'Los Angeles Rams':      'LAR',
  'Miami Dolphins':        'MIA',
  'Minnesota Vikings':     'MIN',
  'New England Patriots':  'NE',
  'New Orleans Saints':    'NO',
  'New York Giants':       'NYG',
  'New York Jets':         'NYJ',
  'Philadelphia Eagles':   'PHI',
  'Pittsburgh Steelers':   'PIT',
  'San Francisco 49ers':   'SF',
  'Seattle Seahawks':      'SEA',
  'Tampa Bay Buccaneers':  'TB',
  'Tennessee Titans':      'TEN',
  'Washington Commanders': 'WSH',
};

export interface NflRating {
  rating: number;
  tier: string;
  rank: number;
}

/** 2026 ESPN FPI power ratings — projected point differential per game vs avg opponent */
export const NFL_POWER_RATINGS: Record<string, NflRating> = {
  LAR: { rating: 5.6,  tier: 'ELITE',     rank: 1  },
  BUF: { rating: 4.0,  tier: 'ELITE',     rank: 2  },
  BAL: { rating: 3.8,  tier: 'ELITE',     rank: 3  },
  SEA: { rating: 3.5,  tier: 'ELITE',     rank: 4  },
  SF:  { rating: 3.2,  tier: 'ELITE',     rank: 5  },
  GB:  { rating: 3.0,  tier: 'ELITE',     rank: 6  },
  LAC: { rating: 2.8,  tier: 'CONTENDER', rank: 7  },
  DET: { rating: 2.6,  tier: 'CONTENDER', rank: 8  },
  KC:  { rating: 2.4,  tier: 'CONTENDER', rank: 9  },
  PHI: { rating: 2.2,  tier: 'CONTENDER', rank: 10 },
  DAL: { rating: 2.0,  tier: 'CONTENDER', rank: 11 },
  CIN: { rating: 1.8,  tier: 'CONTENDER', rank: 12 },
  HOU: { rating: 1.5,  tier: 'CONTENDER', rank: 13 },
  DEN: { rating: 1.3,  tier: 'CONTENDER', rank: 14 },
  NE:  { rating: 1.0,  tier: 'AVERAGE',   rank: 15 },
  CHI: { rating: 0.8,  tier: 'AVERAGE',   rank: 16 },
  MIN: { rating: 0.5,  tier: 'AVERAGE',   rank: 17 },
  PIT: { rating: 0.2,  tier: 'AVERAGE',   rank: 18 },
  TB:  { rating: 0.0,  tier: 'AVERAGE',   rank: 19 },
  IND: { rating: -0.3, tier: 'AVERAGE',   rank: 20 },
  JAX: { rating: -0.5, tier: 'AVERAGE',   rank: 21 },
  ATL: { rating: -1.0, tier: 'BELOW',     rank: 22 },
  NO:  { rating: -1.3, tier: 'BELOW',     rank: 23 },
  WSH: { rating: -1.5, tier: 'BELOW',     rank: 24 },
  CAR: { rating: -2.0, tier: 'BELOW',     rank: 25 },
  NYG: { rating: -2.5, tier: 'BELOW',     rank: 26 },
  TEN: { rating: -3.0, tier: 'BELOW',     rank: 27 },
  CLE: { rating: -3.5, tier: 'WEAK',      rank: 28 },
  NYJ: { rating: -4.0, tier: 'WEAK',      rank: 29 },
  LV:  { rating: -4.5, tier: 'WEAK',      rank: 30 },
  MIA: { rating: -5.0, tier: 'WEAK',      rank: 31 },
  ARI: { rating: -5.5, tier: 'WEAK',      rank: 32 },
};

export function getNflAbbr(teamName: string): string | null {
  return NFL_TEAM_ABBR[teamName] ?? null;
}

export function getNflRating(teamName: string): NflRating | null {
  const abbr = getNflAbbr(teamName);
  return abbr ? (NFL_POWER_RATINGS[abbr] ?? null) : null;
}
