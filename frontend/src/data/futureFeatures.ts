/**
 * Future Features & ML Enhancement Data
 *
 * Complete data structure for the ML Advantage showcase page.
 * Includes all 25 betting strategies with current vs ML-enhanced metrics,
 * model comparisons, and implementation timeline.
 */

export interface StrategyEnhancement {
  id: number;
  name: string;
  description: string;
  category: 'situational' | 'live' | 'market';
  current: {
    method: string;
    win_rate: number;
    roi: number;
    sample_size: number;
    data_sources: string[];
  };
  enhanced: {
    ml_models: string[];
    additional_features: string[];
    win_rate: number;
    roi: number;
    improvement: {
      win_rate_pct: number;
      roi_pct: number;
      false_positives_reduction: number;
    };
  };
  features_added: string[];
  status: 'live' | 'beta' | 'q1_2025' | 'q2_2025';
  impact_score: 'game_changer' | 'high' | 'medium' | 'low';
  launch_quarter: string;
}

export interface ModelComparison {
  name: string;
  type: 'traditional' | 'basic' | 'ml_enhanced';
  features_count: number;
  adaptability: string;
  context_awareness: string;
  confidence_levels: boolean;
  self_improving: boolean;
  typical_roi: number;
  win_rate: number;
  description: string;
}

export interface FeatureRelease {
  quarter: string;
  phase: string;
  features: string[];
  expected_impact: string;
  status: 'completed' | 'in_progress' | 'planned';
  completion_percent?: number;
}

export interface DataEnhancement {
  name: string;
  current_state: string;
  enhanced_state: string;
  impact: string;
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  eta: string;
}

// ============================================================================
// STRATEGY ENHANCEMENTS DATA
// ============================================================================

