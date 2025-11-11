import { AdvancedSystem } from '../types';

export const ADVANCED_SYSTEMS: AdvancedSystem[] = [
  // NBA SYSTEMS
  {
    id: 1,
    name: "Max EV Boost",
    status: "live",
    description: "XGBoost-powered live total analysis. Detects when live lines drift 2+ standard deviations from predicted value.",
    sports: ["basketball_nba"],
    difficulty: "MEDIUM",
    evRange: { min: 14, max: 35 },
    performance: {
      winRate: 66.3,
      roi: 26.5,
      alerts: 163,
      games: 3690
    },
    backend: "backend/ml/nba_regression_analyzer.py",
    apiEndpoint: "/api/strategies/regression-to-mean/analyze"
  },
  {
    id: 14,
    name: "Quarter Reversal Strategy",
    status: "active",
    description: "Teams winning 2 consecutive quarters lose the next quarter at 55-61% rate",
    sports: ["basketball_nba"],
    difficulty: "MEDIUM",
    evRange: { min: 8, max: 15 },
    performance: {
      winRate: 55.7,
      roi: 10.5,
      games: 423
    },
    strategyId: 14
  },
  {
    id: 23,
    name: "Halftime Tracker",
    status: "active",
    description: "2H betting opportunities based on 1H performance and regression",
    sports: ["basketball_nba", "basketball_ncaab"],
    difficulty: "MEDIUM",
    evRange: { min: 3, max: 6 },
    performance: {
      winRate: 60.2,
      roi: 3.9,
      games: 892
    },
    strategyId: 23
  },
  {
    id: 24,
    name: "Momentum Detector",
    status: "active",
    description: "Detects when teams are 'on a run' and live odds haven't adjusted",
    sports: ["basketball_nba", "icehockey_nhl"],
    difficulty: "MEDIUM",
    evRange: { min: 2, max: 5 },
    performance: {
      winRate: 57.8,
      roi: 2.3,
      games: 234
    },
    strategyId: 24
  },
  {
    id: 25,
    name: "Pace Mismatch Detector",
    status: "active",
    description: "Detects EV opportunities based on pace tempo mismatches",
    sports: ["basketball_nba", "basketball_ncaab"],
    difficulty: "MEDIUM",
    evRange: { min: 7, max: 12 },
    performance: {
      winRate: 56.8,
      roi: 8.4,
      games: 256
    },
    strategyId: 25
  },
  {
    id: 8,
    name: "End-Game Unders",
    status: "active",
    description: "Bet Q4 under when there's a blowout after Q3",
    sports: ["basketball_nba", "basketball_ncaab"],
    difficulty: "EASY",
    evRange: { min: 4, max: 7 },
    performance: {
      winRate: 61.7,
      roi: 5.1,
      games: 223
    },
    strategyId: 8
  },
  {
    id: 13,
    name: "Favorite Comeback Detection",
    status: "pending",
    description: "Identifies when pre-game favorites trailing after hot underdog starts are prime comeback candidates",
    sports: ["basketball_nba"],
    difficulty: "MEDIUM",
    evRange: { min: 8, max: 12 },
    backend: "backend/strategies/favorite_comeback_detector.py",
    strategyId: 13
  },
  {
    id: 101,
    name: "Hot-Shooting Fade",
    status: "pending",
    description: "Fade teams that had an unusually hot shooting night in their previous game",
    sports: ["basketball_nba", "basketball_ncaab"],
    difficulty: "EASY",
    evRange: { min: 8, max: 15 },
    strategyId: 1
  },
  {
    id: 102,
    name: "Momentum Shift Betting",
    status: "pending",
    description: "Bet on teams immediately after a major momentum shift in the game",
    sports: ["basketball_nba", "americanfootball_nfl", "icehockey_nhl"],
    difficulty: "MEDIUM",
    evRange: { min: 5, max: 12 },
    strategyId: 2
  },
  {
    id: 103,
    name: "Injury Cascade Props",
    status: "pending",
    description: "Target player props on role players when stars get injured mid-game",
    sports: ["basketball_nba", "americanfootball_nfl"],
    difficulty: "HARD",
    evRange: { min: 15, max: 30 },
    strategyId: 3
  },
  {
    id: 104,
    name: "The Pace Trap",
    status: "pending",
    description: "Bet overs when slow-paced teams fall behind early",
    sports: ["basketball_nba", "basketball_ncaab"],
    difficulty: "EASY",
    evRange: { min: 10, max: 18 },
    strategyId: 4
  },
  {
    id: 105,
    name: "Foul Trouble Overs",
    status: "pending",
    description: "Bet team totals over when key defenders pick up early fouls",
    sports: ["basketball_nba", "basketball_ncaab"],
    difficulty: "MEDIUM",
    evRange: { min: 8, max: 16 },
    strategyId: 5
  },
  {
    id: 107,
    name: "Blowout Contrarian Spreads",
    status: "pending",
    description: "Bet underdogs when they're down big at halftime but showing fight",
    sports: ["basketball_nba", "americanfootball_nfl"],
    difficulty: "MEDIUM",
    evRange: { min: 6, max: 14 },
    strategyId: 7
  },
  {
    id: 109,
    name: "Overtime Total Resets",
    status: "pending",
    description: "Bet under on adjusted OT totals after high-scoring regulation",
    sports: ["basketball_nba", "americanfootball_nfl", "icehockey_nhl"],
    difficulty: "MEDIUM",
    evRange: { min: 7, max: 15 },
    strategyId: 9
  },
  {
    id: 110,
    name: "Fatigue Spreads (Back-to-Backs)",
    status: "pending",
    description: "Bet against teams on 2nd night of B2B playing against rested opponents",
    sports: ["basketball_nba", "icehockey_nhl"],
    difficulty: "EASY",
    evRange: { min: 8, max: 16 },
    backend: "backend/strategies/b2b_vs_rested_strategy.py",
    strategyId: 10
  },
  {
    id: 111,
    name: "Coaching Timeout Value",
    status: "pending",
    description: "Bet against teams immediately after burning all timeouts early",
    sports: ["basketball_nba", "americanfootball_nfl"],
    difficulty: "HARD",
    evRange: { min: 5, max: 12 },
    strategyId: 11
  },

  // NCAAB SYSTEMS (Additional to shared NBA systems above)
  {
    id: 2,
    name: "Max EV Boost (NCAAB)",
    status: "live",
    description: "XGBoost-powered live total analysis using KenPom efficiency ratings",
    sports: ["basketball_ncaab"],
    difficulty: "MEDIUM",
    evRange: { min: 10, max: 20 },
    performance: {
      winRate: 60.0,
      roi: 14.5,
      alerts: 30,
      games: 675
    },
    backend: "backend/ml/ncaab_regression_analyzer.py",
    apiEndpoint: "/api/strategies/regression-to-mean/analyze"
  },

  // NHL SYSTEMS
  {
    id: 6,
    name: "Goalie Pull Alert",
    status: "proven",
    description: "Bet team totals over when trailing teams pull their goalie early",
    sports: ["icehockey_nhl"],
    difficulty: "EASY",
    evRange: { min: 5, max: 10 },
    performance: {
      winRate: 80.4,
      roi: 6.8,
      games: 467
    },
    backend: "backend/strategies/Goalie_Pull_Predictor.py",
    strategyId: 6
  },

  // NFL SYSTEMS
  {
    id: 112,
    name: "Weather-Driven Live Totals",
    status: "pending",
    description: "Bet unders when weather deteriorates during outdoor games",
    sports: ["americanfootball_nfl", "baseball_mlb"],
    difficulty: "MEDIUM",
    evRange: { min: 10, max: 20 },
    backend: "backend/strategies/weather_strategy.py",
    strategyId: 12
  },
  {
    id: 21,
    name: "Key Numbers Strategy",
    status: "pending",
    description: "Analyzes NFL spreads for key number opportunities (3, 7, 10)",
    sports: ["americanfootball_nfl"],
    difficulty: "EASY",
    evRange: { min: 10, max: 18 },
    backend: "backend/strategies/key_numbers.py",
    strategyId: 21
  },

  // MULTI-SPORT / UNIVERSAL SYSTEMS
  {
    id: 115,
    name: "Line Movement Arbitrage",
    status: "pending",
    description: "Capitalize on line movement discrepancies between bookmakers",
    sports: ["multi-sport"],
    difficulty: "MEDIUM",
    evRange: { min: 2, max: 8 },
    strategyId: 15
  },
  {
    id: 116,
    name: "Middle Opportunity Detection",
    status: "pending",
    description: "Identify and exploit middle betting opportunities across multiple bookmakers",
    sports: ["multi-sport"],
    difficulty: "EASY",
    evRange: { min: 5, max: 15 },
    strategyId: 16
  },
  {
    id: 117,
    name: "Sharp Money Tracking",
    status: "pending",
    description: "Follow professional betting patterns by monitoring line movements without corresponding public betting trends",
    sports: ["multi-sport"],
    difficulty: "HARD",
    evRange: { min: 4, max: 10 },
    backend: "backend/strategies/sharp_money_tracker.py",
    strategyId: 17
  },
  {
    id: 118,
    name: "CLV Tracker (Closing Line Value)",
    status: "pending",
    description: "Tracks whether user bets beat the closing line - the most important metric for long-term profitability",
    sports: ["multi-sport"],
    difficulty: "MEDIUM",
    evRange: { min: 4, max: 10 },
    backend: "backend/strategies/clv_tracker.py",
    strategyId: 18
  },
  {
    id: 119,
    name: "Home/Away Splits Strategy",
    status: "pending",
    description: "Identifies betting value based on team performance differentials between home and away games",
    sports: ["multi-sport"],
    difficulty: "MEDIUM",
    evRange: { min: 6, max: 14 },
    backend: "backend/strategies/home_away_splits.py",
    strategyId: 19
  },
  {
    id: 120,
    name: "Divisional Rivalries Strategy",
    status: "pending",
    description: "Identifies betting value in division games based on historical trends and rivalry dynamics",
    sports: ["multi-sport"],
    difficulty: "MEDIUM",
    evRange: { min: 4, max: 10 },
    backend: "backend/strategies/divisional_rivalries.py",
    strategyId: 20
  },
  {
    id: 122,
    name: "Low-Hold Opportunities",
    status: "pending",
    description: "Identifies betting opportunities with low bookmaker hold (vig)",
    sports: ["multi-sport"],
    difficulty: "EASY",
    evRange: { min: 2, max: 5 },
    backend: "backend/strategies/low_hold.py",
    strategyId: 22
  }
];

