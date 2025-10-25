import { useState, useEffect, useRef } from 'react';
import { GoaliePullAlerts } from '../components/GoaliePullAlert';
import { FavoriteComebackAlerts } from '../components/FavoriteComebackAlert';
import { HalftimeTrackerAlerts } from '../components/HalftimeTrackerAlert';
import { MomentumAlerts } from '../components/MomentumAlert';

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
  const [goaliePullCount, setGoaliePullCount] = useState(0);
  const [favoriteComebackCount, setFavoriteComebackCount] = useState(0);
  const [halftimeCount, setHalftimeCount] = useState(0);
  const [momentumCount, setMomentumCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'arbitrage' | 'steam' | 'lines' | 'goalie' | 'comeback' | 'halftime' | 'momentum'>('comeback');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const alertBellRef = useRef<HTMLAudioElement>(null);
  const sirenRef = useRef<HTMLAudioElement>(null);
  const previousCountRef = useRef({ arbitrage: 0, steam: 0, lines: 0 });

  const fetchAlerts = async () => {
    try {
      const [alertsResponse, goalieResponse, comebackResponse, halftimeResponse, momentumResponse] = await Promise.all([
        fetch('/api/alerts/all?user_id=default'),
        fetch('/api/goalie-pull-opportunities'),
        fetch('/api/favorite-comeback-opportunities'),
        fetch('/api/halftime-opportunities'),
        fetch('/api/momentum-opportunities')
      ]);

      if (!alertsResponse.ok) throw new Error('Failed to fetch alerts');

      const alertsData = await alertsResponse.json();
      setAlertsData(alertsData);

      if (goalieResponse.ok) {
        const goalieData = await goalieResponse.json();
        setGoaliePullCount(goalieData.count || 0);
      }

      if (comebackResponse.ok) {
        const comebackData = await comebackResponse.json();
        setFavoriteComebackCount(comebackData.count || 0);
      }

      if (halftimeResponse.ok) {
        const halftimeData = await halftimeResponse.json();
        setHalftimeCount(halftimeData.count || 0);
      }

      if (momentumResponse.ok) {
        const momentumData = await momentumResponse.json();
        setMomentumCount(momentumData.count || 0);
      }

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
      <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black flex items-center justify-center">
        <div className="text-white text-xl">Loading alerts...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black flex items-center justify-center">
        <div className="text-red-400 text-xl">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black py-8 px-4">
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
                className={`px-4 py-2 rounded-lg border-4 font-bold tracking-wide transition-colors ${
                  autoRefresh
                    ? 'bg-gradient-to-br from-green-600 via-green-700 to-green-800 text-white border-green-500'
                    : 'bg-gradient-to-br from-slate-700 via-slate-800 to-slate-900 text-slate-300 border-slate-600 hover:border-blue-500'
                }`}
              >
                {autoRefresh ? 'AUTO-REFRESH ON' : 'AUTO-REFRESH OFF'}
              </button>
              <button
                onClick={fetchAlerts}
                className="px-4 py-2 bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 hover:from-blue-500 hover:via-blue-600 hover:to-blue-700 text-white border-4 border-blue-500 rounded-lg font-bold tracking-wide transition-all"
              >
                REFRESH NOW
              </button>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
            <div className="bg-gradient-to-br from-orange-900 via-orange-700 to-orange-900 border-4 border-orange-500 rounded-lg p-6 hover:shadow-lg hover:shadow-orange-600/30 transition-all">
              <div className="text-base text-white font-bold tracking-wide mb-1">🔥 NBA COMEBACKS</div>
              <div className="text-3xl font-bold text-white">{favoriteComebackCount}</div>
            </div>
            <div className="bg-gradient-to-br from-red-900 via-red-700 to-red-900 border-4 border-red-500 rounded-lg p-6 hover:shadow-lg hover:shadow-red-600/30 transition-all">
              <div className="text-base text-white font-bold tracking-wide mb-1">🚨 NHL GOALIE PULLS</div>
              <div className="text-3xl font-bold text-white">{goaliePullCount}</div>
            </div>
            <div className="bg-gradient-to-br from-purple-900 via-purple-700 to-purple-900 border-4 border-purple-500 rounded-lg p-6 hover:shadow-lg hover:shadow-purple-600/30 transition-all">
              <div className="text-base text-white font-bold tracking-wide mb-1">⏰ NBA HALFTIME 2H</div>
              <div className="text-3xl font-bold text-white">{halftimeCount}</div>
            </div>
            <div className="bg-gradient-to-br from-red-900 via-orange-700 to-red-900 border-4 border-orange-500 rounded-lg p-6 hover:shadow-lg hover:shadow-orange-600/30 transition-all">
              <div className="text-base text-white font-bold tracking-wide mb-1">🔥 MOMENTUM SURGES</div>
              <div className="text-3xl font-bold text-white">{momentumCount}</div>
            </div>
            <div className="bg-gradient-to-br from-green-900 via-green-700 to-green-900 border-4 border-green-600 rounded-lg p-6 hover:shadow-lg hover:shadow-green-600/30 transition-all">
              <div className="text-base text-white font-bold tracking-wide mb-1">ARBITRAGE OPPORTUNITIES</div>
              <div className="text-3xl font-bold text-white">{alertsData?.arbitrage.count || 0}</div>
            </div>
            <div className="bg-gradient-to-br from-blue-900 via-blue-700 to-blue-900 border-4 border-blue-500 rounded-lg p-6 hover:shadow-lg hover:shadow-blue-600/30 transition-all">
              <div className="text-base text-white font-bold tracking-wide mb-1">STEAM MOVES</div>
              <div className="text-3xl font-bold text-white">{alertsData?.steam_moves.count || 0}</div>
            </div>
            <div className="bg-gradient-to-br from-slate-900 via-slate-700 to-slate-900 border-4 border-slate-600 rounded-lg p-6 hover:shadow-lg hover:shadow-slate-600/30 transition-all">
              <div className="text-base text-white font-bold tracking-wide mb-1">LINE MOVEMENTS</div>
              <div className="text-3xl font-bold text-white">{alertsData?.line_movements.count || 0}</div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('comeback')}
            className={`px-6 py-3 rounded-lg border-4 font-bold tracking-wide transition-colors ${
              activeTab === 'comeback'
                ? 'bg-gradient-to-br from-orange-600 via-orange-700 to-orange-800 text-white border-orange-500 shadow-lg shadow-orange-600/30'
                : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800 hover:border-blue-600'
            }`}
          >
            🔥 NBA COMEBACKS ({favoriteComebackCount})
          </button>
          <button
            onClick={() => setActiveTab('goalie')}
            className={`px-6 py-3 rounded-lg border-4 font-bold tracking-wide transition-colors ${
              activeTab === 'goalie'
                ? 'bg-gradient-to-br from-red-600 via-red-700 to-red-800 text-white border-red-500 shadow-lg shadow-red-600/30'
                : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800 hover:border-blue-600'
            }`}
          >
            🚨 NHL GOALIE PULLS ({goaliePullCount})
          </button>
          <button
            onClick={() => setActiveTab('halftime')}
            className={`px-6 py-3 rounded-lg border-4 font-bold tracking-wide transition-colors ${
              activeTab === 'halftime'
                ? 'bg-gradient-to-br from-purple-600 via-purple-700 to-purple-800 text-white border-purple-500 shadow-lg shadow-purple-600/30'
                : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800 hover:border-blue-600'
            }`}
          >
            ⏰ NBA HALFTIME 2H ({halftimeCount})
          </button>
          <button
            onClick={() => setActiveTab('momentum')}
            className={`px-6 py-3 rounded-lg border-4 font-bold tracking-wide transition-colors ${
              activeTab === 'momentum'
                ? 'bg-gradient-to-br from-red-600 via-orange-700 to-red-800 text-white border-orange-500 shadow-lg shadow-orange-600/30'
                : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800 hover:border-blue-600'
            }`}
          >
            🔥 MOMENTUM SURGES ({momentumCount})
          </button>
          <button
            onClick={() => setActiveTab('arbitrage')}
            className={`px-6 py-3 rounded-lg border-4 font-bold tracking-wide transition-colors ${
              activeTab === 'arbitrage'
                ? 'bg-gradient-to-br from-green-600 via-green-700 to-green-800 text-white border-green-500'
                : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800 hover:border-blue-600'
            }`}
          >
            ARBITRAGE ({alertsData?.arbitrage.count || 0})
          </button>
          <button
            onClick={() => setActiveTab('steam')}
            className={`px-6 py-3 rounded-lg border-4 font-bold tracking-wide transition-colors ${
              activeTab === 'steam'
                ? 'bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 text-white border-blue-500'
                : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800 hover:border-blue-600'
            }`}
          >
            STEAM MOVES ({alertsData?.steam_moves.count || 0})
          </button>
          <button
            onClick={() => setActiveTab('lines')}
            className={`px-6 py-3 rounded-lg border-4 font-bold tracking-wide transition-colors ${
              activeTab === 'lines'
                ? 'bg-gradient-to-br from-slate-600 via-slate-700 to-slate-800 text-white border-slate-500'
                : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800 hover:border-blue-600'
            }`}
          >
            LINE MOVEMENTS ({alertsData?.line_movements.count || 0})
          </button>
        </div>

        {/* Arbitrage Alerts */}
        {activeTab === 'arbitrage' && (
          <div className="space-y-4">
            {alertsData?.arbitrage.alerts.length === 0 ? (
              <div className="bg-slate-800 border-4 border-slate-700 rounded-lg p-12 text-center">
                <div className="text-slate-400 text-lg">No arbitrage opportunities detected</div>
                <div className="text-slate-500 text-sm mt-2">Scanning every 10 seconds...</div>
              </div>
            ) : (
              alertsData?.arbitrage.alerts.map((alert, idx) => (
                <div key={idx} className="bg-gradient-to-br from-red-900 to-black border-4 border-red-600 rounded-lg p-6">
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
                    <div className="bg-slate-800 border-4 border-slate-700 rounded-lg p-4">
                      <div className="text-sm text-slate-400 mb-2">Book A: {alert.book_a}</div>
                      <div className="text-xl font-bold text-white mb-1">
                        {alert.odds_a > 0 ? `+${alert.odds_a}` : alert.odds_a}
                      </div>
                      <div className="text-sm text-slate-300">
                        Stake: ${alert.stake_a.toFixed(2)}
                      </div>
                    </div>
                    <div className="bg-slate-800 border-4 border-slate-700 rounded-lg p-4">
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
              <div className="bg-slate-800 border-4 border-slate-700 rounded-lg p-12 text-center">
                <div className="text-slate-400 text-lg">No steam moves detected</div>
                <div className="text-slate-500 text-sm mt-2">Scanning every 10 seconds...</div>
              </div>
            ) : (
              alertsData?.steam_moves.alerts.map((alert, idx) => (
                <div key={idx} className="bg-gradient-to-br from-blue-900 to-slate-800 border-4 border-blue-500 rounded-lg p-6">
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
                      <div className="text-2xl font-bold text-white">
                        {alert.consensus_percent.toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-800 border-4 border-slate-700 rounded-lg p-4 mb-4">
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
              <div className="bg-slate-800 border-4 border-slate-700 rounded-lg p-12 text-center">
                <div className="text-slate-400 text-lg">No significant line movements detected</div>
                <div className="text-slate-500 text-sm mt-2">Scanning every 10 seconds...</div>
              </div>
            ) : (
              alertsData?.line_movements.alerts.map((alert, idx) => (
                <div key={idx} className="bg-gradient-to-br from-green-900 to-black border-4 border-green-600 rounded-lg p-6">
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
                      <div className="text-2xl font-bold text-white">
                        {alert.movement_percent.toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-800 border-4 border-slate-700 rounded-lg p-4 mb-4">
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

        {/* NHL Goalie Pull Alerts */}
        {activeTab === 'goalie' && (
          <GoaliePullAlerts />
        )}

        {/* NBA Halftime Tracker Alerts */}
        {activeTab === 'halftime' && (
          <HalftimeTrackerAlerts />
        )}

        {/* NBA Favorite Comeback Alerts */}
        {activeTab === 'comeback' && (
          <FavoriteComebackAlerts />
        )}

        {/* Momentum Surge Alerts */}
        {activeTab === 'momentum' && (
          <MomentumAlerts />
        )}
      </div>
    </div>
  );
}
