import { useState } from 'react';
import { getApiUrl } from '../config';

interface SimulationRequest {
  game_id: string;
  current_state?: {
    quarter: number;
    time_remaining: string;
    home_score: number;
    away_score: number;
  };
  home_stats?: {
    pace: number;
    off_rating: number;
    def_rating: number;
  };
  away_stats?: {
    pace: number;
    off_rating: number;
    def_rating: number;
  };
  market_total?: number;
  n_simulations?: number;
}

interface SimulationResult {
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
}

export function useMonteCarloSimulation() {
  const [simulation, setSimulation] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSimulation = async (request: SimulationRequest) => {
    setLoading(true);
    setError(null);

    try {
      const url = getApiUrl('simulation/monte-carlo');
      console.log('🎲 Running Monte Carlo simulation:', url, request);

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...request,
          n_simulations: request.n_simulations || 10000,
        }),
      });

      if (!response.ok) {
        throw new Error(`Simulation failed: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('✅ Simulation complete:', data);
      setSimulation(data);
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Simulation failed';
      console.error('❌ Simulation error:', errorMessage);
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setSimulation(null);
    setError(null);
    setLoading(false);
  };

  return {
    simulation,
    loading,
    error,
    runSimulation,
    reset,
  };
}
