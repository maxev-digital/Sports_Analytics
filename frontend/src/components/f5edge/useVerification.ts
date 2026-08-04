/**
 * Verification data hook.
 * Polls /verify/status on mount; re-polls every 8s while a run is in flight.
 * Uses useRef for the interval ID — no stale closure on state values.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import type { VerificationStatus } from './VerificationTypes';
import { VERIFICATION_API_BASE } from './VerificationTypes';

export function useVerification() {
  const [status, setStatus] = useState<VerificationStatus | null>(null);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const r = await fetch(`${VERIFICATION_API_BASE}/verify/status`);
      if (!r.ok) return;
      const d: VerificationStatus = await r.json();
      setStatus(d);
      if (d.verifications.signals && d.verifications.ratings) {
        setRunning(false);
      }
    } catch { /* network errors are silent — stale data stays visible */ }
  }, []);

  // Initial load
  useEffect(() => {
    fetchStatus().finally(() => setLoading(false));
  }, [fetchStatus]);

  // Polling — ref-based interval avoids stale closure on running state
  useEffect(() => {
    if (running) {
      intervalRef.current = setInterval(fetchStatus, 8_000);
      return () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
      };
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, [running, fetchStatus]);

  const triggerRun = useCallback(async () => {
    setRunning(true);
    try {
      await fetch(`${VERIFICATION_API_BASE}/verify/run`, { method: 'POST' });
      setTimeout(fetchStatus, 3_000);
    } catch {
      setRunning(false);
    }
  }, [fetchStatus]);

  return { status, running, loading, triggerRun };
}
