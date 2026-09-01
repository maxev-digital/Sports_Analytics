/// <reference lib="webworker" />
/**
 * Survivor Worker — runs Monte Carlo simulations off the main thread.
 * Instantiated via:
 *   new Worker(new URL('./survivorWorker.ts', import.meta.url), { type: 'module' })
 */
import {
  monteCarlo,
  portfolioMonteCarlo,
  type WorkerMsg,
  type WorkerResult,
} from './survivorAlgo';

self.onmessage = (e: MessageEvent<WorkerMsg>) => {
  const msg = e.data;

  if (msg.type === 'monteCarlo') {
    const results: Record<string, { survivalByWeek: number[]; expectedElim: number }> = {};
    for (const path of msg.paths) {
      results[path.id] = monteCarlo(path.picks, msg.iters);
    }
    self.postMessage({ type: 'monteCarlo', results } satisfies WorkerResult);
    return;
  }

  const res = portfolioMonteCarlo(msg.entries, msg.weeks, msg.iters);
  self.postMessage({ type: 'portfolio', ...res } satisfies WorkerResult);
};
