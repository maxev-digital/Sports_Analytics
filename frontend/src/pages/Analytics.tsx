import { useEffect, useState } from 'react';
import { sportEmojis, uiEmojis } from '../utils/sportDetection';
import { useAuth } from '../contexts/AuthContext';
import { getUserBets, getUserBettingStats, getPendingBets, addStakeToBet, deleteBet } from '../utils/betTracking';
import { PersonalBetAnalytics } from '../components/PersonalBetAnalytics';
import { BetHistory } from '../components/BetHistory';
import { BankrollManager } from '../components/BankrollManager';
import { WelcomeModal } from '../components/WelcomeModal';
import { getApiUrl } from '../config';

interface StrategyData {
  total_alerts: number;
  successful_alerts: number;
  failed_alerts: number;
  pending_alerts: number;
  win_rate: number;
  avg_profit: number;
  total_profit: number;
}

interface PerformanceData {
  arbitrage: StrategyData;
  steam_moves: StrategyData;
  middles: StrategyData;
  [key: string]: StrategyData; // Allow dynamic strategy keys
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

  // Tab state: 'system', 'personal', 'history', or 'bankroll'
  const [activeTab, setActiveTab] = useState<'system' | 'personal' | 'history' | 'bankroll'>('system');

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

  // Demo data for screenshots (enable with ?demo=true in URL OR automatically in Electron)
  const isElectron = typeof window !== 'undefined' && (window as any).electron !== undefined;
  const urlDemoMode = new URLSearchParams(window.location.search).get('demo') === 'true';
  const isDemoMode = urlDemoMode || isElectron;

