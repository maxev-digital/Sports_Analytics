import type { TendencyLabel } from '../../types/referee';

const CONFIG: Record<TendencyLabel, { label: string; className: string }> = {
  OVER_HEAVY:     { label: 'OVER HEAVY',     className: 'bg-orange-500/20 text-orange-400 border border-orange-500/40' },
  UNDER_HEAVY:    { label: 'UNDER HEAVY',    className: 'bg-blue-500/20 text-blue-400 border border-blue-500/40' },
  HOME_FRIENDLY:  { label: 'HOME FRIENDLY',  className: 'bg-green-500/20 text-green-400 border border-green-500/40' },
  NEUTRAL:        { label: 'NEUTRAL',         className: 'bg-slate-700/50 text-slate-400 border border-slate-600' },
};

interface Props {
  tendency: TendencyLabel;
}

export function RefereeTrendBadge({ tendency }: Props) {
  const { label, className } = CONFIG[tendency];
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold tracking-wide ${className}`}>
      {label}
    </span>
  );
}
