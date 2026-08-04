import { PickCard } from '../../hooks/useAgentChat';

interface PickReasoningCardProps {
  pick: PickCard;
}

const CONFIDENCE_STYLES: Record<string, string> = {
  high:   'bg-green-900/40 border-green-500/40 text-green-300',
  medium: 'bg-yellow-900/40 border-yellow-500/40 text-yellow-300',
  low:    'bg-slate-700/40 border-slate-500/40 text-slate-400',
};

function formatMarket(pick: PickCard): string {
  const side = (pick.pick_side ?? '').toUpperCase();
  const type = (pick.pick_type ?? '').toLowerCase();
  if (type === 'totals' || type === 'total') {
    return `${side} ${pick.total_line ?? '?'}`;
  }
  if (type === 'h2h' || type === 'moneyline' || type === 'ml') {
    return `${side} ML`;
  }
  return `${side} ${type.toUpperCase()}`;
}

function formatOdds(odds: number): string {
  return odds >= 0 ? `+${odds}` : `${odds}`;
}

export function PickReasoningCard({ pick }: PickReasoningCardProps) {
  const confStyle = CONFIDENCE_STYLES[pick.confidence_tier] ?? CONFIDENCE_STYLES.low;

  return (
    <div className="bg-slate-800/80 border border-slate-600/40 rounded-lg p-3 space-y-2">
      {/* Sport + Teams */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">{pick.sport}</span>
        <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${confStyle}`}>
          {pick.confidence_tier.toUpperCase()}
        </span>
      </div>

      <div className="text-sm font-bold text-white">
        {pick.away_team} @ {pick.home_team}
      </div>

      {/* Pick line */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="bg-blue-600/80 text-white text-xs font-bold px-2 py-0.5 rounded">
          {formatMarket(pick)}
        </span>
        <span className="text-xs text-slate-300">{formatOdds(pick.market_odds)}</span>
        <span className="text-xs text-green-400 font-semibold">+{pick.edge_pct.toFixed(1)}% edge</span>
      </div>

      {/* Stats row */}
      <div className="flex gap-3 text-xs text-slate-400">
        <span>ML: <span className="text-slate-200 font-medium">{pick.ml_confidence_pct.toFixed(0)}%</span></span>
        {pick.kelly_units > 0 && (
          <span>Kelly: <span className="text-slate-200 font-medium">{pick.kelly_units.toFixed(2)}u</span></span>
        )}
        {pick.detector && (
          <span className="text-slate-500 truncate">{pick.detector}</span>
        )}
      </div>

      {/* Narrative */}
      {pick.narrative && (
        <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">{pick.narrative}</p>
      )}
    </div>
  );
}