export const STRATEGY_ENHANCEMENTS: StrategyEnhancement[] = [
  // SITUATIONAL STRATEGIES
  {
    id: 1,
    name: "Back-to-Back vs Rested Teams",
    description: "Targets teams on back-to-back games facing well-rested opponents",
    category: 'situational',
    current: {
      method: "Fixed multiplier: rest_diff × 1.5 points",
      win_rate: 0.572,
      roi: 0.083,
      sample_size: 847,
      data_sources: ["Schedule data", "Basic rest days"]
    },
    enhanced: {
      ml_models: ["XGBoost Spreads", "Random Forest Totals", "Ensemble"],
      additional_features: [
        "Fatigue Index (travel, altitude, OT, minutes)",
        "Rolling performance stats (L5, L10, L15)",
        "Opponent-adjusted metrics",
        "Historical B2B performance by team"
      ],
      win_rate: 0.607,
      roi: 0.128,
      improvement: {
        win_rate_pct: 6.1,
        roi_pct: 54.2,
        false_positives_reduction: 28
      }
    },
    features_added: [
      "Cumulative fatigue scoring",
      "Travel distance tracking",
      "Elevation change impact",
      "Minutes played tracking",
      "Team-specific B2B patterns"
    ],
    status: 'q1_2025',
    impact_score: 'game_changer',
    launch_quarter: 'Q1 2025'
  },
  {
    id: 2,
    name: "3-in-4 Nights Schedule Crunch",
    description: "Identifies teams playing 3 games in 4 nights",
    category: 'situational',
    current: {
      method: "Binary flag: 3-in-4 = bet against",
      win_rate: 0.564,
      roi: 0.092,
      sample_size: 342,
      data_sources: ["Schedule data"]
    },
    enhanced: {
      ml_models: ["LightGBM Spreads", "Linear Regression Totals"],
      additional_features: [
        "Game position in stretch (1st, 2nd, 3rd)",
        "Travel miles between games",
        "Home vs away distribution",
        "Roster depth scoring"
      ],
      win_rate: 0.596,
      roi: 0.134,
      improvement: {
        win_rate_pct: 5.7,
        roi_pct: 45.7,
        false_positives_reduction: 22
      }
    },
    features_added: [
      "Sequential fatigue modeling",
      "Rotation pattern analysis",
      "Injury likelihood scoring"
    ],
    status: 'q1_2025',
    impact_score: 'high',
    launch_quarter: 'Q1 2025'
  },
  {
    id: 3,
    name: "Post All-Star Break Adjustments",
    description: "Teams adjusting to trades and roster changes after All-Star break",
    category: 'situational',
    current: {
      method: "Fixed adjustment: -2 points for new roster",
      win_rate: 0.481,
      roi: -0.038,
      sample_size: 156,
      data_sources: ["Trade data", "Roster changes"]
    },
    enhanced: {
      ml_models: ["Ensemble", "XGBoost"],
      additional_features: [
        "Player integration time modeling",
        "Chemistry metrics (assist rates)",
        "Playing time distribution changes",
        "Coaching adjustment period"
      ],
      win_rate: 0.553,
      roi: 0.067,
      improvement: {
        win_rate_pct: 15.0,
        roi_pct: 276.3,
        false_positives_reduction: 45
      }
    },
    features_added: [
      "Trade impact quantification",
      "Chemistry degradation curves",
      "Integration timeline models"
    ],
    status: 'q2_2025',
    impact_score: 'medium',
    launch_quarter: 'Q2 2025'
  },
  {
    id: 4,
    name: "Playoff Race Intensity",
    description: "Teams fighting for playoff spots play harder in final stretch",
    category: 'situational',
    current: {
      method: "Manual playoff race classification",
      win_rate: 0.537,
      roi: 0.041,
      sample_size: 289,
      data_sources: ["Standings", "Games remaining"]
    },
    enhanced: {
      ml_models: ["Logistic Regression", "Random Forest"],
      additional_features: [
        "Playoff probability calculations",
        "Must-win game identification",
        "Opponent incentive alignment",
        "Historical clutch performance"
      ],
      win_rate: 0.581,
      roi: 0.112,
      improvement: {
        win_rate_pct: 8.2,
        roi_pct: 173.2,
        false_positives_reduction: 35
      }
    },
    features_added: [
      "Desperation index",
      "Win impact on playoff odds",
      "Rest vs win trade-off modeling"
    ],
    status: 'q2_2025',
    impact_score: 'high',
    launch_quarter: 'Q2 2025'
  },
  {
    id: 5,
    name: "Revenge Game Motivations",
    description: "Teams facing recent playoff eliminators or embarrassing losses",
    category: 'situational',
    current: {
      method: "Manual identification of revenge spots",
      win_rate: 0.492,
      roi: -0.016,
      sample_size: 124,
      data_sources: ["Historical matchups"]
    },
    enhanced: {
      ml_models: ["XGBoost", "LightGBM"],
      additional_features: [
        "Loss severity scoring (blowout vs close)",
        "Time since last matchup",
        "Playoff context weighting",
        "Media attention metrics"
      ],
      win_rate: 0.547,
      roi: 0.054,
      improvement: {
        win_rate_pct: 11.2,
        roi_pct: 437.5,
        false_positives_reduction: 40
      }
    },
    features_added: [
      "Motivation quantification",
      "Recency-weighted revenge scoring",
      "Context importance modeling"
    ],
    status: 'q2_2025',
    impact_score: 'low',
    launch_quarter: 'Q2 2025'
  },

  // LIVE BETTING STRATEGIES
  {
    id: 6,
    name: "Favorite Comeback (After Hot Start)",
    description: "Favorites trailing underdogs who shot unusually well early",
    category: 'live',
    current: {
      method: "5-factor regression score (0-20 points)",
      win_rate: 0.603,
      roi: 0.124,
      sample_size: 412,
      data_sources: ["Live shooting data", "Talent ratings"]
    },
    enhanced: {
      ml_models: ["XGBoost Live", "Random Forest", "Ensemble"],
      additional_features: [
        "Real-time fatigue monitoring",
        "Hot hand persistence modeling",
        "Defensive adjustment detection",
        "Rotation pattern changes",
        "Momentum indicators (run detection)"
      ],
      win_rate: 0.647,
      roi: 0.183,
      improvement: {
        win_rate_pct: 7.3,
        roi_pct: 47.6,
        false_positives_reduction: 25
      }
    },
    features_added: [
      "Shooting regression curves by player",
      "Defensive scheme adjustment detection",
      "Timeout impact modeling",
      "Foul trouble cascades"
    ],
    status: 'live',
    impact_score: 'game_changer',
    launch_quarter: 'Q4 2024'
  },
  {
    id: 7,
    name: "Quarter Momentum Reversal",
    description: "Teams that dominated a quarter often regress next quarter",
    category: 'live',
    current: {
      method: "Historical reversal rates by period",
      win_rate: 0.553,
      roi: 0.067,
      sample_size: 1847,
      data_sources: ["Quarter scoring data"]
    },
    enhanced: {
      ml_models: ["LightGBM Live", "Linear Regression"],
      additional_features: [
        "Scoring margin severity",
        "Possession efficiency trends",
        "Turnover rate changes",
        "Bench impact scoring",
        "Coaching adjustment signals"
      ],
      win_rate: 0.591,
      roi: 0.123,
      improvement: {
        win_rate_pct: 6.9,
        roi_pct: 83.6,
        false_positives_reduction: 30
      }
    },
    features_added: [
      "Momentum intensity scoring",
      "Mean reversion probability",
      "Rotation pattern detection"
    ],
    status: 'beta',
    impact_score: 'game_changer',
    launch_quarter: 'Q1 2025'
  },
  {
    id: 8,
    name: "Halftime Adjustments",
    description: "Predict second half performance based on first half patterns",
    category: 'live',
    current: {
      method: "Simple mean reversion to pregame total",
      win_rate: 0.523,
      roi: 0.028,
      sample_size: 2341,
      data_sources: ["Halftime box scores"]
    },
    enhanced: {
      ml_models: ["XGBoost Halftime", "Ensemble"],
      additional_features: [
        "Coach-specific adjustment patterns",
        "Foul trouble impact",
        "Bench production differential",
        "Three-point regression analysis",
        "Pace sustainability metrics"
      ],
      win_rate: 0.568,
      roi: 0.096,
      improvement: {
        win_rate_pct: 8.6,
        roi_pct: 242.9,
        false_positives_reduction: 35
      }
    },
    features_added: [
      "Coach adjustment profiles",
      "Player-specific 2H patterns",
      "Halftime speech sentiment (media)"
    ],
    status: 'q1_2025',
    impact_score: 'high',
    launch_quarter: 'Q1 2025'
  },
  {
    id: 9,
    name: "Garbage Time Detection",
    description: "Avoid bets during blowouts when starters rest",
    category: 'live',
    current: {
      method: "Fixed threshold: 20+ point lead in Q4",
      win_rate: 0.447,
      roi: -0.106,
      sample_size: 634,
      data_sources: ["Live scores", "Game clock"]
    },
    enhanced: {
      ml_models: ["Logistic Classifier", "Random Forest"],
      additional_features: [
        "Coach pull-starters tendency",
        "Time remaining + point differential curves",
        "Team competitiveness profiles",
        "Bench scoring volatility",
        "Comeback probability by era"
      ],
      win_rate: 0.512,
      roi: 0.014,
      improvement: {
        win_rate_pct: 14.5,
        roi_pct: 113.2,
        false_positives_reduction: 52
      }
    },
    features_added: [
      "Garbage time probability curves",
      "Coach substitution pattern recognition",
      "Bench unit efficiency scoring"
    ],
    status: 'q1_2025',
    impact_score: 'medium',
    launch_quarter: 'Q1 2025'
  },
  {
    id: 10,
    name: "Late Game Foul Situations",
    description: "Intentional fouling impacts pace and scoring in final minutes",
    category: 'live',
    current: {
      method: "Manual identification when team down 6-10 pts",
      win_rate: 0.508,
      roi: 0.006,
      sample_size: 423,
      data_sources: ["Live game state"]
    },
    enhanced: {
      ml_models: ["XGBoost Live", "Linear Regression"],
      additional_features: [
        "Free throw shooting percentages",
        "Intentional foul likelihood by coach",
        "Possession count remaining",
        "Timeout availability",
        "Historical team behavior patterns"
      ],
      win_rate: 0.559,
      roi: 0.078,
      improvement: {
        win_rate_pct: 10.0,
        roi_pct: 1200.0,
        false_positives_reduction: 38
      }
    },
    features_added: [
      "Foul strategy likelihood models",
      "Expected possessions remaining",
      "FT% impact on strategy choice"
    ],
    status: 'q2_2025',
    impact_score: 'medium',
    launch_quarter: 'Q2 2025'
  },
  {
    id: 11,
    name: "End-of-Quarter 2-for-1 Situations",
    description: "Teams rushing shots to get extra possession before period ends",
    category: 'live',
    current: {
      method: "Manual detection at 35-40 seconds remaining",
      win_rate: 0.531,
      roi: 0.042,
      sample_size: 867,
      data_sources: ["Shot clock", "Game clock"]
    },
    enhanced: {
      ml_models: ["LightGBM Live", "Ensemble"],
      additional_features: [
        "Team 2-for-1 aggressiveness rates",
        "Shot quality impact (rushed vs normal)",
        "Score differential influence",
        "Coach tendency profiles",
        "Expected points per rushed possession"
      ],
      win_rate: 0.574,
      roi: 0.098,
      improvement: {
        win_rate_pct: 8.1,
        roi_pct: 133.3,
        false_positives_reduction: 32
      }
    },
    features_added: [
      "2-for-1 execution rate by team",
      "Shot quality degradation models",
      "Defensive awareness scoring"
    ],
    status: 'q2_2025',
    impact_score: 'medium',
    launch_quarter: 'Q2 2025'
  },
  {
    id: 12,
    name: "Bonus Penalty Situations (NBA)",
    description: "Team in bonus gets more free throws, impacts quarter totals",
    category: 'live',
    current: {
      method: "Simple bonus flag detection",
      win_rate: 0.518,
      roi: 0.026,
      sample_size: 1523,
      data_sources: ["Live foul counts"]
    },
    enhanced: {
      ml_models: ["XGBoost Live", "Random Forest"],
      additional_features: [
        "Foul-to-give strategy likelihood",
        "Free throw rate by player on court",
        "Paint attack rate adjustments",
        "Referee tendencies (foul rate by crew)",
        "Time remaining in period"
      ],
      win_rate: 0.562,
      roi: 0.084,
      improvement: {
        win_rate_pct: 8.5,
        roi_pct: 223.1,
        false_positives_reduction: 29
      }
    },
    features_added: [
      "Referee crew foul rate profiles",
      "Paint attack strategy adjustments",
      "FT opportunity expectation models"
    ],
    status: 'q2_2025',
    impact_score: 'high',
    launch_quarter: 'Q2 2025'
  },

  // NHL-SPECIFIC LIVE STRATEGIES
  {
    id: 13,
    name: "Goalie Pull Timing (NHL)",
    description: "Empty net situations create high variance scoring opportunities",
    category: 'live',
    current: {
      method: "Historical 6v5 scoring rates",
      win_rate: 0.804,
      roi: 0.324,
      sample_size: 89,
      data_sources: ["Live game state", "Goalie pulled flag"]
    },
    enhanced: {
      ml_models: ["NHL XGBoost Live", "Ensemble"],
      additional_features: [
        "Team 6v5 offensive efficiency",
        "Empty net defense efficiency",
        "Faceoff win probability",
        "Zone entry success rates",
        "Goalie pull timing by coach"
      ],
      win_rate: 0.843,
      roi: 0.412,
      improvement: {
        win_rate_pct: 4.9,
        roi_pct: 27.2,
        false_positives_reduction: 18
      }
    },
    features_added: [
      "6v5 zone entry success by team",
      "Empty net shooting accuracy",
      "Opponent empty net defense rating",
      "Coach aggressiveness profiles"
    ],
    status: 'live',
    impact_score: 'game_changer',
    launch_quarter: 'Q4 2024'
  },
  {
    id: 14,
    name: "Power Play Opportunities (NHL)",
    description: "Power plays significantly impact period totals",
    category: 'live',
    current: {
      method: "League average PP scoring rate",
      win_rate: 0.556,
      roi: 0.072,
      sample_size: 2134,
      data_sources: ["Live penalty data"]
    },
    enhanced: {
      ml_models: ["NHL LightGBM", "Random Forest"],
      additional_features: [
        "Team-specific PP efficiency",
        "PK efficiency",
        "PP unit on ice vs bench",
        "Time remaining in period",
        "5v3 vs 5v4 distinction",
        "Ref crew penalty tendency"
      ],
      win_rate: 0.598,
      roi: 0.136,
      improvement: {
        win_rate_pct: 7.6,
        roi_pct: 88.9,
        false_positives_reduction: 26
      }
    },
    features_added: [
      "Unit-specific PP/PK ratings",
      "Penalty kill aggressiveness",
      "Shorthanded goal likelihood"
    ],
    status: 'q1_2025',
    impact_score: 'high',
    launch_quarter: 'Q1 2025'
  },
  {
    id: 15,
    name: "Delayed Penalty Situations (NHL)",
    description: "6-on-5 advantage during delayed penalties",
    category: 'live',
    current: {
      method: "Simple delayed penalty flag",
      win_rate: 0.523,
      roi: 0.036,
      sample_size: 456,
      data_sources: ["Live penalty flags"]
    },
    enhanced: {
      ml_models: ["NHL XGBoost", "Linear Regression"],
      additional_features: [
        "Extra attacker efficiency by team",
        "Zone at delayed penalty start",
        "Time of possession before whistle",
        "Shot quality in 6v5 situations"
      ],
      win_rate: 0.571,
      roi: 0.094,
      improvement: {
        win_rate_pct: 9.2,
        roi_pct: 161.1,
        false_positives_reduction: 33
      }
    },
    features_added: [
      "Possession duration models",
      "Zone-based scoring probabilities",
      "Whistle timing prediction"
    ],
    status: 'q2_2025',
    impact_score: 'medium',
    launch_quarter: 'Q2 2025'
  },

  // MARKET INEFFICIENCY STRATEGIES
  {
    id: 16,
    name: "Steam Moves Detection",
    description: "Sharp money causing rapid line movements",
    category: 'market',
    current: {
      method: "Line movement threshold: 1+ point in 10 min",
      win_rate: 0.542,
      roi: 0.054,
      sample_size: 1247,
      data_sources: ["Odds history API"]
    },
    enhanced: {
      ml_models: ["Ensemble", "Logistic Regression"],
      additional_features: [
        "Movement velocity (points per minute)",
        "Number of books moving simultaneously",
        "Market leader identification",
        "Reverse line movement detection",
        "Volume-weighted movement"
      ],
      win_rate: 0.587,
      roi: 0.118,
      improvement: {
        win_rate_pct: 8.3,
        roi_pct: 118.5,
        false_positives_reduction: 36
      }
    },
    features_added: [
      "Sharp book identification",
      "Synchronized movement detection",
      "Injury news correlation"
    ],
    status: 'q1_2025',
    impact_score: 'game_changer',
    launch_quarter: 'Q1 2025'
  },
  {
    id: 17,
    name: "Reverse Line Movement",
    description: "Line moving opposite to public betting percentages",
    category: 'market',
    current: {
      method: "Manual comparison of line + public%",
      win_rate: 0.548,
      roi: 0.062,
      sample_size: 834,
      data_sources: ["Public betting %", "Line history"]
    },
    enhanced: {
      ml_models: ["XGBoost", "Random Forest"],
      additional_features: [
        "Magnitude of public/sharp disagreement",
        "Historical RLM success rate by sport",
        "Book-specific RLM patterns",
        "Time until game (recency)",
        "Ticket count vs dollar amount split"
      ],
      win_rate: 0.593,
      roi: 0.127,
      improvement: {
        win_rate_pct: 8.2,
        roi_pct: 104.8,
        false_positives_reduction: 31
      }
    },
    features_added: [
      "Sharp vs square money quantification",
      "RLM strength scoring",
      "Book behavior classification"
    ],
    status: 'q1_2025',
    impact_score: 'game_changer',
    launch_quarter: 'Q1 2025'
  },
  {
    id: 18,
    name: "Market Maker Follows",
    description: "Following books known for sharp, accurate lines",
    category: 'market',
    current: {
      method: "Manual sharp book identification",
      win_rate: 0.534,
      roi: 0.046,
      sample_size: 2145,
      data_sources: ["Multi-book odds comparison"]
    },
    enhanced: {
      ml_models: ["Logistic Regression", "LightGBM"],
      additional_features: [
        "Historical book accuracy by sport/bet type",
        "Book line-setting speed (first mover)",
        "Limit size by book",
        "CLV tracking by book",
        "Book correlations and follower detection"
      ],
      win_rate: 0.571,
      roi: 0.094,
      improvement: {
        win_rate_pct: 6.9,
        roi_pct: 104.3,
        false_positives_reduction: 27
      }
    },
    features_added: [
      "Book sharpness scoring",
      "Leader-follower relationship mapping",
      "Book-specific win rate tracking"
    ],
    status: 'q1_2025',
    impact_score: 'high',
    launch_quarter: 'Q1 2025'
  },
  {
    id: 19,
    name: "Closing Line Value (CLV) Tracking",
    description: "Measure if our predictions beat closing lines over time",
    category: 'market',
    current: {
      method: "Manual post-game CLV calculation",
      win_rate: 0.528,
      roi: 0.038,
      sample_size: 3421,
      data_sources: ["Opening + closing odds"]
    },
    enhanced: {
      ml_models: ["All models with CLV feedback loop"],
      additional_features: [
        "Real-time CLV prediction",
        "Expected line movement models",
        "Optimal betting timing",
        "CLV by confidence level tracking",
        "Model CLV leaderboard"
      ],
      win_rate: 0.574,
      roi: 0.102,
      improvement: {
        win_rate_pct: 8.7,
        roi_pct: 168.4,
        false_positives_reduction: 29
      }
    },
    features_added: [
      "Closing line prediction models",
      "Timing alpha quantification",
      "CLV-based model reweighting"
    ],
    status: 'q1_2025',
    impact_score: 'game_changer',
    launch_quarter: 'Q1 2025'
  },
  {
    id: 20,
    name: "Middle & Arbitrage Scanner",
    description: "Finds risk-free or low-risk middle opportunities",
    category: 'market',
    current: {
      method: "Multi-book comparison, manual identification",
      win_rate: 0.892,
      roi: 0.047,
      sample_size: 234,
      data_sources: ["All bookmaker odds"]
    },
    enhanced: {
      ml_models: ["Probability models for middle hit rate"],
      additional_features: [
        "Middle width optimization",
        "Sport-specific middle hit rates",
        "Kelly criterion for middle sizing",
        "Hedge timing optimization",
        "Correlated parlay detection"
      ],
      win_rate: 0.918,
      roi: 0.073,
      improvement: {
        win_rate_pct: 2.9,
        roi_pct: 55.3,
        false_positives_reduction: 15
      }
    },
    features_added: [
      "Middle probability curves",
      "Optimal middle width calculation",
      "Real-time opportunity alerts"
    ],
    status: 'live',
    impact_score: 'high',
    launch_quarter: 'Q4 2024'
  },

  // ADVANCED MULTI-SPORT STRATEGIES
  {
    id: 21,
    name: "Pace Deviation Detector",
    description: "Identifies games likely to play faster/slower than expected",
    category: 'situational',
    current: {
      method: "Simple geometric mean of team pace",
      win_rate: 0.519,
      roi: 0.028,
      sample_size: 2847,
      data_sources: ["Team pace stats"]
    },
    enhanced: {
      ml_models: ["Random Forest", "XGBoost", "Linear Regression"],
      additional_features: [
        "Opponent-adjusted pace",
        "Home vs away pace splits",
        "Referee pace impact",
        "Injury impact on pace",
        "Recent pace trends (L5, L10)"
      ],
      win_rate: 0.564,
      roi: 0.088,
      improvement: {
        win_rate_pct: 8.7,
        roi_pct: 214.3,
        false_positives_reduction: 31
      }
    },
    features_added: [
      "Referee-specific pace factors",
      "Matchup-based pace adjustments",
      "Injury-adjusted pace modeling"
    ],
    status: 'q1_2025',
    impact_score: 'high',
    launch_quarter: 'Q1 2025'
  },
  {
    id: 22,
    name: "Injury Impact Quantification",
    description: "Calculates point spread impact of player injuries",
    category: 'situational',
    current: {
      method: "Binary: key player out = avoid bet",
      win_rate: 0.501,
      roi: 0.002,
      sample_size: 1834,
      data_sources: ["Injury reports"]
    },
    enhanced: {
      ml_models: ["XGBoost", "LightGBM", "Ensemble"],
      additional_features: [
        "Player replacement value",
        "Historical team performance without player",
        "Position-specific impact curves",
        "Lineup chemistry adjustments",
        "Injury severity classification"
      ],
      win_rate: 0.557,
      roi: 0.074,
      improvement: {
        win_rate_pct: 11.2,
        roi_pct: 3600.0,
        false_positives_reduction: 42
      }
    },
    features_added: [
      "Player impact database (RAPM, BPM, etc.)",
      "Replacement player projections",
      "Team depth chart analysis"
    ],
    status: 'q1_2025',
    impact_score: 'game_changer',
    launch_quarter: 'Q1 2025'
  },
  {
    id: 23,
    name: "Weather Impact (NFL/MLB)",
    description: "Wind, rain, snow impact totals and spreads",
    category: 'situational',
    current: {
      method: "Fixed adjustment: high wind = -3 points",
      win_rate: 0.531,
      roi: 0.042,
      sample_size: 447,
      data_sources: ["Weather API"]
    },
    enhanced: {
      ml_models: ["Random Forest", "Linear Regression"],
      additional_features: [
        "Team-specific weather performance",
        "Passing vs rushing impact differences",
        "Stadium configuration (open/dome/retractable)",
        "Temperature impact on ball flight",
        "Precipitation intensity levels"
      ],
      win_rate: 0.579,
      roi: 0.108,
      improvement: {
        win_rate_pct: 9.0,
        roi_pct: 157.1,
        false_positives_reduction: 28
      }
    },
    features_added: [
      "Sport-specific weather models",
      "Stadium microclimate factors",
      "Team weather history database"
    ],
    status: 'q2_2025',
    impact_score: 'medium',
    launch_quarter: 'Q2 2025'
  },
  {
    id: 24,
    name: "Umpire/Referee Tendencies",
    description: "Officials impact totals through foul/strike zone variations",
    category: 'situational',
    current: {
      method: "Basic official assignment tracking",
      win_rate: 0.514,
      roi: 0.018,
      sample_size: 1647,
      data_sources: ["Official assignments"]
    },
    enhanced: {
      ml_models: ["LightGBM", "Linear Regression"],
      additional_features: [
        "Official-specific foul/call rates",
        "Strike zone width/height (MLB)",
        "Penalty tendency (NFL/NHL)",
        "Pace impact by official",
        "Home vs away bias quantification"
      ],
      win_rate: 0.561,
      roi: 0.082,
      improvement: {
        win_rate_pct: 9.1,
        roi_pct: 355.6,
        false_positives_reduction: 34
      }
    },
    features_added: [
      "Official database by sport",
      "Call tendency profiles",
      "Matchup-specific adjustments"
    ],
    status: 'q2_2025',
    impact_score: 'medium',
    launch_quarter: 'Q2 2025'
  },
  {
    id: 25,
    name: "Public Fade System",
    description: "Bet against heavily bet public teams",
    category: 'market',
    current: {
      method: "Fade teams with 65%+ public betting",
      win_rate: 0.527,
      roi: 0.034,
      sample_size: 2934,
      data_sources: ["Public betting percentages"]
    },
    enhanced: {
      ml_models: ["Logistic Regression", "Random Forest"],
      additional_features: [
        "Public betting % by bet type",
        "Ticket count vs money percentages",
        "Historical fade success by team",
        "Line movement vs public% correlation",
        "Recency bias detection"
      ],
      win_rate: 0.568,
      roi: 0.096,
      improvement: {
        win_rate_pct: 7.8,
        roi_pct: 182.4,
        false_positives_reduction: 29
      }
    },
    features_added: [
      "Sharp vs square money identification",
      "Team-specific public bias",
      "Optimal fade threshold by sport"
    ],
    status: 'q1_2025',
    impact_score: 'high',
    launch_quarter: 'Q1 2025'
  }
];

