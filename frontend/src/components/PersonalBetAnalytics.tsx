import { useState } from 'react';
import { addStakeToBet, deleteBet, addManualBet } from '../utils/betTracking';
import { useAuth } from '../contexts/AuthContext';

interface PersonalBetAnalyticsProps {
  stats: any;
  pendingBets: any[];
  activeBets: any[];
  settledBets: any[];
  onRefresh: () => void;
}

interface ManualBetForm {
  sport: string;
  homeTeam: string;
  awayTeam: string;
  commenceTime: string;
  betType: 'spread' | 'total' | 'moneyline' | 'prop';
  betSide: string;
  odds: string;
  stake: string;
  bookmaker: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | '';
  edgePercent: string;
  notes: string;
}

export function PersonalBetAnalytics({
  stats,
  pendingBets,
  activeBets,
  settledBets,
  onRefresh
}: PersonalBetAnalyticsProps) {
  const { username } = useAuth();
  const [stakes, setStakes] = useState<Record<string, string>>({});
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [manualBetForm, setManualBetForm] = useState<ManualBetForm>({
    sport: 'NBA',
    homeTeam: '',
    awayTeam: '',
    commenceTime: new Date().toISOString().slice(0, 16),
    betType: 'spread',
    betSide: '',
    odds: '',
    stake: '',
    bookmaker: '',
    confidence: '',
    edgePercent: '',
    notes: ''
  });

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

  const handleManualBetSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!username) {
      alert('You must be logged in to add a bet');
      return;
    }

    // Validate required fields
    if (!manualBetForm.homeTeam || !manualBetForm.awayTeam || !manualBetForm.betSide ||
        !manualBetForm.odds || !manualBetForm.stake || !manualBetForm.bookmaker) {
      alert('Please fill in all required fields');
      return;
    }

    const result = await addManualBet({
      userId: username,
      sport: manualBetForm.sport,
      homeTeam: manualBetForm.homeTeam,
      awayTeam: manualBetForm.awayTeam,
      commenceTime: manualBetForm.commenceTime,
      betType: manualBetForm.betType,
      betSide: manualBetForm.betSide,
      odds: parseFloat(manualBetForm.odds),
      stake: parseFloat(manualBetForm.stake),
      bookmaker: manualBetForm.bookmaker,
      confidence: manualBetForm.confidence || undefined,
      edgePercent: manualBetForm.edgePercent ? parseFloat(manualBetForm.edgePercent) : undefined,
      notes: manualBetForm.notes || undefined,
    });

    if (result) {
      // Reset form and close modal
      setManualBetForm({
        sport: 'NBA',
        homeTeam: '',
        awayTeam: '',
        commenceTime: new Date().toISOString().slice(0, 16),
        betType: 'spread',
        betSide: '',
        odds: '',
        stake: '',
        bookmaker: '',
        confidence: '',
        edgePercent: '',
        notes: ''
      });
      setShowManualEntry(false);
      onRefresh();
      alert('Bet added successfully!');
    } else {
      alert('Failed to add bet. Please try again.');
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
      {/* Manual Entry Button */}
      <div className="mb-6 flex justify-end">
        <button
          onClick={() => setShowManualEntry(true)}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-bold rounded-lg shadow-lg hover:shadow-blue-600/50 transition-all border-2 border-blue-500"
        >
          <span className="text-2xl">📖</span>
          Manual Bet Entry
        </button>
      </div>

      {/* Manual Entry Modal */}
      {showManualEntry && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-slate-800 via-slate-700 to-slate-900 border-4 border-blue-600 rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <span className="text-3xl">📖</span>
                Manual Bet Entry
              </h2>
              <button
                onClick={() => setShowManualEntry(false)}
                className="text-slate-400 hover:text-white text-2xl font-bold"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleManualBetSubmit} className="space-y-4">
              {/* Sport Selection */}
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">
                  Sport *
                </label>
                <select
                  value={manualBetForm.sport}
                  onChange={(e) => setManualBetForm({ ...manualBetForm, sport: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                  required
                >
                  <option value="NBA">NBA</option>
                  <option value="NFL">NFL</option>
                  <option value="NHL">NHL</option>
                  <option value="MLB">MLB</option>
                  <option value="NCAAB">NCAAB</option>
                  <option value="NCAAF">NCAAF</option>
                </select>
              </div>

              {/* Teams */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">
                    Away Team *
                  </label>
                  <input
                    type="text"
                    value={manualBetForm.awayTeam}
                    onChange={(e) => setManualBetForm({ ...manualBetForm, awayTeam: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                    placeholder="e.g., Lakers"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">
                    Home Team *
                  </label>
                  <input
                    type="text"
                    value={manualBetForm.homeTeam}
                    onChange={(e) => setManualBetForm({ ...manualBetForm, homeTeam: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                    placeholder="e.g., Warriors"
                    required
                  />
                </div>
              </div>

              {/* Game Time */}
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">
                  Game Time *
                </label>
                <input
                  type="datetime-local"
                  value={manualBetForm.commenceTime}
                  onChange={(e) => setManualBetForm({ ...manualBetForm, commenceTime: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>

              {/* Bet Type and Side */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">
                    Bet Type *
                  </label>
                  <select
                    value={manualBetForm.betType}
                    onChange={(e) => setManualBetForm({ ...manualBetForm, betType: e.target.value as any })}
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                    required
                  >
                    <option value="spread">Spread</option>
                    <option value="total">Total</option>
                    <option value="moneyline">Moneyline</option>
                    <option value="prop">Prop</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">
                    Bet Side *
                  </label>
                  <input
                    type="text"
                    value={manualBetForm.betSide}
                    onChange={(e) => setManualBetForm({ ...manualBetForm, betSide: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                    placeholder="e.g., OVER 220.5, Lakers -5.5"
                    required
                  />
                </div>
              </div>

              {/* Odds, Stake, Bookmaker */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">
                    Odds *
                  </label>
                  <input
                    type="number"
                    step="1"
                    value={manualBetForm.odds}
                    onChange={(e) => setManualBetForm({ ...manualBetForm, odds: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                    placeholder="-110"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">
                    Stake ($) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={manualBetForm.stake}
                    onChange={(e) => setManualBetForm({ ...manualBetForm, stake: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                    placeholder="100.00"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">
                    Bookmaker *
                  </label>
                  <input
                    type="text"
                    value={manualBetForm.bookmaker}
                    onChange={(e) => setManualBetForm({ ...manualBetForm, bookmaker: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                    placeholder="DraftKings"
                    required
                  />
                </div>
              </div>

              {/* Optional: Confidence and Edge */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">
                    Confidence (Optional)
                  </label>
                  <select
                    value={manualBetForm.confidence}
                    onChange={(e) => setManualBetForm({ ...manualBetForm, confidence: e.target.value as any })}
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                  >
                    <option value="">None</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-2">
                    Edge % (Optional)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={manualBetForm.edgePercent}
                    onChange={(e) => setManualBetForm({ ...manualBetForm, edgePercent: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                    placeholder="5.2"
                  />
                </div>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">
                  Notes (Optional)
                </label>
                <textarea
                  value={manualBetForm.notes}
                  onChange={(e) => setManualBetForm({ ...manualBetForm, notes: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                  rows={3}
                  placeholder="Any additional notes about this bet..."
                />
              </div>

              {/* Submit Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg transition-all"
                >
                  Add Bet
                </button>
                <button
                  type="button"
                  onClick={() => setShowManualEntry(false)}
                  className="px-6 py-3 bg-slate-600 hover:bg-slate-700 text-white font-semibold rounded-lg transition-all"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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
