import { useState, useEffect } from 'react';
import { useSettings } from '../hooks/useSettings';
import { BOOKMAKERS, getPopularBookmakers, getAllBookmakerKeys } from '../data/bookmakers';

interface BookmakersByRegion {
  [region: string]: typeof BOOKMAKERS;
}

export function Settings() {
  const {
    settings,
    loading,
    saving,
    error,
    updateBookmakers,
    toggleBookmaker,
    enableAllBookmakers,
    disableAllBookmakers,
    enablePopularBookmakers,
    resetToDefaults
  } = useSettings('default');

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRegion, setSelectedRegion] = useState<string>('all');

  // Group bookmakers by region for organized display
  const bookmakersByRegion: BookmakersByRegion = {};
  Object.entries(BOOKMAKERS).forEach(([key, bookmaker]) => {
    const primaryRegion = bookmaker.region[0];
    if (!bookmakersByRegion[primaryRegion]) {
      bookmakersByRegion[primaryRegion] = {};
    }
    bookmakersByRegion[primaryRegion][key] = bookmaker;
  });

  // Filter bookmakers based on search and region
  const getFilteredBookmakers = () => {
    let filtered = Object.entries(BOOKMAKERS);

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(([_, bookmaker]) =>
        bookmaker.name.toLowerCase().includes(query) ||
        bookmaker.key.toLowerCase().includes(query)
      );
    }

    // Filter by region
    if (selectedRegion !== 'all') {
      filtered = filtered.filter(([_, bookmaker]) =>
        bookmaker.region.includes(selectedRegion)
      );
    }

    return filtered;
  };

  const filteredBookmakers = getFilteredBookmakers();
  const enabledCount = settings?.enabled_bookmakers.length || 0;
  const totalCount = Object.keys(BOOKMAKERS).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-slate-300">Loading settings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-red-400">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
          <p className="text-slate-400">
            Select which bookmakers you want to see in odds feeds and alerts. You need at least 2 bookmakers enabled for comparison.
          </p>
        </div>

        {/* Stats Bar */}
        <div className="bg-slate-800/50 rounded-lg p-4 mb-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-slate-400">Enabled Bookmakers: </span>
              <span className="text-white font-semibold text-lg">
                {enabledCount} / {totalCount}
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
              onClick={enableAllBookmakers}
              disabled={saving}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-semibold"
            >
              Enable All ({totalCount})
            </button>
            <button
              onClick={disableAllBookmakers}
              disabled={saving}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-semibold"
            >
              Disable All
            </button>
            <button
              onClick={enablePopularBookmakers}
              disabled={saving}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-semibold"
            >
              Popular Only ({getPopularBookmakers().length})
            </button>
            <button
              onClick={resetToDefaults}
              disabled={saving}
              className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-semibold"
            >
              Reset to Defaults
            </button>
          </div>
        </div>

        {/* Search and Filter Bar */}
        <div className="mb-6 flex gap-4 flex-wrap">
          {/* Search Input */}
          <div className="flex-1 min-w-[250px]">
            <input
              type="text"
              placeholder="Search bookmakers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Region Filter */}
          <select
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            className="px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700 focus:border-blue-500 focus:outline-none"
          >
            <option value="all">All Regions</option>
            <option value="US">United States</option>
            <option value="UK">United Kingdom</option>
            <option value="AU">Australia</option>
            <option value="EU">Europe</option>
            <option value="CA">Canada</option>
            <option value="ASIA">Asia</option>
            <option value="Global">Global/Offshore</option>
          </select>
        </div>

        {/* Bookmaker Grid */}
        {filteredBookmakers.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredBookmakers.map(([key, bookmaker]) => {
              const isEnabled = settings?.enabled_bookmakers.includes(key) || false;
              const isPopular = bookmaker.popular || false;

              return (
                <div
                  key={key}
                  className={`bg-slate-800/50 rounded-lg p-4 border transition-all ${
                    isEnabled
                      ? 'border-blue-500 shadow-lg shadow-blue-500/20'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    {/* Logo and Name */}
                    <div className="flex items-center gap-3 flex-1">
                      <img
                        src={bookmaker.logo}
                        alt={bookmaker.name}
                        className="w-10 h-10 rounded"
                        onError={(e) => {
                          // Fallback to favicon if logo fails
                          e.currentTarget.src = bookmaker.logoFallback;
                        }}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-white truncate">
                          {bookmaker.name}
                        </div>
                        <div className="text-xs text-slate-400">
                          {bookmaker.region.join(', ')}
                        </div>
                      </div>
                    </div>

                    {/* Toggle Switch */}
                    <button
                      onClick={() => toggleBookmaker(key)}
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

                  {/* Popular Badge */}
                  {isPopular && (
                    <div className="inline-block px-2 py-1 bg-yellow-500/20 text-yellow-300 text-xs font-semibold rounded">
                      Popular
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-slate-400 text-lg">
              No bookmakers found matching your search.
            </div>
          </div>
        )}

        {/* Info Footer */}
        <div className="mt-8 p-4 bg-blue-900/20 border border-blue-700/50 rounded-lg">
          <div className="text-sm text-blue-300">
            <strong>Note:</strong> You need at least 2 bookmakers enabled to see odds comparisons.
            Changes are saved automatically and will take effect immediately on all pages.
          </div>
        </div>
      </div>
    </div>
  );
}
