/**
 * URL Builder for Sportsbooks
 * Constructs specific URLs for each bookmaker, sport, and game
 */

// Team name to URL slug conversion
function slugify(teamName) {
  return teamName
    .toLowerCase()
    .replace(/\s+/g, '-')           // Spaces to hyphens
    .replace(/[^a-z0-9-]/g, '')     // Remove special chars
    .replace(/-+/g, '-')            // Multiple hyphens to single
    .replace(/^-|-$/g, '');         // Trim hyphens
}

// Extract sport key from full sport identifier
function getSportKey(sportKey) {
  if (!sportKey) return 'basketball'; // default

  if (sportKey.includes('basketball')) return 'basketball';
  if (sportKey.includes('football_nfl')) return 'americanfootball';
  if (sportKey.includes('football_ncaaf')) return 'americanfootball';
  if (sportKey.includes('baseball')) return 'baseball';
  if (sportKey.includes('hockey')) return 'icehockey';
  if (sportKey.includes('soccer')) return 'soccer';

  return 'basketball'; // default
}

// Extract league from sport key
function getLeague(sportKey) {
  if (!sportKey) return 'nba';

  if (sportKey.includes('nba')) return 'nba';
  if (sportKey.includes('nfl')) return 'nfl';
  if (sportKey.includes('ncaaf')) return 'ncaaf';
  if (sportKey.includes('mlb')) return 'mlb';
  if (sportKey.includes('nhl')) return 'nhl';
  if (sportKey.includes('mls')) return 'mls';
  if (sportKey.includes('epl')) return 'epl';

  return 'nba'; // default
}

/**
 * Build URL for a specific bookmaker and game
 * @param {string} bookmaker - Bookmaker key (e.g., 'draftkings', 'fanduel')
 * @param {object} game - Game data from API
 * @param {string} game.sport_key - Sport identifier (e.g., 'basketball_nba')
 * @param {string} game.home_team - Home team name
 * @param {string} game.away_team - Away team name
 * @param {string} game.commence_time - Game start time ISO string
 * @returns {string} - URL to open
 */
