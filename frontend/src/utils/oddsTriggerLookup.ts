/**
 * Odds Trigger Lookup Utility
 * Calculates minimum acceptable betting odds based on strategy win rate
 */

interface OddsLookupEntry {
  win_rate_pct: number;
  win_probability: number;
  decimal_odds: number;
  american_odds_exact: number;
  american_odds_rounded: number;
  min_acceptable_odds: string;
}

// Pre-calculated lookup table (loaded from public/odds_trigger_lookup.json)
let oddsLookupTable: OddsLookupEntry[] = [];

/**
 * Load the odds lookup table from public folder
 */
export async function loadOddsLookupTable(): Promise<void> {
  try {
    const response = await fetch('/odds_trigger_lookup.json');
    oddsLookupTable = await response.json();
  } catch (error) {
    console.error('Failed to load odds trigger lookup table:', error);
    oddsLookupTable = [];
  }
}

/**
 * Calculate minimum acceptable odds for a given win rate
 * Uses interpolation for win rates between table entries
 *
 * @param winRate - Win rate as percentage (e.g., 53.4 for 53.4%)
 * @returns Minimum acceptable odds in American format (e.g., "-115", "+120")
 */
export function getMinAcceptableOdds(winRate: number): string {
  if (!oddsLookupTable || oddsLookupTable.length === 0) {
    // Fallback calculation if table not loaded
    return calculateOddsDirectly(winRate);
  }

  // Handle edge cases
  if (winRate < 50) return '+100'; // Below 50% = underdog territory
  if (winRate >= 75) return '-300'; // 75%+ = max in our table

  // Find the two closest entries in the lookup table
  let lowerEntry: OddsLookupEntry | null = null;
  let upperEntry: OddsLookupEntry | null = null;

  for (let i = 0; i < oddsLookupTable.length - 1; i++) {
    if (winRate >= oddsLookupTable[i].win_rate_pct && winRate <= oddsLookupTable[i + 1].win_rate_pct) {
      lowerEntry = oddsLookupTable[i];
      upperEntry = oddsLookupTable[i + 1];
      break;
    }
  }

  // Exact match found
  if (lowerEntry && lowerEntry.win_rate_pct === winRate) {
    return lowerEntry.min_acceptable_odds;
  }

  // Interpolate between two entries
  if (lowerEntry && upperEntry) {
    const ratio = (winRate - lowerEntry.win_rate_pct) / (upperEntry.win_rate_pct - lowerEntry.win_rate_pct);
    const interpolatedOdds = lowerEntry.american_odds_rounded +
                             ratio * (upperEntry.american_odds_rounded - lowerEntry.american_odds_rounded);

    // Round to nearest 5 (standard sportsbook practice)
    const rounded = Math.round(interpolatedOdds / 5) * 5;
    return rounded >= 0 ? `+${rounded}` : `${rounded}`;
  }

  // Fallback to direct calculation
  return calculateOddsDirectly(winRate);
}

/**
 * Direct calculation of minimum acceptable odds (fallback)
 *
 * @param winRate - Win rate as percentage
 * @returns Minimum acceptable odds in American format
 */
function calculateOddsDirectly(winRate: number): string {
  const winProbability = winRate / 100;
  const decimalOdds = 1 / winProbability;

  let americanOdds: number;

  if (winProbability > 0.5) {
    // Favorite (negative odds)
    americanOdds = -100 / (decimalOdds - 1);
  } else if (winProbability < 0.5) {
    // Underdog (positive odds)
    americanOdds = 100 * (decimalOdds - 1);
  } else {
    // Even money
    americanOdds = 100;
  }

  // Round to nearest 5
  const rounded = Math.round(americanOdds / 5) * 5;
  return rounded >= 0 ? `+${rounded}` : `${rounded}`;
}

/**
 * Get odds with color coding for UI display
 *
 * @param winRate - Win rate as percentage
 * @returns Object with odds and color class
 */
export function getOddsWithColor(winRate: number): { odds: string; colorClass: string } {
  const odds = getMinAcceptableOdds(winRate);

  // Determine color based on odds value
  let colorClass = 'text-white';

  if (odds.startsWith('+')) {
    // Positive odds (underdog) - green
    colorClass = 'text-green-400';
  } else if (odds.startsWith('-')) {
    const value = Math.abs(parseInt(odds));
    if (value >= 200) {
      // Heavy favorite - red
      colorClass = 'text-red-400';
    } else if (value >= 150) {
      // Strong favorite - orange
      colorClass = 'text-orange-400';
    } else {
      // Slight favorite - yellow
      colorClass = 'text-yellow-400';
    }
  }

  return { odds, colorClass };
}

/**
 * Format odds for display with proper styling
 *
 * @param winRate - Win rate as percentage
 * @returns Formatted odds string with sign
 */
export function formatOddsDisplay(winRate: number | undefined): string {
  if (!winRate || winRate < 50) {
    return 'N/A';
  }

  return getMinAcceptableOdds(winRate);
}
