/**
 * SurvivorSimPanel — Monte Carlo controls and results table for the SIMULATOR tab.
 */
import type { AlgoPath, SimResult } from './survivorAlgo';
import { COLORS, withAlpha } from './survivorUtils';

const CHECK_WEEKS = [1, 4, 8, 10, 12, 14, 16, 18];

interface Props {
  allPaths: AlgoPath[];
  iters: number;
  setIters: (n: number) => void;
  running: boolean;
  ran: boolean;
  simResults: Record<string, SimResult>;
  onRun: () => void;
}

function pctColor(p: number): string {
  const { EMERALD, BLUE, YELLOW, ORANGE, RED } = COLORS;
  return p >= 50 ? EMERALD : p >= 20 ? BLUE : p >= 5 ? YELLOW : p >= 1 ? ORANGE : RED;
}

function survPct(simResults: Record<string, SimResult>, pathId: string, week: number): number {
  return (simResults[pathId]?.survivalByWeek[week - 1] ?? 0) * 100;
}

export function SurvivorSimPanel({ allPaths, iters, setIters, running, ran, simResults, onRun }: Props) {
  const { PURPLE, BLUE } = COLORS;

  return (
    <div className="rounded-[10px] py-4 px-[18px] bg-panel border border-ev-border">
      {/* Controls */}
      <div className="flex items-center gap-[10px] mb-[14px] flex-wrap">
        <div className="text-[0.7rem] font-extrabold text-fg tracking-[0.06em] flex-1">
          MONTE CARLO SIMULATION
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-[0.6rem] text-muted">Iterations:</span>
          {[10_000, 50_000, 100_000].map(n => (
            <button
              key={n}
              onClick={() => setIters(n)}
              className="text-[0.63rem] font-bold py-1 px-[9px] rounded-[5px] cursor-pointer"
              style={{
                background: iters === n ? withAlpha(BLUE, 0.13) : 'transparent',
                border: `1px solid ${iters === n ? BLUE : 'var(--c-muted)'}`,
                color: iters === n ? BLUE : 'var(--c-muted)',
              }}
            >
              {(n / 1000).toFixed(0)}K
            </button>
          ))}
        </div>
        <button
          onClick={onRun}
          disabled={running}
          className="text-[0.72rem] font-extrabold py-[7px] px-[18px] rounded-md"
          style={{
            cursor: running ? 'default' : 'pointer',
            background: running ? 'var(--c-muted)' : withAlpha(PURPLE, 0.13),
            border: `1px solid ${running ? 'var(--c-muted)' : PURPLE}`,
            color: running ? 'var(--c-muted)' : PURPLE,
          }}
        >
          {running ? 'RUNNING...' : '▶ RUN SIMULATION'}
        </button>
      </div>

      {!ran && (
        <div className="text-[0.63rem] text-muted py-3">
          Simulates {iters.toLocaleString()} full seasons per path. Each week the picked team wins at their WP.
          Shows survival probability at key checkpoints and expected elimination week.
        </div>
      )}

      {ran && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[0.68rem]">
              <thead>
                <tr className="border-b border-ev-border">
                  <th className="py-1.5 px-[10px] text-left text-muted text-[0.58rem] font-bold min-w-[120px]">PATH</th>
                  {CHECK_WEEKS.map(wk => (
                    <th key={wk} className="py-1.5 px-2 text-center text-muted text-[0.58rem] font-bold">
                      WK {wk}
                    </th>
                  ))}
                  <th className="py-1.5 px-2 text-center text-muted text-[0.58rem] font-bold">EXP. ELIM</th>
                </tr>
              </thead>
              <tbody>
                {allPaths.map(path => {
                  const res = simResults[path.id];
                  if (!res) return null;
                  return (
                    <tr key={path.id} className="border-b border-ev-border">
                      <td className="py-2 px-[10px]">
                        <div className="flex items-center gap-1.5">
                          <div className="w-2 h-2 rounded-full shrink-0" style={{ background: path.color }} />
                          <span className="font-bold text-[0.65rem]" style={{ color: path.color }}>{path.name}</span>
                        </div>
                      </td>
                      {CHECK_WEEKS.map(wk => {
                        const p = survPct(simResults, path.id, wk);
                        const col = pctColor(p);
                        return (
                          <td key={wk} className="py-2 px-2 text-center">
                            <div className="text-[0.7rem] font-extrabold" style={{ color: col }}>{p.toFixed(1)}%</div>
                            <div className="h-[3px] rounded-sm mt-0.5 overflow-hidden" style={{ background: 'var(--c-muted)' }}>
                              <div className="h-full rounded-sm" style={{ width: `${Math.min(p, 100)}%`, background: col }} />
                            </div>
                          </td>
                        );
                      })}
                      <td className="py-2 px-2 text-center text-muted font-mono text-[0.65rem]">
                        Wk {res.expectedElim.toFixed(1)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="mt-2 text-[0.58rem] text-muted">
            {iters.toLocaleString()} simulations · survival % = fraction of sims where all picks won through that week
          </div>
        </>
      )}
    </div>
  );
}
