/**
 * SurvivorSimulator — "SIMULATOR" tab for the Survivor Helper.
 * Features:
 *   1. Beam search optimal path (near-globally-optimal, K=300)
 *   2. Monte Carlo survival simulation across all paths
 *   3. Week-by-week pick comparison table
 */
import { useState, useMemo } from 'react';
import { beamSearch, monteCarlo, type SurvivorGame, type SurvivorPick, type CustomPath } from './survivorAlgo';

const EMERALD = 'oklch(69.6% .17 162.48)';
const RED     = 'oklch(63.2% .204 25.331)';
const YELLOW  = 'oklch(79.5% .184 86.047)';
const BLUE    = 'oklch(62.3% .214 259.815)';
const ORANGE  = 'oklch(72% .19 50)';
const PURPLE  = 'oklch(70% .18 290)';
const MUTED   = 'var(--c-muted)';
const PANEL   = 'var(--c-panel)';
const BORDER  = 'var(--c-border)';
const FG      = 'var(--c-fg)';

const LOGO_MAP: Record<string, string> = {
  ARI:'ari',ATL:'atl',BAL:'bal',BUF:'buf',CAR:'car',CHI:'chi',CIN:'cin',CLE:'cle',
  DAL:'dal',DEN:'den',DET:'det',GB:'gb',HOU:'hou',IND:'ind',JAX:'jax',KC:'kc',
  LAC:'lac',LAR:'lar',LV:'lv',MIA:'mia',MIN:'min',NE:'ne',NO:'no',NYG:'nyg',
  NYJ:'nyj',PHI:'phi',PIT:'pit',SEA:'sea',SF:'sf',TB:'tb',TEN:'ten',WSH:'wsh',
};
const logo = (abbr: string) =>
  `https://a.espncdn.com/i/teamlogos/nfl/500/${LOGO_MAP[abbr] ?? abbr.toLowerCase()}.png`;

const wpColor = (wp: number) =>
  wp >= 0.73 ? EMERALD : wp >= 0.58 ? BLUE : wp >= 0.45 ? YELLOW : RED;

interface AlgoPath {
  id: string; name: string; color: string;
  picks: Record<number, SurvivorPick>;
}

interface Props {
  weeks: Record<number, SurvivorGame[]>;
  userPicks: Record<number, string>;
  algorithmicPaths: AlgoPath[];
  customPaths: CustomPath[];
}

type SimResult = { survivalByWeek: number[]; expectedElim: number };

const CHECK_WEEKS = [1, 4, 8, 10, 12, 14, 16, 18];

