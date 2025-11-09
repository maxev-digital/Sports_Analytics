import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/Toast';
import { ADVANCED_SYSTEMS } from '../data/advancedSystems';
import { SystemStatusBadge } from '../components/SystemStatusBadge';
import {
  getAlertPreferences,
  toggleSystemAlerts,
  enableSystemAlerts,
  disableSystemAlerts,
  AlertPreferencesResponse
} from '../api/alertPreferences';

export default function AlertPreferences() {
  const { username } = useAuth();
  const { showToast } = useToast();
  const [preferences, setPreferences] = useState<AlertPreferencesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [togglingSystem, setTogglingSystem] = useState<number | null>(null);
  const [filterSport, setFilterSport] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  // Load preferences on mount
  useEffect(() => {
    loadPreferences();
  }, [username]);

  const loadPreferences = async () => {
    if (!username) return;

    try {
      setLoading(true);
      const prefs = await getAlertPreferences(username);
      setPreferences(prefs);
    } catch (error) {
      console.error('Failed to load preferences:', error);
      showToast('Failed to load alert preferences', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (systemId: number, systemName: string) => {
    if (!username) return;

    setTogglingSystem(systemId);
    try {
      const response = await toggleSystemAlerts(username, systemId);

      // Update local state
      if (preferences) {
        const newPreferences = { ...preferences };
        if (response.alerts_enabled) {
          newPreferences.enabled_systems = [...preferences.enabled_systems, systemId];
        } else {
          newPreferences.enabled_systems = preferences.enabled_systems.filter(id => id !== systemId);
        }
        setPreferences(newPreferences);
      }

      const action = response.alerts_enabled ? 'enabled' : 'disabled';
      showToast(`Alerts ${action} for ${systemName}`, 'success');
    } catch (error) {
      console.error('Failed to toggle alerts:', error);
      showToast('Failed to update alert preferences', 'error');
    } finally {
      setTogglingSystem(null);
    }
  };

  const handleEnableAll = async () => {
    if (!username) return;

    setLoading(true);
    try {
      const eligibleSystems = ADVANCED_SYSTEMS.filter(
        s => s.status === 'live' || s.status === 'proven' || s.status === 'active'
      );

      for (const system of eligibleSystems) {
        if (!preferences?.enabled_systems.includes(system.id)) {
          await enableSystemAlerts(username, system.id);
        }
      }

      await loadPreferences();
      showToast(`Enabled alerts for ${eligibleSystems.length} systems`, 'success');
    } catch (error) {
      console.error('Failed to enable all:', error);
      showToast('Failed to enable all alerts', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDisableAll = async () => {
    if (!username) return;

    setLoading(true);
    try {
      for (const systemId of preferences?.enabled_systems || []) {
        await disableSystemAlerts(username, systemId);
      }

      await loadPreferences();
      showToast('Disabled all alerts', 'success');
    } catch (error) {
      console.error('Failed to disable all:', error);
      showToast('Failed to disable all alerts', 'error');
    } finally {
      setLoading(false);
    }
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

  // Filter systems
  const filteredSystems = ADVANCED_SYSTEMS.filter(system => {
    if (filterSport !== 'all' && !system.sports.includes(filterSport) && !system.sports.includes('multi-sport')) {
      return false;
    }
    if (filterStatus !== 'all' && system.status !== filterStatus) {
      return false;
    }
    return true;
  });

  const enabledCount = preferences?.enabled_systems.length || 0;
  const totalActive = ADVANCED_SYSTEMS.filter(
    s => s.status === 'live' || s.status === 'proven' || s.status === 'active'
  ).length;

  if (loading && !preferences) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-20">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
            <p className="text-white mt-4">Loading alert preferences...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Alert Preferences</h1>
          <p className="text-slate-300">
            Manage which advanced systems trigger real-time alerts
          </p>
        </div>

        {/* Stats Card */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 mb-6 shadow-xl">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-4xl font-bold text-white">{enabledCount}</div>
              <div className="text-blue-100 text-sm">Alerts Enabled</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-white">{totalActive}</div>
              <div className="text-blue-100 text-sm">Active Systems</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-white">{ADVANCED_SYSTEMS.length}</div>
              <div className="text-blue-100 text-sm">Total Systems</div>
            </div>
          </div>
        </div>

        {/* Bulk Actions */}
        <div className="bg-slate-800 border-2 border-slate-700 rounded-lg p-4 mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap gap-4">
              {/* Sport Filter */}
              <select
                value={filterSport}
                onChange={(e) => setFilterSport(e.target.value)}
                className="px-4 py-2 bg-slate-700 text-white rounded border-2 border-slate-600 focus:border-blue-500 outline-none"
              >
                <option value="all">All Sports</option>
                <option value="basketball_nba">NBA</option>
                <option value="basketball_ncaab">NCAAB</option>
                <option value="icehockey_nhl">NHL</option>
                <option value="americanfootball_nfl">NFL</option>
                <option value="americanfootball_ncaaf">NCAAF</option>
                <option value="baseball_mlb">MLB</option>
              </select>

              {/* Status Filter */}
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-4 py-2 bg-slate-700 text-white rounded border-2 border-slate-600 focus:border-blue-500 outline-none"
              >
                <option value="all">All Statuses</option>
                <option value="live">Live</option>
                <option value="proven">Proven</option>
                <option value="active">Active</option>
                <option value="pending">Pending</option>
              </select>
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleEnableAll}
                disabled={loading}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded font-semibold transition-colors disabled:opacity-50"
              >
                Enable All Active
              </button>
              <button
                onClick={handleDisableAll}
                disabled={loading || enabledCount === 0}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded font-semibold transition-colors disabled:opacity-50"
              >
                Disable All
              </button>
            </div>
          </div>
        </div>

        {/* Systems Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSystems.map((system) => {
            const isEnabled = preferences?.enabled_systems.includes(system.id) || false;
            const isActive = system.status === 'live' || system.status === 'proven' || system.status === 'active';
            const isToggling = togglingSystem === system.id;

            return (
              <div
                key={system.id}
                className={`bg-slate-800 border-2 rounded-lg p-4 transition-all ${
                  isEnabled ? 'border-green-500' : 'border-slate-700'
                } ${isActive ? 'hover:border-blue-500' : 'opacity-60'}`}
              >
                {/* Header */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <h3 className="text-lg font-bold text-white flex-1">{system.name}</h3>
                  <SystemStatusBadge status={system.status} />
                </div>

                {/* Description */}
                <p className="text-sm text-slate-300 mb-3 line-clamp-2">
                  {system.description}
                </p>

                {/* Sports Tags */}
                <div className="flex flex-wrap gap-1 mb-3">
                  {system.sports.map((sport) => (
                    <span
                      key={sport}
                      className="inline-block px-2 py-0.5 bg-blue-600 text-white rounded text-xs font-semibold"
                    >
                      {formatSportName(sport)}
                    </span>
                  ))}
                </div>

                {/* EV Range */}
                <div className="text-sm text-slate-400 mb-3">
                  EV: <span className="text-purple-400 font-bold">+{system.evRange.min}% to +{system.evRange.max}%</span>
                </div>

                {/* Toggle Button */}
                {isActive ? (
                  <button
                    onClick={() => handleToggle(system.id, system.name)}
                    disabled={isToggling}
                    className={`w-full px-3 py-2 rounded font-semibold text-sm transition-all ${
                      isEnabled
                        ? 'bg-green-600 hover:bg-green-700 text-white'
                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                    } ${isToggling ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    {isToggling ? 'Loading...' : isEnabled ? '✓ Alerts Enabled' : 'Enable Alerts'}
                  </button>
                ) : (
                  <button
                    className="w-full px-3 py-2 bg-gray-600 text-gray-400 rounded font-semibold text-sm cursor-not-allowed"
                    disabled
                  >
                    Coming Soon
                  </button>
                )}
              </div>
            );
          })}
        </div>

        {/* No Results */}
        {filteredSystems.length === 0 && (
          <div className="text-center py-12">
            <p className="text-slate-400 text-lg">No systems match your filters</p>
          </div>
        )}
      </div>
    </div>
  );
}