  // Fetch performance data
  useEffect(() => {
    const fetchData = async () => {
      // Use demo data if in demo mode
      if (isDemoMode) {
        setPerformanceData({
          arbitrage: {
            total_alerts: 87,
            successful_alerts: 48,
            failed_alerts: 34,
            pending_alerts: 5,
            win_rate: 55.2,
            avg_profit: 47.85,
            total_profit: 4163.45
          },
          steam_moves: {
            total_alerts: 143,
            successful_alerts: 91,
            failed_alerts: 42,
            pending_alerts: 10,
            win_rate: 63.6,
            avg_profit: 32.20,
            total_profit: 4604.60
          },
          middles: {
            total_alerts: 56,
            successful_alerts: 29,
            failed_alerts: 24,
            pending_alerts: 3,
            win_rate: 51.8,
            avg_profit: 61.75,
            total_profit: 3457.75
          },
          goalie_pull: {
            total_alerts: 68,
            successful_alerts: 30,
            failed_alerts: 35,
            pending_alerts: 3,
            win_rate: 46.0,
            avg_profit: 38.45,
            total_profit: 2614.60
          },
          favorite_comeback: {
            total_alerts: 92,
            successful_alerts: 62,
            failed_alerts: 27,
            pending_alerts: 3,
            win_rate: 67.4,
            avg_profit: 41.30,
            total_profit: 3799.60
          },
          halftime_tracker: {
            total_alerts: 124,
            successful_alerts: 63,
            failed_alerts: 54,
            pending_alerts: 7,
            win_rate: 50.8,
            avg_profit: 28.15,
            total_profit: 3490.60
          },
          momentum_shift: {
            total_alerts: 156,
            successful_alerts: 82,
            failed_alerts: 67,
            pending_alerts: 7,
            win_rate: 52.6,
            avg_profit: 24.85,
            total_profit: 3878.60
          },
          late_line_movement: {
            total_alerts: 78,
            successful_alerts: 52,
            failed_alerts: 23,
            pending_alerts: 3,
            win_rate: 66.7,
            avg_profit: 35.70,
            total_profit: 2784.60
          },
          public_fade: {
            total_alerts: 89,
            successful_alerts: 44,
            failed_alerts: 42,
            pending_alerts: 3,
            win_rate: 49.4,
            avg_profit: 31.90,
            total_profit: 2839.10
          },
          closing_line_value: {
            total_alerts: 134,
            successful_alerts: 88,
            failed_alerts: 42,
            pending_alerts: 4,
            win_rate: 65.7,
            avg_profit: 29.40,
            total_profit: 3941.60
          }
        });
        setRecentAlerts([
          {
            game_id: '1',
            sport: 'NBA',
            home_team: 'Lakers',
            away_team: 'Celtics',
            market_type: 'Moneyline',
            book_a: 'DraftKings',
            book_b: 'FanDuel',
            odds_a: -110,
            odds_b: 120,
            profit_percent: 4.2,
            stake_a: 545,
            stake_b: 455,
            total_stake: 1000,
            guaranteed_profit: 42.0,
            timestamp: new Date().toISOString(),
            expires_in: 180
          },
          {
            game_id: '2',
            sport: 'NFL',
            home_team: 'Chiefs',
            away_team: 'Bills',
            market_type: 'Spread',
            book_a: 'BetMGM',
            book_b: 'Caesars',
            odds_a: -105,
            odds_b: 115,
            profit_percent: 3.8,
            stake_a: 520,
            stake_b: 480,
            total_stake: 1000,
            guaranteed_profit: 38.0,
            timestamp: new Date().toISOString(),
            expires_in: 245
          }
        ]);
        setLoading(false);
        return;
      }

      try {
        const [perfResponse, alertsResponse] = await Promise.all([
          fetch(getApiUrl('/alerts/performance')),
          fetch(getApiUrl('/alerts/arbitrage'))
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
  }, [isDemoMode]);

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
      <div className="min-h-screen bg-black py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center text-white text-xl">Loading analytics...</div>
        </div>
      </div>
    );
  }

  // Calculate aggregate stats dynamically from all strategies
  const strategies = Object.entries(performanceData);

  const totalAlerts = strategies.reduce((sum, [_, data]) => sum + data.total_alerts, 0);
  const totalProfit = strategies.reduce((sum, [_, data]) => sum + data.total_profit, 0);
  const totalSuccess = strategies.reduce((sum, [_, data]) => sum + data.successful_alerts, 0);

  const overallWinRate = totalAlerts > 0 ? (totalSuccess / totalAlerts) * 100 : 0;
  const avgROI = totalAlerts > 0 ? (totalProfit / (totalAlerts * 100)) * 100 : 0; // Assuming $100 avg stake

  // Strategy display names
  const strategyNames: { [key: string]: string } = {
    arbitrage: 'Arbitrage',
    steam_moves: 'Steam Moves',
    middles: 'Line Movements',
    goalie_pull: 'Goalie Pull',
    favorite_comeback: 'Favorite Comeback',
    halftime_tracker: 'Halftime Tracker',
    momentum_shift: 'Momentum Shift',
    late_line_movement: 'Late Line Movement',
    public_fade: 'Public Fade',
    closing_line_value: 'Closing Line Value'
  };

  // Color schemes for strategies
  const strategyColors: { [key: string]: { bg: string; border: string; text: string; bar: string } } = {
    arbitrage: { bg: 'from-green-900 via-slate-700 to-slate-900', border: 'border-green-700', text: 'text-green-400', bar: 'from-green-600 to-green-400' },
    steam_moves: { bg: 'from-blue-900 via-slate-700 to-slate-900', border: 'border-blue-700', text: 'text-blue-400', bar: 'from-blue-600 to-blue-400' },
    middles: { bg: 'from-slate-900 via-slate-700 to-slate-900', border: 'border-slate-700', text: 'text-slate-300', bar: 'from-slate-600 to-slate-500' },
    goalie_pull: { bg: 'from-cyan-900 via-slate-700 to-slate-900', border: 'border-cyan-700', text: 'text-cyan-400', bar: 'from-cyan-600 to-cyan-400' },
    favorite_comeback: { bg: 'from-purple-900 via-slate-700 to-slate-900', border: 'border-purple-700', text: 'text-purple-400', bar: 'from-purple-600 to-purple-400' },
    halftime_tracker: { bg: 'from-amber-900 via-slate-700 to-slate-900', border: 'border-amber-700', text: 'text-amber-400', bar: 'from-amber-600 to-amber-400' },
    momentum_shift: { bg: 'from-rose-900 via-slate-700 to-slate-900', border: 'border-rose-700', text: 'text-rose-400', bar: 'from-rose-600 to-rose-400' },
    late_line_movement: { bg: 'from-emerald-900 via-slate-700 to-slate-900', border: 'border-emerald-700', text: 'text-emerald-400', bar: 'from-emerald-600 to-emerald-400' },
    public_fade: { bg: 'from-orange-900 via-slate-700 to-slate-900', border: 'border-orange-700', text: 'text-orange-400', bar: 'from-orange-600 to-orange-400' },
    closing_line_value: { bg: 'from-teal-900 via-slate-700 to-slate-900', border: 'border-teal-700', text: 'text-teal-400', bar: 'from-teal-600 to-teal-400' }
  };




  return (
    <div className="min-h-screen bg-black py-12 px-4">
      {username && <WelcomeModal username={username} />}
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold italic text-white mb-3" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>ANALYTICS DASHBOARD</h1>
          <p className="text-lg text-slate-400">
            Real-time performance metrics and insights from live alert monitoring
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={() => setActiveTab('system')}
            className={`flex items-center gap-2 px-6 py-3 font-semibold text-lg transition-all border-2 ${
              activeTab === 'system'
                ? 'bg-blue-600 text-white border-blue-400'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-slate-100 border-slate-600'
            }`}
          >
            <img src={uiEmojis.chart} alt="" className="w-6 h-6" style={{ imageRendering: 'crisp-edges' }} />
            System Alerts
          </button>
          <button
            onClick={() => setActiveTab('personal')}
            className={`flex items-center gap-2 px-6 py-3 font-semibold text-lg transition-all border-2 ${
              activeTab === 'personal'
                ? 'bg-blue-600 text-white border-blue-400'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-slate-100 border-slate-600'
            }`}
          >
            <img src={uiEmojis.dollar} alt="" className="w-6 h-6" style={{ imageRendering: 'crisp-edges' }} />
            My Bets
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2 px-6 py-3 font-semibold text-lg transition-all border-2 ${
              activeTab === 'history'
                ? 'bg-blue-600 text-white border-blue-400'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-slate-100 border-slate-600'
            }`}
          >
            <img src={uiEmojis.book} alt="" className="w-6 h-6" style={{ imageRendering: 'crisp-edges' }} />
            Bet History
          </button>
          <button
            onClick={() => setActiveTab('bankroll')}
            className={`flex items-center gap-2 px-6 py-3 font-semibold text-lg transition-all border-2 ${
              activeTab === 'bankroll'
                ? 'bg-blue-600 text-white border-blue-400'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-slate-100 border-slate-600'
            }`}
          >
            <span className="text-2xl">💰</span>
            My Bankroll
          </button>
        </div>

        {/* Conditional Rendering based on Active Tab */}
        {activeTab === 'system' ? (
          <>
            {/* SYSTEM ANALYTICS VIEW */}
            {/* MODULE 1: Overall Performance Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-slate-900 border-2 border-green-700 p-6 hover:border-green-500 transition-all">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm text-white font-bold tracking-wide">TOTAL PROFIT</div>
            </div>
            <div className="text-3xl font-bold text-green-400 mb-1">
              ${totalProfit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-green-300/60">{totalAlerts.toLocaleString()} total alerts tracked</div>
          </div>

          <div className="bg-slate-900 border-2 border-blue-500 p-6 hover:border-blue-400 transition-all">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm text-white font-bold tracking-wide">WIN RATE</div>
            </div>
            <div className="text-3xl font-bold text-blue-400 mb-1">
              {overallWinRate.toFixed(1)}%
            </div>
            <div className="text-xs text-blue-300/60">{totalSuccess} successful alerts</div>
          </div>

          <div className="bg-slate-900 border-2 border-slate-600 p-6 hover:border-slate-500 transition-all">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm text-white font-bold tracking-wide">AVERAGE ROI</div>
            </div>
            <div className="text-3xl font-bold text-white mb-1">
              +{avgROI.toFixed(1)}%
            </div>
            <div className="text-xs text-slate-400">Return on investment</div>
          </div>

          <div className="bg-slate-900 border-2 border-slate-600 p-6 hover:border-slate-500 transition-all">
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
          <div className="bg-slate-900 border-2 border-green-700 p-6">
            <h3 className="text-xl font-bold text-white mb-5 tracking-wide">
              PROFIT BY ALERT TYPE
            </h3>
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {strategies
                .sort(([_, a], [__, b]) => b.total_profit - a.total_profit)
                .map(([key, data]) => {
                  const colors = strategyColors[key] || strategyColors.middles;
                  return (
                    <div key={key} className={`bg-slate-800 p-4 border ${colors.border}`}>
                      <div className="flex justify-between items-center mb-2">
                        <span className={`${colors.text} font-semibold`}>{strategyNames[key] || key}</span>
                        <span className={`${colors.text} font-bold`}>${data.total_profit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      </div>
                      <div className="flex justify-between text-xs text-slate-400">
                        <span>{data.total_alerts.toLocaleString()} alerts</span>
                        <span>Avg: ${data.avg_profit.toFixed(2)}/alert</span>
                      </div>
                      <div className="mt-2 bg-slate-700 h-2">
                        <div
                          className={`${colors.text} h-2`}
                          style={{
                            width: `${(data.total_profit / totalProfit) * 100}%`,
                            backgroundColor: 'currentColor'
                          }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Module 3: Win Rate Breakdown */}
          <div className="bg-slate-900 border-2 border-blue-500 p-6">
            <h3 className="text-xl font-bold text-white mb-5 tracking-wide">
              WIN RATE ANALYSIS
            </h3>
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {strategies
                .sort(([_, a], [__, b]) => b.win_rate - a.win_rate)
                .map(([key, data]) => {
                  const colors = strategyColors[key] || strategyColors.middles;
                  return (
                    <div key={key} className={`bg-slate-800 p-4 border ${colors.border}`}>
                      <div className="flex justify-between items-center mb-3">
                        <div>
                          <div className="text-white font-semibold mb-1">{strategyNames[key] || key}</div>
                          <div className="text-xs text-slate-400">
                            {data.successful_alerts} wins / {data.failed_alerts} losses / {data.pending_alerts} pending
                          </div>
                        </div>
                        <div className={`text-3xl font-bold ${colors.text}`}>
                          {data.win_rate.toFixed(1)}%
                        </div>
                      </div>
                      <div className="bg-slate-700 h-3">
                        <div
                          className={`${colors.text} h-3 flex items-center justify-end pr-2`}
                          style={{
                            width: `${data.win_rate}%`,
                            backgroundColor: 'currentColor'
                          }}
                        >
                          <span className="text-[10px] text-white font-bold">{data.win_rate.toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        </div>

        {/* MODULE 4: Alert Distribution Chart */}
        <div className="bg-slate-900 border-2 border-purple-600 p-6 mb-8">
          <h3 className="text-xl font-bold text-white mb-5 tracking-wide">
            TOP 4 STRATEGIES BY VOLUME
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {strategies
              .sort(([_, a], [__, b]) => b.total_alerts - a.total_alerts)
              .slice(0, 4)
              .map(([key, data], index) => {
                const colors = strategyColors[key] || strategyColors.middles;
                const percentage = (data.total_alerts / totalAlerts) * 100;
                const circumference = 440;
                const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`;

                // Color mapping for circles
                const circleColors = ['#10b981', '#3b82f6', '#a855f7', '#f59e0b'];

                return (
                  <div key={key} className="text-center">
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
                          stroke={circleColors[index]}
                          strokeWidth="20"
                          fill="none"
                          strokeDasharray={strokeDasharray}
                        />
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <div className={`text-3xl font-bold ${colors.text}`}>
                          {percentage.toFixed(0)}%
                        </div>
                        <div className="text-xs text-slate-400">{strategyNames[key]?.split(' ')[0] || key}</div>
                      </div>
                    </div>
                    <div className="mt-3 text-sm text-slate-300">{data.total_alerts.toLocaleString()} alerts</div>
                  </div>
                );
              })}
          </div>
        </div>

        {/* MODULE 6: Recent High-Value Alerts */}
        <div className="bg-slate-900 border-2 border-red-700 p-6 mb-8">
          <h3 className="text-xl font-bold text-white mb-5 tracking-wide">
            TOP ACTIVE OPPORTUNITIES
          </h3>
          <div className="space-y-3">
            {recentAlerts.length > 0 ? (
              recentAlerts.map((alert, idx) => (
                <div key={idx} className="bg-slate-800 border-2 border-green-600 p-3">
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
                        ${alert.guaranteed_profit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 text-xs">
                    <span className="bg-slate-800/70 px-2 py-1 text-slate-300">
                      {alert.book_a}: {alert.odds_a > 0 ? '+' : ''}{alert.odds_a}
                    </span>
                    <span className="bg-slate-800/70 px-2 py-1 text-slate-300">
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
      ) : activeTab === 'personal' ? (
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
        ) : activeTab === 'history' ? (
          /* BET HISTORY VIEW */
          <BetHistory />
        ) : (
          /* BANKROLL MANAGER VIEW */
          <BankrollManager />
        )}
      </div>
    </div>
  );
}
