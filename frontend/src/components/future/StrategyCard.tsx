import React from 'react';
import { StrategyEnhancement } from '../../data/futureFeatures';

interface StrategyCardProps {
  strategy: StrategyEnhancement;
}

const STATUS_CONFIG = {
  live: {
    color: 'border-green-500 bg-green-950/30',
    badge: 'bg-green-500 text-white',
    label: 'LIVE NOW'
  },
  beta: {
    color: 'border-blue-500 bg-blue-950/30',
    badge: 'bg-blue-500 text-white',
    label: 'BETA'
  },
  q1_2025: {
    color: 'border-purple-500 bg-purple-950/30',
    badge: 'bg-purple-500 text-white',
    label: 'Q1 2025'
  },
  q2_2025: {
    color: 'border-orange-500 bg-orange-950/30',
    badge: 'bg-orange-500 text-white',
    label: 'Q2 2025'
  }
};

const IMPACT_ICONS = {
  game_changer: '🔥🔥🔥',
  high: '🔥🔥',
  medium: '🔥',
  low: '⭐'
};

const IMPACT_LABELS = {
  game_changer: 'Game Changer',
  high: 'High Impact',
  medium: 'Medium Impact',
  low: 'Low Impact'
};

export const StrategyCard: React.FC<StrategyCardProps> = ({ strategy }) => {
  const statusConfig = STATUS_CONFIG[strategy.status];

  return (
    <div className={`rounded-xl p-6 border-2 ${statusConfig.color} backdrop-blur-sm hover:scale-105 transition-all duration-300 relative overflow-hidden`}>
      {/* Status Badge */}
      <div className="absolute top-4 right-4">
        <span className={`text-xs font-bold px-3 py-1 rounded-full ${statusConfig.badge}`}>
          {statusConfig.label}
        </span>
      </div>

      {/* Header */}
      <div className="mb-4 pr-20">
        <div className="text-xs text-slate-400 uppercase mb-1">
          {strategy.category.replace('_', ' ')}
        </div>
        <h3 className="text-xl font-bold text-white mb-2">
          {strategy.name}
        </h3>
        <p className="text-sm text-slate-400">
          {strategy.description}
        </p>
      </div>

      {/* Current Performance */}
      <div className="mb-4 p-4 bg-slate-800/50 rounded-lg">
        <div className="text-xs text-slate-400 mb-2 flex items-center justify-between">
          <span>CURRENT PERFORMANCE</span>
          <span className="text-slate-500">
            {strategy.current.sample_size} bets
          </span>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-2xl font-bold text-white">
              {(strategy.current.win_rate * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-slate-400">Win Rate</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white">
              {(strategy.current.roi * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-slate-400">ROI</div>
          </div>
        </div>
        <div className="mt-3 text-xs text-slate-500">
          Method: {strategy.current.method}
        </div>
      </div>

      {/* Enhanced Performance */}
      <div className="mb-4 p-4 bg-gradient-to-br from-green-900/30 to-blue-900/30 rounded-lg border border-green-500/30">
        <div className="text-xs text-green-400 mb-2 flex items-center justify-between">
          <span>ML-ENHANCED TARGET</span>
          <span className="flex items-center gap-1">
            <span>{IMPACT_ICONS[strategy.impact_score]}</span>
            <span className="text-slate-400">{IMPACT_LABELS[strategy.impact_score]}</span>
          </span>
        </div>
        <div className="grid grid-cols-2 gap-4 mb-3">
          <div>
            <div className="text-2xl font-bold text-green-400">
              {(strategy.enhanced.win_rate * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-slate-400">Win Rate</div>
            <div className="text-xs text-green-400 font-semibold">
              +{strategy.enhanced.improvement.win_rate_pct.toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-400">
              {(strategy.enhanced.roi * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-slate-400">ROI</div>
            <div className="text-xs text-green-400 font-semibold">
              +{strategy.enhanced.improvement.roi_pct.toFixed(1)}%
            </div>
          </div>
        </div>
        <div className="text-xs text-green-300/80">
          {strategy.enhanced.improvement.false_positives_reduction}% fewer false positives
        </div>
      </div>

      {/* ML Models Added */}
      <div className="mb-4">
        <div className="text-xs text-slate-400 mb-2">ML MODELS ADDED</div>
        <div className="flex flex-wrap gap-2">
          {strategy.enhanced.ml_models.map((model, idx) => (
            <span
              key={idx}
              className="text-xs px-2 py-1 rounded bg-slate-700 text-slate-300 border border-slate-600"
            >
              {model}
            </span>
          ))}
        </div>
      </div>

      {/* Features Added */}
      <div>
        <div className="text-xs text-slate-400 mb-2">KEY ENHANCEMENTS</div>
        <ul className="text-xs text-slate-300 space-y-1">
          {strategy.features_added.slice(0, 3).map((feature, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">✓</span>
              <span>{feature}</span>
            </li>
          ))}
          {strategy.features_added.length > 3 && (
            <li className="text-slate-500 italic">
              +{strategy.features_added.length - 3} more enhancements...
            </li>
          )}
        </ul>
      </div>

      {/* Launch Quarter Tag */}
      <div className="mt-4 pt-4 border-t border-slate-700">
        <div className="text-xs text-slate-500">
          Expected Launch: <span className="text-slate-300 font-semibold">{strategy.launch_quarter}</span>
        </div>
      </div>
    </div>
  );
};
