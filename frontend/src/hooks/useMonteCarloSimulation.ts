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
  n_simulations?: number;
}

interface SimulationResult {
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
