import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getApiUrl } from '../config';
import { logger } from '../utils/logger';

export interface BetLeg {
  sport: string | null;
  game: string | null;
  pick: string | null;
  odds: number | null;
  game_time: string | null;
  result: string | null; // 'won' | 'lost' | 'push' | null
}

export interface UserBet {
  id: number;
  book: string | null;
  bet_type: string;
  legs: BetLeg[];
  stake: number | null;
  to_win: number | null;
  combined_odds: number | null;
  status: string; // 'pending' | 'won' | 'lost' | 'push' | 'void'
  game_date: string | null;
  created_at: string | null;
  graded_at: string | null;
}

function buildHeaders(token: string | null): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}

export function useBetTracker(token: string | null) {
  const queryClient = useQueryClient();
  const [importError, setImportError] = useState<string | null>(null);
  const [lastImported, setLastImported] = useState<string | null>(null);

  const {
    data: bets = [],
    isLoading: loadingBets,
    error: listError,
    refetch: refetchBets,
  } = useQuery({
    queryKey: ['user-bets', token],
    queryFn: async (): Promise<UserBet[]> => {
      const resp = await fetch(getApiUrl('v1/bets/'), {
        headers: buildHeaders(token),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json() as { bets: UserBet[]; count: number };
      return data.bets;
    },
    enabled: !!token,
    staleTime: 60_000,
    refetchInterval: 5 * 60_000, // refresh every 5 min (picks up auto-grades)
  });

  const importMutation = useMutation({
    mutationFn: async (rawSlip: string): Promise<string> => {
      const resp = await fetch(getApiUrl('v1/bets/import'), {
        method: 'POST',
        headers: buildHeaders(token),
        body: JSON.stringify({ raw_slip: rawSlip }),
      });
      const data = await resp.json() as { message?: string; detail?: string };
      if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`);
      return data.message ?? 'Bet saved.';
    },
    onSuccess: (message) => {
      setImportError(null);
      setLastImported(message);
      queryClient.invalidateQueries({ queryKey: ['user-bets', token] });
    },
    onError: (err: Error) => {
      logger.error('importSlip error:', err);
      setImportError(err.message);
    },
  });

  const importSlip = useCallback((rawSlip: string) => {
    setLastImported(null);
    setImportError(null);
    importMutation.mutate(rawSlip);
  }, [importMutation]);

  const gradeMutation = useMutation({
    mutationFn: async (): Promise<{ graded: number; skipped: number }> => {
      const resp = await fetch(getApiUrl('v1/bets/grade'), {
        method: 'POST',
        headers: buildHeaders(token),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return resp.json() as Promise<{ graded: number; skipped: number }>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-bets', token] });
    },
    onError: (err: Error) => {
      logger.error('refreshGrades error:', err);
    },
  });

  const refreshGrades = useCallback(() => {
    gradeMutation.mutate();
  }, [gradeMutation]);

  const clearConfirmation = useCallback(() => {
    setLastImported(null);
    setImportError(null);
  }, []);

  return {
    bets,
    loadingBets,
    listError: listError ? 'Could not load bets.' : null,
    importSlip,
    importing: importMutation.isPending,
    importError,
    lastImported,
    clearConfirmation,
    refetchBets,
    refreshGrades,
    refreshing: gradeMutation.isPending,
    gradeResult: gradeMutation.data ?? null,
  };
}
