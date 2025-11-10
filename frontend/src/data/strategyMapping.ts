/**
 * Unified Strategy Mapping
 * Maps StrategySettings.tsx strategies to ADVANCED_SYSTEMS IDs for backend integration
 */

export interface StrategyMapping {
  // Strategy Settings ID
  settingsId: string;

  // Maps to ADVANCED_SYSTEMS.id
  systemId: number | null;

  // Strategy metadata
  name: string;
  category: 'pregame' | 'live';

  // Implementation status
  hasBackendDetection: boolean;
  hasAlertEndpoint: boolean;
}

export const STRATEGY_MAPPINGS: StrategyMapping[] = [
  // ========== PRE-GAME STRATEGIES ==========
  {
    settingsId: 'steam-plays',
    systemId: null, // Steam moves detected by alert_monitor.py but not in ADVANCED_SYSTEMS
    name: 'Steam Plays',
    category: 'pregame',
    hasBackendDetection: true, // Detected by alert_monitor
    hasAlertEndpoint: true // Included in /api/alerts/all
  },
  {
    settingsId: 'sharp-money',
    systemId: 117, // Sharp Money Tracking
    name: 'Sharp Money Tracking',
    category: 'pregame',
    hasBackendDetection: true, // ✅ Implemented in Phase 2
    hasAlertEndpoint: true // ✅ /api/alerts/sharp-money
  },
  {
    settingsId: 'closing-line-value',
    systemId: 118, // CLV Tracker
    name: 'Closing Line Value (CLV)',
    category: 'pregame',
    hasBackendDetection: false, // TODO: Needs implementation
    hasAlertEndpoint: false
  },
  {
    settingsId: 'multi-fatigue',
    systemId: 110, // Fatigue Spreads (Back-to-Backs)
    name: 'Schedule Fatigue',
    category: 'pregame',
    hasBackendDetection: false, // TODO: Needs implementation
    hasAlertEndpoint: false
  },
  {
    settingsId: 'nfl-weather',
    systemId: 112, // Weather-Driven Live Totals
    name: 'Weather Impact',
    category: 'pregame',
    hasBackendDetection: false, // TODO: Needs implementation
    hasAlertEndpoint: false
  },
  {
    settingsId: 'pace-based',
    systemId: 25, // Pace Mismatch Detector
    name: 'Pace Mismatches',
    category: 'pregame',
    hasBackendDetection: true,
    hasAlertEndpoint: true
  },
  {
    settingsId: 'matchup-history',
    systemId: null, // Not in ADVANCED_SYSTEMS
    name: 'Matchup History',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },
  {
    settingsId: 'player-props',
    systemId: null, // Not in ADVANCED_SYSTEMS
    name: 'Player Props',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },
  {
    settingsId: 'regression-analysis',
    systemId: null, // Not in ADVANCED_SYSTEMS (different from Max EV Boost)
    name: 'Regression Analysis',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },
  {
    settingsId: 'b2b-vs-rested',
    systemId: 110, // Fatigue Spreads (Back-to-Backs)
    name: 'Back-to-Back vs Rested',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },
  {
    settingsId: 'nhl-b2b-vs-rested',
    systemId: 110, // Same system, different sport
    name: 'Back-to-Back vs Rested (NHL)',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },
  {
    settingsId: 'home-away-splits',
    systemId: 119, // Home/Away Splits Strategy
    name: 'Home/Away Splits',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },
  {
    settingsId: 'divisional-rivalries',
    systemId: null, // Not in ADVANCED_SYSTEMS
    name: 'Divisional Rivalries',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },
  {
    settingsId: 'revenge-games',
    systemId: null, // Not in ADVANCED_SYSTEMS
    name: 'Revenge Games',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },
  {
    settingsId: 'fade-the-public',
    systemId: null, // Not in ADVANCED_SYSTEMS
    name: 'Fade the Public',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },
  {
    settingsId: 'reverse-line-movement',
    systemId: 117, // Part of Sharp Money Tracking
    name: 'Reverse Line Movement (RLM)',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },
  {
    settingsId: 'after-blowout-loss',
    systemId: null, // Not in ADVANCED_SYSTEMS
    name: 'After Blowout Loss',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },
  {
    settingsId: 'letdown-spot',
    systemId: null, // Not in ADVANCED_SYSTEMS
    name: 'Letdown Spot',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },
  {
    settingsId: 'lookahead-spot',
    systemId: null, // Not in ADVANCED_SYSTEMS
    name: 'Lookahead Spot',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },
  {
    settingsId: 'nfl-primetime-unders',
    systemId: null, // Not in ADVANCED_SYSTEMS
    name: 'Primetime Unders',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },
  {
    settingsId: 'conference-mismatch',
    systemId: null, // Not in ADVANCED_SYSTEMS
    name: 'Conference Mismatches',
    category: 'pregame',
    hasBackendDetection: false,
    hasAlertEndpoint: false
  },

  // ========== LIVE STRATEGIES ==========
  {
    settingsId: 'nhl-goalie-pull',
    systemId: 6, // Goalie Pull Alert
    name: 'Empty Net Goals',
    category: 'live',
    hasBackendDetection: true,
    hasAlertEndpoint: true
  },
  {
    settingsId: 'nba-favorite-comeback',
    systemId: 13, // Favorite Comeback Detection
    name: 'Favorite Comeback',
    category: 'live',
    hasBackendDetection: true,
    hasAlertEndpoint: true
  },
  {
    settingsId: 'quarter-reversal',
    systemId: 14, // Quarter Reversal Strategy
    name: 'Quarter Reversal',
    category: 'live',
    hasBackendDetection: true,
    hasAlertEndpoint: true
  },
  {
    settingsId: 'nba-halftime-tracker',
    systemId: 23, // Halftime Tracker
    name: 'Halftime Adjustments',
    category: 'live',
    hasBackendDetection: true,
    hasAlertEndpoint: true
  },
  {
    settingsId: 'nhl-halftime-tracker',
    systemId: 23, // Same system, different sport
    name: 'Period Tracking',
    category: 'live',
    hasBackendDetection: true,
    hasAlertEndpoint: true
  },
  {
    settingsId: 'nba-momentum',
    systemId: 24, // Momentum Detector
    name: 'Momentum Detector',
    category: 'live',
    hasBackendDetection: true,
    hasAlertEndpoint: true
  }
];

/**
 * Get system ID for a strategy settings ID
 */
export function getSystemIdForStrategy(settingsId: string): number | null {
  const mapping = STRATEGY_MAPPINGS.find(m => m.settingsId === settingsId);
  return mapping?.systemId || null;
}

/**
 * Check if a strategy has backend detection
 */
export function hasBackendDetection(settingsId: string): boolean {
  const mapping = STRATEGY_MAPPINGS.find(m => m.settingsId === settingsId);
  return mapping?.hasBackendDetection || false;
}

/**
 * Get all strategies with backend detection
 */
export function getStrategiesWithDetection(): StrategyMapping[] {
  return STRATEGY_MAPPINGS.filter(m => m.hasBackendDetection);
}

/**
 * Get strategies missing backend implementation
 */
export function getStrategiesNeedingImplementation(): StrategyMapping[] {
  return STRATEGY_MAPPINGS.filter(m => !m.hasBackendDetection);
}
