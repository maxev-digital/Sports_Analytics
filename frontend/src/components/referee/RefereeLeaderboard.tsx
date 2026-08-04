import type { RefereeSummary, ColumnGroup } from '../../types/referee';
import { RefereeTrendBadge } from './RefereeTrendBadge';

type SortKey =
  | 'games' | 'avg_total' | 'over_rate' | 'home_cover_pct'
  | 'flags_per_game' | 'yards_per_game' | 'home_bias'
  | 'ot_rate' | 'dome_pct';

interface Props {
  referees: RefereeSummary[];
  loading: boolean;
  selectedName: string | null;
  onSelect: (name: string | null) => void;
  sort: SortKey;
  onSort: (key: SortKey) => void;
  columnGroup: ColumnGroup;
}

function pct(val: number | null | undefined): string {
  return val != null ? `${(val * 100).toFixed(1)}%` : '—';
}
function num(val: number | null | undefined, decimals = 1): string {
  return val != null ? val.toFixed(decimals) : '—';
}

type ColDef = { key: SortKey; label: string; render: (r: RefereeSummary) => string; highlight?: (r: RefereeSummary) => string };

const BETTING_COLS: ColDef[] = [
  { key: 'avg_total',      label: 'AVG TOTAL',  render: r => num(r.avg_total) },
  { key: 'over_rate',      label: 'OVER%',      render: r => pct(r.over_rate),
    highlight: r => r.over_rate != null && r.over_rate >= 0.58 ? 'text-orange-400 font-bold' :
                    r.over_rate != null && r.over_rate <= 0.42 ? 'text-blue-400 font-bold' : '' },
  { key: 'home_cover_pct', label: 'HOME CVR%',  render: r => pct(r.home_cover_pct),
    highlight: r => r.home_cover_pct != null && r.home_cover_pct >= 0.58 ? 'text-green-400 font-bold' : '' },
];

const PENALTY_COLS: ColDef[] = [
  { key: 'flags_per_game', label: 'FLAGS/G',  render: r => num(r.flags_per_game, 1),
    highlight: r => r.flags_per_game != null && r.flags_per_game > 16.5 ? 'text-red-400 font-bold' :
                    r.flags_per_game != null && r.flags_per_game < 12.5 ? 'text-green-400 font-bold' : '' },
  { key: 'yards_per_game', label: 'PEN YDS/G', render: r => num(r.yards_per_game, 0) },
  { key: 'home_bias',      label: 'HOME BIAS', render: r => pct(r.home_bias),
    highlight: r => r.home_bias != null && r.home_bias > 0.54 ? 'text-yellow-400 font-bold' :
                    r.home_bias != null && r.home_bias < 0.46 ? 'text-cyan-400 font-bold' : '' },
];

const ENV_COLS: ColDef[] = [
  { key: 'ot_rate',   label: 'OT RATE',   render: r => pct(r.ot_rate) },
  { key: 'dome_pct',  label: 'DOME%',     render: r => pct(r.dome_pct) },
  { key: 'games',     label: 'AVG WIND',  render: r => num(r.avg_wind, 0) },
];

const GROUP_COLS: Record<ColumnGroup, ColDef[]> = {
  betting:     BETTING_COLS,
  penalties:   PENALTY_COLS,
  environment: ENV_COLS,
};

export function RefereeLeaderboard({
  referees, loading, selectedName, onSelect, sort, onSort, columnGroup,
}: Props) {
  if (loading) {
    return <div className="py-16 text-center text-slate-500 animate-pulse">Loading referee data…</div>;
  }
  if (!referees.length) {
    return (
      <div className="py-16 text-center text-slate-500">
        <p className="font-bold text-slate-400">No referee data available</p>
        <p className="text-sm mt-1">
          Run <code className="bg-slate-800 px-1 rounded">python3 build_nfl_trends.py</code> to rebuild the database.
        </p>
      </div>
    );
  }

  const cols = GROUP_COLS[columnGroup];

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700 bg-slate-800/80">
              <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400 w-8">#</th>
              <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400">REFEREE</th>
              <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400">TENDENCY</th>
              <th
                onClick={() => onSort('games')}
                className={`px-3 py-2.5 text-right text-xs font-bold cursor-pointer select-none transition-colors
                  ${sort === 'games' ? 'text-blue-400' : 'text-slate-400 hover:text-white'}`}
              >
                GAMES {sort === 'games' ? '↓' : ''}
              </th>
              {cols.map(col => (
                <th
                  key={col.key}
                  onClick={() => onSort(col.key)}
                  className={`px-3 py-2.5 text-right text-xs font-bold cursor-pointer select-none transition-colors
                    ${sort === col.key ? 'text-blue-400' : 'text-slate-400 hover:text-white'}`}
                >
                  {col.label} {sort === col.key ? '↓' : ''}
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
                {cols.map(col => (
                  <td
                    key={col.key}
                    className={`px-3 py-2.5 text-right font-mono text-xs
                      ${col.highlight ? col.highlight(ref) : 'text-slate-300'}`}
                  >
                    {col.render(ref)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
