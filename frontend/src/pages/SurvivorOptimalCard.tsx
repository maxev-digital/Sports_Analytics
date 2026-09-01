/**
 * SurvivorOptimalCard — beam search result card for the SIMULATOR tab.
 */
import type { SurvivorPick } from './survivorAlgo';
import { logo, wpColor, COLORS, withAlpha } from './survivorUtils';

interface Props {
  weekNums: number[];
  optimalPicks: Record<number, SurvivorPick>;
  survivalProb: number;
}

export function SurvivorOptimalCard({ weekNums, optimalPicks, survivalProb }: Props) {
  const { PURPLE } = COLORS;

  return (
    <div
      className="rounded-[10px] py-4 px-[18px]"
      style={{
        background: 'var(--c-panel)',
        border: `1px solid ${withAlpha(PURPLE, 0.31)}`,
        borderLeft: `3px solid ${PURPLE}`,
      }}
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <div className="text-[0.7rem] font-extrabold tracking-[0.1em]" style={{ color: PURPLE }}>
            BEAM SEARCH — OPTIMAL PATH
          </div>
          <div className="text-[0.63rem] mt-[3px] text-muted">
            K=300 beam search across all 18 weeks. Near-globally-optimal pick sequence — better than any greedy algorithm.
          </div>
        </div>
        <div className="text-right shrink-0 ml-4">
          <div className="text-[0.58rem] tracking-[0.06em] text-muted">JOINT SURVIVAL PROB</div>
          <div className="text-[1.2rem] font-extrabold font-[Nunito]" style={{ color: PURPLE }}>
            {(survivalProb * 100).toFixed(2)}%
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <div className="flex gap-[3px]" style={{ minWidth: `${weekNums.length * 58}px` }}>
          {weekNums.map(wk => {
            const pick = optimalPicks[wk];
            return (
              <div
                key={wk}
                className="shrink-0 w-[54px] text-center py-1.5 px-0.5 rounded-[6px]"
                style={{
                  background: pick ? withAlpha(PURPLE, 0.06) : 'transparent',
                  border: pick ? `1px solid ${withAlpha(PURPLE, 0.19)}` : '1px solid transparent',
                }}
              >
                <div className="text-[0.48rem] font-bold mb-[3px] text-muted">WK {wk}</div>
                {pick ? (
                  <>
                    <img
                      src={logo(pick.team)} alt={pick.team}
                      className="w-6 h-6 block mx-auto mb-0.5"
                      onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                    />
                    <div className="text-[0.55rem] font-bold text-fg">{pick.team}</div>
                    <div className="text-[0.5rem]" style={{ color: wpColor(pick.wp) }}>
                      {Math.round(pick.wp * 100)}%
                    </div>
                  </>
                ) : (
                  <div className="text-[0.5rem] pt-2 text-muted">BYE</div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
