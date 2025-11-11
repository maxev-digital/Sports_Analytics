import { useState, useCallback } from 'react';
import { getApiUrl } from '../config';

export type ModelId =
  | 'monte_carlo'
  | 'random_forest'
  | 'xgboost'
  | 'lightgbm'
  | 'linear_regression';

export interface ModelResult {
  model_id: ModelId;
  model_name: string;
  prediction: {
    total: number;
    confidence: number;
    std_dev?: number;
  };
  market_analysis: {
    market_line: number;
    edge: number;
    recommendation: 'OVER' | 'UNDER' | 'PASS';
    probability_over: number;
    probability_under: number;
    kelly_fraction: number;
  };
  model_performance?: {
    mae: number;
    rmse: number;
    accuracy: number;
    games_trained: number;
  };
  feature_importance?: Record<string, number>;
  timestamp: string;
  status: 'success' | 'error';
  error_message?: string;
}

export interface EnsembleResult {
  weighted_average: number;
  confidence: number;
  recommendation: 'OVER' | 'UNDER' | 'PASS';
  consensus_strength: 'STRONG' | 'MODERATE' | 'WEAK';
  agreement_count: number;
  disagreement_count: number;
  edge: number;
  kelly_fraction: number;
}

export interface ComparisonResult {
  game_id: string;
  market_line: number;
  models: Record<ModelId, ModelResult>;
  ensemble: EnsembleResult;
  best_model: {
    id: ModelId;
    reason: string;
  };
}

interface ModelCache {
  result: ModelResult;
  timestamp: number;
  ttl: number;
}

const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

interface TeamStats {
  pace: number;
  off_rating: number;
  def_rating: number;
  rest_days: number;
}

interface GameData {
  game_id: string;
  home_team: string;
  away_team: string;
  home_stats: TeamStats;
  away_stats: TeamStats;
  market_total: number;
  sport?: string;
  // Live game fields
  is_live?: boolean;
  current_score?: number;
  quarter?: number;
  time_remaining?: string;
}

