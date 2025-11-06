import { useState, useEffect } from 'react';
import { getApiUrl } from '../config';
import { loadOddsLookupTable, getOddsWithColor, formatOddsDisplay } from '../utils/oddsTriggerLookup';
import { useAuth } from '../contexts/AuthContext';

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
  edge_decay?: 'Low' | 'Medium' | 'High';
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

type SortField = 'name' | 'ev' | 'roi' | 'win_rate' | 'frequency' | 'confidence' | 'sample_size' | 'edge_decay';
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
        <div className="absolute z-[9999] top-full left-1/2 transform -translate-x-1/2 mt-2 px-3 py-2 bg-slate-900 border-2 border-blue-500 rounded-lg shadow-2xl whitespace-nowrap text-sm text-white min-w-max">
          {text}
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-[-1px]">
            <div className="border-8 border-transparent border-b-blue-500"></div>
          </div>
        </div>
      )}
    </div>
  );
};

// Alert Subscription Modal
const AlertModal = ({ strategy, onClose }: { strategy: Strategy; onClose: () => void }) => {
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  const handleSubscribe = async () => {
    try {
      const response = await fetch(getApiUrl('/strategies/subscribe'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy_id: strategy.id, email }),
      });

      if (response.ok) {
        setSubscribed(true);
        setTimeout(() => onClose(), 2000);
      } else {
        alert('Subscription failed. Please try again.');
      }
    } catch (error) {
      console.error('Subscription error:', error);
      alert('Network error. Please check your connection.');
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

// User statistics interface
interface UserStatistics {
  total_bets: number;
  wins: number;
  losses: number;
  pushes: number;
  win_rate: number;
  roi: number;
  total_profit: number;
  total_wagered: number;
}

export function PreGameStrategyResults() {
  const { token, username } = useAuth();
  const [selectedSport, setSelectedSport] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [performanceSummary, setPerformanceSummary] = useState<PerformanceSummary | null>(null);
  const [userStats, setUserStats] = useState<UserStatistics | null>(null);
  const [sortField, setSortField] = useState<SortField>('ev');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [selectedStrategies, setSelectedStrategies] = useState<Set<number>>(new Set());

  // Toggle strategy selection
  const toggleStrategySelection = (strategyId: number) => {
    const newSelected = new Set(selectedStrategies);
    if (newSelected.has(strategyId)) {
      newSelected.delete(strategyId);
    } else {
      newSelected.add(strategyId);
    }
    setSelectedStrategies(newSelected);
  };

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
    const fetchWithRetry = async (url: string, retries = 3, delay = 1000): Promise<Response> => {
      for (let i = 0; i < retries; i++) {
        try {
          const response = await fetch(url);
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
          return response;
        } catch (error) {
          if (i === retries - 1) throw error;
          console.warn(`Retry ${i + 1}/${retries} for ${url}:`, error);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
      throw new Error('Max retries exceeded');
    };

    const fetchData = async () => {
      try {
        setLoading(true);

        const strategiesResponse = await fetchWithRetry(getApiUrl('/strategies/'));
        const strategiesData = await strategiesResponse.json();

        // Filter for pre-game strategies only (17-22, 25)
        // Include: 17 (Sharp Money), 18-22 (CLV, Home/Away, Divisional, Key Numbers, Low-Hold), 25 (Pace Mismatch)
        // Exclude: 23 (Halftime Tracker - live), 24 (Momentum Detector - live)
        const preGameStrategies = strategiesData.filter((s: Strategy) =>
          s.id === 17 || (s.id >= 18 && s.id <= 22) || s.id === 25
        );

        // Helper function to determine edge decay rate
        const getEdgeDecay = (strategy: Strategy): 'Low' | 'Medium' | 'High' => {
          const name = strategy.name.toLowerCase();

          // High edge decay - value disappears quickly (live betting, arbitrage, line movement)
          if (name.includes('live') || name.includes('arbitrage') || name.includes('line movement') ||
              name.includes('middle') || name.includes('steam') || name.includes('momentum') ||
              name.includes('goalie pull') || name.includes('reversal') || name.includes('pace mismatch')) {
            return 'High';
          }

          // Low edge decay - value persists longer (pre-game analysis, long-term tracking)
          if (name.includes('clv') || name.includes('home/away') || name.includes('key numbers') ||
              name.includes('divisional') || name.includes('weather') || name.includes('fatigue') ||
              name.includes('back-to-back')) {
            return 'Low';
          }

          // Medium edge decay - moderate urgency (most other strategies)
          return 'Medium';
        };

        // Add mock data for new fields (replace with real API data later)
        const enhancedStrategies = preGameStrategies.map((s: Strategy, idx: number) => ({
          ...s,
          bet_type: s.sports.includes('NBA') ? 'Spread' : s.sports.includes('NFL') ? 'Spread' : 'Moneyline',
          frequency: idx % 3 === 0 ? '4x/week' : idx % 3 === 1 ? 'Daily' : '2x/week',
          confidence: Math.min(10, Math.max(6, 10 - Math.floor(idx / 2))),
          edge_decay: getEdgeDecay(s),
        }));

        setStrategies(enhancedStrategies);

        const summaryResponse = await fetchWithRetry(getApiUrl('/strategies/performance/summary'));
        const summaryData = await summaryResponse.json();

        setPerformanceSummary(summaryData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching strategies:', error);
        alert('Failed to load strategies. Please refresh the page.');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Load odds trigger lookup table on component mount
  useEffect(() => {
    loadOddsLookupTable().catch(error => {
      console.error('Failed to load odds lookup table:', error);
    });
  }, []);

  // Fetch user bet statistics
  useEffect(() => {
    const fetchUserStats = async () => {
      if (!token || !username) return;

      try {
        const response = await fetch(getApiUrl(`bets/user/${username}/stats`));

        if (response.ok) {
          const data = await response.json();
          // Map backend field names to expected frontend names
          setUserStats({
            total_bets: data.settled_bets || 0,
            wins: data.won_bets || 0,
            losses: data.lost_bets || 0,
            pushes: data.push_bets || 0,
            win_rate: data.win_rate || 0,
            roi: data.roi_percent || 0,
            total_profit: data.net_profit_loss || 0,
            total_wagered: data.settled_wagered || 0
          });
        }
      } catch (error) {
        console.error('Error fetching user statistics:', error);
      }
    };

    fetchUserStats();
  }, [token, username]);

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
        case 'sample_size':
          aVal = backtestResults[a.id]?.bets_placed || 0;
          bVal = backtestResults[b.id]?.bets_placed || 0;
          break;
        case 'frequency':
          const freqMap: Record<string, number> = { 'Daily': 7, '4x/week': 4, '2x/week': 2 };
          aVal = freqMap[a.frequency || ''] || 0;
          bVal = freqMap[b.frequency || ''] || 0;
          break;
        case 'edge_decay':
          const edgeDecayMap: Record<string, number> = { 'High': 3, 'Medium': 2, 'Low': 1 };
          aVal = edgeDecayMap[a.edge_decay || 'Medium'] || 2;
          bVal = edgeDecayMap[b.edge_decay || 'Medium'] || 2;
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
    const configs: Record<string, { text: string; color: string }> = {
      proven: { text: 'Proven', color: 'text-emerald-400 bg-emerald-900/40 border-emerald-600' },
      active: { text: 'Backtested', color: 'text-green-400 bg-green-900/30 border-green-700' },
      pending: { text: 'Pending', color: 'text-yellow-400 bg-yellow-900/30 border-yellow-700' },
      collecting: { text: 'Collecting Data', color: 'text-blue-400 bg-blue-900/30 border-blue-700' }
    };
    const config = configs[status] || configs.pending;
    return (
      <span className={`px-2 py-1 rounded border text-xs font-semibold ${config.color}`}>
        {config.text}
      </span>
    );
  };

  // Strategy badges
  const StrategyBadges = ({ strategy, result }: { strategy: Strategy; result?: BacktestResult }) => {
    const badges = [];
    const avgEV = (strategy.typical_ev_min + strategy.typical_ev_max) / 2;

    // NEW badge for Phase 9 strategies (IDs 18-25)
    if (strategy.id >= 18 && strategy.id <= 25) {
      badges.push({ text: 'NEW', color: 'bg-pink-900/40 border-pink-600 text-pink-400 animate-pulse' });
    }

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

  // Calculate Strategy Stack metrics
  const selectedStratData = Array.from(selectedStrategies)
    .map(id => {
      const strategy = strategies.find(s => s.id === id);
      const result = backtestResults[id];
      return { strategy, result };
    })
    .filter(item => item.strategy && item.result);

  const stackExpected = selectedStratData.reduce((acc, { result, strategy }) => {
    if (result) {
      const freqMap: Record<string, number> = { 'Daily': 7, '4x/week': 4, '2x/week': 2, '': 0 };
      const betsPerDay = (freqMap[strategy?.frequency || ''] || 0) / 7;

      // Calculate profit_loss from ROI if not provided
      // profit_loss = (roi / 100) * bets_placed * 100 (assuming $100 per bet)
      const profitLoss = result.profit_loss !== undefined
        ? result.profit_loss
        : ((result.roi / 100) * (result.bets_placed || 0) * 100);

      return {
        totalBets: acc.totalBets + (result.bets_placed || 0),
        totalWins: acc.totalWins + result.wins,
        totalLosses: acc.totalLosses + result.losses,
        totalProfit: acc.totalProfit + profitLoss,
        betsPerDay: acc.betsPerDay + betsPerDay,
      };
    }
    return acc;
  }, { totalBets: 0, totalWins: 0, totalLosses: 0, totalProfit: 0, betsPerDay: 0 });

  const stackWinRate = stackExpected.totalBets > 0
    ? (stackExpected.totalWins / (stackExpected.totalWins + stackExpected.totalLosses)) * 100
    : 0;

  // ROI calculation: profit_loss is in dollars (assuming $100/bet)
  // ROI = (total_profit / total_wagered) * 100 = (profit_loss / (bets * 100)) * 100
  const stackROI = stackExpected.totalBets > 0
    ? (stackExpected.totalProfit / (stackExpected.totalBets * 100)) * 100
    : 0;

  // Profit per unit (1 unit = $100)
  const stackProfitPerUnit = stackExpected.totalBets > 0
    ? stackExpected.totalProfit / 100  // Convert dollars to units
    : 0;

  // Loading Skeleton Component
  const LoadingSkeleton = () => (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black p-4" style={{ fontFamily: 'Rubik, sans-serif' }}>
      <div className="w-full mx-auto">
        {/* Header Skeleton */}
        <div className="mb-4 animate-pulse">
          <div className="h-10 w-96 bg-slate-700 rounded mb-2"></div>
          <div className="h-6 w-64 bg-slate-800 rounded"></div>
        </div>

        <div className="flex gap-4 mb-2">
          {/* Sport Tabs Skeleton */}
          <div className="flex flex-col gap-2">
            {[...Array(13)].map((_, i) => (
              <div key={i} className="h-9 w-24 bg-slate-800 rounded animate-pulse"></div>
            ))}
          </div>

          {/* Content Skeleton */}
          <div className="flex-1">
            {/* Performance Cards Skeleton */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-24 bg-gradient-to-br from-slate-800/50 to-slate-700/30 border border-slate-600 rounded-lg animate-pulse"></div>
              ))}
            </div>

            {/* Strategy Stack Skeleton */}
            <div className="h-6 w-48 bg-slate-700 rounded mb-2 animate-pulse"></div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-28 bg-gradient-to-br from-slate-800/50 to-slate-700/30 border border-slate-600 rounded animate-pulse"></div>
              ))}
            </div>

            {/* Search Skeleton */}
            <div className="h-16 bg-slate-800/50 border border-slate-700 rounded-lg mb-3 animate-pulse"></div>

            {/* Status Legend Skeleton */}
            <div className="h-16 bg-slate-800/50 border border-slate-700 rounded-lg mb-3 animate-pulse"></div>

            {/* Table Skeleton */}
            <div className="bg-slate-900 border-2 border-slate-700 rounded-lg p-4">
              <div className="space-y-3">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="h-16 bg-slate-800 rounded animate-pulse"></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Loading state
  if (loading) {
    return <LoadingSkeleton />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black p-4" style={{ fontFamily: 'Rubik, sans-serif' }}>
      <div className="w-full mx-auto">
        {/* Header */}
        <div className="mb-4">
          <h1 className="text-4xl font-bold text-slate-100 mb-2">Pre-Game Betting Strategy Results</h1>
          <p className="text-slate-400 text-base">
            Historical backtest performance for pre-game betting strategies
          </p>
        </div>

        {/* Beta Disclaimer Banner */}
        <div className="mb-4 bg-gradient-to-r from-green-900/40 via-green-800/30 to-green-900/40 border-2 border-green-600/50 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="text-2xl">🧪</div>
            <div className="flex-1">
              <h3 className="text-green-400 font-bold text-lg mb-2">Beta Mode - Data Optimization in Progress</h3>
              <p className="text-green-200 text-sm leading-relaxed">
                Results in Beta Mode are based on our historical game and odds data with backtesting ongoing.
                Live games are being logged and stored for our Machine Learning Models every day.
                By the time we launch the official site after beta, data will be refined and optimized for more accurate results.
              </p>
            </div>
          </div>
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
            {/* Users Results Section */}
            <h2 className="text-sm font-bold text-blue-300 mb-2">Users Results</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-3">
              <Tooltip text="Your actual win rate from graded bets in My Bets">
                <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 border border-green-700 rounded-lg p-1.5 cursor-help">
                  <div className="text-green-400 text-xs font-semibold mb-0">Win Rate</div>
                  <div className="text-white text-3xl font-bold leading-tight">
                    {userStats ? `${userStats.win_rate.toFixed(1)}%` : '--'}
                  </div>
                  <div className="text-green-300 text-xs mt-0">
                    {userStats ? `${userStats.wins}W-${userStats.losses}L` : 'No graded bets yet'}
                  </div>
                </div>
              </Tooltip>

              <Tooltip text="Your actual ROI - Profit/loss as percentage of total amount wagered">
                <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border border-blue-700 rounded-lg p-1.5 cursor-help">
                  <div className="text-blue-400 text-xs font-semibold mb-0">ROI</div>
                  <div className="text-white text-3xl font-bold leading-tight">
                    {userStats ? `${userStats.roi >= 0 ? '+' : ''}${userStats.roi.toFixed(1)}%` : '--'}
                  </div>
                  <div className="text-blue-300 text-xs mt-0">From My Bets</div>
                </div>
              </Tooltip>

              <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border border-purple-700 rounded-lg p-1.5">
                <div className="text-purple-400 text-xs font-semibold mb-0">Total Bets</div>
                <div className="text-white text-3xl font-bold leading-tight">
                  {userStats ? userStats.total_bets : '--'}
                </div>
                <div className="text-purple-300 text-xs mt-0">Graded</div>
              </div>

              <Tooltip text="Your actual profit/loss from graded bets">
                <div className="bg-gradient-to-br from-amber-900/50 to-amber-800/30 border border-amber-700 rounded-lg p-1.5 cursor-help">
                  <div className="text-amber-400 text-xs font-semibold mb-0">Total Profit</div>
                  <div className="text-white text-3xl font-bold leading-tight">
                    {userStats ? `${userStats.total_profit >= 0 ? '+' : ''}$${userStats.total_profit.toFixed(0)}` : '--'}
                  </div>
                  <div className="text-amber-300 text-xs mt-0">
                    {userStats ? `Wagered: $${userStats.total_wagered.toFixed(0)}` : 'Place bets to track'}
                  </div>
                </div>
              </Tooltip>
            </div>

            {/* Strategy Stack Metrics - Expected Performance */}
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-bold text-indigo-300">
                Strategy Stack {selectedStrategies.size > 0 && `(${selectedStrategies.size} selected)`}
              </h2>
              {selectedStrategies.size > 0 && (
                <button
                  onClick={() => setSelectedStrategies(new Set())}
                  className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded"
                >
                  Clear All
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-3">
              {/* Expected Win Rate */}
              <Tooltip text="Expected win rate based on historical backtest data for selected strategies">
                <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 border border-green-600 rounded-lg p-1.5 cursor-help">
                  <div className="text-green-400 text-xs font-semibold mb-0">Expected Win Rate</div>
                  <div className="text-white text-3xl font-bold leading-tight">
                    {selectedStrategies.size > 0 ? `${stackWinRate.toFixed(1)}%` : '--'}
                  </div>
                  <div className="text-green-300 text-xs mt-0">
                    {selectedStrategies.size > 0 ? `${stackExpected.totalWins}W-${stackExpected.totalLosses}L` : 'Select strategies'}
                  </div>
                </div>
              </Tooltip>

              {/* Expected ROI */}
              <Tooltip text="Expected return on investment for selected strategies">
                <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border border-blue-600 rounded-lg p-1.5 cursor-help">
                  <div className="text-blue-400 text-xs font-semibold mb-0">Expected ROI</div>
                  <div className="text-white text-3xl font-bold leading-tight">
                    {selectedStrategies.size > 0 ? `${stackROI >= 0 ? '+' : ''}${stackROI.toFixed(1)}%` : '--'}
                  </div>
                  <div className="text-blue-300 text-xs mt-0">
                    {selectedStrategies.size > 0 ? `${stackExpected.betsPerDay.toFixed(1)} bets/day` : 'Historical avg'}
                  </div>
                </div>
              </Tooltip>

              {/* Total Bets */}
              <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border border-purple-600 rounded-lg p-1.5">
                <div className="text-purple-400 text-xs font-semibold mb-0">Total Bets</div>
                <div className="text-white text-3xl font-bold leading-tight">
                  {selectedStrategies.size > 0 ? stackExpected.totalBets.toLocaleString() : '--'}
                </div>
                <div className="text-purple-300 text-xs mt-0">Historical data</div>
              </div>

              {/* Expected Profit */}
              <Tooltip text="Expected profit based on historical performance">
                <div className="bg-gradient-to-br from-amber-900/50 to-amber-800/30 border border-amber-600 rounded-lg p-1.5 cursor-help">
                  <div className="text-amber-400 text-xs font-semibold mb-0">Expected Profit</div>
                  <div className="text-white text-3xl font-bold leading-tight">
                    {selectedStrategies.size > 0 ? `${stackExpected.totalProfit >= 0 ? '+' : ''}${stackExpected.totalProfit.toFixed(1)}u` : '--'}
                  </div>
                  <div className="text-amber-300 text-xs mt-0">
                    {selectedStrategies.size > 0 ? `${stackProfitPerUnit >= 0 ? '+' : ''}${stackProfitPerUnit.toFixed(2)}u per unit` : 'Based on backtest'}
                  </div>
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
            ) : filteredStrategies.length === 0 ? (
              <div className="bg-slate-900 border-2 border-slate-700 shadow-2xl rounded-lg p-12 text-center">
                <div className="text-6xl mb-4">🔍</div>
                <h3 className="text-2xl font-bold text-white mb-2">No strategies found</h3>
                <p className="text-slate-400 text-lg mb-4">
                  {searchQuery ? (
                    <>No strategies match your search query "{searchQuery}"</>
                  ) : (
                    <>No strategies available for {sports.find(s => s.key === selectedSport)?.name || 'this sport'}</>
                  )}
                </p>
                <div className="flex gap-3 justify-center">
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery('')}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded"
                    >
                      Clear Search
                    </button>
                  )}
                  {selectedSport !== 'all' && (
                    <button
                      onClick={() => setSelectedSport('all')}
                      className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded"
                    >
                      View All Sports
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-slate-900 border-2 border-slate-700 shadow-2xl rounded-lg overflow-visible">
                {/* Mobile scroll hint */}
                <div className="md:hidden bg-blue-900/40 border-b-2 border-blue-600 px-4 py-2 text-center">
                  <span className="text-blue-300 text-xs font-semibold">← Scroll horizontally to see all columns →</span>
                </div>
                <div className="overflow-x-auto overflow-y-visible">
                  <table className="w-full border-collapse min-w-[1200px]">
                    <thead className="bg-slate-800">
                      <tr>
                        <th className="text-center py-2 px-2 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 w-12">
                          <input
                            type="checkbox"
                            checked={selectedStrategies.size === filteredStrategies.length && filteredStrategies.length > 0}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedStrategies(new Set(filteredStrategies.map(s => s.id)));
                              } else {
                                setSelectedStrategies(new Set());
                              }
                            }}
                            className="w-4 h-4 cursor-pointer"
                          />
                        </th>
                        <th
                          className="text-left py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 cursor-pointer hover:bg-slate-700 transition-colors"
                          onClick={() => toggleSort('name')}
                        >
                          <Tooltip text="Betting strategy name and associated badges (NEW, High EV, etc.)">
                            <span className="cursor-pointer">
                              Strategy <SortIndicator field="name" />
                            </span>
                          </Tooltip>
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          Sport
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          Bet Type
                        </th>
                        <th
                          className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 cursor-pointer hover:bg-slate-700 transition-colors"
                          onClick={() => toggleSort('ev')}
                        >
                          <Tooltip text="Expected Value - Your edge over the bookmaker">
                            <span className="cursor-pointer">
                              Typical EV <SortIndicator field="ev" />
                            </span>
                          </Tooltip>
                        </th>
                        <th
                          className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 cursor-pointer hover:bg-slate-700 transition-colors"
                          onClick={() => toggleSort('win_rate')}
                        >
                          <Tooltip text="Winning percentage - What % of bets won historically">
                            <span className="cursor-pointer">
                              Win % <SortIndicator field="win_rate" />
                            </span>
                          </Tooltip>
                        </th>
                        <th
                          className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 cursor-pointer hover:bg-slate-700 transition-colors"
                          onClick={() => toggleSort('roi')}
                        >
                          <Tooltip text="Return on Investment - Profit as % of total wagered">
                            <span className="cursor-pointer">
                              ROI <SortIndicator field="roi" />
                            </span>
                          </Tooltip>
                        </th>
                        <th
                          className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 cursor-pointer hover:bg-slate-700 transition-colors"
                          onClick={() => toggleSort('sample_size')}
                        >
                          <Tooltip text="Number of historical bets analyzed in backtest">
                            <span className="cursor-pointer">
                              Sample Size <SortIndicator field="sample_size" />
                            </span>
                          </Tooltip>
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600">
                          <Tooltip text="Minimum acceptable odds to bet this strategy at break-even, based on historical win rate. Anything worse has negative expected value.">
                            <span className="cursor-help">Min Odds</span>
                          </Tooltip>
                        </th>
                        <th
                          className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 cursor-pointer hover:bg-slate-700 transition-colors"
                          onClick={() => toggleSort('frequency')}
                        >
                          <Tooltip text="How often betting opportunities appear (Daily, 4x/week, 2x/week)">
                            <span className="cursor-pointer">
                              Frequency <SortIndicator field="frequency" />
                            </span>
                          </Tooltip>
                        </th>
                        <th
                          className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 cursor-pointer hover:bg-slate-700 transition-colors"
                          onClick={() => toggleSort('edge_decay')}
                        >
                          <Tooltip text="How quickly the betting edge disappears - High means act fast, Low means edge persists">
                            <span className="cursor-pointer">
                              Edge Decay <SortIndicator field="edge_decay" />
                            </span>
                          </Tooltip>
                        </th>
                        <th
                          className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-r border-b-2 border-slate-600 cursor-pointer hover:bg-slate-700 transition-colors"
                          onClick={() => toggleSort('confidence')}
                        >
                          <Tooltip text="Strategy confidence rating 1-10 based on edge size and consistency">
                            <span className="cursor-pointer">
                              Confidence <SortIndicator field="confidence" />
                            </span>
                          </Tooltip>
                        </th>
                        <th className="text-center py-2 px-3 text-slate-300 font-bold text-xs uppercase tracking-wider border-b-2 border-slate-600">
                          <Tooltip text="Subscribe to real-time alerts when this strategy triggers">
                            <span className="cursor-help">Alerts</span>
                          </Tooltip>
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
                            className={`hover:bg-slate-800/70 hover:shadow-lg hover:scale-[1.01] transition-all duration-200 cursor-pointer ${
                              idx < filteredStrategies.length - 1 ? 'border-b border-slate-700' : ''
                            } ${selectedStrategies.has(strategy.id) ? 'bg-blue-900/20 border-l-4 border-l-blue-500' : ''}`}
                          >
                            <td className="py-3 px-2 text-center border-r border-slate-600">
                              <input
                                type="checkbox"
                                checked={selectedStrategies.has(strategy.id)}
                                onChange={() => toggleStrategySelection(strategy.id)}
                                className="w-4 h-4 cursor-pointer"
                              />
                            </td>
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
                                <div className={`font-bold text-lg ${result.roi > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                  {result.roi > 0 ? '+' : ''}{result.roi.toFixed(1)}%
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
                              {result && result.win_rate ? (
                                (() => {
                                  const { odds, colorClass } = getOddsWithColor(result.win_rate);
                                  return (
                                    <div className={`${colorClass} font-bold text-base`}>
                                      {odds}
                                    </div>
                                  );
                                })()
                              ) : (
                                <span className="text-slate-500">-</span>
                              )}
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              <span className="text-slate-300 text-sm font-semibold">{strategy.frequency || 'N/A'}</span>
                            </td>
                            <td className="py-3 px-3 text-center border-r border-slate-600">
                              {strategy.edge_decay === 'High' && (
                                <span className="px-2 py-1 bg-red-900/40 border border-red-600 text-red-400 rounded text-xs font-bold">
                                  HIGH
                                </span>
                              )}
                              {strategy.edge_decay === 'Medium' && (
                                <span className="px-2 py-1 bg-yellow-900/40 border border-yellow-600 text-yellow-400 rounded text-xs font-bold">
                                  MED
                                </span>
                              )}
                              {strategy.edge_decay === 'Low' && (
                                <span className="px-2 py-1 bg-green-900/40 border border-green-600 text-green-400 rounded text-xs font-bold">
                                  LOW
                                </span>
                              )}
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
                                Subscribe
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
