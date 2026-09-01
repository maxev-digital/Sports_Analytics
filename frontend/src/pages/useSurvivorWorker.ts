/**
 * useSurvivorWorker — React hook wrapping the survivor Monte Carlo Web Worker.
 * Returns a stable `dispatch` function; the worker lifecycle is tied to the component.
 */
import { useRef, useEffect, useCallback } from 'react';
import type { WorkerMsg, WorkerResult } from './survivorAlgo';

export function useSurvivorWorker(): (msg: WorkerMsg, onDone: (data: WorkerResult) => void) => void {
  const ref = useRef<Worker | null>(null);

  useEffect(() => {
    ref.current = new Worker(
      new URL('./survivorWorker.ts', import.meta.url),
      { type: 'module' },
    );
    return () => {
      ref.current?.terminate();
      ref.current = null;
    };
  }, []);

  return useCallback((msg: WorkerMsg, onDone: (data: WorkerResult) => void) => {
    const worker = ref.current;
    if (!worker) return;
    const handler = (e: MessageEvent<WorkerResult>) => {
      worker.removeEventListener('message', handler);
      onDone(e.data);
    };
    worker.addEventListener('message', handler);
    worker.postMessage(msg);
  }, []);
}
