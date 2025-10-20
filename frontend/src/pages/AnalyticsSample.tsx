import { useEffect, useState } from 'react';

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

export function AnalyticsSample() {
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [recentAlerts, setRecentAlerts] = useState<LiveArbitrage[]>([]);
  const [loading, setLoading] = useState(true);

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

  if (loading || !performanceData) {
    return (
      <div className="min-h-screen bg-black py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center text-[#C5A028] text-xl">Loading analytics...</div>
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

  // Sport breakdown (simulated based on alert types)
  const sportStats = [
    {
      sport: 'NBA',
      alerts: Math.floor(totalAlerts * 0.25),
      profit: totalProfit * 0.28,
      winRate: 86.2,
      logo: 'https://cdn.ssref.net/req/202410311/tlogo/bbr/NBA.png',
      hasLogo: true
    },
    {
      sport: 'NFL',
      alerts: Math.floor(totalAlerts * 0.22),
      profit: totalProfit * 0.26,
      winRate: 84.8,
      logo: 'https://cdn.ssref.net/req/202410311/tlogo/pfr/NFL.png',
      hasLogo: true
    },
    {
      sport: 'NHL',
      alerts: Math.floor(totalAlerts * 0.18),
      profit: totalProfit * 0.18,
      winRate: 82.1,
      logo: 'https://cdn.ssref.net/req/202410311/tlogo/hr/NHL.png',
      hasLogo: true
    },
    {
      sport: 'MLB',
      alerts: Math.floor(totalAlerts * 0.15),
      profit: totalProfit * 0.12,
      winRate: 79.5,
      logo: 'https://cdn.ssref.net/req/202410311/tlogo/br/MLB.png',
      hasLogo: true
    },
    {
      sport: 'NCAAF',
      alerts: Math.floor(totalAlerts * 0.12),
      profit: totalProfit * 0.10,
      winRate: 78.3,
      emoji: '🏈',
      hasLogo: false
    },
    {
      sport: 'NCAAB',
      alerts: Math.floor(totalAlerts * 0.08),
      profit: totalProfit * 0.06,
      winRate: 76.8,
      emoji: '🏀',
      hasLogo: false
    }
  ];

  // Bookmaker analysis (simulated top performers)
  const bookmakerStats = [
    { book: 'DraftKings', opportunities: 342, avgProfit: 2.8, winRate: 88.2 },
    { book: 'FanDuel', opportunities: 318, avgProfit: 2.5, winRate: 85.9 },
    { book: 'BetMGM', opportunities: 276, avgProfit: 2.3, winRate: 84.1 },
    { book: 'Caesars', opportunities: 251, avgProfit: 2.1, winRate: 82.7 }
  ];

  // Time-based patterns (simulated hourly performance)
  const hourlyPerformance = [
    { time: '9AM-12PM', alerts: 187, profit: 428.50, winRate: 83.4 },
    { time: '12PM-3PM', alerts: 245, profit: 612.30, winRate: 86.1 },
    { time: '3PM-6PM', alerts: 312, profit: 758.90, winRate: 87.8 },
    { time: '6PM-9PM', alerts: 401, profit: 942.20, winRate: 88.5 },
    { time: '9PM-12AM', alerts: 289, profit: 651.40, winRate: 85.2 }
  ];

  return (
    <div className="min-h-screen py-12 px-4 relative overflow-hidden" style={{
      background: 'linear-gradient(to bottom, #000000 0%, #1a1a1a 50%, #262626 100%)',
      fontFamily: 'Inter, sans-serif'
    }}>
      {/* Paisley-inspired Decorative Pattern */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        {/* Ornate teardrops and curved motifs */}
        <div className="absolute inset-0" style={{
          backgroundImage: `
            radial-gradient(ellipse 30px 50px at 50% 50%, rgba(212, 175, 55, 0.15) 0%, transparent 50%),
            radial-gradient(ellipse 20px 35px at 70% 30%, rgba(212, 175, 55, 0.1) 0%, transparent 50%),
            radial-gradient(circle 8px at 50% 70%, rgba(197, 160, 40, 0.2) 0%, transparent 100%)
          `,
          backgroundSize: '120px 120px',
          backgroundPosition: '0 0, 60px 60px, 40px 80px'
        }}></div>

        {/* Curved swirl accents */}
        <div className="absolute inset-0" style={{
          backgroundImage: `
            radial-gradient(ellipse 40px 15px at 30% 40%, rgba(184, 134, 11, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse 15px 40px at 70% 60%, rgba(184, 134, 11, 0.08) 0%, transparent 50%)
          `,
          backgroundSize: '150px 150px',
          backgroundPosition: '20px 20px, 80px 90px'
        }}></div>

        {/* Fine detail dots - like paisley fill pattern */}
        <div className="absolute inset-0" style={{
          backgroundImage: `
            radial-gradient(circle 2px at center, rgba(212, 175, 55, 0.12) 0%, transparent 100%)
          `,
          backgroundSize: '30px 30px',
          backgroundPosition: '15px 15px'
        }}></div>

        {/* Subtle connecting curves */}
        <div className="absolute inset-0 opacity-40" style={{
          backgroundImage: `
            repeating-linear-gradient(45deg, transparent, transparent 58px, rgba(212, 175, 55, 0.03) 58px, rgba(212, 175, 55, 0.03) 60px),
            repeating-linear-gradient(-45deg, transparent, transparent 58px, rgba(184, 134, 11, 0.03) 58px, rgba(184, 134, 11, 0.03) 60px)
          `
        }}></div>
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <div className="mb-8 border-b border-neutral-800 pb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-5xl font-bold mb-2" style={{
                fontFamily: "'Libre Caslon Display', serif",
                background: 'linear-gradient(135deg, #D4AF37 0%, #C5A028 50%, #B8941E 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                letterSpacing: '0.08em',
                textTransform: 'uppercase'
              }}>ANALYTICS DASHBOARD</h1>
              <p className="text-lg text-neutral-400" style={{ fontFamily: 'Inter, sans-serif' }}>
                Real-time performance metrics and insights from live alert monitoring
              </p>
            </div>
            <div className="px-4 py-2 bg-neutral-900 rounded-lg" style={{ borderColor: '#B8860B', borderWidth: '1px', borderStyle: 'solid' }}>
              <span className="text-xs text-neutral-400 uppercase tracking-wider" style={{ fontFamily: 'Inter, sans-serif', fontWeight: 600 }}>Sample Theme</span>
            </div>
          </div>
        </div>

        {/* MODULE 1: Overall Performance Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-neutral-950 rounded-lg p-6 hover:shadow-lg transition-all" style={{
            borderColor: '#B8860B',
            borderWidth: '1px',
            borderStyle: 'solid',
            boxShadow: '0 0 20px rgba(184, 134, 11, 0.1)'
          }}>
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-bold tracking-wide" style={{ color: '#D4AF37', fontFamily: 'Inter, sans-serif', fontWeight: 700 }}>TOTAL PROFIT</div>
            </div>
            <div className="text-3xl font-bold mb-1" style={{
              color: '#D4AF37',
              fontFamily: "'Libre Caslon Text', serif"
            }}>
              ${totalProfit.toFixed(2)}
            </div>
            <div className="text-xs text-neutral-500" style={{ fontFamily: 'Inter, sans-serif' }}>{totalAlerts} total alerts tracked</div>
          </div>

          <div className="bg-neutral-900 border border-neutral-700 rounded-lg p-6 hover:shadow-lg hover:shadow-neutral-600/20 hover:border-neutral-500 transition-all">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm text-neutral-300 font-bold tracking-wide" style={{ fontFamily: 'Inter, sans-serif', fontWeight: 700 }}>WIN RATE</div>
            </div>
            <div className="text-3xl font-bold text-white mb-1" style={{ fontFamily: "'Libre Caslon Text', serif" }}>
              {overallWinRate.toFixed(1)}%
            </div>
            <div className="text-xs text-neutral-500" style={{ fontFamily: 'Inter, sans-serif' }}>{totalSuccess} successful alerts</div>
          </div>

          <div className="bg-neutral-900 border border-neutral-700 rounded-lg p-6 hover:shadow-lg hover:shadow-neutral-600/20 hover:border-neutral-500 transition-all">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm text-neutral-300 font-bold tracking-wide" style={{ fontFamily: 'Inter, sans-serif', fontWeight: 700 }}>AVERAGE ROI</div>
            </div>
            <div className="text-3xl font-bold mb-1" style={{
              color: '#C5A028',
              fontFamily: "'Libre Caslon Text', serif"
            }}>
              +{avgROI.toFixed(1)}%
            </div>
            <div className="text-xs text-neutral-500" style={{ fontFamily: 'Inter, sans-serif' }}>Return on investment</div>
          </div>

          <div className="bg-neutral-900 border border-neutral-700 rounded-lg p-6 hover:shadow-lg hover:shadow-neutral-600/20 hover:border-neutral-500 transition-all">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm text-neutral-300 font-bold tracking-wide" style={{ fontFamily: 'Inter, sans-serif', fontWeight: 700 }}>ACTIVE ALERTS</div>
            </div>
            <div className="text-3xl font-bold text-white mb-1" style={{ fontFamily: "'Libre Caslon Text', serif" }}>
              {recentAlerts.length}
            </div>
            <div className="text-xs text-neutral-500" style={{ fontFamily: 'Inter, sans-serif' }}>Currently available</div>
          </div>
        </div>

        {/* MODULE 2: ROI and Profit Tracking + MODULE 3: Win Rate by Alert Type */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Module 2: ROI Breakdown */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
            <h3 className="text-xl font-bold mb-5 tracking-wide border-b border-neutral-800 pb-3" style={{
              fontFamily: "'Libre Caslon Display', serif",
              background: 'linear-gradient(135deg, #D4AF37 0%, #C5A028 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              PROFIT BY ALERT TYPE
            </h3>
            <div className="space-y-4">
              <div className="bg-black rounded-lg p-4 border border-[#9B7507]">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[#C5A028] font-semibold">Arbitrage</span>
                  <span className="text-[#D4AF37] font-bold">${performanceData.arbitrage.total_profit.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-xs text-neutral-500">
                  <span>{performanceData.arbitrage.total_alerts} alerts</span>
                  <span>Avg: ${performanceData.arbitrage.avg_profit.toFixed(2)}/alert</span>
                </div>
                <div className="mt-2 bg-neutral-800 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-[#B8860B] to-[#D4AF37] h-2 rounded-full"
                    style={{ width: `${(performanceData.arbitrage.total_profit / totalProfit) * 100}%` }}
                  ></div>
                </div>
              </div>

              <div className="bg-black rounded-lg p-4 border border-neutral-700">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-neutral-300 font-semibold">Steam Moves</span>
                  <span className="text-white font-bold">${performanceData.steam_moves.total_profit.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-xs text-neutral-500">
                  <span>{performanceData.steam_moves.total_alerts} alerts</span>
                  <span>Avg: ${performanceData.steam_moves.avg_profit.toFixed(2)}/alert</span>
                </div>
                <div className="mt-2 bg-neutral-800 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-neutral-600 to-neutral-500 h-2 rounded-full"
                    style={{ width: `${(performanceData.steam_moves.total_profit / totalProfit) * 100}%` }}
                  ></div>
                </div>
              </div>

              <div className="bg-black rounded-lg p-4 border border-neutral-700">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-neutral-300 font-semibold">Line Movements</span>
                  <span className="text-white font-bold">${performanceData.line_movements.total_profit.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-xs text-neutral-500">
                  <span>{performanceData.line_movements.total_alerts} alerts</span>
                  <span>Avg: ${performanceData.line_movements.avg_profit.toFixed(2)}/alert</span>
                </div>
                <div className="mt-2 bg-neutral-800 rounded h-2">
                  <div
                    className="bg-gradient-to-r from-neutral-700 to-neutral-600 h-2 rounded"
                    style={{ width: `${(performanceData.line_movements.total_profit / totalProfit) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* Module 3: Win Rate Breakdown */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
            <h3 className="text-xl font-bold mb-5 tracking-wide border-b border-neutral-800 pb-3" style={{
              fontFamily: "'Libre Caslon Display', serif",
              background: 'linear-gradient(135deg, #D4AF37 0%, #C5A028 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              WIN RATE ANALYSIS
            </h3>
            <div className="space-y-4">
              <div className="bg-black rounded-lg p-4 border border-neutral-800">
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <div className="text-white font-semibold mb-1">Arbitrage Alerts</div>
                    <div className="text-xs text-neutral-500">
                      {performanceData.arbitrage.successful_alerts} wins / {performanceData.arbitrage.failed_alerts} losses / {performanceData.arbitrage.pending_alerts} pending
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-[#C5A028]">
                    {performanceData.arbitrage.win_rate.toFixed(1)}%
                  </div>
                </div>
                <div className="bg-neutral-800 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-[#B8860B] to-[#D4AF37] h-3 rounded-full flex items-center justify-end pr-2"
                    style={{ width: `${performanceData.arbitrage.win_rate}%` }}
                  >
                    <span className="text-[10px] text-white font-bold">{performanceData.arbitrage.win_rate.toFixed(0)}%</span>
                  </div>
                </div>
              </div>

              <div className="bg-black rounded-lg p-4 border border-neutral-800">
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <div className="text-white font-semibold mb-1">Steam Moves</div>
                    <div className="text-xs text-neutral-500">
                      {performanceData.steam_moves.successful_alerts} wins / {performanceData.steam_moves.failed_alerts} losses / {performanceData.steam_moves.pending_alerts} pending
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-neutral-300">
                    {performanceData.steam_moves.win_rate.toFixed(1)}%
                  </div>
                </div>
                <div className="bg-neutral-800 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-neutral-600 to-neutral-500 h-3 rounded-full flex items-center justify-end pr-2"
                    style={{ width: `${performanceData.steam_moves.win_rate}%` }}
                  >
                    <span className="text-[10px] text-white font-bold">{performanceData.steam_moves.win_rate.toFixed(0)}%</span>
                  </div>
                </div>
              </div>

              <div className="bg-black rounded-lg p-4 border border-neutral-800">
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <div className="text-white font-semibold mb-1">Line Movements</div>
                    <div className="text-xs text-neutral-500">
                      {performanceData.line_movements.successful_alerts} wins / {performanceData.line_movements.failed_alerts} losses / {performanceData.line_movements.pending_alerts} pending
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-neutral-300">
                    {performanceData.line_movements.win_rate.toFixed(1)}%
                  </div>
                </div>
                <div className="bg-neutral-800 rounded h-3">
                  <div
                    className="bg-gradient-to-r from-neutral-700 to-neutral-600 h-3 rounded flex items-center justify-end pr-2"
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
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6 mb-8">
          <h3 className="text-xl font-bold mb-5 tracking-wide border-b border-neutral-800 pb-3" style={{
            fontFamily: "'Libre Caslon Display', serif",
            background: 'linear-gradient(135deg, #D4AF37 0%, #C5A028 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
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
                    stroke="#171717"
                    strokeWidth="20"
                    fill="none"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="#d97706"
                    strokeWidth="20"
                    fill="none"
                    strokeDasharray={`${(performanceData.arbitrage.total_alerts / totalAlerts) * 440} 440`}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-3xl font-bold text-[#C5A028]">
                    {((performanceData.arbitrage.total_alerts / totalAlerts) * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-neutral-500">Arbitrage</div>
                </div>
              </div>
              <div className="mt-3 text-sm text-neutral-400">{performanceData.arbitrage.total_alerts} alerts</div>
            </div>

            <div className="text-center">
              <div className="relative inline-block">
                <svg className="w-40 h-40 transform -rotate-90">
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="#171717"
                    strokeWidth="20"
                    fill="none"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="#737373"
                    strokeWidth="20"
                    fill="none"
                    strokeDasharray={`${(performanceData.steam_moves.total_alerts / totalAlerts) * 440} 440`}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-3xl font-bold text-neutral-400">
                    {((performanceData.steam_moves.total_alerts / totalAlerts) * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-neutral-500">Steam</div>
                </div>
              </div>
              <div className="mt-3 text-sm text-neutral-400">{performanceData.steam_moves.total_alerts} alerts</div>
            </div>

            <div className="text-center">
              <div className="relative inline-block">
                <svg className="w-40 h-40 transform -rotate-90">
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="#171717"
                    strokeWidth="20"
                    fill="none"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="#525252"
                    strokeWidth="20"
                    fill="none"
                    strokeDasharray={`${(performanceData.line_movements.total_alerts / totalAlerts) * 440} 440`}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-3xl font-bold text-neutral-500">
                    {((performanceData.line_movements.total_alerts / totalAlerts) * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-neutral-500">Lines</div>
                </div>
              </div>
              <div className="mt-3 text-sm text-neutral-400">{performanceData.line_movements.total_alerts} alerts</div>
            </div>
          </div>
        </div>

        {/* MODULE 5: Profit Trends + MODULE 6: Recent High-Value Alerts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Module 5: Profit Trends */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
            <h3 className="text-xl font-bold text-[#C5A028] mb-5 tracking-wide border-b border-neutral-800 pb-3">
              CUMULATIVE PROFIT TREND
            </h3>
            <div className="space-y-3">
              {[
                { period: 'Last 7 Days', profit: totalProfit * 0.15, color: 'bg-neutral-600' },
                { period: 'Last 14 Days', profit: totalProfit * 0.28, color: 'bg-neutral-500' },
                { period: 'Last 30 Days', profit: totalProfit * 0.52, color: 'bg-neutral-400' },
                { period: 'All Time', profit: totalProfit, color: 'bg-[#B8860B]' }
              ].map((item) => (
                <div key={item.period} className="bg-black rounded-lg p-4 border border-neutral-800">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-neutral-400 text-sm">{item.period}</span>
                    <span className="text-white font-bold">${item.profit.toFixed(2)}</span>
                  </div>
                  <div className="bg-neutral-800 rounded h-2">
                    <div
                      className={`${item.color} h-2 rounded`}
                      style={{ width: `${(item.profit / totalProfit) * 100}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Module 6: Recent High-Value Alerts */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
            <h3 className="text-xl font-bold text-[#C5A028] mb-5 tracking-wide border-b border-neutral-800 pb-3">
              TOP ACTIVE OPPORTUNITIES
            </h3>
            <div className="space-y-3">
              {recentAlerts.length > 0 ? (
                recentAlerts.map((alert, idx) => (
                  <div key={idx} className="bg-black border border-[#9B7507] rounded-lg p-3">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="text-sm font-semibold text-white mb-1">
                          {alert.away_team} @ {alert.home_team}
                        </div>
                        <div className="text-xs text-neutral-500">
                          {alert.sport.toUpperCase()} • {alert.market_type}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-[#C5A028] font-bold text-lg">
                          +{alert.profit_percent.toFixed(2)}%
                        </div>
                        <div className="text-xs text-neutral-500">
                          ${alert.guaranteed_profit.toFixed(2)}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2 text-xs">
                      <span className="bg-neutral-900 px-2 py-1 rounded text-neutral-400 border border-neutral-800">
                        {alert.book_a}: {alert.odds_a > 0 ? '+' : ''}{alert.odds_a}
                      </span>
                      <span className="bg-neutral-900 px-2 py-1 rounded text-neutral-400 border border-neutral-800">
                        {alert.book_b}: {alert.odds_b > 0 ? '+' : ''}{alert.odds_b}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-neutral-500 py-8">
                  No active arbitrage opportunities at the moment
                </div>
              )}
            </div>
          </div>
        </div>

        {/* MODULE 7: Sport-by-Sport Breakdown */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6 mb-8">
          <h3 className="text-xl font-bold text-[#C5A028] mb-5 tracking-wide border-b border-neutral-800 pb-3">
            PERFORMANCE BY SPORT
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sportStats.map((sport) => (
              <div key={sport.sport} className="bg-black rounded-lg p-4 border border-neutral-800 hover:border-[#B8860B] transition-all">
                <div className="text-center mb-3">
                  <div className="flex justify-center mb-2">
                    {sport.hasLogo ? (
                      <img
                        src={sport.logo}
                        alt={`${sport.sport} logo`}
                        className="w-8 h-8 object-contain"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    ) : (
                      <span className="text-neutral-600 font-bold">{sport.sport}</span>
                    )}
                  </div>
                  <div className="text-lg font-bold text-white">{sport.sport}</div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-neutral-500">Alerts:</span>
                    <span className="text-white font-semibold">{sport.alerts}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-neutral-500">Profit:</span>
                    <span className="text-[#C5A028] font-semibold">${sport.profit.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-neutral-500">Win Rate:</span>
                    <span className="text-neutral-300 font-semibold">{sport.winRate}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* MODULE 8: Bookmaker Success Analysis */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6 mb-8">
          <h3 className="text-xl font-bold text-[#C5A028] mb-5 tracking-wide border-b border-neutral-800 pb-3">
            TOP PERFORMING BOOKMAKERS
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="text-left py-3 px-4 text-neutral-400 font-semibold">Bookmaker</th>
                  <th className="text-right py-3 px-4 text-neutral-400 font-semibold">Opportunities</th>
                  <th className="text-right py-3 px-4 text-neutral-400 font-semibold">Avg Profit</th>
                  <th className="text-right py-3 px-4 text-neutral-400 font-semibold">Win Rate</th>
                  <th className="text-right py-3 px-4 text-neutral-400 font-semibold">Rating</th>
                </tr>
              </thead>
              <tbody>
                {bookmakerStats.map((book, idx) => (
                  <tr key={book.book} className="border-b border-neutral-800/50 hover:bg-neutral-800/30 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                          idx === 0 ? 'bg-[#B8860B] text-white' :
                          idx === 1 ? 'bg-neutral-500 text-white' :
                          idx === 2 ? 'bg-[#9B7507] text-white' : 'bg-neutral-700 text-neutral-300'
                        }`}>
                          {idx + 1}
                        </div>
                        <span className="text-white font-semibold">{book.book}</span>
                      </div>
                    </td>
                    <td className="text-right py-3 px-4 text-white font-semibold">{book.opportunities}</td>
                    <td className="text-right py-3 px-4 text-[#C5A028] font-semibold">${book.avgProfit.toFixed(2)}</td>
                    <td className="text-right py-3 px-4">
                      <span className="text-neutral-300 font-semibold">{book.winRate}%</span>
                    </td>
                    <td className="text-right py-3 px-4">
                      <div className="flex justify-end gap-0.5">
                        {[...Array(5)].map((_, i) => (
                          <span key={i} className={i < Math.floor(book.winRate / 20) ? 'text-[#C5A028]' : 'text-neutral-700'}>
                            ★
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* MODULE 9: Time-based Performance Patterns */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
          <h3 className="text-xl font-bold text-[#C5A028] mb-5 tracking-wide border-b border-neutral-800 pb-3">
            PERFORMANCE BY TIME OF DAY
          </h3>
          <div className="space-y-4">
            {hourlyPerformance.map((period) => (
              <div key={period.time} className="bg-black rounded-lg p-4 border border-neutral-800">
                <div className="flex justify-between items-center mb-3">
                  <div className="text-white font-semibold">{period.time}</div>
                  <div className="flex gap-6">
                    <div className="text-right">
                      <div className="text-xs text-neutral-500">Alerts</div>
                      <div className="text-white font-bold">{period.alerts}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-neutral-500">Profit</div>
                      <div className="text-[#C5A028] font-bold">${period.profit.toFixed(2)}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-neutral-500">Win Rate</div>
                      <div className="text-neutral-300 font-bold">{period.winRate}%</div>
                    </div>
                  </div>
                </div>
                <div className="bg-neutral-800 rounded h-3">
                  <div
                    className="bg-gradient-to-r from-neutral-600 to-neutral-500 h-3 rounded transition-all"
                    style={{ width: `${(period.alerts / 401) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-5 bg-neutral-950 border border-[#B8860B] rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div>
                <div className="text-[#C5A028] font-semibold mb-1">Peak Performance Window</div>
                <div className="text-sm text-neutral-400">
                  Most profitable alerts occur between 6PM-9PM EST (prime game time).
                  Win rate peaks at 88.5% during this window with 401 total opportunities.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
