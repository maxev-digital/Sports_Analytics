/**
 * Volatility Arbitrage Performance Tracker
 *
 * Shows performance stats and analytics:
 * - Actual vs expected trigger rate
 * - Profit vs projections
 * - Hedged vs held positions
 * - ROI and variance metrics
 */

import { useState, useEffect } from 'react';
import { TrendingUp, DollarSign, Target, BarChart3, Activity, Info } from 'lucide-react';

interface PerformanceStats {
  // Position counts
  total_positions: number;
  hedged_positions: number;
  held_positions: number;
  closed_won: number;
  closed_lost: number;
  open_positions: number;

  // Financial metrics
  total_profit: number;
  total_wagered: number;
  roi_percent: number;
  avg_profit_per_position: number;

  // Trigger metrics
  actual_trigger_rate: number;
  expected_trigger_rate: number;

  // EV metrics
  expected_profit: number;
  variance: number;
  variance_percent: number;

  // Breakdown
  hedged_profit: number;
  held_won_profit: number;
  held_lost_loss: number;
}

interface DateRange {
  label: string;
  days: number;
}

const DATE_RANGES: DateRange[] = [
  { label: '7 Days', days: 7 },
  { label: '30 Days', days: 30 },
  { label: '90 Days', days: 90 },
  { label: 'All Time', days: 0 }
];

