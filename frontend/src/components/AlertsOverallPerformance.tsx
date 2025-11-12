import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

interface OverallStats {
  win_rate: number;
  roi: number;
  total_bets: number;
  total_profit: number;
  wins: number;
  losses: number;
}

export function AlertsOverallPerformance() {
  const [stats, setStats] = useState<OverallStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOverallStats();
  }, []);

  const fetchOverallStats = async () => {
    try {
      const response = await fetch(getApiUrl('performance/summary?days=365'));
      if (response.ok) {
        const data = await response.json();

        // Calculate stats from the API response
        const overall = data.overall || {};
        setStats({
          win_rate: overall.win_rate || 0,
          roi: overall.roi || 0,
          total_bets: overall.total_predictions || 0,
          total_profit: overall.profit_loss || 0,
          wins: overall.wins || 0,
          losses: overall.losses || 0,
        });
      }
    } catch (error) {
      console.error('Error fetching overall stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-900 border-4 border-slate-700 rounded-lg p-8 mb-8">
        <div className="text-white text-center">Loading overall performance...</div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="bg-slate-900 border-4 border-slate-700 rounded-lg p-8 mb-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-4xl font-bold text-white">🏆 Overall Alerts Performance</h2>
        <div className="text-slate-400 text-lg">All-Time Results</div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Win Rate */}
        <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 border-4 border-green-600 rounded-lg p-6">
          <div className="text-green-400 text-base font-bold mb-2">Win Rate</div>
          <div className="text-white text-5xl font-bold leading-tight mb-2">
            {stats.win_rate.toFixed(1)}%
          </div>
          <div className="text-green-300 text-base font-bold">
            {stats.wins}W - {stats.losses}L
          </div>
        </div>

        {/* ROI */}
        <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border-4 border-blue-600 rounded-lg p-6">
          <div className="text-blue-400 text-base font-bold mb-2">ROI</div>
          <div className="text-white text-5xl font-bold leading-tight mb-2">
            {stats.roi >= 0 ? '+' : ''}{stats.roi.toFixed(1)}%
          </div>
          <div className="text-blue-300 text-base font-bold">
            Return on Investment
          </div>
        </div>

        {/* Total Bets */}
        <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border-4 border-purple-600 rounded-lg p-6">
          <div className="text-purple-400 text-base font-bold mb-2">Total Bets</div>
          <div className="text-white text-5xl font-bold leading-tight mb-2">
            {stats.total_bets.toLocaleString()}
          </div>
          <div className="text-purple-300 text-base font-bold">
            Graded Predictions
          </div>
        </div>

        {/* Total Profit (in Units) */}
        <div className="bg-gradient-to-br from-amber-900/50 to-amber-800/30 border-4 border-amber-600 rounded-lg p-6">
          <div className="text-amber-400 text-base font-bold mb-2">Total Profit</div>
          <div className={`text-5xl font-bold leading-tight mb-2 ${
            stats.total_profit >= 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            {stats.total_profit >= 0 ? '+' : ''}{(stats.total_profit / 100).toFixed(1)} U
          </div>
          <div className="text-amber-300 text-base font-bold">
            ${Math.abs(stats.total_profit).toLocaleString()} ($100 Units)
          </div>
        </div>
      </div>

      {/* Additional Context */}
      <div className="mt-6 pt-6 border-t-4 border-slate-700 text-center">
        <p className="text-slate-400 text-base">
          Performance based on all graded alerts using standard $100 unit sizing.
          ROI calculated as: (Total Profit / Total Wagered) × 100
        </p>
      </div>
    </div>
  );
}
