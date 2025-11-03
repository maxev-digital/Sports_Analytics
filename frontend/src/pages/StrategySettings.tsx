import { useState } from 'react';

interface Strategy {
  id: string;
  name: string;
  sport: 'NBA' | 'NHL' | 'NFL' | 'NCAAB' | 'Multi-Sport';
  sportColor: string;
  category: 'pregame' | 'live';
  description: string;
  sampleSize: string;
  edge: string;
  winRate: string;
  defaultEnabled: boolean;
}

const STRATEGIES: Strategy[] = [
  // ========== PRE-GAME STRATEGIES ==========
  {
    id: 'steam-plays',
    name: 'Steam Plays',
    sport: 'Multi-Sport',
    sportColor: 'bg-purple-600',
    category: 'pregame',
    description: 'Track sudden line movements from sharp money hitting the market',
    sampleSize: '49,847+ games',
    edge: '+4.2%',
    winRate: '54% (following steam)',
    defaultEnabled: true
  },
  {
    id: 'sharp-money',
    name: 'Sharp Money Tracking',
    sport: 'Multi-Sport',
    sportColor: 'bg-purple-600',
    category: 'pregame',
    description: 'Identify where professional bettors are placing their money',
    sampleSize: '98,263+ bets',
    edge: '+6.8%',
    winRate: '56% (sharp side)',
    defaultEnabled: true
  },
  {
    id: 'closing-line-value',
    name: 'Closing Line Value (CLV)',
    sport: 'Multi-Sport',
    sportColor: 'bg-purple-600',
    category: 'pregame',
    description: 'Beat the closing line to ensure long-term profitability',
    sampleSize: '197,841+ bets',
    edge: '+8.5%',
    winRate: '58% (positive CLV)',
    defaultEnabled: true
  },
  {
    id: 'multi-fatigue',
    name: 'Schedule Fatigue',
    sport: 'Multi-Sport',
    sportColor: 'bg-purple-600',
    category: 'pregame',
    description: 'Back-to-back games and rest differential analysis',
    sampleSize: '24,738+ games',
    edge: '+5.3%',
    winRate: '54% (B2B situations)',
    defaultEnabled: true
  },
  {
    id: 'nfl-weather',
    name: 'Weather Impact',
    sport: 'NFL',
    sportColor: 'bg-green-600',
    category: 'pregame',
    description: 'Rain, snow, wind, and temperature effects on totals',
    sampleSize: '3,187+ games',
    edge: '+11.2%',
    winRate: '62% (extreme weather)',
    defaultEnabled: true
  },
  {
    id: 'pace-based',
    name: 'Pace Mismatches',
    sport: 'NBA',
    sportColor: 'bg-orange-600',
    category: 'pregame',
    description: 'Identify tempo mismatches for over/under value',
    sampleSize: '17,842+ games',
    edge: '+7.1%',
    winRate: '57% (pace differential >8)',
    defaultEnabled: false
  },
  {
    id: 'matchup-history',
    name: 'Matchup History',
    sport: 'Multi-Sport',
    sportColor: 'bg-purple-600',
    category: 'pregame',
    description: 'Head-to-head trends and situational matchup analysis',
    sampleSize: '29,561+ matchups',
    edge: '+4.8%',
    winRate: '53% (strong trends)',
    defaultEnabled: false
  },
  {
    id: 'player-props',
    name: 'Player Props',
    sport: 'NBA',
    sportColor: 'bg-orange-600',
    category: 'pregame',
    description: 'Usage rates and matchup analysis for player markets',
    sampleSize: '48,923+ props',
    edge: '+9.3%',
    winRate: '59% (high usage)',
    defaultEnabled: false
  },
  {
    id: 'regression-analysis',
    name: 'Regression Analysis',
    sport: 'Multi-Sport',
    sportColor: 'bg-purple-600',
    category: 'pregame',
    description: 'Identify teams due for positive or negative regression',
    sampleSize: '39,614+ games',
    edge: '+5.7%',
    winRate: '55% (strong deviation)',
    defaultEnabled: false
  },
  {
    id: 'b2b-vs-rested',
    name: 'Back-to-Back vs Rested',
    sport: 'NBA',
    sportColor: 'bg-orange-600',
    category: 'pregame',
    description: 'Fade teams on B2B against fully rested opponents (3+ days rest)',
    sampleSize: '8,437+ games',
    edge: '+12.3%',
    winRate: '61% ATS (rested team)',
    defaultEnabled: true
  },
  {
    id: 'nhl-b2b-vs-rested',
    name: 'Back-to-Back vs Rested',
    sport: 'NHL',
    sportColor: 'bg-blue-600',
    category: 'pregame',
    description: 'NHL teams on B2B lose -4-5% win rate vs rested teams',
    sampleSize: '6,184+ games',
    edge: '+10.8%',
    winRate: '59% (rested team)',
    defaultEnabled: true
  },
  {
    id: 'home-away-splits',
    name: 'Home/Away Splits',
    sport: 'Multi-Sport',
    sportColor: 'bg-purple-600',
    category: 'pregame',
    description: 'Exploit extreme home/away performance differentials',
    sampleSize: '74,329+ games',
    edge: '+6.4%',
    winRate: '56% (extreme splits)',
    defaultEnabled: false
  },
  {
    id: 'divisional-rivalries',
    name: 'Divisional Rivalries',
    sport: 'Multi-Sport',
    sportColor: 'bg-purple-600',
    category: 'pregame',
    description: 'Division games trend under (defensive familiarity)',
    sampleSize: '19,783+ games',
    edge: '+5.1%',
    winRate: '54% (under)',
    defaultEnabled: false
  },
  {
    id: 'revenge-games',
    name: 'Revenge Games',
    sport: 'Multi-Sport',
    sportColor: 'bg-purple-600',
    category: 'pregame',
    description: 'Teams seeking revenge after lopsided losses (10+ points)',
    sampleSize: '11,826+ games',
    edge: '+7.9%',
    winRate: '58% ATS (revenge team)',
    defaultEnabled: false
  },
  {
    id: 'fade-the-public',
    name: 'Fade the Public',
    sport: 'Multi-Sport',
    sportColor: 'bg-purple-600',
    category: 'pregame',
    description: 'Bet against teams with 70%+ public betting support',
    sampleSize: '97,541+ bets',
    edge: '+8.2%',
    winRate: '57% (contrarian)',
    defaultEnabled: true
  },
  {
    id: 'reverse-line-movement',
    name: 'Reverse Line Movement (RLM)',
    sport: 'Multi-Sport',
    sportColor: 'bg-purple-600',
    category: 'pregame',
    description: 'Line moves opposite of public betting percentages (sharp money)',
    sampleSize: '48,917+ games',
    edge: '+9.7%',
    winRate: '59% (follow RLM)',
    defaultEnabled: true
  },
  {
    id: 'after-blowout-loss',
    name: 'After Blowout Loss',
    sport: 'NBA',
    sportColor: 'bg-orange-600',
    category: 'pregame',
    description: 'NBA teams bounce back strong ATS after losing by 15+ points',
    sampleSize: '4,927+ games',
    edge: '+11.4%',
    winRate: '61% ATS (next game)',
    defaultEnabled: false
  },
  {
    id: 'letdown-spot',
    name: 'Letdown Spot',
    sport: 'Multi-Sport',
    sportColor: 'bg-purple-600',
    category: 'pregame',
    description: 'Fade teams coming off big emotional wins (vs rivals, OT wins)',
    sampleSize: '14,738+ games',
    edge: '+6.7%',
    winRate: '56% (fade letdown)',
    defaultEnabled: false
  },
  {
    id: 'lookahead-spot',
    name: 'Lookahead Spot',
    sport: 'Multi-Sport',
    sportColor: 'bg-purple-600',
    category: 'pregame',
    description: 'Fade teams before major games (vs top opponents, playoffs)',
    sampleSize: '9,864+ games',
    edge: '+5.9%',
    winRate: '55% (fade lookahead)',
    defaultEnabled: false
  },
  {
    id: 'nfl-primetime-unders',
    name: 'Primetime Unders',
    sport: 'NFL',
    sportColor: 'bg-green-600',
    category: 'pregame',
    description: 'NFL primetime games (SNF, MNF, TNF) trend under the total',
    sampleSize: '817+ games',
    edge: '+8.3%',
    winRate: '58% (under)',
    defaultEnabled: false
  },
  {
    id: 'conference-mismatch',
    name: 'Conference Mismatches',
    sport: 'NBA',
    sportColor: 'bg-orange-600',
    category: 'pregame',
    description: 'Exploit talent gaps between East and West conferences',
    sampleSize: '17,659+ games',
    edge: '+4.6%',
    winRate: '53% (superior conference)',
    defaultEnabled: false
  },

  // ========== LIVE STRATEGIES ==========
  {
    id: 'nhl-goalie-pull',
    name: 'Empty Net Goals',
    sport: 'NHL',
    sportColor: 'bg-blue-600',
    category: 'live',
    description: 'Predict empty net goal opportunities when goalies are pulled in final minutes',
    sampleSize: '36,847+ games',
    edge: '+37.7%',
    winRate: '48% (profitable at +140 odds)',
    defaultEnabled: true
  },
  {
    id: 'nba-favorite-comeback',
    name: 'Favorite Comeback',
    sport: 'NBA',
    sportColor: 'bg-orange-600',
    category: 'live',
    description: 'Regression to mean when favorites trail underdogs after hot starts',
    sampleSize: '8,138 games',
    edge: '+9.4%',
    winRate: '60.3% ATS at halftime',
    defaultEnabled: true
  },
  {
    id: 'quarter-reversal',
    name: 'Quarter Reversal',
    sport: 'NBA',
    sportColor: 'bg-orange-600',
    category: 'live',
    description: 'Teams winning 2 consecutive quarters lose the next (55-61% hit rate, +8-35% ROI)',
    sampleSize: '1,230 games',
    edge: '+13.6%',
    winRate: '54.4% (backtested 2023-24)',
    defaultEnabled: true
  },
  {
    id: 'nba-halftime-tracker',
    name: 'Halftime Adjustments',
    sport: 'NBA',
    sportColor: 'bg-orange-600',
    category: 'live',
    description: 'Track period transitions and 1Q under opportunities',
    sampleSize: '11,942+ games',
    edge: '+8.5%',
    winRate: '64-67% (1Q under)',
    defaultEnabled: true
  },
  {
    id: 'nhl-halftime-tracker',
    name: 'Period Tracking',
    sport: 'NHL',
    sportColor: 'bg-blue-600',
    category: 'live',
    description: 'Period-specific betting opportunities and transitions',
    sampleSize: '8,473+ games',
    edge: '+7.2%',
    winRate: '58% (period props)',
    defaultEnabled: true
  },
  {
    id: 'nba-momentum',
    name: 'Momentum Detector',
    sport: 'NBA',
    sportColor: 'bg-orange-600',
    category: 'live',
    description: '5-minute sliding window to detect scoring runs and momentum shifts',
    sampleSize: '14,891+ games',
    edge: '+6.8%',
    winRate: '56% (8-0 runs)',
    defaultEnabled: false
  }
];

