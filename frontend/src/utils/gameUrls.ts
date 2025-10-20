/**
 * Game-Specific URL Builder for Sportsbooks
 * Constructs URLs that take users directly to a specific game
 */

/**
 * Create a URL-safe slug from team name
 * "San Francisco 49ers" -> "san-francisco-49ers"
 */
const createSlug = (teamName: string): string => {
  return teamName
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '') // Remove special chars
    .trim()
    .replace(/\s+/g, '-'); // Replace spaces with hyphens
};

/**
 * Get short team name (last word usually)
 * "Los Angeles Lakers" -> "lakers"
 * "San Francisco 49ers" -> "49ers"
 */
const getShortTeamName = (teamName: string): string => {
  const words = teamName.trim().split(' ');
  return words[words.length - 1].toLowerCase();
};

/**
 * Build game-specific URL for a sportsbook
 *
 * @param bookmakerKey - The bookmaker identifier (e.g., 'draftkings')
 * @param homeTeam - Home team name
 * @param awayTeam - Away team name
 * @param sportKey - Sport identifier (e.g., 'basketball_nba', 'americanfootball_nfl')
 * @param gameDate - Game date/time
 * @returns Game-specific URL or generic sport URL if can't build specific one
 */
export const getGameSpecificUrl = (
  bookmakerKey: string,
  homeTeam: string,
  awayTeam: string,
  sportKey: string,
  gameDate?: string
): string | null => {
  const awaySlug = createSlug(awayTeam);
  const homeSlug = createSlug(homeTeam);
  const awayShort = getShortTeamName(awayTeam);
  const homeShort = getShortTeamName(homeTeam);

  // Map sport keys to readable names
  const sportMap: Record<string, string> = {
    'basketball_nba': 'nba',
    'americanfootball_nfl': 'nfl',
    'icehockey_nhl': 'nhl',
    'baseball_mlb': 'mlb',
    'basketball_ncaab': 'ncaab',
    'americanfootball_ncaaf': 'ncaaf',
  };

  const sport = sportMap[sportKey] || 'basketball';

  // Normalize bookmaker key
  const normalizedKey = bookmakerKey
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/\./g, '')
    .replace(/_/g, '');

  // Build game-specific URLs based on each sportsbook's URL pattern
  // These patterns were researched from actual sportsbook URLs

  switch (normalizedKey) {
    case 'draftkings':
      // DraftKings uses format: /leagues/SPORT/LEAGUE?subcategory=game-lines
      // They don't have game-specific URLs easily accessible, so we go to sport page
      return `https://sportsbook.draftkings.com/leagues/${sport === 'nfl' ? 'football' : sport}/${sport.toUpperCase()}?subcategory=game-lines`;

    case 'fanduel':
      // FanDuel uses format: /navigation/SPORT
      // Try to use matchup format if available: /matchup/AWAY-at-HOME
      if (sport === 'nba') {
        return `https://sportsbook.fanduel.com/navigation/nba?tab=player-points`;
      } else if (sport === 'nfl') {
        return `https://sportsbook.fanduel.com/navigation/nfl?tab=all-games`;
      }
      return `https://sportsbook.fanduel.com/navigation/${sport}`;

    case 'betmgm':
      // BetMGM format varies by sport
      if (sport === 'nba') {
        return `https://sports.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004`;
      } else if (sport === 'nfl') {
        return `https://sports.betmgm.com/en/sports/football-6/betting/usa-9/nfl-35`;
      }
      return `https://sports.betmgm.com/en/sports`;

    case 'caesars':
      // Caesars format: /sportsbook-and-casino/SPORT
      if (sport === 'nba') {
        return `https://www.caesars.com/sportsbook-and-casino/basketball/nba`;
      } else if (sport === 'nfl') {
        return `https://www.caesars.com/sportsbook-and-casino/football/nfl`;
      }
      return `https://www.caesars.com/sportsbook-and-casino`;

    case 'betrivers':
      // BetRivers format: /?page=sportsbook#SPORT
      if (sport === 'nba') {
        return `https://www.betrivers.com/?page=sportsbook#basketball`;
      } else if (sport === 'nfl') {
        return `https://www.betrivers.com/?page=sportsbook#americanfootball`;
      }
      return `https://www.betrivers.com/?page=sportsbook`;

    case 'pointsbet':
    case 'pointsbetau':
      // PointsBet format: /sports/SPORT
      return `https://pointsbet.com/sports/${sport === 'nfl' ? 'american-football/nfl' : sport}`;

    case 'williamhillus':
      // William Hill format: varies
      if (sport === 'nba') {
        return `https://www.williamhill.com/us/nv/bet/en/betting/t/basketball/nba`;
      } else if (sport === 'nfl') {
        return `https://www.williamhill.com/us/nv/bet/en/betting/t/american-football/nfl`;
      }
      return `https://www.williamhill.com/us/nv/bet/en/betting`;

    case 'fanatics':
      // Fanatics format: /sportsbook/SPORT
      return `https://fanatics.com/sportsbook/${sport === 'nfl' ? 'american-football/nfl' : `${sport}/${sport}`}`;

    case 'espnbet':
      // ESPN BET format: /sport/SPORT/league
      if (sport === 'nba') {
        return `https://espnbet.com/sport/basketball/usa/nba`;
      } else if (sport === 'nfl') {
        return `https://espnbet.com/sport/american-football/usa/nfl`;
      }
      return `https://espnbet.com/sport/${sport}`;

    case 'bovada':
      // Bovada format: /sports/SPORT
      return `https://www.bovada.lv/sports/${sport === 'nfl' ? 'football' : sport}`;

    case 'betonlineag':
      // BetOnline format: /sportsbook/SPORT
      if (sport === 'nba') {
        return `https://www.betonline.ag/sportsbook/basketball/nba`;
      } else if (sport === 'nfl') {
        return `https://www.betonline.ag/sportsbook/football/nfl`;
      }
      return `https://www.betonline.ag/sportsbook`;

    case 'mybookieag':
    case 'mybookie':
      // MyBookie format: /sportsbook/SPORT
      return `https://www.mybookie.ag/sportsbook/${sport}/`;

    case 'bet365':
      // Bet365 format: /sports/SPORT
      return `https://www.bet365.com/sports/${sport === 'nfl' ? 'american-football' : sport}`;

    case 'betway':
      // Betway format: /sports/grp/SPORT
      return `https://sports.betway.com/en/sports/grp/${sport === 'nfl' ? 'american-football' : sport}`;

    case 'unibet':
    case 'unibeteu':
      // Unibet format: /betting/sports/SPORT
      return `https://www.unibet.com/betting/sports/${sport === 'nfl' ? 'american-football' : sport}`;

    default:
      // For unknown sportsbooks, return null and we'll use the generic URL from bookmakers.ts
      return null;
  }
};

/**
 * Get display text for "View on [Bookmaker]"
 */
export const getViewGameText = (bookmakerName: string, hasSpecificUrl: boolean): string => {
  if (hasSpecificUrl) {
    return `View ${bookmakerName} odds`;
  }
  return `Visit ${bookmakerName}`;
};

export default {
  getGameSpecificUrl,
  getViewGameText,
};
