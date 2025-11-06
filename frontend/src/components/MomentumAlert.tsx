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

interface MomentumFactor {
  name: string;
  score: number;
  max_score: number;
  details: string;
}

interface BettingRecommendation {
  bet: string;
  reasoning: string;
}

interface MomentumOpportunity {
  strategy: string;
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  period?: string;  // NHL
  quarter?: string; // NBA
  score: string;
  momentum_team: string;
  momentum_score: number;
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
  recommendation: BettingRecommendation;
  edge_percentage: number;
  expected_win_rate: number;
  recommended_stake_percent: number;
  momentum_factors: MomentumFactor[];
  timestamp: string;
}

interface MomentumAlertsResponse {
  count: number;
  opportunities: MomentumOpportunity[];
}

export const MomentumAlerts: React.FC = () => {
  const [opportunities, setOpportunities] = useState<MomentumOpportunity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOpportunities = async () => {
      try {
        const response = await fetch(getApiUrl('momentum-opportunities'));
        if (!response.ok) {
          throw new Error('Failed to fetch momentum opportunities');
        }
        const data: MomentumAlertsResponse = await response.json();
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
        <div className="text-slate-400 text-lg">Loading momentum opportunities...</div>
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
        <div className="text-slate-400 text-lg mb-2">No momentum surges detected</div>
        <div className="text-slate-500 text-sm">Monitoring NHL and NBA games every 10 seconds...</div>
        <div className="text-slate-600 text-xs mt-4">
          Opportunities appear when teams go on hot scoring/shot runs
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {opportunities.map((opp, idx) => {
        const isHighConfidence = opp.confidence_level === 'HIGH';
        const isMediumConfidence = opp.confidence_level === 'MEDIUM';
        const isNHL = opp.sport === 'icehockey_nhl';

        return (
          <div
            key={`${opp.game_id}-${idx}`}
            className={`rounded-lg p-6 border-4 ${ isHighConfidence
                ? 'bg-gradient-to-br from-red-900 via-orange-800 to-red-900 border-orange-500 shadow-lg shadow-orange-600/30'
                : isMediumConfidence
                ? 'bg-gradient-to-br from-orange-900 via-red-800 to-orange-900 border-orange-500'
                : 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border-slate-500'
            }`}
          >
            {/* Alert Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span
                  className={`px-4 py-2 rounded-lg font-bold text-white text-sm tracking-wide ${
                    isHighConfidence
                      ? 'bg-red-600 border-2 border-orange-400 animate-pulse'
                      : isMediumConfidence
                      ? 'bg-orange-600 border-2 border-orange-400'
                      : 'bg-slate-600 border-2 border-slate-400'
                  }`}
                >
                  🔥 {opp.confidence_level} CONFIDENCE
                </span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold text-white border-2 ${
                  isNHL ? 'bg-blue-500 border-blue-300' : 'bg-orange-500 border-orange-300'
                }`}>
                  {isNHL ? 'NHL' : 'NBA'}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-red-500 text-white border-2 border-red-300">
                  MOMENTUM SURGE
                </span>
              </div>
              <div className="text-right">
                <div className="text-xs text-slate-300">
                  {new Date(opp.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>

            {/* Game Info */}
            <div className="bg-black/40 border-4 border-slate-700 rounded-lg p-4 mb-4">
              <h4 className="font-bold text-white text-2xl mb-2">
                {formatTeamName(opp.home_team, sportKeyMapper(opp.sport))} vs {formatTeamName(opp.away_team, sportKeyMapper(opp.sport))}
              </h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-400">Score:</span>
                  <span className="ml-2 font-bold text-white text-lg">{opp.score}</span>
                </div>
                <div>
                  <span className="text-slate-400">{isNHL ? 'Period' : 'Quarter'}:</span>
                  <span className="ml-2 font-bold text-white text-lg">{opp.period || opp.quarter}</span>
                </div>
                <div>
                  <span className="text-slate-400">Momentum Team:</span>
                  <span className="ml-2 font-bold text-orange-300 text-lg">{opp.momentum_team}</span>
                </div>
                <div>
                  <span className="text-slate-400">Momentum Score:</span>
                  <span className={`ml-2 font-bold text-lg ${
                    opp.momentum_score >= 75 ? 'text-green-400' :
                    opp.momentum_score >= 60 ? 'text-yellow-400' : 'text-red-400'
                  }`}>
                    {opp.momentum_score}/100
                  </span>
                </div>
              </div>
            </div>

            {/* Momentum Factors */}
            <div className="bg-black/40 border-4 border-slate-700 rounded-lg p-4 mb-4">
              <h5 className="font-bold text-white mb-3 text-lg flex items-center gap-2">
                📊 MOMENTUM FACTORS
              </h5>
              <div className="space-y-3">
                {opp.momentum_factors.map((factor, fidx) => (
                  <div key={fidx} className="bg-slate-800/70 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-bold text-slate-300">{factor.name}</span>
                      <span className={`text-sm font-bold ${
                        factor.score >= factor.max_score * 0.8 ? 'text-green-400' :
                        factor.score >= factor.max_score * 0.5 ? 'text-yellow-400' : 'text-red-400'
                      }`}>
                        {factor.score}/{factor.max_score}
                      </span>
                    </div>
                    {/* Score Bar */}
                    <div className="bg-slate-900 rounded-full h-2 mb-2 border border-slate-600">
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${
                          factor.score >= factor.max_score * 0.8 ? 'bg-gradient-to-r from-green-500 to-green-400' :
                          factor.score >= factor.max_score * 0.5 ? 'bg-gradient-to-r from-green-600 to-yellow-500' :
                          'bg-gradient-to-r from-red-600 to-red-500'
                        }`}
                        style={{ width: `${(factor.score / factor.max_score) * 100}%` }}
                      />
                    </div>
                    <div className="text-xs text-slate-400">{factor.details}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Betting Recommendation */}
            <div className={`rounded-lg p-5 border-4 ${
              isHighConfidence
                ? 'bg-gradient-to-br from-red-700 via-orange-600 to-red-700 border-orange-400'
                : isMediumConfidence
                ? 'bg-gradient-to-br from-orange-700 via-red-600 to-orange-700 border-orange-400'
                : 'bg-gradient-to-br from-slate-700 via-slate-600 to-slate-700 border-slate-400'
            }`}>
              <h5 className="font-bold text-white mb-3 text-2xl flex items-center gap-2">
                💰 LIVE BETTING RECOMMENDATION
              </h5>

              <div className="bg-black/30 rounded-lg p-4 mb-4">
                <div className="text-white font-bold text-xl mb-2">
                  {opp.recommendation.bet}
                </div>
                <div className="text-slate-200 text-sm">
                  {opp.recommendation.reasoning}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className={`rounded-lg p-3 border-2 ${
                  isHighConfidence ? 'bg-red-900/60 border-orange-500' :
                  isMediumConfidence ? 'bg-orange-900/60 border-orange-500' :
                  'bg-slate-900/60 border-slate-500'
                }`}>
                  <div className="text-xs text-slate-300 mb-1">EXPECTED WIN RATE</div>
                  <div className="font-bold text-white text-xl">
                    {(opp.expected_win_rate * 100).toFixed(1)}%
                  </div>
                </div>
                <div className={`rounded-lg p-3 border-2 ${
                  isHighConfidence ? 'bg-red-900/60 border-orange-500' :
                  isMediumConfidence ? 'bg-orange-900/60 border-orange-500' :
                  'bg-slate-900/60 border-slate-500'
                }`}>
                  <div className="text-xs text-slate-300 mb-1">EDGE</div>
                  <div className="font-bold text-green-400 text-xl">
                    +{opp.edge_percentage.toFixed(1)}%
                  </div>
                </div>
                <div className={`rounded-lg p-3 border-2 ${
                  isHighConfidence ? 'bg-red-900/60 border-orange-500' :
                  isMediumConfidence ? 'bg-orange-900/60 border-orange-500' :
                  'bg-slate-900/60 border-slate-500'
                }`}>
                  <div className="text-xs text-slate-300 mb-1">RECOMMENDED STAKE</div>
                  <div className="font-bold text-white text-xl">
                    {opp.recommended_stake_percent.toFixed(1)}%
                  </div>
                </div>
                <div className={`rounded-lg p-3 border-2 ${
                  isHighConfidence ? 'bg-red-900/60 border-orange-500' :
                  isMediumConfidence ? 'bg-orange-900/60 border-orange-500' :
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
                    🔥 STRIKE NOW! {opp.momentum_team} is surging with {opp.momentum_score}/100 momentum!
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
