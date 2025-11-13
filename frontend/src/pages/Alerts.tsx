import { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { GoaliePullAlerts } from '../components/GoaliePullAlert';
import { FavoriteComebackAlerts } from '../components/FavoriteComebackAlert';
import { HalftimeTrackerAlerts } from '../components/HalftimeTrackerAlert';
import { MomentumAlerts } from '../components/MomentumAlert';
import { PaceMismatchAlerts } from '../components/PaceMismatchAlert';
import { WeatherImpactAlerts } from '../components/WeatherImpactAlert';
import { QuarterReversalAlerts } from '../components/QuarterReversalAlert';
import { AlertsOverallPerformance } from '../components/AlertsOverallPerformance';
import { GenericStrategyAlert } from '../components/GenericStrategyAlert';
import { AlertsPerformance } from '../components/AlertsPerformance';
import { getApiUrl } from '../config';
import { useSoundEffect } from '../hooks/useSoundEffect';
// Toast notifications removed - no longer needed

interface StrategyInfo {
  id: string;
  name: string;
  description: string;
  sport: string;
  sportColor: string;
  category: 'pregame' | 'live';
  hasComponent: boolean;
}

const ALL_STRATEGIES: StrategyInfo[] = [
  // LIVE STRATEGIES
  { id: 'comeback', name: 'NBA Favorite Comeback', description: 'Regression to mean when favorites trail underdogs after hot starts', sport: 'Basketball', sportColor: 'bg-orange-600', category: 'live', hasComponent: true },
  { id: 'quarter-reversal', name: 'Basketball Quarter Reversal', description: 'Teams winning 2 consecutive quarters lose the next (55-61%% hit rate, +8-35%% ROI) - NBA & NCAA', sport: 'Basketball', sportColor: 'bg-orange-600', category: 'live', hasComponent: true },
  { id: 'goalie', name: 'NHL Empty Net Goals', description: 'Predict empty net goal opportunities when goalies are pulled', sport: 'NHL', sportColor: 'bg-blue-600', category: 'live', hasComponent: true },
  { id: 'halftime', name: 'NBA Halftime Adjustments', description: 'Track period transitions and 1Q under opportunities', sport: 'Basketball', sportColor: 'bg-orange-600', category: 'live', hasComponent: true },
  { id: 'momentum', name: 'Momentum Detector', description: '5-minute sliding window to detect scoring runs and momentum shifts', sport: 'Basketball', sportColor: 'bg-orange-600', category: 'live', hasComponent: true },
  { id: 'nhl-period', name: 'NHL Period Tracking', description: 'Period-specific betting opportunities and transitions', sport: 'NHL', sportColor: 'bg-blue-600', category: 'live', hasComponent: false },

  // PRE-GAME STRATEGIES
  { id: 'steam', name: 'Steam Plays', description: 'Track sudden line movements from sharp money hitting the market', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: true },
  { id: 'arbitrage', name: 'Arbitrage', description: 'Risk-free profit opportunities across different sportsbooks', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: true },
  { id: 'lines', name: 'Middles', description: 'Bet both sides with a gap to win both or push one', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: true },
  { id: 'sharp-money', name: 'Sharp Money Tracking', description: 'Identify where professional bettors are placing their money', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: true },
  { id: 'clv', name: 'Closing Line Value (CLV)', description: 'Beat the closing line to ensure long-term profitability', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: false },
  { id: 'fatigue', name: 'Schedule Fatigue', description: 'Back-to-back games and rest differential analysis', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: false },
  { id: 'weather', name: 'NFL Weather Impact', description: 'Rain, snow, wind, and temperature effects on totals', sport: 'NFL', sportColor: 'bg-green-600', category: 'pregame', hasComponent: true },
  { id: 'pace', name: 'NBA Pace Mismatches', description: 'Identify tempo mismatches for over/under value', sport: 'NBA', sportColor: 'bg-orange-600', category: 'pregame', hasComponent: true },
  { id: 'matchup-history', name: 'Matchup History', description: 'Head-to-head trends and situational matchup analysis', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: false },
  { id: 'props', name: 'Player Props', description: 'Usage rates and matchup analysis for player markets', sport: 'NBA', sportColor: 'bg-orange-600', category: 'pregame', hasComponent: false },
  { id: 'regression', name: 'Regression Analysis', description: 'Identify teams due for positive or negative regression', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: false },
  { id: 'b2b-rested', name: 'NBA Back-to-Back vs Rested', description: 'Fade teams on B2B against fully rested opponents', sport: 'NBA', sportColor: 'bg-orange-600', category: 'pregame', hasComponent: false },
  { id: 'nhl-b2b-rested', name: 'NHL Back-to-Back vs Rested', description: 'NHL teams on B2B lose win rate vs rested teams', sport: 'NHL', sportColor: 'bg-blue-600', category: 'pregame', hasComponent: false },
  { id: 'home-away', name: 'Home/Away Splits', description: 'Exploit extreme home/away performance differentials', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: false },
  { id: 'divisional', name: 'Divisional Rivalries', description: 'Division games trend under due to defensive familiarity', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: false },
  { id: 'revenge', name: 'Revenge Games', description: 'Teams seeking revenge after lopsided losses', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: false },
  { id: 'fade-public', name: 'Fade the Public', description: 'Bet against teams with 70%+ public betting support', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: false },
  { id: 'rlm', name: 'Reverse Line Movement', description: 'Line moves opposite of public betting percentages', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: false },
  { id: 'blowout-bounce', name: 'After Blowout Loss', description: 'NBA teams bounce back strong ATS after losing big', sport: 'NBA', sportColor: 'bg-orange-600', category: 'pregame', hasComponent: false },
  { id: 'letdown', name: 'Letdown Spot', description: 'Fade teams coming off big emotional wins', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: false },
  { id: 'lookahead', name: 'Lookahead Spot', description: 'Fade teams before major games', sport: 'Multi-Sport', sportColor: 'bg-purple-600', category: 'pregame', hasComponent: false },
  { id: 'primetime', name: 'NFL Primetime Unders', description: 'NFL primetime games trend under the total', sport: 'NFL', sportColor: 'bg-green-600', category: 'pregame', hasComponent: false },
  { id: 'conference', name: 'Conference Mismatches', description: 'Exploit talent gaps between East and West', sport: 'NBA', sportColor: 'bg-orange-600', category: 'pregame', hasComponent: false },
];

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

interface MiddleAlert {
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  market_type: string;
  book_low: string;
  book_high: string;
  low_line: number;
  high_line: number;
  gap: number;
  side_low: string;
  side_high: string;
  odds_low: number;
  odds_high: number;
  timestamp: string;
  expires_in: number;
}

interface SharpMoneyAlert {
  id: string;
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  alert_type: string;
  market_type: string;
  recommendation: string;
  opening_line?: number;
  current_line?: number;
  movement?: number;
  sharp_books_involved: string[];
  confidence: number;
  confidence_level: string;
  reasoning: string;
  key_factors: string[];
  edge_percent: number;
  timestamp: string;
}

interface ScheduleFatigueAlert {
  id: string;
  game_id: string;
  sport: string;
  home_team: string;
  away_team: string;
  alert_type: string;
  market_type: string;
  fatigue_type: string;
  favored_side: string;
  home_rest_days: number;
  away_rest_days: number;
  rest_differential: number;
  home_is_b2b: boolean;
  away_is_b2b: boolean;
  confidence: number;
  confidence_level: string;
  reasoning: string;
  key_factors: string[];
  edge_percent: number;
  timestamp: string;
}

interface AlertsData {
  arbitrage: { count: number; alerts: ArbitrageAlert[] };
  steam_moves: { count: number; alerts: SteamMoveAlert[] };
  middles: { count: number; alerts: MiddleAlert[] };
  sharp_money: { count: number; alerts: SharpMoneyAlert[] };
  schedule_fatigue: { count: number; alerts: ScheduleFatigueAlert[] };
}

export function Alerts() {
  const location = useLocation();
  const [alertsData, setAlertsData] = useState<AlertsData | null>(null);
  const [goaliePullCount, setGoaliePullCount] = useState(0);
  const [favoriteComebackCount, setFavoriteComebackCount] = useState(0);
  const [halftimeCount, setHalftimeCount] = useState(0);
  const [momentumCount, setMomentumCount] = useState(0);
  const [paceMismatchCount, setPaceMismatchCount] = useState(0);
  const [weatherCount, setWeatherCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('comeback');
  const [categoryTab, setCategoryTab] = useState<'live' | 'pregame'>('live');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const alertBellRef = useRef<HTMLAudioElement>(null);
  const sirenRef = useRef<HTMLAudioElement>(null);
  const previousCountRef = useRef({ arbitrage: -1, steam: -1, lines: -1, goaliePull: -1, sharpMoney: -1, scheduleFatigue: -1 });
  const isInitialLoadRef = useRef(true);
  // Handle navigation state from clicks (when user clicks on other pages)
  useEffect(() => {
    const state = location.state as { category?: 'live' | 'pregame'; tab?: string } | null;
    if (state?.category && state?.tab) {
      setCategoryTab(state.category);
      setActiveTab(state.tab);
    }
  }, [location]);

  // Sound effects for different alert types
  const playGoaliePullSound = useSoundEffect('alert-bell.mp3', 0.6);
  const playArbitrageSound = useSoundEffect('alert-bell.mp3', 0.7);
  const playMiddleSound = useSoundEffect('alert-bell.mp3', 0.6);
  const playSteamMoveSound = useSoundEffect('alert-bell.mp3', 0.7);

  const fetchAlerts = async () => {
    try {
      const [alertsResponse, goalieResponse, comebackResponse, halftimeResponse, momentumResponse, paceResponse, weatherResponse] = await Promise.all([
        fetch(getApiUrl('alerts/all?user_id=default')),
        fetch(getApiUrl('goalie-pull-opportunities')),
        fetch(getApiUrl('favorite-comeback-opportunities')),
        fetch(getApiUrl('halftime-opportunities')),
        fetch(getApiUrl('momentum-opportunities')),
        fetch(getApiUrl('pace-mismatch-opportunities')),
        fetch(getApiUrl('weather-opportunities'))
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

      if (paceResponse.ok) {
        const paceData = await paceResponse.json();
        setPaceMismatchCount(paceData.count || 0);
      }

      if (weatherResponse.ok) {
        const weatherData = await weatherResponse.json();
        setWeatherCount(weatherData.count || 0);
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

  // Mark initial load as complete after first data fetch
  useEffect(() => {
    if (alertsData) {
      isInitialLoadRef.current = false;
    }
  }, [alertsData]);

  // Play sound when new goalie pull alerts arrive
  useEffect(() => {
    if (goaliePullCount > previousCountRef.current.goaliePull && previousCountRef.current.goaliePull > 0) {
      console.log('[GOALIE PULL ALERT] New alert detected! Playing sound...');
      playGoaliePullSound();
    }
    previousCountRef.current.goaliePull = goaliePullCount;
  }, [goaliePullCount, playGoaliePullSound]);

  // Play sound and show toast when new arbitrage alerts arrive
  useEffect(() => {
    const currentCount = alertsData?.arbitrage.count || 0;

    // Skip on initial load
    if (isInitialLoadRef.current) {
      previousCountRef.current.arbitrage = currentCount;
      return;
    }

    if (currentCount > previousCountRef.current.arbitrage && previousCountRef.current.arbitrage >= 0) {
      console.log('[ARBITRAGE ALERT] New alert detected! Playing sound...');
      playArbitrageSound();
    }
    previousCountRef.current.arbitrage = currentCount;
  }, [alertsData?.arbitrage.count, playArbitrageSound]);

  // Play sound when new middle alerts arrive
  useEffect(() => {
    const currentCount = alertsData?.middles.count || 0;

    // Skip on initial load
    if (isInitialLoadRef.current) {
      previousCountRef.current.lines = currentCount;
      return;
    }

    if (currentCount > previousCountRef.current.lines && previousCountRef.current.lines >= 0) {
      console.log('[MIDDLE ALERT] New alert detected! Playing sound...');
      playMiddleSound();
    }
    previousCountRef.current.lines = currentCount;
  }, [alertsData?.middles.count, playMiddleSound]);

  // Play sound when new steam move alerts arrive
  useEffect(() => {
    const currentCount = alertsData?.steam_moves.count || 0;

    // Skip on initial load
    if (isInitialLoadRef.current) {
      previousCountRef.current.steam = currentCount;
      return;
    }

    if (currentCount > previousCountRef.current.steam && previousCountRef.current.steam >= 0) {
      console.log('[STEAM MOVE ALERT] New alert detected! Playing sound...');
      playSteamMoveSound();
    }
    previousCountRef.current.steam = currentCount;
  }, [alertsData?.steam_moves.count, playSteamMoveSound]);

  // Play sound when new sharp money alerts arrive
  useEffect(() => {
    const currentCount = alertsData?.sharp_money.count || 0;

    // Skip on initial load
    if (isInitialLoadRef.current) {
      previousCountRef.current.sharpMoney = currentCount;
      return;
    }

    if (currentCount > previousCountRef.current.sharpMoney && previousCountRef.current.sharpMoney >= 0) {
      console.log('[SHARP MONEY ALERT] New alert detected! Playing sound...');
      playSteamMoveSound(); // Reuse steam move sound
    }
    previousCountRef.current.sharpMoney = currentCount;
  }, [alertsData?.sharp_money.count, playSteamMoveSound]);

  // Play sound when new schedule fatigue alerts arrive
  useEffect(() => {
    const currentCount = alertsData?.schedule_fatigue.count || 0;

    // Skip on initial load
    if (isInitialLoadRef.current) {
      previousCountRef.current.scheduleFatigue = currentCount;
      return;
    }

    if (currentCount > previousCountRef.current.scheduleFatigue && previousCountRef.current.scheduleFatigue >= 0) {
      console.log('[SCHEDULE FATIGUE ALERT] New alert detected! Playing sound...');
      playSteamMoveSound(); // Reuse steam move sound
    }
    previousCountRef.current.scheduleFatigue = currentCount;
  }, [alertsData?.schedule_fatigue.count, playSteamMoveSound]);

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
              <h1 className="text-4xl font-bold italic text-slate-100 mb-2" style={{ fontStyle: 'italic', textTransform: 'uppercase' }}>LIVE ALERTS</h1>
              <p className="text-slate-400">Real-time betting opportunities detected every 10 seconds</p>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`px-4 py-2 border font-bold tracking-wide transition-colors ${
                  autoRefresh
                    ? 'bg-gradient-to-br from-green-600 via-green-700 to-green-800 text-white border-green-500'
                    : 'bg-gradient-to-br from-slate-700 via-slate-800 to-slate-900 text-slate-300 border-slate-600 hover:border-blue-500'
                }`}
              >
                {autoRefresh ? 'AUTO-REFRESH ON' : 'AUTO-REFRESH OFF'}
              </button>
              <button
                onClick={fetchAlerts}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white border-2 border-blue-500 font-bold tracking-wide transition-all"
              >
                REFRESH NOW
              </button>
            </div>
          </div>


          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-2">
            <div className="bg-gradient-to-br from-orange-900/50 to-orange-800/30 border border-orange-700 rounded-lg p-1.5 transition-all hover:border-orange-500">
              <div className="text-xs text-orange-400 font-semibold mb-0">🔥 NBA COMEBACKS</div>
              <div className="text-3xl font-bold text-white leading-tight">{favoriteComebackCount}</div>
            </div>
            <div className="bg-gradient-to-br from-red-900/50 to-red-800/30 border border-red-700 rounded-lg p-1.5 transition-all hover:border-red-500">
              <div className="text-xs text-red-400 font-semibold mb-0">🚨 NHL GOALIE PULLS</div>
              <div className="text-3xl font-bold text-white leading-tight">{goaliePullCount}</div>
            </div>
            <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border border-purple-700 rounded-lg p-1.5 transition-all hover:border-purple-500">
              <div className="text-xs text-purple-400 font-semibold mb-0">⏰ NBA HALFTIME 2H</div>
              <div className="text-3xl font-bold text-white leading-tight">{halftimeCount}</div>
            </div>
            <div className="bg-gradient-to-br from-orange-900/50 to-orange-800/30 border border-orange-700 rounded-lg p-1.5 transition-all hover:border-orange-500">
              <div className="text-xs text-orange-400 font-semibold mb-0">🔥 MOMENTUM SURGES</div>
              <div className="text-3xl font-bold text-white leading-tight">{momentumCount}</div>
            </div>
            <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 border border-green-700 rounded-lg p-1.5 transition-all hover:border-green-500">
              <div className="text-xs text-green-400 font-semibold mb-0">ARBITRAGE</div>
              <div className="text-3xl font-bold text-white leading-tight">{alertsData?.arbitrage.count || 0}</div>
            </div>
            <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border border-blue-700 rounded-lg p-1.5 transition-all hover:border-blue-500">
              <div className="text-xs text-blue-400 font-semibold mb-0">STEAM MOVES</div>
              <div className="text-3xl font-bold text-white leading-tight">{alertsData?.steam_moves.count || 0}</div>
            </div>
            <div className="bg-gradient-to-br from-slate-900/50 to-slate-800/30 border border-slate-700 rounded-lg p-1.5 transition-all hover:border-slate-500">
              <div className="text-xs text-slate-400 font-semibold mb-0">MIDDLES</div>
              <div className="text-3xl font-bold text-white leading-tight">{alertsData?.middles.count || 0}</div>
            </div>
            <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border border-purple-700 rounded-lg p-1.5 transition-all hover:border-purple-500">
              <div className="text-xs text-purple-400 font-semibold mb-0">💰 SHARP MONEY</div>
              <div className="text-3xl font-bold text-white leading-tight">{alertsData?.sharp_money.count || 0}</div>
            </div>
          </div>
        </div>

        {/* Category Tabs */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => { setCategoryTab('live'); setActiveTab('comeback'); }}
            className={`px-8 py-4 border-2 font-bold text-lg tracking-wide transition-all ${
              categoryTab === 'live'
                ? 'bg-gradient-to-br from-red-600 via-red-700 to-red-800 text-white border-red-500 shadow-lg shadow-red-600/30'
                : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800 hover:border-blue-600'
            }`}
          >
            🔴 LIVE STRATEGIES ({ALL_STRATEGIES.filter(s => s.category === 'live').length})
          </button>
          <button
            onClick={() => { setCategoryTab('pregame'); setActiveTab('steam'); }}
            className={`px-8 py-4 border-2 font-bold text-lg tracking-wide transition-all ${
              categoryTab === 'pregame'
                ? 'bg-gradient-to-br from-green-600 via-green-700 to-green-800 text-white border-green-500 shadow-lg shadow-green-600/30'
                : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800 hover:border-blue-600'
            }`}
          >
            📊 PRE-GAME STRATEGIES ({ALL_STRATEGIES.filter(s => s.category === 'pregame').length})
          </button>
        </div>

        {/* Strategy Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {ALL_STRATEGIES.filter(s => s.category === categoryTab).map((strategy) => (
            <button
              key={strategy.id}
              onClick={() => setActiveTab(strategy.id)}
              className={`px-4 py-2 border font-semibold whitespace-nowrap transition-colors ${
                activeTab === strategy.id
                  ? `${strategy.sportColor} text-white border-white shadow-lg`
                  : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800 hover:border-blue-600'
              }`}
            >
              {strategy.name}
              {strategy.id === 'comeback' && ` (${favoriteComebackCount})`}
              {strategy.id === 'goalie' && ` (${goaliePullCount})`}
              {strategy.id === 'halftime' && ` (${halftimeCount})`}
              {strategy.id === 'momentum' && ` (${momentumCount})`}
              {strategy.id === 'pace' && ` (${paceMismatchCount})`}
              {strategy.id === 'weather' && ` (${weatherCount})`}
              {strategy.id === 'arbitrage' && ` (${alertsData?.arbitrage.count || 0})`}
              {strategy.id === 'steam' && ` (${alertsData?.steam_moves.count || 0})`}
              {strategy.id === 'lines' && ` (${alertsData?.middles.count || 0})`}
              {strategy.id === 'sharp-money' && ` (${alertsData?.sharp_money.count || 0})`}
              {strategy.id === 'fatigue' && ` (${alertsData?.schedule_fatigue.count || 0})`}
            </button>
          ))}
        </div>

        {/* Overall Performance Summary - Always Visible */}
        <AlertsOverallPerformance />

        {/* Arbitrage Alerts */}
        {activeTab === 'arbitrage' && (
          <div className="space-y-4">
            {alertsData?.arbitrage.alerts.length === 0 ? (
              <div className="bg-slate-800 border-2 border-slate-700 p-12 text-center">
                <div className="text-slate-400 text-lg">No arbitrage opportunities detected</div>
                <div className="text-slate-500 text-sm mt-2">Scanning every 10 seconds...</div>
              </div>
            ) : (
              alertsData?.arbitrage.alerts.map((alert, idx) => (
                <div key={idx} className="bg-slate-900 border-2 border-red-700 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 text-xs font-bold text-white ${getSportBadgeColor(alert.sport)}`}>
                        {alert.sport.toUpperCase()}
                      </span>
                      <span className="px-3 py-1 text-xs font-bold bg-green-600 text-white">
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
                    <div className="bg-slate-800 border-2 border-slate-700 p-4">
                      <div className="text-sm text-slate-400 mb-2">Book A: {alert.book_a}</div>
                      <div className="text-xl font-bold text-white mb-1">
                        {alert.odds_a > 0 ? `+${alert.odds_a}` : alert.odds_a}
                      </div>
                      <div className="text-sm text-slate-300">
                        Stake: ${alert.stake_a.toFixed(2)}
                      </div>
                    </div>
                    <div className="bg-slate-800 border-2 border-slate-700 p-4">
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
              <div className="bg-slate-800 border-2 border-slate-700 p-12 text-center">
                <div className="text-slate-400 text-lg">No steam moves detected</div>
                <div className="text-slate-500 text-sm mt-2">Scanning every 10 seconds...</div>
              </div>
            ) : (
              alertsData?.steam_moves.alerts.map((alert, idx) => (
                <div key={idx} className="bg-slate-900 border-2 border-blue-500 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 text-xs font-bold text-white ${getSportBadgeColor(alert.sport)}`}>
                        {alert.sport.toUpperCase()}
                      </span>
                      <span className="px-3 py-1 text-xs font-bold bg-orange-600 text-white">
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

                  <div className="bg-slate-800 border-2 border-slate-700 p-4 mb-4">
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

        {/* Middle Alerts */}
        {activeTab === 'lines' && (
          <div className="space-y-4">
            {alertsData?.middles.alerts.length === 0 ? (
              <div className="bg-slate-800 border-2 border-slate-700 p-12 text-center">
                <div className="text-slate-400 text-lg">No middle opportunities detected</div>
                <div className="text-slate-500 text-sm mt-2">Scanning every 10 seconds...</div>
              </div>
            ) : (
              alertsData?.middles.alerts.map((alert, idx) => (
                <div key={idx} className="bg-slate-900 border-2 border-purple-600 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 text-xs font-bold text-white ${getSportBadgeColor(alert.sport)}`}>
                        {alert.sport.toUpperCase()}
                      </span>
                      <span className="px-3 py-1 text-xs font-bold bg-purple-600 text-white">
                        {getMarketLabel(alert.market_type)}
                      </span>
                      <span className="text-lg font-bold text-white">
                        {alert.away_team} @ {alert.home_team}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-purple-400">
                        {alert.gap.toFixed(1)} pt gap
                      </div>
                      <div className="text-sm text-slate-400">
                        Expires in {formatExpiresIn(alert.expires_in)}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-slate-800 border-2 border-slate-700 p-4">
                      <div className="text-sm text-slate-400 mb-2">Low: {alert.book_low}</div>
                      <div className="text-lg font-bold text-white mb-1">
                        {alert.side_low}
                      </div>
                      <div className="text-sm text-slate-300">
                        Odds: {alert.odds_low > 0 ? `+${alert.odds_low}` : alert.odds_low}
                      </div>
                    </div>
                    <div className="bg-slate-800 border-2 border-slate-700 p-4">
                      <div className="text-sm text-slate-400 mb-2">High: {alert.book_high}</div>
                      <div className="text-lg font-bold text-white mb-1">
                        {alert.side_high}
                      </div>
                      <div className="text-sm text-slate-300">
                        Odds: {alert.odds_high > 0 ? `+${alert.odds_high}` : alert.odds_high}
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

        {/* Sharp Money Alerts */}
        {activeTab === 'sharp-money' && (
          <div className="space-y-4">
            {alertsData?.sharp_money.alerts.length === 0 ? (
              <div className="bg-slate-800 border-2 border-slate-700 p-12 text-center">
                <div className="text-slate-400 text-lg">No sharp money movements detected</div>
                <div className="text-slate-500 text-sm mt-2">Scanning every 2 minutes...</div>
              </div>
            ) : (
              alertsData?.sharp_money.alerts.map((alert, idx) => (
                <div key={idx} className="bg-slate-900 border-2 border-purple-600 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 text-xs font-bold text-white ${getSportBadgeColor(alert.sport)}`}>
                        {alert.sport.toUpperCase()}
                      </span>
                      <span className={`px-3 py-1 text-xs font-bold text-white ${
                        alert.confidence_level === 'HIGH' ? 'bg-green-600' :
                        alert.confidence_level === 'MEDIUM' ? 'bg-yellow-600' : 'bg-slate-600'
                      }`}>
                        {alert.confidence_level} CONFIDENCE
                      </span>
                      <span className="px-3 py-1 text-xs font-bold bg-purple-600 text-white">
                        {getMarketLabel(alert.market_type)}
                      </span>
                      <span className="text-lg font-bold text-white">
                        {alert.away_team} @ {alert.home_team}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-purple-400">
                        {alert.recommendation}
                      </div>
                      <div className="text-sm text-green-400">
                        {alert.edge_percent.toFixed(1)}% edge
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-slate-800 border-2 border-slate-700 p-4">
                      <div className="text-sm text-slate-400 mb-2">Line Movement</div>
                      <div className="text-lg font-bold text-white mb-1">
                        {alert.opening_line !== undefined && alert.current_line !== undefined ? (
                          <>
                            {alert.opening_line} → {alert.current_line}
                            <span className="text-sm text-yellow-400 ml-2">
                              ({alert.movement && alert.movement > 0 ? '+' : ''}{alert.movement?.toFixed(1)})
                            </span>
                          </>
                        ) : (
                          'Tracking...'
                        )}
                      </div>
                    </div>
                    <div className="bg-slate-800 border-2 border-slate-700 p-4">
                      <div className="text-sm text-slate-400 mb-2">Sharp Books Involved</div>
                      <div className="text-sm font-bold text-purple-400">
                        {alert.sharp_books_involved.join(', ')}
                      </div>
                    </div>
                  </div>

                  {alert.reasoning && (
                    <div className="bg-slate-800 border-2 border-slate-700 p-4 mb-4">
                      <div className="text-sm text-slate-400 mb-2">Analysis</div>
                      <div className="text-sm text-slate-200">{alert.reasoning}</div>
                    </div>
                  )}

                  {alert.key_factors.length > 0 && (
                    <div className="mb-4">
                      <div className="text-sm text-slate-400 mb-2">Key Factors</div>
                      <div className="flex flex-wrap gap-2">
                        {alert.key_factors.map((factor, i) => (
                          <span key={i} className="px-3 py-1 text-xs bg-slate-700 text-slate-300 border border-slate-600">
                            {factor}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="text-sm text-slate-500 text-right">
                    {formatTime(alert.timestamp)}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Schedule Fatigue Alerts */}
        {activeTab === 'fatigue' && (
          <div className="space-y-4">
            {alertsData?.schedule_fatigue.alerts.length === 0 ? (
              <div className="bg-slate-800 border-2 border-slate-700 p-12 text-center">
                <div className="text-slate-400 text-lg">No schedule fatigue situations detected</div>
                <div className="text-slate-500 text-sm mt-2">Scanning every hour for rest advantages...</div>
              </div>
            ) : (
              alertsData?.schedule_fatigue.alerts.map((alert, idx) => (
                <div key={idx} className="bg-slate-900 border-2 border-yellow-600 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 text-xs font-bold text-white ${getSportBadgeColor(alert.sport)}`}>
                        {alert.sport.toUpperCase()}
                      </span>
                      <span className={`px-3 py-1 text-xs font-bold text-white ${
                        alert.confidence_level === 'HIGH' ? 'bg-green-600' :
                        alert.confidence_level === 'MEDIUM' ? 'bg-yellow-600' : 'bg-slate-600'
                      }`}>
                        {alert.confidence_level} CONFIDENCE
                      </span>
                      <span className="px-3 py-1 text-xs font-bold bg-yellow-600 text-white">
                        {alert.fatigue_type.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className="text-lg font-bold text-white">
                        {alert.away_team} @ {alert.home_team}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-yellow-400">
                        FAVOR {alert.favored_side.toUpperCase()}
                      </div>
                      <div className="text-sm text-green-400">
                        {alert.edge_percent.toFixed(1)}% edge
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-slate-800 border-2 border-slate-700 p-4">
                      <div className="text-sm text-slate-400 mb-2">Rest Differential</div>
                      <div className="text-lg font-bold text-white mb-1">
                        {alert.rest_differential} days
                      </div>
                      <div className="text-sm text-slate-300">
                        Home: {alert.home_rest_days} days {alert.home_is_b2b && '(B2B)'}
                      </div>
                      <div className="text-sm text-slate-300">
                        Away: {alert.away_rest_days} days {alert.away_is_b2b && '(B2B)'}
                      </div>
                    </div>
                    <div className="bg-slate-800 border-2 border-slate-700 p-4">
                      <div className="text-sm text-slate-400 mb-2">Fatigue Impact</div>
                      <div className="text-sm font-bold text-yellow-400">
                        {alert.favored_side === 'home' ? alert.home_team : alert.away_team} has rest advantage
                      </div>
                    </div>
                  </div>

                  {alert.reasoning && (
                    <div className="bg-slate-800 border-2 border-slate-700 p-4 mb-4">
                      <div className="text-sm text-slate-400 mb-2">Analysis</div>
                      <div className="text-sm text-slate-200">{alert.reasoning}</div>
                    </div>
                  )}

                  {alert.key_factors.length > 0 && (
                    <div className="mb-4">
                      <div className="text-sm text-slate-400 mb-2">Key Factors</div>
                      <div className="flex flex-wrap gap-2">
                        {alert.key_factors.map((factor, i) => (
                          <span key={i} className="px-3 py-1 text-xs bg-slate-700 text-slate-300 border border-slate-600">
                            {factor}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

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

        {/* Pace Mismatch Alerts */}
        {activeTab === 'pace' && (
          <PaceMismatchAlerts />
        )}

        {/* Weather Impact Alerts */}
        {activeTab === 'weather' && (
          <WeatherImpactAlerts />
        )}

        {/* NBA Quarter Reversal Alerts */}
        {activeTab === 'quarter-reversal' && (
          <QuarterReversalAlerts />
        )}

        {/* Generic Strategy Alerts (for strategies without dedicated components) */}
        {ALL_STRATEGIES.filter(s => !s.hasComponent && s.id === activeTab).map((strategy) => (
          <GenericStrategyAlert
            key={strategy.id}
            strategyName={strategy.name}
            strategyDescription={strategy.description}
            sport={strategy.sport}
            sportColor={strategy.sportColor}
            category={strategy.category}
          />
        ))}

        {/* Alerts Performance Section */}
        <div className="mt-8">
          <AlertsPerformance />
        </div>
      </div>
    </div>
  );
}
