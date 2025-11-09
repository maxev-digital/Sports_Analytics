import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';

interface MonitorStatus {
  running: boolean;
  uptime_seconds: number | null;
  scans_completed: number;
  games_monitored: number;
  alerts_generated: number;
  bets_recommended: number;
}

interface Alert {
  alert_id?: number;
  alert_timestamp: string;
  game_id: string;
  home_team: string;
  away_team: string;
  trailing_team: string;
  time_remaining: string;
  time_remaining_seconds: number;
  score_diff: number;
  coach_id: string | null;
  pull_propensity: number;
  p_at_least_1_goal: number;
  fair_price_american: number;
  offered_price_american: number | null;
  bet_size: number | null;
  ev_at_entry: number | null;
  bet_placed: boolean;
}

interface PerformanceMetrics {
  period_days: number;
  total_alerts: number;
  bets_placed: number;
  wins: number;
  losses: number;
  pushes: number;
  hit_rate_pct: number;
  roi_pct: number;
  avg_clv_cents: number;
  avg_ev_entry_pct: number;
}

const GoaliePull: React.FC = () => {
  const [status, setStatus] = useState<MonitorStatus | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatus();
    fetchAlerts();
    fetchPerformance();

    // Poll status every 10 seconds
    const interval = setInterval(() => {
      fetchStatus();
      fetchAlerts();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/goalie-pull/status`);
      if (!response.ok) throw new Error('Failed to fetch status');
      const data = await response.json();
      setStatus(data);
      setLoading(false);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/goalie-pull/alerts?limit=20`);
      if (!response.ok) throw new Error('Failed to fetch alerts');
      const data = await response.json();
      setAlerts(data);
    } catch (err: any) {
      console.error('Error fetching alerts:', err);
    }
  };

  const fetchPerformance = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/goalie-pull/performance?days=30`);
      if (!response.ok) throw new Error('Failed to fetch performance');
      const data = await response.json();
      setPerformance(data);
    } catch (err: any) {
      console.error('Error fetching performance:', err);
    }
  };

  const startMonitor = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/goalie-pull/start`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to start monitor');
      await fetchStatus();
      alert('Goalie pull monitor started successfully!');
    } catch (err: any) {
      alert(`Error starting monitor: ${err.message}`);
    }
  };

  const stopMonitor = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/goalie-pull/stop`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to stop monitor');
      await fetchStatus();
      alert('Goalie pull monitor stopped successfully!');
    } catch (err: any) {
      alert(`Error stopping monitor: ${err.message}`);
    }
  };

  const formatUptime = (seconds: number | null): string => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}h ${mins}m ${secs}s`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 p-8 flex items-center justify-center">
        <div className="text-white text-xl">Loading goalie pull monitor...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 p-8 flex items-center justify-center">
        <div className="text-red-500 text-xl">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            🏒 NHL Goalie Pull Timing Alpha
          </h1>
          <p className="text-slate-400">
            Real-time monitoring of goalie pull situations for late-game betting opportunities
          </p>
        </div>

        {/* Monitor Status Card */}
        <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950 border-4 border-slate-700 rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">Monitor Status</h2>
            <div className="flex gap-4">
              {!status?.running ? (
                <button
                  onClick={startMonitor}
                  className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-semibold transition-colors"
                >
                  ▶️ Start Monitor
                </button>
              ) : (
                <button
                  onClick={stopMonitor}
                  className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-semibold transition-colors"
                >
                  ⏹️ Stop Monitor
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="bg-slate-950 border-2 border-slate-700 rounded-lg p-4">
              <div className="text-slate-400 text-sm mb-1">Status</div>
              <div className={`text-2xl font-bold ${status?.running ? 'text-green-500' : 'text-red-500'}`}>
                {status?.running ? '🟢 ACTIVE' : '🔴 STOPPED'}
              </div>
            </div>

            <div className="bg-slate-950 border-2 border-slate-700 rounded-lg p-4">
              <div className="text-slate-400 text-sm mb-1">Uptime</div>
              <div className="text-2xl font-bold text-white">
                {formatUptime(status?.uptime_seconds || 0)}
              </div>
            </div>

            <div className="bg-slate-950 border-2 border-slate-700 rounded-lg p-4">
              <div className="text-slate-400 text-sm mb-1">Scans</div>
              <div className="text-2xl font-bold text-white">
                {status?.scans_completed || 0}
              </div>
            </div>

            <div className="bg-slate-950 border-2 border-slate-700 rounded-lg p-4">
              <div className="text-slate-400 text-sm mb-1">Games</div>
              <div className="text-2xl font-bold text-blue-500">
                {status?.games_monitored || 0}
              </div>
            </div>

            <div className="bg-slate-950 border-2 border-slate-700 rounded-lg p-4">
              <div className="text-slate-400 text-sm mb-1">Alerts</div>
              <div className="text-2xl font-bold text-yellow-500">
                {status?.alerts_generated || 0}
              </div>
            </div>

            <div className="bg-slate-950 border-2 border-slate-700 rounded-lg p-4">
              <div className="text-slate-400 text-sm mb-1">Bets</div>
              <div className="text-2xl font-bold text-green-500">
                {status?.bets_recommended || 0}
              </div>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        {performance && (
          <div className="bg-gradient-to-br from-blue-900 via-slate-900 to-slate-950 border-4 border-blue-700 rounded-lg p-6 mb-8">
            <h2 className="text-2xl font-bold text-white mb-6">
              Performance (Last {performance.period_days} Days)
            </h2>

            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
              <div className="bg-slate-950 border-2 border-blue-700 rounded-lg p-4">
                <div className="text-slate-400 text-sm mb-1">Hit Rate</div>
                <div className="text-2xl font-bold text-white">
                  {performance.hit_rate_pct.toFixed(1)}%
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {performance.wins}W-{performance.losses}L-{performance.pushes}P
                </div>
              </div>

              <div className="bg-slate-950 border-2 border-blue-700 rounded-lg p-4">
                <div className="text-slate-400 text-sm mb-1">ROI</div>
                <div className={`text-2xl font-bold ${performance.roi_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {performance.roi_pct >= 0 ? '+' : ''}{performance.roi_pct.toFixed(1)}%
                </div>
              </div>

              <div className="bg-slate-950 border-2 border-blue-700 rounded-lg p-4">
                <div className="text-slate-400 text-sm mb-1">Avg CLV</div>
                <div className="text-2xl font-bold text-yellow-500">
                  +{performance.avg_clv_cents.toFixed(1)}¢
                </div>
              </div>

              <div className="bg-slate-950 border-2 border-blue-700 rounded-lg p-4">
                <div className="text-slate-400 text-sm mb-1">Avg EV</div>
                <div className="text-2xl font-bold text-green-500">
                  +{performance.avg_ev_entry_pct.toFixed(1)}%
                </div>
              </div>

              <div className="bg-slate-950 border-2 border-blue-700 rounded-lg p-4">
                <div className="text-slate-400 text-sm mb-1">Total Bets</div>
                <div className="text-2xl font-bold text-white">
                  {performance.bets_placed}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {performance.total_alerts} alerts
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Recent Alerts */}
        <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950 border-4 border-slate-700 rounded-lg p-6">
          <h2 className="text-2xl font-bold text-white mb-6">Recent Alerts</h2>

          {alerts.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <div className="text-6xl mb-4">🏒</div>
              <div className="text-xl">No alerts yet</div>
              <div className="text-sm mt-2">Alerts will appear here when monitoring live games</div>
            </div>
          ) : (
            <div className="space-y-4">
              {alerts.map((alert, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950 border-2 border-slate-700 rounded-lg p-4 hover:border-blue-500 transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="text-lg font-bold text-white">
                        {alert.away_team} @ {alert.home_team}
                      </div>
                      <div className="text-sm text-slate-400">
                        {new Date(alert.alert_timestamp).toLocaleString()}
                      </div>
                    </div>
                    {alert.bet_placed && (
                      <span className="bg-green-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                        BET PLACED
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 text-sm">
                    <div>
                      <div className="text-slate-400">Trailing Team</div>
                      <div className="text-white font-semibold">{alert.trailing_team}</div>
                    </div>

                    <div>
                      <div className="text-slate-400">Time Remaining</div>
                      <div className="text-white font-semibold">{alert.time_remaining}</div>
                    </div>

                    <div>
                      <div className="text-slate-400">Down By</div>
                      <div className="text-white font-semibold">{alert.score_diff}</div>
                    </div>

                    <div>
                      <div className="text-slate-400">Pull Propensity</div>
                      <div className="text-yellow-500 font-semibold">
                        {(alert.pull_propensity * 100).toFixed(1)}%
                      </div>
                    </div>

                    <div>
                      <div className="text-slate-400">P(Goal)</div>
                      <div className="text-blue-500 font-semibold">
                        {(alert.p_at_least_1_goal * 100).toFixed(1)}%
                      </div>
                    </div>

                    <div>
                      <div className="text-slate-400">Fair Price</div>
                      <div className="text-green-500 font-semibold">
                        {alert.fair_price_american >= 0 ? '+' : ''}{alert.fair_price_american}
                      </div>
                    </div>
                  </div>

                  {alert.offered_price_american && alert.bet_size && (
                    <div className="mt-3 pt-3 border-t border-slate-700">
                      <div className="flex items-center gap-6 text-sm">
                        <div>
                          <span className="text-slate-400">Offered: </span>
                          <span className="text-white font-semibold">
                            {alert.offered_price_american >= 0 ? '+' : ''}{alert.offered_price_american}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400">EV: </span>
                          <span className="text-green-500 font-semibold">
                            +{alert.ev_at_entry?.toFixed(1)}%
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400">Bet Size: </span>
                          <span className="text-white font-semibold">
                            ${alert.bet_size.toFixed(0)}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Info Section */}
        <div className="mt-8 bg-slate-900 border-2 border-slate-700 rounded-lg p-6">
          <h3 className="text-xl font-bold text-white mb-4">How It Works</h3>
          <div className="text-slate-300 space-y-2">
            <p>
              <strong className="text-white">Timing Alpha:</strong> This system identifies opportunities to bet on goals
              being scored before the market reprices after a goalie pull becomes obvious.
            </p>
            <p>
              <strong className="text-white">Layer A (Propensity):</strong> ML model predicts when a coach will pull the goalie
              based on game state, time remaining, and coach tendencies.
            </p>
            <p>
              <strong className="text-white">Layer B (Goals Probability):</strong> Monte Carlo simulation estimates the
              probability of at least 1 goal before the horn, accounting for both teams.
            </p>
            <p>
              <strong className="text-white">Edge Capture:</strong> By betting before the pull is obvious, we capture +10-25 cents
              of closing line value, even when the bet loses.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GoaliePull;