export function SurvivorSimulator({ weeks, userPicks, algorithmicPaths, customPaths }: Props) {
  const [iters, setIters]           = useState(50_000);
  const [simResults, setSimResults] = useState<Record<string, SimResult>>({});
  const [ran, setRan]               = useState(false);
  const [running, setRunning]       = useState(false);

  const weekNums = useMemo(
    () => Object.keys(weeks).map(Number).sort((a, b) => a - b),
    [weeks],
  );

  // Beam search optimal path — computed once on load
  const optimalPicks = useMemo(() => beamSearch(weeks, 300), [weeks]);
  const optimalSurvivalProb = Object.values(optimalPicks).reduce((acc, p) => acc * p.wp, 1);

  const optimalPath: AlgoPath = {
    id: 'optimal', name: 'OPTIMAL (BEAM)', color: PURPLE,
    picks: optimalPicks,
  };

  // Build user picks as a path if they've made any
  const userPickPath: AlgoPath | null = useMemo(() => {
    const pickMap: Record<number, SurvivorPick> = {};
    for (const wk of weekNums) {
      const team = userPicks[wk];
      if (!team) continue;
      const game = (weeks[wk] ?? []).find(g => g.home === team || g.away === team);
      if (!game) continue;
      const isHome = game.home === team;
      pickMap[wk] = {
        week: wk, team,
        wp: isHome ? game.home_wp : game.away_wp,
        label: isHome ? game.home_label : game.away_label,
        opp: isHome ? game.away : game.home,
        home: isHome,
      };
    }
    return Object.keys(pickMap).length > 0
      ? { id: 'mypicks', name: 'MY PICKS', color: EMERALD, picks: pickMap }
      : null;
  }, [userPicks, weeks, weekNums]);

  const allPaths: AlgoPath[] = [
    optimalPath,
    ...algorithmicPaths,
    ...customPaths,
    ...(userPickPath ? [userPickPath] : []),
  ];

  const runSim = () => {
    setRunning(true);
    // Use setTimeout to let the UI update before the heavy computation
    setTimeout(() => {
      const results: Record<string, SimResult> = {};
      for (const path of allPaths) {
        results[path.id] = monteCarlo(path.picks, iters);
      }
      setSimResults(results);
      setRan(true);
      setRunning(false);
    }, 10);
  };

  const survPct = (pathId: string, week: number): number | null => {
    const res = simResults[pathId];
    if (!res) return null;
    return (res.survivalByWeek[week - 1] ?? 0) * 100;
  };

  const pctColor = (p: number) =>
    p >= 50 ? EMERALD : p >= 20 ? BLUE : p >= 5 ? YELLOW : p >= 1 ? ORANGE : RED;

  return (
    <div style={{ display: 'grid', gap: 24 }}>

      {/* ── Optimal Path Card ────────────────────────────────────────────── */}
      <div style={{
        background: PANEL, borderRadius: 10,
        border: `1px solid ${PURPLE}50`, borderLeft: `3px solid ${PURPLE}`,
        padding: '16px 18px',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
          <div>
            <div style={{ fontSize: '0.7rem', fontWeight: 800, color: PURPLE, letterSpacing: '0.1em' }}>
              BEAM SEARCH — OPTIMAL PATH
            </div>
            <div style={{ fontSize: '0.63rem', color: MUTED, marginTop: 3 }}>
              K=300 beam search across all 18 weeks. Near-globally-optimal pick sequence — better than any greedy algorithm.
            </div>
          </div>
          <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: 16 }}>
            <div style={{ fontSize: '0.58rem', color: MUTED, letterSpacing: '0.06em' }}>JOINT SURVIVAL PROB</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: PURPLE, fontFamily: 'Nunito' }}>
              {(optimalSurvivalProb * 100).toFixed(2)}%
            </div>
          </div>
        </div>

        {/* Pick timeline */}
        <div style={{ overflowX: 'auto' }}>
          <div style={{ display: 'flex', gap: 3, minWidth: weekNums.length * 58 + 'px' }}>
            {weekNums.map(wk => {
              const pick = optimalPicks[wk];
              return (
                <div key={wk} style={{
                  flex: '0 0 54px', textAlign: 'center',
                  padding: '6px 2px',
                  background: pick ? PURPLE + '10' : 'transparent',
                  borderRadius: 6,
                  border: pick ? `1px solid ${PURPLE}30` : '1px solid transparent',
                }}>
                  <div style={{ fontSize: '0.48rem', color: MUTED, fontWeight: 700, marginBottom: 3 }}>WK {wk}</div>
                  {pick ? (
                    <>
                      <img src={logo(pick.team)} alt={pick.team}
                        style={{ width: 24, height: 24, display: 'block', margin: '0 auto 2px' }}
                        onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                      <div style={{ fontSize: '0.55rem', fontWeight: 700, color: FG }}>{pick.team}</div>
                      <div style={{ fontSize: '0.5rem', color: wpColor(pick.wp) }}>
                        {Math.round(pick.wp * 100)}%
                      </div>
                    </>
                  ) : (
                    <div style={{ fontSize: '0.5rem', color: MUTED, paddingTop: 8 }}>BYE</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Monte Carlo Controls ─────────────────────────────────────────── */}
      <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 10, padding: '16px 18px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
          <div style={{ fontSize: '0.7rem', fontWeight: 800, color: FG, letterSpacing: '0.06em', flex: 1 }}>
            MONTE CARLO SIMULATION
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: '0.6rem', color: MUTED }}>Iterations:</span>
            {[10_000, 50_000, 100_000].map(n => (
              <button key={n} onClick={() => setIters(n)} style={{
                fontSize: '0.63rem', fontWeight: 700, padding: '4px 9px', borderRadius: 5, cursor: 'pointer',
                background: iters === n ? BLUE + '22' : 'transparent',
                border: `1px solid ${iters === n ? BLUE : MUTED + '55'}`,
                color: iters === n ? BLUE : MUTED,
              }}>
                {(n / 1000).toFixed(0)}K
              </button>
            ))}
          </div>
          <button onClick={runSim} disabled={running} style={{
            fontSize: '0.72rem', fontWeight: 800, padding: '7px 18px', borderRadius: 6,
            cursor: running ? 'default' : 'pointer',
            background: running ? MUTED + '22' : PURPLE + '22',
            border: `1px solid ${running ? MUTED : PURPLE}`,
            color: running ? MUTED : PURPLE,
          }}>
            {running ? 'RUNNING...' : '▶ RUN SIMULATION'}
          </button>
        </div>

        {!ran && (
          <div style={{ fontSize: '0.63rem', color: MUTED, padding: '12px 0' }}>
            Simulates {iters.toLocaleString()} full seasons per path. Each week the picked team wins at their Walters WP.
            Shows survival probability at key checkpoints and expected elimination week.
          </div>
        )}

        {ran && (
          <>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.68rem' }}>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${BORDER}` }}>
                    <th style={{ padding: '6px 10px', textAlign: 'left', color: MUTED, fontSize: '0.58rem', fontWeight: 700, minWidth: 120 }}>PATH</th>
                    {CHECK_WEEKS.map(wk => (
                      <th key={wk} style={{ padding: '6px 8px', textAlign: 'center', color: MUTED, fontSize: '0.58rem', fontWeight: 700 }}>
                        WK {wk}
                      </th>
                    ))}
                    <th style={{ padding: '6px 8px', textAlign: 'center', color: MUTED, fontSize: '0.58rem', fontWeight: 700 }}>EXP. ELIM</th>
                  </tr>
                </thead>
                <tbody>
                  {allPaths.map(path => {
                    const res = simResults[path.id];
                    if (!res) return null;
                    return (
                      <tr key={path.id} style={{ borderBottom: `1px solid ${BORDER}` }}>
                        <td style={{ padding: '8px 10px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <div style={{ width: 8, height: 8, borderRadius: '50%', background: path.color, flexShrink: 0 }} />
                            <span style={{ fontWeight: 700, color: path.color, fontSize: '0.65rem' }}>{path.name}</span>
                          </div>
                        </td>
                        {CHECK_WEEKS.map(wk => {
                          const p = survPct(path.id, wk) ?? 0;
                          const barColor = pctColor(p);
                          return (
                            <td key={wk} style={{ padding: '8px 8px', textAlign: 'center' }}>
                              <div style={{ fontSize: '0.7rem', fontWeight: 800, color: barColor }}>{p.toFixed(1)}%</div>
                              <div style={{ height: 3, borderRadius: 2, background: MUTED + '33', marginTop: 2, overflow: 'hidden' }}>
                                <div style={{ width: `${Math.min(p, 100)}%`, height: '100%', background: barColor, borderRadius: 2 }} />
                              </div>
                            </td>
                          );
                        })}
                        <td style={{ padding: '8px 8px', textAlign: 'center', color: MUTED, fontFamily: 'monospace', fontSize: '0.65rem' }}>
                          Wk {res.expectedElim.toFixed(1)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div style={{ marginTop: 8, fontSize: '0.58rem', color: MUTED }}>
              {iters.toLocaleString()} simulations · survival % = fraction of sims where all picks won through that week
            </div>
          </>
        )}
      </div>

      {/* ── Week-by-week path comparison ─────────────────────────────────── */}
      <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 10, padding: '16px 18px' }}>
        <div style={{ fontSize: '0.7rem', fontWeight: 800, color: FG, letterSpacing: '0.06em', marginBottom: 12 }}>
          WEEK-BY-WEEK COMPARISON — OPTIMAL vs. ALGORITHMIC PATHS
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ borderCollapse: 'collapse', fontSize: '0.63rem', minWidth: weekNums.length * 62 + 140 + 'px' }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${BORDER}` }}>
                <th style={{ padding: '5px 10px', textAlign: 'left', color: MUTED, fontSize: '0.58rem', minWidth: 130, position: 'sticky', left: 0, background: PANEL }}>PATH</th>
                {weekNums.map(wk => (
                  <th key={wk} style={{ padding: '5px 5px', textAlign: 'center', color: MUTED, fontSize: '0.52rem', minWidth: 58 }}>
                    W{wk}
                  </th>
                ))}
                <th style={{ padding: '5px 8px', textAlign: 'center', color: MUTED, fontSize: '0.52rem' }}>JOINT%</th>
              </tr>
            </thead>
            <tbody>
              {[optimalPath, ...algorithmicPaths, ...(userPickPath ? [userPickPath] : [])].map(path => {
                const joint = Object.values(path.picks).reduce((acc, p) => acc * p.wp, 1);
                return (
                  <tr key={path.id} style={{ borderBottom: `1px solid ${BORDER}` }}>
                    <td style={{ padding: '5px 10px', position: 'sticky', left: 0, background: PANEL }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                        <div style={{ width: 7, height: 7, borderRadius: '50%', background: path.color, flexShrink: 0 }} />
                        <span style={{ fontWeight: 700, color: path.color, fontSize: '0.62rem', whiteSpace: 'nowrap' }}>{path.name}</span>
                      </div>
                    </td>
                    {weekNums.map(wk => {
                      const pick = path.picks[wk] as SurvivorPick | undefined;
                      // Check if optimal and this path diverge
                      const optPick = optimalPicks[wk];
                      const diverges = pick && optPick && pick.team !== optPick.team;
                      return (
                        <td key={wk} style={{
                          padding: '3px 2px', textAlign: 'center',
                          background: diverges && path.id !== 'optimal' ? ORANGE + '12' : undefined,
                        }}>
                          {pick ? (
                            <>
                              <img src={logo(pick.team)} alt={pick.team}
                                style={{ width: 20, height: 20, display: 'block', margin: '0 auto 1px' }}
                                onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                              <div style={{ fontSize: '0.48rem', fontWeight: 700, color: wpColor(pick.wp) }}>
                                {Math.round(pick.wp * 100)}%
                              </div>
                            </>
                          ) : (
                            <span style={{ fontSize: '0.48rem', color: MUTED }}>—</span>
                          )}
                        </td>
                      );
                    })}
                    <td style={{ padding: '5px 8px', textAlign: 'center', fontWeight: 800, fontFamily: 'monospace', fontSize: '0.65rem', color: wpColor(joint) }}>
                      {(joint * 100).toFixed(2)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div style={{ marginTop: 8, fontSize: '0.58rem', color: MUTED }}>
          Orange cells = week where this path diverges from optimal · JOINT% = product of all weekly WPs (theoretical max survival)
        </div>
      </div>

    </div>
  );
}