export function useEdgeLab(gameId: string, gameData?: GameData, isLive: boolean = false, sport: string = 'nba') {
  const [modelResults, setModelResults] = useState<Record<ModelId, ModelResult>>({} as Record<ModelId, ModelResult>);
  const [runningModels, setRunningModels] = useState<Set<ModelId>>(new Set());
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Cache management
  const getCachedResult = useCallback((modelId: ModelId): ModelResult | null => {
    // For live games, include current_score in cache key so cache updates as game progresses
    const liveGameSuffix = isLive && gameData?.current_score
      ? `_live_${gameData.current_score}`
      : '';
    const cacheKey = `edgelab_${gameId}_${modelId}${liveGameSuffix}`;
    const cached = localStorage.getItem(cacheKey);

    if (!cached) return null;

    try {
      const cacheData: ModelCache = JSON.parse(cached);
      const age = Date.now() - cacheData.timestamp;

      if (age < cacheData.ttl) {
        return cacheData.result;
      }

      // Expired, remove from cache
      localStorage.removeItem(cacheKey);
      return null;
    } catch {
      return null;
    }
  }, [gameId, isLive, gameData]);

  const setCachedResult = useCallback((modelId: ModelId, result: ModelResult) => {
    // For live games, include current_score in cache key so cache updates as game progresses
    const liveGameSuffix = isLive && gameData?.current_score
      ? `_live_${gameData.current_score}`
      : '';
    const cacheKey = `edgelab_${gameId}_${modelId}${liveGameSuffix}`;
    const cacheData: ModelCache = {
      result,
      timestamp: Date.now(),
      ttl: isLive ? 30000 : CACHE_TTL  // 30s for live games, 5min for pregame
    };
    localStorage.setItem(cacheKey, JSON.stringify(cacheData));
  }, [gameId, isLive, gameData]);

  // Load cached results on mount
  const loadCachedResults = useCallback(() => {
    const modelIds: ModelId[] = ['monte_carlo', 'random_forest', 'xgboost', 'lightgbm', 'linear_regression'];
    const cached: Record<ModelId, ModelResult> = {} as any;

    modelIds.forEach(id => {
      const result = getCachedResult(id);
      // Validate cached result has required fields (model_name, model_id)
      if (result && result.model_name && result.model_id) {
        cached[id] = result;
      } else if (result) {
        // Old format or invalid data - clear from cache
        const liveGameSuffix = isLive && gameData?.current_score
          ? `_live_${gameData.current_score}`
          : '';
        const cacheKey = `edgelab_${gameId}_${id}${liveGameSuffix}`;
        localStorage.removeItem(cacheKey);
      }
    });

    if (Object.keys(cached).length > 0) {
      setModelResults(cached);
    }
  }, [getCachedResult, gameId, isLive, gameData]);

  // Run a single model
  const runModel = useCallback(async (modelId: ModelId, useMock: boolean = false) => {
    // Guard against undefined modelId
    if (!modelId) {
      console.error('❌ runModel called with undefined modelId');
      return;
    }

    // Monte Carlo requires live game data - skip for pregame
    if (modelId === 'monte_carlo' && !isLive) {
      const unavailableResult: ModelResult = {
        model_id: modelId,
        model_name: getModelName(modelId),
        prediction: { total: 0, confidence: 0 },
        market_analysis: {
          market_line: 0,
          edge: 0,
          recommendation: 'PASS',
          probability_over: 0,
          probability_under: 0,
          kelly_fraction: 0
        },
        timestamp: new Date().toISOString(),
        status: 'error',
        error_message: 'Live games only - Monte Carlo requires current game state'
      };
      setModelResults(prev => ({ ...prev, [modelId]: unavailableResult }));
      return unavailableResult;
    }

    setRunningModels(prev => new Set(prev).add(modelId));
    setError(null);

    try {
      if (useMock) {
        // Mock data for testing
        await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate API delay

        const mockResult: ModelResult = {
          model_id: modelId,
          model_name: getModelName(modelId),
          prediction: {
            total: 226.0 + (Math.random() * 4 - 2),
            confidence: 0.65 + Math.random() * 0.15,
            std_dev: 3.0 + Math.random() * 2
          },
          market_analysis: {
            market_line: 228.5,
            edge: Math.random() * 6 - 1,
            recommendation: Math.random() > 0.5 ? 'UNDER' : 'OVER',
            probability_over: 0.45 + Math.random() * 0.1,
            probability_under: 0.45 + Math.random() * 0.1,
            kelly_fraction: 0.02 + Math.random() * 0.03
          },
          model_performance: {
            mae: 7.5 + Math.random() * 2,
            rmse: 9.5 + Math.random() * 2,
            accuracy: 0.6 + Math.random() * 0.1,
            games_trained: Math.floor(1000 + Math.random() * 500)
          },
          timestamp: new Date().toISOString(),
          status: 'success'
        };

        setModelResults(prev => ({ ...prev, [modelId]: mockResult }));
        setCachedResult(modelId, mockResult);
        return mockResult;
      }

      // Real API call
      // Convert underscores to hyphens for API endpoint
      const apiModelId = modelId.replace(/_/g, '-');
      const endpoint = modelId === 'monte_carlo'
        ? 'simulation/monte-carlo'
        : `models/${apiModelId}/predict`;

      const url = getApiUrl(endpoint);

      // Use provided gameData or create mock data
      const requestBody = gameData || {
        game_id: gameId,
        home_team: "Team A",
        away_team: "Team B",
        home_stats: {
          pace: 100,
          off_rating: 110,
          def_rating: 108,
          rest_days: 1
        },
        away_stats: {
          pace: 98,
          off_rating: 108,
          def_rating: 110,
          rest_days: 2
        },
        market_total: 220,
        sport: sport
      };

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`Model prediction failed: ${response.statusText}`);
      }

      const result: ModelResult = await response.json();

      setModelResults(prev => ({ ...prev, [modelId]: result }));
      setCachedResult(modelId, result);

      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Model prediction failed';
      console.error(`❌ ${modelId} error:`, errorMessage);

      const errorResult: ModelResult = {
        model_id: modelId,
        model_name: getModelName(modelId),
        prediction: { total: 0, confidence: 0 },
        market_analysis: {
          market_line: 0,
          edge: 0,
          recommendation: 'PASS',
          probability_over: 0,
          probability_under: 0,
          kelly_fraction: 0
        },
        timestamp: new Date().toISOString(),
        status: 'error',
        error_message: errorMessage
      };

      setModelResults(prev => ({ ...prev, [modelId]: errorResult }));
      setError(errorMessage);

      return errorResult;
    } finally {
      setRunningModels(prev => {
        const next = new Set(prev);
        next.delete(modelId);
        return next;
      });
    }
  }, [gameId, gameData, isLive, sport, getCachedResult, setCachedResult]);

  // Run all models
  const runAllModels = useCallback(async (useMock: boolean = false) => {
    const modelIds: ModelId[] = ['monte_carlo', 'random_forest', 'xgboost', 'lightgbm', 'linear_regression'];

    const results = await Promise.all(
      modelIds.map(id => runModel(id, useMock))
    );

    return results;
  }, [runModel]);

  // Run comparison endpoint
  const runComparison = useCallback(async (useMock: boolean = false) => {
    setError(null);

    try {
      if (useMock) {
        // Mock comparison
        await runAllModels(true);

        const mockComparison: ComparisonResult = {
          game_id: gameId,
          market_line: 228.5,
          models: modelResults as Record<ModelId, ModelResult>,
          ensemble: {
            weighted_average: 226.2,
            confidence: 0.82,
            recommendation: 'UNDER',
            consensus_strength: 'STRONG',
            agreement_count: 5,
            disagreement_count: 0,
            edge: 3.4,
            kelly_fraction: 0.034
          },
          best_model: {
            id: 'random_forest',
            reason: 'Highest confidence with strong edge'
          }
        };

        setComparison(mockComparison);
        return mockComparison;
      }

      // Real API call
      const url = getApiUrl('models/compare-all');

      // Use provided gameData or create mock data
      const requestBody = gameData || {
        game_id: gameId,
        home_team: "Team A",
        away_team: "Team B",
        home_stats: {
          pace: 100,
          off_rating: 110,
          def_rating: 108,
          rest_days: 1
        },
        away_stats: {
          pace: 98,
          off_rating: 108,
          def_rating: 110,
          rest_days: 2
        },
        market_total: 220,
        sport: sport
      };

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`Comparison failed: ${response.statusText}`);
      }

      const result: ComparisonResult = await response.json();

      setModelResults(result.models);
      setComparison(result);

      // Cache all model results
      Object.entries(result.models).forEach(([id, modelResult]) => {
        setCachedResult(id as ModelId, modelResult);
      });

      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Comparison failed';
      console.error('❌ Comparison error:', errorMessage);
      setError(errorMessage);
      return null;
    }
  }, [gameId, gameData, sport, modelResults, runAllModels, setCachedResult]);

  // Clear results
  const clearResults = useCallback(() => {
    setModelResults({} as Record<ModelId, ModelResult>);
    setComparison(null);
    setError(null);

    // Clear cache
    const modelIds: ModelId[] = ['monte_carlo', 'random_forest', 'xgboost', 'lightgbm', 'linear_regression'];
    modelIds.forEach(id => {
      const cacheKey = `edgelab_${gameId}_${id}`;
      localStorage.removeItem(cacheKey);
    });
  }, [gameId]);

  return {
    modelResults,
    runningModels,
    comparison,
    error,
    runModel,
    runAllModels,
    runComparison,
    loadCachedResults,
    clearResults,
    hasResults: Object.keys(modelResults).length > 0,
    isRunning: runningModels.size > 0
  };
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
