import React, { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

interface GoaliePullPrediction {
  trailing_team: string;
  expected_pull_time: number;
  time_until_pull: number;
  confidence: number;
  earliest_likely: number;
  latest_likely: number;
  analytics_rating: number;
  coach: string;
  is_imminent: boolean;
  is_early_warning: boolean;
  alert_type: 'IMMINENT' | 'EARLY_WARNING' | null;
  alert_priority: 'HIGH' | 'MEDIUM' | null;
}

interface EVAnalysis {
  recommended_bet: string | null;
  current_total: number;
  current_odds: number;
  probability_over_hits: number;
  implied_probability: number;
  edge_percentage: number;
  expected_value_percentage: number;
  confidence: number;
  is_positive_ev: boolean;
  alert_user: boolean;
}

interface GoaliePullOpportunity {
  game_id: string;
  game: string;
  trailing_team: string;
  score: string;
  time_remaining: string;
  prediction: GoaliePullPrediction;
  ev_analysis: EVAnalysis;
  alert_message: string;
  priority: 'HIGH' | 'MEDIUM';
  timestamp: string;
}

interface GoaliePullAlertsResponse {
  count: number;
  opportunities: GoaliePullOpportunity[];
}

export const GoaliePullAlerts: React.FC = () => {
  const [opportunities, setOpportunities] = useState<GoaliePullOpportunity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOpportunities = async () => {
      try {
        const response = await fetch(getApiUrl('goalie-pull-opportunities'));
        if (!response.ok) {
          throw new Error('Failed to fetch goalie pull opportunities');
        }
        const data: GoaliePullAlertsResponse = await response.json();
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

  const formatTimeRemaining = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="bg-slate-800 border-4 border-slate-700 rounded-lg p-12 text-center">
        <div className="text-slate-400 text-lg">Loading NHL goalie pull opportunities...</div>
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
        <div className="text-slate-400 text-lg mb-2">No NHL goalie pull opportunities detected</div>
        <div className="text-slate-500 text-sm">Monitoring live NHL games every 10 seconds...</div>
        <div className="text-slate-600 text-xs mt-4">
          Opportunities appear when teams are trailing by 1-2 goals in the 3rd period
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {opportunities.map((opp) => {
        const isEarlyWarning = opp.prediction.alert_type === 'EARLY_WARNING';
        const isHighPriority = opp.priority === 'HIGH';

        return (
          <div
            key={opp.game_id}
            className={`rounded-lg p-6 border-4 ${
              isEarlyWarning
                ? 'bg-gradient-to-br from-blue-900 via-blue-700 to-blue-900 border-blue-500'
                : isHighPriority
                ? 'bg-gradient-to-br from-red-900 via-red-700 to-red-900 border-red-500 shadow-lg shadow-red-600/30'
                : 'bg-gradient-to-br from-yellow-900 via-yellow-700 to-yellow-900 border-yellow-500'
            }`}
          >
            {/* Alert Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span
                  className={`px-4 py-2 rounded-lg font-bold text-white text-sm tracking-wide ${
                    isEarlyWarning
                      ? 'bg-blue-600 border-2 border-blue-400'
                      : isHighPriority
                      ? 'bg-red-600 border-2 border-red-400 animate-pulse'
                      : 'bg-yellow-600 border-2 border-yellow-400'
                  }`}
                >
                  {isEarlyWarning ? '⏰ EARLY WARNING' : `🚨 ${opp.priority} PRIORITY`}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-500 text-white border-2 border-blue-300">
                  NHL
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
                {opp.game}
              </h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-400">Score:</span>
                  <span className="ml-2 font-bold text-white text-lg">{opp.score}</span>
                </div>
                <div>
                  <span className="text-slate-400">Time Remaining:</span>
                  <span className="ml-2 font-bold text-white text-lg">{opp.time_remaining}</span>
                </div>
              </div>
            </div>

            {/* Prediction Details */}
            <div className="bg-black/40 border-4 border-slate-700 rounded-lg p-4 mb-4">
              <h5 className="font-bold text-white mb-3 text-lg flex items-center gap-2">
                📊 GOALIE PULL PREDICTION
              </h5>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-800/70 rounded-lg p-3">
                  <div className="text-xs text-slate-400 mb-1">TRAILING TEAM</div>
                  <div className="font-bold text-white">{opp.prediction.trailing_team}</div>
                </div>
                <div className="bg-slate-800/70 rounded-lg p-3">
                  <div className="text-xs text-slate-400 mb-1">COACH</div>
                  <div className="font-bold text-white">{opp.prediction.coach}</div>
                </div>
                <div className="bg-slate-800/70 rounded-lg p-3">
                  <div className="text-xs text-slate-400 mb-1">PULL EXPECTED IN</div>
                  <div className="font-bold text-red-400 text-xl">
                    {formatTimeRemaining(opp.prediction.time_until_pull)}
                  </div>
                </div>
                <div className="bg-slate-800/70 rounded-lg p-3">
                  <div className="text-xs text-slate-400 mb-1">ANALYTICS RATING</div>
                  <div className="font-bold text-white text-xl">
                    {opp.prediction.analytics_rating.toFixed(1)}/10
                  </div>
                </div>
              </div>

              {/* Confidence Bar */}
              <div className="mt-4">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                  <span>CONFIDENCE</span>
                  <span className="font-bold text-white">
                    {(opp.prediction.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="bg-slate-800 rounded-full h-3 border-2 border-slate-600">
                  <div
                    className="bg-gradient-to-r from-green-600 to-green-400 h-full rounded-full transition-all duration-300"
                    style={{ width: `${opp.prediction.confidence * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Betting Recommendation */}
            {isEarlyWarning ? (
              <div className="bg-gradient-to-br from-blue-700 via-blue-600 to-blue-700 border-4 border-blue-400 rounded-lg p-5">
                <h5 className="font-bold text-white mb-3 text-xl flex items-center gap-2">
                  🎯 PREPARE YOUR BETTING BOOKS NOW
                </h5>
                <p className="text-white text-sm mb-4 leading-relaxed">
                  Possible empty net goal pending. Get ready to bet <span className="font-bold text-yellow-300">OVER {opp.ev_analysis.current_total}</span> when goalie pull becomes imminent.
                </p>

                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="bg-blue-900/60 rounded-lg p-3 border-2 border-blue-500">
                    <div className="text-xs text-blue-200 mb-1">CURRENT ODDS</div>
                    <div className="font-bold text-white text-xl">
                      {opp.ev_analysis.current_odds > 0 ? '+' : ''}
                      {opp.ev_analysis.current_odds}
                    </div>
                  </div>
                  <div className="bg-blue-900/60 rounded-lg p-3 border-2 border-blue-500">
                    <div className="text-xs text-blue-200 mb-1">WIN PROBABILITY</div>
                    <div className="font-bold text-white text-xl">
                      {(opp.ev_analysis.probability_over_hits * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-blue-900/60 rounded-lg p-3 border-2 border-blue-500">
                    <div className="text-xs text-blue-200 mb-1">EXPECTED EDGE</div>
                    <div className="font-bold text-green-400 text-xl">
                      +{opp.ev_analysis.edge_percentage.toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-blue-900/60 rounded-lg p-3 border-2 border-blue-500">
                    <div className="text-xs text-blue-200 mb-1">PULL IN</div>
                    <div className="font-bold text-yellow-300 text-xl">
                      {formatTimeRemaining(opp.prediction.time_until_pull)}
                    </div>
                  </div>
                </div>

                <div className="bg-blue-800 border-3 border-blue-500 rounded-lg p-3">
                  <p className="text-white font-bold text-center text-sm">
                    ⏰ STANDBY - Watch for imminent alert when it's time to place bet
                  </p>
                </div>
              </div>
            ) : (
              <div className="bg-gradient-to-br from-green-700 via-green-600 to-green-700 border-4 border-green-400 rounded-lg p-5">
                <h5 className="font-bold text-white mb-3 text-2xl flex items-center gap-2">
                  💰 BET NOW - OVER {opp.ev_analysis.current_total}
                </h5>

                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="bg-green-900/60 rounded-lg p-3 border-2 border-green-500">
                    <div className="text-xs text-green-200 mb-1">CURRENT ODDS</div>
                    <div className="font-bold text-white text-xl">
                      {opp.ev_analysis.current_odds > 0 ? '+' : ''}
                      {opp.ev_analysis.current_odds}
                    </div>
                  </div>
                  <div className="bg-green-900/60 rounded-lg p-3 border-2 border-green-500">
                    <div className="text-xs text-green-200 mb-1">WIN PROBABILITY</div>
                    <div className="font-bold text-white text-xl">
                      {(opp.ev_analysis.probability_over_hits * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-green-900/60 rounded-lg p-3 border-2 border-green-500">
                    <div className="text-xs text-green-200 mb-1">EDGE</div>
                    <div className="font-bold text-yellow-300 text-xl">
                      +{opp.ev_analysis.edge_percentage.toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-green-900/60 rounded-lg p-3 border-2 border-green-500">
                    <div className="text-xs text-green-200 mb-1">EXPECTED VALUE</div>
                    <div className="font-bold text-yellow-300 text-xl">
                      +{opp.ev_analysis.expected_value_percentage.toFixed(1)}%
                    </div>
                  </div>
                </div>

                <div className="bg-yellow-500 border-3 border-yellow-300 rounded-lg p-4 animate-pulse">
                  <p className="text-black font-bold text-center text-lg">
                    ⏰ BET IMMEDIATELY! Odds will shift to -110 or worse after goalie is pulled.
                  </p>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
