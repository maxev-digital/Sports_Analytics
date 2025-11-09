import React from 'react';
import { ModelResult, ModelId } from '../hooks/useEdgeLab';

interface ModelCardProps {
  model: ModelResult;
  isRunning: boolean;
  isRecommended?: boolean;
  onRun: (modelId: ModelId) => void;
  onViewDetails: (modelId: ModelId) => void;
}

const MODEL_ICONS: Record<ModelId, string> = {
  monte_carlo: 'MC',
  random_forest: 'RF',
  xgboost: 'XGB',
  lightgbm: 'LGBM',
  linear_regression: 'LR'
};

const MODEL_DESCRIPTIONS: Record<ModelId, string> = {
  monte_carlo: '10,000 possession simulations',
  random_forest: 'Best for NBA totals • Handles interactions',
  xgboost: 'Current system default',
  lightgbm: 'Faster than XGBoost • Often better accuracy',
  linear_regression: 'Fast baseline • Interpretable'
};

export function ModelCard({ model, isRunning, isRecommended, onRun, onViewDetails }: ModelCardProps) {
  const icon = MODEL_ICONS[model.model_id];
  const description = MODEL_DESCRIPTIONS[model.model_id];
  const hasResult = model.status === 'success' && model.prediction.total > 0;
  const hasError = model.status === 'error';

  // Determine card styling
  const getCardClasses = () => {
    if (isRecommended) {
      return 'bg-gradient-to-br from-blue-900/60 via-purple-900/40 to-blue-900/60 border-blue-500 shadow-lg shadow-blue-500/20';
    }
    if (hasError) {
      return 'bg-slate-800/60 border-red-500/50';
    }
    if (hasResult) {
      return 'bg-slate-800/60 border-slate-600 hover:border-slate-500';
    }
    return 'bg-slate-800/40 border-slate-700';
  };

  const edge = model.market_analysis?.edge ?? 0;
  const hasEdge = model.market_analysis ? Math.abs(edge) >= 2.0 : false;

  return (
    <div className={`relative rounded-lg border-2 p-4 transition-all ${getCardClasses()}`}>
      {/* Recommended Badge */}
      {isRecommended && (
        <div className="absolute -top-2 -right-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-xs font-bold px-3 py-1 rounded-full shadow-lg flex items-center gap-1">
          <span>RECOMMENDED</span>
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 flex-1">
          <div className="bg-purple-600 text-white font-bold text-xs px-2 py-1 rounded">
            {icon}
          </div>
          <div className="flex-1">
            <h4 className="text-white font-bold text-lg">{model.model_name || model.model_id}</h4>
            <p className="text-xs text-slate-400">{description}</p>
          </div>
        </div>

        {/* Status Indicator */}
        {isRunning && (
          <div className="flex items-center gap-2 px-2 py-1 bg-blue-900/50 border border-blue-500 rounded-full">
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
            <span className="text-xs text-blue-300">Running...</span>
          </div>
        )}

        {hasResult && !isRunning && (
          <div className="flex items-center gap-2 px-2 py-1 bg-green-900/50 border border-green-500 rounded-full">
            <span className="text-xs text-green-300 font-semibold">Complete</span>
          </div>
        )}

        {hasError && !isRunning && (
          <div className="flex items-center gap-2 px-2 py-1 bg-red-900/50 border border-red-500 rounded-full">
            <span className="text-xs text-red-300 font-semibold">Error</span>
          </div>
        )}
      </div>

      {/* Results or Run Button */}
      {!hasResult && !hasError && !isRunning && (
        <div className="mt-4">
          <button
            onClick={() => onRun(model.model_id)}
            className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
          >
            <span>Run {model.model_name || model.model_id}</span>
          </button>
        </div>
      )}

      {hasError && (
        <div className={`mt-3 p-3 rounded ${
          model.error_message?.includes('Live games only')
            ? 'bg-slate-800/60 border border-slate-600'
            : 'bg-red-900/30 border border-red-500'
        }`}>
          <p className={`text-sm flex items-center gap-2 ${
            model.error_message?.includes('Live games only')
              ? 'text-slate-400'
              : 'text-red-300'
          }`}>
            {model.error_message?.includes('Live games only') && (
              <span className="text-lg">🔴</span>
            )}
            {model.error_message || 'Model failed'}
          </p>
          {!model.error_message?.includes('Live games only') && (
            <button
              onClick={() => onRun(model.model_id)}
              className="mt-2 px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-semibold transition-colors"
            >
              {model.error_message ? 'Retry' : 'Run'} {model.model_name || model.model_id}
            </button>
          )}
        </div>
      )}

      {hasResult && !isRunning && (
        <>
          {/* Prediction */}
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-slate-900/60 rounded-lg p-3">
              <div className="text-xs text-slate-400 mb-1">Prediction</div>
              <div className="text-lg font-bold text-white">{model.prediction?.total?.toFixed(2) || '0.00'}</div>
              {model.prediction?.std_dev && (
                <div className="text-xs text-slate-500 mt-1">±{model.prediction.std_dev.toFixed(2)}</div>
              )}
            </div>

            <div className="bg-slate-900/60 rounded-lg p-3">
              <div className="text-xs text-slate-400 mb-1">Confidence</div>
              <div className="text-lg font-bold text-purple-300">
                {((model.prediction?.confidence || 0) * 100).toFixed(2)}%
              </div>
              <div className="w-full bg-slate-700 rounded-full h-1.5 mt-2">
                <div
                  className="bg-purple-500 h-full rounded-full transition-all"
                  style={{ width: `${(model.prediction?.confidence || 0) * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* Market Analysis */}
          {model.market_analysis && (
          <div className="mb-3 p-3 bg-slate-900/40 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-slate-400">vs Market Line</span>
              <span className="text-sm text-white font-semibold">{model.market_analysis.market_line?.toFixed(2) || 'N/A'}</span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`text-sm font-bold ${
                  model.market_analysis?.recommendation === 'OVER' ? 'text-green-400' :
                  model.market_analysis?.recommendation === 'UNDER' ? 'text-red-400' :
                  'text-slate-400'
                }`}>
                  {model.market_analysis?.recommendation || 'PASS'}
                </span>
                {hasEdge && (
                  <span className="text-xs px-2 py-0.5 bg-green-900/50 border border-green-500 text-green-300 rounded-full">
                    +EV
                  </span>
                )}
              </div>

              <div className="text-right">
                <div className={`text-sm font-bold ${
                  edge > 0 ? 'text-green-400' :
                  edge < 0 ? 'text-red-400' :
                  'text-slate-400'
                }`}>
                  {edge > 0 ? '+' : ''}{edge.toFixed(2)}%
                </div>
                <div className="text-xs text-slate-500">edge</div>
              </div>
            </div>

            {/* Probabilities */}
            <div className="mt-3 flex gap-2">
              <div className="flex-1 bg-green-900/30 border border-green-600 rounded p-2">
                <div className="text-xs text-green-400">OVER</div>
                <div className="text-sm font-bold text-green-300">
                  {((model.market_analysis?.probability_over || 0) * 100).toFixed(2)}%
                </div>
              </div>
              <div className="flex-1 bg-red-900/30 border border-red-600 rounded p-2">
                <div className="text-xs text-red-400">UNDER</div>
                <div className="text-sm font-bold text-red-300">
                  {((model.market_analysis?.probability_under || 0) * 100).toFixed(2)}%
                </div>
              </div>
            </div>

            {/* Kelly Sizing */}
            <div className="mt-2 flex items-center justify-between text-xs">
              <span className="text-slate-400">Kelly Size:</span>
              <span className="text-purple-400 font-semibold">
                {((model.market_analysis?.kelly_fraction || 0) * 100).toFixed(2)}% of bankroll
              </span>
            </div>
          </div>
          )}

          {/* Performance Stats */}
          {model.model_performance && (
            <div className="mb-3 grid grid-cols-2 gap-2">
              <div className="bg-slate-900/40 rounded p-2">
                <div className="text-xs text-slate-400">Accuracy</div>
                <div className="text-sm font-bold text-white">
                  {((model.model_performance?.accuracy || 0) * 100).toFixed(2)}%
                </div>
              </div>
              <div className="bg-slate-900/40 rounded p-2">
                <div className="text-xs text-slate-400">MAE</div>
                <div className="text-sm font-bold text-white">
                  {(model.model_performance?.mae || 0).toFixed(2)}
                </div>
              </div>
            </div>
          )}

          {/* Updated Timestamp */}
          <div className="flex items-center justify-between text-xs text-slate-500 mb-3">
            <span>Updated: {getTimeAgo(model.timestamp)}</span>
            <button
              onClick={() => onRun(model.model_id)}
              className="text-blue-400 hover:text-blue-300 transition-colors"
            >
              🔄 Re-run
            </button>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => onViewDetails(model.model_id)}
              className="flex-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded font-semibold text-sm transition-colors"
            >
              👁️ View Details
            </button>
          </div>
        </>
      )}
    </div>
  );
}

function getTimeAgo(timestamp: string): string {
  const now = Date.now();
  const time = new Date(timestamp).getTime();
  const diff = now - time;

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return 'Just now';
}
