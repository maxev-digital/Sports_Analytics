import React, { useState, useEffect } from 'react';
import { getApiUrl } from '../config';
import { formatTeamName } from '../utils/teamNames';


// Helper function to convert sport names to sport keys
const sportKeyMapper = (sport: string): string => {
  const sportMap: Record<string, string> = {
    'NBA': 'basketball_nba',
    'NCAAB': 'basketball_ncaab',
    'NFL': 'americanfootball_nfl',
    'NCAAF': 'americanfootball_ncaaf',
    'NHL': 'icehockey_nhl',
    'MLB': 'baseball_mlb',
    'Basketball': 'basketball_nba',
    'Football': 'americanfootball_nfl',
    'Hockey': 'icehockey_nhl',
    'Baseball': 'baseball_mlb',
  };
  return sportMap[sport] || sport.toLowerCase();
};

interface RegressionFactor {
  name: string;
  score: number;
  max_score: number;
  details: string;
}

interface BettingRecommendation {
  bet?: string;
  team?: string;
  line?: string | number;
  reasoning: string;
}

interface HistoricalPerformance {
  win_rate: number;
  roi: number;
  sample_size: string;
}

interface HalftimeOpportunity {
  strategy: string;
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  halftime_score: string;
  score_differential: number;
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
  regression_score: number;
  bet_type: '2H Spread' | '2H Total';
  recommendation: BettingRecommendation;
  edge_percentage: number;
  expected_win_rate: number;
  recommended_stake_percent: number;
  historical_performance: HistoricalPerformance;
  regression_factors: RegressionFactor[];
  timestamp?: string;
}

interface HalftimeAlertsResponse {
  count: number;
  opportunities: HalftimeOpportunity[];
}

