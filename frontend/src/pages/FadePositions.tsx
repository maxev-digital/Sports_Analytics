import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface FadePosition {
  id: string;
  game_id: string;
  sport: string;
  favorite_team: string;
  pregame_odds: number;
  entry_odds: number;
  entry_stake: number;
  tier: string;
  improvement_pct: number;
  base_ev: number;
  adjusted_ev: number;
  status: string;
  hedge_team?: string;
  hedge_odds?: number;
  hedge_stake?: number;
  locked_profit?: number;
  actual_profit?: number;
  entry_quarter?: string;
  entry_time_left?: string;
  created_at: string;
}

interface TierPerformance {
  tier: string;
  total_positions: number;
  hedged: number;
  held_won: number;
  held_lost: number;
  total_staked: number;
  total_profit: number;
  avg_improvement: number;
  roi: number;
}

const TIER_COLORS = {
  GOLD: 'bg-gradient-to-br from-yellow-400 to-yellow-600',
  SILVER: 'bg-gradient-to-br from-gray-300 to-gray-500',
  BRONZE: 'bg-gradient-to-br from-orange-700 to-orange-900'
};

export const FadePositions: React.FC = () => {
  const { username } = useAuth();
  const [positions, setPositions] = useState<FadePosition[]>([]);
  const [performance, setPerformance] = useState<Record<string, TierPerformance> | null>(null);
  const [selectedTier, setSelectedTier] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPositions();
    fetchPerformance();
    const interval = setInterval(fetchPositions, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [selectedTier]);

  const fetchPositions = async () => {
    try {
      const tierParam = selectedTier !== 'ALL' ? `&tier=${selectedTier}` : '';
      const response = await fetch(`/api/fade/positions?user_id=${username}${tierParam}`);
      const data = await response.json();
      setPositions(data.positions || []);
    } catch (error) {
      console.error('Error fetching fade positions:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPerformance = async () => {
    try {
      const response = await fetch('/api/fade/performance');
      const data = await response.json();
      setPerformance(data);
    } catch (error) {
      console.error('Error fetching performance:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'text-blue-400';
      case 'hedged': return 'text-green-400';
      case 'closed_won': return 'text-green-500';
      case 'closed_lost': return 'text-red-500';
      default: return 'text-gray-400';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'open': return 'Watching';
      case 'hedged': return 'Hedged';
      case 'closed_won': return 'Won';
      case 'closed_lost': return 'Lost';
      default: return status;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <h1 className="text-4xl font-bold mb-2">40% Fade Positions</h1>
        <p className="text-gray-400">Track your fade entries and performance by tier</p>
      </div>

      {/* Performance Summary */}
      {performance && (
        <div className="max-w-7xl mx-auto mb-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(performance).map(([tier, perf]) => (
            <div key={tier} className="bg-gray-800 rounded-lg p-4 border-2 border-gray-700">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-lg">{tier}</h3>
                <div className={`w-3 h-3 rounded-full ${
                  tier === 'GOLD' ? 'bg-yellow-400' :
                  tier === 'SILVER' ? 'bg-gray-300' :
                  tier === 'BRONZE' ? 'bg-orange-700' :
                  'bg-blue-500'
                }`} />
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Positions:</span>
                  <span className="font-semibold">{perf.total_positions}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Hedged:</span>
                  <span className="font-semibold text-green-400">{perf.hedged}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Held Won:</span>
                  <span className="font-semibold text-green-500">{perf.held_won}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">ROI:</span>
                  <span className={`font-bold ${perf.roi > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {perf.roi > 0 ? '+' : ''}{perf.roi.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Profit:</span>
                  <span className={`font-bold ${perf.total_profit > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {perf.total_profit > 0 ? '+' : ''}${perf.total_profit.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tier Filter */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex space-x-2">
          {['ALL', 'GOLD', 'SILVER', 'BRONZE'].map((tier) => (
            <button
              key={tier}
              onClick={() => setSelectedTier(tier)}
              className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                selectedTier === tier
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {tier}
            </button>
          ))}
        </div>
      </div>

      {/* Positions List */}
      <div className="max-w-7xl mx-auto">
        {loading ? (
          <div className="text-center py-12">
            <div className="text-gray-400">Loading positions...</div>
          </div>
        ) : positions.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-12 text-center border-2 border-dashed border-gray-700">
            <div className="text-gray-400 text-lg mb-2">No Positions Yet</div>
            <div className="text-gray-500 text-sm">
              Fade opportunities will appear on live game cards when detected
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {positions.map((position) => (
              <div key={position.id} className="bg-gray-800 rounded-lg p-6 border-2 border-gray-700">
                {/* Position Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        position.tier === 'GOLD' ? 'bg-yellow-400 text-gray-900' :
                        position.tier === 'SILVER' ? 'bg-gray-300 text-gray-900' :
                        'bg-orange-700 text-white'
                      }`}>
                        {position.tier}
                      </span>
                      <span className={`font-semibold ${getStatusColor(position.status)}`}>
                        {getStatusText(position.status)}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold">{position.favorite_team}</h3>
                    <div className="text-gray-400 text-sm">
                      {new Date(position.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-gray-400 text-sm">Improvement</div>
                    <div className="text-green-400 font-bold text-xl">
                      +{position.improvement_pct.toFixed(1)}%
                    </div>
                  </div>
                </div>

                {/* Position Details */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <div className="text-gray-400 text-sm">Pregame</div>
                    <div className="font-semibold">{position.pregame_odds}</div>
                  </div>
                  <div>
                    <div className="text-gray-400 text-sm">Entry</div>
                    <div className="font-semibold text-green-400">{position.entry_odds}</div>
                  </div>
                  <div>
                    <div className="text-gray-400 text-sm">Stake</div>
                    <div className="font-semibold">${position.entry_stake}</div>
                  </div>
                  <div>
                    <div className="text-gray-400 text-sm">EV</div>
                    <div className="font-semibold text-blue-400">{position.adjusted_ev.toFixed(1)}%</div>
                  </div>
                </div>

                {/* Hedge Info */}
                {position.status === 'hedged' && (
                  <div className="bg-green-900 bg-opacity-30 rounded-lg p-3 border-2 border-green-700">
                    <div className="font-semibold text-green-400 mb-2">Hedged</div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <div className="text-gray-400">Hedge Team</div>
                        <div className="font-semibold">{position.hedge_team}</div>
                      </div>
                      <div>
                        <div className="text-gray-400">Hedge Stake</div>
                        <div className="font-semibold">${position.hedge_stake}</div>
                      </div>
                      <div>
                        <div className="text-gray-400">Locked Profit</div>
                        <div className="font-bold text-green-400">
                          +${position.locked_profit?.toFixed(2)}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Final Result */}
                {(position.status === 'closed_won' || position.status === 'closed_lost') && (
                  <div className={`rounded-lg p-3 border-2 ${
                    position.status === 'closed_won'
                      ? 'bg-green-900 bg-opacity-30 border-green-700'
                      : 'bg-red-900 bg-opacity-30 border-red-700'
                  }`}>
                    <div className="flex items-center justify-between">
                      <span className="font-semibold">Final Result:</span>
                      <span className={`font-bold text-lg ${
                        (position.actual_profit || 0) > 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {(position.actual_profit || 0) > 0 ? '+' : ''}${position.actual_profit?.toFixed(2)}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default FadePositions;