// ============================================================================
// MODEL COMPARISON DATA
// ============================================================================

export const MODEL_COMPARISONS: ModelComparison[] = [
  {
    name: "ELO Rating System",
    type: 'traditional',
    features_count: 1,
    adaptability: "Fixed formulas, manual updates",
    context_awareness: "None (only win/loss history)",
    confidence_levels: false,
    self_improving: false,
    typical_roi: 0.02,
    win_rate: 0.51,
    description: "Single rating number per team, updates after each game based on expected outcome"
  },
  {
    name: "Power Rankings",
    type: 'traditional',
    features_count: 3,
    adaptability: "Expert-based, weekly manual adjustments",
    context_awareness: "Low (wins, losses, point differential)",
    confidence_levels: false,
    self_improving: false,
    typical_roi: 0.01,
    win_rate: 0.505,
    description: "Ordered list using simple metrics like win%, point differential, strength of schedule"
  },
  {
    name: "KenPom Ratings",
    type: 'traditional',
    features_count: 5,
    adaptability: "Fixed efficiency formulas",
    context_awareness: "Medium (pace, efficiency, opponent adjustments)",
    confidence_levels: false,
    self_improving: false,
    typical_roi: 0.035,
    win_rate: 0.52,
    description: "Efficiency-based system (points per 100 possessions), adjusts for tempo and opponents"
  },
  {
    name: "Pythagorean Win%",
    type: 'traditional',
    features_count: 2,
    adaptability: "Static formula, no updates",
    context_awareness: "None (only points scored/allowed)",
    confidence_levels: false,
    self_improving: false,
    typical_roi: 0.015,
    win_rate: 0.508,
    description: "Predicts win% based on points scored vs allowed using fixed exponent formula"
  },
  {
    name: "Current System (Pace-Based)",
    type: 'basic',
    features_count: 12,
    adaptability: "Weekly data refresh, fixed model",
    context_awareness: "Medium (pace, efficiency, rest, home court)",
    confidence_levels: true,
    self_improving: false,
    typical_roi: 0.083,
    win_rate: 0.532,
    description: "Uses pace-adjusted efficiency ratings with rest day and home court adjustments"
  },
  {
    name: "ML-Enhanced System",
    type: 'ml_enhanced',
    features_count: 54,
    adaptability: "Autonomous weekly retraining with new results",
    context_awareness: "High (20-54 features per sport including fatigue, matchups, trends)",
    confidence_levels: true,
    self_improving: true,
    typical_roi: 0.12,
    win_rate: 0.56,
    description: "Ensemble of 6 ML models per sport with autonomous learning and strategy integration"
  }
];

