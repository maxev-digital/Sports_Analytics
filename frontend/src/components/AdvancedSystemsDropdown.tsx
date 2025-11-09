import React, { useState } from 'react';
import { getSystemsBySport, getActiveSystemsCount } from '../data/advancedSystems';
import { AdvancedSystemCard } from './AdvancedSystemCard';

interface AdvancedSystemsDropdownProps {
  sportKey: string;
  gameId: string;
}

export const AdvancedSystemsDropdown: React.FC<AdvancedSystemsDropdownProps> = ({
  sportKey,
  gameId
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const systems = getSystemsBySport(sportKey);
  const activeCount = getActiveSystemsCount(sportKey);

  if (systems.length === 0) {
    return null; // Don't show if no systems for this sport
  }

  return (
    <div className="px-4 pb-4">
      {/* Dropdown Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg font-bold text-sm transition-all shadow-lg hover:shadow-xl flex items-center justify-between group"
      >
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <span>Max Ev Boost Alerts</span>
          <span className="px-2 py-0.5 bg-white bg-opacity-20 rounded-full text-xs font-bold">
            {activeCount} Active
          </span>
        </div>
        <svg
          className={`w-5 h-5 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expandable Panel */}
      {isOpen && (
        <div className="mt-3 bg-slate-900 border-2 border-purple-600 rounded-lg p-4 max-h-[600px] overflow-y-auto">
          {/* Header */}
          <div className="mb-4">
            <h3 className="text-xl font-bold text-white mb-1">
              {systems.length} Systems Available
            </h3>
            <p className="text-sm text-slate-400">
              Sorted by status: Live → Proven → Active → Pending
            </p>
          </div>

          {/* Systems Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {systems.map((system) => (
              <AdvancedSystemCard key={system.id} system={system} />
            ))}
          </div>

          {/* Footer Info */}
          <div className="mt-4 pt-4 border-t border-slate-700">
            <div className="flex items-start gap-2 text-xs text-slate-400">
              <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <p>
                Systems with "LIVE" or "ACTIVE" status have been backtested and are fully operational.
                "PENDING" systems are planned for future releases.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
