import React from 'react';

interface MonteCarloSimulationProps {
  gameId: string;
  simulation: {
    current_total: number;
    simulations_run: number;
    mean_final_total: number;
    median_final_total: number;
    std_dev: number;
    percentiles: {
      p10: number;
      p25: number;
      p50: number;
      p75: number;
      p90: number;
    };
    market_analysis: {
      market_line: number;
      over_probability: number;
      under_probability: number;
      implied_over_odds: number;
      market_over_odds: number;
      edge: number;
      recommendation: 'OVER' | 'UNDER' | 'PASS';
      kelly_fraction: number;
    };
    distribution_buckets: Record<string, number>;
    confidence_intervals: {
      '90%': [number, number];
      '95%': [number, number];
      '99%': [number, number];
    };
  };
  teams: {
    home: string;
    away: string;
  };
}

export function MonteCarloSimulation({ gameId, simulation, teams }: MonteCarloSimulationProps) {
  const { market_analysis, percentiles } = simulation;
  const hasEdge = Math.abs(market_analysis.edge) >= 2.0; // 2%+ edge threshold

  return (
    <div className="bg-gradient-to-br from-slate-800 via-purple-900/30 to-slate-800 border-2 border-purple-500 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🎲</span>
          <div>
            <h3 className="text-xl font-bold text-white">Monte Carlo Simulation</h3>
            <p className="text-xs text-slate-400">
              {simulation.simulations_run.toLocaleString()} simulations • {teams.away} @ {teams.home}
            </p>
          </div>
        </div>
        {hasEdge && (
          <div className="flex items-center gap-2 px-3 py-1 bg-green-900/40 border border-green-500 rounded-full">
            <span className="text-green-400 text-xs font-bold">+EV DETECTED</span>
            <span className="text-green-300 text-sm font-bold">{market_analysis.edge.toFixed(1)}%</span>
          </div>
        )}
      </div>

      {/* Main Probability Display */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* OVER */}
        <div className={`relative rounded-lg p-4 border-2 transition-all ${
          market_analysis.recommendation === 'OVER'
            ? 'bg-green-900/40 border-green-500 shadow-lg shadow-green-500/20'
            : 'bg-slate-700/40 border-slate-600'
        }`}>
          <div className="flex items-start justify-between mb-2">
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wide">Over</div>
              <div className="text-2xl font-bold text-white">{market_analysis.market_line}</div>
            </div>
            {market_analysis.recommendation === 'OVER' && (
              <span className="text-lg">✅</span>
            )}
          </div>
          <div className="mt-3">
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-3xl font-bold text-green-300">
                {(market_analysis.over_probability * 100).toFixed(1)}%
              </span>
              <span className="text-sm text-slate-400">probability</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span>True odds:</span>
              <span className="text-green-400 font-semibold">
                {market_analysis.implied_over_odds > 0 ? '+' : ''}{market_analysis.implied_over_odds}
              </span>
              <span className="text-slate-500">vs</span>
              <span className="text-white">{market_analysis.market_over_odds}</span>
            </div>
          </div>
        </div>

        {/* UNDER */}
        <div className={`relative rounded-lg p-4 border-2 transition-all ${
          market_analysis.recommendation === 'UNDER'
            ? 'bg-red-900/40 border-red-500 shadow-lg shadow-red-500/20'
            : 'bg-slate-700/40 border-slate-600'
        }`}>
          <div className="flex items-start justify-between mb-2">
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wide">Under</div>
              <div className="text-2xl font-bold text-white">{market_analysis.market_line}</div>
            </div>
            {market_analysis.recommendation === 'UNDER' && (
              <span className="text-lg">✅</span>
            )}
          </div>
          <div className="mt-3">
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-3xl font-bold text-red-300">
                {(market_analysis.under_probability * 100).toFixed(1)}%
              </span>
              <span className="text-sm text-slate-400">probability</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span>True odds:</span>
              <span className="text-red-400 font-semibold">
                {market_analysis.implied_over_odds > 0 ? '-' : '+'}{Math.abs(market_analysis.implied_over_odds)}
              </span>
              <span className="text-slate-500">vs</span>
              <span className="text-white">-110</span>
            </div>
          </div>
        </div>
      </div>

      {/* Prediction Stats */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        <div className="bg-slate-700/60 rounded p-3">
          <div className="text-xs text-slate-400 mb-1">Current Total</div>
          <div className="text-lg font-bold text-white">{simulation.current_total}</div>
        </div>
        <div className="bg-slate-700/60 rounded p-3">
          <div className="text-xs text-slate-400 mb-1">Mean Projection</div>
          <div className="text-lg font-bold text-purple-300">{simulation.mean_final_total.toFixed(1)}</div>
        </div>
        <div className="bg-slate-700/60 rounded p-3">
          <div className="text-xs text-slate-400 mb-1">Median</div>
          <div className="text-lg font-bold text-blue-300">{simulation.median_final_total.toFixed(1)}</div>
        </div>
        <div className="bg-slate-700/60 rounded p-3">
          <div className="text-xs text-slate-400 mb-1">Std Dev</div>
          <div className="text-lg font-bold text-slate-300">{simulation.std_dev.toFixed(1)}</div>
        </div>
      </div>

      {/* Confidence Intervals */}
      <div className="space-y-3 mb-6">
        <div className="text-sm font-semibold text-slate-300 mb-2">Confidence Intervals</div>

        {/* 25th Percentile */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 w-16">25%</span>
          <div className="flex-1 bg-slate-700 rounded-full h-3 relative overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-500 to-blue-600 h-full rounded-full transition-all duration-500"
              style={{ width: `${(percentiles.p25 / market_analysis.market_line) * 100}%` }}
            />
            <div
              className="absolute top-0 left-0 h-full w-1 bg-yellow-400"
              style={{ left: `${(market_analysis.market_line / 300) * 100}%` }}
            />
          </div>
          <span className="text-sm text-white font-semibold w-16 text-right">{percentiles.p25.toFixed(1)}</span>
        </div>

        {/* 50th Percentile (Median) */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 w-16">50%</span>
          <div className="flex-1 bg-slate-700 rounded-full h-3 relative overflow-hidden">
            <div
              className="bg-gradient-to-r from-purple-500 to-purple-600 h-full rounded-full transition-all duration-500"
              style={{ width: `${(percentiles.p50 / market_analysis.market_line) * 100}%` }}
            />
            <div
              className="absolute top-0 left-0 h-full w-1 bg-yellow-400"
              style={{ left: `${(market_analysis.market_line / 300) * 100}%` }}
            />
          </div>
          <span className="text-sm text-white font-semibold w-16 text-right">{percentiles.p50.toFixed(1)}</span>
        </div>

        {/* 75th Percentile */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 w-16">75%</span>
          <div className="flex-1 bg-slate-700 rounded-full h-3 relative overflow-hidden">
            <div
              className="bg-gradient-to-r from-orange-500 to-orange-600 h-full rounded-full transition-all duration-500"
              style={{ width: `${(percentiles.p75 / market_analysis.market_line) * 100}%` }}
            />
            <div
              className="absolute top-0 left-0 h-full w-1 bg-yellow-400"
              style={{ left: `${(market_analysis.market_line / 300) * 100}%` }}
            />
          </div>
          <span className="text-sm text-white font-semibold w-16 text-right">{percentiles.p75.toFixed(1)}</span>
        </div>

        <div className="flex items-center gap-2 text-xs text-yellow-400 mt-2">
          <div className="w-1 h-3 bg-yellow-400" />
          <span>Market Line ({market_analysis.market_line})</span>
        </div>
      </div>

      {/* Recommendation Card */}
      {market_analysis.recommendation !== 'PASS' && (
        <div className={`rounded-lg p-4 border-2 ${
          market_analysis.recommendation === 'OVER'
            ? 'bg-green-900/30 border-green-500'
            : 'bg-red-900/30 border-red-500'
        }`}>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-2xl">
                  {market_analysis.recommendation === 'OVER' ? '📈' : '📉'}
                </span>
                <div>
                  <div className="text-lg font-bold text-white">
                    Recommended: {market_analysis.recommendation} {market_analysis.market_line}
                  </div>
                  <div className="text-sm text-slate-300">
                    {(market_analysis.edge > 0 ? market_analysis.over_probability : market_analysis.under_probability) * 100}% probability
                    • {market_analysis.edge.toFixed(1)}% edge
                  </div>
                </div>
              </div>

              {/* Kelly Criterion */}
              <div className="flex items-center gap-3 mt-3 p-3 bg-slate-900/50 rounded">
                <div className="flex-1">
                  <div className="text-xs text-slate-400 mb-1">Kelly Criterion Bet Size</div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xl font-bold text-green-300">
                      {(market_analysis.kelly_fraction * 100).toFixed(1)}%
                    </span>
                    <span className="text-xs text-slate-400">of bankroll</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-400 mb-1">Example: $5,000 bankroll</div>
                  <div className="text-lg font-bold text-white">
                    ${(5000 * market_analysis.kelly_fraction).toFixed(0)} bet
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {market_analysis.recommendation === 'PASS' && (
        <div className="rounded-lg p-4 bg-slate-700/40 border-2 border-slate-600">
          <div className="flex items-center gap-2">
            <span className="text-2xl">⏸️</span>
            <div>
              <div className="text-lg font-bold text-white">No Bet Recommended</div>
              <div className="text-sm text-slate-400">
                Edge too small ({market_analysis.edge.toFixed(1)}%). Wait for better opportunity.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 90% Confidence Interval */}
      <div className="mt-4 p-3 bg-slate-900/50 rounded border border-slate-700">
        <div className="text-xs text-slate-400 mb-2">90% Confidence Interval</div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-300">
            {simulation.confidence_intervals['90%'][0].toFixed(1)}
          </span>
          <span className="text-xs text-slate-500">to</span>
          <span className="text-sm text-slate-300">
            {simulation.confidence_intervals['90%'][1].toFixed(1)}
          </span>
        </div>
        <div className="text-xs text-slate-500 mt-1">
          90% of simulations finish within this range
        </div>
      </div>
    </div>
  );
}