/**
 * Get systems applicable to a specific sport
 * @param sportKey - The sport key from the game (e.g., 'basketball_nba', 'icehockey_nhl')
 * @returns Array of systems for that sport
 */
export const getSystemsBySport = (sportKey: string): AdvancedSystem[] => {
  return ADVANCED_SYSTEMS.filter(system =>
    system.sports.includes(sportKey) || system.sports.includes('multi-sport')
  ).sort((a, b) => {
    // Sort order: live > proven > active > pending
    const statusOrder = { live: 0, proven: 1, active: 2, pending: 3 };
    return statusOrder[a.status] - statusOrder[b.status];
  });
};

/**
 * Get count of active systems for a sport
 * @param sportKey - The sport key from the game
 * @returns Number of live/proven/active systems
 */
export const getActiveSystemsCount = (sportKey: string): number => {
  return ADVANCED_SYSTEMS.filter(system =>
    (system.sports.includes(sportKey) || system.sports.includes('multi-sport')) &&
    (system.status === 'live' || system.status === 'proven' || system.status === 'active')
  ).length;
};

/**
 * Get system by ID
 * @param id - System ID
 * @returns System or undefined
 */
export const getSystemById = (id: number): AdvancedSystem | undefined => {
  return ADVANCED_SYSTEMS.find(system => system.id === id);
};