export function VolatilityPerformance() {
  const [stats, setStats] = useState<PerformanceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedRange, setSelectedRange] = useState<DateRange>(DATE_RANGES[1]); // 30 days default
  const [showInfo, setShowInfo] = useState(false);

  useEffect(() => {
    fetchStats();
  }, [selectedRange]);

  const fetchStats = async () => {
    try {
      // TODO: Get actual user_id from auth
      const userId = 'USER_ID';

      let startDate = '';
      if (selectedRange.days > 0) {
        const date = new Date();
        date.setDate(date.getDate() - selectedRange.days);
        startDate = date.toISOString();
      }

      const response = await fetch(
        `/api/volatility/performance?user_id=${userId}&start_date=${startDate}`
      );
      const data = await response.json();

      setStats(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching performance stats:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900 rounded-lg p-8 text-center">
        <div className="text-white">Loading performance data...</div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900 rounded-lg p-8 text-center">
        <div className="text-white/60">No performance data available yet</div>
      </div>
    );
  }

  const hedgedPercent = stats.total_positions > 0
    ? (stats.hedged_positions / stats.total_positions * 100)
    : 0;

  const heldPercent = stats.total_positions > 0
    ? (stats.held_positions / stats.total_positions * 100)
    : 0;

  const heldWinRate = stats.held_positions > 0
    ? (stats.closed_won / stats.held_positions * 100)
    : 0;

  return (
    <div className="bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900 rounded-lg border-4 border-cyan-600 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-cyan-600 to-blue-600 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-white/20 rounded-lg">
              <BarChart3 className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Performance Analytics</h2>
              <p className="text-cyan-100">Volatility Arbitrage Strategy</p>
            </div>
          </div>
          <button
            onClick={() => setShowInfo(!showInfo)}
            className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
          >
            <Info className="w-6 h-6 text-white" />
          </button>
        </div>

        {/* Date Range Selector */}
        <div className="flex gap-2 mt-4">
          {DATE_RANGES.map(range => (
            <button
              key={range.label}
              onClick={() => setSelectedRange(range)}
              className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                selectedRange.label === range.label
                  ? 'bg-white text-cyan-700'
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {/* Info Panel */}
      {showInfo && (
        <div className="bg-black/30 p-6 border-b border-white/10">
          <h3 className="text-white font-bold mb-2">How to Read These Metrics</h3>
          <ul className="text-white/80 text-sm space-y-1 list-disc list-inside">
            <li><strong>Trigger Rate:</strong> Percentage of positions where hedge opportunity hit target price</li>
            <li><strong>Expected Profit:</strong> What you would make at 15.7% EV with perfect execution</li>
            <li><strong>Variance:</strong> How much you're beating or trailing expected value</li>
            <li><strong>Hedged %:</strong> Positions where you locked in guaranteed profit</li>
            <li><strong>Held %:</strong> Positions where you rode the first bet to completion</li>
          </ul>
        </div>
      )}

      <div className="p-6 space-y-6">
        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Total Profit */}
          <div className="bg-gradient-to-br from-emerald-900/40 to-green-900/40 rounded-lg p-6 border-2 border-emerald-600">
            <div className="flex items-center gap-3 mb-2">
              <DollarSign className="w-6 h-6 text-emerald-400" />
              <div className="text-emerald-300 text-sm font-semibold">Total Profit</div>
            </div>
            <div className={`text-4xl font-bold ${
              stats.total_profit >= 0 ? 'text-emerald-300' : 'text-red-300'
            }`}>
              {stats.total_profit >= 0 ? '+' : ''}${stats.total_profit.toFixed(2)}
            </div>
            <div className="text-white/60 text-sm mt-2">
              ${stats.total_wagered.toFixed(2)} wagered
            </div>
          </div>

          {/* ROI */}
          <div className="bg-gradient-to-br from-blue-900/40 to-indigo-900/40 rounded-lg p-6 border-2 border-blue-600">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp className="w-6 h-6 text-blue-400" />
              <div className="text-blue-300 text-sm font-semibold">ROI</div>
            </div>
            <div className={`text-4xl font-bold ${
              stats.roi_percent >= 0 ? 'text-emerald-300' : 'text-red-300'
            }`}>
              {stats.roi_percent >= 0 ? '+' : ''}{stats.roi_percent.toFixed(1)}%
            </div>
            <div className="text-white/60 text-sm mt-2">
              Avg ${stats.avg_profit_per_position.toFixed(2)}/position
            </div>
          </div>

          {/* Total Positions */}
          <div className="bg-gradient-to-br from-purple-900/40 to-violet-900/40 rounded-lg p-6 border-2 border-purple-600">
            <div className="flex items-center gap-3 mb-2">
              <Target className="w-6 h-6 text-purple-400" />
              <div className="text-purple-300 text-sm font-semibold">Total Positions</div>
            </div>
            <div className="text-4xl font-bold text-white">{stats.total_positions}</div>
            <div className="text-white/60 text-sm mt-2">
              {stats.open_positions} currently open
            </div>
          </div>
        </div>

        {/* Trigger Rate Analysis */}
        <div className="bg-white/5 rounded-lg p-6">
          <h3 className="text-white font-bold text-lg mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-400" />
            Trigger Rate Analysis
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Actual vs Expected */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-white/70 text-sm">Actual Trigger Rate</span>
                <span className="text-white font-bold text-2xl">
                  {stats.actual_trigger_rate.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-black/30 rounded-full h-3 mb-4">
                <div
                  className="bg-gradient-to-r from-cyan-500 to-blue-500 h-3 rounded-full"
                  style={{ width: `${Math.min(stats.actual_trigger_rate, 100)}%` }}
                />
              </div>

              <div className="flex justify-between items-center mb-2">
                <span className="text-white/70 text-sm">Expected Trigger Rate</span>
                <span className="text-white/60 font-semibold text-xl">
                  {stats.expected_trigger_rate.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-black/30 rounded-full h-3">
                <div
                  className="bg-gradient-to-r from-gray-500 to-gray-600 h-3 rounded-full"
                  style={{ width: `${stats.expected_trigger_rate}%` }}
                />
              </div>

              <div className="mt-4 p-3 bg-black/30 rounded-lg">
                <div className="text-white/70 text-xs mb-1">Variance</div>
                <div className={`font-semibold ${
                  stats.actual_trigger_rate >= stats.expected_trigger_rate
                    ? 'text-emerald-300'
                    : 'text-yellow-300'
                }`}>
                  {stats.actual_trigger_rate >= stats.expected_trigger_rate ? '+' : ''}
                  {(stats.actual_trigger_rate - stats.expected_trigger_rate).toFixed(1)}% from expected
                </div>
              </div>
            </div>

            {/* Position Distribution */}
            <div>
              <div className="mb-3">
                <div className="flex justify-between mb-2">
                  <span className="text-emerald-300 text-sm">Hedged (Locked Profit)</span>
                  <span className="text-white font-semibold">{hedgedPercent.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-black/30 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-emerald-500 to-green-500 h-3 rounded-full"
                    style={{ width: `${hedgedPercent}%` }}
                  />
                </div>
                <div className="text-white/50 text-xs mt-1">
                  {stats.hedged_positions} positions
                </div>
              </div>

              <div className="mb-3">
                <div className="flex justify-between mb-2">
                  <span className="text-blue-300 text-sm">Held (Rode First Bet)</span>
                  <span className="text-white font-semibold">{heldPercent.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-black/30 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-indigo-500 h-3 rounded-full"
                    style={{ width: `${heldPercent}%` }}
                  />
                </div>
                <div className="text-white/50 text-xs mt-1">
                  {stats.held_positions} positions • {heldWinRate.toFixed(1)}% win rate
                </div>
              </div>

              <div className="mt-4 p-3 bg-black/30 rounded-lg">
                <div className="text-white/70 text-xs mb-2">Held Positions Breakdown</div>
                <div className="flex justify-between text-sm">
                  <span className="text-green-300">Won: {stats.closed_won}</span>
                  <span className="text-red-300">Lost: {stats.closed_lost}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* EV Comparison */}
        <div className="bg-white/5 rounded-lg p-6">
          <h3 className="text-white font-bold text-lg mb-4">EV Performance vs Projections</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Expected Profit */}
            <div className="bg-black/30 rounded-lg p-4">
              <div className="text-white/70 text-sm mb-2">Expected Profit (15.7% EV)</div>
              <div className="text-white font-bold text-3xl">
                ${stats.expected_profit.toFixed(2)}
              </div>
              <div className="text-white/50 text-xs mt-1">
                Based on {stats.total_positions} positions at target EV
              </div>
            </div>

            {/* Actual vs Expected */}
            <div className="bg-black/30 rounded-lg p-4">
              <div className="text-white/70 text-sm mb-2">Variance from Expected</div>
              <div className={`font-bold text-3xl ${
                stats.variance >= 0 ? 'text-emerald-300' : 'text-red-300'
              }`}>
                {stats.variance >= 0 ? '+' : ''}${stats.variance.toFixed(2)}
              </div>
              <div className={`text-sm mt-1 ${
                stats.variance >= 0 ? 'text-emerald-300' : 'text-red-300'
              }`}>
                {stats.variance >= 0 ? '+' : ''}{stats.variance_percent.toFixed(1)}% {
                  stats.variance >= 0 ? 'above' : 'below'
                } expected
              </div>
            </div>
          </div>

          <div className="mt-4 p-4 bg-blue-900/20 border border-blue-600 rounded-lg">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-400 mt-0.5" />
              <div className="text-white/80 text-sm leading-relaxed">
                <strong className="text-white">Variance is expected:</strong> Volatility arbitrage is a high-variance strategy.
                Short-term results will fluctuate significantly. The 15.7% EV is a long-term expectation over
                hundreds of positions. Sample size of {stats.total_positions} is {
                  stats.total_positions < 50 ? 'too small for statistical significance' :
                  stats.total_positions < 100 ? 'developing' :
                  stats.total_positions < 500 ? 'moderate' :
                  'strong'
                }.
              </div>
            </div>
          </div>
        </div>

        {/* Profit Breakdown */}
        <div className="bg-white/5 rounded-lg p-6">
          <h3 className="text-white font-bold text-lg mb-4">Profit Breakdown</h3>

          <div className="space-y-3">
            {/* Hedged Profit */}
            <div className="flex justify-between items-center p-3 bg-emerald-900/20 rounded-lg border border-emerald-600">
              <div>
                <div className="text-emerald-300 font-semibold">Hedged Positions</div>
                <div className="text-white/60 text-sm">
                  {stats.hedged_positions} positions • Guaranteed profit locked
                </div>
              </div>
              <div className="text-emerald-300 font-bold text-xl">
                +${stats.hedged_profit.toFixed(2)}
              </div>
            </div>

            {/* Held Won Profit */}
            <div className="flex justify-between items-center p-3 bg-green-900/20 rounded-lg border border-green-600">
              <div>
                <div className="text-green-300 font-semibold">Held & Won</div>
                <div className="text-white/60 text-sm">
                  {stats.closed_won} positions • Rode first bet to victory
                </div>
              </div>
              <div className="text-green-300 font-bold text-xl">
                +${stats.held_won_profit.toFixed(2)}
              </div>
            </div>

            {/* Held Lost Loss */}
            <div className="flex justify-between items-center p-3 bg-red-900/20 rounded-lg border border-red-600">
              <div>
                <div className="text-red-300 font-semibold">Held & Lost</div>
                <div className="text-white/60 text-sm">
                  {stats.closed_lost} positions • First bet did not hit
                </div>
              </div>
              <div className="text-red-300 font-bold text-xl">
                -${Math.abs(stats.held_lost_loss).toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
