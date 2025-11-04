import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getApiUrl } from '../config';

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
                    {bet.away_team} @ {bet.home_team}
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
    </div>
  );
}
