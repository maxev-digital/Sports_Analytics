import { useState, useEffect } from 'react';

interface ArbitrageAlert {
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  market_type: string;
  book_a: string;
  book_b: string;
  odds_a: number;
  odds_b: number;
  profit_percent: number;
  stake_a: number;
  stake_b: number;
  total_stake: number;
  guaranteed_profit: number;
  timestamp: string;
  expires_in: number;
}

interface SteamMoveAlert {
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  market_type: string;
  side: string;
  original_line: number;
  new_line: number;
  movement: number;
  books_moved: string[];
  consensus_percent: number;
  timestamp: string;
}

interface LineMovementAlert {
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  market_type: string;
  bookmaker: string;
  original_line: number;
  new_line: number;
  movement: number;
  movement_percent: number;
  timestamp: string;
}

interface AlertsData {
  arbitrage: { count: number; alerts: ArbitrageAlert[] };
  steam_moves: { count: number; alerts: SteamMoveAlert[] };
  line_movements: { count: number; alerts: LineMovementAlert[] };
}

export function Alerts() {
  const [alertsData, setAlertsData] = useState<AlertsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'arbitrage' | 'steam' | 'lines'>('arbitrage');
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchAlerts = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/alerts/all');
      if (!response.ok) throw new Error('Failed to fetch alerts');
      const data = await response.json();
      setAlertsData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();

    if (autoRefresh) {
      const interval = setInterval(fetchAlerts, 10000); // Refresh every 10 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const formatExpiresIn = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h`;
  };

  const getSportBadgeColor = (sport: string) => {
    if (sport.includes('nba')) return 'bg-orange-500';
    if (sport.includes('nfl')) return 'bg-green-500';
    if (sport.includes('nhl')) return 'bg-blue-500';
    if (sport.includes('ncaa')) return 'bg-purple-500';
    return 'bg-gray-500';
  };

  const getMarketLabel = (marketType: string) => {
    if (marketType === 'h2h') return 'Moneyline';
    if (marketType === 'spreads') return 'Spread';
    if (marketType === 'totals') return 'Total';
    return marketType;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading alerts...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-red-400 text-xl">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold text-slate-100 mb-2">Live Alerts</h1>
              <p className="text-slate-400">Real-time betting opportunities detected every 10 seconds</p>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  autoRefresh
                    ? 'bg-green-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {autoRefresh ? '● Auto-Refresh ON' : 'Auto-Refresh OFF'}
              </button>
              <button
                onClick={fetchAlerts}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
              >
                Refresh Now
              </button>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
              <div className="text-sm text-slate-400 mb-1">Arbitrage Opportunities</div>
              <div className="text-3xl font-bold text-green-400">{alertsData?.arbitrage.count || 0}</div>
            </div>
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
              <div className="text-sm text-slate-400 mb-1">Steam Moves</div>
              <div className="text-3xl font-bold text-orange-400">{alertsData?.steam_moves.count || 0}</div>
            </div>
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
              <div className="text-sm text-slate-400 mb-1">Line Movements</div>
              <div className="text-3xl font-bold text-blue-400">{alertsData?.line_movements.count || 0}</div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('arbitrage')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === 'arbitrage'
                ? 'bg-green-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Arbitrage ({alertsData?.arbitrage.count || 0})
          </button>
          <button
            onClick={() => setActiveTab('steam')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === 'steam'
                ? 'bg-orange-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Steam Moves ({alertsData?.steam_moves.count || 0})
          </button>
          <button
            onClick={() => setActiveTab('lines')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === 'lines'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            Line Movements ({alertsData?.line_movements.count || 0})
          </button>
        </div>

        {/* Arbitrage Alerts */}
        {activeTab === 'arbitrage' && (
          <div className="space-y-4">
            {alertsData?.arbitrage.alerts.length === 0 ? (
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-12 text-center">
                <div className="text-slate-400 text-lg">No arbitrage opportunities detected</div>
                <div className="text-slate-500 text-sm mt-2">Scanning every 10 seconds...</div>
              </div>
            ) : (
              alertsData?.arbitrage.alerts.map((alert, idx) => (
                <div key={idx} className="bg-gradient-to-r from-green-900/20 to-green-800/20 border border-green-700/50 rounded-lg p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold text-white ${getSportBadgeColor(alert.sport)}`}>
                        {alert.sport.toUpperCase()}
                      </span>
                      <span className="px-3 py-1 rounded-full text-xs font-bold bg-green-600 text-white">
                        {getMarketLabel(alert.market_type)}
                      </span>
                      <span className="text-lg font-bold text-white">
                        {alert.away_team} @ {alert.home_team}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-green-400">
                        +{alert.profit_percent.toFixed(2)}%
                      </div>
                      <div className="text-sm text-slate-400">
                        Expires in {formatExpiresIn(alert.expires_in)}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <div className="text-sm text-slate-400 mb-2">Book A: {alert.book_a}</div>
                      <div className="text-xl font-bold text-white mb-1">
                        {alert.odds_a > 0 ? `+${alert.odds_a}` : alert.odds_a}
                      </div>
                      <div className="text-sm text-slate-300">
                        Stake: ${alert.stake_a.toFixed(2)}
                      </div>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <div className="text-sm text-slate-400 mb-2">Book B: {alert.book_b}</div>
                      <div className="text-xl font-bold text-white mb-1">
                        {alert.odds_b > 0 ? `+${alert.odds_b}` : alert.odds_b}
                      </div>
                      <div className="text-sm text-slate-300">
                        Stake: ${alert.stake_b.toFixed(2)}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <div className="text-slate-400">
                      Total Investment: ${alert.total_stake.toFixed(2)}
                    </div>
                    <div className="text-green-400 font-bold">
                      Guaranteed Profit: ${alert.guaranteed_profit.toFixed(2)}
                    </div>
                    <div className="text-slate-500">
                      {formatTime(alert.timestamp)}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Steam Move Alerts */}
        {activeTab === 'steam' && (
          <div className="space-y-4">
            {alertsData?.steam_moves.alerts.length === 0 ? (
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-12 text-center">
                <div className="text-slate-400 text-lg">No steam moves detected</div>
                <div className="text-slate-500 text-sm mt-2">Scanning every 10 seconds...</div>
              </div>
            ) : (
              alertsData?.steam_moves.alerts.map((alert, idx) => (
                <div key={idx} className="bg-gradient-to-r from-orange-900/20 to-orange-800/20 border border-orange-700/50 rounded-lg p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold text-white ${getSportBadgeColor(alert.sport)}`}>
                        {alert.sport.toUpperCase()}
                      </span>
                      <span className="px-3 py-1 rounded-full text-xs font-bold bg-orange-600 text-white">
                        {getMarketLabel(alert.market_type)}
                      </span>
                      <span className="text-lg font-bold text-white">
                        {alert.away_team} @ {alert.home_team}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-slate-400">Consensus</div>
                      <div className="text-2xl font-bold text-orange-400">
                        {alert.consensus_percent.toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-800/50 rounded-lg p-4 mb-4">
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-sm text-slate-400 mb-1">Original Line</div>
                        <div className="text-xl font-bold text-white">{alert.original_line}</div>
                      </div>
                      <div>
                        <div className="text-sm text-slate-400 mb-1">Movement</div>
                        <div className={`text-xl font-bold ${alert.movement > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {alert.movement > 0 ? '+' : ''}{alert.movement.toFixed(1)}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-slate-400 mb-1">New Line</div>
                        <div className="text-xl font-bold text-white">{alert.new_line}</div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <div className="text-slate-400">
                      Books Moved: {alert.books_moved.join(', ')}
                    </div>
                    <div className="text-slate-500">
                      {formatTime(alert.timestamp)}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Line Movement Alerts */}
        {activeTab === 'lines' && (
          <div className="space-y-4">
            {alertsData?.line_movements.alerts.length === 0 ? (
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-12 text-center">
                <div className="text-slate-400 text-lg">No significant line movements detected</div>
                <div className="text-slate-500 text-sm mt-2">Scanning every 10 seconds...</div>
              </div>
            ) : (
              alertsData?.line_movements.alerts.map((alert, idx) => (
                <div key={idx} className="bg-gradient-to-r from-blue-900/20 to-blue-800/20 border border-blue-700/50 rounded-lg p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold text-white ${getSportBadgeColor(alert.sport)}`}>
                        {alert.sport.toUpperCase()}
                      </span>
                      <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-600 text-white">
                        {getMarketLabel(alert.market_type)}
                      </span>
                      <span className="text-lg font-bold text-white">
                        {alert.away_team} @ {alert.home_team}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-slate-400">{alert.bookmaker}</div>
                      <div className="text-2xl font-bold text-blue-400">
                        {alert.movement_percent.toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-800/50 rounded-lg p-4 mb-4">
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-sm text-slate-400 mb-1">Original</div>
                        <div className="text-xl font-bold text-white">{alert.original_line}</div>
                      </div>
                      <div>
                        <div className="text-sm text-slate-400 mb-1">Movement</div>
                        <div className={`text-xl font-bold ${alert.movement > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {alert.movement > 0 ? '+' : ''}{alert.movement.toFixed(1)}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-slate-400 mb-1">New Line</div>
                        <div className="text-xl font-bold text-white">{alert.new_line}</div>
                      </div>
                    </div>
                  </div>

                  <div className="text-sm text-slate-500 text-right">
                    {formatTime(alert.timestamp)}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
