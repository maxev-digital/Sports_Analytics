import { useState, useEffect } from 'react';
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

interface PaceMismatchOpportunity {
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  market_total: number;
  predicted_total: number;
  edge: number;
  edge_percentage: number;
  recommendation: string;
  confidence: number;
  confidence_level: string;
  home_pace: number;
  away_pace: number;
  pace_diff: number;
  expected_pace: number;
  scenario: string;
  reasoning: string;
  status: string;
  commence_time: string;
}

export function PaceMismatchAlerts() {
  const [opportunities, setOpportunities] = useState<PaceMismatchOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOpportunities = async () => {
    try {
      const response = await fetch(getApiUrl('pace-mismatch-opportunities'));
      if (!response.ok) throw new Error('Failed to fetch pace mismatch opportunities');
      const data = await response.json();
      setOpportunities(data.opportunities || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOpportunities();
    const interval = setInterval(fetchOpportunities, 10000);
    return () => clearInterval(interval);
  }, []);

  const getConfidenceColor = (level: string) => {
    if (level === 'HIGH') return 'text-green-400';
    if (level === 'MEDIUM') return 'text-yellow-400';
    return 'text-slate-400';
  };

  const getRecommendationColor = (rec: string) => {
    if (rec === 'OVER') return 'bg-red-600';
    if (rec === 'UNDER') return 'bg-blue-600';
    return 'bg-slate-600';
  };

  if (loading) {
    return (
      <div className="bg-slate-800 border-2 border-slate-700 p-12 text-center">
        <div className="text-slate-400 text-lg">Loading pace mismatch opportunities...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-800 border-2 border-red-700 p-12 text-center">
        <div className="text-red-400 text-lg">Error: {error}</div>
      </div>
    );
  }

  if (opportunities.length === 0) {
    return (
      <div className="bg-slate-800 border-2 border-slate-700 p-12 text-center">
        <div className="text-slate-400 text-lg">No pace mismatch opportunities detected</div>
        <div className="text-slate-500 text-sm mt-2">
          Looking for NBA games with significant tempo mismatches (5+ possessions difference)
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {opportunities.map((opp, idx) => (
        <div
          key={idx}
          className={`bg-slate-900 border-4 p-6 transition-all ${
            opp.confidence_level === 'HIGH'
              ? 'border-green-600 shadow-lg shadow-green-600/30'
              : opp.confidence_level === 'MEDIUM'
              ? 'border-yellow-600 shadow-lg shadow-yellow-600/20'
              : 'border-slate-600'
          }`}
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 text-xs font-bold text-white bg-orange-600">
                NBA
              </span>
              <span className="px-3 py-1 text-xs font-bold bg-green-900/50 text-green-300">
                📊 PRE-GAME
              </span>
              <span className="text-xl font-bold text-white">
                {formatTeamName(opp.away_team, sportKeyMapper(opp.sport))} @ {formatTeamName(opp.home_team, sportKeyMapper(opp.sport))}
              </span>
              {opp.status === 'live' && (
                <span className="px-2 py-1 text-xs font-bold bg-red-600 text-white animate-pulse">
                  LIVE
                </span>
              )}
            </div>
            <div className="text-right">
              <div className={`text-sm font-bold ${getConfidenceColor(opp.confidence_level)}`}>
                {opp.confidence_level} CONFIDENCE
              </div>
              <div className="text-slate-400 text-xs mt-1">
                {(opp.confidence * 100).toFixed(0)}% certainty
              </div>
            </div>
          </div>

          {/* Recommendation Card */}
          <div className="bg-gradient-to-br from-slate-800 to-black border-2 border-slate-700 p-6 mb-6">
            <div className="text-center mb-4">
              <div className={`inline-block px-8 py-3 ${getRecommendationColor(opp.recommendation)} text-white text-2xl font-bold shadow-lg mb-2`}>
                {opp.recommendation} {opp.market_total}
              </div>
              <div className="text-slate-300 text-sm mt-2">
                Market Total: {opp.market_total} | Predicted: {opp.predicted_total}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-slate-900/50 border border-slate-700 p-3 text-center">
                <div className="text-slate-400 text-xs mb-1">Edge</div>
                <div className={`text-xl font-bold ${opp.edge > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {opp.edge > 0 ? '+' : ''}{opp.edge}
                </div>
                <div className="text-slate-500 text-xs">
                  {opp.edge_percentage > 0 ? '+' : ''}{opp.edge_percentage.toFixed(1)}%
                </div>
              </div>

              <div className="bg-slate-900/50 border border-slate-700 p-3 text-center">
                <div className="text-slate-400 text-xs mb-1">Expected Pace</div>
                <div className="text-xl font-bold text-white">{opp.expected_pace}</div>
                <div className="text-slate-500 text-xs">possessions/48</div>
              </div>

              <div className="bg-slate-900/50 border border-slate-700 p-3 text-center">
                <div className="text-slate-400 text-xs mb-1">Pace Diff</div>
                <div className="text-xl font-bold text-purple-400">{opp.pace_diff}</div>
                <div className="text-slate-500 text-xs">mismatch</div>
              </div>
            </div>
          </div>

          {/* Pace Analysis */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-slate-800/50 border border-slate-700 p-4">
              <div className="text-sm text-slate-400 mb-2">🏠 {formatTeamName(opp.home_team, sportKeyMapper(opp.sport))} Pace</div>
              <div className="text-2xl font-bold text-white">{opp.home_pace}</div>
              <div className="text-xs text-slate-500">possessions per 48 min</div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700 p-4">
              <div className="text-sm text-slate-400 mb-2">✈️ {formatTeamName(opp.away_team, sportKeyMapper(opp.sport))} Pace</div>
              <div className="text-2xl font-bold text-white">{opp.away_pace}</div>
              <div className="text-xs text-slate-500">possessions per 48 min</div>
            </div>
          </div>

          {/* Scenario Badge */}
          <div className="mb-4">
            <div className="inline-block px-4 py-2 bg-purple-900/50 border border-purple-700 text-purple-300 text-sm font-bold">
              Scenario: {opp.scenario.replace(/_/g, ' ')}
            </div>
          </div>

          {/* Reasoning */}
          <div className="bg-blue-900/20 border border-blue-700/50 p-4">
            <div className="text-sm font-bold text-blue-300 mb-2">📊 Analysis:</div>
            <div className="text-sm text-slate-300 leading-relaxed">
              {opp.reasoning}
            </div>
          </div>

          {/* Footer Info */}
          <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
            <div>Game ID: {opp.game_id}</div>
            <div>Updated: {new Date(opp.commence_time).toLocaleString()}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