function buildBookmakerURL(bookmaker, game = null) {
  const sport = game ? getSportKey(game.sport_key) : 'basketball';
  const league = game ? getLeague(game.sport_key) : 'nba';

  const homeSlug = game ? slugify(game.home_team) : '';
  const awaySlug = game ? slugify(game.away_team) : '';

  // URL patterns for each bookmaker
  const urlPatterns = {
    // TIER 1: Major US Books (have deep linking)
    'draftkings': {
      base: 'https://sportsbook.draftkings.com',
      sport: {
        'basketball': `/leagues/basketball/${league}`,
        'americanfootball': `/leagues/football/${league}`,
        'icehockey': `/leagues/hockey/${league}`,
        'baseball': `/leagues/baseball/${league}`,
        'soccer': `/leagues/soccer/${league}`
      },
      // DraftKings doesn't have predictable game URLs
      game: null
    },

    'fanduel': {
      base: 'https://sportsbook.fanduel.com',
      sport: {
        'basketball': `/navigation/${league}`,
        'americanfootball': `/navigation/${league}`,
        'icehockey': `/navigation/${league}`,
        'baseball': `/navigation/${league}`,
        'soccer': `/navigation/${league}`
      },
      game: null // FanDuel uses dynamic IDs
    },

    'betmgm': {
      base: 'https://sports.betmgm.com',
      sport: {
        'basketball': `/en/sports/${sport}-7/betting/usa-9/${league}`,
        'americanfootball': `/en/sports/${sport}-16/betting/usa-9/${league}`,
        'icehockey': `/en/sports/${sport}-17/betting/usa-9/${league}`,
        'baseball': `/en/sports/${sport}-23/betting/usa-9/${league}`,
        'soccer': `/en/sports/${sport}-4/betting`
      },
      game: null
    },

    'caesars': {
      base: 'https://www.caesars.com/sportsbook-and-casino',
      sport: {
        'basketball': `/${sport}/${league}`,
        'americanfootball': `/${sport}/${league}`,
        'icehockey': `/${sport}/${league}`,
        'baseball': `/${sport}/${league}`,
        'soccer': `/${sport}/${league}`
      },
      game: null
    },

    'betrivers': {
      base: 'https://www.betrivers.com',
      sport: {
        'basketball': `/?page=sportsbook#${sport}`,
        'americanfootball': `/?page=sportsbook#${sport}`,
        'icehockey': `/?page=sportsbook#${sport}`,
        'baseball': `/?page=sportsbook#${sport}`,
        'soccer': `/?page=sportsbook#${sport}`
      },
      game: null
    },

    // TIER 2: Offshore Books
    'bovada': {
      base: 'https://www.bovada.lv',
      sport: {
        'basketball': `/sports/${sport}/${league}`,
        'americanfootball': `/sports/${sport}/${league}`,
        'icehockey': `/sports/${sport}/${league}`,
        'baseball': `/sports/${sport}/${league}`,
        'soccer': `/sports/${sport}/${league}`
      },
      game: null // Bovada uses session-based URLs
    },

    'betonlineag': {
      base: 'https://www.betonline.ag',
      sport: {
        'basketball': `/sportsbook/${sport}/${league}`,
        'americanfootball': `/sportsbook/${sport}/${league}`,
        'icehockey': `/sportsbook/${sport}/${league}`,
        'baseball': `/sportsbook/${sport}/${league}`,
        'soccer': `/sportsbook/${sport}`
      },
      game: null
    },

    'mybookieag': {
      base: 'https://www.mybookie.ag',
      sport: {
        'basketball': `/sportsbook/${league}/`,
        'americanfootball': `/sportsbook/${league}/`,
        'icehockey': `/sportsbook/${league}/`,
        'baseball': `/sportsbook/${league}/`,
        'soccer': `/sportsbook/soccer/`
      },
      game: null
    },

    'betus': {
      base: 'https://www.betus.com.pa',
      sport: {
        'basketball': `/sportsbook/${sport}/`,
        'americanfootball': `/sportsbook/${sport}/`,
        'icehockey': `/sportsbook/${sport}/`,
        'baseball': `/sportsbook/${sport}/`,
        'soccer': `/sportsbook/${sport}/`
      },
      game: null
    },

    'lowvig': {
      base: 'https://lowvig.ag',
      sport: {
        'basketball': `/sports/${sport}`,
        'americanfootball': `/sports/${sport}`,
        'icehockey': `/sports/${sport}`,
        'baseball': `/sports/${sport}`,
        'soccer': `/sports/${sport}`
      },
      game: null
    },

    'williamhill_us': {
      base: 'https://www.williamhill.com/us',
      sport: {
        'basketball': `/bet/en/betting/t/${sport}/${league}`,
        'americanfootball': `/bet/en/betting/t/${sport}/${league}`,
        'icehockey': `/bet/en/betting/t/${sport}/${league}`,
        'baseball': `/bet/en/betting/t/${sport}/${league}`,
        'soccer': `/bet/en/betting/t/${sport}`
      },
      game: null
    }
  };

  // Get bookmaker config
  const config = urlPatterns[bookmaker];
  if (!config) {
    console.warn(`[URL Builder] No URL pattern for bookmaker: ${bookmaker}`);
    return null;
  }

  // Try to build game-specific URL if available
  if (game && config.game) {
    const gameUrl = config.game(homeSlug, awaySlug, league);
    if (gameUrl) {
      return `${config.base}${gameUrl}`;
    }
  }

  // Fall back to sport-level URL
  const sportUrl = config.sport[sport] || config.sport['basketball'];
  return `${config.base}${sportUrl}`;
}

/**
 * Get bookmaker display info
 */
function getBookmakerInfo(bookmakerKey) {
  const bookmakers = {
    'draftkings': { name: 'DraftKings', logo: 'https://www.google.com/s2/favicons?domain=draftkings.com&sz=64' },
    'fanduel': { name: 'FanDuel', logo: 'https://www.google.com/s2/favicons?domain=fanduel.com&sz=64' },
    'betmgm': { name: 'BetMGM', logo: 'https://www.google.com/s2/favicons?domain=betmgm.com&sz=64' },
    'caesars': { name: 'Caesars', logo: 'https://www.google.com/s2/favicons?domain=caesars.com&sz=64' },
    'betrivers': { name: 'BetRivers', logo: 'https://www.google.com/s2/favicons?domain=betrivers.com&sz=64' },
    'bovada': { name: 'Bovada', logo: 'https://www.google.com/s2/favicons?domain=bovada.lv&sz=64' },
    'betonlineag': { name: 'BetOnline', logo: 'https://www.google.com/s2/favicons?domain=betonline.ag&sz=64' },
    'mybookieag': { name: 'MyBookie', logo: 'https://www.google.com/s2/favicons?domain=mybookie.ag&sz=64' },
    'betus': { name: 'BetUS', logo: 'https://www.google.com/s2/favicons?domain=betus.com.pa&sz=64' },
    'lowvig': { name: 'LowVig', logo: 'https://www.google.com/s2/favicons?domain=lowvig.ag&sz=64' },
    'williamhill_us': { name: 'William Hill', logo: 'https://www.google.com/s2/favicons?domain=williamhill.com&sz=64' }
  };

  return bookmakers[bookmakerKey] || {
    name: bookmakerKey.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    logo: `https://www.google.com/s2/favicons?domain=${bookmakerKey}.com&sz=64`
  };
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { buildBookmakerURL, getBookmakerInfo, slugify };
}
