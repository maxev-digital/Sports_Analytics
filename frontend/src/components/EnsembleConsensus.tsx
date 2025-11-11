import React from 'react';
import { EnsembleResult } from '../hooks/useEdgeLab';

interface EnsembleConsensusProps {
  ensemble: EnsembleResult;
  marketLine: number;
}

export function EnsembleConsensus({ ensemble, marketLine }: EnsembleConsensusProps) {
  const hasStrongEdge = (ensemble.edge || 0) >= 3.0;
  const isStrongConsensus = ensemble.consensus_strength === 'STRONG';

  const getConsensusColor = () => {
    switch (ensemble.consensus_strength) {
      case 'STRONG': return 'from-green-600 to-green-700';
      case 'MODERATE': return 'from-yellow-600 to-yellow-700';
      case 'WEAK': return 'from-orange-600 to-orange-700';
      default: return 'from-slate-600 to-slate-700';
    }
  };

  const getRecommendationColor = () => {
    if (ensemble.recommendation === 'OVER') return 'text-green-400';
    if (ensemble.recommendation === 'UNDER') return 'text-red-400';
    return 'text-slate-400';
  };

  return (
    <div className="bg-gradient-to-br from-purple-900/60 via-blue-900/40 to-purple-900/60 border-2 border-purple-500 rounded-lg p-6 shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div>
            <h3 className="text-2xl font-bold text-white">Ensemble Consensus</h3>
            <p className="text-sm text-slate-300">Weighted average of all models</p>
          </div>
        </div>

        {/* Consensus Strength Badge */}
        <div className={`px-4 py-2 bg-gradient-to-r ${getConsensusColor()} text-white rounded-full font-bold text-sm shadow-lg flex items-center gap-2`}>
          <span>{ensemble.consensus_strength} CONSENSUS</span>
        </div>
      </div>

      {/* Main Prediction */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Weighted Average */}
        <div className="bg-slate-900/60 rounded-lg p-6 border-2 border-purple-500">
          <div className="text-sm text-purple-300 mb-2">Ensemble Prediction</div>
          <div className="text-5xl font-bold text-white mb-2 truncate">
            {ensemble.weighted_average?.toFixed(2) || 'N/A'}
          </div>
          <div className="text-sm text-slate-400">Confidence: {((ensemble.confidence || 0) * 100).toFixed(2)}%</div>
          <div className="w-full bg-slate-700 rounded-full h-2 mt-3">
            <div
              className="bg-gradient-to-r from-purple-500 to-blue-500 h-full rounded-full transition-all"
              style={{ width: `${(ensemble.confidence || 0) * 100}%` }}
            />
          </div>
        </div>

        {/* Market Comparison */}
        <div className="bg-slate-900/60 rounded-lg p-6 border-2 border-slate-600">
          <div className="text-sm text-slate-400 mb-2">Market Line</div>
          <div className="text-5xl font-bold text-yellow-300 mb-2 truncate">
            {marketLine?.toFixed(2) || 'N/A'}
          </div>
          <div className="text-sm text-slate-400">
            Difference: <span className={`font-bold ${
              (ensemble.weighted_average || 0) < marketLine ? 'text-red-400' : 'text-green-400'
            }`}>
              {(ensemble.weighted_average || 0) < marketLine ? '-' : '+'}{Math.abs((ensemble.weighted_average || 0) - marketLine).toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Agreement Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-900/40 rounded-lg p-4">
          <div className="text-xs text-slate-400 mb-2">Models Agree</div>
          <div className="flex items-center gap-2">
            <span className="text-3xl font-bold text-green-400">{ensemble.agreement_count || 0}</span>
            <span className="text-sm text-slate-400">/ {(ensemble.agreement_count || 0) + (ensemble.disagreement_count || 0)}</span>
          </div>
        </div>

        <div className="bg-slate-900/40 rounded-lg p-4">
          <div className="text-xs text-slate-400 mb-2">Edge</div>
          <div className="flex items-center gap-2">
            <span className={`text-3xl font-bold truncate ${
              (ensemble.edge || 0) > 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {(ensemble.edge || 0) > 0 ? '+' : ''}{(ensemble.edge || 0).toFixed(2)}%
            </span>
            {hasStrongEdge && (
              <span className="text-xs px-2 py-1 bg-green-900/50 border border-green-500 text-green-300 rounded-full">
                Strong
              </span>
            )}
          </div>
        </div>

        <div className="bg-slate-900/40 rounded-lg p-4">
          <div className="text-xs text-slate-400 mb-2">Kelly Size</div>
          <div className="flex items-center gap-2">
            <span className="text-3xl font-bold text-purple-400 truncate">
              {((ensemble.kelly_fraction || 0) * 100).toFixed(2)}%
            </span>
          </div>
        </div>
      </div>

      {/* Recommendation */}
      {ensemble.recommendation !== 'PASS' && (
        <div className={`rounded-lg p-6 border-2 ${
          ensemble.recommendation === 'OVER'
            ? 'bg-green-900/30 border-green-500'
            : 'bg-red-900/30 border-red-500'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-4xl">
                {ensemble.recommendation === 'OVER' ? '📈' : '📉'}
              </span>
              <div>
                <div className={`text-2xl font-bold ${getRecommendationColor()}`}>
                  {ensemble.recommendation} {marketLine.toFixed(2)}
                </div>
                <div className="text-sm text-slate-300 mt-1">
                  {ensemble.agreement_count === ensemble.agreement_count + ensemble.disagreement_count
                    ? `All ${ensemble.agreement_count} models agree`
                    : `${ensemble.agreement_count} of ${ensemble.agreement_count + ensemble.disagreement_count} models agree`
                  }
                </div>
              </div>
            </div>

            <div className="text-right">
              <div className="text-3xl font-bold text-white truncate">
                {(ensemble.edge || 0) > 0 ? '+' : ''}{(ensemble.edge || 0).toFixed(2)}%
              </div>
              <div className="text-sm text-slate-400">expected value</div>
            </div>
          </div>

          {/* Kelly Sizing Example */}
          <div className="mt-4 p-4 bg-slate-900/50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">Recommended Bet Size</span>
              <span className="text-sm font-bold text-purple-400">
                {((ensemble.kelly_fraction || 0) * 100).toFixed(2)}% of bankroll
              </span>
            </div>
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div>
                <div className="text-slate-500">$1,000 bankroll</div>
                <div className="text-white font-bold">${(1000 * (ensemble.kelly_fraction || 0)).toFixed(0)}</div>
              </div>
              <div>
                <div className="text-slate-500">$5,000 bankroll</div>
                <div className="text-white font-bold">${(5000 * (ensemble.kelly_fraction || 0)).toFixed(0)}</div>
              </div>
              <div>
                <div className="text-slate-500">$10,000 bankroll</div>
                <div className="text-white font-bold">${(10000 * (ensemble.kelly_fraction || 0)).toFixed(0)}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {ensemble.recommendation === 'PASS' && (
        <div className="rounded-lg p-6 bg-slate-800/60 border-2 border-slate-600">
          <div className="flex items-center gap-3">
            <span className="text-3xl">⏸️</span>
            <div>
              <div className="text-xl font-bold text-white">No Bet Recommended</div>
              <div className="text-sm text-slate-400 mt-1">
                Edge too small ({(ensemble.edge || 0).toFixed(2)}%) or models disagree. Wait for better opportunity.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Consensus Visualization */}
      <div className="mt-6 p-4 bg-slate-900/40 rounded-lg">
        <div className="text-sm text-slate-400 mb-3">Agreement Distribution</div>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-8 bg-slate-700 rounded-full overflow-hidden flex">
            <div
              className="bg-gradient-to-r from-green-500 to-green-600 flex items-center justify-center text-white font-bold text-xs"
              style={{ width: `${((ensemble.agreement_count || 0) / ((ensemble.agreement_count || 0) + (ensemble.disagreement_count || 0)) || 0) * 100}%` }}
            >
              {ensemble.agreement_count || 0}
            </div>
            {(ensemble.disagreement_count || 0) > 0 && (
              <div
                className="bg-gradient-to-r from-red-500 to-red-600 flex items-center justify-center text-white font-bold text-xs"
                style={{ width: `${((ensemble.disagreement_count || 0) / ((ensemble.agreement_count || 0) + (ensemble.disagreement_count || 0)) || 0) * 100}%` }}
              >
                {ensemble.disagreement_count || 0}
              </div>
            )}
          </div>
        </div>
        <div className="flex justify-between mt-2 text-xs text-slate-500">
          <span>✓ Agree: {ensemble.agreement_count || 0}</span>
          <span>✗ Disagree: {ensemble.disagreement_count || 0}</span>
        </div>
      </div>
    </div>
  );
}
