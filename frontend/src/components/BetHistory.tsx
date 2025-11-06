import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getApiUrl } from '../config';
import { formatTeamName } from '../utils/teamNames';


// Helper function to convert sport names to sport keys
const sportKeyMapper = (sport: string): string => {
  const sportMap: Record<string, string> = {
    'NBA': 'basketball_nba',
    'NCAAB': 'basketball_ncaab',
    'NFL': 'americanfootball_nfl',
    'NCAAF': 'americanfootball_ncaaf',
    'NHL': 'icehockey_nhl',
    'MLB': 'baseball_mlb',
    'Basketball': 'basketball_nba',
    'Football': 'americanfootball_nfl',
    'Hockey': 'icehockey_nhl',
    'Baseball': 'baseball_mlb',
  };
  return sportMap[sport] || sport.toLowerCase();
};

interface Bet {
  id: string;
  sport: string;
  home_team: string;
  away_team: string;
  bet_type: string;
  bet_side: string;
  odds: number;
  stake: number;
  bookmaker: string;
  confidence?: string;
  status: 'win' | 'loss' | 'push';
  result?: string;
  profit_loss: number;
  commence_time: string;
  settled_at: string;
  notes?: string;
}

export function BetHistory() {
  const { username } = useAuth();
  const [bets, setBets] = useState<Bet[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortField, setSortField] = useState<'settled_at' | 'profit_loss' | 'stake'>('settled_at');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [editingBet, setEditingBet] = useState<Bet | null>(null);
  const [editForm, setEditForm] = useState({
    odds: 0,
    stake: 0,
    bookmaker: '',
    bet_side: ''
  });

  useEffect(() => {
    fetchBetHistory();
  }, [username]);

  const fetchBetHistory = async () => {
    if (!username) {
      setLoading(false);
      return;
    }

    try {
      // Use my-bets endpoint with user_id parameter
      const response = await fetch(getApiUrl(`bets/my-bets?user_id=${username}`));
      if (response.ok) {
        const allBets = await response.json();
        // Filter for only graded/settled bets
        const gradedBets = allBets.filter((bet: Bet) =>
          ['win', 'loss', 'push'].includes(bet.status)
        );
        setBets(gradedBets);
      } else {
        console.error('Failed to fetch bet history:', response.status);
      }
    } catch (error) {
      console.error('Error fetching bet history:', error);
    } finally {
      setLoading(false);
    }
  };

  const openEditModal = (bet: Bet) => {
    setEditingBet(bet);
    setEditForm({
      odds: bet.odds,
      stake: bet.stake,
      bookmaker: bet.bookmaker,
      bet_side: bet.bet_side
    });
  };

  const closeEditModal = () => {
    setEditingBet(null);
  };

  const handleEditSubmit = async () => {
    if (!editingBet) return;

    try {
      const response = await fetch(getApiUrl(`bets/${editingBet.id}/update`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          odds: editForm.odds,
          stake: editForm.stake,
          bookmaker: editForm.bookmaker,
          bet_side: editForm.bet_side
        })
      });

      if (response.ok) {
        // Refresh bet history after successful update
        await fetchBetHistory();
        closeEditModal();
      } else {
        console.error('Failed to update bet:', response.status);
        alert('Failed to update bet. Please try again.');
      }
    } catch (error) {
      console.error('Error updating bet:', error);
      alert('Error updating bet. Please try again.');
    }
  };

  const toggleSort = (field: typeof sortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getSortedBets = () => {
    return [...bets].sort((a, b) => {
      let aVal, bVal;

      if (sortField === 'settled_at') {
        aVal = new Date(a.settled_at).getTime();
        bVal = new Date(b.settled_at).getTime();
      } else if (sortField === 'profit_loss') {
        aVal = a.profit_loss;
        bVal = b.profit_loss;
      } else {
        aVal = a.stake;
        bVal = b.stake;
      }

      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    });
  };

  const SortIndicator = ({ field }: { field: typeof sortField }) => {
    if (sortField !== field) return <span className="text-slate-600">⇅</span>;
    return <span className="text-blue-400">{sortDirection === 'asc' ? '↑' : '↓'}</span>;
  };

  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="text-white text-xl">Loading bet history...</div>
      </div>
    );
  }

  if (bets.length === 0) {
    return (
      <div className="text-center py-20">
        <div className="text-4xl mb-4">📊</div>
        <h3 className="text-2xl font-bold text-white mb-2">No Bet History Yet</h3>
        <p className="text-slate-400">
          Your graded bets will appear here automatically once you settle them in My Bets
        </p>
      </div>
    );
  }

  const sortedBets = getSortedBets();

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-white mb-2">Bet History</h2>
        <p className="text-slate-400">Complete record of all graded bets ({bets.length} total)</p>
      </div>

      <div className="bg-slate-900 border-2 border-slate-700 overflow-hidden">
        {/* Mobile scroll hint */}
        <div className="md:hidden bg-blue-900/40 border-b-2 border-blue-600 px-4 py-2 text-center">
          <span className="text-blue-300 text-xs font-semibold">← Scroll horizontally to see all columns →</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse min-w-[1000px]">
            <thead className="bg-slate-800 sticky top-0 z-10">
              <tr className="border-b-2 border-slate-600">
                <th
                  onClick={() => toggleSort('settled_at')}
                  className="text-left py-3 px-4 text-slate-300 font-bold text-xs uppercase tracking-wider cursor-pointer hover:bg-slate-700 transition-colors"
                >
                  Date <SortIndicator field="settled_at" />
                </th>
                <th className="text-left py-3 px-4 text-slate-300 font-bold text-xs uppercase tracking-wider">
                  Sport
                </th>
                <th className="text-left py-3 px-4 text-slate-300 font-bold text-xs uppercase tracking-wider">
                  Game
                </th>
                <th className="text-left py-3 px-4 text-slate-300 font-bold text-xs uppercase tracking-wider">
                  Bet
                </th>
                <th className="text-center py-3 px-4 text-slate-300 font-bold text-xs uppercase tracking-wider">
                  Odds
                </th>
                <th
                  onClick={() => toggleSort('stake')}
                  className="text-right py-3 px-4 text-slate-300 font-bold text-xs uppercase tracking-wider cursor-pointer hover:bg-slate-700 transition-colors"
                >
                  Stake <SortIndicator field="stake" />
                </th>
                <th className="text-center py-3 px-4 text-slate-300 font-bold text-xs uppercase tracking-wider">
                  Result
                </th>
                <th
                  onClick={() => toggleSort('profit_loss')}
                  className="text-right py-3 px-4 text-slate-300 font-bold text-xs uppercase tracking-wider cursor-pointer hover:bg-slate-700 transition-colors"
                >
                  P/L <SortIndicator field="profit_loss" />
                </th>
                <th className="text-center py-3 px-4 text-slate-300 font-bold text-xs uppercase tracking-wider">
                  Book
                </th>
                <th className="text-center py-3 px-4 text-slate-300 font-bold text-xs uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedBets.map((bet, idx) => (
                <tr
                  key={bet.id}
                  className={`border-b border-slate-700/50 hover:bg-slate-800/50 transition-colors ${
                    idx % 2 === 0 ? 'bg-slate-900/50' : 'bg-slate-900/30'
                  }`}
                >
                  <td className="py-3 px-4 text-sm text-slate-400">
                    {new Date(bet.settled_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-1 bg-slate-700 text-slate-300 text-xs rounded font-semibold">
                      {bet.sport}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-white">
                    {formatTeamName(bet.away_team, sportKeyMapper(bet.sport))} @ {formatTeamName(bet.home_team, sportKeyMapper(bet.sport))}
                  </td>
                  <td className="py-3 px-4 text-sm text-slate-300">
                    <div className="font-semibold">{bet.bet_side}</div>
                    {bet.confidence && (
                      <div className={`text-xs mt-1 ${
                        bet.confidence === 'HIGH' ? 'text-green-400' :
                        bet.confidence === 'MEDIUM' ? 'text-yellow-400' :
                        'text-slate-400'
                      }`}>
                        {bet.confidence}
                      </div>
                    )}
                  </td>
                  <td className="py-3 px-4 text-center text-sm text-slate-300">
                    {bet.odds > 0 ? '+' : ''}{bet.odds}
                  </td>
                  <td className="py-3 px-4 text-right text-sm font-semibold text-white">
                    ${bet.stake.toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className={`px-3 py-1 text-xs font-bold rounded ${
                      bet.status === 'win' ? 'bg-green-900 text-green-300 border border-green-600' :
                      bet.status === 'loss' ? 'bg-red-900 text-red-300 border border-red-600' :
                      'bg-slate-700 text-slate-300 border border-slate-600'
                    }`}>
                      {bet.status.toUpperCase()}
                    </span>
                  </td>
                  <td className={`py-3 px-4 text-right text-sm font-bold ${
                    bet.profit_loss > 0 ? 'text-green-400' :
                    bet.profit_loss < 0 ? 'text-red-400' :
                    'text-slate-400'
                  }`}>
                    {bet.profit_loss > 0 ? '+' : ''}${bet.profit_loss.toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-center text-xs text-slate-400">
                    {bet.bookmaker}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => openEditModal(bet)}
                      className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded transition-colors"
                      title="Edit bet details"
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border-2 border-green-700 p-4">
          <div className="text-xs text-slate-400 mb-1">Total P/L</div>
          <div className={`text-2xl font-bold ${
            bets.reduce((sum, b) => sum + b.profit_loss, 0) > 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            ${bets.reduce((sum, b) => sum + b.profit_loss, 0).toFixed(2)}
          </div>
        </div>
        <div className="bg-slate-900 border-2 border-blue-700 p-4">
          <div className="text-xs text-slate-400 mb-1">Win Rate</div>
          <div className="text-2xl font-bold text-blue-400">
            {((bets.filter(b => b.status === 'win').length / bets.filter(b => b.status !== 'push').length) * 100).toFixed(1)}%
          </div>
        </div>
        <div className="bg-slate-900 border-2 border-purple-700 p-4">
          <div className="text-xs text-slate-400 mb-1">Total Wagered</div>
          <div className="text-2xl font-bold text-white">
            ${bets.reduce((sum, b) => sum + b.stake, 0).toFixed(2)}
          </div>
        </div>
        <div className="bg-slate-900 border-2 border-slate-700 p-4">
          <div className="text-xs text-slate-400 mb-1">Avg Bet Size</div>
          <div className="text-2xl font-bold text-white">
            ${(bets.reduce((sum, b) => sum + b.stake, 0) / bets.length).toFixed(2)}
          </div>
        </div>
      </div>

      {/* Edit Bet Modal */}
      {editingBet && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border-2 border-slate-700 rounded-lg max-w-md w-full p-6">
            <h3 className="text-2xl font-bold text-white mb-4">Edit Bet</h3>

            <div className="space-y-4">
              {/* Game Info (read-only) */}
              <div className="bg-slate-800 p-3 rounded border border-slate-700">
                <div className="text-xs text-slate-400 mb-1">Game</div>
                <div className="text-sm text-white font-semibold">
                  {formatTeamName(editingBet.away_team, sportKeyMapper(editingBet.sport))} @ {formatTeamName(editingBet.home_team, sportKeyMapper(editingBet.sport))}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {editingBet.sport} • {new Date(editingBet.settled_at).toLocaleDateString()}
                </div>
              </div>

              {/* Bet Side */}
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Bet Side</label>
                <input
                  type="text"
                  value={editForm.bet_side}
                  onChange={(e) => setEditForm({ ...editForm, bet_side: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white text-sm"
                />
              </div>

              {/* Odds */}
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Odds (American)</label>
                <input
                  type="number"
                  value={editForm.odds}
                  onChange={(e) => setEditForm({ ...editForm, odds: parseFloat(e.target.value) })}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white text-sm"
                />
              </div>

              {/* Stake */}
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Stake ($)</label>
                <input
                  type="number"
                  step="0.01"
                  value={editForm.stake}
                  onChange={(e) => setEditForm({ ...editForm, stake: parseFloat(e.target.value) })}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white text-sm"
                />
              </div>

              {/* Bookmaker */}
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Bookmaker</label>
                <input
                  type="text"
                  value={editForm.bookmaker}
                  onChange={(e) => setEditForm({ ...editForm, bookmaker: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white text-sm"
                />
              </div>

              {/* Result Info (read-only) */}
              <div className="bg-slate-800 p-3 rounded border border-slate-700">
                <div className="flex justify-between items-center">
                  <div>
                    <div className="text-xs text-slate-400">Result</div>
                    <div className={`text-sm font-bold ${
                      editingBet.status === 'win' ? 'text-green-400' :
                      editingBet.status === 'loss' ? 'text-red-400' :
                      'text-slate-400'
                    }`}>
                      {editingBet.status.toUpperCase()}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-400">P/L</div>
                    <div className={`text-sm font-bold ${
                      editingBet.profit_loss > 0 ? 'text-green-400' :
                      editingBet.profit_loss < 0 ? 'text-red-400' :
                      'text-slate-400'
                    }`}>
                      {editingBet.profit_loss > 0 ? '+' : ''}${editingBet.profit_loss.toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Warning */}
              <div className="bg-yellow-900/30 border border-yellow-700 rounded p-3">
                <p className="text-xs text-yellow-300">
                  Note: The bet will be automatically re-graded with the updated odds and stake. The result ({editingBet.status}) will remain the same.
                </p>
              </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={closeEditModal}
                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleEditSubmit}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded transition-colors"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
