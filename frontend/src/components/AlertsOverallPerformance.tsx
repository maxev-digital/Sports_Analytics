import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';

interface OverallStats {
  win_rate: number;
  roi: number;
  total_bets: number;
  total_profit: number;
  wins: number;
  losses: number;
}

export function AlertsOverallPerformance() {
  const [stats, setStats] = useState<OverallStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedBetType, setSelectedBetType] = useState<string>('all');
  const [selectedSport, setSelectedSport] = useState<string>('all');

  const betTypes = [
    { key: 'all', name: 'ALL', emoji: '🎯' },
    { key: 'totals', name: 'TOTALS', emoji: '📊' },
    { key: 'spreads', name: 'SPREADS', emoji: '📈' },
    { key: 'moneyline', name: 'MONEYLINE', emoji: '💰' },
  ];

  const sports = [
    { key: 'all', name: 'ALL', emoji: '🎯' },
    { key: 'NBA', name: 'NBA', emoji: '🏀' },
    { key: 'NFL', name: 'NFL', emoji: '🏈' },
    { key: 'NHL', name: 'NHL', emoji: '🏒' },
    { key: 'NCAAB', name: 'NCAAB', emoji: '🏀' },
    { key: 'NCAAF', name: 'NCAAF', emoji: '🏈' },
  ];

  useEffect(() => {
    fetchOverallStats();
  }, [selectedBetType, selectedSport]);

  const fetchOverallStats = async () => {
    try {
      setLoading(true);
      let url = 'performance/summary?days=365';

      // Add filters if not 'all'
      if (selectedBetType !== 'all') {
        url += `&bet_type=${selectedBetType}`;
      }
      if (selectedSport !== 'all') {
        url += `&sport=${selectedSport}`;
      }

      const response = await fetch(getApiUrl(url));
      if (response.ok) {
        const data = await response.json();

        // Calculate stats from the API response
        const overall = data.overall || {};
        setStats({
          win_rate: overall.win_rate || 0,
          roi: overall.roi || 0,
          total_bets: overall.total_predictions || 0,
          total_profit: overall.profit_loss || 0,
          wins: overall.wins || 0,
          losses: overall.losses || 0,
        });
      }
    } catch (error) {
      console.error('Error fetching overall stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 mb-3">
        <div className="text-white text-center text-sm">Loading overall performance...</div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="mb-3">
      <h2 className="text-sm font-bold text-blue-300 mb-2">Overall Alerts Performance</h2>

      {/* Filter Buttons */}
      <div className="mb-3 space-y-2">
        {/* Bet Type Filters */}
        <div className="flex flex-wrap gap-2">
          <span className="text-slate-400 text-xs font-semibold self-center mr-1">Bet Type:</span>
          {betTypes.map((betType) => (
            <button
              key={betType.key}
              onClick={() => setSelectedBetType(betType.key)}
              className={`px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-2 rounded ${
                selectedBetType === betType.key
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              <span className="text-sm">{betType.emoji}</span>
              {betType.name}
            </button>
          ))}
        </div>

        {/* Sport Filters */}
        <div className="flex flex-wrap gap-2">
          <span className="text-slate-400 text-xs font-semibold self-center mr-1">Sport:</span>
          {sports.map((sport) => (
            <button
              key={sport.key}
              onClick={() => setSelectedSport(sport.key)}
              className={`px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-2 rounded ${
                selectedSport === sport.key
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              <span className="text-sm">{sport.emoji}</span>
              {sport.name}
            </button>
          ))}
        </div>
      </div>

      {/* Performance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
        {/* Win Rate */}
        <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 border border-green-700 rounded-lg p-1.5">
          <div className="text-green-400 text-xs font-semibold mb-0">Win Rate</div>
          <div className="text-white text-3xl font-bold leading-tight">
            {stats.win_rate.toFixed(1)}%
          </div>
          <div className="text-green-300 text-xs mt-0">
            {stats.wins}W-{stats.losses}L
          </div>
        </div>

        {/* ROI */}
        <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border border-blue-700 rounded-lg p-1.5">
          <div className="text-blue-400 text-xs font-semibold mb-0">ROI</div>
          <div className="text-white text-3xl font-bold leading-tight">
            {stats.roi >= 0 ? '+' : ''}{stats.roi.toFixed(1)}%
          </div>
          <div className="text-blue-300 text-xs mt-0">All-Time</div>
        </div>

        {/* Total Bets */}
        <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border border-purple-700 rounded-lg p-1.5">
          <div className="text-purple-400 text-xs font-semibold mb-0">Total Bets</div>
          <div className="text-white text-3xl font-bold leading-tight">
            {stats.total_bets.toLocaleString()}
          </div>
          <div className="text-purple-300 text-xs mt-0">Graded</div>
        </div>

        {/* Total Profit (in Units) */}
        <div className="bg-gradient-to-br from-amber-900/50 to-amber-800/30 border border-amber-700 rounded-lg p-1.5">
          <div className="text-amber-400 text-xs font-semibold mb-0">Total Profit</div>
          <div className="text-white text-3xl font-bold leading-tight">
            {stats.total_profit >= 0 ? '+' : ''}${stats.total_profit.toFixed(0)}
          </div>
          <div className="text-amber-300 text-xs mt-0">
            {(stats.total_profit / 100).toFixed(1)} Units
          </div>
        </div>
      </div>
    </div>
  );
}
