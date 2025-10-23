import { useState } from 'react';
import { addStakeToBet, deleteBet } from '../utils/betTracking';

interface PersonalBetAnalyticsProps {
  stats: any;
  pendingBets: any[];
  activeBets: any[];
  settledBets: any[];
  onRefresh: () => void;
}

export function PersonalBetAnalytics({
  stats,
  pendingBets,
  activeBets,
  settledBets,
  onRefresh
}: PersonalBetAnalyticsProps) {
  const [stakes, setStakes] = useState<Record<string, string>>({});

  const handleAddStake = async (betId: string) => {
    const stakeAmount = parseFloat(stakes[betId] || '0');
    if (stakeAmount <= 0) {
      alert('Please enter a valid stake amount');
      return;
    }

    const success = await addStakeToBet(betId, stakeAmount);
    if (success) {
      setStakes({ ...stakes, [betId]: '' });
      onRefresh();
    }
  };

  const handleDeleteBet = async (betId: string) => {
    if (confirm('Are you sure you want to remove this pending bet?')) {
      await deleteBet(betId);
      onRefresh();
    }
  };

  // Show loading state if no stats yet
  if (!stats) {
    return (
      <div className="text-center py-20">
        <div className="text-white text-xl">Loading your bet data...</div>
      </div>
    );
  }

  return (
    <div>
      {/* Overall Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-gradient-to-br from-green-900 via-green-700 to-green-900 border-4 border-green-700 rounded-lg p-6 hover:shadow-lg hover:shadow-green-600/20 hover:border-green-600 transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm text-white font-bold tracking-wide">NET PROFIT/LOSS</div>
          </div>
          <div className={`text-3xl font-bold mb-1 ${stats.net_profit_loss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {stats.net_profit_loss >= 0 ? '+' : ''}${stats.net_profit_loss.toFixed(2)}
          </div>
          <div className="text-xs text-green-300/60">{stats.settled_bets} settled bets</div>
        </div>

        <div className="bg-gradient-to-br from-blue-900 via-blue-700 to-blue-900 border-4 border-blue-700 rounded-lg p-6 hover:shadow-lg hover:shadow-blue-600/20 hover:border-blue-600 transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm text-white font-bold tracking-wide">WIN RATE</div>
          </div>
          <div className="text-3xl font-bold text-blue-400 mb-1">
            {stats.win_rate}%
          </div>
          <div className="text-xs text-blue-300/60">{stats.won_bets}W / {stats.lost_bets}L / {stats.push_bets}P</div>
        </div>

        <div className="bg-gradient-to-br from-purple-900 via-purple-700 to-purple-900 border-4 border-purple-700 rounded-lg p-6 hover:shadow-lg hover:shadow-purple-600/20 hover:border-purple-600 transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm text-white font-bold tracking-wide">ROI</div>
          </div>
          <div className={`text-3xl font-bold mb-1 ${stats.roi_percent >= 0 ? 'text-purple-400' : 'text-red-400'}`}>
            {stats.roi_percent >= 0 ? '+' : ''}{stats.roi_percent}%
          </div>
          <div className="text-xs text-purple-300/60">Return on investment</div>
        </div>

        <div className="bg-gradient-to-br from-slate-900 via-slate-700 to-slate-900 border-4 border-slate-700 rounded-lg p-6 hover:shadow-lg hover:shadow-blue-600/20 hover:border-blue-600 transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm text-white font-bold tracking-wide">TOTAL WAGERED</div>
          </div>
          <div className="text-3xl font-bold text-white mb-1">
            ${stats.total_wagered.toFixed(2)}
          </div>
          <div className="text-xs text-slate-400">{stats.total_bets} bets placed</div>
        </div>
      </div>

      {/* Pending Bets Section */}
      {pendingBets.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-2xl font-bold text-white">⏳ Pending Bets</h2>
            <span className="text-sm text-slate-400">({pendingBets.length}) - Add stake amount to track</span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {pendingBets.map((bet) => (
              <div key={bet.id} className="bg-gradient-to-br from-slate-800 via-slate-700 to-slate-900 border-4 border-yellow-600 rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="text-lg font-bold text-white mb-1">
                      {bet.away_team} @ {bet.home_team}
                    </div>
                    <div className="text-sm text-slate-400 mb-1">
                      {bet.sport} • {new Date(bet.clicked_at).toLocaleDateString()}
                    </div>
                    <div className="text-sm text-yellow-400 font-semibold">
                      {bet.bet_side} ({bet.odds > 0 ? '+' : ''}{bet.odds})
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-400 mb-1">Bookmaker</div>
                    <div className="text-sm font-semibold text-white">{bet.bookmaker}</div>
                  </div>
                </div>

                {bet.edge_percent && (
                  <div className="text-xs text-green-400 mb-3">
                    Edge: +{bet.edge_percent.toFixed(1)}%
                  </div>
                )}

                <div className="flex gap-2">
                  <input
                    type="number"
                    placeholder="Stake amount ($)"
                    value={stakes[bet.id] || ''}
                    onChange={(e) => setStakes({ ...stakes, [bet.id]: e.target.value })}
                    className="flex-1 px-3 py-2 bg-slate-900 border-2 border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                  />
                  <button
                    onClick={() => handleAddStake(bet.id)}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-all"
                  >
                    Log Bet
                  </button>
                  <button
                    onClick={() => handleDeleteBet(bet.id)}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-all"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Bets Section */}
      {activeBets.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-2xl font-bold text-white">🔴 Active Bets</h2>
            <span className="text-sm text-slate-400">({activeBets.length}) - Waiting for results</span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {activeBets.map((bet) => (
              <div key={bet.id} className="bg-gradient-to-br from-slate-800 via-slate-700 to-slate-900 border-4 border-blue-600 rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="text-lg font-bold text-white mb-1">
                      {bet.away_team} @ {bet.home_team}
                    </div>
                    <div className="text-sm text-slate-400 mb-1">
                      {bet.sport} • {new Date(bet.commence_time).toLocaleDateString()}
                    </div>
                    <div className="text-sm text-blue-400 font-semibold">
                      {bet.bet_side} ({bet.odds > 0 ? '+' : ''}{bet.odds})
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-400 mb-1">Stake</div>
                    <div className="text-lg font-bold text-white">${bet.stake.toFixed(2)}</div>
                  </div>
                </div>

                <div className="flex justify-between text-xs text-slate-400">
                  <span>Bookmaker: {bet.bookmaker}</span>
                  {bet.edge_percent && (
                    <span className="text-green-400">Edge: +{bet.edge_percent.toFixed(1)}%</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Settled Bets Table */}
      {settledBets.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-2xl font-bold text-white">✅ Settled Bets</h2>
            <span className="text-sm text-slate-400">({settledBets.length}) - Last 50 shown</span>
          </div>
          <div className="bg-gradient-to-br from-slate-800 via-slate-700 to-slate-900 border-4 border-slate-700 rounded-lg p-6 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-4 text-slate-300 font-semibold">Date</th>
                  <th className="text-left py-3 px-4 text-slate-300 font-semibold">Game</th>
                  <th className="text-left py-3 px-4 text-slate-300 font-semibold">Bet</th>
                  <th className="text-right py-3 px-4 text-slate-300 font-semibold">Stake</th>
                  <th className="text-right py-3 px-4 text-slate-300 font-semibold">Odds</th>
                  <th className="text-center py-3 px-4 text-slate-300 font-semibold">Result</th>
                  <th className="text-right py-3 px-4 text-slate-300 font-semibold">Profit/Loss</th>
                </tr>
              </thead>
              <tbody>
                {settledBets.slice(0, 50).map((bet) => (
                  <tr key={bet.id} className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors">
                    <td className="py-3 px-4 text-sm text-slate-400">
                      {new Date(bet.settled_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-sm text-white">
                      {bet.away_team} @ {bet.home_team}
                    </td>
                    <td className="py-3 px-4 text-sm text-slate-300">
                      {bet.bet_side}
                    </td>
                    <td className="text-right py-3 px-4 text-sm text-white">
                      ${bet.stake.toFixed(2)}
                    </td>
                    <td className="text-right py-3 px-4 text-sm text-slate-300">
                      {bet.odds > 0 ? '+' : ''}{bet.odds}
                    </td>
                    <td className="text-center py-3 px-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        bet.status === 'won' ? 'bg-green-900 text-green-300' :
                        bet.status === 'lost' ? 'bg-red-900 text-red-300' :
                        'bg-slate-700 text-slate-300'
                      }`}>
                        {bet.status.toUpperCase()}
                      </span>
                    </td>
                    <td className={`text-right py-3 px-4 text-sm font-bold ${
                      bet.profit_loss > 0 ? 'text-green-400' :
                      bet.profit_loss < 0 ? 'text-red-400' :
                      'text-slate-400'
                    }`}>
                      {bet.profit_loss > 0 ? '+' : ''}${bet.profit_loss.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty State */}
      {pendingBets.length === 0 && activeBets.length === 0 && settledBets.length === 0 && (
        <div className="text-center py-20">
          <div className="text-4xl mb-4">📊</div>
          <h3 className="text-2xl font-bold text-white mb-2">No Bets Yet</h3>
          <p className="text-slate-400 mb-6">
            Start tracking your bets by clicking bookmaker icons on game cards
          </p>
          <div className="bg-blue-900/30 border-2 border-blue-700 rounded-lg p-6 max-w-2xl mx-auto">
            <h4 className="text-lg font-semibold text-blue-300 mb-3">How it works:</h4>
            <ol className="text-left text-slate-300 space-y-2">
              <li>1. Click a bookmaker icon on any game card</li>
              <li>2. Your bet is automatically tracked as "pending"</li>
              <li>3. Come here to add your stake amount</li>
              <li>4. Track your performance over time!</li>
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}
