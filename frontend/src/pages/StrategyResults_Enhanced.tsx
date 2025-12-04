import { useState, useEffect } from 'react';

// Strategy interfaces
interface Strategy {
  id: number;
  angle_number?: number;
  name: string;
  description: string;
  why_it_works: string;
  example?: string;
  typical_ev_min: number;
  typical_ev_max: number;
  sports: string[];
  status: string;
  difficulty: string;
  bet_type?: string;
  frequency?: string;
  confidence?: number;
}

interface BacktestResult {
  strategy_id: number;
  strategy_name?: string;
  total_opportunities?: number;
  bets_placed?: number;
  wins: number;
  losses: number;
  pushes?: number;
  win_rate: number;
  roi: number;
  avg_edge?: number;
  profit_loss?: number;
  data_range?: string;
  baseline_odds?: number;
  roi_history?: number[];
}

interface PerformanceSummary {
  total_strategies: number;
  backtested_strategies: number;
  overall_win_rate: number;
  overall_roi: number;
  total_bets: number;
  total_wins: number;
  total_losses: number;
  total_pushes: number;
  total_profit: number;
  strategies: BacktestResult[];
}

type SortField = 'name' | 'ev' | 'roi' | 'win_rate' | 'frequency' | 'confidence';
type SortDirection = 'asc' | 'desc';

// Tooltip Component
const Tooltip = ({ children, text }: { children: React.ReactNode; text: string }) => {
  const [show, setShow] = useState(false);

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
      >
        {children}
      </div>
      {show && (
        <div className="absolute z-50 bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg shadow-xl whitespace-nowrap text-sm text-slate-200">
          {text}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
            <div className="border-4 border-transparent border-t-slate-800"></div>
          </div>
        </div>
      )}
    </div>
  );
};

// Sparkline Component for ROI trends
const Sparkline = ({ data }: { data: number[] }) => {
  if (!data || data.length === 0) return <span className="text-slate-500 text-xs">-</span>;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * 100;
    const y = 100 - ((value - min) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  const isPositiveTrend = data[data.length - 1] >= data[0];

  return (
    <svg className="w-16 h-8 inline-block" viewBox="0 0 100 100" preserveAspectRatio="none">
      <polyline
        points={points}
        fill="none"
        stroke={isPositiveTrend ? '#4ade80' : '#f87171'}
        strokeWidth="3"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
};

// Alert Subscription Modal
const AlertModal = ({ strategy, onClose }: { strategy: Strategy; onClose: () => void }) => {
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  const handleSubscribe = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/strategies/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy_id: strategy.id, email }),
      });

      if (response.ok) {
        setSubscribed(true);
        setTimeout(() => onClose(), 2000);
      }
    } catch (error) {
      console.error('Subscription error:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-slate-900 border-2 border-slate-700 rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-2xl font-bold text-white mb-2">Subscribe to Alerts</h2>
        <p className="text-slate-400 mb-4">Get notified when "{strategy.name}" entry signals are detected</p>

        {!subscribed ? (
          <>
            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded text-white mb-4"
            />
            <div className="flex gap-2">
              <button
                onClick={handleSubscribe}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded"
              >
                Subscribe
              </button>
              <button
                onClick={onClose}
                className="flex-1 bg-slate-700 hover:bg-slate-600 text-white font-semibold py-2 rounded"
              >
                Cancel
              </button>
            </div>
          </>
        ) : (
          <div className="text-center">
            <div className="text-4xl mb-2">✅</div>
            <p className="text-green-400 font-semibold">Successfully subscribed!</p>
          </div>
        )}
      </div>
    </div>
  );
};

