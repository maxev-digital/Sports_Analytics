import { GameProjection } from '../../types';
import { SportType } from '../../utils/sportDetection';

interface PickSummary {
  id: number;
  pick_side: string;
  pick_type: string;
  edge_pct: number;
  market_odds: number;
  confidence_tier: string | null;
  total_line: number | null;
}

interface SignalBarProps {
  projection: GameProjection;
  matchingPicks: PickSummary[];
  sport: SportType;
  isLive: boolean;
}

export function SignalBar({ projection, matchingPicks, isLive }: SignalBarProps) {
  const hasEdge = projection.edge !== null && Math.abs(projection.edge) >= 3;
  const hasPicks = matchingPicks.length > 0;
  const hasProjection = isLive && projection.projected_final > 0 && projection.recommendation;

  if (!hasEdge && !hasPicks && !hasProjection) return null;

  return (
    <div className="mt-2 pt-2 border-t border-slate-700 space-y-1.5">
      {/* Live projection banner */}
      {hasProjection && projection.recommendation && (
        <div className={`flex items-center justify-between px-3 py-2 rounded-lg text-sm font-bold ${
          projection.recommendation === 'OVER'
            ? 'bg-green-900/50 border border-green-600/50 text-green-300'
            : 'bg-red-900/50 border border-red-600/50 text-red-300'
        }`}>
          <span>{projection.recommendation === 'OVER' ? '⬆ TRENDING OVER' : '⬇ TRENDING UNDER'}</span>
          <div className="flex items-center gap-2 text-xs font-normal">
            {projection.edge !== null && (
              <span className="font-bold">{projection.edge > 0 ? '+' : ''}{projection.edge.toFixed(1)}%</span>
            )}
            <span className="text-slate-400">{projection.confidence}</span>
            {projection.unit_recommendation != null && projection.unit_recommendation > 0 && (
              <span className="text-purple-300">{projection.unit_recommendation.toFixed(1)}u</span>
            )}
          </div>
        </div>
      )}

      {/* MAX EV picks */}
      {hasPicks && (
        <div>
          <div className="text-xs font-bold text-blue-400 mb-1 uppercase tracking-widest">MAX EV Picks</div>
          <div className="space-y-0.5">
            {matchingPicks.map(pick => (
              <div key={pick.id} className="flex items-center justify-between bg-blue-900/20 border border-blue-600/20 rounded px-2 py-1.5">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                    pick.confidence_tier === 'HIGH'   ? 'bg-green-700/80 text-green-100' :
                    pick.confidence_tier === 'MEDIUM' ? 'bg-yellow-700/80 text-yellow-100' :
                    'bg-slate-600 text-slate-200'
                  }`}>{pick.confidence_tier ?? 'N/A'}</span>
                  <span className="text-sm font-bold text-white">{pick.pick_side}</span>
                  {pick.total_line != null && <span className="text-xs text-slate-400">{pick.total_line}</span>}
                  <span className="text-xs text-slate-500 capitalize">{pick.pick_type.replace('_', ' ')}</span>
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <span className="text-xs font-bold text-green-400">+{pick.edge_pct.toFixed(1)}%</span>
                  <span className="text-xs text-slate-400">{pick.market_odds > 0 ? '+' : ''}{pick.market_odds}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
