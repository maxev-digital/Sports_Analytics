import { useState, useMemo } from 'react';
import {
  beamSearch,
  portfolioMonteCarlo,
  CUSTOM_PATH_COLORS,
  type SurvivorGame,
  type SurvivorPick,
} from './survivorAlgo';

// ── Theme tokens (inherited from parent via CSS vars) ─────────────────────────
const PANEL  = 'var(--c-panel)';
const BORDER = 'var(--c-border)';
const FG     = 'var(--c-fg)';
const MUTED  = 'var(--c-muted)';
const EMERALD = 'oklch(69.6% .17 162.48)';
const RED     = 'oklch(63.2% .204 25.331)';
const AMBER   = 'oklch(79.5% .184 86.047)';

function getLogo(abbr: string): string {
  const map: Record<string, string> = {
    ARI:'ari',ATL:'atl',BAL:'bal',BUF:'buf',CAR:'car',CHI:'chi',CIN:'cin',CLE:'cle',
    DAL:'dal',DEN:'den',DET:'det',GB:'gb',HOU:'hou',IND:'ind',JAX:'jax',KC:'kc',
    LAC:'lac',LAR:'lar',LV:'lv',MIA:'mia',MIN:'min',NE:'ne',NO:'no',NYG:'nyg',
    NYJ:'nyj',PHI:'phi',PIT:'pit',SEA:'sea',SF:'sf',TB:'tb',TEN:'ten',WSH:'wsh',
  };
  const slug = map[abbr] ?? abbr.toLowerCase();
  return `https://a.espncdn.com/i/teamlogos/nfl/500/${slug}.png`;
}

interface Props {
  weeks: Record<number, SurvivorGame[]>;
}

