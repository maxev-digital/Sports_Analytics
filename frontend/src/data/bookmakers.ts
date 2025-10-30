/**
 * Comprehensive Bookmaker Database
 * Contains all 62 bookmakers from The Odds API
 * Supports both local logo hosting (production) and favicon fallback (development)
 */

export interface Bookmaker {
  key: string;           // The Odds API key
  name: string;          // Display name
  url: string;           // Sportsbook URL
  region: string[];      // Regions where available
  logo: string;          // Logo URL (production: local, dev: favicon)
  logoFallback: string;  // Fallback to Google favicon
  popular?: boolean;     // Flag for major bookmakers
}

/**
 * Get logo URL based on environment
 * In production: Use local logos from /assets/bookmaker-logos/
 * In development: Use Google favicon service
 */
const getLogoUrl = (key: string, useLocal: boolean = false): string => {
  if (useLocal) {
    // Production: Use self-hosted logos
    return `/assets/bookmaker-logos/${key}.png`;
  }

  // Development: Use Google S2 Favicon API (proven reliable)
  // Handle special cases first
  let domain: string;

  if (key === 'betonlineag') {
    domain = 'betonline.ag';
  } else if (key === 'mybookieag') {
    domain = 'mybookie.ag';
  } else if (key === 'lowvig') {
    domain = 'lowvig.ag';
  } else if (key === 'betus') {
    domain = 'betus.com.pa';
  } else if (key === 'bovada') {
    domain = 'bovada.lv';
  } else {
    // Default: remove _us suffix and add .com
    domain = key.replace('_us', '') + '.com';
  }

  return `https://www.google.com/s2/favicons?domain=${domain}&sz=128`;
};

/**
 * Master bookmaker database
 * All 62 bookmakers from The Odds API
 */