// ============================================================================
// DATA ENHANCEMENTS
// ============================================================================

export const DATA_ENHANCEMENTS: DataEnhancement[] = [
  {
    name: "Rolling Performance Stats",
    current_state: "Season averages only",
    enhanced_state: "Last 5, 10, 15 game averages with trend detection",
    impact: "+2-3% win rate, better capture of recent form",
    priority: 'P0',
    eta: 'Week 1'
  },
  {
    name: "Fatigue Index",
    current_state: "Binary rest days (B2B or not)",
    enhanced_state: "Cumulative score: games, travel, altitude, OT, minutes",
    impact: "+1.5-2% win rate on schedule-based strategies",
    priority: 'P0',
    eta: 'Week 2'
  },
  {
    name: "Injury Impact Quantification",
    current_state: "Binary flag (player out or not)",
    enhanced_state: "Player value metrics, replacement projections",
    impact: "+3-4% win rate, -40% false positives",
    priority: 'P1',
    eta: 'Week 3'
  },
  {
    name: "Opponent-Adjusted Metrics",
    current_state: "Raw season averages",
    enhanced_state: "Performance vs top/bottom tier opponents",
    impact: "+1-2% win rate, better strength of schedule",
    priority: 'P1',
    eta: 'Week 4'
  },
  {
    name: "Probability Calibration",
    current_state: "Raw model probabilities",
    enhanced_state: "Isotonic regression calibrated confidence",
    impact: "HIGH confidence: 47% → 60%+ win rate",
    priority: 'P0',
    eta: 'Week 2'
  },
  {
    name: "Quote-Age Tracking",
    current_state: "No tracking of odds freshness",
    enhanced_state: "Block alerts if odds >10 seconds old",
    impact: "-15-20% false edges, prevents stale line bets",
    priority: 'P0',
    eta: 'Week 1'
  },
  {
    name: "Two-Book Confirmation",
    current_state: "Alert on single book edge",
    enhanced_state: "Require 2+ books with edge before alerting",
    impact: "-30% false positives, higher quality alerts",
    priority: 'P0',
    eta: 'Week 1'
  },
  {
    name: "CLV Tracking",
    current_state: "No closing line tracking",
    enhanced_state: "Real-time CLV, model CLV leaderboard",
    impact: "Proves timing alpha, +2-3% ROI improvement",
    priority: 'P1',
    eta: 'Week 3'
  }
];

