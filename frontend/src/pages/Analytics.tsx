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
            My Performance
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
            {/* MY PERFORMANCE DASHBOARD - Mirrors Model Performance Layout */}
            <div className="bg-gradient-to-br from-black via-gray-900 to-slate-900 border-2 border-white rounded-xl p-8 mb-8">
              {/* Header */}
              <div className="mb-8">
                <h2 className="text-4xl font-bold italic text-white mb-2" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>
                  MY BETTING PERFORMANCE
                </h2>
                <p className="text-slate-400 text-lg">
                  Track your personal bet history and ROI across all strategies
                </p>
              </div>

              {/* Filter Controls */}
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 mb-6">
                <div className="flex gap-4 items-center flex-wrap">
                  <div>
                    <label className="text-slate-400 text-sm block mb-1">Time Range:</label>
                    <select className="px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white">
                      <option value="1">Last 24h</option>
                      <option value="7">Last 7 Days</option>
                      <option value="30">Last 30 Days</option>
                      <option value="365">All Time</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-400 text-sm block mb-1">Alert Type:</label>
                    <select className="px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white">
                      <option value="all">All Types</option>
                      <option value="arbitrage">Arbitrage</option>
                      <option value="steam_moves">Steam Moves</option>
                      <option value="middles">Middles</option>
                      <option value="goalie_pull">Goalie Pull</option>
                      <option value="favorite_comeback">Favorite Comeback</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-400 text-sm block mb-1">Sport:</label>
                    <select className="px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white">
                      <option value="all">All Sports</option>
                      <option value="nba">NBA</option>
                      <option value="nhl">NHL</option>
                      <option value="nfl">NFL</option>
                      <option value="ncaab">NCAAB</option>
                      <option value="ncaaf">NCAAF</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Summary Cards - 4 metrics with colored glows */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                {/* Total Profit - Green */}
                <div className="bg-gradient-to-br from-green-600/20 to-green-900/40 rounded-xl p-6 shadow-lg shadow-green-500/50">
                  <div className="text-slate-400 text-sm mb-1 font-semibold">TOTAL PROFIT</div>
                  <div className="text-4xl font-bold text-green-400 mb-1">
                    ${totalProfit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  <div className="text-slate-500 text-xs mt-2">{totalAlerts.toLocaleString()} bets placed</div>
                </div>

                {/* Win Rate - Blue */}
                <div className="bg-gradient-to-br from-blue-600/20 to-blue-900/40 rounded-xl p-6 shadow-lg shadow-blue-500/50">
                  <div className="text-slate-400 text-sm mb-1 font-semibold">WIN RATE</div>
                  <div className="text-4xl font-bold text-blue-400 mb-1">
                    {overallWinRate.toFixed(1)}%
                  </div>
                  <div className="text-slate-500 text-xs mt-2">{totalSuccess} wins - {totalAlerts - totalSuccess} losses</div>
                </div>

                {/* Average ROI - Red/Orange */}
                <div className="bg-gradient-to-br from-red-600/20 to-orange-900/40 rounded-xl p-6 shadow-lg shadow-red-500/50">
                  <div className="text-slate-400 text-sm mb-1 font-semibold">AVERAGE ROI</div>
                  <div className="text-4xl font-bold text-orange-400 mb-1">
                    +{avgROI.toFixed(1)}%
                  </div>
                  <div className="text-slate-500 text-xs mt-2">Return on investment</div>
                </div>

                {/* Total Alerts - Purple */}
                <div className="bg-gradient-to-br from-purple-600/20 to-purple-900/40 rounded-xl p-6 shadow-lg shadow-purple-500/50">
                  <div className="text-slate-400 text-sm mb-1 font-semibold">TOTAL ALERTS</div>
                  <div className="text-4xl font-bold text-purple-400 mb-1">
                    {totalAlerts}
                  </div>
                  <div className="text-slate-500 text-xs mt-2">Tracked opportunities</div>
                </div>
              </div>

              {/* Performance Charts - Using existing strategy data as demo */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {/* Cumulative Profit Line Chart */}
                <div className="bg-gradient-to-br from-black via-gray-900 to-slate-900 border-2 border-white rounded-xl p-6">
                  <h3 className="text-xl font-bold text-white mb-4">CUMULATIVE PROFIT</h3>
                  <div className="h-64 flex items-center justify-center">
                    <div className="text-slate-400 text-sm">
                      Chart: Cumulative profit over time
                      <br />
                      <span className="text-xs">(Will integrate with recharts)</span>
                    </div>
                  </div>
                </div>

                {/* Win Rate by Alert Type Bar Chart */}
                <div className="bg-gradient-to-br from-black via-gray-900 to-slate-900 border-2 border-white rounded-xl p-6">
                  <h3 className="text-xl font-bold text-white mb-4">WIN RATE BY ALERT TYPE</h3>
                  <div className="h-64 flex items-center justify-center">
                    <div className="text-slate-400 text-sm">
                      Chart: Win rate breakdown by strategy
                      <br />
                      <span className="text-xs">(Will integrate with recharts)</span>
                    </div>
                  </div>
                </div>

                {/* ROI by Sport */}
                <div className="bg-gradient-to-br from-black via-gray-900 to-slate-900 border-2 border-white rounded-xl p-6">
                  <h3 className="text-xl font-bold text-white mb-4">ROI BY SPORT</h3>
                  <div className="h-64 flex items-center justify-center">
                    <div className="text-slate-400 text-sm">
                      Chart: ROI breakdown by sport
                      <br />
                      <span className="text-xs">(Will integrate with recharts)</span>
                    </div>
                  </div>
                </div>

                {/* Units Won Over Time */}
                <div className="bg-gradient-to-br from-black via-gray-900 to-slate-900 border-2 border-white rounded-xl p-6">
                  <h3 className="text-xl font-bold text-white mb-4">UNITS WON</h3>
                  <div className="h-64 flex items-center justify-center">
                    <div className="text-slate-400 text-sm">
                      Chart: Units won over time
                      <br />
                      <span className="text-xs">(Will integrate with recharts)</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Best Performing Strategies Table */}
              <div className="bg-gradient-to-br from-black via-gray-900 to-slate-900 border-2 border-white rounded-xl p-6 mb-8">
                <h3 className="text-2xl font-bold text-white mb-5">BEST PERFORMING STRATEGIES</h3>
                <div className="space-y-3">
                  {strategies
                    .sort(([_, a], [__, b]) => b.win_rate - a.win_rate)
                    .slice(0, 5)
                    .map(([key, data]) => {
                      const colors = strategyColors[key] || strategyColors.middles;
                      return (
                        <div key={key} className="bg-slate-800/80 border border-slate-600 rounded-lg p-4 flex items-center justify-between">
                          <div className="flex-1">
                            <div className="text-white font-semibold text-lg mb-1">
                              {strategyNames[key] || key}
                            </div>
                            <div className="text-xs text-slate-400">
                              {data.successful_alerts}W - {data.failed_alerts}L - {data.pending_alerts}P
                            </div>
                          </div>
                          <div className="flex gap-8 items-center">
                            <div className="text-center">
                              <div className="text-2xl font-bold text-green-400">
                                ${data.total_profit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                              </div>
                              <div className="text-xs text-slate-400">Profit</div>
                            </div>
                            <div className="text-center">
                              <div className="text-2xl font-bold text-blue-400">
                                {data.win_rate.toFixed(1)}%
                              </div>
                              <div className="text-xs text-slate-400">Win Rate</div>
                            </div>
                            <div className="text-center">
                              <div className="text-2xl font-bold text-purple-400">
                                {data.total_alerts}
                              </div>
                              <div className="text-xs text-slate-400">Bets</div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>

              {/* Recent Bet History */}
              <div className="bg-gradient-to-br from-black via-gray-900 to-slate-900 border-2 border-white rounded-xl p-6">
                <h3 className="text-2xl font-bold text-white mb-5">RECENT BET HISTORY</h3>
                <div className="space-y-2">
                  {recentAlerts.slice(0, 10).map((alert, idx) => (
                    <div key={idx} className="bg-slate-800/80 border border-slate-600 rounded-lg p-3 flex items-center justify-between">
                      <div className="flex-1">
                        <div className="text-white font-semibold text-sm mb-1">
                          {alert.away_team} @ {alert.home_team}
                        </div>
                        <div className="text-xs text-slate-400">
                          {alert.sport.toUpperCase()} • {alert.market_type} • {alert.book_a}
                        </div>
                      </div>
                      <div className="flex gap-4 items-center">
                        <div className="text-sm">
                          <span className="text-slate-400">Odds:</span>{' '}
                          <span className="text-white font-semibold">
                            {alert.odds_a > 0 ? '+' : ''}{alert.odds_a}
                          </span>
                        </div>
                        <div className="text-sm">
                          <span className="text-slate-400">Profit:</span>{' '}
                          <span className="text-green-400 font-bold">
                            +${alert.guaranteed_profit.toFixed(2)}
                          </span>
                        </div>
                        <div className="px-3 py-1 bg-green-600/20 border border-green-600 rounded text-green-400 text-xs font-semibold">
                          WON
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
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
