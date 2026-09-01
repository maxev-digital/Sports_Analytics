/**
 * SurvivorMultiEntry — "MULTI-ENTRY" tab for the Survivor Helper.
 * Generates N diversified entries via beam search and runs correlated portfolio simulation.
 * Monte Carlo runs off the main thread via useSurvivorWorker.
 */
import { useState, useMemo } from 'react';
import {
  beamSearch,
  CUSTOM_PATH_COLORS,
  type SurvivorGame,
  type SurvivorPick,
} from './survivorAlgo';
import { logo, COLORS, withAlpha } from './survivorUtils';
import { useSurvivorWorker } from './useSurvivorWorker';

const { EMERALD, RED, YELLOW: AMBER } = COLORS;
const PORTFOLIO_ITERS = 30_000;
const SURVIVAL_CHECKPOINTS = [1, 4, 8, 10, 12, 14, 16, 18];

interface Props {
  weeks: Record<number, SurvivorGame[]>;
}

export function SurvivorMultiEntry({ weeks }: Props) {
  const [nEntries, setNEntries]       = useState(3);
  const [entries, setEntries]         = useState<Record<number, SurvivorPick>[]>([]);
  const [portfolioResults, setPR]     = useState<{ atLeastOne: number[]; perEntry: number[][] } | null>(null);
  const [simRunning, setSimRunning]   = useState(false);
  const dispatch = useSurvivorWorker();

  const weekNums = useMemo(
    () => Object.keys(weeks).map(Number).sort((a, b) => a - b),
    [weeks],
  );

  function generateEntries() {
    const result: Record<number, SurvivorPick>[] = [];
    for (let i = 0; i < nEntries; i++) {
      const penalty: Record<number, Set<string>> = {};
      for (const prev of result) {
        for (const [wkStr, pick] of Object.entries(prev)) {
          const wk = Number(wkStr);
          if (!penalty[wk]) penalty[wk] = new Set();
          penalty[wk].add(pick.team);
        }
      }
      result.push(beamSearch(weeks, 300, penalty));
    }
    setEntries(result);
    setPR(null);
  }

  function runSim() {
    if (!entries.length) return;
    setSimRunning(true);
    dispatch(
      { type: 'portfolio', entries, weeks, iters: PORTFOLIO_ITERS },
      data => {
        if (data.type !== 'portfolio') return;
        setPR({ atLeastOne: data.atLeastOne, perEntry: data.perEntry });
        setSimRunning(false);
      },
    );
  }

  const correlationMap = useMemo(() => {
    const map: Record<string, boolean> = {};
    for (const wk of weekNums) {
      const teamGame: Record<string, string> = {};
      for (const g of weeks[wk] ?? []) {
        const key = [g.home, g.away].sort().join(':');
        teamGame[g.home] = key;
        teamGame[g.away] = key;
      }
      const gameGroups: Record<string, number[]> = {};
      for (let ei = 0; ei < entries.length; ei++) {
        const pick = entries[ei][wk];
        if (!pick) continue;
        const gk = teamGame[pick.team];
        if (!gk) continue;
        if (!gameGroups[gk]) gameGroups[gk] = [];
        gameGroups[gk].push(ei);
      }
      for (const group of Object.values(gameGroups)) {
        if (group.length > 1) {
          for (const ei of group) map[`${ei}:${wk}`] = true;
        }
      }
    }
    return map;
  }, [entries, weekNums, weeks]);

  return (
    <div className="flex flex-col gap-6">

      {/* ── Controls ─────────────────────────────────────────────────────── */}
      <div className="bg-panel border border-ev-border rounded-xl py-5 px-6 flex items-center gap-6 flex-wrap">
        <div>
          <div className="text-[0.6rem] text-muted tracking-[0.08em] mb-2">NUMBER OF ENTRIES</div>
          <div className="flex gap-1.5">
            {[2, 3, 4, 5].map(n => (
              <button
                key={n}
                onClick={() => setNEntries(n)}
                className="py-1.5 px-[14px] rounded-[7px] cursor-pointer text-[0.8rem]"
                style={{
                  border: `1px solid ${nEntries === n ? EMERALD : 'var(--c-border)'}`,
                  background: nEntries === n ? withAlpha(EMERALD, 0.09) : 'transparent',
                  color: nEntries === n ? EMERALD : 'var(--c-fg)',
                  fontWeight: nEntries === n ? 700 : 400,
                }}
              >
                {n}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <button
            onClick={generateEntries}
            className="py-[9px] px-5 rounded-lg cursor-pointer text-[0.8rem] font-bold"
            style={{
              background: withAlpha(EMERALD, 0.09),
              border: `1px solid ${EMERALD}`,
              color: EMERALD,
            }}
          >
            Generate {nEntries} Diversified Entries
          </button>
          <div className="text-[0.6rem] text-muted">
            Beam search K=300 with diversity penalty — each entry picks different teams
          </div>
        </div>

        {entries.length > 0 && (
          <button
            onClick={runSim}
            disabled={simRunning}
            className="py-[9px] px-5 rounded-lg text-[0.8rem] font-bold"
            style={{
              cursor: simRunning ? 'default' : 'pointer',
              background: simRunning ? 'transparent' : withAlpha(AMBER, 0.09),
              border: `1px solid ${AMBER}`,
              color: AMBER,
            }}
          >
            {simRunning ? 'Simulating...' : `Run Portfolio Sim (${(PORTFOLIO_ITERS / 1000).toFixed(0)}K)`}
          </button>
        )}

        {entries.length > 0 && (
          <div className="ml-auto text-right">
            <div className="text-[0.6rem] text-muted">CORRELATED RISK</div>
            <div className="flex gap-1.5 mt-1 items-center">
              <div
                className="w-[10px] h-[10px] rounded-[2px]"
                style={{ background: withAlpha(AMBER, 0.38), border: `1px solid ${AMBER}` }}
              />
              <span className="text-[0.7rem] text-muted">= Same game, only 1 can win</span>
            </div>
          </div>
        )}
      </div>

      {/* ── Entry grid table ─────────────────────────────────────────────── */}
      {entries.length > 0 && (
        <div className="bg-panel border border-ev-border rounded-xl overflow-hidden">
          <div className="py-[14px] px-5 border-b border-ev-border">
            <div className="font-bold font-[Nunito] text-[1rem] text-fg">{nEntries}-Entry Portfolio</div>
            <div className="text-[0.68rem] text-muted mt-0.5">
              Week-by-week picks. Amber = entries picking from the same game (correlated risk — only one can win).
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[0.7rem]">
              <thead>
                <tr>
                  <th className="py-2 px-[14px] text-left font-bold text-muted text-[0.6rem] tracking-[0.06em] border-b border-ev-border whitespace-nowrap sticky left-0 bg-panel z-[2]">
                    ENTRY
                  </th>
                  {weekNums.map(wk => (
                    <th key={wk} className="py-2 px-1.5 text-center font-bold text-muted text-[0.6rem] tracking-[0.06em] border-b border-ev-border whitespace-nowrap min-w-[64px]">
                      WK{wk}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {entries.map((entry, ei) => {
                  const color = CUSTOM_PATH_COLORS[ei % CUSTOM_PATH_COLORS.length];
                  const survProb = weekNums.reduce((acc, wk) => {
                    const pick = entry[wk];
                    return pick ? acc * pick.wp : acc;
                  }, 1);
                  return (
                    <tr key={ei} className="border-b border-ev-border">
                      <td className="py-[10px] px-[14px] font-bold whitespace-nowrap sticky left-0 bg-panel z-[1] border-r border-ev-border">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full shrink-0" style={{ background: color }} />
                          <div>
                            <div className="text-[0.75rem]" style={{ color }}>Entry {ei + 1}</div>
                            <div className="text-muted text-[0.6rem] font-normal">
                              {(survProb * 100).toFixed(1)}% survive
                            </div>
                          </div>
                        </div>
                      </td>
                      {weekNums.map(wk => {
                        const pick = entry[wk];
                        const isCorrelated = correlationMap[`${ei}:${wk}`];
                        return (
                          <td
                            key={wk}
                            className="py-1.5 px-1 text-center"
                            style={{
                              background: isCorrelated ? withAlpha(AMBER, 0.09) : 'transparent',
                              border: isCorrelated ? `1px solid ${withAlpha(AMBER, 0.25)}` : '1px solid transparent',
                            }}
                          >
                            {pick ? (
                              <div className="flex flex-col items-center gap-0.5">
                                <img
                                  src={logo(pick.team)} alt={pick.team}
                                  className="w-[22px] h-[22px]"
                                  onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                                />
                                <div className="text-[0.6rem] font-bold text-fg">{pick.team}</div>
                                <div className="text-[0.58rem] text-muted">{Math.round(pick.wp * 100)}%</div>
                              </div>
                            ) : (
                              <div className="text-[0.55rem] text-muted">BYE</div>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Portfolio simulation results ──────────────────────────────────── */}
      {portfolioResults && (
        <div className="grid grid-cols-2 gap-5">

          <div className="bg-panel border border-ev-border rounded-xl py-5 px-6">
            <div className="font-bold font-[Nunito] text-[0.95rem] text-fg mb-[14px]">
              P(At Least 1 Entry Survives)
            </div>
            <table className="w-full text-[0.72rem] border-collapse">
              <thead>
                <tr>
                  <th className="text-left text-muted py-1 font-semibold text-[0.6rem]">WEEK</th>
                  <th className="text-right text-muted py-1 font-semibold text-[0.6rem]">PROBABILITY</th>
                  <th className="w-[80px]" />
                </tr>
              </thead>
              <tbody>
                {SURVIVAL_CHECKPOINTS.map(wk => {
                  const wi = weekNums.indexOf(wk);
                  if (wi < 0) return null;
                  const prob = portfolioResults.atLeastOne[wi] / PORTFOLIO_ITERS;
                  const col  = prob >= 0.7 ? EMERALD : prob >= 0.4 ? AMBER : RED;
                  return (
                    <tr key={wk} className="border-b border-ev-border">
                      <td className="py-[7px] text-muted">Week {wk}</td>
                      <td className="py-[7px] text-right font-bold" style={{ color: col }}>
                        {(prob * 100).toFixed(1)}%
                      </td>
                      <td className="py-[7px] px-2">
                        <div className="h-1 bg-track rounded-sm overflow-hidden">
                          <div className="h-full rounded-sm" style={{ width: `${prob * 100}%`, background: col }} />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="bg-panel border border-ev-border rounded-xl py-5 px-6">
            <div className="font-bold font-[Nunito] text-[0.95rem] text-fg mb-[14px]">Per-Entry Survival</div>
            <table className="w-full text-[0.72rem] border-collapse">
              <thead>
                <tr>
                  <th className="text-left text-muted py-1 font-semibold text-[0.6rem]">ENTRY</th>
                  {SURVIVAL_CHECKPOINTS.map(wk => (
                    <th key={wk} className="text-center text-muted py-1 px-1 font-semibold text-[0.6rem]">W{wk}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {portfolioResults.perEntry.map((curve, ei) => {
                  const color = CUSTOM_PATH_COLORS[ei % CUSTOM_PATH_COLORS.length];
                  return (
                    <tr key={ei} className="border-b border-ev-border">
                      <td className="py-[7px]">
                        <div className="flex items-center gap-1.5">
                          <div className="w-1.5 h-1.5 rounded-full" style={{ background: color }} />
                          <span className="font-bold" style={{ color }}>E{ei + 1}</span>
                        </div>
                      </td>
                      {SURVIVAL_CHECKPOINTS.map(wk => {
                        const wi   = weekNums.indexOf(wk);
                        const prob = wi >= 0 ? curve[wi] / PORTFOLIO_ITERS : null;
                        const col  = prob == null ? 'var(--c-muted)' : prob >= 0.7 ? EMERALD : prob >= 0.4 ? AMBER : RED;
                        return (
                          <td key={wk} className="py-[7px] px-1 text-center font-bold" style={{ color: col }}>
                            {prob != null ? `${(prob * 100).toFixed(0)}%` : '—'}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div className="mt-3 text-[0.6rem] text-muted leading-relaxed">
              Correlated simulation — game outcomes are resolved once per iteration,
              so overlapping picks properly reduce portfolio survival.
            </div>
          </div>

        </div>
      )}

      {/* ── Empty state ───────────────────────────────────────────────────── */}
      {!entries.length && (
        <div className="bg-panel border border-ev-border rounded-xl py-12 px-6 text-center">
          <div className="text-[2rem] mb-3">🎯</div>
          <div className="font-bold font-[Nunito] text-[1rem] text-fg mb-2">
            Multi-Entry Portfolio Optimizer
          </div>
          <div className="text-muted text-[0.8rem] max-w-[480px] mx-auto leading-relaxed">
            Select the number of entries and click Generate. The beam search algorithm (K=300) will
            produce maximally diversified paths — each entry uses a different team each week where possible.
            Run the portfolio sim to see correlated survival probabilities.
          </div>
        </div>
      )}

    </div>
  );
}
