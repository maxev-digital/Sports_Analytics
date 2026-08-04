/**
 * F5 Edge Engine — Data fetching hook.
 * Pulls live data from the F5 API endpoints.
 */
import { useState, useEffect, useCallback } from 'react';
import type { F5GameWithPlays, SignalStats, VenueEdge } from './types';

const API_BASE = import.meta.env.DEV
  ? 'http://localhost:8888/api/f5'
  : '/api/f5';

interface TodayData {
  date: string;
  games_scanned: number;
  qualifying_games: number;
  total_plays: number;
  total_risk: number;
  credits_remaining: string;
  results: F5GameWithPlays[];
  scanned_at: string;
}

interface PlData {
  daily: Record<string, { pl: number; bets: number; wins: number }>;
  running: { total_pl: number; total_bets: number; total_wins: number; days: number };
}

export function useF5Today() {
  const [data, setData] = useState<TodayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (force = false) => {
    setLoading(true);
    setError(null);
    try {
      const url = force ? `${API_BASE}/today?force=true` : `${API_BASE}/today`;
      const r = await fetch(url);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setData(await r.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return { data, loading, error, refresh };
}

export function useF5Signals() {
  const [signals, setSignals] = useState<SignalStats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/signals`)
      .then(r => r.json())
      .then(d => setSignals(d.signals ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return { signals, loading };
}

export function useF5Venues() {
  const [venues, setVenues] = useState<VenueEdge[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/venues`)
      .then(r => r.json())
      .then(d => setVenues(d.venues ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return { venues, loading };
}

export function useF5Pl() {
  const [data, setData] = useState<PlData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/pl`)
      .then(r => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return { data, loading };
}