export function StrategyResults() {
  const [selectedSport, setSelectedSport] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [performanceSummary, setPerformanceSummary] = useState<PerformanceSummary | null>(null);
  const [sortField, setSortField] = useState<SortField>('ev');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);

  const sports = [
    { key: 'all', name: 'ALL', emoji: '🎯' },
    { key: 'nba', name: 'NBA', emoji: '🏀' },
    { key: 'nfl', name: 'NFL', emoji: '🏈' },
    { key: 'nhl', name: 'NHL', emoji: '🏒' },
    { key: 'mlb', name: 'MLB', emoji: '⚾' },
    { key: 'ncaab', name: 'NCAAB', emoji: '🏀' },
    { key: 'ncaaf', name: 'NCAAF', emoji: '🏈' },
    { key: 'soccer', name: 'Soccer', emoji: '⚽' },
    { key: 'tennis', name: 'Tennis', emoji: '🎾' },
    { key: 'golf', name: 'Golf', emoji: '⛳' },
    { key: 'mma', name: 'MMA', emoji: '🥊' },
    { key: 'boxing', name: 'Boxing', emoji: '🥊' },
    { key: 'esports', name: 'Esports', emoji: '🎮' },
  ];

  // Fetch strategies and performance data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        const strategiesResponse = await fetch('http://localhost:8000/api/strategies/');
        const strategiesData = await strategiesResponse.json();

        // Add mock data for new fields (replace with real API data later)
        const enhancedStrategies = strategiesData.map((s: Strategy, idx: number) => ({
          ...s,
          bet_type: s.sports.includes('NBA') ? 'Live Total' : s.sports.includes('NFL') ? 'Spread' : 'Moneyline',
          frequency: idx % 3 === 0 ? '4x/week' : idx % 3 === 1 ? 'Daily' : '2x/week',
          confidence: Math.min(10, Math.max(6, 10 - Math.floor(idx / 2))),
        }));

        setStrategies(enhancedStrategies);

        const summaryResponse = await fetch('http://localhost:8000/api/strategies/performance/summary');
        const summaryData = await summaryResponse.json();

        // Add mock ROI history (replace with real API data)
        summaryData.strategies = summaryData.strategies.map((s: BacktestResult) => ({
          ...s,
          roi_history: Array.from({ length: 10 }, () => s.roi + (Math.random() - 0.5) * 5),
        }));

        setPerformanceSummary(summaryData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching strategies:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Create backtest results lookup
  const backtestResults: Record<number, BacktestResult> = {};
  if (performanceSummary) {
    performanceSummary.strategies.forEach(result => {
      backtestResults[result.strategy_id] = result;
    });
  }

  // Filter and sort strategies
  const filteredStrategies = strategies
    .filter(strategy => {
      const matchesSport = selectedSport === 'all' ||
        strategy.sports.includes(selectedSport.toUpperCase()) ||
        strategy.sports.includes('ALL');
      const matchesSearch = strategy.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        strategy.description.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSport && matchesSearch;
    })
    .sort((a, b) => {
      let aVal: number, bVal: number;

      switch (sortField) {
        case 'name':
          return sortDirection === 'asc'
            ? a.name.localeCompare(b.name)
            : b.name.localeCompare(a.name);
        case 'ev':
          aVal = (a.typical_ev_min + a.typical_ev_max) / 2;
          bVal = (b.typical_ev_min + b.typical_ev_max) / 2;
          break;
        case 'roi':
          aVal = backtestResults[a.id]?.roi || 0;
          bVal = backtestResults[b.id]?.roi || 0;
          break;
        case 'win_rate':
          aVal = backtestResults[a.id]?.win_rate || 0;
          bVal = backtestResults[b.id]?.win_rate || 0;
          break;
        case 'frequency':
          const freqMap: Record<string, number> = { 'Daily': 7, '4x/week': 4, '2x/week': 2 };
          aVal = freqMap[a.frequency || ''] || 0;
          bVal = freqMap[b.frequency || ''] || 0;
          break;
        case 'confidence':
          aVal = a.confidence || 0;
          bVal = b.confidence || 0;
          break;
        default:
          return 0;
      }

      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    });

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  // Performance metrics
  const totalOpportunities = performanceSummary?.total_bets || 0;
  const totalWins = performanceSummary?.total_wins || 0;
  const totalLosses = performanceSummary?.total_losses || 0;
  const overallWinRate = performanceSummary?.overall_win_rate || 0;
  const totalProfit = performanceSummary?.total_profit || 0;
  const avgROI = performanceSummary?.overall_roi || 0;
  const backtestedCount = performanceSummary?.backtested_strategies || 0;
  const avgEdge = performanceSummary?.strategies?.length > 0
    ? performanceSummary.strategies.reduce((sum, s) => sum + (s.avg_edge || 0), 0) / performanceSummary.strategies.length
    : 0;
  const collectingCount = filteredStrategies.filter(s => s.status === 'pending').length;

  // Status badge
  const StatusBadge = ({ status }: { status: string }) => {
    const configs: Record<string, { emoji: string; text: string; color: string }> = {
      active: { emoji: '✅', text: 'Backtested', color: 'text-green-400 bg-green-900/30 border-green-700' },
      pending: { emoji: '⏳', text: 'Pending', color: 'text-yellow-400 bg-yellow-900/30 border-yellow-700' },
      collecting: { emoji: '📊', text: 'Collecting Data', color: 'text-blue-400 bg-blue-900/30 border-blue-700' }
    };
    const config = configs[status] || configs.pending;
    return (
      <span className={`px-2 py-1 rounded border text-xs font-semibold ${config.color}`}>
        {config.emoji} {config.text}
      </span>
    );
  };

  // Strategy badges
  const StrategyBadges = ({ strategy, result }: { strategy: Strategy; result?: BacktestResult }) => {
    const badges = [];
    const avgEV = (strategy.typical_ev_min + strategy.typical_ev_max) / 2;

    if (avgEV >= 8) {
      badges.push({ text: 'High EV', color: 'bg-emerald-900/40 border-emerald-600 text-emerald-400' });
    }

    if (strategy.frequency === 'Daily' || strategy.frequency === '4x/week') {
      badges.push({ text: 'High Frequency', color: 'bg-blue-900/40 border-blue-600 text-blue-400' });
    }

    if (result && result.roi > 0 && result.roi < 15) {
      badges.push({ text: 'Low Volatility', color: 'bg-purple-900/40 border-purple-600 text-purple-400' });
    }

    return (
      <div className="flex flex-wrap gap-1 mt-1">
        {badges.map((badge, idx) => (
          <span key={idx} className={`px-1.5 py-0.5 rounded border text-xs font-semibold ${badge.color}`}>
            {badge.text}
          </span>
        ))}
      </div>
    );
  };

  // Sort indicator
  const SortIndicator = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black p-4" style={{ fontFamily: 'Rubik, sans-serif' }}>
      <div className="w-full mx-auto">
        {/* Header */}
        <div className="mb-4">
          <h1 className="text-4xl font-bold italic text-slate-100 mb-2" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>LIVE BETTING STRATEGY RESULTS</h1>
          <p className="text-slate-400 text-base">
            Backtested performance of strategies from "Interception" by Ed Miller & Matthew Davidow
          </p>
        </div>

        {/* Sport Tabs & Content */}
        <div className="flex gap-4 mb-2">
          {/* Sport Tabs - Vertical */}
          <div className="flex flex-col gap-2">
            {sports.map((sport) => (
              <button
                key={sport.key}
                onClick={() => setSelectedSport(sport.key)}
                className={`px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-2 ${
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

          {/* Main Content */}
          <div className="flex-1">
            {/* Performance Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
              <Tooltip text="Percentage of bets won across all strategies">
                <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 border border-green-700 rounded-lg p-2 cursor-help">
                  <div className="text-green-400 text-base font-semibold mb-0.5">Win Rate</div>
                  <div className="text-white text-4xl font-bold">{overallWinRate.toFixed(1)}%</div>
                  <div className="text-green-300 text-sm mt-0.5">{totalWins}W-{totalLosses}L</div>
                </div>
              </Tooltip>

              <Tooltip text="Return on Investment - Profit/loss as percentage of total amount wagered">
                <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border border-blue-700 rounded-lg p-2 cursor-help">
                  <div className="text-blue-400 text-base font-semibold mb-0.5">Avg ROI</div>
                  <div className="text-white text-4xl font-bold">{avgROI >= 0 ? '+' : ''}{avgROI.toFixed(1)}%</div>
                  <div className="text-blue-300 text-sm mt-0.5">Across {backtestedCount} strategies</div>
                </div>
              </Tooltip>

              <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border border-purple-700 rounded-lg p-2">
                <div className="text-purple-400 text-base font-semibold mb-0.5">Total Bets</div>
                <div className="text-white text-4xl font-bold">{totalOpportunities.toLocaleString()}</div>
                <div className="text-purple-300 text-sm mt-0.5">Backtested</div>
              </div>

              <Tooltip text="Expected Value - Average edge over the bookmaker on each bet">
                <div className="bg-gradient-to-br from-amber-900/50 to-amber-800/30 border border-amber-700 rounded-lg p-2 cursor-help">
                  <div className="text-amber-400 text-base font-semibold mb-0.5">Total Profit</div>
                  <div className="text-white text-4xl font-bold">{totalProfit >= 0 ? '+' : ''}{totalProfit.toFixed(1)}u</div>
                  <div className="text-amber-300 text-sm mt-0.5">Avg edge: {avgEdge >= 0 ? '+' : ''}{avgEdge.toFixed(1)}%</div>
                </div>
              </Tooltip>
            </div>

            {/* Search and Filters */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-3 mb-3">
              <div className="flex gap-3 items-center flex-wrap">
                <input
                  type="text"
                  placeholder="Search strategies..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 min-w-[200px] px-3 py-1.5 bg-slate-900 border border-slate-600 rounded text-white text-sm"
                />
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => toggleSort('ev')}
                    className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm rounded border border-slate-600"
                  >
                    Sort by EV <SortIndicator field="ev" />
                  </button>
                  <button
                    onClick={() => toggleSort('roi')}
                    className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm rounded border border-slate-600"
                  >
                    Sort by ROI <SortIndicator field="roi" />
                  </button>
                  <button
                    onClick={() => toggleSort('frequency')}
                    className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm rounded border border-slate-600"
                  >
                    Sort by Frequency <SortIndicator field="frequency" />
                  </button>
                </div>
              </div>
            </div>

            {/* Status Legend */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-2 mb-3">
              <div className="text-slate-300 text-base font-semibold mb-1">STATUS LEGEND:</div>
              <div className="flex flex-wrap gap-3 text-sm">
                <div className="flex items-center gap-2">
                  <StatusBadge status="active" />
                  <span className="text-slate-400">Historical backtest complete ({backtestedCount} strategies)</span>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status="pending" />
                  <span className="text-slate-400">Backtest pending ({collectingCount} strategies)</span>
                </div>
              </div>
            </div>

            {/* Strategies Table */}
            {loading ? (
              <div className="text-center text-white text-xl py-12">
                Loading strategies...
              </div>
            ) : (
              <div className="bg-slate-900 overflow-hidden border-2 border-slate-700 shadow-2xl rounded-lg">
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead className="bg-slate-800">
                      <tr>
                        <th className="text-left py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          Strategy
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          Sport
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          Bet Type
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          <Tooltip text="Expected Value - Your edge over the bookmaker">
                            <span className="cursor-help">Typical EV</span>
                          </Tooltip>
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          Win %
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          <Tooltip text="Return on Investment - Profit as % of total wagered">
                            <span className="cursor-help">ROI</span>
                          </Tooltip>
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          Sample Size
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          Odds Trigger
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          Frequency
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          Confidence
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-b-2 border-slate-600">
                          Alerts
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredStrategies.map((strategy, idx) => {
                        const result = backtestResults[strategy.id];
                        const avgEV = ((strategy.typical_ev_min + strategy.typical_ev_max) / 2).toFixed(0);

                        return (
                          <tr
                            key={strategy.id}
                            className={`hover:bg-slate-800/50 transition-colors ${
                              idx < filteredStrategies.length - 1 ? 'border-b border-slate-700' : ''
                            }`}
                          >
                            <td className="py-3 px-3 border-r border-slate-600">
                              <div className="text-white font-semibold text-sm">{strategy.name}</div>
                              <StrategyBadges strategy={strategy} result={result} />
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <div className="flex flex-wrap gap-1 justify-center">
                                {strategy.sports.map(sport => (
                                  <span key={sport} className="px-2 py-0.5 bg-slate-700 text-slate-300 text-xs rounded font-semibold">
                                    {sport}
                                  </span>
                                ))}
                              </div>
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <span className="text-slate-300 text-sm">{strategy.bet_type || 'N/A'}</span>
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <div className="text-green-400 font-bold text-base">+{avgEV}%</div>
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              {result ? (
                                <div className="text-white font-semibold text-base">
                                  {result.win_rate.toFixed(1)}%
                                </div>
                              ) : (
                                <span className="text-slate-500">-</span>
                              )}
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              {result ? (
                                <div>
                                  <div className={`font-bold text-lg ${result.roi > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    {result.roi > 0 ? '+' : ''}{result.roi.toFixed(1)}%
                                  </div>
                                  {result.roi_history && (
                                    <Tooltip text="Rolling ROI trend over time">
                                      <div className="cursor-help mt-1">
                                        <Sparkline data={result.roi_history} />
                                      </div>
                                    </Tooltip>
                                  )}
                                </div>
                              ) : (
                                <span className="text-slate-500">-</span>
                              )}
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              {result ? (
                                <div className="text-slate-300 text-sm font-semibold">
                                  {(result.bets_placed || result.total_opportunities || 0).toLocaleString()} bets
                                </div>
                              ) : (
                                <span className="text-slate-500">-</span>
                              )}
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              {result ? (
                                <div className="text-white font-bold text-base">
                                  {result.baseline_odds !== undefined ? (
                                    result.baseline_odds > 0 ? `+${result.baseline_odds}` : result.baseline_odds
                                  ) : '+125'}
                                </div>
                              ) : (
                                <span className="text-slate-500">-</span>
                              )}
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <span className="text-slate-300 text-sm font-semibold">{strategy.frequency || 'N/A'}</span>
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <div className="text-amber-400 font-bold text-lg">
                                {strategy.confidence || 'N/A'}/10
                              </div>
                            </td>
                            <td className="py-3 px-3 text-center">
                              <button
                                onClick={() => setSelectedStrategy(strategy)}
                                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded transition-colors"
                              >
                                🔔 Subscribe
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Stats Footer */}
            <div className="mt-4 text-center text-slate-500 text-base">
              Showing {filteredStrategies.length} strategies
              {selectedSport !== 'all' && ` for ${sports.find(s => s.key === selectedSport)?.name}`}
              • {backtestedCount} backtested • {collectingCount} collecting data
            </div>
          </div>
        </div>
      </div>

      {/* Alert Modal */}
      {selectedStrategy && (
        <AlertModal strategy={selectedStrategy} onClose={() => setSelectedStrategy(null)} />
      )}
    </div>
  );
}
