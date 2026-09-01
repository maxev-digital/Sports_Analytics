/**
 * SurvivorComparisonTable — week-by-week path comparison for the SIMULATOR tab.
 * Highlights divergences from the optimal beam-search path.
 */
import type { AlgoPath, SurvivorPick } from './survivorAlgo';
import { logo, wpColor, COLORS, withAlpha } from './survivorUtils';

interface Props {
  paths: AlgoPath[];
  weekNums: number[];
  optimalPicks: Record<number, SurvivorPick>;
}

export function SurvivorComparisonTable({ paths, weekNums, optimalPicks }: Props) {
  const { ORANGE } = COLORS;

  return (
    <div className="rounded-[10px] py-4 px-[18px] bg-panel border border-ev-border">
      <div className="text-[0.7rem] font-extrabold text-fg tracking-[0.06em] mb-3">
        WEEK-BY-WEEK COMPARISON — OPTIMAL vs. ALGORITHMIC PATHS
      </div>
      <div className="overflow-x-auto">
        <table
          className="border-collapse text-[0.63rem]"
          style={{ minWidth: `${weekNums.length * 62 + 140}px` }}
        >
          <thead>
            <tr className="border-b border-ev-border">
              <th className="py-[5px] px-[10px] text-left text-muted text-[0.58rem] min-w-[130px] sticky left-0 bg-panel">
                PATH
              </th>
              {weekNums.map(wk => (
                <th key={wk} className="py-[5px] px-[5px] text-center text-muted text-[0.52rem] min-w-[58px]">
                  W{wk}
                </th>
              ))}
              <th className="py-[5px] px-2 text-center text-muted text-[0.52rem]">JOINT%</th>
            </tr>
          </thead>
          <tbody>
            {paths.map(path => {
              const joint = Object.values(path.picks).reduce((acc, p) => acc * p.wp, 1);
              return (
                <tr key={path.id} className="border-b border-ev-border">
                  <td className="py-[5px] px-[10px] sticky left-0 bg-panel">
                    <div className="flex items-center gap-[5px]">
                      <div className="w-[7px] h-[7px] rounded-full shrink-0" style={{ background: path.color }} />
                      <span className="font-bold text-[0.62rem] whitespace-nowrap" style={{ color: path.color }}>
                        {path.name}
                      </span>
                    </div>
                  </td>
                  {weekNums.map(wk => {
                    const pick = path.picks[wk] as SurvivorPick | undefined;
                    const optPick = optimalPicks[wk];
                    const diverges = pick && optPick && pick.team !== optPick.team;
                    return (
                      <td
                        key={wk}
                        className="py-[3px] px-0.5 text-center"
                        style={{
                          background: diverges && path.id !== 'optimal'
                            ? withAlpha(ORANGE, 0.07)
                            : undefined,
                        }}
                      >
                        {pick ? (
                          <>
                            <img
                              src={logo(pick.team)} alt={pick.team}
                              className="w-5 h-5 block mx-auto mb-[1px]"
                              onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                            />
                            <div className="text-[0.48rem] font-bold" style={{ color: wpColor(pick.wp) }}>
                              {Math.round(pick.wp * 100)}%
                            </div>
                          </>
                        ) : (
                          <span className="text-[0.48rem] text-muted">—</span>
                        )}
                      </td>
                    );
                  })}
                  <td
                    className="py-[5px] px-2 text-center font-extrabold font-mono text-[0.65rem]"
                    style={{ color: wpColor(joint) }}
                  >
                    {(joint * 100).toFixed(2)}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="mt-2 text-[0.58rem] text-muted">
        Orange cells = week where this path diverges from optimal · JOINT% = product of all weekly WPs
      </div>
    </div>
  );
}