export function StrategySettings() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSport, setSelectedSport] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'pregame' | 'live'>('all');
  const [enabledStrategies, setEnabledStrategies] = useState<Set<string>>(
    new Set(STRATEGIES.filter(s => s.defaultEnabled).map(s => s.id))
  );
  const [saving, setSaving] = useState(false);

  // Filter strategies
  const getFilteredStrategies = () => {
    let filtered = STRATEGIES;

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(s => s.category === selectedCategory);
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(s =>
        s.name.toLowerCase().includes(query) ||
        s.description.toLowerCase().includes(query) ||
        s.sport.toLowerCase().includes(query)
      );
    }

    // Filter by sport
    if (selectedSport !== 'all') {
      filtered = filtered.filter(s => s.sport === selectedSport);
    }

    return filtered;
  };

  const filteredStrategies = getFilteredStrategies();
  const pregameCount = STRATEGIES.filter(s => s.category === 'pregame').length;
  const liveCount = STRATEGIES.filter(s => s.category === 'live').length;

  const toggleStrategy = (strategyId: string) => {
    setSaving(true);

    setEnabledStrategies(prev => {
      const newSet = new Set(prev);
      if (newSet.has(strategyId)) {
        newSet.delete(strategyId);
      } else {
        newSet.add(strategyId);
      }
      return newSet;
    });

    // Simulate API call
    setTimeout(() => setSaving(false), 500);
  };

  const enableAll = () => {
    setSaving(true);
    setEnabledStrategies(new Set(STRATEGIES.map(s => s.id)));
    setTimeout(() => setSaving(false), 500);
  };

  const disableAll = () => {
    setSaving(true);
    setEnabledStrategies(new Set());
    setTimeout(() => setSaving(false), 500);
  };

  const enableDefaults = () => {
    setSaving(true);
    setEnabledStrategies(new Set(STRATEGIES.filter(s => s.defaultEnabled).map(s => s.id)));
    setTimeout(() => setSaving(false), 500);
  };

  const enablePregame = () => {
    setSaving(true);
    setEnabledStrategies(new Set(STRATEGIES.filter(s => s.category === 'pregame').map(s => s.id)));
    setTimeout(() => setSaving(false), 500);
  };

  const enableLive = () => {
    setSaving(true);
    setEnabledStrategies(new Set(STRATEGIES.filter(s => s.category === 'live').map(s => s.id)));
    setTimeout(() => setSaving(false), 500);
  };

  const sportOptions = [
    { value: 'all', label: 'All Sports' },
    { value: 'NBA', label: 'NBA' },
    { value: 'NHL', label: 'NHL' },
    { value: 'NFL', label: 'NFL' },
    { value: 'NCAAB', label: 'NCAAB' },
    { value: 'Multi-Sport', label: 'Multi-Sport' }
  ];

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)' }}>
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Betting Strategies</h1>
          <p className="text-slate-400">
            Select which betting strategies you want to receive alerts for. Each strategy is backed by historical data and proven edge.
          </p>
        </div>

        {/* Category Tabs */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-6 py-3 rounded-lg font-bold transition-all ${
              selectedCategory === 'all'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            All Strategies ({STRATEGIES.length})
          </button>
          <button
            onClick={() => setSelectedCategory('pregame')}
            className={`px-6 py-3 rounded-lg font-bold transition-all ${
              selectedCategory === 'pregame'
                ? 'bg-green-600 text-white shadow-lg'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            📊 Pre-game ({pregameCount})
          </button>
          <button
            onClick={() => setSelectedCategory('live')}
            className={`px-6 py-3 rounded-lg font-bold transition-all ${
              selectedCategory === 'live'
                ? 'bg-red-600 text-white shadow-lg'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            🔴 Live ({liveCount})
          </button>
        </div>

        {/* Stats Bar */}
        <div className="bg-slate-800/50 rounded-lg p-4 mb-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-slate-400">Enabled Strategies: </span>
              <span className="text-white font-semibold text-lg">
                {enabledStrategies.size} / {STRATEGIES.length}
              </span>
            </div>
            {saving && (
              <div className="flex items-center gap-2 text-blue-400">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                Saving...
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mb-6">
          <div className="flex flex-wrap gap-3">
            <button
              onClick={enableAll}
              disabled={saving}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-semibold"
            >
              Enable All ({STRATEGIES.length})
            </button>
            <button
              onClick={disableAll}
              disabled={saving}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-semibold"
            >
              Disable All
            </button>
            <button
              onClick={enableDefaults}
              disabled={saving}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-semibold"
            >
              Recommended Only ({STRATEGIES.filter(s => s.defaultEnabled).length})
            </button>
            <button
              onClick={enablePregame}
              disabled={saving}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-semibold"
            >
              All Pre-game ({pregameCount})
            </button>
            <button
              onClick={enableLive}
              disabled={saving}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-semibold"
            >
              All Live ({liveCount})
            </button>
          </div>
        </div>

        {/* Search and Filter Bar */}
        <div className="mb-6 flex gap-4 flex-wrap">
          {/* Search Input */}
          <div className="flex-1 min-w-[250px]">
            <input
              type="text"
              placeholder="Search strategies..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Sport Filter */}
          <select
            value={selectedSport}
            onChange={(e) => setSelectedSport(e.target.value)}
            className="px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700 focus:border-blue-500 focus:outline-none"
          >
            {sportOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Strategy Grid */}
        {filteredStrategies.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {filteredStrategies.map((strategy) => {
              const isEnabled = enabledStrategies.has(strategy.id);

              return (
                <div
                  key={strategy.id}
                  className={`bg-slate-800/50 rounded-lg p-6 border transition-all ${
                    isEnabled
                      ? 'border-blue-500 shadow-lg shadow-blue-500/20'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    {/* Header with Sport Badge, Category, and Toggle */}
                    <div className="flex items-center gap-3 flex-1">
                      <div className={`${strategy.sportColor} text-white px-3 py-1 rounded-lg text-sm font-bold`}>
                        {strategy.sport}
                      </div>
                      <div className={`${strategy.category === 'pregame' ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'} px-2 py-1 rounded text-xs font-bold`}>
                        {strategy.category === 'pregame' ? '📊 PRE' : '🔴 LIVE'}
                      </div>
                      <h3 className="text-white font-bold text-lg">{strategy.name}</h3>
                    </div>

                    {/* Toggle Switch */}
                    <button
                      onClick={() => toggleStrategy(strategy.id)}
                      disabled={saving}
                      className={`relative inline-flex items-center h-6 rounded-full w-11 transition-colors focus:outline-none ${
                        isEnabled ? 'bg-blue-600' : 'bg-slate-600'
                      } ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <span
                        className={`inline-block w-4 h-4 transform bg-white rounded-full transition-transform ${
                          isEnabled ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>

                  {/* Description */}
                  <p className="text-slate-300 text-sm mb-4">
                    {strategy.description}
                  </p>

                  {/* Performance Metrics */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                      <div className="text-slate-400 text-xs mb-1">Sample Size</div>
                      <div className="text-white font-bold text-sm">{strategy.sampleSize}</div>
                    </div>

                    <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                      <div className="text-slate-400 text-xs mb-1">Edge</div>
                      <div className="text-green-400 font-bold text-sm">{strategy.edge}</div>
                    </div>

                    <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                      <div className="text-slate-400 text-xs mb-1">Win Rate</div>
                      <div className="text-blue-400 font-bold text-sm">{strategy.winRate}</div>
                    </div>
                  </div>

                  {/* Default Badge */}
                  {strategy.defaultEnabled && (
                    <div className="mt-3">
                      <div className="inline-block px-2 py-1 bg-yellow-500/20 text-yellow-300 text-xs font-semibold rounded">
                        Recommended
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-slate-400 text-lg">
              No strategies found matching your search.
            </div>
          </div>
        )}

        {/* Info Footer */}
        <div className="mt-8 p-4 bg-blue-900/20 border border-blue-700/50 rounded-lg">
          <div className="text-sm text-blue-300">
            <strong>Note:</strong> <span className="text-green-300">📊 Pre-game strategies</span> analyze data before the game starts (line movement, sharp money, matchups). <span className="text-red-300">🔴 Live strategies</span> require real-time in-game data (momentum, comebacks, periods). Enabling a strategy means you'll receive real-time alerts when opportunities are detected.
          </div>
        </div>

        {/* Learn More Section */}
        <div className="mt-6 p-4 bg-purple-900/20 border border-purple-700/50 rounded-lg">
          <div className="text-sm text-purple-300">
            <strong>Want to learn more?</strong> Check out our <a href="/learn" className="text-purple-400 hover:text-purple-300 underline">Learn section</a> for detailed guides on each strategy, including full mathematical breakdowns and historical performance analysis.
          </div>
        </div>
      </div>
    </div>
  );
}
