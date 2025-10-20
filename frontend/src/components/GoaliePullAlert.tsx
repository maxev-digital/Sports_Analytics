import React, { useState, useEffect } from 'react';

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
        const response = await fetch('/api/goalie-pull-opportunities');
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-200 text-sm">Error: {error}</p>
      </div>
    );
  }

  if (opportunities.length === 0) {
    return (
      <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <p className="text-gray-600 dark:text-gray-400 text-sm text-center">
          No goalie pull opportunities at this time. Monitoring live NHL games...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
          🚨 NHL Goalie Pull Alerts
        </h3>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {opportunities.length} {opportunities.length === 1 ? 'opportunity' : 'opportunities'}
        </span>
      </div>

      {opportunities.map((opp) => {
        const isEarlyWarning = opp.prediction.alert_type === 'EARLY_WARNING';

        return (
        <div
          key={opp.game_id}
          className={`border-2 rounded-lg p-4 ${
            isEarlyWarning
              ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 dark:border-blue-600'
              : opp.priority === 'HIGH'
              ? 'bg-red-50 dark:bg-red-900/20 border-red-500 dark:border-red-600'
              : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-500 dark:border-yellow-600'
          }`}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <span
                className={`px-2 py-1 rounded text-xs font-bold ${
                  isEarlyWarning
                    ? 'bg-blue-600 text-white'
                    : opp.priority === 'HIGH'
                    ? 'bg-red-600 text-white'
                    : 'bg-yellow-600 text-white'
                }`}
              >
                {isEarlyWarning ? '⏰ EARLY WARNING' : `${opp.priority} PRIORITY`}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {new Date(opp.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>

          {/* Game Info */}
          <div className="mb-3">
            <h4 className="font-bold text-gray-900 dark:text-gray-100 text-lg">
              {opp.game}
            </h4>
            <div className="flex items-center space-x-4 text-sm text-gray-700 dark:text-gray-300 mt-1">
              <span>Score: {opp.score}</span>
              <span>•</span>
              <span>Time: {opp.time_remaining}</span>
            </div>
          </div>

          {/* Prediction Details */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-3 mb-3">
            <h5 className="font-semibold text-gray-900 dark:text-gray-100 mb-2 flex items-center">
              📊 Prediction
            </h5>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">Trailing Team:</span>
                <span className="ml-2 font-semibold text-gray-900 dark:text-gray-100">
                  {opp.prediction.trailing_team}
                </span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Coach:</span>
                <span className="ml-2 font-semibold text-gray-900 dark:text-gray-100">
                  {opp.prediction.coach}
                </span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Pull in:</span>
                <span className="ml-2 font-bold text-red-600 dark:text-red-400">
                  ~{opp.prediction.time_until_pull}s
                </span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Analytics:</span>
                <span className="ml-2 font-semibold text-gray-900 dark:text-gray-100">
                  {opp.prediction.analytics_rating}/10
                </span>
              </div>
              <div className="col-span-2">
                <span className="text-gray-600 dark:text-gray-400">Confidence:</span>
                <div className="flex items-center mt-1">
                  <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mr-2">
                    <div
                      className="bg-green-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${opp.prediction.confidence * 100}%` }}
                    />
                  </div>
                  <span className="font-semibold text-gray-900 dark:text-gray-100">
                    {(opp.prediction.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Betting Recommendation */}
          {isEarlyWarning ? (
            <div className="bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-500 dark:border-blue-600 rounded-lg p-3">
              <h5 className="font-bold text-blue-900 dark:text-blue-100 mb-2 flex items-center text-lg">
                🎯 PREPARE YOUR BETTING BOOKS NOW
              </h5>
              <p className="text-blue-800 dark:text-blue-200 text-sm mb-3">
                Possible empty net goal pending. Get ready to bet OVER {opp.ev_analysis.current_total} when goalie pull becomes imminent.
              </p>
              <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                <div>
                  <span className="text-blue-700 dark:text-blue-300">Current Odds:</span>
                  <span className="ml-2 font-bold text-blue-900 dark:text-blue-100">
                    {opp.ev_analysis.current_odds > 0 ? '+' : ''}
                    {opp.ev_analysis.current_odds}
                  </span>
                </div>
                <div>
                  <span className="text-blue-700 dark:text-blue-300">Win Probability:</span>
                  <span className="ml-2 font-bold text-blue-900 dark:text-blue-100">
                    {(opp.ev_analysis.probability_over_hits * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-blue-700 dark:text-blue-300">Expected Edge:</span>
                  <span className="ml-2 font-bold text-blue-900 dark:text-blue-100">
                    {opp.ev_analysis.expected_value_percentage >= 0 ? '+' : ''}
                    {opp.ev_analysis.expected_value_percentage.toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-blue-700 dark:text-blue-300">Time Until Pull:</span>
                  <span className="ml-2 font-bold text-blue-900 dark:text-blue-100">
                    ~{opp.prediction.time_until_pull}s
                  </span>
                </div>
              </div>
              <div className="bg-blue-100 dark:bg-blue-900/40 border border-blue-300 dark:border-blue-700 rounded p-2">
                <p className="text-blue-900 dark:text-blue-100 font-semibold text-xs text-center">
                  ⏰ STANDBY - Watch for imminent alert when it's time to place bet
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-green-50 dark:bg-green-900/20 border-2 border-green-500 dark:border-green-600 rounded-lg p-3">
              <h5 className="font-bold text-green-900 dark:text-green-100 mb-2 flex items-center text-lg">
                💰 BET NOW - OVER {opp.ev_analysis.current_total}
              </h5>
              <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                <div>
                  <span className="text-green-700 dark:text-green-300">Current Odds:</span>
                  <span className="ml-2 font-bold text-green-900 dark:text-green-100">
                    {opp.ev_analysis.current_odds > 0 ? '+' : ''}
                    {opp.ev_analysis.current_odds}
                  </span>
                </div>
                <div>
                  <span className="text-green-700 dark:text-green-300">Win Probability:</span>
                  <span className="ml-2 font-bold text-green-900 dark:text-green-100">
                    {(opp.ev_analysis.probability_over_hits * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-green-700 dark:text-green-300">Edge:</span>
                  <span className="ml-2 font-bold text-green-900 dark:text-green-100">
                    +{opp.ev_analysis.edge_percentage.toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-green-700 dark:text-green-300">Expected Value:</span>
                  <span className="ml-2 font-bold text-green-900 dark:text-green-100">
                    +{opp.ev_analysis.expected_value_percentage.toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="bg-green-100 dark:bg-green-900/40 border border-green-300 dark:border-green-700 rounded p-2">
                <p className="text-green-900 dark:text-green-100 font-semibold text-xs text-center">
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
