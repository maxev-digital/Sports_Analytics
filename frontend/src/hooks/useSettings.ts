import { useState, useEffect } from 'react';
import { BOOKMAKERS, getAllBookmakerKeys } from '../data/bookmakers';

export interface UserSettings {
  user_id: string;
  enabled_bookmakers: string[];
  total_bankroll: number;
  unit_size: number;
  risk_level: string;
  min_arb_profit: number;
  steam_move_threshold: number;
  line_movement_threshold: number;
  alert_sound_enabled: boolean;
  highlight_pinnacle: boolean;
  dark_mode: boolean;
}

export function useSettings(userId: string = 'default') {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch settings on mount
  useEffect(() => {
    fetchSettings();
  }, [userId]);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/settings?user_id=${userId}`);

      if (!response.ok) {
        throw new Error('Failed to fetch settings');
      }

      const data = await response.json();
      setSettings(data.settings);
      setError(null);
    } catch (err) {
      console.error('Error fetching settings:', err);
      setError(err instanceof Error ? err.message : 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const updateBookmakers = async (enabledBookmakers: string[]) => {
    try {
      setSaving(true);
      const response = await fetch(`/api/settings/bookmakers?user_id=${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ enabled_bookmakers: enabledBookmakers }),
      });

      if (!response.ok) {
        throw new Error('Failed to update bookmakers');
      }

      const data = await response.json();

      // Update local state
      setSettings(prev => prev ? {
        ...prev,
        enabled_bookmakers: data.enabled_bookmakers
      } : null);

      setError(null);
      return true;
    } catch (err) {
      console.error('Error updating bookmakers:', err);
      setError(err instanceof Error ? err.message : 'Failed to save bookmakers');
      return false;
    } finally {
      setSaving(false);
    }
  };

  const toggleBookmaker = async (bookmakerKey: string) => {
    if (!settings) return false;

    const isEnabled = settings.enabled_bookmakers.includes(bookmakerKey);
    const newEnabledBookmakers = isEnabled
      ? settings.enabled_bookmakers.filter(k => k !== bookmakerKey)
      : [...settings.enabled_bookmakers, bookmakerKey];

    return await updateBookmakers(newEnabledBookmakers);
  };

  const enableAllBookmakers = async () => {
    const allKeys = getAllBookmakerKeys();
    return await updateBookmakers(allKeys);
  };

  const disableAllBookmakers = async () => {
    return await updateBookmakers([]);
  };

  const enablePopularBookmakers = async () => {
    const popularKeys = Object.values(BOOKMAKERS)
      .filter(book => book.popular)
      .map(book => book.key);
    return await updateBookmakers(popularKeys);
  };

  const resetToDefaults = async () => {
    try {
      setSaving(true);
      const response = await fetch(`/api/settings/reset?user_id=${userId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to reset settings');
      }

      const data = await response.json();
      setSettings(data.settings);
      setError(null);
      return true;
    } catch (err) {
      console.error('Error resetting settings:', err);
      setError(err instanceof Error ? err.message : 'Failed to reset settings');
      return false;
    } finally {
      setSaving(false);
    }
  };

  return {
    settings,
    loading,
    saving,
    error,
    updateBookmakers,
    toggleBookmaker,
    enableAllBookmakers,
    disableAllBookmakers,
    enablePopularBookmakers,
    resetToDefaults,
    refetch: fetchSettings,
  };
}
