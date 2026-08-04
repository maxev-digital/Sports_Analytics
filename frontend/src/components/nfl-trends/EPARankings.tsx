import { useState } from 'react';

export interface EPARow {
  rank: number; team: string; season: number;
  pass_epa: number | null; rush_epa: number | null;
  total_off_epa: number | null;
  pts_per_game: number | null; pts_allowed_per_game: number | null;
  games: number | null;
}

type SortKey = 'total_off_epa' | 'pass_epa' | 'rush_epa' | 'pts_per_game' | 'pts_allowed_per_game';

const SORT_OPTS: { key: SortKey; label: string }[] = [
  { key: 'total_off_epa',       label: 'OFF EPA'    },
  { key: 'pass_epa',            label: 'PASS EPA'   },
  { key: 'rush_epa',            label: 'RUSH EPA'   },
  { key: 'pts_per_game',        label: 'PTS/G'      },
  { key: 'pts_allowed_per_game', label: 'DEF PTS/G' },
];

function epaBar(val: number | null, max: number, color: string) {
  if (val === null) return null;
  const pct = Math.max(0, Math.min(100, (val / max) * 100));
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 bg-slate-700 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs tabular-nums">{val > 0 ? '+' : ''}{val.toFixed(0)}</span>
    </div>
  );
}

interface Props {
  rows: EPARow[];
  loading: boolean;
  onSelectTeam: (team: string) => void;
  selectedTeam: string | null;
}

export function EPARankings({ rows, loading, onSelectTeam, selectedTeam }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('total_off_epa');

  const ascending = sortKey === 'pts_allowed_per_game';
  const sorted = [...rows].sort((a, b) => {
    const av = (a[sortKey] as number | null) ?? (ascending ? 999 : -999);
    const bv = (b[sortKey] as number | null) ?? (ascending ? 999 : -999);
    return ascending ? av - bv : bv - av;
  }).map((r, i) => ({ ...r, rank: i + 1 }));

  const maxEpa = Math.max(...rows.map(r => Math.abs(r.total_off_epa ?? 0)), 1);
  const maxPts = Math.max(...rows.map(r => r.pts_per_game ?? 0), 1);
  const maxDef = Math.max(...rows.map(r => r.pts_allowed_per_game ?? 0), 1);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {SORT_OPTS.map(o => (
          <button
            key={o.key}
            onClick={() => setSortKey(o.key)}
            className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${
              sortKey === o.key ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            {o.label}
          </button>
        ))}
        <span className="ml-auto text-xs text-slate-500 self-center">Offensive EPA from player stats · Defense = pts allowed/g</span>
      </div>

      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        {loading ? (
          <div className="py-12 text-center text-slate-500 animate-pulse">Loading EPA data…</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700 bg-slate-800/80">
                  <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400 w-8">#</th>
                  <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400">TEAM</th>
                  <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400">OFF EPA</th>
                  <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400">PASS EPA</th>
                  <th className="px-3 py-2.5 text-left text-xs font-bold text-slate-400">RUSH EPA</th>
                  <th className="px-3 py-2.5 text-right text-xs font-bold text-slate-400">PTS/G</th>
                  <th className="px-3 py-2.5 text-right text-xs font-bold text-slate-400 text-red-400/80">OPP PTS/G</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map(row => (
                  <tr
                    key={row.team}
                    onClick={() => onSelectTeam(row.team === selectedTeam ? '' : row.team)}
                    className={`border-b border-slate-800 cursor-pointer transition-colors ${
                      selectedTeam === row.team ? 'bg-blue-900/30 border-blue-700/50' : 'hover:bg-slate-800/40'
                    }`}
                  >
                    <td className="px-3 py-2.5 text-slate-500 text-xs">{row.rank}</td>
                    <td className="px-3 py-2.5 font-bold text-white">{row.team}</td>
                    <td className="px-3 py-2.5 text-green-400">
                      {epaBar(row.total_off_epa, maxEpa, 'bg-green-500')}
                    </td>
                    <td className="px-3 py-2.5 text-blue-400">
                      {epaBar(row.pass_epa, maxEpa, 'bg-blue-500')}
                    </td>
                    <td className="px-3 py-2.5 text-yellow-400">
                      {epaBar(row.rush_epa, maxEpa, 'bg-yellow-500')}
                    </td>
                    <td className="px-3 py-2.5 text-right text-sm font-semibold text-white">
                      {row.pts_per_game?.toFixed(1) ?? '—'}
                    </td>
                    <td className="px-3 py-2.5 text-right text-sm">
                      <span className={row.pts_allowed_per_game !== null && row.pts_allowed_per_game <= 20 ? 'text-green-400 font-semibold' : row.pts_allowed_per_game !== null && row.pts_allowed_per_game >= 28 ? 'text-red-400' : 'text-slate-300'}>
                        {row.pts_allowed_per_game?.toFixed(1) ?? '—'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