export function SurvivorMultiEntry({ weeks }: Props) {
  const [nEntries, setNEntries] = useState(3);
  const [entries, setEntries] = useState<Record<number, SurvivorPick>[]>([]);
  const [portfolioResults, setPortfolioResults] = useState<{
    atLeastOne: number[];
    perEntry: number[][];
  } | null>(null);
  const [simRunning, setSimRunning] = useState(false);

  const weekNums = useMemo(
    () => Object.keys(weeks).map(Number).sort((a, b) => a - b),
    [weeks],
  );

  // ── Generate N diversified entries via beam search ────────────────────────
  function generateEntries() {
    const result: Record<number, SurvivorPick>[] = [];
    for (let i = 0; i < nEntries; i++) {
      // Build diversity penalty from all prior entries
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
    setPortfolioResults(null);
  }

  // ── Portfolio Monte Carlo ─────────────────────────────────────────────────
  function runSim() {
    if (!entries.length) return;
    setSimRunning(true);
    setTimeout(() => {
      const res = portfolioMonteCarlo(entries, weeks, 30_000);
      setPortfolioResults(res);
      setSimRunning(false);
    }, 0);
  }

  // ── Correlation detection: flag cells where 2+ entries pick same game ──────
  const correlationMap = useMemo(() => {
    const map: Record<string, boolean> = {}; // `${entryIdx}:${wk}` → true if correlated
    for (const wk of weekNums) {
      // Map each team to its game's "game key" (sorted pair)
      const teamGame: Record<string, string> = {};
      for (const g of weeks[wk] ?? []) {
        const key = [g.home, g.away].sort().join(':');
        teamGame[g.home] = key;
        teamGame[g.away] = key;
      }
      // Group entries by game key
      const gameGroups: Record<string, number[]> = {};
      for (let ei = 0; ei < entries.length; ei++) {
        const pick = entries[ei][wk];
        if (!pick) continue;
        const gk = teamGame[pick.team];
        if (!gk) continue;
        if (!gameGroups[gk]) gameGroups[gk] = [];
        gameGroups[gk].push(ei);
      }
      // Mark correlated entries
      for (const group of Object.values(gameGroups)) {
        if (group.length > 1) {
          for (const ei of group) {
            map[`${ei}:${wk}`] = true;
          }
        }
      }
    }
    return map;
  }, [entries, weekNums, weeks]);

  const survivalCheckpoints = [1, 4, 8, 10, 12, 14, 16, 18];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* ── Controls ────────────────────────────────────────────────────── */}
      <div style={{
        background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 12, padding: '20px 24px',
        display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap',
      }}>
        <div>
          <div style={{ fontSize: '0.6rem', color: MUTED, letterSpacing: '0.08em', marginBottom: 8 }}>
            NUMBER OF ENTRIES
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            {[2, 3, 4, 5].map(n => (
              <button
                key={n}
                onClick={() => setNEntries(n)}
                style={{
                  padding: '6px 14px', borderRadius: 7, cursor: 'pointer',
                  border: `1px solid ${nEntries === n ? EMERALD : BORDER}`,
                  background: nEntries === n ? EMERALD + '18' : 'transparent',
                  color: nEntries === n ? EMERALD : FG,
                  fontWeight: nEntries === n ? 700 : 400, fontSize: '0.8rem',
                }}
              >
                {n}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <button
            onClick={generateEntries}
            style={{
              padding: '9px 20px', background: EMERALD + '15', border: `1px solid ${EMERALD}`,
              borderRadius: 8, color: EMERALD, fontWeight: 700, cursor: 'pointer', fontSize: '0.8rem',
            }}
          >
            Generate {nEntries} Diversified Entries
          </button>
          <div style={{ fontSize: '0.6rem', color: MUTED }}>
            Beam search K=300 with diversity penalty — each entry picks different teams
          </div>
        </div>

        {entries.length > 0 && (
          <button
            onClick={runSim}
            disabled={simRunning}
            style={{
              padding: '9px 20px', background: simRunning ? 'transparent' : AMBER + '15',
              border: `1px solid ${AMBER}`, borderRadius: 8, color: AMBER,
              fontWeight: 700, cursor: simRunning ? 'default' : 'pointer', fontSize: '0.8rem',
            }}
          >
            {simRunning ? 'Simulating...' : 'Run Portfolio Sim (30K)'}
          </button>
        )}

        {entries.length > 0 && (
          <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
            <div style={{ fontSize: '0.6rem', color: MUTED }}>CORRELATED RISK</div>
            <div style={{ display: 'flex', gap: 6, marginTop: 4, alignItems: 'center' }}>
              <div style={{ width: 10, height: 10, borderRadius: 2, background: AMBER + '60', border: `1px solid ${AMBER}` }} />
              <span style={{ fontSize: '0.7rem', color: MUTED }}>= Same game, only 1 can win</span>
            </div>
          </div>
        )}
      </div>

      {/* ── Entry grid table ─────────────────────────────────────────────── */}
      {entries.length > 0 && (
        <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 12, overflow: 'hidden' }}>
          <div style={{ padding: '14px 20px', borderBottom: `1px solid ${BORDER}` }}>
            <div style={{ fontWeight: 700, fontFamily: 'Nunito', fontSize: '1rem' }}>
              {nEntries}-Entry Portfolio
            </div>
            <div style={{ fontSize: '0.68rem', color: MUTED, marginTop: 2 }}>
              Week-by-week picks. Amber = entries picking from the same game (correlated risk — only one can win).
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.7rem' }}>
              <thead>
                <tr>
                  <th style={{
                    padding: '8px 14px', textAlign: 'left', fontWeight: 700,
                    color: MUTED, fontSize: '0.6rem', letterSpacing: '0.06em',
                    borderBottom: `1px solid ${BORDER}`, whiteSpace: 'nowrap',
                    position: 'sticky', left: 0, background: PANEL, zIndex: 2,
                  }}>
                    ENTRY
                  </th>
                  {weekNums.map(wk => (
                    <th key={wk} style={{
                      padding: '8px 6px', textAlign: 'center', fontWeight: 700,
                      color: MUTED, fontSize: '0.6rem', letterSpacing: '0.06em',
                      borderBottom: `1px solid ${BORDER}`, whiteSpace: 'nowrap',
                      minWidth: 64,
                    }}>
                      WK{wk}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {entries.map((entry, ei) => {
                  const color = CUSTOM_PATH_COLORS[ei % CUSTOM_PATH_COLORS.length];
                  // Per-entry joint survival prob
                  const survProb = weekNums.reduce((acc, wk) => {
                    const pick = entry[wk];
                    return pick ? acc * pick.wp : acc;
                  }, 1);

                  return (
                    <tr key={ei} style={{ borderBottom: `1px solid ${BORDER}` }}>
                      {/* Entry label */}
                      <td style={{
                        padding: '10px 14px', fontWeight: 700, whiteSpace: 'nowrap',
                        position: 'sticky', left: 0, background: PANEL, zIndex: 1,
                        borderRight: `1px solid ${BORDER}`,
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
                          <div>
                            <div style={{ color, fontSize: '0.75rem' }}>Entry {ei + 1}</div>
                            <div style={{ color: MUTED, fontSize: '0.6rem', fontWeight: 400 }}>
                              {(survProb * 100).toFixed(1)}% survive
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Weekly pick cells */}
                      {weekNums.map(wk => {
                        const pick = entry[wk];
                        const isCorrelated = correlationMap[`${ei}:${wk}`];

                        return (
                          <td key={wk} style={{
                            padding: '6px 4px', textAlign: 'center',
                            background: isCorrelated ? AMBER + '18' : 'transparent',
                            border: isCorrelated ? `1px solid ${AMBER}40` : '1px solid transparent',
                          }}>
                            {pick ? (
                              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                                <img
                                  src={getLogo(pick.team)}
                                  alt={pick.team}
                                  style={{ width: 22, height: 22 }}
                                  onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                                />
                                <div style={{ fontSize: '0.6rem', fontWeight: 700, color: FG }}>{pick.team}</div>
                                <div style={{ fontSize: '0.58rem', color: MUTED }}>
                                  {Math.round(pick.wp * 100)}%
                                </div>
                              </div>
                            ) : (
                              <div style={{ fontSize: '0.55rem', color: MUTED }}>BYE</div>
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
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

          {/* P(at least 1 survives) */}
          <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 12, padding: '20px 24px' }}>
            <div style={{ fontWeight: 700, fontFamily: 'Nunito', fontSize: '0.95rem', marginBottom: 14 }}>
              P(At Least 1 Entry Survives)
            </div>
            <table style={{ width: '100%', fontSize: '0.72rem', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', color: MUTED, padding: '4px 0', fontWeight: 600, fontSize: '0.6rem' }}>WEEK</th>
                  <th style={{ textAlign: 'right', color: MUTED, padding: '4px 0', fontWeight: 600, fontSize: '0.6rem' }}>PROBABILITY</th>
                  <th style={{ width: 80 }} />
                </tr>
              </thead>
              <tbody>
                {survivalCheckpoints.map(wk => {
                  const wi = weekNums.indexOf(wk);
                  if (wi < 0) return null;
                  const prob = portfolioResults.atLeastOne[wi] / 30_000;
                  const color = prob >= 0.7 ? EMERALD : prob >= 0.4 ? AMBER : RED;
                  return (
                    <tr key={wk} style={{ borderBottom: `1px solid ${BORDER}` }}>
                      <td style={{ padding: '7px 0', color: MUTED }}>Week {wk}</td>
                      <td style={{ padding: '7px 0', textAlign: 'right', fontWeight: 700, color }}>
                        {(prob * 100).toFixed(1)}%
                      </td>
                      <td style={{ padding: '7px 8px' }}>
                        <div style={{ height: 4, background: 'var(--c-track)', borderRadius: 2, overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${prob * 100}%`, background: color, borderRadius: 2 }} />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Per-entry survival curves */}
          <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 12, padding: '20px 24px' }}>
            <div style={{ fontWeight: 700, fontFamily: 'Nunito', fontSize: '0.95rem', marginBottom: 14 }}>
              Per-Entry Survival
            </div>
            <table style={{ width: '100%', fontSize: '0.72rem', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', color: MUTED, padding: '4px 0', fontWeight: 600, fontSize: '0.6rem' }}>ENTRY</th>
                  {survivalCheckpoints.map(wk => (
                    <th key={wk} style={{ textAlign: 'center', color: MUTED, padding: '4px 4px', fontWeight: 600, fontSize: '0.6rem' }}>
                      W{wk}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {portfolioResults.perEntry.map((curve, ei) => {
                  const color = CUSTOM_PATH_COLORS[ei % CUSTOM_PATH_COLORS.length];
                  return (
                    <tr key={ei} style={{ borderBottom: `1px solid ${BORDER}` }}>
                      <td style={{ padding: '7px 0' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div style={{ width: 6, height: 6, borderRadius: '50%', background: color }} />
                          <span style={{ color, fontWeight: 700 }}>E{ei + 1}</span>
                        </div>
                      </td>
                      {survivalCheckpoints.map(wk => {
                        const wi = weekNums.indexOf(wk);
                        const prob = wi >= 0 ? curve[wi] / 30_000 : null;
                        const cellColor = prob == null ? MUTED : prob >= 0.7 ? EMERALD : prob >= 0.4 ? AMBER : RED;
                        return (
                          <td key={wk} style={{ padding: '7px 4px', textAlign: 'center', fontWeight: 700, color: cellColor }}>
                            {prob != null ? `${(prob * 100).toFixed(0)}%` : '—'}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div style={{ marginTop: 12, fontSize: '0.6rem', color: MUTED, lineHeight: 1.6 }}>
              Correlated simulation — game outcomes are resolved once per iteration,
              so overlapping picks properly reduce portfolio survival.
            </div>
          </div>

        </div>
      )}

      {/* ── Empty state ───────────────────────────────────────────────────── */}
      {!entries.length && (
        <div style={{
          background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 12,
          padding: '48px 24px', textAlign: 'center',
        }}>
          <div style={{ fontSize: '2rem', marginBottom: 12 }}>🎯</div>
          <div style={{ fontWeight: 700, fontFamily: 'Nunito', fontSize: '1rem', marginBottom: 8 }}>
            Multi-Entry Portfolio Optimizer
          </div>
          <div style={{ color: MUTED, fontSize: '0.8rem', maxWidth: 480, margin: '0 auto', lineHeight: 1.6 }}>
            Select the number of entries and click Generate. The beam search algorithm (K=300) will
            produce maximally diversified paths — each entry uses a different team each week where possible.
            Run the portfolio sim to see correlated survival probabilities.
          </div>
        </div>
      )}

    </div>
  );
}
