/**
 * Bookmaker utilities - icons, names, and data
 * Consistent with ARB Extension design
 */

export interface BookmakerInfo {
  name: string;
  domain: string;
  logo: string;
}

const bookmakerMap: Record<string, { name: string; domain: string }> = {
  'draftkings': { name: 'DraftKings', domain: 'draftkings.com' },
  'fanduel': { name: 'FanDuel', domain: 'fanduel.com' },
  'betmgm': { name: 'BetMGM', domain: 'betmgm.com' },
  'betrivers': { name: 'BetRivers', domain: 'betrivers.com' },
  'williamhill_us': { name: 'William Hill', domain: 'williamhill.com' },
  'fanatics': { name: 'Fanatics', domain: 'fanatics.com' },
  'espnbet': { name: 'ESPN BET', domain: 'espnbet.com' },
  'caesars': { name: 'Caesars', domain: 'caesars.com' },
  'pointsbet': { name: 'PointsBet', domain: 'pointsbet.com' },
  'ballybet': { name: 'Bally Bet', domain: 'ballybet.com' },
  'betonlineag': { name: 'BetOnline', domain: 'betonline.ag' },
  'bovada': { name: 'Bovada', domain: 'bovada.lv' },
  'mybookieag': { name: 'MyBookie', domain: 'mybookie.ag' },
  'lowvig': { name: 'LowVig', domain: 'lowvig.ag' },
  'betway': { name: 'Betway', domain: 'betway.com' },
  'betus': { name: 'BetUS', domain: 'betus.com.pa' },
  'superbook': { name: 'SuperBook', domain: 'superbook.com' },
  'wynnbet': { name: 'WynnBet', domain: 'wynnbet.com' },
  'unibet_us': { name: 'Unibet', domain: 'unibet.com' },
  'twinspires': { name: 'TwinSpires', domain: 'twinspires.com' },
  'sugarhouse': { name: 'SugarHouse', domain: 'sugarhousecasino.com' },
  'betfred': { name: 'Betfred', domain: 'betfred.com' },
  'hardrockbet': { name: 'Hard Rock', domain: 'hardrock.com' },
  'sisportsbook': { name: 'SI Sportsbook', domain: 'sisportsbook.com' },
  'barstool': { name: 'Barstool', domain: 'barstoolsportsbook.com' }
};

/**
 * Get bookmaker information including logo URL
 * Uses Google's favicon service for consistency with ARB Extension
 */
export function getBookmaker(key: string): BookmakerInfo {
  const bookmaker = bookmakerMap[key.toLowerCase()];

  if (bookmaker) {
    return {
      name: bookmaker.name,
      domain: bookmaker.domain,
      logo: `https://www.google.com/s2/favicons?domain=${bookmaker.domain}&sz=64`
    };
  }

  // Fallback for unknown bookmakers
  const cleanName = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  return {
    name: cleanName,
    domain: `${key}.com`,
    logo: `https://www.google.com/s2/favicons?domain=${key}.com&sz=64`
  };
}

/**
 * Format American odds for display
 */
export function formatOdds(odds: number): string {
  if (odds > 0) return `+${Math.round(odds)}`;
  return Math.round(odds).toString();
}

/**
 * Get market type label for display
 */
export function getMarketLabel(marketType: string): string {
  const labels: Record<string, string> = {
    'h2h': 'Moneyline',
    'spreads': 'Spread',
    'totals': 'Over/Under',
    'player_points': 'Player Points',
    'player_rebounds': 'Player Rebounds',
    'player_assists': 'Player Assists'
  };

  return labels[marketType] || marketType.replace(/_/g, ' ').toUpperCase();
}
