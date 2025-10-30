import React, { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

interface RegressionFactor {
  name: string;
  score: number;
  max_score: number;
  details: string;
}

interface BettingRecommendation {
  bet_type: string;
  team: string;
  reasoning: string;
  expected_spread: string;
}

interface HistoricalPerformance {
  timing: string;
  win_rate: number;
  ats_coverage: string;
  sample_size: string;
}

interface FavoriteComebackOpportunity {
  strategy: string;
  game_id: string;
  sport: string;
  favorite: string;
  underdog: string;
  current_score: string;
  score_differential: number;
  period: string;
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
  regression_score: number;
  recommendation: BettingRecommendation;
  edge_percentage: number;
  expected_win_rate: number;
  recommended_stake_percent: number;
  betting_window: string;
  historical_performance: HistoricalPerformance;
  regression_factors: RegressionFactor[];
  timestamp?: string;
}

interface FavoriteComebackAlertsResponse {
  count: number;
  opportunities: FavoriteComebackOpportunity[];
}

export const FavoriteComebackAlerts: React.FC = () => {
  const [opportunities, setOpportunities] = useState<FavoriteComebackOpportunity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOpportunities = async () => {
      try {
        const response = await fetch(getApiUrl('favorite-comeback-opportunities'));
        if (!response.ok) {
          throw new Error('Failed to fetch favorite comeback opportunities');
        }
        const data: FavoriteComebackAlertsResponse = await response.json();
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
        <div className="text-slate-400 text-lg">Loading NBA favorite comeback opportunities...</div>
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
        <div className="text-slate-400 text-lg mb-2">No NBA favorite comeback opportunities detected</div>
        <div className="text-slate-500 text-sm">Monitoring live NBA games every 10 seconds...</div>
        <div className="text-slate-600 text-xs mt-4">
          Opportunities appear when favorites trail underdogs in Q1, Q2, or at Halftime with strong regression indicators
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {opportunities.map((opp) => {
        const isHighConfidence = opp.confidence_level === 'HIGH';
        const isMediumConfidence = opp.confidence_level === 'MEDIUM';

        return (
          <div
            key={opp.game_id}
            className={`rounded-lg p-6 border-4 ${
              isHighConfidence
                ? 'bg-gradient-to-br from-green-900 via-green-700 to-green-900 border-green-500 shadow-lg shadow-green-600/30'
                : isMediumConfidence
                ? 'bg-gradient-to-br from-yellow-900 via-yellow-700 to-yellow-900 border-yellow-500'
                : 'bg-gradient-to-br from-slate-900 via-slate-700 to-slate-900 border-slate-500'
            }`}
          >
            {/* Alert Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span
                  className={`px-4 py-2 rounded-lg font-bold text-white text-sm tracking-wide ${
                    isHighConfidence
                      ? 'bg-green-600 border-2 border-green-400 animate-pulse'
                      : isMediumConfidence
                      ? 'bg-yellow-600 border-2 border-yellow-400'
                      : 'bg-slate-600 border-2 border-slate-400'
                  }`}
                >
                  🔥 {opp.confidence_level} CONFIDENCE
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-orange-500 text-white border-2 border-orange-300">
                  {opp.sport}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-purple-500 text-white border-2 border-purple-300">
                  {opp.betting_window}
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
                {opp.favorite} vs {opp.underdog}
              </h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-400">Current Score:</span>
                  <span className="ml-2 font-bold text-white text-lg">{opp.current_score}</span>
                </div>
                <div>
                  <span className="text-slate-400">Period:</span>
                  <span className="ml-2 font-bold text-white text-lg">{opp.period}</span>
                </div>
                <div>
                  <span className="text-slate-400">Trailing By:</span>
                  <span className="ml-2 font-bold text-red-400 text-lg">{opp.score_differential} pts</span>
                </div>
                <div>
                  <span className="text-slate-400">Regression Score:</span>
                  <span className={`ml-2 font-bold text-lg ${
                    opp.regression_score >= 15 ? 'text-green-400' :
                    opp.regression_score >= 10 ? 'text-yellow-400' : 'text-slate-400'
                  }`}>
                    {opp.regression_score}/20
                  </span>
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
                        factor.score >= factor.max_score * 0.8 ? 'text-green-400' :
                        factor.score >= factor.max_score * 0.5 ? 'text-yellow-400' : 'text-slate-400'
                      }`}>
                        {factor.score}/{factor.max_score}
                      </span>
                    </div>
                    {/* Score Bar */}
                    <div className="bg-slate-900 rounded-full h-2 mb-2 border border-slate-600">
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${
                          factor.score >= factor.max_score * 0.8 ? 'bg-gradient-to-r from-green-600 to-green-400' :
                          factor.score >= factor.max_score * 0.5 ? 'bg-gradient-to-r from-yellow-600 to-yellow-400' :
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
                  <div className="font-bold text-green-400 text-xl">
                    {opp.historical_performance.win_rate}%
                  </div>
                </div>
                <div className="bg-slate-800/70 rounded-lg p-3">
                  <div className="text-xs text-slate-400 mb-1">ATS COVERAGE</div>
                  <div className="font-bold text-white text-lg">
                    {opp.historical_performance.ats_coverage}
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

            {/* Betting Recommendation */}
            <div className={`rounded-lg p-5 border-4 ${
              isHighConfidence
                ? 'bg-gradient-to-br from-green-700 via-green-600 to-green-700 border-green-400'
                : isMediumConfidence
                ? 'bg-gradient-to-br from-yellow-700 via-yellow-600 to-yellow-700 border-yellow-400'
                : 'bg-gradient-to-br from-slate-700 via-slate-600 to-slate-700 border-slate-400'
            }`}>
              <h5 className="font-bold text-white mb-3 text-2xl flex items-center gap-2">
                💰 BETTING RECOMMENDATION
              </h5>

              <div className="bg-black/30 rounded-lg p-4 mb-4">
                <div className="text-white font-bold text-xl mb-2">
                  {opp.recommendation.bet_type}: {opp.recommendation.team} {opp.recommendation.expected_spread}
                </div>
                <div className="text-slate-200 text-sm">
                  {opp.recommendation.reasoning}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className={`rounded-lg p-3 border-2 ${
                  isHighConfidence ? 'bg-green-900/60 border-green-500' :
                  isMediumConfidence ? 'bg-yellow-900/60 border-yellow-500' :
                  'bg-slate-900/60 border-slate-500'
                }`}>
                  <div className="text-xs text-slate-300 mb-1">EXPECTED WIN RATE</div>
                  <div className="font-bold text-white text-xl">
                    {opp.expected_win_rate.toFixed(1)}%
                  </div>
                </div>
                <div className={`rounded-lg p-3 border-2 ${
                  isHighConfidence ? 'bg-green-900/60 border-green-500' :
                  isMediumConfidence ? 'bg-yellow-900/60 border-yellow-500' :
                  'bg-slate-900/60 border-slate-500'
                }`}>
                  <div className="text-xs text-slate-300 mb-1">EDGE</div>
                  <div className="font-bold text-green-400 text-xl">
                    +{opp.edge_percentage.toFixed(1)}%
                  </div>
                </div>
                <div className={`rounded-lg p-3 border-2 ${
                  isHighConfidence ? 'bg-green-900/60 border-green-500' :
                  isMediumConfidence ? 'bg-yellow-900/60 border-yellow-500' :
                  'bg-slate-900/60 border-slate-500'
                }`}>
                  <div className="text-xs text-slate-300 mb-1">RECOMMENDED STAKE</div>
                  <div className="font-bold text-white text-xl">
                    {opp.recommended_stake_percent.toFixed(1)}%
                  </div>
                </div>
                <div className={`rounded-lg p-3 border-2 ${
                  isHighConfidence ? 'bg-green-900/60 border-green-500' :
                  isMediumConfidence ? 'bg-yellow-900/60 border-yellow-500' :
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
                    🔥 HIGH CONFIDENCE BET - Place wager on 2H spread when available!
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
