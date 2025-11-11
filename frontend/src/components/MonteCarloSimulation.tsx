import React from 'react';

interface MonteCarloSimulationProps {
  gameId: string;
  simulation: {
    status: string;
    game_id: string;
    over_probability: number;
    under_probability: number;
    push_probability: number;
    over_ev: number;
    under_ev: number;
    recommended_bet: 'OVER' | 'UNDER' | 'PASS';
    edge: number;
    kelly_pct: number;
    percentiles: {
      '5th': number;
      '10th': number;
      '25th': number;
      '50th': number;
      '75th': number;
      '90th': number;
      '95th': number;
    };
    mean: number;
    median: number;
    std_dev: number;
    min: number;
    max: number;
    metadata: {
      current_total: number;
      remaining_minutes: number;
      estimated_remaining_possessions: number;
      n_simulations: number;
    };
  };
  teams: {
    home: string;
    away: string;
  };
  marketTotal?: number;
}

export function MonteCarloSimulation({ gameId, simulation, teams, marketTotal }: MonteCarloSimulationProps) {
  const hasEdge = Math.abs(simulation.edge) >= 2.0; // 2%+ edge threshold

  return (
    <div className="bg-gradient-to-br from-slate-800 via-purple-900/30 to-slate-800 border-2 border-purple-500 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🎲</span>
          <div>
            <h3 className="text-xl font-bold text-white">Monte Carlo Simulation</h3>
            <p className="text-xs text-slate-400">
              {simulation.metadata.n_simulations.toLocaleString()} simulations • {teams.away} @ {teams.home}
            </p>
          </div>
        </div>
        {hasEdge && (
          <div className="flex items-center gap-2 px-3 py-1 bg-green-900/40 border border-green-500 rounded-full">
            <span className="text-green-400 text-xs font-bold">+EV DETECTED</span>
            <span className="text-green-300 text-sm font-bold">{simulation.edge.toFixed(1)}%</span>
          </div>
        )}
      </div>

      {/* Main Probability Display */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* OVER */}
        <div className={`relative rounded-lg p-4 border-2 transition-all ${
          simulation.recommended_bet === 'OVER'
            ? 'bg-green-900/40 border-green-500 shadow-lg shadow-green-500/20'
            : 'bg-slate-700/40 border-slate-600'
        }`}>
          <div className="flex items-start justify-between mb-2">
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wide">Over</div>
              <div className="text-2xl font-bold text-white">{marketTotal || 'N/A'}</div>
            </div>
            {simulation.recommended_bet === 'OVER' && (
              <span className="text-lg">✅</span>
            )}
          </div>
          <div className="mt-3">
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-3xl font-bold text-green-300">
                {(simulation.over_probability * 100).toFixed(1)}%
              </span>
              <span className="text-sm text-slate-400">probability</span>
            </div>
            {simulation.over_ev !== 0 && (
              <div className="text-xs text-slate-400 mt-1">
                EV: <span className={simulation.over_ev > 0 ? 'text-green-400 font-semibold' : 'text-red-400'}>
                  {simulation.over_ev > 0 ? '+' : ''}{simulation.over_ev.toFixed(2)}%
                </span>
              </div>
            )}
          </div>
        </div>

        {/* UNDER */}
        <div className={`relative rounded-lg p-4 border-2 transition-all ${
          simulation.recommended_bet === 'UNDER'
            ? 'bg-red-900/40 border-red-500 shadow-lg shadow-red-500/20'
            : 'bg-slate-700/40 border-slate-600'
        }`}>
          <div className="flex items-start justify-between mb-2">
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wide">Under</div>
              <div className="text-2xl font-bold text-white">{marketTotal || 'N/A'}</div>
            </div>
            {simulation.recommended_bet === 'UNDER' && (
              <span className="text-lg">✅</span>
            )}
          </div>
          <div className="mt-3">
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-3xl font-bold text-red-300">
                {(simulation.under_probability * 100).toFixed(1)}%
              </span>
              <span className="text-sm text-slate-400">probability</span>
            </div>
            {simulation.under_ev !== 0 && (
              <div className="text-xs text-slate-400 mt-1">
                EV: <span className={simulation.under_ev > 0 ? 'text-green-400 font-semibold' : 'text-red-400'}>
                  {simulation.under_ev > 0 ? '+' : ''}{simulation.under_ev.toFixed(2)}%
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Prediction Stats */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        <div className="bg-slate-700/60 rounded p-3">
          <div className="text-xs text-slate-400 mb-1">Current Total</div>
          <div className="text-lg font-bold text-white">{simulation.metadata.current_total}</div>
        </div>
        <div className="bg-slate-700/60 rounded p-3">
          <div className="text-xs text-slate-400 mb-1">Mean Projection</div>
          <div className="text-lg font-bold text-purple-300">{simulation.mean.toFixed(1)}</div>
        </div>
        <div className="bg-slate-700/60 rounded p-3">
          <div className="text-xs text-slate-400 mb-1">Median</div>
          <div className="text-lg font-bold text-blue-300">{simulation.median.toFixed(1)}</div>
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
              style={{ width: `${marketTotal ? (simulation.percentiles['25th'] / marketTotal) * 100 : 50}%` }}
            />
            {marketTotal && (
              <div
                className="absolute top-0 left-0 h-full w-1 bg-yellow-400"
                style={{ left: `${(marketTotal / 300) * 100}%` }}
              />
            )}
          </div>
          <span className="text-sm text-white font-semibold w-16 text-right">{simulation.percentiles['25th'].toFixed(1)}</span>
        </div>

        {/* 50th Percentile (Median) */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 w-16">50%</span>
          <div className="flex-1 bg-slate-700 rounded-full h-3 relative overflow-hidden">
            <div
              className="bg-gradient-to-r from-purple-500 to-purple-600 h-full rounded-full transition-all duration-500"
              style={{ width: `${marketTotal ? (simulation.percentiles['50th'] / marketTotal) * 100 : 50}%` }}
            />
            {marketTotal && (
              <div
                className="absolute top-0 left-0 h-full w-1 bg-yellow-400"
                style={{ left: `${(marketTotal / 300) * 100}%` }}
              />
            )}
          </div>
          <span className="text-sm text-white font-semibold w-16 text-right">{simulation.percentiles['50th'].toFixed(1)}</span>
        </div>

        {/* 75th Percentile */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 w-16">75%</span>
          <div className="flex-1 bg-slate-700 rounded-full h-3 relative overflow-hidden">
            <div
              className="bg-gradient-to-r from-orange-500 to-orange-600 h-full rounded-full transition-all duration-500"
              style={{ width: `${marketTotal ? (simulation.percentiles['75th'] / marketTotal) * 100 : 50}%` }}
            />
            {marketTotal && (
              <div
                className="absolute top-0 left-0 h-full w-1 bg-yellow-400"
                style={{ left: `${(marketTotal / 300) * 100}%` }}
              />
            )}
          </div>
          <span className="text-sm text-white font-semibold w-16 text-right">{simulation.percentiles['75th'].toFixed(1)}</span>
        </div>
      </div>

      {/* Kelly Criterion & Recommendation */}
      {simulation.recommended_bet !== 'PASS' && (
        <div className="bg-gradient-to-r from-purple-900/60 to-blue-900/60 rounded-lg p-4 border border-purple-500/50">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">Recommended Bet</div>
              <div className="text-2xl font-bold text-white">
                {simulation.recommended_bet} {marketTotal}
              </div>
              <div className="text-sm text-slate-300 mt-1">
                Edge: <span className="text-green-400 font-semibold">{simulation.edge.toFixed(2)}%</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">Kelly Bet Size</div>
              <div className="text-2xl font-bold text-purple-300">{simulation.kelly_pct.toFixed(1)}%</div>
              <div className="text-xs text-slate-400 mt-1">of bankroll</div>
            </div>
          </div>
        </div>
      )}

      {/* Additional Stats */}
      <div className="mt-4 grid grid-cols-3 gap-3 text-xs">
        <div className="bg-slate-800/60 rounded p-2">
          <span className="text-slate-400">Remaining:</span> <span className="text-white font-semibold">{simulation.metadata.remaining_minutes.toFixed(1)} min</span>
        </div>
        <div className="bg-slate-800/60 rounded p-2">
          <span className="text-slate-400">Min:</span> <span className="text-white font-semibold">{simulation.min.toFixed(1)}</span>
        </div>
        <div className="bg-slate-800/60 rounded p-2">
          <span className="text-slate-400">Max:</span> <span className="text-white font-semibold">{simulation.max.toFixed(1)}</span>
        </div>
      </div>
    </div>
  );
}
