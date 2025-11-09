import React, { useEffect } from 'react';
import { MonteCarloSimulation } from './MonteCarloSimulation';
import { useMonteCarloSimulation } from '../hooks/useMonteCarloSimulation';

interface SimulationModalProps {
  isOpen: boolean;
  onClose: () => void;
  game: {
    state: {
      id: string;
      home_team: string;
      away_team: string;
      home_score?: number;
      away_score?: number;
      period?: string;
      time_remaining?: string;
      status: 'live' | 'upcoming';
    };
    markets?: {
      totals?: {
        over_under: number;
      };
    };
  };
}

export function SimulationModal({ isOpen, onClose, game }: SimulationModalProps) {
  const { simulation, loading, error, runSimulation, reset } = useMonteCarloSimulation();

  useEffect(() => {
    if (isOpen && !simulation && !loading) {
      // Auto-run simulation when modal opens
      const currentState = game.state.status === 'live' && game.state.home_score !== undefined
        ? {
            quarter: parseInt(game.state.period?.replace(/[^0-9]/g, '') || '1'),
            time_remaining: game.state.time_remaining || '12:00',
            home_score: game.state.home_score || 0,
            away_score: game.state.away_score || 0,
          }
        : undefined;

      runSimulation({
        game_id: game.state.id,
        current_state: currentState,
        n_simulations: 10000,
      });
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) {
      reset();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal Content */}
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-slate-900 rounded-lg shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-gradient-to-r from-slate-900 via-purple-900 to-slate-900 border-b border-slate-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white">
                {game.state.away_team} @ {game.state.home_team}
              </h2>
              <p className="text-sm text-slate-400 mt-1">
                {game.state.status === 'live'
                  ? `Live • ${game.state.period} ${game.state.time_remaining}`
                  : 'Pre-game simulation'
                }
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <svg className="w-6 h-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading && (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="relative">
                <div className="w-20 h-20 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
                <span className="absolute inset-0 flex items-center justify-center text-2xl">🎲</span>
              </div>
              <p className="text-white mt-6 text-lg font-semibold">Running 10,000 simulations...</p>
              <p className="text-slate-400 text-sm mt-2">Analyzing possession-by-possession outcomes</p>
            </div>
          )}

          {error && (
            <div className="bg-red-900/30 border-2 border-red-500 rounded-lg p-6">
              <div className="flex items-start gap-3">
                <span className="text-2xl">⚠️</span>
                <div>
                  <h3 className="text-white font-bold mb-2">Simulation Failed</h3>
                  <p className="text-red-300 text-sm">{error}</p>
                  <button
                    onClick={() => runSimulation({
                      game_id: game.state.id,
                      n_simulations: 10000,
                    })}
                    className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded font-semibold transition-colors"
                  >
                    Try Again
                  </button>
                </div>
              </div>
            </div>
          )}

          {simulation && !loading && (
            <MonteCarloSimulation
              gameId={game.state.id}
              simulation={simulation}
              teams={{
                home: game.state.home_team,
                away: game.state.away_team,
              }}
            />
          )}
        </div>

        {/* Footer Actions */}
        {simulation && (
          <div className="sticky bottom-0 bg-slate-900 border-t border-slate-700 p-4">
            <div className="flex items-center justify-between">
              <button
                onClick={() => runSimulation({
                  game_id: game.state.id,
                  n_simulations: 10000,
                })}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded font-semibold transition-colors flex items-center gap-2"
              >
                <span>🔄</span>
                <span>Re-run Simulation</span>
              </button>
              <button
                onClick={onClose}
                className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded font-semibold transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
