import { useState } from 'react';
import { addStakeToBet, deleteBet, addManualBet, updateBet, settleBet } from '../utils/betTracking';
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
  const [editingBetId, setEditingBetId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<{
    betSide: string;
    odds: string;
    stake: string;
    bookmaker: string;
  }>({
    betSide: '',
    odds: '',
    stake: '',
    bookmaker: ''
  });
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

  const handleStartEdit = (bet: any) => {
    setEditingBetId(bet.id);
    setEditForm({
      betSide: bet.bet_side || '',
      odds: bet.odds?.toString() || '',
      stake: bet.stake?.toString() || '',
      bookmaker: bet.bookmaker || ''
    });
  };

  const handleCancelEdit = () => {
    setEditingBetId(null);
    setEditForm({
      betSide: '',
      odds: '',
      stake: '',
      bookmaker: ''
    });
  };

  const handleSaveEdit = async (betId: string) => {
    // Validate fields
    if (!editForm.betSide || !editForm.odds || !editForm.bookmaker) {
      alert('Please fill in all required fields (Bet Side, Odds, Bookmaker)');
      return;
    }

    const updates: any = {
      betSide: editForm.betSide,
      odds: parseFloat(editForm.odds),
      bookmaker: editForm.bookmaker
    };

    // Only include stake if it's provided (for pending bets)
    if (editForm.stake && parseFloat(editForm.stake) > 0) {
      updates.stake = parseFloat(editForm.stake);
    }

    const result = await updateBet(betId, updates);

    if (result) {
      handleCancelEdit();
      onRefresh();
    } else {
      alert('Failed to update bet. Please try again.');
    }
  };

  const handleToggleBetSide = () => {
    // Toggle between OVER and UNDER if it's a total bet
    if (editForm.betSide.includes('OVER')) {
      setEditForm({ ...editForm, betSide: editForm.betSide.replace('OVER', 'UNDER') });
    } else if (editForm.betSide.includes('UNDER')) {
      setEditForm({ ...editForm, betSide: editForm.betSide.replace('UNDER', 'OVER') });
    }
  };

  const handleAdjustOdds = (amount: number) => {
    const currentOdds = parseFloat(editForm.odds) || 0;
    const newOdds = currentOdds + amount;
    // Don't let odds be exactly 0 or between -100 and 0
    if (newOdds === 0 || (newOdds > -100 && newOdds < 0)) {
      setEditForm({ ...editForm, odds: (amount > 0 ? '100' : '-105') });
    } else {
      setEditForm({ ...editForm, odds: newOdds.toString() });
    }
  };

  const handleAdjustStake = (amount: number) => {
    const currentStake = parseFloat(editForm.stake) || 0;
    const newStake = Math.max(0, currentStake + amount); // Don't go below 0
    setEditForm({ ...editForm, stake: newStake.toFixed(2) });
  };

  const canToggleBetSide = (betSide: string) => {
    return betSide.includes('OVER') || betSide.includes('UNDER');
  };

  const handleSettleBet = async (betId: string, result: 'win' | 'loss' | 'push') => {
    const confirmMessage = result === 'win' ? 'Mark this bet as WON?' :
                          result === 'loss' ? 'Mark this bet as LOST?' :
                          'Mark this bet as PUSH (tie)?';

    if (confirm(confirmMessage)) {
      const settled = await settleBet(betId, result);
      if (settled) {
        onRefresh();
      } else {
        alert('Failed to settle bet. Please try again.');
      }
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
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold transition-all border-2 border-blue-500"
        >
          <span className="text-2xl">📖</span>
          Manual Bet Entry
        </button>
      </div>

      {/* Manual Entry Modal */}
      {showManualEntry && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border-2 border-blue-600 p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
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
                  className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
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
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
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
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
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
                  className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
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
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
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
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
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
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
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
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
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
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
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
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
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
                    className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
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
                  className="w-full px-3 py-2 bg-slate-900 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
                  rows={3}
                  placeholder="Any additional notes about this bet..."
                />
              </div>

              {/* Submit Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-bold transition-all"
                >
                  Add Bet
                </button>
                <button
                  type="button"
                  onClick={() => setShowManualEntry(false)}
                  className="px-6 py-3 bg-slate-600 hover:bg-slate-700 text-white font-semibold transition-all"
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
        <div className="bg-slate-900 border-2 border-green-700 p-6 hover:border-green-600 transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm text-white font-bold tracking-wide">NET PROFIT/LOSS</div>
          </div>
          <div className={`text-3xl font-bold mb-1 ${stats.net_profit_loss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {stats.net_profit_loss >= 0 ? '+' : ''}${stats.net_profit_loss.toFixed(2)}
          </div>
          <div className="text-xs text-green-300/60">{stats.settled_bets} settled bets</div>
        </div>

        <div className="bg-slate-900 border-2 border-blue-700 p-6 hover:border-blue-600 transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm text-white font-bold tracking-wide">WIN RATE</div>
          </div>
          <div className="text-3xl font-bold text-blue-400 mb-1">
            {stats.win_rate}%
          </div>
          <div className="text-xs text-blue-300/60">{stats.won_bets}W / {stats.lost_bets}L / {stats.push_bets}P</div>
        </div>

        <div className="bg-slate-900 border-2 border-purple-700 p-6 hover:border-purple-600 transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm text-white font-bold tracking-wide">ROI</div>
          </div>
          <div className={`text-3xl font-bold mb-1 ${stats.roi_percent >= 0 ? 'text-purple-400' : 'text-red-400'}`}>
            {stats.roi_percent >= 0 ? '+' : ''}{stats.roi_percent}%
          </div>
          <div className="text-xs text-purple-300/60">Return on investment</div>
        </div>

        <div className="bg-slate-900 border-2 border-slate-700 p-6 hover:border-blue-600 transition-all">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm text-white font-bold tracking-wide">TOTAL WAGERED</div>
          </div>
          <div className="text-3xl font-bold text-white mb-1">
            ${stats.total_wagered.toFixed(2)}
          </div>
          <div className="text-xs text-slate-400">
            {stats.total_bets} bets • ${stats.settled_wagered?.toFixed(2) || '0.00'} settled
          </div>
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
              <div key={bet.id} className="bg-slate-900 border-2 border-orange-600 p-4">
                {editingBetId === bet.id ? (
                  // Edit Mode
                  <div>
                    <div className="text-lg font-bold text-white mb-3">
                      {bet.away_team} @ {bet.home_team}
                    </div>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Bet Side *</label>
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={editForm.betSide}
                            onChange={(e) => setEditForm({ ...editForm, betSide: e.target.value })}
                            className="flex-1 px-3 py-2 bg-slate-800 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
                            placeholder="e.g., OVER 220.5"
                          />
                          {canToggleBetSide(editForm.betSide) && (
                            <button
                              type="button"
                              onClick={handleToggleBetSide}
                              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold transition-all"
                              title="Toggle OVER/UNDER"
                            >
                              ⇅
                            </button>
                          )}
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Odds *</label>
                          <div className="flex gap-1">
                            <button
                              type="button"
                              onClick={() => handleAdjustOdds(-5)}
                              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white font-bold transition-all"
                              title="Decrease odds by 5"
                            >
                              ▼
                            </button>
                            <input
                              type="number"
                              step="1"
                              value={editForm.odds}
                              onChange={(e) => setEditForm({ ...editForm, odds: e.target.value })}
                              className="flex-1 px-3 py-2 bg-slate-800 border-2 border-slate-600 text-white text-center focus:border-blue-500 focus:outline-none"
                              placeholder="-110"
                            />
                            <button
                              type="button"
                              onClick={() => handleAdjustOdds(5)}
                              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white font-bold transition-all"
                              title="Increase odds by 5"
                            >
                              ▲
                            </button>
                          </div>
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Stake ($)</label>
                          <div className="flex gap-1">
                            <button
                              type="button"
                              onClick={() => handleAdjustStake(-5)}
                              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white font-bold transition-all"
                              title="Decrease stake by $5"
                            >
                              ▼
                            </button>
                            <input
                              type="number"
                              step="0.01"
                              value={editForm.stake}
                              onChange={(e) => setEditForm({ ...editForm, stake: e.target.value })}
                              className="flex-1 px-3 py-2 bg-slate-800 border-2 border-slate-600 text-white text-center focus:border-blue-500 focus:outline-none"
                              placeholder="100.00"
                            />
                            <button
                              type="button"
                              onClick={() => handleAdjustStake(5)}
                              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white font-bold transition-all"
                              title="Increase stake by $5"
                            >
                              ▲
                            </button>
                          </div>
                        </div>
                      </div>
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Bookmaker *</label>
                        <input
                          type="text"
                          value={editForm.bookmaker}
                          onChange={(e) => setEditForm({ ...editForm, bookmaker: e.target.value })}
                          className="w-full px-3 py-2 bg-slate-800 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
                          placeholder="DraftKings"
                        />
                      </div>
                      <div className="flex gap-2 pt-2">
                        <button
                          onClick={() => handleSaveEdit(bet.id)}
                          className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-semibold transition-all"
                        >
                          Save
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white font-semibold transition-all"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  // View Mode
                  <>
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
                        className="flex-1 px-3 py-2 bg-slate-900 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
                      />
                      <button
                        onClick={() => handleAddStake(bet.id)}
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-semibold transition-all"
                      >
                        Log Bet
                      </button>
                      <button
                        onClick={() => handleStartEdit(bet)}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold transition-all"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteBet(bet.id)}
                        className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold transition-all"
                      >
                        Remove
                      </button>
                    </div>
                  </>
                )}
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
              <div key={bet.id} className="bg-slate-900 border-2 border-blue-600 p-4">
                {editingBetId === bet.id ? (
                  // Edit Mode
                  <div>
                    <div className="text-lg font-bold text-white mb-3">
                      {bet.away_team} @ {bet.home_team}
                    </div>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Bet Side *</label>
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={editForm.betSide}
                            onChange={(e) => setEditForm({ ...editForm, betSide: e.target.value })}
                            className="flex-1 px-3 py-2 bg-slate-800 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
                            placeholder="e.g., OVER 220.5"
                          />
                          {canToggleBetSide(editForm.betSide) && (
                            <button
                              type="button"
                              onClick={handleToggleBetSide}
                              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold transition-all"
                              title="Toggle OVER/UNDER"
                            >
                              ⇅
                            </button>
                          )}
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Odds *</label>
                          <div className="flex gap-1">
                            <button
                              type="button"
                              onClick={() => handleAdjustOdds(-5)}
                              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white font-bold transition-all"
                              title="Decrease odds by 5"
                            >
                              ▼
                            </button>
                            <input
                              type="number"
                              step="1"
                              value={editForm.odds}
                              onChange={(e) => setEditForm({ ...editForm, odds: e.target.value })}
                              className="flex-1 px-3 py-2 bg-slate-800 border-2 border-slate-600 text-white text-center focus:border-blue-500 focus:outline-none"
                              placeholder="-110"
                            />
                            <button
                              type="button"
                              onClick={() => handleAdjustOdds(5)}
                              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white font-bold transition-all"
                              title="Increase odds by 5"
                            >
                              ▲
                            </button>
                          </div>
                        </div>
                        <div>
                          <label className="block text-xs text-slate-400 mb-1">Stake ($) *</label>
                          <div className="flex gap-1">
                            <button
                              type="button"
                              onClick={() => handleAdjustStake(-5)}
                              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white font-bold transition-all"
                              title="Decrease stake by $5"
                            >
                              ▼
                            </button>
                            <input
                              type="number"
                              step="0.01"
                              value={editForm.stake}
                              onChange={(e) => setEditForm({ ...editForm, stake: e.target.value })}
                              className="flex-1 px-3 py-2 bg-slate-800 border-2 border-slate-600 text-white text-center focus:border-blue-500 focus:outline-none"
                              placeholder="100.00"
                            />
                            <button
                              type="button"
                              onClick={() => handleAdjustStake(5)}
                              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white font-bold transition-all"
                              title="Increase stake by $5"
                            >
                              ▲
                            </button>
                          </div>
                        </div>
                      </div>
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Bookmaker *</label>
                        <input
                          type="text"
                          value={editForm.bookmaker}
                          onChange={(e) => setEditForm({ ...editForm, bookmaker: e.target.value })}
                          className="w-full px-3 py-2 bg-slate-800 border-2 border-slate-600 text-white focus:border-blue-500 focus:outline-none"
                          placeholder="DraftKings"
                        />
                      </div>
                      <div className="flex gap-2 pt-2">
                        <button
                          onClick={() => handleSaveEdit(bet.id)}
                          className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-semibold transition-all"
                        >
                          Save
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white font-semibold transition-all"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  // View Mode
                  <>
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

                    <div className="flex justify-between items-center text-xs text-slate-400 mb-3">
                      <span>Bookmaker: {bet.bookmaker}</span>
                      {bet.edge_percent && (
                        <span className="text-green-400">Edge: +{bet.edge_percent.toFixed(1)}%</span>
                      )}
                    </div>

                    {/* Settle Bet Buttons */}
                    <div className="border-t border-slate-700 pt-3 mt-3">
                      <div className="text-xs text-slate-400 mb-2 font-semibold">SETTLE BET:</div>
                      <div className="grid grid-cols-4 gap-2">
                        <button
                          onClick={() => handleSettleBet(bet.id, 'win')}
                          className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white font-bold transition-all text-sm"
                        >
                          WON ✓
                        </button>
                        <button
                          onClick={() => handleSettleBet(bet.id, 'loss')}
                          className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white font-bold transition-all text-sm"
                        >
                          LOST ✗
                        </button>
                        <button
                          onClick={() => handleSettleBet(bet.id, 'push')}
                          className="px-3 py-2 bg-slate-600 hover:bg-slate-700 text-white font-bold transition-all text-sm"
                        >
                          PUSH ↔
                        </button>
                        <button
                          onClick={() => handleStartEdit(bet)}
                          className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold transition-all text-sm"
                        >
                          Edit
                        </button>
                      </div>
                    </div>
                  </>
                )}
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
          <div className="bg-slate-900 border-2 border-slate-700 p-6 overflow-x-auto">
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
                      <span className={`px-3 py-1 text-xs font-bold ${
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
          <div className="bg-blue-900/30 border-2 border-blue-700 p-6 max-w-2xl mx-auto">
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