export const HalftimeTrackerAlerts: React.FC = () => {
  const [opportunities, setOpportunities] = useState<HalftimeOpportunity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOpportunities = async () => {
      try {
        const response = await fetch(getApiUrl('halftime-opportunities'));
        if (!response.ok) {
          throw new Error('Failed to fetch halftime opportunities');
        }
        const data: HalftimeAlertsResponse = await response.json();
        setOpportunities(data.opportunities);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    };

    // Initial fetch
    fetchOpportunities();

    // Poll every 10 seconds for new opportunities
    const interval = setInterval(fetchOpportunities, 10000);

    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="bg-slate-800 border-4 border-slate-700 rounded-lg p-12 text-center">
        <div className="text-slate-400 text-lg">Loading NBA halftime opportunities...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/50 border-4 border-red-600 rounded-lg p-6">
        <p className="text-red-200 font-bold">Error: {error}</p>
      </div>
    );
  }

  if (opportunities.length === 0) {
    return (
      <div className="bg-slate-800 border-4 border-slate-700 rounded-lg p-12 text-center">
        <div className="text-slate-400 text-lg mb-2">No NBA halftime opportunities detected</div>
        <div className="text-slate-500 text-sm">Monitoring live NBA games every 10 seconds...</div>
        <div className="text-slate-600 text-xs mt-4">
          Opportunities appear when NBA games reach halftime with strong 2H regression indicators
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {opportunities.map((opp) => {
        const isHighConfidence = opp.confidence_level === 'HIGH';
        const isMediumConfidence = opp.confidence_level === 'MEDIUM';
        const is2HSpread = opp.bet_type === '2H Spread';

        return (
          <div
            key={`${opp.game_id}-${opp.bet_type}`}
            className={`rounded-lg p-6 border-4 ${
              isHighConfidence
                ? 'bg-gradient-to-br from-purple-900 via-purple-700 to-purple-900 border-purple-500 shadow-lg shadow-purple-600/30'
                : isMediumConfidence
                ? 'bg-gradient-to-br from-indigo-900 via-indigo-700 to-indigo-900 border-indigo-500'
                : 'bg-gradient-to-br from-slate-900 via-slate-700 to-slate-900 border-slate-500'
            }`}
          >
            {/* Alert Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span
                  className={`px-4 py-2 rounded-lg font-bold text-white text-sm tracking-wide ${
                    isHighConfidence
                      ? 'bg-purple-600 border-2 border-purple-400 animate-pulse'
                      : isMediumConfidence
                      ? 'bg-indigo-600 border-2 border-indigo-400'
                      : 'bg-slate-600 border-2 border-slate-400'
                  }`}
                >
                  ⏰ {opp.confidence_level} CONFIDENCE
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-orange-500 text-white border-2 border-orange-300">
                  {opp.sport}
                </span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold text-white border-2 ${
                  is2HSpread ? 'bg-blue-500 border-blue-300' : 'bg-green-500 border-green-300'
                }`}>
                  {opp.bet_type}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-yellow-500 text-black border-2 border-yellow-300">
                  HALFTIME
                </span>
              </div>
              {opp.timestamp && (
                <div className="text-right">
                  <div className="text-xs text-slate-300">
                    {new Date(opp.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              )}
            </div>

            {/* Game Info */}
            <div className="bg-black/40 border-4 border-slate-700 rounded-lg p-4 mb-4">
              <h4 className="font-bold text-white text-2xl mb-2">
                {formatTeamName(opp.home_team, sportKeyMapper(opp.sport))} vs {formatTeamName(opp.away_team, sportKeyMapper(opp.sport))}
              </h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-400">Halftime Score:</span>
                  <span className="ml-2 font-bold text-white text-lg">{opp.halftime_score}</span>
                </div>
                <div>
                  <span className="text-slate-400">Lead:</span>
                  <span className="ml-2 font-bold text-white text-lg">{opp.score_differential} pts</span>
                </div>
                <div>
                  <span className="text-slate-400">Regression Score:</span>
                  <span className={`ml-2 font-bold text-lg ${
                    opp.regression_score >= 16 ? 'text-purple-400' :
                    opp.regression_score >= 12 ? 'text-indigo-400' : 'text-slate-400'
                  }`}>
                    {opp.regression_score}/20
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">2H Window:</span>
                  <span className="ml-2 font-bold text-yellow-300 text-lg">15 MIN</span>
                </div>
              </div>
            </div>

            {/* Regression Analysis - 5 Factors */}
            <div className="bg-black/40 border-4 border-slate-700 rounded-lg p-4 mb-4">
              <h5 className="font-bold text-white mb-3 text-lg flex items-center gap-2">
                📊 REGRESSION ANALYSIS (5-FACTOR SYSTEM)
              </h5>
              <div className="space-y-3">
                {opp.regression_factors.map((factor, idx) => (
                  <div key={idx} className="bg-slate-800/70 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-bold text-slate-300">{factor.name}</span>
                      <span className={`text-sm font-bold ${
                        factor.score >= factor.max_score * 0.8 ? 'text-purple-400' :
                        factor.score >= factor.max_score * 0.5 ? 'text-indigo-400' : 'text-slate-400'
                      }`}>
                        {factor.score}/{factor.max_score}
                      </span>
                    </div>
                    {/* Score Bar */}
                    <div className="bg-slate-900 rounded-full h-2 mb-2 border border-slate-600">
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${
                          factor.score >= factor.max_score * 0.8 ? 'bg-gradient-to-r from-purple-600 to-purple-400' :
                          factor.score >= factor.max_score * 0.5 ? 'bg-gradient-to-r from-indigo-600 to-indigo-400' :
                          'bg-gradient-to-r from-slate-600 to-slate-500'
                        }`}
                        style={{ width: `${(factor.score / factor.max_score) * 100}%` }}
                      />
                    </div>
                    <div className="text-xs text-slate-400">{factor.details}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Historical Performance */}
            <div className="bg-black/40 border-4 border-slate-700 rounded-lg p-4 mb-4">
              <h5 className="font-bold text-white mb-3 text-lg flex items-center gap-2">
                📈 HISTORICAL PERFORMANCE
              </h5>
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-800/70 rounded-lg p-3">
                  <div className="text-xs text-slate-400 mb-1">WIN RATE</div>
                  <div className="font-bold text-purple-400 text-xl">
                    {opp.historical_performance.win_rate}%
                  </div>
                </div>
                <div className="bg-slate-800/70 rounded-lg p-3">
                  <div className="text-xs text-slate-400 mb-1">ROI</div>
                  <div className="font-bold text-green-400 text-xl">
                    +{opp.historical_performance.roi}%
                  </div>
                </div>
                <div className="bg-slate-800/70 rounded-lg p-3">
                  <div className="text-xs text-slate-400 mb-1">SAMPLE SIZE</div>
                  <div className="font-bold text-slate-300 text-sm">
                    {opp.historical_performance.sample_size}
                  </div>
                </div>
              </div>
            </div>

            {/* 2H Betting Recommendation */}
            <div className={`rounded-lg p-5 border-4 ${
              isHighConfidence
                ? 'bg-gradient-to-br from-purple-700 via-purple-600 to-purple-700 border-purple-400'
                : isMediumConfidence
                ? 'bg-gradient-to-br from-indigo-700 via-indigo-600 to-indigo-700 border-indigo-400'
                : 'bg-gradient-to-br from-slate-700 via-slate-600 to-slate-700 border-slate-400'
            }`}>
              <h5 className="font-bold text-white mb-3 text-2xl flex items-center gap-2">
                💰 2H BETTING RECOMMENDATION
              </h5>

              <div className="bg-black/30 rounded-lg p-4 mb-4">
                <div className="text-white font-bold text-xl mb-2">
                  {is2HSpread ? (
                    <>
                      {opp.recommendation.bet}: {opp.recommendation.team} {opp.recommendation.line}
                    </>
                  ) : (
                    <>
                      {opp.recommendation.bet} {opp.recommendation.line}
                    </>
                  )}
                </div>
                <div className="text-slate-200 text-sm">
                  {opp.recommendation.reasoning}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className={`rounded-lg p-3 border-2 ${
                  isHighConfidence ? 'bg-purple-900/60 border-purple-500' :
                  isMediumConfidence ? 'bg-indigo-900/60 border-indigo-500' :
                  'bg-slate-900/60 border-slate-500'
                }`}>
                  <div className="text-xs text-slate-300 mb-1">EXPECTED WIN RATE</div>
                  <div className="font-bold text-white text-xl">
                    {opp.expected_win_rate.toFixed(1)}%
                  </div>
                </div>
                <div className={`rounded-lg p-3 border-2 ${
                  isHighConfidence ? 'bg-purple-900/60 border-purple-500' :
                  isMediumConfidence ? 'bg-indigo-900/60 border-indigo-500' :
                  'bg-slate-900/60 border-slate-500'
                }`}>
                  <div className="text-xs text-slate-300 mb-1">EDGE</div>
                  <div className="font-bold text-green-400 text-xl">
                    +{opp.edge_percentage.toFixed(1)}%
                  </div>
                </div>
                <div className={`rounded-lg p-3 border-2 ${
                  isHighConfidence ? 'bg-purple-900/60 border-purple-500' :
                  isMediumConfidence ? 'bg-indigo-900/60 border-indigo-500' :
                  'bg-slate-900/60 border-slate-500'
                }`}>
                  <div className="text-xs text-slate-300 mb-1">RECOMMENDED STAKE</div>
                  <div className="font-bold text-white text-xl">
                    {opp.recommended_stake_percent.toFixed(1)}%
                  </div>
                </div>
                <div className={`rounded-lg p-3 border-2 ${
                  isHighConfidence ? 'bg-purple-900/60 border-purple-500' :
                  isMediumConfidence ? 'bg-indigo-900/60 border-indigo-500' :
                  'bg-slate-900/60 border-slate-500'
                }`}>
                  <div className="text-xs text-slate-300 mb-1">CONFIDENCE</div>
                  <div className="font-bold text-white text-xl">
                    {opp.confidence_level}
                  </div>
                </div>
              </div>

              {isHighConfidence && (
                <div className="bg-yellow-500 border-3 border-yellow-300 rounded-lg p-4 animate-pulse">
                  <p className="text-black font-bold text-center text-lg">
                    ⏰ BET NOW! You have 15 minutes until 3rd quarter starts!
                  </p>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
