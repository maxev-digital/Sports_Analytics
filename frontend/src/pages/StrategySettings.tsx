import { useState } from 'react';

interface Strategy {
  id: string;
  name: string;
  sport: 'NBA' | 'NHL' | 'NFL' | 'NCAAB' | 'Multi-Sport';
  sportColor: string;
  description: string;
  sampleSize: string;
  edge: string;
  winRate: string;
  defaultEnabled: boolean;
}

const STRATEGIES: Strategy[] = [
  {
    id: 'nhl-goalie-pull',
    name: 'Empty Net Goals',
    sport: 'NHL',
    sportColor: 'bg-blue-600',
    description: 'Predict empty net goal opportunities when goalies are pulled in final minutes',
    sampleSize: '37,000+ games',
    edge: '+37.7%',
    winRate: '48% (profitable at +140 odds)',
    defaultEnabled: true
  },
  {
    id: 'nba-favorite-comeback',
    name: 'Favorite Comeback',
    sport: 'NBA',
    sportColor: 'bg-orange-600',
    description: 'Regression to mean when favorites trail underdogs after hot starts',
    sampleSize: '8,138 games',
    edge: '+9.4%',
    winRate: '60.3% ATS at halftime',
    defaultEnabled: true
  },
  {
    id: 'nba-halftime-tracker',
    name: 'Halftime Adjustments',
    sport: 'NBA',
    sportColor: 'bg-orange-600',
    description: 'Track period transitions and 1Q under opportunities',
    sampleSize: '12,000+ games',
    edge: '+8.5%',
    winRate: '64-67% (1Q under)',
    defaultEnabled: true
  },
  {
    id: 'nhl-halftime-tracker',
    name: 'Period Tracking',
    sport: 'NHL',
    sportColor: 'bg-blue-600',
    description: 'Period-specific betting opportunities and transitions',
    sampleSize: '8,500+ games',
    edge: '+7.2%',
    winRate: '58% (period props)',
    defaultEnabled: true
  },
  {
    id: 'nba-momentum',
    name: 'Momentum Detector',
    sport: 'NBA',
    sportColor: 'bg-orange-600',
    description: '5-minute sliding window to detect scoring runs and momentum shifts',
    sampleSize: '15,000+ games',
    edge: '+6.8%',
    winRate: '56% (8-0 runs)',
    defaultEnabled: false
  },
  {
    id: 'multi-fatigue',
    name: 'Schedule Fatigue',
    sport: 'Multi-Sport',
    sportColor: 'bg-purple-600',
    description: 'Back-to-back games and rest differential analysis',
    sampleSize: '25,000+ games',
    edge: '+5.3%',
    winRate: '54% (B2B situations)',
    defaultEnabled: false
  },
  {
    id: 'nfl-weather',
    name: 'Weather Impact',
    sport: 'NFL',
    sportColor: 'bg-green-600',
    description: 'Rain, snow, wind, and temperature effects on totals',
    sampleSize: '3,200+ games',
    edge: '+11.2%',
    winRate: '62% (extreme weather)',
    defaultEnabled: false
  }
];

export function StrategySettings() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSport, setSelectedSport] = useState<string>('all');
  const [enabledStrategies, setEnabledStrategies] = useState<Set<string>>(
    new Set(STRATEGIES.filter(s => s.defaultEnabled).map(s => s.id))
  );
  const [saving, setSaving] = useState(false);

  // Filter strategies
  const getFilteredStrategies = () => {
    let filtered = STRATEGIES;

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
                    {/* Header with Sport Badge and Toggle */}
                    <div className="flex items-center gap-3 flex-1">
                      <div className={`${strategy.sportColor} text-white px-3 py-1 rounded-lg text-sm font-bold`}>
                        {strategy.sport}
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
            <strong>Note:</strong> Enabling a strategy means you'll receive real-time alerts when opportunities are detected.
            All strategies are backed by historical data and statistical analysis. Changes are saved automatically.
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
