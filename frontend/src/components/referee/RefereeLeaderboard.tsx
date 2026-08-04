import type { RefereeSummary } from '../../types/referee';
import { RefereeTrendBadge } from './RefereeTrendBadge';

type SortKey = 'games' | 'avg_total' | 'over_rate' | 'home_cover_pct';

interface Props {
  referees: RefereeSummary[];
  loading: boolean;
  selectedName: string | null;
  onSelect: (name: string | null) => void;
  sort: SortKey;
  onSort: (key: SortKey) => void;
}

function pct(val: number | null): string {
  return val !== null ? `${(val * 100).toFixed(1)}%` : '—';
}

const HEADERS: { key: SortKey; label: string }[] = [
  { key: 'games',          label: 'GAMES' },
  { key: 'avg_total',      label: 'AVG TOTAL' },
  { key: 'over_rate',      label: 'OVER%' },
  { key: 'home_cover_pct', label: 'HOME CVR%' },
];

export function RefereeLeaderboard({ referees, loading, selectedName, onSelect, sort, onSort }: Props) {
  if (loading) {
    return <div className="py-16 text-center text-slate-500 animate-pulse">Loading referee data…</div>;
  }

  if (!referees.length) {
    return (
      <div className="py-16 text-center text-slate-500">
        <p className="font-bold text-slate-400">No referee data available</p>
        <p className="text-sm mt-1">Run <code className="bg-slate-800 px-1 rounded">python3 build_nfl_trends.py</code> to rebuild the database.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700 bg-slate-800/80">
              <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400 w-8">#</th>
              <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400">REFEREE</th>
              <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400">TENDENCY</th>
              {HEADERS.map(h => (
                <th key={h.key}
                  onClick={() => onSort(h.key)}
                  className={`px-3 py-2.5 text-right text-xs font-bold cursor-pointer select-none transition-colors
                    ${sort === h.key ? 'text-blue-400' : 'text-slate-400 hover:text-white'}`}
                >
                  {h.label} {sort === h.key ? '↓' : ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {referees.map((ref, i) => (
              <tr
                key={ref.name}
                onClick={() => onSelect(selectedName === ref.name ? null : ref.name)}
                className={`border-b border-slate-800 cursor-pointer transition-colors
                  ${selectedName === ref.name ? 'bg-blue-900/30' : 'hover:bg-slate-800/40'}`}
              >
                <td className="px-3 py-2.5 text-slate-500 text-xs">{i + 1}</td>
                <td className="px-3 py-2.5 font-bold text-white">{ref.name}</td>
                <td className="px-3 py-2.5"><RefereeTrendBadge tendency={ref.tendency} /></td>
                <td className="px-3 py-2.5 text-right font-mono text-xs text-slate-300">{ref.games}</td>
                <td className="px-3 py-2.5 text-right font-mono text-xs text-slate-300">
                  {ref.avg_total !== null ? ref.avg_total.toFixed(1) : '—'}
                </td>
                <td className={`px-3 py-2.5 text-right font-mono text-xs font-bold
                  ${ref.over_rate !== null && ref.over_rate >= 0.58 ? 'text-orange-400' :
                    ref.over_rate !== null && ref.over_rate <= 0.42 ? 'text-blue-400' : 'text-slate-300'}`}>
                  {pct(ref.over_rate)}
                </td>
                <td className={`px-3 py-2.5 text-right font-mono text-xs font-bold
                  ${ref.home_cover_pct !== null && ref.home_cover_pct >= 0.58 ? 'text-green-400' : 'text-slate-300'}`}>
                  {pct(ref.home_cover_pct)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
