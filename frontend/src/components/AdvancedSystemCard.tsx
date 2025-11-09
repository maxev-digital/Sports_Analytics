import React, { useState, useEffect } from 'react';
import { AdvancedSystem } from '../types';
import { SystemStatusBadge } from './SystemStatusBadge';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from './Toast';
import { toggleSystemAlerts, getSystemPreference } from '../api/alertPreferences';

interface AdvancedSystemCardProps {
  system: AdvancedSystem;
}

export const AdvancedSystemCard: React.FC<AdvancedSystemCardProps> = ({ system }) => {
  const { username } = useAuth();
  const { showToast } = useToast();
  const [isEnabled, setIsEnabled] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
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

  // Load alert status on mount
  useEffect(() => {
    const loadAlertStatus = async () => {
      if (!username) return;

      try {
        const prefs = await getSystemPreference(username, system.id);
        if (prefs) {
          setIsEnabled(prefs.alerts_enabled);
        }
      } catch (error) {
        console.error('Failed to load alert status:', error);
      }
    };

    loadAlertStatus();
  }, [username, system.id]);

  // Handle toggle alerts
  const handleToggleAlerts = async () => {
    if (!username) {
      showToast('Please log in to enable alerts', 'warning');
      return;
    }

    setIsLoading(true);
    try {
      const response = await toggleSystemAlerts(username, system.id);
      setIsEnabled(response.alerts_enabled);

      const action = response.alerts_enabled ? 'enabled' : 'disabled';
      showToast(`Alerts ${action} for ${system.name}`, 'success');
    } catch (error) {
      console.error('Failed to toggle alerts:', error);
      showToast('Failed to update alert preferences', 'error');
    } finally {
      setIsLoading(false);
    }
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
            {system.performance.alerts && (
              <div className="bg-slate-700 rounded px-3 py-2">
                <div className="text-xs text-slate-400">Alerts</div>
                <div className="text-lg font-bold text-blue-400">{system.performance.alerts}</div>
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

      {/* Action Buttons */}
      <div className="flex gap-2">
        {(system.status === 'live' || system.status === 'proven' || system.status === 'active') ? (
          <>
            <button
              onClick={handleToggleAlerts}
              disabled={isLoading}
              className={`flex-1 px-3 py-2 rounded font-semibold text-sm transition-all ${
                isEnabled
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {isLoading ? 'Loading...' : isEnabled ? '✓ Alerts Enabled' : 'Enable Alerts'}
            </button>
            <button className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded font-semibold text-sm transition-colors">
              Details
            </button>
          </>
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
