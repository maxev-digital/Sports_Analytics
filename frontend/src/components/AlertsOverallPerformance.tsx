import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

interface AlertTypeStats {
  alert_type: string;
  total_alerts: number;
  settled_alerts: number;
  pending_alerts: number;
  wins: number;
  losses: number;
  pushes: number;
  win_rate: number;
  roi: number;
  total_profit: number;
  avg_odds: number;
}

interface AlertPerformance {
  total_alerts: number;
  settled_alerts: number;
  pending_alerts: number;
  by_alert_type: AlertTypeStats[];
}

export function AlertsOverallPerformance() {
  const [data, setData] = useState<AlertPerformance | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedAlertType, setSelectedAlertType] = useState<string>('ALL');

  const alertTypes = [
    { key: 'ALL', name: 'ALL ALERTS', emoji: '🎯' },
    { key: 'ARBITRAGE', name: 'ARBITRAGE', emoji: '💰' },
    { key: 'MIDDLE', name: 'MIDDLE', emoji: '🎯' },
    { key: 'STEAM_MOVE', name: 'STEAM MOVES', emoji: '🚀' },
  ];

  useEffect(() => {
    fetchAlertPerformance();
  }, []);

  const fetchAlertPerformance = async () => {
    try {
      setLoading(true);
      const response = await fetch(getApiUrl('alert-performance/overview'));
      if (response.ok) {
        const responseData = await response.json();
        // Map API response to expected format
        setData({
          total_alerts: responseData.overall_stats?.total_alerts || 0,
          settled_alerts: responseData.overall_stats?.settled_alerts || 0,
          pending_alerts: responseData.overall_stats?.pending_alerts || 0,
          by_alert_type: responseData.by_alert_type || []
        });
      }
    } catch (error) {
      console.error('Error fetching alert performance:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDisplayStats = () => {
    if (!data) return null;

    if (selectedAlertType === 'ALL') {
      // Calculate combined stats from all alert types
      const allAlerts = data.by_alert_type.reduce((acc, type) => {
        return {
          wins: acc.wins + type.wins,
          losses: acc.losses + type.losses,
          pushes: acc.pushes + type.pushes,
          total_profit: acc.total_profit + type.total_profit,
          settled_alerts: acc.settled_alerts + type.settled_alerts,
        };
      }, { wins: 0, losses: 0, pushes: 0, total_profit: 0, settled_alerts: 0 });

      const winRate = allAlerts.settled_alerts > 0
        ? (allAlerts.wins / (allAlerts.wins + allAlerts.losses)) * 100
        : 0;

      const roi = data.total_alerts > 0
        ? (allAlerts.total_profit / (data.total_alerts * 100)) * 100
        : 0;

      return {
        win_rate: winRate,
        roi: roi,
        total_bets: data.total_alerts,
        total_profit: allAlerts.total_profit,
        wins: allAlerts.wins,
        losses: allAlerts.losses,
      };
    } else {
      // Find specific alert type
      const alertType = data.by_alert_type.find(t => t.alert_type === selectedAlertType);
      if (!alertType) return null;

      return {
        win_rate: alertType.win_rate,
        roi: alertType.roi,
        total_bets: alertType.total_alerts,
        total_profit: alertType.total_profit,
        wins: alertType.wins,
        losses: alertType.losses,
      };
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 mb-3">
        <div className="text-white text-center text-sm">Loading alert performance...</div>
      </div>
    );
  }

  const stats = getDisplayStats();

  if (!stats) {
    return null;
  }

  return (
    <div className="mb-3">
      <h2 className="text-sm font-bold text-green-300 mb-2">Alert Grading Performance</h2>

      {/* Alert Type Filter Buttons */}
      <div className="mb-3">
        <div className="flex flex-wrap gap-2">
          <span className="text-slate-400 text-xs font-semibold self-center mr-1">Alert Type:</span>
          {alertTypes.map((alertType) => (
            <button
              key={alertType.key}
              onClick={() => setSelectedAlertType(alertType.key)}
              className={`px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-2 rounded ${
                selectedAlertType === alertType.key
                  ? 'bg-green-600 text-white shadow-lg shadow-green-600/50'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              <span className="text-sm">{alertType.emoji}</span>
              {alertType.name}
            </button>
          ))}
        </div>
      </div>

      {/* Performance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
        {/* Win Rate */}
        <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 border border-green-700 rounded-lg p-1.5">
          <div className="text-green-400 text-xs font-semibold mb-0">Win Rate</div>
          <div className="text-white text-3xl font-bold leading-tight">
            {stats.win_rate.toFixed(1)}%
          </div>
          <div className="text-green-300 text-xs mt-0">
            {stats.wins}W-{stats.losses}L
          </div>
        </div>

        {/* ROI */}
        <div className={`bg-gradient-to-br ${stats.roi >= 0 ? 'from-blue-900/50 to-blue-800/30 border-blue-700' : 'from-red-900/50 to-red-800/30 border-red-700'} border rounded-lg p-1.5`}>
          <div className={`${stats.roi >= 0 ? 'text-blue-400' : 'text-red-400'} text-xs font-semibold mb-0`}>ROI</div>
          <div className="text-white text-3xl font-bold leading-tight">
            {stats.roi >= 0 ? '+' : ''}{stats.roi.toFixed(1)}%
          </div>
          <div className={`${stats.roi >= 0 ? 'text-blue-300' : 'text-red-300'} text-xs mt-0`}>All-Time</div>
        </div>

        {/* Total Alerts */}
        <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border border-purple-700 rounded-lg p-1.5">
          <div className="text-purple-400 text-xs font-semibold mb-0">Total Alerts</div>
          <div className="text-white text-3xl font-bold leading-tight">
            {stats.total_bets.toLocaleString()}
          </div>
          <div className="text-purple-300 text-xs mt-0">Graded</div>
        </div>

        {/* Total Profit */}
        <div className={`bg-gradient-to-br ${stats.total_profit >= 0 ? 'from-amber-900/50 to-amber-800/30 border-amber-700' : 'from-red-900/50 to-red-800/30 border-red-700'} border rounded-lg p-1.5`}>
          <div className={`${stats.total_profit >= 0 ? 'text-amber-400' : 'text-red-400'} text-xs font-semibold mb-0`}>Total Profit</div>
          <div className="text-white text-3xl font-bold leading-tight">
            {stats.total_profit >= 0 ? '+' : ''}${stats.total_profit.toFixed(0)}
          </div>
          <div className={`${stats.total_profit >= 0 ? 'text-amber-300' : 'text-red-300'} text-xs mt-0`}>
            ${100} per alert
          </div>
        </div>
      </div>
    </div>
  );
}