export const BOOKMAKERS: Record<string, Bookmaker> = {
  // ========== UNITED STATES - MAJOR BOOKMAKERS ==========
  draftkings: {
    key: 'draftkings',
    name: 'DraftKings',
    url: 'https://sportsbook.draftkings.com/leagues/basketball/nba',
    region: ['US'],
    logo: getLogoUrl('draftkings', false),
    logoFallback: getLogoUrl('draftkings', false),
    popular: true,
  },
  fanduel: {
    key: 'fanduel',
    name: 'FanDuel',
    url: 'https://sportsbook.fanduel.com/navigation/nba',
    region: ['US'],
    logo: getLogoUrl('fanduel', false),
    logoFallback: getLogoUrl('fanduel', false),
    popular: true,
  },
  betmgm: {
    key: 'betmgm',
    name: 'BetMGM',
    url: 'https://sports.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004',
    region: ['US'],
    logo: getLogoUrl('betmgm', false),
    logoFallback: getLogoUrl('betmgm', false),
    popular: true,
  },
  caesars: {
    key: 'caesars',
    name: 'Caesars',
    url: 'https://www.caesars.com/sportsbook-and-casino/basketball/nba',
    region: ['US'],
    logo: getLogoUrl('caesars', false),
    logoFallback: getLogoUrl('caesars', false),
    popular: true,
  },
  betrivers: {
    key: 'betrivers',
    name: 'BetRivers',
    url: 'https://www.betrivers.com/?page=sportsbook#basketball',
    region: ['US'],
    logo: getLogoUrl('betrivers', false),
    logoFallback: getLogoUrl('betrivers', false),
    popular: true,
  },
  pointsbet: {
    key: 'pointsbet',
    name: 'PointsBet',
    url: 'https://pointsbet.com/sports/basketball/nba',
    region: ['US'],
    logo: getLogoUrl('pointsbet', false),
    logoFallback: getLogoUrl('pointsbet', false),
    popular: true,
  },
  williamhill_us: {
    key: 'williamhill_us',
    name: 'William Hill US',
    url: 'https://www.williamhill.com/us/nv/bet/en/betting/t/basketball/nba',
    region: ['US'],
    logo: getLogoUrl('williamhill_us', false),
    logoFallback: getLogoUrl('williamhill_us', false),
    popular: true,
  },
  fanatics: {
    key: 'fanatics',
    name: 'Fanatics',
    url: 'https://fanatics.com/sportsbook/basketball/nba',
    region: ['US'],
    logo: getLogoUrl('fanatics', false),
    logoFallback: getLogoUrl('fanatics', false),
    popular: true,
  },
  espnbet: {
    key: 'espnbet',
    name: 'ESPN BET',
    url: 'https://espnbet.com/sport/basketball/usa/nba',
    region: ['US'],
    logo: getLogoUrl('espnbet', false),
    logoFallback: getLogoUrl('espnbet', false),
    popular: true,
  },

  // ========== UNITED STATES - REGIONAL ==========
  ballybet: {
    key: 'ballybet',
    name: 'Bally Bet',
    url: 'https://ballybet.com/sports/basketball',
    region: ['US'],
    logo: getLogoUrl('ballybet', false),
    logoFallback: getLogoUrl('ballybet', false),
  },
  betway: {
    key: 'betway',
    name: 'Betway',
    url: 'https://sports.betway.com/en/sports/grp/basketball',
    region: ['US', 'UK', 'EU'],
    logo: getLogoUrl('betway', false),
    logoFallback: getLogoUrl('betway', false),
  },
  unibet: {
    key: 'unibet',
    name: 'Unibet',
    url: 'https://www.unibet.com/betting/sports/basketball',
    region: ['US', 'EU'],
    logo: getLogoUrl('unibet', false),
    logoFallback: getLogoUrl('unibet', false),
  },
  wynnbet: {
    key: 'wynnbet',
    name: 'WynnBET',
    url: 'https://www.wynnbet.com/sports/basketball',
    region: ['US'],
    logo: getLogoUrl('wynnbet', false),
    logoFallback: getLogoUrl('wynnbet', false),
  },
  superbook: {
    key: 'superbook',
    name: 'SuperBook',
    url: 'https://www.superbook.com/sports/basketball',
    region: ['US'],
    logo: getLogoUrl('superbook', false),
    logoFallback: getLogoUrl('superbook', false),
  },
  twinspires: {
    key: 'twinspires',
    name: 'TwinSpires',
    url: 'https://www.twinspires.com/sportsbook',
    region: ['US'],
    logo: getLogoUrl('twinspires', false),
    logoFallback: getLogoUrl('twinspires', false),
  },
  foxbet: {
    key: 'foxbet',
    name: 'FOX Bet',
    url: 'https://www.foxbet.com/sport/basketball',
    region: ['US'],
    logo: getLogoUrl('foxbet', false),
    logoFallback: getLogoUrl('foxbet', false),
  },

  // ========== OFFSHORE - US ACCESSIBLE ==========
  betonlineag: {
    key: 'betonlineag',
    name: 'BetOnline.ag',
    url: 'https://www.betonline.ag/sportsbook/basketball/nba',
    region: ['US', 'Global'],
    logo: getLogoUrl('betonlineag', false),
    logoFallback: getLogoUrl('betonlineag', false),
    popular: true,
  },
  bovada: {
    key: 'bovada',
    name: 'Bovada',
    url: 'https://www.bovada.lv/sports/basketball',
    region: ['US', 'Global'],
    logo: getLogoUrl('bovada', false),
    logoFallback: getLogoUrl('bovada', false),
    popular: true,
  },
  mybookieag: {
    key: 'mybookieag',
    name: 'MyBookie',
    url: 'https://www.mybookie.ag/sportsbook/nba/',
    region: ['US', 'Global'],
    logo: getLogoUrl('mybookieag', false),
    logoFallback: getLogoUrl('mybookieag', false),
  },
  lowvig: {
    key: 'lowvig',
    name: 'LowVig.ag',
    url: 'https://lowvig.ag/sports/basketball',
    region: ['US', 'Global'],
    logo: getLogoUrl('lowvig', false),
    logoFallback: getLogoUrl('lowvig', false),
  },
  betus: {
    key: 'betus',
    name: 'BetUS',
    url: 'https://www.betus.com.pa/sportsbook/basketball/',
    region: ['US', 'Global'],
    logo: getLogoUrl('betus', false),
    logoFallback: getLogoUrl('betus', false),
  },
  bookmaker: {
    key: 'bookmaker',
    name: 'Bookmaker',
    url: 'https://www.bookmaker.eu/sportsbook/basketball',
    region: ['Global'],
    logo: getLogoUrl('bookmaker', false),
    logoFallback: getLogoUrl('bookmaker', false),
  },
  gtbets: {
    key: 'gtbets',
    name: 'GTBets',
    url: 'https://www.gtbets.ag/sportsbook',
    region: ['Global'],
    logo: getLogoUrl('gtbets', false),
    logoFallback: getLogoUrl('gtbets', false),
  },
  intertops: {
    key: 'intertops',
    name: 'Intertops',
    url: 'https://www.intertops.eu/en/sportsbook',
    region: ['Global'],
    logo: getLogoUrl('intertops', false),
    logoFallback: getLogoUrl('intertops', false),
  },

  // ========== UNITED KINGDOM ==========
  bet365: {
    key: 'bet365',
    name: 'Bet365',
    url: 'https://www.bet365.com/sports/basketball',
    region: ['UK', 'EU', 'AU'],
    logo: getLogoUrl('bet365', false),
    logoFallback: getLogoUrl('bet365', false),
    popular: true,
  },
  williamhill: {
    key: 'williamhill',
    name: 'William Hill',
    url: 'https://sports.williamhill.com/betting/en-gb/basketball',
    region: ['UK', 'EU'],
    logo: getLogoUrl('williamhill', false),
    logoFallback: getLogoUrl('williamhill', false),
    popular: true,
  },
  ladbrokes: {
    key: 'ladbrokes',
    name: 'Ladbrokes',
    url: 'https://sports.ladbrokes.com/en-gb/basketball',
    region: ['UK', 'AU'],
    logo: getLogoUrl('ladbrokes', false),
    logoFallback: getLogoUrl('ladbrokes', false),
  },
  coral: {
    key: 'coral',
    name: 'Coral',
    url: 'https://sports.coral.co.uk/basketball',
    region: ['UK'],
    logo: getLogoUrl('coral', false),
    logoFallback: getLogoUrl('coral', false),
  },
  paddypower: {
    key: 'paddypower',
    name: 'Paddy Power',
    url: 'https://www.paddypower.com/basketball',
    region: ['UK', 'IE'],
    logo: getLogoUrl('paddypower', false),
    logoFallback: getLogoUrl('paddypower', false),
  },
  skybet: {
    key: 'skybet',
    name: 'Sky Bet',
    url: 'https://www.skybet.com/basketball',
    region: ['UK'],
    logo: getLogoUrl('skybet', false),
    logoFallback: getLogoUrl('skybet', false),
  },
  virginbet: {
    key: 'virginbet',
    name: 'Virgin Bet',
    url: 'https://www.virginbet.com/sports/basketball',
    region: ['UK'],
    logo: getLogoUrl('virginbet', false),
    logoFallback: getLogoUrl('virginbet', false),
  },
  betfair: {
    key: 'betfair',
    name: 'Betfair',
    url: 'https://www.betfair.com/sport/basketball',
    region: ['UK', 'EU', 'AU'],
    logo: getLogoUrl('betfair', false),
    logoFallback: getLogoUrl('betfair', false),
  },
  matchbook: {
    key: 'matchbook',
    name: 'Matchbook',
    url: 'https://www.matchbook.com/sports/basketball',
    region: ['UK', 'EU'],
    logo: getLogoUrl('matchbook', false),
    logoFallback: getLogoUrl('matchbook', false),
  },
  livescorebet: {
    key: 'livescorebet',
    name: 'LiveScore Bet',
    url: 'https://www.livescorebet.com/en/sports/basketball',
    region: ['UK'],
    logo: getLogoUrl('livescorebet', false),
    logoFallback: getLogoUrl('livescorebet', false),
  },
  mrgreen: {
    key: 'mrgreen',
    name: 'Mr Green',
    url: 'https://www.mrgreen.com/en/sports/basketball',
    region: ['UK', 'EU'],
    logo: getLogoUrl('mrgreen', false),
    logoFallback: getLogoUrl('mrgreen', false),
  },

  // ========== AUSTRALIA ==========
  sportsbet: {
    key: 'sportsbet',
    name: 'Sportsbet',
    url: 'https://www.sportsbet.com.au/betting/basketball',
    region: ['AU'],
    logo: getLogoUrl('sportsbet', false),
    logoFallback: getLogoUrl('sportsbet', false),
    popular: true,
  },
  tab: {
    key: 'tab',
    name: 'TAB',
    url: 'https://www.tab.com.au/sports/basketball',
    region: ['AU'],
    logo: getLogoUrl('tab', false),
    logoFallback: getLogoUrl('tab', false),
    popular: true,
  },
  neds: {
    key: 'neds',
    name: 'Neds',
    url: 'https://www.neds.com.au/sports/basketball',
    region: ['AU'],
    logo: getLogoUrl('neds', false),
    logoFallback: getLogoUrl('neds', false),
  },
  bluebet: {
    key: 'bluebet',
    name: 'BlueBet',
    url: 'https://www.bluebet.com.au/sports/basketball',
    region: ['AU'],
    logo: getLogoUrl('bluebet', false),
    logoFallback: getLogoUrl('bluebet', false),
  },
  picklebet: {
    key: 'picklebet',
    name: 'PickleBet',
    url: 'https://www.picklebet.com/sports/basketball',
    region: ['AU'],
    logo: getLogoUrl('picklebet', false),
    logoFallback: getLogoUrl('picklebet', false),
  },
  playup: {
    key: 'playup',
    name: 'PlayUp',
    url: 'https://www.playup.com/sports/basketball',
    region: ['AU'],
    logo: getLogoUrl('playup', false),
    logoFallback: getLogoUrl('playup', false),
  },
  topsport: {
    key: 'topsport',
    name: 'TopSport',
    url: 'https://www.topsport.com.au/Sport/Basketball',
    region: ['AU'],
    logo: getLogoUrl('topsport', false),
    logoFallback: getLogoUrl('topsport', false),
  },

  // ========== EUROPE ==========
  bwin: {
    key: 'bwin',
    name: 'bwin',
    url: 'https://sports.bwin.com/en/sports/basketball',
    region: ['EU'],
    logo: getLogoUrl('bwin', false),
    logoFallback: getLogoUrl('bwin', false),
    popular: true,
  },
  pinnacle: {
    key: 'pinnacle',
    name: 'Pinnacle',
    url: 'https://www.pinnacle.com/en/basketball',
    region: ['EU', 'Global'],
    logo: getLogoUrl('pinnacle', false),
    logoFallback: getLogoUrl('pinnacle', false),
    popular: true,
  },
  marathon: {
    key: 'marathon',
    name: 'Marathon Bet',
    url: 'https://www.marathonbet.com/en/betting/Basketball',
    region: ['EU'],
    logo: getLogoUrl('marathon', false),
    logoFallback: getLogoUrl('marathon', false),
  },
  betsson: {
    key: 'betsson',
    name: 'Betsson',
    url: 'https://www.betsson.com/en/sportsbook/basketball',
    region: ['EU'],
    logo: getLogoUrl('betsson', false),
    logoFallback: getLogoUrl('betsson', false),
  },
  nordicbet: {
    key: 'nordicbet',
    name: 'NordicBet',
    url: 'https://www.nordicbet.com/en/sportsbook/basketball',
    region: ['EU'],
    logo: getLogoUrl('nordicbet', false),
    logoFallback: getLogoUrl('nordicbet', false),
  },
  coolbet: {
    key: 'coolbet',
    name: 'Coolbet',
    url: 'https://www.coolbet.com/en/sportsbook/basketball',
    region: ['EU'],
    logo: getLogoUrl('coolbet', false),
    logoFallback: getLogoUrl('coolbet', false),
  },
  leovegas: {
    key: 'leovegas',
    name: 'LeoVegas',
    url: 'https://www.leovegas.com/en-row/sports/basketball',
    region: ['EU'],
    logo: getLogoUrl('leovegas', false),
    logoFallback: getLogoUrl('leovegas', false),
  },
  betclic: {
    key: 'betclic',
    name: 'Betclic',
    url: 'https://www.betclic.com/basketball',
    region: ['EU'],
    logo: getLogoUrl('betclic', false),
    logoFallback: getLogoUrl('betclic', false),
  },
  unibet_eu: {
    key: 'unibet_eu',
    name: 'Unibet EU',
    url: 'https://www.unibet.eu/betting/sports/basketball',
    region: ['EU'],
    logo: getLogoUrl('unibet_eu', false),
    logoFallback: getLogoUrl('unibet_eu', false),
  },
  sport888: {
    key: 'sport888',
    name: '888sport',
    url: 'https://www.888sport.com/basketball',
    region: ['EU', 'UK'],
    logo: getLogoUrl('sport888', false),
    logoFallback: getLogoUrl('sport888', false),
  },
  tipico: {
    key: 'tipico',
    name: 'Tipico',
    url: 'https://www.tipico.com/en/sports/basketball',
    region: ['EU'],
    logo: getLogoUrl('tipico', false),
    logoFallback: getLogoUrl('tipico', false),
  },
  betano: {
    key: 'betano',
    name: 'Betano',
    url: 'https://www.betano.com/sport/basketball',
    region: ['EU'],
    logo: getLogoUrl('betano', false),
    logoFallback: getLogoUrl('betano', false),
  },

  // ========== CANADA ==========
  sport_interaction: {
    key: 'sport_interaction',
    name: 'Sports Interaction',
    url: 'https://www.sportsinteraction.com/basketball',
    region: ['CA'],
    logo: getLogoUrl('sport_interaction', false),
    logoFallback: getLogoUrl('sport_interaction', false),
  },
  bet99: {
    key: 'bet99',
    name: 'Bet99',
    url: 'https://www.bet99.com/en/sports/basketball',
    region: ['CA'],
    logo: getLogoUrl('bet99', false),
    logoFallback: getLogoUrl('bet99', false),
  },
  betvictor: {
    key: 'betvictor',
    name: 'BetVictor',
    url: 'https://www.betvictor.com/en-ca/sports/basketball',
    region: ['CA', 'UK', 'EU'],
    logo: getLogoUrl('betvictor', false),
    logoFallback: getLogoUrl('betvictor', false),
  },

  // ========== ASIA ==========
  singbet: {
    key: 'singbet',
    name: 'SingBet',
    url: 'https://www.singbet.com/sports/basketball',
    region: ['ASIA'],
    logo: getLogoUrl('singbet', false),
    logoFallback: getLogoUrl('singbet', false),
  },
  orbit: {
    key: 'orbit',
    name: 'OrbitX',
    url: 'https://www.orbitx.com/sports/basketball',
    region: ['ASIA'],
    logo: getLogoUrl('orbit', false),
    logoFallback: getLogoUrl('orbit', false),
  },
};

/**
 * Helper function to get bookmaker data by key
 */
export const getBookmaker = (key: string): Bookmaker | undefined => {
  return BOOKMAKERS[key];
};

/**
 * Get all bookmakers for a specific region
 */
export const getBookmakersByRegion = (region: string): Bookmaker[] => {
  return Object.values(BOOKMAKERS).filter(book =>
    book.region.includes(region)
  );
};

/**
 * Get only popular/major bookmakers
 */
export const getPopularBookmakers = (): Bookmaker[] => {
  return Object.values(BOOKMAKERS).filter(book => book.popular);
};

/**
 * Get all bookmaker keys (for API calls)
 */
export const getAllBookmakerKeys = (): string[] => {
  return Object.keys(BOOKMAKERS);
};

/**
 * Search bookmakers by name
 */
export const searchBookmakers = (query: string): Bookmaker[] => {
  const lowerQuery = query.toLowerCase();
  return Object.values(BOOKMAKERS).filter(book =>
    book.name.toLowerCase().includes(lowerQuery) ||
    book.key.toLowerCase().includes(lowerQuery)
  );
};

export default BOOKMAKERS;
