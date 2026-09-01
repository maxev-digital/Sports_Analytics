/**
 * Survivor Helper — shared algorithms and types.
 * Used by SurvivorSimulator, SurvivorPathBuilder, SurvivorMultiEntry.
 */

// ── Named constants ────────────────────────────────────────────────────────────
/** Beam-search beam width. K=300 reliably finds the globally-optimal path. */
export const BEAM_WIDTH = 300;
/** Diversity penalty multiplier applied when a pick overlaps prior entries. */
export const DIVERSITY_PENALTY_FACTOR = 0.25;
/** Floor for log-probability scoring to avoid log(0) over 18 weeks. */
export const LOG_SCORE_FLOOR = 1e-9;

// ── Domain types ───────────────────────────────────────────────────────────────
export interface SurvivorGame {
  home: string;
  away: string;
  home_wp: number;
  away_wp: number;
  home_label: string;
  away_label: string;
}

export interface SurvivorPick {
  week: number;
  team: string;
  wp: number;
  label: string;
  opp: string;
  home: boolean;
}

/**
 * Base path shape consumed by the simulator and comparison table.
 * Structurally compatible with OptimalPath in Survivor.tsx.
 */
export interface AlgoPath {
  id: string;
  name: string;
  color: string;
  picks: Record<number, SurvivorPick>;
}

/** User-built path with optional holiday picks. Extends AlgoPath. */
export interface CustomPath extends AlgoPath {
  createdAt: number;
  thkPick?: SurvivorPick;
  xmasPick?: SurvivorPick;
}

// ── Worker message types ────────────────────────────────────────────────────────
export interface SimResult {
  survivalByWeek: number[];
  expectedElim: number;
}

export type WorkerMsg =
  | {
      type: 'monteCarlo';
      paths: { id: string; picks: Record<number, { wp: number }> }[];
      iters: number;
    }
  | {
      type: 'portfolio';
      entries: Record<number, SurvivorPick>[];
      weeks: Record<number, SurvivorGame[]>;
      iters: number;
    };

export type WorkerResult =
  | { type: 'monteCarlo'; results: Record<string, SimResult> }
  | { type: 'portfolio'; atLeastOne: number[]; perEntry: number[][] };

// ── Color palette ──────────────────────────────────────────────────────────────
export const CUSTOM_PATH_COLORS = [
  'oklch(70% .18 290)',  // purple
  'oklch(72% .19 50)',   // orange
  'oklch(65% .22 330)',  // magenta
  'oklch(68% .20 200)',  // teal
  'oklch(65% .22 20)',   // coral
];

// ── Algorithms ─────────────────────────────────────────────────────────────────
/**
 * Beam search — near-optimal survivor season path.
 * K=BEAM_WIDTH reliably finds the globally optimal path across all NFL schedules.
 * Log-probability scoring avoids floating-point underflow over 18 weeks.
 *
 * @param diversityPenalty  Per-week set of teams already claimed by prior entries.
 *                          Penalizes picks that overlap with existing entries.
 */
export function beamSearch(
  weeks: Record<number, SurvivorGame[]>,
  k = BEAM_WIDTH,
  diversityPenalty?: Record<number, Set<string>>,
): Record<number, SurvivorPick> {
  const weekNums = Object.keys(weeks).map(Number).sort((a, b) => a - b);

  type State = {
    used: string[];
    picks: Record<number, SurvivorPick>;
    logScore: number;
  };

  let beam: State[] = [{ used: [], picks: {}, logScore: 0 }];

  for (const wk of weekNums) {
    const next: State[] = [];

    for (const state of beam) {
      const usedSet = new Set(state.used);
      let expanded = false;

      for (const g of weeks[wk] ?? []) {
        const sides: [string, number, string, boolean, string][] = [
          [g.home, g.home_wp, g.away, true,  g.home_label],
          [g.away, g.away_wp, g.home, false, g.away_label],
        ];
        for (const [team, wp, opp, home, label] of sides) {
          if (usedSet.has(team)) continue;
          expanded = true;
          const penalty = diversityPenalty?.[wk]?.has(team)
            ? DIVERSITY_PENALTY_FACTOR
            : 1.0;
          next.push({
            used: [...state.used, team],
            picks: {
              ...state.picks,
              [wk]: { week: wk, team, wp, opp: opp as string, home: home as boolean, label: label as string },
            },
            logScore: state.logScore + Math.log(Math.max(wp * penalty, LOG_SCORE_FLOOR)),
          });
        }
      }

      if (!expanded) next.push(state);
    }

    next.sort((a, b) => b.logScore - a.logScore);
    beam = next.slice(0, k);
  }

  return beam[0]?.picks ?? {};
}

/**
 * Monte Carlo survivor simulation.
 * Each iteration steps through every week; the pick wins with probability wp.
 * Returns per-week survival probability (index 0 = P(survived wk1)).
 */
export function monteCarlo(
  picks: Record<number, { wp: number }>,
  iters = 50_000,
): SimResult {
  const wks = Object.keys(picks).map(Number).sort((a, b) => a - b);
  const maxWk = wks[wks.length - 1] ?? 18;
  const elimAt = new Array(maxWk + 2).fill(0);

  for (let i = 0; i < iters; i++) {
    let elim = maxWk + 1;
    for (const wk of wks) {
      if (Math.random() > picks[wk].wp) { elim = wk; break; }
    }
    elimAt[elim]++;
  }

  let alive = iters;
  const survivalByWeek: number[] = [];
  for (let wk = 1; wk <= maxWk; wk++) {
    alive -= elimAt[wk] ?? 0;
    survivalByWeek.push(alive / iters);
  }

  let expElim = 0;
  for (let wk = 1; wk <= maxWk + 1; wk++) {
    expElim += wk * ((elimAt[wk] ?? 0) / iters);
  }

  return { survivalByWeek, expectedElim: expElim };
}

/**
 * Portfolio Monte Carlo — N entries simulated simultaneously with correlated outcomes.
 * When two entries pick teams from the same game only one side can win.
 * This properly captures correlation risk that independent simulations miss.
 */
export function portfolioMonteCarlo(
  entries: Record<number, SurvivorPick>[],
  weeks: Record<number, SurvivorGame[]>,
  iters = 30_000,
): { atLeastOne: number[]; perEntry: number[][] } {
  const weekNums = Object.keys(weeks).map(Number).sort((a, b) => a - b);
  const n = entries.length;
  const atLeastOne = new Array(weekNums.length).fill(0);
  const perEntry: number[][] = Array.from({ length: n }, () =>
    new Array(weekNums.length).fill(0),
  );

  for (let i = 0; i < iters; i++) {
    const wins = new Map<string, boolean>();
    for (const wk of weekNums) {
      for (const g of weeks[wk] ?? []) {
        const homeWins = Math.random() < g.home_wp;
        wins.set(`${wk}:${g.home}`, homeWins);
        wins.set(`${wk}:${g.away}`, !homeWins);
      }
    }

    const alive = Array.from({ length: n }, () => true);
    for (let wi = 0; wi < weekNums.length; wi++) {
      const wk = weekNums[wi];
      for (let e = 0; e < n; e++) {
        if (!alive[e]) continue;
        const pick = entries[e][wk];
        if (pick && wins.get(`${wk}:${pick.team}`) === false) alive[e] = false;
        if (alive[e]) perEntry[e][wi]++;
      }
      if (alive.some(Boolean)) atLeastOne[wi]++;
    }
  }

  return { atLeastOne, perEntry };
}
