import { useEffect, useState } from 'react';
import { sportEmojis, uiEmojis } from '../utils/sportDetection';
import { useAuth } from '../contexts/AuthContext';
import { getUserBets, getUserBettingStats, getPendingBets, addStakeToBet, deleteBet } from '../utils/betTracking';
import { PersonalBetAnalytics } from '../components/PersonalBetAnalytics';

interface PerformanceData {
  arbitrage: {
    total_alerts: number;
    successful_alerts: number;
    failed_alerts: number;
    pending_alerts: number;
    win_rate: number;
    avg_profit: number;
    total_profit: number;
  };
  steam_moves: {
    total_alerts: number;
    successful_alerts: number;
    failed_alerts: number;
    pending_alerts: number;
    win_rate: number;
    avg_profit: number;
    total_profit: number;
  };
  line_movements: {
    total_alerts: number;
    successful_alerts: number;
    failed_alerts: number;
    pending_alerts: number;
    win_rate: number;
    avg_profit: number;
    total_profit: number;
  };
}

interface LiveArbitrage {
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

export function Analytics() {
  const { username } = useAuth();

  // Tab state: 'system' or 'personal'
  const [activeTab, setActiveTab] = useState<'system' | 'personal'>('system');

  // System Analytics State
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [recentAlerts, setRecentAlerts] = useState<LiveArbitrage[]>([]);
  const [loading, setLoading] = useState(true);

  // Personal Bet Analytics State
  const [personalStats, setPersonalStats] = useState<any>(null);
  const [pendingBets, setPendingBets] = useState<any[]>([]);
  const [activeBets, setActiveBets] = useState<any[]>([]);
  const [settledBets, setSettledBets] = useState<any[]>([]);
  const [personalLoading, setPersonalLoading] = useState(true);

  // Fetch performance data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [perfResponse, alertsResponse] = await Promise.all([
          fetch('/api/alerts/performance'),
          fetch('/api/alerts/arbitrage')
        ]);

        if (perfResponse.ok) {
          const perfData = await perfResponse.json();
          setPerformanceData(perfData);
        }

        if (alertsResponse.ok) {
          const alertsData = await alertsResponse.json();
          setRecentAlerts(alertsData.alerts.slice(0, 5));
        }

        setLoading(false);
      } catch (error) {
        console.error('Error fetching analytics data:', error);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  // Fetch personal bet data
  useEffect(() => {
    if (!username) return;

    const fetchPersonalData = async () => {
      try {
        const [stats, pending, active, settled] = await Promise.all([
          getUserBettingStats(username),
          getPendingBets(username),
          getUserBets(username, 'active'),
          getUserBets(username, undefined) // Get all to filter settled
        ]);

        setPersonalStats(stats);
        setPendingBets(pending);
        setActiveBets(active);
        // Filter settled bets (won, lost, push)
        setSettledBets(settled.filter((b: any) => ['won', 'lost', 'push'].includes(b.status)));
        setPersonalLoading(false);
      } catch (error) {
        console.error('Error fetching personal bet data:', error);
        setPersonalLoading(false);
      }
    };

    fetchPersonalData();
    const interval = setInterval(fetchPersonalData, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [username]);

  if (loading || !performanceData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center text-white text-xl">Loading analytics...</div>
        </div>
      </div>
    );
  }

  // Calculate aggregate stats
  const totalAlerts = performanceData.arbitrage.total_alerts +
                      performanceData.steam_moves.total_alerts +
                      performanceData.line_movements.total_alerts;

  const totalProfit = performanceData.arbitrage.total_profit +
                      performanceData.steam_moves.total_profit +
                      performanceData.line_movements.total_profit;

  const totalSuccess = performanceData.arbitrage.successful_alerts +
                       performanceData.steam_moves.successful_alerts +
                       performanceData.line_movements.successful_alerts;

  const overallWinRate = totalAlerts > 0 ? (totalSuccess / totalAlerts) * 100 : 0;

  const avgROI = totalAlerts > 0 ? (totalProfit / (totalAlerts * 100)) * 100 : 0; // Assuming $100 avg stake




  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-3">Analytics Dashboard</h1>
          <p className="text-lg text-slate-400">
            Real-time performance metrics and insights from live alert monitoring
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={() => setActiveTab('system')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold text-lg transition-all ${
              activeTab === 'system'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-slate-100'
            }`}
          >
            <img src={uiEmojis.chart} alt="" className="w-6 h-6" style={{ imageRendering: 'crisp-edges' }} />
            System Alerts
          </button>
          <button
            onClick={() => setActiveTab('personal')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold text-lg transition-all ${
              activeTab === 'personal'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-slate-100'
            }`}
          >
            <img src={uiEmojis.dollar} alt="" className="w-6 h-6" style={{ imageRendering: 'crisp-edges' }} />
            My Bets
          </button>
        </div>

        {/* Conditional Rendering based on Active Tab */}
        {activeTab === 'system' ? (
          <>
            {/* SYSTEM ANALYTICS VIEW */}
            {/* MODULE 1: Overall Performance Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-br from-green-900 via-slate-900 to-black border-4 border-green-700 rounded-lg p-6 hover:shadow-lg hover:shadow-green-600/20 hover:border-green-600 transition-all">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm text-white font-bold tracking-wide">TOTAL PROFIT</div>
            </div>
            <div className="text-3xl font-bold text-green-400 mb-1">
              ${totalProfit.toFixed(2)}
            </div>
            <div className="text-xs text-green-300/60">{totalAlerts} total alerts tracked</div>
          </div>

          <div className="bg-gradient-to-br from-blue-900 to-slate-900 border-4 border-blue-500 rounded-lg p-6 hover:shadow-lg hover:shadow-blue-600/20 hover:border-blue-600 transition-all">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm text-white font-bold tracking-wide">WIN RATE</div>
            </div>
            <div className="text-3xl font-bold text-blue-400 mb-1">
              {overallWinRate.toFixed(1)}%
            </div>
            <div className="text-xs text-blue-300/60">{totalSuccess} successful alerts</div>
          </div>

          <div className="bg-gradient-to-br from-slate-900 via-slate-700 to-slate-900 border-4 border-slate-700 rounded-lg p-6 hover:shadow-lg hover:shadow-blue-600/20 hover:border-blue-600 transition-all">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm text-white font-bold tracking-wide">AVERAGE ROI</div>
            </div>
            <div className="text-3xl font-bold text-white mb-1">
              +{avgROI.toFixed(1)}%
            </div>
            <div className="text-xs text-slate-400">Return on investment</div>
          </div>

          <div className="bg-gradient-to-br from-slate-900 via-slate-700 to-slate-900 border-4 border-slate-700 rounded-lg p-6 hover:shadow-lg hover:shadow-blue-600/20 hover:border-blue-600 transition-all">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm text-white font-bold tracking-wide">ACTIVE ALERTS</div>
            </div>
            <div className="text-3xl font-bold text-white mb-1">
              {recentAlerts.length}
            </div>
            <div className="text-xs text-slate-400">Currently available</div>
          </div>
        </div>

        {/* MODULE 2: ROI and Profit Tracking + MODULE 3: Win Rate by Alert Type */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Module 2: ROI Breakdown */}
          <div className="bg-gradient-to-br from-green-900 via-slate-900 to-black border-4 border-green-700 rounded-lg p-6">
            <h3 className="text-xl font-bold text-white mb-5 tracking-wide">
              PROFIT BY ALERT TYPE
            </h3>
            <div className="space-y-4">
              <div className="bg-gradient-to-br from-slate-900 via-slate-700 to-slate-900 rounded-lg p-4 border-4 border-green-700">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-green-400 font-semibold">Arbitrage</span>
                  <span className="text-green-400 font-bold">${performanceData.arbitrage.total_profit.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-xs text-slate-400">
                  <span>{performanceData.arbitrage.total_alerts} alerts</span>
                  <span>Avg: ${performanceData.arbitrage.avg_profit.toFixed(2)}/alert</span>
                </div>
                <div className="mt-2 bg-slate-800 rounded-full h-2">
                  <div
                    className="bg-gradient-to-br from-green-500 via-green-700 to-green-900 h-2 rounded-full"
                    style={{ width: `${(performanceData.arbitrage.total_profit / totalProfit) * 100}%` }}
                  ></div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-slate-900 via-slate-700 to-slate-900 rounded-lg p-4 border-4 border-blue-700">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-blue-400 font-semibold">Steam Moves</span>
                  <span className="text-blue-400 font-bold">${performanceData.steam_moves.total_profit.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-xs text-slate-400">
                  <span>{performanceData.steam_moves.total_alerts} alerts</span>
                  <span>Avg: ${performanceData.steam_moves.avg_profit.toFixed(2)}/alert</span>
                </div>
                <div className="mt-2 bg-slate-800 rounded-full h-2">
                  <div
                    className="bg-gradient-to-br from-blue-500 via-blue-700 to-blue-900 h-2 rounded-full"
                    style={{ width: `${(performanceData.steam_moves.total_profit / totalProfit) * 100}%` }}
                  ></div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-slate-900 via-slate-700 to-slate-900 rounded-lg p-4 border-4 border-slate-700">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-slate-300 font-semibold">Line Movements</span>
                  <span className="text-white font-bold">${performanceData.line_movements.total_profit.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-xs text-slate-400">
                  <span>{performanceData.line_movements.total_alerts} alerts</span>
                  <span>Avg: ${performanceData.line_movements.avg_profit.toFixed(2)}/alert</span>
                </div>
                <div className="mt-2 bg-slate-800 rounded-lg h-2">
                  <div
                    className="bg-gradient-to-br from-slate-500 via-slate-700 to-slate-900 h-2 rounded"
                    style={{ width: `${(performanceData.line_movements.total_profit / totalProfit) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* Module 3: Win Rate Breakdown */}
          <div className="bg-gradient-to-br from-blue-900 to-slate-900 border-4 border-blue-500 rounded-lg p-6">
            <h3 className="text-xl font-bold text-white mb-5 tracking-wide">
              WIN RATE ANALYSIS
            </h3>
            <div className="space-y-4">
              <div className="bg-gradient-to-br from-slate-900 via-slate-700 to-slate-900 rounded-lg p-4">
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <div className="text-white font-semibold mb-1">Arbitrage Alerts</div>
                    <div className="text-xs text-slate-400">
                      {performanceData.arbitrage.successful_alerts} wins / {performanceData.arbitrage.failed_alerts} losses / {performanceData.arbitrage.pending_alerts} pending
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-green-400">
                    {performanceData.arbitrage.win_rate.toFixed(1)}%
                  </div>
                </div>
                <div className="bg-gradient-to-br from-slate-800 via-slate-700 to-slate-900 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-green-600 to-green-400 h-3 rounded-full flex items-center justify-end pr-2"
                    style={{ width: `${performanceData.arbitrage.win_rate}%` }}
                  >
                    <span className="text-[10px] text-white font-bold">{performanceData.arbitrage.win_rate.toFixed(0)}%</span>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-slate-900 via-slate-700 to-slate-900 rounded-lg p-4">
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <div className="text-white font-semibold mb-1">Steam Moves</div>
                    <div className="text-xs text-slate-400">
                      {performanceData.steam_moves.successful_alerts} wins / {performanceData.steam_moves.failed_alerts} losses / {performanceData.steam_moves.pending_alerts} pending
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-blue-400">
                    {performanceData.steam_moves.win_rate.toFixed(1)}%
                  </div>
                </div>
                <div className="bg-gradient-to-br from-slate-800 via-slate-700 to-slate-900 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-blue-600 to-blue-400 h-3 rounded-full flex items-center justify-end pr-2"
                    style={{ width: `${performanceData.steam_moves.win_rate}%` }}
                  >
                    <span className="text-[10px] text-white font-bold">{performanceData.steam_moves.win_rate.toFixed(0)}%</span>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-slate-900 via-slate-700 to-slate-900 rounded-lg p-4">
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <div className="text-white font-semibold mb-1">Line Movements</div>
                    <div className="text-xs text-slate-400">
                      {performanceData.line_movements.successful_alerts} wins / {performanceData.line_movements.failed_alerts} losses / {performanceData.line_movements.pending_alerts} pending
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-white">
                    {performanceData.line_movements.win_rate.toFixed(1)}%
                  </div>
                </div>
                <div className="bg-gradient-to-br from-slate-800 via-slate-700 to-slate-900 rounded-lg h-3">
                  <div
                    className="bg-gradient-to-r from-slate-600 to-slate-500 h-3 rounded-lg flex items-center justify-end pr-2"
                    style={{ width: `${performanceData.line_movements.win_rate}%` }}
                  >
                    <span className="text-[10px] text-white font-bold">{performanceData.line_movements.win_rate.toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* MODULE 4: Alert Distribution Chart */}
        <div className="bg-gradient-to-br from-red-900 via-slate-900 to-black border-4 border-red-700 rounded-lg p-6 mb-8">
          <h3 className="text-xl font-bold text-white mb-5 tracking-wide">
            ALERT VOLUME DISTRIBUTION
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="relative inline-block">
                <svg className="w-40 h-40 transform -rotate-90">
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="#1e293b"
                    strokeWidth="20"
                    fill="none"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="#10b981"
                    strokeWidth="20"
                    fill="none"
                    strokeDasharray={`${(performanceData.arbitrage.total_alerts / totalAlerts) * 440} 440`}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-3xl font-bold text-green-400">
                    {((performanceData.arbitrage.total_alerts / totalAlerts) * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-slate-400">Arbitrage</div>
                </div>
              </div>
              <div className="mt-3 text-sm text-slate-300">{performanceData.arbitrage.total_alerts} alerts</div>
            </div>

            <div className="text-center">
              <div className="relative inline-block">
                <svg className="w-40 h-40 transform -rotate-90">
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="#1e293b"
                    strokeWidth="20"
                    fill="none"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="#3b82f6"
                    strokeWidth="20"
                    fill="none"
                    strokeDasharray={`${(performanceData.steam_moves.total_alerts / totalAlerts) * 440} 440`}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-3xl font-bold text-blue-400">
                    {((performanceData.steam_moves.total_alerts / totalAlerts) * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-slate-400">Steam</div>
                </div>
              </div>
              <div className="mt-3 text-sm text-slate-300">{performanceData.steam_moves.total_alerts} alerts</div>
            </div>

            <div className="text-center">
              <div className="relative inline-block">
                <svg className="w-40 h-40 transform -rotate-90">
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="#1e293b"
                    strokeWidth="20"
                    fill="none"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="#a855f7"
                    strokeWidth="20"
                    fill="none"
                    strokeDasharray={`${(performanceData.line_movements.total_alerts / totalAlerts) * 440} 440`}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-3xl font-bold text-purple-400">
                    {((performanceData.line_movements.total_alerts / totalAlerts) * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-slate-400">Lines</div>
                </div>
              </div>
              <div className="mt-3 text-sm text-slate-300">{performanceData.line_movements.total_alerts} alerts</div>
            </div>
          </div>
        </div>

        {/* MODULE 6: Recent High-Value Alerts */}
        <div className="bg-gradient-to-br from-red-900 via-slate-900 to-black border-4 border-red-700 rounded-lg p-6 mb-8">
          <h3 className="text-xl font-bold text-white mb-5 tracking-wide">
            TOP ACTIVE OPPORTUNITIES
          </h3>
          <div className="space-y-3">
            {recentAlerts.length > 0 ? (
              recentAlerts.map((alert, idx) => (
                <div key={idx} className="bg-gradient-to-br from-green-900 via-green-700 to-green-900 border-4 border-green-700 rounded-lg p-3">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="text-sm font-semibold text-white mb-1">
                        {alert.away_team} @ {alert.home_team}
                      </div>
                      <div className="text-xs text-slate-400">
                        {alert.sport.toUpperCase()} • {alert.market_type}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-green-400 font-bold text-lg">
                        +{alert.profit_percent.toFixed(2)}%
                      </div>
                      <div className="text-xs text-slate-400">
                        ${alert.guaranteed_profit.toFixed(2)}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 text-xs">
                    <span className="bg-slate-800/70 px-2 py-1 rounded-lg text-slate-300">
                      {alert.book_a}: {alert.odds_a > 0 ? '+' : ''}{alert.odds_a}
                    </span>
                    <span className="bg-slate-800/70 px-2 py-1 rounded-lg text-slate-300">
                      {alert.book_b}: {alert.odds_b > 0 ? '+' : ''}{alert.odds_b}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-slate-400 py-8">
                No active arbitrage opportunities at the moment
              </div>
            )}
          </div>
        </div>



        </>
      ) : (
          /* PERSONAL BET ANALYTICS VIEW */
          <PersonalBetAnalytics
            stats={personalStats}
            pendingBets={pendingBets}
            activeBets={activeBets}
            settledBets={settledBets}
            onRefresh={() => {
              // Re-fetch personal data when user adds stake or deletes bet
              if (username) {
                Promise.all([
                  getUserBettingStats(username),
                  getPendingBets(username),
                  getUserBets(username, 'active'),
                  getUserBets(username, undefined)
                ]).then(([stats, pending, active, settled]) => {
                  setPersonalStats(stats);
                  setPendingBets(pending);
                  setActiveBets(active);
                  setSettledBets(settled.filter((b: any) => ['won', 'lost', 'push'].includes(b.status)));
                });
              }
            }}
          />
        )}
      </div>
    </div>
  );
}
