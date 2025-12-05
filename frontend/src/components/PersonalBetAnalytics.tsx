import { useState, useEffect } from 'react';
import { addStakeToBet, deleteBet, addManualBet, updateBet, settleBet } from '../utils/betTracking';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from './Toast';
import { formatTeamName } from '../utils/teamNames';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Temporary type definition
interface PerformanceData {
  totalBets: number;
  wins: number;
  losses: number;
  pending: number;
  winRate: number;
  totalProfit: number;
  roi: number;
}

// Temporary stub function
const getUserPerformanceData = async (username: string, days?: number): Promise<PerformanceData> => {
  return {
    totalBets: 0,
    wins: 0,
    losses: 0,
    pending: 0,
    winRate: 0,
    totalProfit: 0,
    roi: 0
  };
};

// Helper function to convert sport names to sport keys
const sportKeyMapper = (sport: string): string => {
  const sportMap: Record<string, string> = {
    'NBA': 'basketball_nba',
    'NCAAB': 'basketball_ncaab',
    'NFL': 'americanfootball_nfl',
    'NCAAF': 'americanfootball_ncaaf',
    'NHL': 'icehockey_nhl',
    'MLB': 'baseball_mlb',
  };
  return sportMap[sport] || sport.toLowerCase();
};

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
  const { showToast } = useToast();
  const [stakes, setStakes] = useState<Record<string, string>>({});
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [editingBetId, setEditingBetId] = useState<string | null>(null);
  const [settleConfirmation, setSettleConfirmation] = useState<{
    betId: string;
    result: 'win' | 'loss' | 'push';
  } | null>(null);

  // Time range filter state
  const [days, setDays] = useState<number | undefined>(undefined);
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [loadingPerformance, setLoadingPerformance] = useState(false);

  const [editForm, setEditForm] = useState<{ betSide: string; line: string; odds: string; stake: string; bookmaker: string; betType: string; }>({
    betSide: '', line: '', odds: '', stake: '', bookmaker: '', betType: ''
  });
  const [manualBetForm, setManualBetForm] = useState<ManualBetForm>({
    sport: 'NBA', homeTeam: '', awayTeam: '', commenceTime: new Date().toISOString().slice(0, 16),
    betType: 'spread', betSide: '', odds: '', stake: '', bookmaker: '', confidence: '', edgePercent: '', notes: ''
  });

  useEffect(() => {
    if (username) fetchPerformanceData();
  }, [username, days]);

  const fetchPerformanceData = async () => {
    if (!username) return;
    setLoadingPerformance(true);
    try {
      const data = await getUserPerformanceData(username, days);
      setPerformanceData(data);
    } catch (error) {
      console.error('Error fetching performance data:', error);
    } finally {
      setLoadingPerformance(false);
    }
  };

  const handleAddStake = async (betId: string) => {
    const stakeAmount = parseFloat(stakes[betId] || '0');
    if (stakeAmount <= 0) { alert('Please enter a valid stake amount'); return; }
    const success = await addStakeToBet(betId, stakeAmount);
    if (success) { setStakes({ ...stakes, [betId]: '' }); onRefresh(); fetchPerformanceData(); }
  };

  const handleDeleteBet = async (betId: string) => {
    if (confirm('Are you sure you want to remove this pending bet?')) {
      await deleteBet(betId); onRefresh(); fetchPerformanceData();
    }
  };

  const handleManualBetSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username) { alert('You must be logged in to add a bet'); return; }
    if (!manualBetForm.homeTeam || !manualBetForm.awayTeam || !manualBetForm.betSide || !manualBetForm.odds || !manualBetForm.stake || !manualBetForm.bookmaker) {
      showToast('Please fill in all required fields', 'warning'); return;
    }
    const result = await addManualBet({
      userId: username, sport: manualBetForm.sport, homeTeam: manualBetForm.homeTeam, awayTeam: manualBetForm.awayTeam,
      commenceTime: manualBetForm.commenceTime, betType: manualBetForm.betType, betSide: manualBetForm.betSide,
      odds: parseFloat(manualBetForm.odds), stake: parseFloat(manualBetForm.stake), bookmaker: manualBetForm.bookmaker,
      confidence: manualBetForm.confidence || undefined, edgePercent: manualBetForm.edgePercent ? parseFloat(manualBetForm.edgePercent) : undefined,
    });
    if (result) {
      setManualBetForm({ sport: 'NBA', homeTeam: '', awayTeam: '', commenceTime: new Date().toISOString().slice(0, 16), betType: 'spread', betSide: '', odds: '', stake: '', bookmaker: '', confidence: '', edgePercent: '', notes: '' });
      setShowManualEntry(false); onRefresh(); fetchPerformanceData(); showToast('Bet added successfully!', 'success');
    } else { showToast('Failed to add bet. Please try again.', 'error'); }
  };

  const handleStartEdit = (bet: any) => {
    setEditingBetId(bet.id);
    // Parse line from bet_side if it exists (e.g., "OVER 220.5" -> side="OVER", line="220.5")
    let side = bet.bet_side || '';
    let line = '';
    const match = side.match(/^(OVER|UNDER|.+?)\s+([-+]?\d+\.?\d*)$/);
    if (match) {
      side = match[1];
      line = match[2];
    }
    setEditForm({ 
      betSide: side, 
      line: line,
      odds: bet.odds?.toString() || '', 
      stake: bet.stake?.toString() || '', 
      bookmaker: bet.bookmaker || '',
      betType: bet.bet_type || 'total'
    });
  };

  const handleCancelEdit = () => { setEditingBetId(null); setEditForm({ betSide: '', line: '', odds: '', stake: '', bookmaker: '', betType: '' }); };

  const handleSaveEdit = async (betId: string) => {
    if (!editForm.betSide || !editForm.odds || !editForm.bookmaker) { alert("Please fill in all required fields"); return; }
    // Combine betSide with line if line exists (e.g., "OVER" + "220.5" = "OVER 220.5")
    const finalBetSide = editForm.line ? editForm.betSide + " " + editForm.line : editForm.betSide;
    const updates: any = { betSide: finalBetSide, odds: parseFloat(editForm.odds), bookmaker: editForm.bookmaker };
    if (editForm.stake && parseFloat(editForm.stake) > 0) updates.stake = parseFloat(editForm.stake);
    const result = await updateBet(betId, updates);
    if (result) { handleCancelEdit(); onRefresh(); fetchPerformanceData(); showToast("Bet updated!", "success"); } else { showToast("Failed to update bet.", "error"); }
  };

  const canToggleBetSide = (betSide: string) => betSide.includes('OVER') || betSide.includes('UNDER');

  const handleQuickToggleBetSide = async (bet: any) => {
    let newBetSide = bet.bet_side;
    if (bet.bet_side.includes('OVER')) newBetSide = bet.bet_side.replace('OVER', 'UNDER');
    else if (bet.bet_side.includes('UNDER')) newBetSide = bet.bet_side.replace('UNDER', 'OVER');
    else return;
    const success = await updateBet(bet.id, { betSide: newBetSide });
    if (success) onRefresh();
  };

  const handleSettleBet = async (betId: string, result: 'win' | 'loss' | 'push') => { setSettleConfirmation({ betId, result }); };

  const confirmSettleBet = async () => {
    if (!settleConfirmation) return;
    const { betId, result } = settleConfirmation;
    const settled = await settleBet(betId, result);
    if (settled) { showToast(`Bet settled as ${result.toUpperCase()}!`, 'success'); setSettleConfirmation(null); onRefresh(); fetchPerformanceData(); }
    else { showToast('Failed to settle bet.', 'error'); }
  };

  const summaryData = performanceData?.summary || stats;

  if (!stats && !performanceData) {
    return <div className="text-center py-20"><div className="text-white text-xl">Loading your bet data...</div></div>;
  }

  return (
    <div>
      {/* Time Range Filter & Manual Entry */}
      <div className="bg-gradient-to-br from-slate-700 via-slate-800 to-slate-900 border border-white rounded-xl p-4 mb-6">
        <div className="flex gap-4 items-center justify-between flex-wrap">
          <div className="flex gap-4 items-center flex-wrap">
            <div>
              <label className="text-slate-400 text-sm block mb-1">Time Range:</label>
              <select value={days || 'all'} onChange={(e) => setDays(e.target.value === 'all' ? undefined : parseInt(e.target.value))} className="px-3 py-2 bg-slate-800 border border-slate-600 hover:border-white transition-all rounded text-white">
                <option value="7">Last 7 Days</option>
                <option value="30">Last 30 Days</option>
                <option value="90">Last 90 Days</option>
                <option value="all">All Time</option>
              </select>
            </div>
          </div>
          <button onClick={() => setShowManualEntry(true)} className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold transition-all border border-blue-500 rounded">
            <span className="text-xl">+</span> Manual Bet Entry
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-1">Win Rate</div>
          <div className="text-3xl font-bold text-blue-400">{(summaryData?.win_rate || 0).toFixed(1)}%</div>
          <div className="text-slate-500 text-xs mt-2">{summaryData?.wins || summaryData?.won_bets || 0}W - {summaryData?.losses || summaryData?.lost_bets || 0}L</div>
        </div>
        <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-1">ROI</div>
          <div className={`text-3xl font-bold ${(summaryData?.roi || summaryData?.roi_percent || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {(summaryData?.roi || summaryData?.roi_percent || 0) >= 0 ? '+' : ''}{(summaryData?.roi || summaryData?.roi_percent || 0).toFixed(1)}%
          </div>
          <div className="text-slate-500 text-xs mt-2">Return on Investment</div>
        </div>
        <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-1">Net Profit/Loss</div>
          <div className={`text-3xl font-bold ${(summaryData?.net_profit_loss || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {(summaryData?.net_profit_loss || 0) >= 0 ? '+' : ''}${(summaryData?.net_profit_loss || 0).toFixed(2)}
          </div>
          <div className="text-slate-500 text-xs mt-2">{summaryData?.total_bets || summaryData?.settled_bets || 0} settled bets</div>
        </div>
        <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-1">Total Wagered</div>
          <div className="text-3xl font-bold text-purple-400">${(summaryData?.total_wagered || 0).toFixed(0)}</div>
          <div className="text-slate-500 text-xs mt-2">{summaryData?.pushes || summaryData?.push_bets || 0} pushes</div>
        </div>
        <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
          <div className="text-slate-400 text-sm mb-1">Avg Stake</div>
          <div className="text-3xl font-bold text-orange-400">${(summaryData?.avg_stake || 0).toFixed(0)}</div>
          <div className="text-slate-500 text-xs mt-2">Per bet average</div>
        </div>
      </div>

      {/* Performance Charts */}
      {performanceData && performanceData.history && performanceData.history.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">Cumulative Profit/Loss</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={performanceData.history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9CA3AF" fontSize={10} tickFormatter={(v) => v.slice(5)} />
                <YAxis stroke="#9CA3AF" fontSize={10} tickFormatter={(v) => `$${v}`} />
                <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }} labelStyle={{ color: '#9CA3AF' }} formatter={(value: number) => [`$${value.toFixed(2)}`, 'Cumulative P/L']} />
                <Line type="monotone" dataKey="cumulative_pl" stroke="#10B981" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">Daily Results</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={performanceData.history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9CA3AF" fontSize={10} tickFormatter={(v) => v.slice(5)} />
                <YAxis stroke="#9CA3AF" fontSize={10} />
                <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }} labelStyle={{ color: '#9CA3AF' }} />
                <Bar dataKey="wins" name="Wins" fill="#10B981" stackId="a" />
                <Bar dataKey="losses" name="Losses" fill="#EF4444" stackId="a" />
                <Legend />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Performance Breakdowns */}
      {performanceData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {performanceData.by_sport && performanceData.by_sport.length > 0 && (
            <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
              <h3 className="text-lg font-bold text-white mb-4">Performance by Sport</h3>
              <table className="w-full text-sm">
                <thead><tr className="border-b border-slate-700"><th className="text-left py-2 text-slate-400">Sport</th><th className="text-center py-2 text-slate-400">Bets</th><th className="text-center py-2 text-slate-400">W-L</th><th className="text-center py-2 text-slate-400">Win%</th><th className="text-right py-2 text-slate-400">P/L</th><th className="text-right py-2 text-slate-400">ROI</th></tr></thead>
                <tbody>{performanceData.by_sport.map((s) => (
                  <tr key={s.sport} className="border-b border-slate-700/50">
                    <td className="py-2 text-white font-semibold">{s.sport}</td>
                    <td className="text-center py-2 text-slate-300">{s.total}</td>
                    <td className="text-center py-2 text-slate-300">{s.wins}-{s.losses}</td>
                    <td className="text-center py-2 text-blue-400">{s.win_rate.toFixed(1)}%</td>
                    <td className={`text-right py-2 font-semibold ${s.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'}`}>{s.profit_loss >= 0 ? '+' : ''}${s.profit_loss.toFixed(2)}</td>
                    <td className={`text-right py-2 ${s.roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>{s.roi >= 0 ? '+' : ''}{s.roi.toFixed(1)}%</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
          {performanceData.by_bet_type && performanceData.by_bet_type.length > 0 && (
            <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6">
              <h3 className="text-lg font-bold text-white mb-4">Performance by Bet Type</h3>
              <table className="w-full text-sm">
                <thead><tr className="border-b border-slate-700"><th className="text-left py-2 text-slate-400">Type</th><th className="text-center py-2 text-slate-400">Bets</th><th className="text-center py-2 text-slate-400">W-L</th><th className="text-center py-2 text-slate-400">Win%</th><th className="text-right py-2 text-slate-400">P/L</th><th className="text-right py-2 text-slate-400">ROI</th></tr></thead>
                <tbody>{performanceData.by_bet_type.map((t) => (
                  <tr key={t.bet_type} className="border-b border-slate-700/50">
                    <td className="py-2 text-white font-semibold capitalize">{t.bet_type}</td>
                    <td className="text-center py-2 text-slate-300">{t.total}</td>
                    <td className="text-center py-2 text-slate-300">{t.wins}-{t.losses}</td>
                    <td className="text-center py-2 text-blue-400">{t.win_rate.toFixed(1)}%</td>
                    <td className={`text-right py-2 font-semibold ${t.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'}`}>{t.profit_loss >= 0 ? '+' : ''}${t.profit_loss.toFixed(2)}</td>
                    <td className={`text-right py-2 ${t.roi >= 0 ? 'text-green-400' : 'text-red-400'}`}>{t.roi >= 0 ? '+' : ''}{t.roi.toFixed(1)}%</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Manual Entry Modal */}
      {showManualEntry && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white">Manual Bet Entry</h2>
              <button onClick={() => setShowManualEntry(false)} className="text-slate-400 hover:text-white text-2xl font-bold">x</button>
            </div>
            <form onSubmit={handleManualBetSubmit} className="space-y-4">
              <div><label className="block text-sm font-semibold text-slate-300 mb-2">Sport *</label><select value={manualBetForm.sport} onChange={(e) => setManualBetForm({ ...manualBetForm, sport: e.target.value })} className="w-full px-3 py-2 bg-slate-900 border border-slate-600 text-white rounded" required><option value="NBA">NBA</option><option value="NFL">NFL</option><option value="NHL">NHL</option><option value="MLB">MLB</option><option value="NCAAB">NCAAB</option><option value="NCAAF">NCAAF</option></select></div>
              <div className="grid grid-cols-2 gap-4"><div><label className="block text-sm font-semibold text-slate-300 mb-2">Away Team *</label><input type="text" value={manualBetForm.awayTeam} onChange={(e) => setManualBetForm({ ...manualBetForm, awayTeam: e.target.value })} className="w-full px-3 py-2 bg-slate-900 border border-slate-600 text-white rounded" placeholder="e.g., Lakers" required /></div><div><label className="block text-sm font-semibold text-slate-300 mb-2">Home Team *</label><input type="text" value={manualBetForm.homeTeam} onChange={(e) => setManualBetForm({ ...manualBetForm, homeTeam: e.target.value })} className="w-full px-3 py-2 bg-slate-900 border border-slate-600 text-white rounded" placeholder="e.g., Warriors" required /></div></div>
              <div><label className="block text-sm font-semibold text-slate-300 mb-2">Game Time *</label><input type="datetime-local" value={manualBetForm.commenceTime} onChange={(e) => setManualBetForm({ ...manualBetForm, commenceTime: e.target.value })} className="w-full px-3 py-2 bg-slate-900 border border-slate-600 text-white rounded" required /></div>
              <div className="grid grid-cols-2 gap-4"><div><label className="block text-sm font-semibold text-slate-300 mb-2">Bet Type *</label><select value={manualBetForm.betType} onChange={(e) => setManualBetForm({ ...manualBetForm, betType: e.target.value as any })} className="w-full px-3 py-2 bg-slate-900 border border-slate-600 text-white rounded" required><option value="spread">Spread</option><option value="total">Total</option><option value="moneyline">Moneyline</option><option value="prop">Prop</option></select></div><div><label className="block text-sm font-semibold text-slate-300 mb-2">Bet Side *</label><input type="text" value={manualBetForm.betSide} onChange={(e) => setManualBetForm({ ...manualBetForm, betSide: e.target.value })} className="w-full px-3 py-2 bg-slate-900 border border-slate-600 text-white rounded" placeholder="e.g., OVER 220.5" required /></div></div>
              <div className="grid grid-cols-3 gap-4"><div><label className="block text-sm font-semibold text-slate-300 mb-2">Odds *</label><input type="number" step="1" value={manualBetForm.odds} onChange={(e) => setManualBetForm({ ...manualBetForm, odds: e.target.value })} className="w-full px-3 py-2 bg-slate-900 border border-slate-600 text-white rounded" placeholder="-110" required /></div><div><label className="block text-sm font-semibold text-slate-300 mb-2">Stake ($) *</label><input type="number" step="0.01" value={manualBetForm.stake} onChange={(e) => setManualBetForm({ ...manualBetForm, stake: e.target.value })} className="w-full px-3 py-2 bg-slate-900 border border-slate-600 text-white rounded" placeholder="100.00" required /></div><div><label className="block text-sm font-semibold text-slate-300 mb-2">Bookmaker *</label><input type="text" value={manualBetForm.bookmaker} onChange={(e) => setManualBetForm({ ...manualBetForm, bookmaker: e.target.value })} className="w-full px-3 py-2 bg-slate-900 border border-slate-600 text-white rounded" placeholder="DraftKings" required /></div></div>
              <div className="flex gap-3 pt-4"><button type="submit" className="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded">Add Bet</button><button type="button" onClick={() => setShowManualEntry(false)} className="px-6 py-3 bg-slate-600 hover:bg-slate-700 text-white font-semibold rounded">Cancel</button></div>
            </form>
          </div>
        </div>
      )}

      {/* Pending Bets */}
      {pendingBets.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4"><h2 className="text-2xl font-bold text-white">Pending Bets</h2><span className="text-sm text-slate-400">({pendingBets.length})</span></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {pendingBets.map((bet) => (
              <div key={bet.id} className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-4">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <div className="text-lg font-bold text-white mb-1">{formatTeamName(bet.away_team, sportKeyMapper(bet.sport))} @ {formatTeamName(bet.home_team, sportKeyMapper(bet.sport))}</div>
                    <div className="text-sm text-slate-400 mb-2">{bet.sport} - {new Date(bet.clicked_at).toLocaleDateString()}</div>
                    <div className="flex items-center gap-2">
                      <div className="text-sm text-yellow-400 font-semibold">{bet.bet_side} ({bet.odds > 0 ? '+' : ''}{bet.odds})</div>
                      {canToggleBetSide(bet.bet_side) && <button onClick={() => handleQuickToggleBetSide(bet)} className="px-2 py-1 bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold rounded">Switch</button>}
                    </div>
                  </div>
                  <div className="text-right"><div className="text-xs text-slate-400">Bookmaker</div><div className="text-sm font-semibold text-white">{bet.bookmaker}</div></div>
                </div>
                <div className="flex gap-2">
                  <input type="number" placeholder="Stake ($)" value={stakes[bet.id] || ''} onChange={(e) => setStakes({ ...stakes, [bet.id]: e.target.value })} className="flex-1 px-3 py-2 bg-slate-900 border border-slate-600 text-white rounded" />
                  <button onClick={() => handleAddStake(bet.id)} className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-semibold rounded">Log</button>
                  <button onClick={() => handleStartEdit(bet)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded">Edit</button>
                  <button onClick={() => handleDeleteBet(bet.id)} className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded">X</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Bets */}
      {activeBets.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4"><h2 className="text-2xl font-bold text-white">Active Bets</h2><span className="text-sm text-slate-400">({activeBets.length})</span></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {activeBets.map((bet) => (
              <div key={bet.id} className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="text-lg font-bold text-white mb-1">{formatTeamName(bet.away_team, sportKeyMapper(bet.sport))} @ {formatTeamName(bet.home_team, sportKeyMapper(bet.sport))}</div>
                    <div className="text-sm text-slate-400 mb-1">{bet.sport} - {new Date(bet.commence_time).toLocaleDateString()}</div>
                    <div className="text-sm text-blue-400 font-semibold">{bet.bet_side} ({bet.odds > 0 ? '+' : ''}{bet.odds})</div>
                  </div>
                  <div className="text-right"><div className="text-xs text-slate-400">Stake</div><div className="text-lg font-bold text-white">${bet.stake.toFixed(2)}</div></div>
                </div>
                <div className="text-xs text-slate-400 mb-3">Bookmaker: {bet.bookmaker}</div>
                <div className="border-t border-slate-700 pt-3">
                  <div className="text-xs text-slate-400 mb-2 font-semibold">SETTLE BET:</div>
                  <div className="grid grid-cols-4 gap-2">
                    <button onClick={() => handleSettleBet(bet.id, 'win')} className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white font-bold text-sm rounded">WON</button>
                    <button onClick={() => handleSettleBet(bet.id, 'loss')} className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white font-bold text-sm rounded">LOST</button>
                    <button onClick={() => handleSettleBet(bet.id, 'push')} className="px-3 py-2 bg-slate-600 hover:bg-slate-700 text-white font-bold text-sm rounded">PUSH</button>
                    <button onClick={() => handleStartEdit(bet)} className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm rounded">Edit</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Settled Bets Table */}
      {settledBets.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4"><h2 className="text-2xl font-bold text-white">Settled Bets</h2><span className="text-sm text-slate-400">({settledBets.length})</span></div>
          <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6 overflow-x-auto">
            <table className="w-full">
              <thead><tr className="border-b border-slate-700"><th className="text-left py-3 px-4 text-slate-300 font-semibold">Date</th><th className="text-left py-3 px-4 text-slate-300 font-semibold">Game</th><th className="text-left py-3 px-4 text-slate-300 font-semibold">Bet</th><th className="text-right py-3 px-4 text-slate-300 font-semibold">Stake</th><th className="text-right py-3 px-4 text-slate-300 font-semibold">Odds</th><th className="text-center py-3 px-4 text-slate-300 font-semibold">Result</th><th className="text-right py-3 px-4 text-slate-300 font-semibold">P/L</th></tr></thead>
              <tbody>{settledBets.slice(0, 50).map((bet) => (
                <tr key={bet.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="py-3 px-4 text-sm text-slate-400">{new Date(bet.settled_at).toLocaleDateString()}</td>
                  <td className="py-3 px-4 text-sm text-white">{formatTeamName(bet.away_team, sportKeyMapper(bet.sport))} @ {formatTeamName(bet.home_team, sportKeyMapper(bet.sport))}</td>
                  <td className="py-3 px-4 text-sm text-slate-300">{bet.bet_side}</td>
                  <td className="text-right py-3 px-4 text-sm text-white">${bet.stake.toFixed(2)}</td>
                  <td className="text-right py-3 px-4 text-sm text-slate-300">{bet.odds > 0 ? '+' : ''}{bet.odds}</td>
                  <td className="text-center py-3 px-4"><span className={`px-3 py-1 text-xs font-bold rounded ${bet.status === 'won' ? 'bg-green-900 text-green-300' : bet.status === 'lost' ? 'bg-red-900 text-red-300' : 'bg-slate-700 text-slate-300'}`}>{bet.status.toUpperCase()}</span></td>
                  <td className={`text-right py-3 px-4 text-sm font-bold ${bet.profit_loss > 0 ? 'text-green-400' : bet.profit_loss < 0 ? 'text-red-400' : 'text-slate-400'}`}>{bet.profit_loss > 0 ? '+' : ''}${bet.profit_loss.toFixed(2)}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty State */}
      {pendingBets.length === 0 && activeBets.length === 0 && settledBets.length === 0 && (
        <div className="text-center py-20">
          <h3 className="text-2xl font-bold text-white mb-2">No Bets Yet</h3>
          <p className="text-slate-400 mb-6">Start tracking your bets by clicking bookmaker icons on game cards</p>
        </div>
      )}

      {/* Settle Confirmation Modal */}
      {settleConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6 max-w-md w-full">
            <h3 className="text-xl font-bold text-white mb-4">{settleConfirmation.result === 'win' ? 'Mark as WON?' : settleConfirmation.result === 'loss' ? 'Mark as LOST?' : 'Mark as PUSH?'}</h3>
            <p className="text-slate-300 mb-6">{settleConfirmation.result === 'win' ? 'This bet won.' : settleConfirmation.result === 'loss' ? 'This bet lost.' : 'This bet pushed.'}</p>
            <div className="flex gap-3">
              <button onClick={confirmSettleBet} className={`flex-1 px-6 py-3 font-bold rounded ${settleConfirmation.result === 'win' ? 'bg-green-600 hover:bg-green-700' : settleConfirmation.result === 'loss' ? 'bg-red-600 hover:bg-red-700' : 'bg-slate-600 hover:bg-slate-700'} text-white`}>Confirm</button>
              <button onClick={() => setSettleConfirmation(null)} className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Bet Modal */}
      {editingBetId && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-black border border-white rounded-xl p-6 max-w-md w-full">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-white">Edit Bet</h3>
              <button onClick={handleCancelEdit} className="text-slate-400 hover:text-white text-2xl font-bold">×</button>
            </div>
            <div className="space-y-4">
              {/* Bet Side Toggle for Totals */}
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">Bet Side *</label>
                {editForm.betType === 'total' ? (
                  <div className="flex gap-2">
                    <button type="button" onClick={() => setEditForm({ ...editForm, betSide: 'OVER' })} className={`flex-1 py-2 px-3 rounded font-bold text-sm ${editForm.betSide === 'OVER' ? 'bg-green-600 text-white border-2 border-green-400' : 'bg-slate-700 text-slate-300 border border-slate-600'}`}>OVER</button>
                    <button type="button" onClick={() => setEditForm({ ...editForm, betSide: 'UNDER' })} className={`flex-1 py-2 px-3 rounded font-bold text-sm ${editForm.betSide === 'UNDER' ? 'bg-red-600 text-white border-2 border-red-400' : 'bg-slate-700 text-slate-300 border border-slate-600'}`}>UNDER</button>
                  </div>
                ) : (
                  <input type="text" value={editForm.betSide} onChange={(e) => setEditForm({ ...editForm, betSide: e.target.value })} className="w-full px-3 py-2 bg-slate-900 border border-slate-600 text-white rounded" placeholder="e.g., Lakers" />
                )}
              </div>
              {/* Line Input for Totals/Spreads */}
              <div>
                <label className="block text-sm font-semibold text-yellow-400 mb-2">Line (Total/Spread)</label>
                <div className="flex items-center gap-2">
                  <button type="button" onClick={() => setEditForm({ ...editForm, line: (parseFloat(editForm.line || '0') - 0.5).toString() })} className="w-10 h-10 bg-slate-700 hover:bg-slate-600 text-white rounded font-bold text-lg border border-slate-600">-</button>
                  <input type="number" step="0.5" value={editForm.line} onChange={(e) => setEditForm({ ...editForm, line: e.target.value })} className="flex-1 px-3 py-2 bg-slate-900 border-2 border-yellow-500/50 text-white rounded text-center font-bold" placeholder="220.5" />
                  <button type="button" onClick={() => setEditForm({ ...editForm, line: (parseFloat(editForm.line || '0') + 0.5).toString() })} className="w-10 h-10 bg-slate-700 hover:bg-slate-600 text-white rounded font-bold text-lg border border-slate-600">+</button>
                </div>
                <p className="text-xs text-slate-400 mt-1">For totals (e.g., 220.5) or spreads (e.g., -5.5)</p>
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">Odds (American) *</label>
                <input type="number" value={editForm.odds} onChange={(e) => setEditForm({ ...editForm, odds: e.target.value })} className="w-full px-3 py-2 bg-slate-900 border border-slate-600 text-white rounded" placeholder="-110" />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">Stake ($)</label>
                <input type="number" step="0.01" value={editForm.stake} onChange={(e) => setEditForm({ ...editForm, stake: e.target.value })} className="w-full px-3 py-2 bg-slate-900 border border-slate-600 text-white rounded" placeholder="100.00" />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">Bookmaker *</label>
                <input type="text" value={editForm.bookmaker} onChange={(e) => setEditForm({ ...editForm, bookmaker: e.target.value })} className="w-full px-3 py-2 bg-slate-900 border border-slate-600 text-white rounded" placeholder="DraftKings" />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => handleSaveEdit(editingBetId)} className="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded">Save Changes</button>
              <button onClick={handleCancelEdit} className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
