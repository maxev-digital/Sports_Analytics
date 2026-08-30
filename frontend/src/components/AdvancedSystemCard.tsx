import React from 'react';
import { AdvancedSystem } from '../types';
import { SystemStatusBadge } from './SystemStatusBadge';

interface AdvancedSystemCardProps {
  system: AdvancedSystem;
}

export const AdvancedSystemCard: React.FC<AdvancedSystemCardProps> = ({ system }) => {
  const difficultyColors = {
    EASY: 'bg-green-600 text-white',
    MEDIUM: 'bg-yellow-600 text-white',
    HARD: 'bg-red-600 text-white'
  };

  const formatSportName = (sportKey: string): string => {
    if (sportKey === 'multi-sport') return 'All Sports';
    const sportMap: { [key: string]: string } = {
      'basketball_nba': 'NBA',
      'basketball_ncaab': 'NCAAB',
      'icehockey_nhl': 'NHL',
      'americanfootball_nfl': 'NFL',
      'americanfootball_ncaaf': 'NCAAF',
      'baseball_mlb': 'MLB'
    };
    return sportMap[sportKey] || sportKey;
  };

  return (
    <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-slate-800 border-2 border-slate-700 rounded-lg p-4 hover:border-blue-500 transition-all">
      {/* Header: Status Badge + Name */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <h3 className="text-lg font-bold text-white flex-1">{system.name}</h3>
        <SystemStatusBadge status={system.status} />
      </div>

      {/* Description */}
      <p className="text-sm text-slate-300 mb-4 leading-relaxed">
        {system.description}
      </p>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {/* Performance Metrics (only for live/proven/active) */}
        {system.performance && (system.status === 'live' || system.status === 'proven' || system.status === 'active') && (
          <>
            {system.performance.winRate && (
              <div className="bg-slate-700 rounded px-3 py-2">
                <div className="text-xs text-slate-400">Win Rate</div>
                <div className="text-lg font-bold text-green-400">{system.performance.winRate}%</div>
              </div>
            )}
            {system.performance.roi && (
              <div className="bg-slate-700 rounded px-3 py-2">
                <div className="text-xs text-slate-400">ROI</div>
                <div className="text-lg font-bold text-green-400">+{system.performance.roi}%</div>
              </div>
            )}
            {system.performance.games && (
              <div className="bg-slate-700 rounded px-3 py-2">
                <div className="text-xs text-slate-400">Games</div>
                <div className="text-lg font-bold text-blue-400">{system.performance.games.toLocaleString()}</div>
              </div>
            )}
          </>
        )}

        {/* EV Range */}
        <div className="bg-slate-700 rounded px-3 py-2">
          <div className="text-xs text-slate-400">EV Range</div>
          <div className="text-lg font-bold text-purple-400">
            +{system.evRange.min}% to +{system.evRange.max}%
          </div>
        </div>

        {/* Difficulty */}
        <div className="bg-slate-700 rounded px-3 py-2">
          <div className="text-xs text-slate-400">Difficulty</div>
          <div className={`inline-block px-2 py-0.5 rounded text-xs font-bold mt-1 ${difficultyColors[system.difficulty]}`}>
            {system.difficulty}
          </div>
        </div>
      </div>

      {/* Sports Tags */}
      <div className="flex flex-wrap gap-2 mb-4">
        <span className="text-xs text-slate-400">Sports:</span>
        {system.sports.map((sport) => (
          <span
            key={sport}
            className="inline-block px-2 py-1 bg-blue-600 text-white rounded text-xs font-semibold"
          >
            {formatSportName(sport)}
          </span>
        ))}
      </div>

      {/* Action Button */}
      <div className="flex gap-2">
        {(system.status === 'live' || system.status === 'proven' || system.status === 'active') ? (
          <button className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded font-semibold text-sm transition-colors">
            Details
          </button>
        ) : (
          <button
            className="flex-1 px-3 py-2 bg-gray-600 text-gray-400 rounded font-semibold text-sm cursor-not-allowed"
            disabled
          >
            Coming Soon
          </button>
        )}
      </div>
    </div>
  );
};