// ============================================================================
// IMPLEMENTATION ROADMAP
// ============================================================================

export const ROADMAP: FeatureRelease[] = [
  {
    quarter: "Q4 2024",
    phase: "Foundation (Complete)",
    features: [
      "25 betting strategies (situational, live, market)",
      "87 ML models across 5 sports (NBA, NCAAB, NHL, NFL, NCAAF)",
      "Weekly autonomous retraining (Mondays 4-9am)",
      "Daily predictions (9-11am CST)",
      "Live betting alerts (6-11pm CST, every 5 min)",
      "Multi-sport edge scanner",
      "Basic confidence levels (HIGH/MEDIUM/LOW)"
    ],
    expected_impact: "8.3% average ROI, 53.2% win rate",
    status: 'completed',
    completion_percent: 100
  },
  {
    quarter: "Q1 2025",
    phase: "Quick Wins",
    features: [
      "Rolling stats integration (L5, L10, L15 with trends)",
      "Probability calibration (isotonic regression)",
      "Quote-age guards (block stale odds >10s)",
      "Two-book confirmation (require 2+ books with edge)",
      "Fatigue index (travel, altitude, OT, minutes)",
      "ML-enhanced B2B strategy with fatigue scoring",
      "CLV tracking system with model feedback",
      "Steam move & reverse line movement detection"
    ],
    expected_impact: "+2-3% immediate win rate, +4-5% ROI",
    status: 'in_progress',
    completion_percent: 35
  },
  {
    quarter: "Q2 2025",
    phase: "Advanced Features",
    features: [
      "Injury impact quantification (player value database)",
      "Opponent-adjusted performance metrics",
      "Feature store (prevents data leakage)",
      "Grouped cross-validation (by game_id)",
      "Model registry with canary deployment",
      "Drift & decay monitoring dashboard",
      "NBA bonus-imminent + 2-for-1 triggers",
      "NHL delayed penalty + goalie pull models"
    ],
    expected_impact: "+3-4% additional win rate, 12-13% total ROI",
    status: 'planned',
    completion_percent: 0
  },
  {
    quarter: "Q3 2025",
    phase: "Production Hardening",
    features: [
      "Conformal prediction intervals (uncertainty quantification)",
      "Backtest realism (slippage, fill-probability models)",
      "Referee/umpire tendency database",
      "Weather impact models (NFL/MLB)",
      "Team chemistry metrics (post-trade adjustments)",
      "Playoff race intensity scoring",
      "Public betting fade optimization",
      "Hedge timing optimization for middles"
    ],
    expected_impact: "14-16% ROI with production-grade reliability",
    status: 'planned',
    completion_percent: 0
  }
];

