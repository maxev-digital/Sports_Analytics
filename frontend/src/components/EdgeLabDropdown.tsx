import React, { useState, useEffect } from 'react';
import { useEdgeLab, ModelId } from '../hooks/useEdgeLab';
import { ModelCard } from './ModelCard';
import { EnsembleConsensus } from './EnsembleConsensus';

interface EdgeLabDropdownProps {
  gameId: string;
  marketLine: number;
  sport?: string;
  betType?: string;
  gameData?: any;
}

export function EdgeLabDropdown({ gameId, marketLine, sport = 'nba', betType = 'totals', gameData }: EdgeLabDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);

  const {
    modelResults,
    runningModels,
    comparison,
    error,
    runModel,
    runAllModels,
    runComparison,
    loadCachedResults,
    clearResults,
    hasResults,
    isRunning
  } = useEdgeLab(gameId, gameData, false, sport);

  // Load cached results on mount
  useEffect(() => {
    loadCachedResults();
  }, [loadCachedResults]);

  // Get available models for this sport/bet type
  const getAvailableModels = (): ModelId[] => {
    if (sport === 'nba' && betType === 'totals') {
      return ['monte_carlo', 'random_forest', 'xgboost', 'lightgbm', 'linear_regression'];
    }
    if (sport === 'ncaab' && betType === 'totals') {
      return ['random_forest', 'xgboost', 'lightgbm', 'linear_regression'];
    }
    // For other sports/bet types, return subset of available models
    return ['xgboost', 'linear_regression'];
  };

  const availableModels = getAvailableModels();

  // Determine best model based on results
  const getBestModelId = (): ModelId | null => {
    if (!comparison?.best_model?.id) {
      // Fallback: find model with highest edge
      const modelsWithResults = availableModels.filter(id => modelResults[id]?.status === 'success');
      if (modelsWithResults.length === 0) return null;

      const best = modelsWithResults.reduce((best, current) => {
        const currentEdge = Math.abs(modelResults[current]?.market_analysis?.edge || 0);
        const bestEdge = Math.abs(modelResults[best]?.market_analysis?.edge || 0);
        return currentEdge > bestEdge ? current : best;
      });

      return best;
    }
    return comparison.best_model.id;
  };

  const bestModelId = getBestModelId();

  const handleRunAllModels = async () => {
    // Just run comparison - it runs all models and returns them
    await runComparison(false);
  };

  const handleRunModel = async (modelId: ModelId) => {
    await runModel(modelId, false); // false = real API, true = mock data
  };

  const handleViewDetails = (modelId: ModelId) => {
    // TODO: Open detailed model view modal
    console.log('View details for:', modelId);
  };

  const hasAnyResults = availableModels.some(id => modelResults[id]);
  const allModelsRun = availableModels.every(id => modelResults[id]?.status === 'success');
  const completedCount = Object.values(modelResults).filter(r => r?.status === 'success').length;

  return (
    <div className="px-4 pb-4">
      {/* Edge Lab Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg font-bold text-sm transition-all shadow-lg hover:shadow-xl flex items-center justify-between group"
      >
        <div className="flex items-center gap-2">
          <span>Edge Lab - Multi-Model Predictions</span>
          {hasResults && !isRunning && (
            <span className="px-2 py-0.5 bg-white bg-opacity-20 rounded-full text-xs font-bold">
              {completedCount} / {availableModels.length} Complete
            </span>
          )}
          {isRunning && (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          )}
        </div>
        <svg
          className={`w-5 h-5 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expandable Panel */}
      {isOpen && (
        <div className="mt-3 bg-slate-900 border-2 border-purple-600 rounded-lg p-4 max-h-[600px] overflow-y-auto">
          {/* Header */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xl font-bold text-white">
                {availableModels.length} Prediction Models
              </h3>
              <div className="flex items-center gap-2">
                {!allModelsRun && (
                  <button
                    onClick={handleRunAllModels}
                    disabled={isRunning}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded font-semibold text-xs transition-colors flex items-center gap-2"
                  >
                    {isRunning ? (
                      <>
                        <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Running...</span>
                      </>
                    ) : (
                      <>
                        <span>Run All</span>
                      </>
                    )}
                  </button>
                )}
                {hasAnyResults && (
                  <button
                    onClick={clearResults}
                    className="px-2 py-1.5 bg-red-600/80 hover:bg-red-700 text-white rounded text-xs transition-colors"
                    title="Clear all results"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>
            <p className="text-sm text-slate-400">
              Run models individually or all at once • {sport.toUpperCase()} {betType} • Market: {marketLine.toFixed(2)}
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-500 rounded-lg">
              <div className="flex items-start gap-2">
                <div>
                  <p className="font-bold text-red-200 text-sm mb-1">Error</p>
                  <p className="text-red-300 text-sm">{error}</p>
                </div>
              </div>
            </div>
          )}
            {/* Ensemble Consensus - Show at top when available */}
            {comparison?.ensemble && (
              <EnsembleConsensus
                ensemble={comparison.ensemble}
                marketLine={marketLine}
              />
            )}

            {/* Info Card - Show when no results yet */}
            {!hasAnyResults && !isRunning && (
              <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 border-2 border-slate-600 rounded-lg p-8 text-center">
                <h4 className="text-2xl font-bold text-white mb-3">Welcome to Edge Lab</h4>
                <p className="text-slate-300 mb-6 max-w-2xl mx-auto">
                  Run advanced ML models and Monte Carlo simulations to find betting edges.
                  Each model analyzes the game from different angles to give you the most confident predictions.
                </p>
                <button
                  onClick={handleRunAllModels}
                  className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg font-bold text-lg transition-all shadow-lg shadow-purple-500/30 flex items-center gap-3 mx-auto"
                >
                  <span>Run All {availableModels.length} Models</span>
                </button>
              </div>
            )}

            {/* Model Cards Grid */}
            {hasAnyResults && (
              <>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-base font-bold text-white">Models</h4>
                  <p className="text-xs text-slate-400">
                    {Object.values(modelResults).filter(r => r?.status === 'success').length} of {availableModels.length} complete
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {availableModels.map((modelId) => {
                    const result = modelResults[modelId];
                    const isModelRunning = runningModels.has(modelId);
                    const isRecommended = modelId === bestModelId;

                    // If no result yet, show placeholder
                    if (!result) {
                      return (
                        <ModelCard
                          key={modelId}
                          model={{
                            model_id: modelId,
                            model_name: getModelName(modelId),
                            prediction: { total: 0, confidence: 0 },
                            market_analysis: {
                              market_line: marketLine,
                              edge: 0,
                              recommendation: 'PASS',
                              probability_over: 0,
                              probability_under: 0,
                              kelly_fraction: 0
                            },
                            timestamp: new Date().toISOString(),
                            status: 'error',
                            error_message: ''
                          }}
                          isRunning={isModelRunning}
                          isRecommended={false}
                          onRun={handleRunModel}
                          onViewDetails={handleViewDetails}
                        />
                      );
                    }

                    return (
                      <ModelCard
                        key={modelId}
                        model={result}
                        isRunning={isModelRunning}
                        isRecommended={isRecommended}
                        onRun={handleRunModel}
                        onViewDetails={handleViewDetails}
                      />
                    );
                  })}
                </div>
              </>
            )}

            {/* Best Model Recommendation */}
            {comparison?.best_model && (
              <div className="mt-4 bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-500 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">⭐</span>
                  <div className="flex-1">
                    <h4 className="text-white font-semibold text-sm mb-1">Recommended Model</h4>
                    <p className="text-blue-300 text-xs">
                      <span className="font-semibold">{getModelName(comparison.best_model.id)}</span>
                      {' • '}
                      {comparison.best_model.reason}
                    </p>
                  </div>
                </div>
              </div>
            )}

          {/* Footer Info */}
          <div className="mt-4 pt-4 border-t border-slate-700">
            <div className="flex items-start gap-2 text-xs text-slate-400">
              <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <p>
                Run models individually or all at once. Ensemble consensus combines all models with weighted averaging.
                All predictions use Kelly Criterion for optimal bet sizing.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function getModelName(modelId: ModelId): string {
  const names: Record<ModelId, string> = {
    monte_carlo: 'Monte Carlo Simulation',
    random_forest: 'Random Forest',
    xgboost: 'XGBoost',
    lightgbm: 'LightGBM',
    linear_regression: 'Linear Regression'
  };
  return names[modelId];
}
