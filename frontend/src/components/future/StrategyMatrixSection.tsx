import React, { useState } from 'react';
import { STRATEGY_ENHANCEMENTS, StrategyEnhancement } from '../../data/futureFeatures';
import { StrategyCard } from './StrategyCard';

type FilterType = 'all' | 'situational' | 'live' | 'market';
type StatusFilter = 'all' | 'live' | 'beta' | 'q1_2025' | 'q2_2025';

export const StrategyMatrixSection: React.FC = () => {
  const [categoryFilter, setCategoryFilter] = useState<FilterType>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');

  const filteredStrategies = STRATEGY_ENHANCEMENTS.filter(strategy => {
    const matchesCategory = categoryFilter === 'all' || strategy.category === categoryFilter;
    const matchesStatus = statusFilter === 'all' || strategy.status === statusFilter;
    return matchesCategory && matchesStatus;
  });

  const getCategoryCount = (category: FilterType) => {
    if (category === 'all') return STRATEGY_ENHANCEMENTS.length;
    return STRATEGY_ENHANCEMENTS.filter(s => s.category === category).length;
  };

  const getStatusCount = (status: StatusFilter) => {
    if (status === 'all') return STRATEGY_ENHANCEMENTS.length;
    return STRATEGY_ENHANCEMENTS.filter(s => s.status === status).length;
  };

  return (
    <section className="py-20 px-4 bg-slate-900">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            25 Betting Strategies
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-green-400">
              Enhanced by Machine Learning
            </span>
          </h2>
          <p className="text-lg text-slate-400 max-w-3xl mx-auto">
            Every strategy gets supercharged with ML models, rolling stats, fatigue tracking,
            and dozens of new features. See the transformation.
          </p>
        </div>

        {/* Filters */}
        <div className="mb-8 space-y-4">
          {/* Category Filter */}
          <div>
            <div className="text-sm text-slate-400 mb-2">FILTER BY CATEGORY</div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setCategoryFilter('all')}
                className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                  categoryFilter === 'all'
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                All Strategies ({getCategoryCount('all')})
              </button>
              <button
                onClick={() => setCategoryFilter('situational')}
                className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                  categoryFilter === 'situational'
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                Situational ({getCategoryCount('situational')})
              </button>
              <button
                onClick={() => setCategoryFilter('live')}
                className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                  categoryFilter === 'live'
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                Live Betting ({getCategoryCount('live')})
              </button>
              <button
                onClick={() => setCategoryFilter('market')}
                className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                  categoryFilter === 'market'
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                Market Inefficiency ({getCategoryCount('market')})
              </button>
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <div className="text-sm text-slate-400 mb-2">FILTER BY STATUS</div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setStatusFilter('all')}
                className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                  statusFilter === 'all'
                    ? 'bg-green-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                All ({getStatusCount('all')})
              </button>
              <button
                onClick={() => setStatusFilter('live')}
                className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                  statusFilter === 'live'
                    ? 'bg-green-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                Live Now ({getStatusCount('live')})
              </button>
              <button
                onClick={() => setStatusFilter('beta')}
                className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                  statusFilter === 'beta'
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                Beta ({getStatusCount('beta')})
              </button>
              <button
                onClick={() => setStatusFilter('q1_2025')}
                className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                  statusFilter === 'q1_2025'
                    ? 'bg-purple-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                Q1 2025 ({getStatusCount('q1_2025')})
              </button>
              <button
                onClick={() => setStatusFilter('q2_2025')}
                className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                  statusFilter === 'q2_2025'
                    ? 'bg-orange-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                Q2 2025 ({getStatusCount('q2_2025')})
              </button>
            </div>
          </div>
        </div>

        {/* Results Count */}
        <div className="mb-6 text-slate-400">
          Showing <span className="text-white font-semibold">{filteredStrategies.length}</span> strategies
        </div>

        {/* Strategy Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredStrategies.map(strategy => (
            <StrategyCard key={strategy.id} strategy={strategy} />
          ))}
        </div>

        {/* Summary Stats */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-gradient-to-br from-green-900/30 to-slate-900 rounded-xl p-6 border border-green-500/30 text-center">
            <div className="text-3xl font-bold text-green-400 mb-2">
              {STRATEGY_ENHANCEMENTS.filter(s => s.status === 'live').length}
            </div>
            <div className="text-sm text-slate-400">Live Strategies</div>
          </div>

          <div className="bg-gradient-to-br from-blue-900/30 to-slate-900 rounded-xl p-6 border border-blue-500/30 text-center">
            <div className="text-3xl font-bold text-blue-400 mb-2">
              {STRATEGY_ENHANCEMENTS.filter(s => s.status === 'beta').length}
            </div>
            <div className="text-sm text-slate-400">In Beta Testing</div>
          </div>

          <div className="bg-gradient-to-br from-purple-900/30 to-slate-900 rounded-xl p-6 border border-purple-500/30 text-center">
            <div className="text-3xl font-bold text-purple-400 mb-2">
              {STRATEGY_ENHANCEMENTS.filter(s => s.status === 'q1_2025').length}
            </div>
            <div className="text-sm text-slate-400">Q1 2025 Launch</div>
          </div>

          <div className="bg-gradient-to-br from-orange-900/30 to-slate-900 rounded-xl p-6 border border-orange-500/30 text-center">
            <div className="text-3xl font-bold text-orange-400 mb-2">
              {STRATEGY_ENHANCEMENTS.filter(s => s.status === 'q2_2025').length}
            </div>
            <div className="text-sm text-slate-400">Q2 2025 Launch</div>
          </div>
        </div>
      </div>
    </section>
  );
};