// ============================================================================
// PERFORMANCE PROJECTIONS
// ============================================================================

export interface PerformanceProjection {
  system: string;
  current_roi: number;
  enhanced_roi: number;
  current_win_rate: number;
  enhanced_win_rate: number;
  profit_per_1000_bets: number;
  confidence_in_estimate: string;
}

export const PERFORMANCE_PROJECTIONS: PerformanceProjection[] = [
  {
    system: "Traditional Models (ELO, Power Rankings)",
    current_roi: 0.02,
    enhanced_roi: 0.02,
    current_win_rate: 0.51,
    enhanced_win_rate: 0.51,
    profit_per_1000_bets: 400,
    confidence_in_estimate: "High (based on public data)"
  },
  {
    system: "Current System (Pace-Based)",
    current_roi: 0.083,
    enhanced_roi: 0.083,
    current_win_rate: 0.532,
    enhanced_win_rate: 0.532,
    profit_per_1000_bets: 1660,
    confidence_in_estimate: "High (actual live data)"
  },
  {
    system: "ML-Enhanced (Q1 2025 Quick Wins)",
    current_roi: 0.083,
    enhanced_roi: 0.12,
    current_win_rate: 0.532,
    enhanced_win_rate: 0.56,
    profit_per_1000_bets: 2400,
    confidence_in_estimate: "Medium-High (based on backtests)"
  },
  {
    system: "ML-Enhanced (Q2 2025 Full System)",
    current_roi: 0.083,
    enhanced_roi: 0.14,
    current_win_rate: 0.532,
    enhanced_win_rate: 0.575,
    profit_per_1000_bets: 2800,
    confidence_in_estimate: "Medium (projected)"
  },
  {
    system: "ML-Enhanced (Q3 2025 Production-Grade)",
    current_roi: 0.083,
    enhanced_roi: 0.16,
    current_win_rate: 0.532,
    enhanced_win_rate: 0.59,
    profit_per_1000_bets: 3200,
    confidence_in_estimate: "Medium-Low (aspirational)"
  }
];

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

export const getStrategiesByStatus = (status: StrategyEnhancement['status']) => {
  return STRATEGY_ENHANCEMENTS.filter(s => s.status === status);
};

export const getStrategiesByCategory = (category: StrategyEnhancement['category']) => {
  return STRATEGY_ENHANCEMENTS.filter(s => s.category === category);
};

export const getStrategiesByImpact = (impact: StrategyEnhancement['impact_score']) => {
  return STRATEGY_ENHANCEMENTS.filter(s => s.impact_score === impact);
};

export const calculateROIImprovement = (current_roi: number, enhanced_roi: number) => {
  return ((enhanced_roi - current_roi) / current_roi) * 100;
};

export const calculateProfitDifference = (
  bankroll: number,
  bets_per_week: number,
  current_roi: number,
  enhanced_roi: number
) => {
  const weeks_per_year = 52;
  const total_bets = bets_per_week * weeks_per_year;
  const avg_bet_size = bankroll * 0.02; // 2% Kelly

  const current_profit = total_bets * avg_bet_size * current_roi;
  const enhanced_profit = total_bets * avg_bet_size * enhanced_roi;

  return {
    current_profit,
    enhanced_profit,
    difference: enhanced_profit - current_profit,
    improvement_percent: ((enhanced_profit - current_profit) / current_profit) * 100
  };
};
